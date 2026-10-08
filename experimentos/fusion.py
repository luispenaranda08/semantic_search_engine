#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""¿RRF es la mejor forma de fusionar? Comparación con fusión convexa, RRF ponderado y fusión con compuerta.

Motivación (hallazgos de la escalera): el híbrido por RRF no supera al denso puro y en consultas sin
vocabulario común lo lastra; Bruch et al. (2024) reportan que la combinación convexa supera a RRF
pero necesita calibrar un peso con etiquetas. Aquí se mide cuánto, y con qué protocolo honesto.

Protocolo (sin fuga): el parámetro de cada familia (alpha, peso del denso, umbral de cobertura) se elige
por LEAVE-ONE-SET-OUT: para evaluar en el conjunto T se escoge el parámetro que maximiza el nDCG@10
medio (promedio de medias por conjunto) en los OTROS tres conjuntos, y se aplica a T sin retocarlo.
Se reporta también el óptimo «oráculo» dentro del conjunto, solo como cota superior optimista.

Conjuntos: sintético (40), ampliado (127), difícil A (52), difícil B (78, réplica).
Bases de texto: «desc» (descripción, tipo C3) y «onto» (texto enriquecido, tipo C4).
Comparación pareada de cada familia frente a RRF(k=60) con Wilcoxon + permutación y Holm entre familias.

Uso:  python3 fusion.py   ->  resultados/fusion.json y fusion.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import fusion as F
from lib import metrics as M
from lib.banco import (CONJUNTOS, EncoderCacheado, Puntuaciones, cargar_conjunto, cargar_config,
                       cargar_jsonl, ranking, RAIZ)
from lib.encoders import construir_encoder
from lib.stats import comparar, holm

ALPHAS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
PESOS = [1.0, 1.5, 2.0, 3.0, 5.0]
THETAS = [0.25, 0.5, 0.75, 1.0]
FAMILIAS = {
    "convexa_minmax": [("a=%.1f" % a, a) for a in ALPHAS],
    "convexa_z": [("a=%.1f" % a, a) for a in ALPHAS],
    "rrf_ponderado": [("w=%.1f" % w, w) for w in PESOS],
    "rrf_compuerta": [("t=%.2f" % t, t) for t in THETAS],
}


def puntajes(fam: str, par, P: Puntuaciones, q: str) -> dict[str, float]:
    b, d = P.puntaje_bm25(q), P.puntaje_denso(q)
    if fam == "convexa_minmax":
        return F.convexa(b, d, P.ids, par, "minmax")
    if fam == "convexa_z":
        return F.convexa(b, d, P.ids, par, "z")
    if fam == "rrf_ponderado":
        return F.rrf(b, d, 60, w_denso=par)
    if fam == "rrf_compuerta":
        return F.rrf_compuerta(b, d, P.cobertura_lexica(q), par)
    raise ValueError(fam)


