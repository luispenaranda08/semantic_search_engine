#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Índices de recuperación: léxico (BM25) y denso (coseno exacto).

BM25 se implementa desde cero (sin dependencias) para tener control total sobre el
analizador en español y sobre los parámetros k1 y b. El índice denso hace búsqueda
exacta por producto interno sobre vectores L2-normalizados, suficiente para un corpus
de decenas de documentos; para producción se sustituiría por un índice ANN (HNSW).
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Sequence

import numpy as np

import snowballstemmer

from .encoders import Encoder

_STOPWORDS_ES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "a", "ante",
    "con", "en", "para", "por", "que", "y", "o", "u", "se", "su", "sus", "lo", "al",
    "es", "son", "como", "mas", "mas", "pero", "sin", "sobre", "entre", "cada", "ya",
    "cuando", "donde", "cual", "quien", "cuanto", "muy", "este", "esta", "estos",
}


_STEMMER_ES = snowballstemmer.stemmer("spanish")


def tokenizar_es(texto: str, raiz: bool = True) -> list[str]:
    """Tokeniza en español: minúsculas, sin tildes, sin puntuación, sin stopwords y, por
    defecto, reducido a la raíz con Snowball ES (así "deportista" y "deportistas", o "fase"
    y "fases", cuentan como el mismo término)."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    tokens = [t for t in re.findall(r"[a-z0-9]+", texto) if t not in _STOPWORDS_ES and len(t) > 1]
    return _STEMMER_ES.stemWords(tokens) if raiz else tokens


class BM25Index:
    """Índice BM25 clásico con analizador en español."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._doc_ids: list[str] = []
        self._tf: list[Counter] = []
        self._len: list[int] = []
        self._avg_len: float = 0.0
        self._idf: dict[str, float] = {}

    def indexar(self, doc_ids: Sequence[str], textos: Sequence[str]) -> "BM25Index":
        self._doc_ids = list(doc_ids)
        self._tf = [Counter(tokenizar_es(t)) for t in textos]
        self._len = [sum(c.values()) for c in self._tf]
        self._avg_len = (sum(self._len) / len(self._len)) if self._len else 0.0
        df: Counter = Counter()
        for c in self._tf:
            df.update(c.keys())
        n = len(self._tf)
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        return self

    def buscar(self, consulta: str) -> list[tuple[str, float]]:
        """Devuelve [(doc_id, score)] de mayor a menor BM25, SOLO documentos con score > 0.

        Un documento sin ningún término de la consulta no es un resultado léxico: si se
        devolviera, su posición saldría del orden de indexación (el primer documento del
        corpus quedaría primero en todo empate a cero) y ese orden arbitrario entraría a
        la fusión RRF. Empates con score > 0 se resuelven por doc_id.
        """
        q = tokenizar_es(consulta)
        scores = np.zeros(len(self._doc_ids))
        for i, tf in enumerate(self._tf):
            s = 0.0
            for t in q:
                if t not in tf:
                    continue
                f = tf[t]
                denom = f + self.k1 * (1 - self.b + self.b * self._len[i] / (self._avg_len or 1))
                s += self._idf.get(t, 0.0) * f * (self.k1 + 1) / denom
            scores[i] = s
        orden = sorted((i for i in range(len(scores)) if scores[i] > 0),
                       key=lambda i: (-scores[i], self._doc_ids[i]))
        return [(self._doc_ids[i], float(scores[i])) for i in orden]


class DenseIndex:
    """Índice denso: producto interno exacto sobre vectores normalizados."""

    def __init__(self, encoder: Encoder) -> None:
        self.encoder = encoder
        self._doc_ids: list[str] = []
        self._mat: np.ndarray | None = None

    def indexar(self, doc_ids: Sequence[str], textos: Sequence[str]) -> "DenseIndex":
        self._doc_ids = list(doc_ids)
        self._mat = self.encoder.encode_documentos(textos)
        return self

    def buscar(self, consulta: str) -> list[tuple[str, float]]:
        if self._mat is None:
            raise RuntimeError("DenseIndex no indexado.")
        qv = self.encoder.encode_consultas([consulta])[0]
        scores = self._mat @ qv
        orden = sorted(range(len(scores)), key=lambda i: (-scores[i], self._doc_ids[i]))
        return [(self._doc_ids[i], float(scores[i])) for i in orden]
