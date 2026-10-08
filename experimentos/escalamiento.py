#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Costo de búsqueda y memoria del índice denso al crecer el corpus (búsqueda exacta por fuerza bruta).

Qué mide y qué NO. Mide el tiempo de un producto matriz–vector sobre N vectores de dimensión m
(+ selección del top-10) y la memoria que ocupa la matriz, con vectores ALEATORIOS normalizados de
la forma real de los embeddings. NO mide calidad (los vectores no tienen significado) ni incluye el
tiempo de codificar la consulta con el modelo (≈ 349 ms, medido en barridos.py, que en este corpus
domina). Su finalidad es acotar a partir de qué tamaño de corpus la búsqueda exacta deja de ser
despreciable y cuánto aporta truncar la dimensión Matryoshka a la memoria y al tiempo. Es una
medida dependiente del equipo; se reporta el modelo de CPU/memoria.

Uso: python3 escalamiento.py -> resultados/escalamiento.json y .md
"""
from __future__ import annotations

import json
import platform
import subprocess
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
TAMANOS = [10**3, 10**4, 10**5, 2 * 10**5]
DIMS = [64, 256, 1024]
CONSULTAS = 60


def main() -> None:
    rng = np.random.default_rng(42)
    try:
        cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
    except Exception:
        cpu = platform.processor()
    res = {"equipo": {"cpu": cpu or platform.processor(), "so": platform.platform(), "numpy": np.__version__},
           "consultas_por_celda": CONSULTAS, "celdas": []}
    for m in DIMS:
        for n in TAMANOS:
            mat = rng.standard_normal((n, m)).astype(np.float32)
            mat /= np.linalg.norm(mat, axis=1, keepdims=True)
            qs = rng.standard_normal((CONSULTAS, m)).astype(np.float32)
            qs /= np.linalg.norm(qs, axis=1, keepdims=True)
            _ = mat @ qs[0]                                  # calentamiento
            t = []
            for q in qs:
                t0 = time.perf_counter()
                s = mat @ q
                top = np.argpartition(-s, 10)[:10] if n > 10 else np.arange(n)
                top[np.argsort(-s[top])]
                t.append((time.perf_counter() - t0) * 1000)
            res["celdas"].append({"N": n, "m": m, "indice_MiB": n * m * 4 / 2**20,
                                  "p50_ms": float(np.percentile(t, 50)), "p95_ms": float(np.percentile(t, 95))})
            print(f"N={n:>7} m={m:>4} {n*m*4/2**20:8.1f} MiB  p50={np.percentile(t,50):7.3f} ms")
            del mat
    (RAIZ / "resultados/escalamiento.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    L = ["# Escalamiento de la búsqueda exacta", "", f"Equipo: {res['equipo']['cpu']} · {res['equipo']['so']}. Vectores aleatorios; "
         "no mide calidad ni la codificación de la consulta (≈ 349 ms).", "",
         "| N | " + " | ".join(f"m={m}: MiB / p50 ms" for m in DIMS) + " |", "|---|" + "---|" * len(DIMS)]
    for n in TAMANOS:
        fila = []
        for m in DIMS:
            c = next(x for x in res["celdas"] if x["N"] == n and x["m"] == m)
            fila.append(f"{c['indice_MiB']:.1f} / {c['p50_ms']:.2f}")
        L.append(f"| {n:,} | " + " | ".join(fila) + " |")
    (RAIZ / "resultados/escalamiento.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