def main() -> None:
    cfg = cargar_config()
    docs = cargar_jsonl(RAIZ / cfg["rutas"]["corpus"])
    enc = EncoderCacheado(construir_encoder(cfg, []))
    k1, b = cfg["bm25"]["k1"], cfg["bm25"]["b"]
    bases = {"desc": {d["id"]: d["descripcion"] for d in docs},
             "onto": {d["id"]: d["texto_indexable"] for d in docs}}
    P = {nom: Puntuaciones(t, enc, k1, b) for nom, t in bases.items()}
    ids = P["desc"].ids
    conjuntos = {n: cargar_conjunto(n) for n in CONJUNTOS}

    # nDCG@10 por consulta de cada variante, base y conjunto
    V: dict = {}          # V[base][conjunto][variante] = np.array
    for base in P:
        V[base] = {}
        for cn, (cons, qr) in conjuntos.items():
            def nd(fn):
                return np.array([M.ndcg(ranking(fn(c["texto"]), ids), qr[c["id"]], 10) for c in cons])
            v = {"bm25": nd(P[base].puntaje_bm25), "denso": nd(P[base].puntaje_denso),
                 "rrf60": nd(lambda q: F.rrf(P[base].puntaje_bm25(q), P[base].puntaje_denso(q), 60))}
            for fam, grid in FAMILIAS.items():
                for etq, par in grid:
                    v[f"{fam}|{etq}"] = nd(lambda q, fam=fam, par=par: puntajes(fam, par, P[base], q))
            V[base][cn] = v
        print(f"[fusion] base {base} lista")

    # sanidad: rrf60 y denso reproducen la escalera (C3/C4 y C1/C2)
    ref = json.loads((RAIZ / "resultados/resultados_real_ampliado_v1.json").read_text(encoding="utf-8"))
    chequeo = {
        "C3_ampliado": (V["desc"]["ampliado"]["rrf60"].mean(), ref["global"]["Híbrido (sin ontología)"]["ndcg@10"]),
        "C4_ampliado": (V["onto"]["ampliado"]["rrf60"].mean(), ref["global"]["Híbrido + ontología"]["ndcg@10"]),
        "C1_ampliado": (V["desc"]["ampliado"]["denso"].mean(), ref["global"]["Denso puro"]["ndcg@10"]),
        "C2_ampliado": (V["onto"]["ampliado"]["denso"].mean(), ref["global"]["Denso + ontología"]["ndcg@10"]),
    }
    for k, (a, r) in chequeo.items():
        assert abs(a - r) < 1e-9, f"No reproduce la escalera: {k} {a} vs {r}"
    print("[fusion] sanidad OK: rrf60/denso reproducen C1–C4 del ampliado")

    res = {"alphas": ALPHAS, "pesos": PESOS, "thetas": THETAS, "n": {c: len(v[0]) for c, v in conjuntos.items()},
           "curvas": {}, "loso": {}, "oraculo": {}, "estadistica": {}}
    for base in P:
        res["curvas"][base] = {cn: {k: float(x.mean()) for k, x in V[base][cn].items()} for cn in conjuntos}
        res["loso"][base], res["oraculo"][base], res["estadistica"][base] = {}, {}, {}
        for cn in conjuntos:
            otros = [c for c in conjuntos if c != cn]
            elegido: dict = {}
            for fam, grid in FAMILIAS.items():
                score = {etq: np.mean([V[base][o][f"{fam}|{etq}"].mean() for o in otros]) for etq, _ in grid}
                mejor = max(score, key=score.get)
                elegido[fam] = mejor
            res["loso"][base][cn] = {fam: {"parametro": elegido[fam], "ndcg": float(V[base][cn][f"{fam}|{elegido[fam]}"].mean())}
                                     for fam in FAMILIAS}
            res["oraculo"][base][cn] = {fam: {"parametro": max((e for e, _ in FAMILIAS[fam]), key=lambda e: V[base][cn][f"{fam}|{e}"].mean()),
                                              "ndcg": float(max(V[base][cn][f"{fam}|{e}"].mean() for e, _ in FAMILIAS[fam]))}
                                        for fam in FAMILIAS}
            est, ps = {}, {}
            for fam in FAMILIAS:
                a_ = V[base][cn][f"{fam}|{elegido[fam]}"]
                r = comparar(a_, V[base][cn]["rrf60"])
                est[fam] = {"delta_vs_rrf60": r["media_dif"], "pares_no_nulos": r["n_pares_no_nulos"],
                            "p_wilcoxon": r["p_valor"], "p_permutacion": r["p_permutacion"], "ic95": r["ic95_dif"]}
                ps[fam] = r["p_valor"]
            hw = holm(ps)
            pp = holm({f: est[f]["p_permutacion"] for f in est})
            for f in est:
                est[f]["p_holm"], est[f]["p_holm_permutacion"] = hw[f], pp[f]
                est[f]["robusto"] = bool(hw[f] is not None and pp[f] is not None and hw[f] < 0.05 and pp[f] < 0.05)
            # denso puro frente a rrf60 (referencia: ¿el híbrido ayuda o lastra?)
            r = comparar(V[base][cn]["denso"], V[base][cn]["rrf60"])
            est["denso_puro"] = {"delta_vs_rrf60": r["media_dif"], "pares_no_nulos": r["n_pares_no_nulos"],
                                 "p_wilcoxon": r["p_valor"], "p_permutacion": r["p_permutacion"]}
            res["estadistica"][base][cn] = est
    Path(RAIZ / "resultados/fusion.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(RAIZ / "resultados/fusion.md").write_text(a_markdown(res), encoding="utf-8")
    print("Guardado resultados/fusion.json y fusion.md")
    try:
        figura(res)
    except Exception as e:           # la figura es accesoria
        print("figura omitida:", e)


def a_markdown(r: dict) -> str:
    L = ["# Fusión de señales: RRF frente a alternativas", "",
         "nDCG@10 con el parámetro elegido por *leave-one-set-out* (sin fuga). Δ = variante − RRF(k=60).", ""]
    for base, tit in (("onto", "Base enriquecida (tipo C4)"), ("desc", "Base descripción (tipo C3)")):
        L += [f"## {tit}", "", "| Variante | " + " | ".join(r["n"]) + " |", "|---|" + "---|" * len(r["n"])]
        L.append("| BM25 solo | " + " | ".join(f"{r['curvas'][base][c]['bm25']:.3f}" for c in r["n"]) + " |")
        L.append("| Denso puro | " + " | ".join(f"{r['curvas'][base][c]['denso']:.3f}" for c in r["n"]) + " |")
        L.append("| **RRF k=60** | " + " | ".join(f"{r['curvas'][base][c]['rrf60']:.3f}" for c in r["n"]) + " |")
        for fam in FAMILIAS:
            cel = []
            for c in r["n"]:
                e, l = r["estadistica"][base][c][fam], r["loso"][base][c][fam]
                cel.append(f"{l['ndcg']:.3f} ({e['delta_vs_rrf60']:+.3f}; {l['parametro']}{'; **robusto**' if e['robusto'] else ''})")
            L.append(f"| {fam} (LOSO) | " + " | ".join(cel) + " |")
        L.append("| *oráculo: mejor convexa min–max* | " + " | ".join(
            f"{r['oraculo'][base][c]['convexa_minmax']['ndcg']:.3f} ({r['oraculo'][base][c]['convexa_minmax']['parametro']})" for c in r["n"]) + " |")
        L.append("")
    L += ["## Curva alpha (convexa min–max), base enriquecida", "", "| alpha | " + " | ".join(r["n"]) + " |", "|---|" + "---|" * len(r["n"])]
    for a in r["alphas"]:
        L.append(f"| {a:.1f} | " + " | ".join(f"{r['curvas']['onto'][c]['convexa_minmax|a=%.1f' % a]:.3f}" for c in r["n"]) + " |")
    return "\n".join(L) + "\n"


def figura(r: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4), sharey=False)
    for j, base in enumerate(("onto", "desc")):
        for c in r["n"]:
            ys = [r["curvas"][base][c]["convexa_minmax|a=%.1f" % a] for a in r["alphas"]]
            ax[j].plot(r["alphas"], ys, marker="o", label=f"{c} (n={r['n'][c]})")
            ax[j].axhline(r["curvas"][base][c]["rrf60"], ls=":", lw=1, color=ax[j].lines[-1].get_color())
        ax[j].set_title(f"Convexa min–max, base {'enriquecida' if base == 'onto' else 'descripción'}\n(línea punteada: RRF k=60)")
        ax[j].set_xlabel("alpha (peso de la señal densa)")
        ax[j].set_ylabel("nDCG@10")
        ax[j].grid(alpha=.3)
    ax[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(RAIZ / "resultados/fig_fusion_alpha.png", dpi=130)


if __name__ == "__main__":
    main()
