#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Análisis del corpus v3 (811 documentos, cinco tipos de objeto funcional). Sin modelo.

Lee los resultados por consulta de `eval_flexible.py` y, para el conjunto completo y para cada
estrato, contrasta las comparaciones que deciden la recomendación:

  * C4 − C2: ¿el híbrido con ontología supera al denso con ontología?
  * C3 − C1: efecto de añadir BM25 por RRF sin ontología;
  * C2 − C1 y C4 − C3: efecto de la ontología sobre cada recuperador.

Cada contraste lleva Wilcoxon y permutación pareados (Holm dentro de la familia de cuatro por
estrato) y un IC 95 % por bootstrap POR OBJETIVO: se remuestrean grupos de consultas que
comparten el mismo conjunto de relevantes, para no inflar la confianza con consultas hermanas.
Además compara el conjunto difícil A+B con 177 y con 811 documentos (efecto de la escala).

Uso:
    python3 analisis_v3.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from lib.stats import comparar, holm

RAIZ = Path(__file__).resolve().parent
RES = RAIZ / "resultados"
NOMBRES = {"BM25": "BM25 (referencia léxica)", "C1": "Denso puro", "C2": "Denso + ontología",
           "C3": "Híbrido (sin ontología)", "C4": "Híbrido + ontología",
           "C5": "Híbrido + ontología + realce"}
FAMILIA = [("C4−C2", "C4", "C2"), ("C3−C1", "C3", "C1"), ("C2−C1", "C2", "C1"), ("C4−C3", "C4", "C3")]


def jl(r: Path) -> list[dict]:
    return [json.loads(l) for l in r.read_text(encoding="utf-8").splitlines() if l.strip()]


def boot_cluster(dif: np.ndarray, grupos: list[str], n: int = 2000, semilla: int = 7) -> list[float]:
    por: dict[str, list[float]] = defaultdict(list)
    for d, g in zip(dif, grupos):
        por[g].append(d)
    claves = list(por)
    rng = np.random.default_rng(semilla)
    medias = []
    for _ in range(n):
        m = rng.choice(len(claves), len(claves), replace=True)
        vals = [x for i in m for x in por[claves[i]]]
        medias.append(float(np.mean(vals)))
    return [float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))]


def analizar(resultados: Path, consultas: Path, qrels: Path) -> dict:
    R = json.loads(resultados.read_text(encoding="utf-8"))
    pc = R["por_consulta"]
    cons = {c["id"]: c for c in jl(consultas)}
    objetivo = {q["id"]: "|".join(sorted(q["relevancia"])) for q in jl(qrels)}
    ids = [i for i in pc[NOMBRES["C1"]] if i in cons]
    estratos = {"global": ids}
    for i in ids:
        estratos.setdefault(cons[i].get("estrato", "sin_estrato"), []).append(i)

    salida = {}
    for est, sub in estratos.items():
        medias = {k: float(np.mean([pc[n][i]["ndcg@10"] for i in sub])) for k, n in NOMBRES.items()}
        comps = {}
        for etiqueta, a, b in FAMILIA:
            va = [pc[NOMBRES[a]][i]["ndcg@10"] for i in sub]
            vb = [pc[NOMBRES[b]][i]["ndcg@10"] for i in sub]
            c = comparar(va, vb)
            c["ic95_bootstrap_objetivo"] = boot_cluster(np.array(va) - np.array(vb),
                                                        [objetivo[i] for i in sub])
            c["media_dif"] = float(np.mean(np.array(va) - np.array(vb)))
            comps[etiqueta] = c
        ph = holm({k: v["p_valor"] for k, v in comps.items()})
        pp = holm({k: v["p_permutacion"] for k, v in comps.items()})
        for k, v in comps.items():
            v["p_holm"], v["p_holm_permutacion"] = ph[k], pp[k]
            v["concordante"] = bool(ph[k] is not None and pp[k] is not None and ph[k] < .05 and pp[k] < .05)
        salida[est] = {"n": len(sub), "n_objetivos": len({objetivo[i] for i in sub}),
                       "ndcg@10": medias, "comparaciones": comps}
    return salida


def main() -> None:
    final = {
        "v3_completo": analizar(RES / "resultados_v3.json", RAIZ / "datos" / "consultas_final_v3.jsonl",
                                RAIZ / "datos" / "qrels_final_v3.jsonl"),
        "v3_dificil_ab": analizar(RES / "resultados_v3_dificil_ab.json",
                                  RAIZ / "datos" / "consultas_dificil_ab.jsonl",
                                  RAIZ / "datos" / "qrels_dificil_ab.jsonl"),
    }
    escala = {}
    for etiqueta, ruta in (("177", RES / "resultados_final_dificil_ab.json"),
                           ("811", RES / "resultados_v3_dificil_ab.json")):
        g = json.loads(ruta.read_text(encoding="utf-8"))["global"]
        escala[etiqueta] = {k: g[n]["ndcg@10"] for k, n in NOMBRES.items()}
    final["escala_dificil_ab"] = escala
    (RES / "analisis_v3.json").write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    L = ["# Corpus v3: 811 documentos, cinco tipos de objeto funcional", ""]
    for conj in ("v3_completo", "v3_dificil_ab"):
        L += [f"## {conj}", "", "| Estrato | n | BM25 | C1 | C2 | C3 | C4 | C5 | C4−C2 [IC objetivo] | C3−C1 | C2−C1 |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for est, v in final[conj].items():
            m, c = v["ndcg@10"], v["comparaciones"]
            f = lambda k: f"{c[k]['media_dif']:+.3f}{'*' if c[k]['concordante'] else ''}"
            ic = c["C4−C2"]["ic95_bootstrap_objetivo"]
            L.append(f"| {est} | {v['n']} | " + " | ".join(f"{m[k]:.3f}" for k in NOMBRES) +
                     f" | {f('C4−C2')} [{ic[0]:+.3f}, {ic[1]:+.3f}] | {f('C3−C1')} | {f('C2−C1')} |")
        L.append("")
    L += ["`*` = concordante (Wilcoxon y permutación rechazan tras Holm).", "",
          "## Difícil A+B: 177 frente a 811 documentos", "",
          "| Documentos | " + " | ".join(NOMBRES) + " |", "|---|" + "---|" * len(NOMBRES)]
    for e, v in escala.items():
        L.append(f"| {e} | " + " | ".join(f"{v[k]:.3f}" for k in NOMBRES) + " |")
    (RES / "analisis_v3.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
