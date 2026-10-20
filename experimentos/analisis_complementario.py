#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Análisis complementarios pedidos por la revisión, sobre los resultados por consulta ya guardados.

  1. Contraste C1 (denso puro) frente a BM25: separa el aporte del codificador del de la fusión.
  2. Éxito en la posición 1, 3 y 5 (a partir del MRR@10: 1/rango del primer relevante).
  3. Efecto mínimo detectable (EMD) por comparación: 2,8 × sd(diferencias) / sqrt(n), que corresponde
     a alfa = 0,05 bilateral y potencia 0,8 con la aproximación normal de una prueba pareada.
  4. Metaanálisis de efectos fijos (varianza inversa) de los conjuntos difíciles A y B, en lugar de la
     unión cruda.
  5. nDCG@10 ponderado por la demanda real: cada consulta del conjunto ampliado pesa según la cuota de
     su reporte objetivo en las 6.620 consultas reales, repartida entre las consultas de ese reporte.
  6. Conjunto difícil B por registro de redacción.
No carga el modelo. Uso: python3 analisis_complementario.py -> resultados/complementario.json y .md
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from lib.stats import comparar

RAIZ = Path(__file__).resolve().parent
N = {"BM25": "BM25 (referencia léxica)", "C1": "Denso puro", "C2": "Denso + ontología",
     "C3": "Híbrido (sin ontología)", "C4": "Híbrido + ontología", "C5": "Híbrido + ontología + realce"}
SETS = {"ampliado": "resultados/resultados_real_ampliado_v1.json", "dificil_a": "resultados/resultados_dificil_v1.json",
        "dificil_b": "resultados/resultados_dificil_b_v1.json", "definitivo_177": "resultados/resultados_final.json",
        "dificiles_177": "resultados/resultados_final_dificil_ab.json"}
COMP = [("C1", "BM25"), ("C3", "BM25"), ("C3", "C1"), ("C2", "C1"), ("C4", "C3"), ("C5", "C4"), ("C4", "C2")]


