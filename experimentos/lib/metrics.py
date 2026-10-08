#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Métricas de recuperación de información.

Todas operan sobre una lista ordenada de identificadores de documento (el ranking
que devuelve el recuperador) y un diccionario de relevancia graduada
`qrel: doc_id -> grado` (0 = irrelevante). Un documento ausente de `qrel` se trata
como grado 0. Las funciones son puras y están cubiertas por un auto-test en
`__main__` para poder verificarlas sin infraestructura externa.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence


def _grado(qrel: Mapping[str, float], doc: str) -> float:
    return float(qrel.get(doc, 0.0))


def dcg(ranking: Sequence[str], qrel: Mapping[str, float], k: int) -> float:
    """Discounted Cumulative Gain con ganancia exponencial (2^rel - 1)."""
    total = 0.0
    for i, doc in enumerate(ranking[:k], start=1):
        g = _grado(qrel, doc)
        if g > 0:
            total += (2.0 ** g - 1.0) / math.log2(i + 1)
    return total


def ndcg(ranking: Sequence[str], qrel: Mapping[str, float], k: int) -> float:
    """nDCG@k. Vale 0 si la consulta no tiene ningún documento relevante."""
    ideal = sorted((g for g in qrel.values() if g > 0), reverse=True)
    idcg = sum((2.0 ** g - 1.0) / math.log2(i + 1) for i, g in enumerate(ideal[:k], start=1))
    if idcg == 0:
        return 0.0
    return dcg(ranking, qrel, k) / idcg


def recall(ranking: Sequence[str], qrel: Mapping[str, float], k: int) -> float:
    """Fracción de documentos relevantes recuperados en el top-k."""
    relevantes = {d for d, g in qrel.items() if g > 0}
    if not relevantes:
        return 0.0
    encontrados = sum(1 for d in ranking[:k] if d in relevantes)
    return encontrados / len(relevantes)


def mrr(ranking: Sequence[str], qrel: Mapping[str, float], k: int) -> float:
    """Reciprocal Rank del primer documento relevante dentro del top-k."""
    for i, doc in enumerate(ranking[:k], start=1):
        if _grado(qrel, doc) > 0:
            return 1.0 / i
    return 0.0


def precision(ranking: Sequence[str], qrel: Mapping[str, float], k: int) -> float:
    """Precisión@k."""
    if k == 0:
        return 0.0
    return sum(1 for d in ranking[:k] if _grado(qrel, d) > 0) / k


def average_precision(ranking: Sequence[str], qrel: Mapping[str, float], k: int) -> float:
    """Average Precision hasta el corte k (base de MAP)."""
    relevantes = {d for d, g in qrel.items() if g > 0}
    if not relevantes:
        return 0.0
    aciertos = 0
    suma = 0.0
    for i, doc in enumerate(ranking[:k], start=1):
        if doc in relevantes:
            aciertos += 1
            suma += aciertos / i
    return suma / min(len(relevantes), k)


def tiene_gold(qrel: Mapping[str, float]) -> bool:
    """True si la consulta tiene al menos un documento relevante (grado > 0)."""
    return any(g > 0 for g in qrel.values())


# --------------------------------------------------------------------------- #
def _autotest() -> None:
    # Ranking perfecto: el único relevante está en la posición 1.
    qrel = {"a": 1.0}
    assert ndcg(["a", "b", "c"], qrel, 10) == 1.0
    assert mrr(["a", "b", "c"], qrel, 10) == 1.0
    assert recall(["a", "b", "c"], qrel, 10) == 1.0
    assert precision(["a", "b", "c"], qrel, 1) == 1.0

    # Relevante en posición 2: nDCG = 1/log2(3) / 1 (idcg con el ideal en pos 1).
    val = ndcg(["b", "a", "c"], qrel, 10)
    assert abs(val - (1.0 / math.log2(3))) < 1e-9, val
    assert mrr(["b", "a", "c"], qrel, 10) == 0.5

    # Sin documentos relevantes: todo 0.
    assert ndcg(["a", "b"], {}, 10) == 0.0
    assert not tiene_gold({"x": 0.0})

    # Relevancia graduada: dos relevantes con grados 2 y 1.
    qg = {"a": 2.0, "b": 1.0}
    r = ndcg(["a", "b", "c"], qg, 10)
    assert abs(r - 1.0) < 1e-9, r
    assert abs(average_precision(["a", "b"], qg, 10) - 1.0) < 1e-9

    # Recall parcial.
    assert recall(["a", "x"], {"a": 1.0, "b": 1.0}, 10) == 0.5
    print("metrics.py: auto-test OK")


if __name__ == "__main__":
    _autotest()
