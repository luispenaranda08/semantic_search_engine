#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fusión adaptativa sobre el corpus v3 (811 documentos): ¿se puede tener lo mejor de C2 y de C4?

En el corpus v3 ninguna configuración fija domina: C4 (RRF de BM25 y denso sobre el texto
enriquecido) gana cuando la consulta comparte vocabulario con el documento y C2 (denso sobre el
mismo texto) cuando no lo comparte. Aquí se evalúan fusiones que deciden, consulta por consulta,
cuánto pesa BM25, todas sobre la base enriquecida:

  * rrf_cobertura  — SIN PARÁMETRO: RRF con peso de BM25 igual a su cobertura léxica de la consulta
                     (fracción de raíces de la consulta presentes en el mejor documento de BM25).
                     No se ajusta nada con etiquetas: es la variante que se puede defender sin fuga.
  * rrf_compuerta  — RRF si la cobertura alcanza theta; si no, denso puro.
  * rrf_ponderado  — RRF con peso fijo del denso.
  * convexa_minmax — combinación convexa de puntuaciones normalizadas.

Protocolo sin fuga para las familias con parámetro: LEAVE-ONE-GROUP-OUT sobre seis grupos de
consultas (reportes, pruebas regionales, funcionalidades, pruebas del catálogo, reglas y
difíciles A+B): para evaluar un grupo se elige el parámetro que maximiza la media de las medias de
los otros cinco. Comparaciones pareadas frente a C4 (RRF k=60) y frente a C2 (denso), con
Wilcoxon + permutación y Holm dentro de cada familia de comparaciones.

Uso:  python3 fusion_v3.py   ->  resultados/fusion_v3.json y fusion_v3.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import fusion as F
from lib import metrics as M
from lib.banco import EncoderCacheado, Puntuaciones, cargar_config, cargar_jsonl, ranking, RAIZ
from lib.encoders import construir_encoder
from lib.stats import comparar, holm
from analisis_v3 import boot_cluster

ALPHAS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
PESOS = [1.0, 1.5, 2.0, 3.0, 5.0]
THETAS = [0.25, 0.5, 0.75, 1.0]
FAMILIAS = {
    "convexa_minmax": [("a=%.1f" % a, a) for a in ALPHAS],
    "rrf_ponderado": [("w=%.1f" % w, w) for w in PESOS],
    "rrf_compuerta": [("t=%.2f" % t, t) for t in THETAS],
}
GRUPO_DE_ESTRATO = {"competencias": "pruebas_regionales", "funcionalidad": "funcionalidades",
                    "prueba_catalogo": "pruebas_catalogo", "regla_participacion": "reglas"}
GRUPOS = ["reportes", "pruebas_regionales", "funcionalidades", "pruebas_catalogo", "reglas", "dificiles_ab"]


