#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Funciones de fusión de las señales léxica (BM25) y densa.

RRF (Cormack et al. 2009) es la fusión de la escalera: opera sobre rangos y no necesita
etiquetas. Bruch, Gai e Ingber (2024) muestran que una combinación CONVEXA de puntuaciones
normalizadas suele superarla, pero exige calibrar el peso con juicios de relevancia. Aquí se
implementan variantes para medirlo: RRF ponderado, convexa con normalización min–max o z-score, y
una fusión con compuerta que descarta la señal léxica cuando su cobertura de la consulta es baja
(el mecanismo por el que RRF arrastra al denso cuando la consulta no comparte vocabulario).

Todas devuelven un dict doc_id -> puntaje de fusión; `banco.ranking` lo convierte en orden.
"""
from __future__ import annotations

import numpy as np


def _rangos(puntajes: dict[str, float]) -> dict[str, int]:
    orden = sorted(puntajes, key=lambda d: (-puntajes[d], d))
    return {d: i + 1 for i, d in enumerate(orden)}


def rrf(bm25: dict[str, float], denso: dict[str, float], k: int = 60,
        w_denso: float = 1.0, w_bm25: float = 1.0) -> dict[str, float]:
    """RRF ponderado. Un documento ausente de una lista no recibe aporte de ella."""
    out: dict[str, float] = {}
    for lista, w in ((bm25, w_bm25), (denso, w_denso)):
        for d, r in _rangos(lista).items():
            out[d] = out.get(d, 0.0) + w / (k + r)
    return out


def _norm(puntajes: dict[str, float], ids: list[str], modo: str) -> dict[str, float]:
    v = np.array([puntajes.get(d, 0.0) for d in ids], dtype=float)
    if modo == "minmax":
        lo, hi = v.min(), v.max()
        z = np.zeros_like(v) if hi - lo < 1e-12 else (v - lo) / (hi - lo)
    elif modo == "z":
        s = v.std()
        z = np.zeros_like(v) if s < 1e-12 else (v - v.mean()) / s
    else:
        raise ValueError(modo)
    return dict(zip(ids, z))


def convexa(bm25: dict[str, float], denso: dict[str, float], ids: list[str],
            alpha: float, modo: str = "minmax") -> dict[str, float]:
    """alpha · densa_normalizada + (1 − alpha) · BM25_normalizada (BM25 ausente = 0 antes de normalizar)."""
    nd, nb = _norm(denso, ids, modo), _norm(bm25, ids, modo)
    return {d: alpha * nd[d] + (1 - alpha) * nb[d] for d in ids}


def rrf_compuerta(bm25: dict[str, float], denso: dict[str, float], cobertura: float,
                  theta: float, k: int = 60) -> dict[str, float]:
    """RRF solo si la cobertura léxica de la consulta alcanza `theta`; si no, orden denso puro."""
    if cobertura >= theta:
        return rrf(bm25, denso, k)
    return dict(denso)
