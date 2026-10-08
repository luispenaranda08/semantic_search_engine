#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Acuerdo entre anotadores y consolidación de qrels gold.

Lee hoja_anotador_A.csv y hoja_anotador_B.csv ya rellenas (columna `grado` en {0,1,2}) y calcula:
  * porcentaje de acuerdo exacto,
  * kappa de Cohen sin ponderar y con ponderación lineal (la escala es ordinal: confundir 0 con
    2 es peor que confundir 0 con 1),
  * matriz de confusión,
  * lista de desacuerdos para la reunión de adjudicación.
Con `--adjudicacion archivo.csv` (columnas qid,doc_id,grado_final) escribe datos/qrels_gold.jsonl;
los pares sin desacuerdo toman el grado común. Interpretación de kappa (Landis y Koch, 1977):
<0,20 pobre; 0,21–0,40 débil; 0,41–0,60 moderado; 0,61–0,80 sustancial; >0,80 casi perfecto.

Uso:  python3 anotacion/calcular_kappa.py [--adjudicacion adj.csv]
      python3 anotacion/calcular_kappa.py --autotest
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
ESCALA = (0, 1, 2)


def kappa(a: list[int], b: list[int], ponderado: str | None = None) -> float:
    """Kappa de Cohen; ponderado in {None, 'lineal'}."""
    k = len(ESCALA)
    n = len(a)
    obs = np.zeros((k, k))
    for x, y in zip(a, b):
        obs[ESCALA.index(x), ESCALA.index(y)] += 1
    obs /= n
    esp = np.outer(obs.sum(1), obs.sum(0))
    if ponderado == "lineal":
        w = np.array([[abs(i - j) / (k - 1) for j in range(k)] for i in range(k)])
    else:
        w = 1.0 - np.eye(k)
    den = (w * esp).sum()
    return float("nan") if den == 0 else float(1.0 - (w * obs).sum() / den)


def leer(ruta: Path) -> dict[tuple[str, str], int]:
    out = {}
    with ruta.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            g = r["grado"].strip()
            if g == "":
                raise SystemExit(f"{ruta.name}: fila sin grado ({r['qid']}, {r['doc_id']})")
            if int(g) not in ESCALA:
                raise SystemExit(f"{ruta.name}: grado fuera de escala {g!r}")
            out[(r["qid"], r["doc_id"])] = int(g)
    return out


def autotest() -> None:
    a = [0, 1, 2, 0, 1, 2, 0, 0, 1, 2]
    assert abs(kappa(a, a) - 1.0) < 1e-12 and abs(kappa(a, a, "lineal") - 1.0) < 1e-12
    # 2x2 verificable a mano: celdas 20/5/10/15 (n=50) -> po = 0,7; marginales 25/25 y 30/20 ->
    # pe = (25·30 + 25·20)/2500 = 0,5 -> kappa = (0,7-0,5)/(1-0,5) = 0,4
    x = [0] * 20 + [0] * 5 + [1] * 10 + [1] * 15
    y = [0] * 20 + [1] * 5 + [0] * 10 + [1] * 15
    assert abs(kappa(x, y) - 0.4) < 1e-12, kappa(x, y)
    # el ponderado castiga más 0↔2 que 0↔1
    p, q = [0, 0, 2, 2], [1, 1, 1, 1]
    r, s = [0, 0, 2, 2], [2, 2, 0, 0]
    assert kappa(p, q, "lineal") != kappa(r, s, "lineal")
    print("calcular_kappa.py: autotest OK")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adjudicacion")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    A, B = leer(AQUI / "hoja_anotador_A.csv"), leer(AQUI / "hoja_anotador_B.csv")
    if set(A) != set(B):
        raise SystemExit("Las hojas A y B no contienen los mismos pares.")
    pares = sorted(A)
    va, vb = [A[p] for p in pares], [B[p] for p in pares]
    conf = Counter(zip(va, vb))
    acuerdo = float(np.mean([x == y for x, y in zip(va, vb)]))
    res = {"n_pares": len(pares), "acuerdo_exacto": acuerdo,
           "kappa": kappa(va, vb), "kappa_ponderado_lineal": kappa(va, vb, "lineal"),
           "matriz_confusion_A_filas_B_columnas": [[conf[(i, j)] for j in ESCALA] for i in ESCALA]}
    print(json.dumps(res, indent=2))
    desacuerdos = [(q, d, A[(q, d)], B[(q, d)]) for q, d in pares if A[(q, d)] != B[(q, d)]]
    with (AQUI / "desacuerdos_para_adjudicar.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["qid", "doc_id", "grado_A", "grado_B", "grado_final"])
        w.writerows([(*d, "") for d in desacuerdos])
    print(f"{len(desacuerdos)} desacuerdos -> anotacion/desacuerdos_para_adjudicar.csv")
    if a.adjudicacion:
        final = {}
        with open(a.adjudicacion, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                final[(r["qid"], r["doc_id"])] = int(r["grado_final"])
        qrels: dict[str, dict[str, float]] = {}
        for (q, d) in pares:
            g = A[(q, d)] if A[(q, d)] == B[(q, d)] else final.get((q, d))
            if g is None:
                raise SystemExit(f"Falta adjudicar ({q}, {d})")
            if g > 0:
                qrels.setdefault(q, {})[d] = float(g)
            else:
                qrels.setdefault(q, {})
        with (RAIZ / "datos/qrels_gold.jsonl").open("w", encoding="utf-8") as f:
            for q, rel in qrels.items():
                f.write(json.dumps({"id": q, "relevancia": rel}, ensure_ascii=False) + "\n")
        print("Escrito datos/qrels_gold.jsonl")


if __name__ == "__main__":
    main()