def main() -> None:
    cfg = cargar_config()
    docs = cargar_jsonl(RAIZ / "corpus" / "corpus_v3.jsonl")
    enc = EncoderCacheado(construir_encoder(cfg, []))
    P = Puntuaciones({d["id"]: d["texto_indexable"] for d in docs}, enc, cfg["bm25"]["k1"], cfg["bm25"]["b"])
    ids = P.ids

    consultas = []      # (grupo, id, texto, qrels)
    # Grupos de consultas hermanas (mismo conjunto de relevantes) para el bootstrap por objetivo.
    for cf, qf, dificil in (("consultas_final_v3", "qrels_final_v3", False),
                            ("consultas_dificil_ab", "qrels_dificil_ab", True)):
        qr = {r["id"]: r["relevancia"] for r in cargar_jsonl(RAIZ / "datos" / f"{qf}.jsonl")}
        for c in cargar_jsonl(RAIZ / "datos" / f"{cf}.jsonl"):
            if M.tiene_gold(qr.get(c["id"], {})):
                g = "dificiles_ab" if dificil else GRUPO_DE_ESTRATO.get(c.get("estrato"), "reportes")
                consultas.append((g, c["id"], c["texto"], qr[c["id"]]))

    def nd(fn) -> np.ndarray:
        return np.array([M.ndcg(ranking(fn(t), ids), q, 10) for _, _, t, q in consultas])

    V = {"bm25": nd(P.puntaje_bm25), "C2_denso": nd(P.puntaje_denso),
         "C4_rrf60": nd(lambda q: F.rrf(P.puntaje_bm25(q), P.puntaje_denso(q), 60)),
         "rrf_cobertura": nd(lambda q: F.rrf(P.puntaje_bm25(q), P.puntaje_denso(q), 60,
                                             w_bm25=P.cobertura_lexica(q)))}
    for fam, grid in FAMILIAS.items():
        for etq, par in grid:
            if fam == "convexa_minmax":
                fn = lambda q, a=par: F.convexa(P.puntaje_bm25(q), P.puntaje_denso(q), ids, a, "minmax")
            elif fam == "rrf_ponderado":
                fn = lambda q, w=par: F.rrf(P.puntaje_bm25(q), P.puntaje_denso(q), 60, w_denso=w)
            else:
                fn = lambda q, t=par: F.rrf_compuerta(P.puntaje_bm25(q), P.puntaje_denso(q),
                                                      P.cobertura_lexica(q), t)
            V[f"{fam}|{etq}"] = nd(fn)
    print("[fusion_v3] variantes calculadas")

    # Sanidad: C2 y C4 reproducen exactamente los resultados por consulta de eval_flexible.
    ref = {}
    for f in ("resultados_v3.json", "resultados_v3_dificil_ab.json"):
        pc = json.loads((RAIZ / "resultados" / f).read_text(encoding="utf-8"))["por_consulta"]
        for nombre, clave in (("Denso + ontología", "C2_denso"), ("Híbrido + ontología", "C4_rrf60")):
            for qid, m in pc[nombre].items():
                ref[(clave, qid)] = m["ndcg@10"]
    for clave in ("C2_denso", "C4_rrf60"):
        for i, (_, qid, _, _) in enumerate(consultas):
            assert abs(V[clave][i] - ref[(clave, qid)]) < 1e-9, f"no reproduce {clave} en {qid}"
    print("[fusion_v3] sanidad OK: C2 y C4 reproducen la evaluación del corpus v3")

    grupo = np.array([g for g, *_ in consultas])
    objetivo = np.array(["|".join(sorted(q)) for *_, q in consultas])
    mascara = {g: grupo == g for g in GRUPOS}

    # Leave-one-group-out: la variante elegida para cada grupo se decide sin mirarlo.
    elegida: dict[str, dict[str, str]] = {}
    for fam, grid in FAMILIAS.items():
        elegida[fam] = {}
        for g in GRUPOS:
            otros = [o for o in GRUPOS if o != g]
            score = {etq: np.mean([V[f"{fam}|{etq}"][mascara[o]].mean() for o in otros]) for etq, _ in grid}
            elegida[fam][g] = max(score, key=score.get)
        V[f"{fam}|LOGO"] = np.zeros(len(consultas))
        for g in GRUPOS:
            V[f"{fam}|LOGO"][mascara[g]] = V[f"{fam}|{elegida[fam][g]}"][mascara[g]]

    candidatas = ["rrf_cobertura"] + [f"{fam}|LOGO" for fam in FAMILIAS]
    res = {"n": {g: int(mascara[g].sum()) for g in GRUPOS}, "n_total": len(consultas),
           "parametros_elegidos": elegida, "ndcg": {}, "estadistica": {}}
    alcances = {"total": np.ones(len(consultas), bool),
                "total_sin_dificiles": grupo != "dificiles_ab", **mascara}
    for alc, m in alcances.items():
        res["ndcg"][alc] = {k: float(V[k][m].mean()) for k in ["bm25", "C2_denso", "C4_rrf60", *candidatas]}
        est = {}
        for ref_ in ("C4_rrf60", "C2_denso"):
            comps = {c: comparar(V[c][m], V[ref_][m]) for c in candidatas}
            for c in candidatas:
                comps[c]["ic95_bootstrap_objetivo"] = boot_cluster(V[c][m] - V[ref_][m], list(objetivo[m]))
            ph = holm({c: v["p_valor"] for c, v in comps.items()})
            pp = holm({c: v["p_permutacion"] for c, v in comps.items()})
            for c, v in comps.items():
                v["p_holm"], v["p_holm_permutacion"] = ph[c], pp[c]
                v["concordante"] = bool(ph[c] is not None and pp[c] is not None and ph[c] < .05 and pp[c] < .05)
            est[f"vs_{ref_}"] = comps
        res["estadistica"][alc] = est

    res["por_consulta"] = {k: {qid: float(V[k][i]) for i, (_, qid, _, _) in enumerate(consultas)}
                           for k in ["bm25", "C2_denso", "C4_rrf60", *candidatas]}
    (RAIZ / "resultados" / "fusion_v3.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    L = ["# Fusión adaptativa sobre el corpus v3 (811 documentos)", "",
         f"{len(consultas)} consultas en seis grupos. nDCG@10; entre paréntesis, diferencia frente a C4 y frente a C2 "
         "(`*` = concordante: Wilcoxon y permutación rechazan tras Holm).", "",
         "| Alcance | n | BM25 | C2 denso | C4 RRF | " + " | ".join(candidatas) + " |",
         "|---|---|---|---|---|" + "---|" * len(candidatas)]
    for alc, m in alcances.items():
        r, e = res["ndcg"][alc], res["estadistica"][alc]
        def celda(c):
            a, b = e["vs_C4_rrf60"][c], e["vs_C2_denso"][c]
            return (f"{r[c]:.3f} ({a['media_dif']:+.3f}{'*' if a['concordante'] else ''}; "
                    f"{b['media_dif']:+.3f}{'*' if b['concordante'] else ''})")
        L.append(f"| {alc} | {int(m.sum())} | {r['bm25']:.3f} | {r['C2_denso']:.3f} | {r['C4_rrf60']:.3f} | "
                 + " | ".join(celda(c) for c in candidatas) + " |")
    L += ["", "Parámetros elegidos por leave-one-group-out:", ""]
    for fam, d in elegida.items():
        L.append(f"- {fam}: " + ", ".join(f"{g}={p}" for g, p in d.items()))
    (RAIZ / "resultados" / "fusion_v3.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
