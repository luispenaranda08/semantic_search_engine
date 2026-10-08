#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Banco de experimentos: carga de conjuntos, encoder con caché y puntuaciones crudas por consulta.

Los experimentos que NO son la escalera estándar (fusión alternativa, ontología completa,
análisis de errores) necesitan las puntuaciones crudas de BM25 y del denso para recombinarlas de
otras maneras. `Puntuaciones` las calcula una vez por (consulta, variante de documento) y las
reutiliza; el codificador se invoca una sola vez por texto.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from . import metrics as M
from .encoders import construir_encoder
from .indexes import BM25Index, DenseIndex, tokenizar_es

RAIZ = Path(__file__).resolve().parent.parent

CONJUNTOS = {
    "sintetico": ("datos/consultas_eval.jsonl", "datos/qrels.jsonl"),
    "ampliado": ("datos/consultas_real_ampliado.jsonl", "datos/qrels_real_ampliado.jsonl"),
    "dificil": ("datos/consultas_dificil.jsonl", "datos/qrels_dificil.jsonl"),
    "dificil_b": ("datos/consultas_dificil_b.jsonl", "datos/qrels_dificil_b.jsonl"),
}


def cargar_jsonl(ruta) -> list[dict]:
    return [json.loads(l) for l in Path(ruta).read_text(encoding="utf-8").splitlines() if l.strip()]


def cargar_conjunto(nombre: str):
    """(consultas con juicio, qrels) del conjunto `nombre`."""
    cq, qr = CONJUNTOS[nombre]
    qrels = {r["id"]: r["relevancia"] for r in cargar_jsonl(RAIZ / qr)}
    cons = [c for c in cargar_jsonl(RAIZ / cq) if M.tiene_gold(qrels.get(c["id"], {}))]
    return cons, qrels


def cargar_config() -> dict:
    return yaml.safe_load((RAIZ / "config.yaml").read_text(encoding="utf-8"))


class EncoderCacheado:
    """Calcula una vez el vector de cada texto (consulta o pasaje) y lo reutiliza."""

    def __init__(self, base) -> None:
        self.base = base
        self.dim = base.dim
        self.nombre = base.nombre
        self._c: dict = {}

    def _vecs(self, tipo, textos):
        faltan = [t for t in dict.fromkeys(textos) if (tipo, t) not in self._c]
        if faltan:
            f = self.base.encode_consultas if tipo == "q" else self.base.encode_documentos
            for t, v in zip(faltan, f(faltan)):
                self._c[(tipo, t)] = v
        return np.vstack([self._c[(tipo, t)] for t in textos])

    def encode_consultas(self, textos):
        return self._vecs("q", list(textos))

    def encode_documentos(self, textos):
        return self._vecs("d", list(textos))

    encode = encode_consultas


class Puntuaciones:
    """Puntuaciones crudas BM25 y densas para una variante de texto de documento.

    `textos`: dict doc_id -> texto a indexar (p. ej. la descripción, o el texto enriquecido).
    """

    def __init__(self, textos: dict[str, str], enc: EncoderCacheado, k1: float, b: float) -> None:
        self.ids = list(textos)
        self.bm25 = BM25Index(k1, b).indexar(self.ids, [textos[i] for i in self.ids])
        self.denso = DenseIndex(enc).indexar(self.ids, [textos[i] for i in self.ids])
        self._cb: dict = {}
        self._cd: dict = {}

    def puntaje_bm25(self, q: str) -> dict[str, float]:
        if q not in self._cb:
            self._cb[q] = dict(self.bm25.buscar(q))      # solo documentos con score > 0
        return self._cb[q]

    def puntaje_denso(self, q: str) -> dict[str, float]:
        if q not in self._cd:
            self._cd[q] = dict(self.denso.buscar(q))
        return self._cd[q]

    def cobertura_lexica(self, q: str) -> float:
        """Fracción de las raíces de la consulta presentes en el mejor documento de BM25 (0 si BM25 no devuelve nada)."""
        s = self.puntaje_bm25(q)
        qs = set(tokenizar_es(q))
        if not s or not qs:
            return 0.0
        mejor = max(s, key=lambda d: (s[d], d))
        tf = self.bm25._tf[self.bm25._doc_ids.index(mejor)]
        return len(qs & set(tf)) / len(qs)


def ranking(puntajes: dict[str, float], ids: list[str]) -> list[str]:
    """Orden descendente por puntaje; desempate por doc_id; los ausentes van al final por doc_id."""
    return sorted(ids, key=lambda d: (-puntajes.get(d, float("-inf")), d))


def ndcg_consultas(rank_fn, consultas, qrels, k: int = 10) -> list[float]:
    return [M.ndcg(rank_fn(c["texto"]), qrels[c["id"]], k) for c in consultas]