def jl(r):
    return [json.loads(l) for l in (RAIZ / r).read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    D = {k: json.loads((RAIZ / v).read_text(encoding="utf-8")) for k, v in SETS.items()}
    out: dict = {"exito": {}, "comparaciones": {}, "emd": {}, "metaanalisis": {}, "ponderado_demanda": {}, "por_registro": {}}
    for k, d in D.items():
        por = d["por_consulta"]; ids = list(por[N["C1"]])
        out["exito"][k] = {c: {f"@{t}": float(np.mean([por[N[c]][i]["mrr@10"] >= 1 / t - 1e-12 for i in ids])) for t in (1, 3, 5)}
                           for c in N}
        out["comparaciones"][k] = {}
        out["emd"][k] = {}
        for a, b in COMP:
            x = [por[N[a]][i]["ndcg@10"] for i in ids]; y = [por[N[b]][i]["ndcg@10"] for i in ids]
            r = comparar(x, y)
            out["comparaciones"][k][f"{a}-{b}"] = {kk: r.get(kk) for kk in ("media_dif", "p_valor", "p_permutacion", "rank_biserial", "ic95_dif", "n_pares_no_nulos", "n")}
            dd = np.array(x) - np.array(y)
            out["emd"][k][f"{a}-{b}"] = float(2.8 * dd.std(ddof=1) / np.sqrt(len(dd)))
    # metaanálisis A y B
    for a, b in COMP:
        ests = []
        for k in ("dificil_a", "dificil_b"):
            por = D[k]["por_consulta"]; ids = list(por[N["C1"]])
            dd = np.array([por[N[a]][i]["ndcg@10"] - por[N[b]][i]["ndcg@10"] for i in ids])
            ests.append((dd.mean(), dd.std(ddof=1) / np.sqrt(len(dd))))
        w = [1 / se**2 if se > 0 else 0 for _, se in ests]
        if sum(w) == 0:
            continue
        m = sum(wi * e for wi, (e, _) in zip(w, ests)) / sum(w); se = (1 / sum(w)) ** 0.5
        q = sum(wi * (e - m) ** 2 for wi, (e, _) in zip(w, ests))
        out["metaanalisis"][f"{a}-{b}"] = {"A": ests[0][0], "B": ests[1][0], "combinado": float(m),
                                           "ic95": [float(m - 1.96 * se), float(m + 1.96 * se)], "Q_heterogeneidad": float(q)}
    # ponderado por demanda (ampliado)
    docs = {json.loads(l)["id"]: json.loads(l) for l in (RAIZ / "corpus/corpus_v1.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    qrels = {r["id"]: r["relevancia"] for r in jl("datos/qrels_real_ampliado.jsonl")}
    por = D["ampliado"]["por_consulta"]; ids = list(por[N["C1"]])
    tgt = {i: max(qrels[i], key=qrels[i].get) for i in ids}
    cnt = defaultdict(int)
    for i in ids: cnt[tgt[i]] += 1
    tot = sum(docs[t]["cdr"] for t in set(tgt.values()))
    w = {i: docs[tgt[i]]["cdr"] / tot / cnt[tgt[i]] for i in ids}
    out["ponderado_demanda"] = {c: {"ponderado": float(sum(w[i] * por[N[c]][i]["ndcg@10"] for i in ids) / sum(w.values())),
                                    "sin_ponderar": float(np.mean([por[N[c]][i]["ndcg@10"] for i in ids]))} for c in N}
    # difícil B por registro
    cons = {c["id"]: c for c in jl("datos/consultas_dificil_b.jsonl")}
    por = D["dificil_b"]["por_consulta"]
    regs = sorted({c["registro"] for c in cons.values()})
    out["por_registro"] = {r: {"n": sum(1 for c in cons.values() if c["registro"] == r),
                               **{c: float(np.mean([por[N[c]][i]["ndcg@10"] for i in cons if cons[i]["registro"] == r])) for c in N}} for r in regs}
    (RAIZ / "resultados/complementario.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    L = ["# Análisis complementarios", "", "## Éxito en la posición 1 / 3 / 5", ""]
    for k, e in out["exito"].items():
        L.append(f"**{k}**: " + "; ".join(f"{c} {v['@1']:.2f}/{v['@3']:.2f}/{v['@5']:.2f}" for c, v in e.items()))
    L += ["", "## Comparaciones (Δ, r biserial, IC95 bootstrap) y efecto mínimo detectable (EMD)", ""]
    for k, cc in out["comparaciones"].items():
        L.append(f"### {k}")
        for c, v in cc.items():
            ic = v["ic95_dif"]
            L.append(f"- {c}: Δ={v['media_dif']:+.3f}, r={v['rank_biserial'] if v['rank_biserial'] is None else round(v['rank_biserial'],2)}, IC95=[{ic[0]:+.3f},{ic[1]:+.3f}], p={v['p_valor']}, perm={v['p_permutacion']}, EMD={out['emd'][k][c]:.3f}")
    L += ["", "## Metaanálisis difícil A + B (efectos fijos)", ""]
    for c, v in out["metaanalisis"].items():
        L.append(f"- {c}: A {v['A']:+.3f}, B {v['B']:+.3f} → {v['combinado']:+.3f} [{v['ic95'][0]:+.3f}, {v['ic95'][1]:+.3f}], Q={v['Q_heterogeneidad']:.2f}")
    L += ["", "## nDCG@10 ponderado por demanda (ampliado)", ""]
    for c, v in out["ponderado_demanda"].items():
        L.append(f"- {c}: ponderado {v['ponderado']:.3f} (sin ponderar {v['sin_ponderar']:.3f})")
    L += ["", "## Difícil B por registro", ""]
    for r, v in out["por_registro"].items():
        L.append(f"- {r} (n={v['n']}): " + ", ".join(f"{c} {v[c]:.3f}" for c in N))
    (RAIZ / "resultados/complementario.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
