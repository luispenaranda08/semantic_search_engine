#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Robustez de las comparaciones frente a la dependencia por reporte, y dosis-respuesta de la ontología.

Las consultas de un mismo reporte objetivo no son independientes (comparten documento, vocabulario
y redactor). Este análisis, que solo relee los resultados por consulta ya guardados (no carga el
modelo), reporta para cada comparación de la escalera:
  * IC 95 % por bootstrap POR REPORTE (se remuestrean reportes, no consultas; 2.000 réplicas);
  * dejar un reporte fuera: rango de la diferencia media y número de cambios de signo;
  * número de reportes que aportan consultas.
Y, para los conjuntos difíciles, la relación entre el número de raíces que la consulta comparte con el
bloque de ontología del objetivo y la ganancia de la ontología (dosis-respuesta, Spearman).

Uso: python3 analisis_robustez.py -> resultados/robustez.json y .md
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy import stats as sp

RAIZ = Path(__file__).resolve().parent
N = {"BM25": "BM25 (referencia léxica)", "C1": "Denso puro", "C2": "Denso + ontología",
     "C3": "Híbrido (sin ontología)", "C4": "Híbrido + ontología", "C5": "Híbrido + ontología + realce"}
COMP = [("C3", "BM25"), ("C3", "C1"), ("C2", "C1"), ("C4", "C3"), ("C5", "C4"), ("C4", "C2")]
CONJ = {
    "ampliado (17 docs)": ("resultados/resultados_real_ampliado_v1.json", "datos/qrels_real_ampliado.jsonl", None),
    "difíciles A+B (17 docs)": ("resultados/resultados_dificil_ab_v1.json", "datos/qrels_dificil_ab.jsonl", "datos/consultas_dificil_ab.jsonl"),
    "definitivo (177 docs)": ("resultados/resultados_final.json", "datos/qrels_final.jsonl", None),
    "difíciles A+B (177 docs)": ("resultados/resultados_final_dificil_ab.json", "datos/qrels_dificil_ab.jsonl", "datos/consultas_dificil_ab.jsonl"),
}


def jl(r):
    return [json.loads(l) for l in (RAIZ / r).read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    rng = np.random.default_rng(42)
    out = {}
    for cn, (res, qr, cq) in CONJ.items():
        d = json.loads((RAIZ / res).read_text(encoding="utf-8"))
        por = d["por_consulta"]
        qrels = {r["id"]: r["relevancia"] for r in jl(qr)}
        ids = list(por[N["C1"]])
        # grupo = reporte objetivo (para consultas con varios relevantes: el de mayor grado, desempate por id)
        grupo = {i: sorted(qrels[i].items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for i in ids}
        reps = sorted(set(grupo.values()))
        o = {"n_consultas": len(ids), "n_grupos": len(reps), "comparaciones": {}}
        for a, b in COMP:
            dif = {i: por[N[a]][i]["ndcg@10"] - por[N[b]][i]["ndcg@10"] for i in ids}
            por_g = defaultdict(list)
            for i in ids:
                por_g[grupo[i]].append(dif[i])
            media = float(np.mean(list(dif.values())))
            boots = []
            for _ in range(2000):
                muestra = rng.choice(reps, size=len(reps), replace=True)
                vals = [x for g in muestra for x in por_g[g]]
                boots.append(np.mean(vals))
            lo, hi = np.percentile(boots, [2.5, 97.5])
            loo = [float(np.mean([dif[i] for i in ids if grupo[i] != g])) for g in reps]
            o["comparaciones"][f"{a}-{b}"] = {
                "delta": media, "ic95_bootstrap_reporte": [float(lo), float(hi)],
                "excluye_cero": bool(lo > 0 or hi < 0),
                "loo_min": min(loo), "loo_max": max(loo),
                "loo_cambios_signo": int(sum(1 for x in loo if np.sign(x) != np.sign(media) and abs(x) > 1e-12))}
        if cq:
            cons = {c["id"]: c for c in jl(cq)}
            xs = [len(cons[i].get("solape_onto", [])) for i in ids]
            for a, b in (("C2", "C1"), ("C4", "C3")):
                ys = [por[N[a]][i]["ndcg@10"] - por[N[b]][i]["ndcg@10"] for i in ids]
                rho, p = sp.spearmanr(xs, ys)
                tramos = {}
                for k, lab in ((0, "0"), (1, "1"), (2, "2 o más")):
                    sel = [y for x, y in zip(xs, ys) if (x == k if k < 2 else x >= 2)]
                    tramos[lab] = {"n": len(sel), "delta": float(np.mean(sel)) if sel else None}
                o.setdefault("dosis_respuesta", {})[f"{a}-{b}"] = {"spearman_rho": float(rho), "p": float(p), "tramos": tramos}
        out[cn] = o
        print(f"[robustez] {cn} listo")
    (RAIZ / "resultados/robustez.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    L = ["# Robustez por reporte y dosis-respuesta", ""]
    for cn, o in out.items():
        L += [f"## {cn} ({o['n_consultas']} consultas, {o['n_grupos']} reportes o pruebas objetivo)", "",
              "| Comparación | Δ | IC95 bootstrap por reporte | excluye 0 | dejar uno fuera: mín / máx | cambios de signo |", "|---|---|---|---|---|---|"]
        for k, v in o["comparaciones"].items():
            L.append(f"| {k} | {v['delta']:+.3f} | [{v['ic95_bootstrap_reporte'][0]:+.3f}, {v['ic95_bootstrap_reporte'][1]:+.3f}] | "
                     f"{'sí' if v['excluye_cero'] else 'no'} | {v['loo_min']:+.3f} / {v['loo_max']:+.3f} | {v['loo_cambios_signo']} |")
        if "dosis_respuesta" in o:
            L += ["", "Dosis-respuesta (raíces compartidas con el bloque de ontología):", ""]
            for k, v in o["dosis_respuesta"].items():
                tr = "; ".join(f"{t}: Δ={x['delta']:+.3f} (n={x['n']})" for t, x in v["tramos"].items() if x["delta"] is not None)
                L.append(f"- {k}: rho de Spearman = {v['spearman_rho']:+.3f} (p = {v['p']:.4f}); {tr}")
        L.append("")
    (RAIZ / "resultados/robustez.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
