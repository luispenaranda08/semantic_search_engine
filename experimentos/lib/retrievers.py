#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Las cinco configuraciones de la escalera de ablación.

Cada configuración es una forma de puntuar los documentos frente a una consulta:

  1. Denso puro                         s_dense(q, d_desc)
  2. Denso + ontología                  s_dense(q, d')            d' = d_desc ⊕ φ(o_d)
  3. Híbrido BM25 + denso (sin onto)     s_RRF(BM25_desc, denso_desc)   <- base crítica
  4. Híbrido + ontología                 s_RRF(BM25_onto, denso_onto)
  5. Híbrido + ontología + realce        s_final = s_RRF · (1 + λ·1_entidad)

Además se expone BM25 solo (referencia léxica) para responder P1. El motor construye
los índices una vez y responde cualquier configuración para cualquier consulta.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Mapping, Sequence

from .encoders import Encoder
from .indexes import BM25Index, DenseIndex

CONFIGS = {
    1: "Denso puro",
    2: "Denso + ontología",
    3: "Híbrido (sin ontología)",
    4: "Híbrido + ontología",
    5: "Híbrido + ontología + realce",
}
CONFIG_BM25 = 0
NOMBRE_BM25 = "BM25 (referencia léxica)"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def rrf(lista_a: Sequence[tuple[str, float]], lista_b: Sequence[tuple[str, float]],
        k: int = 60) -> tuple[list[str], dict[str, float]]:
    """Reciprocal Rank Fusion de dos rankings; devuelve (doc_ids ordenados, scores).

    Un documento ausente de una lista (p. ej. sin ningún término de la consulta en BM25)
    no recibe aporte de esa lista: RRF(d) = sum_{listas que contienen d} 1/(k + rango).
    El orden y el desempate son deterministas (por doc_id), para que el resultado sea
    reproducible entre procesos con independencia de la aleatorización de hash de Python.
    """
    fusion: dict[str, float] = {}
    for lista in (lista_a, lista_b):
        for i, (doc, _) in enumerate(lista):
            fusion[doc] = fusion.get(doc, 0.0) + 1.0 / (k + i + 1)
    orden = sorted(fusion, key=lambda d: (-fusion[d], d))   # desempate por doc_id
    return orden, fusion


class DetectorEntidades:
    """Detecta qué clases de entidad menciona una consulta, según la ontología.

    La coincidencia es por palabra completa (no por subcadena: "etapa" no debe activarse
    dentro de "etapas" por accidente ni "grupo" dentro de "agrupa"; se toleran plurales
    con -s/-es). El heurístico de nombre propio descarta las palabras capitalizadas que
    pertenecen al vocabulario del dominio (títulos del corpus y términos de la ontología),
    para que "Caribe", "Región" o "Única" no se confundan con el nombre de una persona.
    """

    def __init__(self, ontologia: dict, vocabulario_dominio: Sequence[str] = ()) -> None:
        self._terminos: list[tuple[re.Pattern, str]] = []
        vocab: set[str] = set()
        for clase, cuerpo in ontologia.get("clases", {}).items():
            for termino in [clase, *cuerpo.get("sinonimos", [])]:
                t = _norm(termino).strip()
                if t:
                    self._terminos.append(
                        (re.compile(r"\b" + re.escape(t) + r"(?:e?s)?\b"), clase))
                    vocab.update(re.findall(r"[a-z0-9]+", t))
        for texto in vocabulario_dominio:
            vocab.update(re.findall(r"[a-z0-9]+", _norm(texto)))
        self._vocab = vocab
        self._patron_propio = re.compile(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b")

    def clases_en(self, consulta: str) -> set[str]:
        cq = _norm(consulta)
        return {clase for patron, clase in self._terminos if patron.search(cq)}

    def tiene_nombre_propio(self, consulta: str) -> bool:
        """Heurística: una palabra capitalizada que no abre la consulta ni es del dominio."""
        tokens = self._patron_propio.findall(consulta)
        primera = consulta.strip().split()[:1]
        candidatos = [t for t in tokens if not (primera and t == primera[0])]
        return any(_norm(t) not in self._vocab for t in candidatos)


class MotorRecuperacion:
    """Construye los índices una vez y responde cualquiera de las configuraciones."""

    def __init__(self, docs: list[dict], encoder: Encoder, ontologia: dict,
                 k1: float, b: float, k_rrf: int, lambda_realce: float) -> None:
        self.docs = docs
        self.doc_ids = [d["id"] for d in docs]
        self.k_rrf = k_rrf
        self.lambda_realce = lambda_realce
        self._detector = DetectorEntidades(ontologia, [d.get("titulo", "") for d in docs])
        self._entidades_doc: dict[str, set[str]] = {
            d["id"]: set(d["metadatos_ontologia"].get("entidades_principales", [])) for d in docs}
        self._nombre_propio_doc: dict[str, bool] = {
            d["id"]: bool(d.get("nombre_propio_buscable", False)) for d in docs}

        desc = [d["descripcion"] for d in docs]
        onto = [d["texto_indexable"] for d in docs]
        self._bm25_desc = BM25Index(k1, b).indexar(self.doc_ids, desc)
        self._bm25_onto = BM25Index(k1, b).indexar(self.doc_ids, onto)
        self._dense_desc = DenseIndex(encoder).indexar(self.doc_ids, desc)
        self._dense_onto = DenseIndex(encoder).indexar(self.doc_ids, onto)

    # -- indicador de entidad para el realce suave (config 5) --
    def _indicador_entidad(self, consulta: str, doc_id: str) -> int:
        clases_q = self._detector.clases_en(consulta)
        if clases_q & self._entidades_doc.get(doc_id, set()):
            return 1
        if self._detector.tiene_nombre_propio(consulta) and self._nombre_propio_doc.get(doc_id):
            return 1
        return 0

    def recuperar(self, config: int, consulta: str) -> list[str]:
        """Devuelve la lista de doc_ids ordenada según la configuración indicada."""
        if config == CONFIG_BM25:
            return [d for d, _ in self._bm25_desc.buscar(consulta)]
        if config == 1:
            return [d for d, _ in self._dense_desc.buscar(consulta)]
        if config == 2:
            return [d for d, _ in self._dense_onto.buscar(consulta)]
        if config == 3:
            orden, _ = rrf(self._bm25_desc.buscar(consulta),
                           self._dense_desc.buscar(consulta), self.k_rrf)
            return orden
        if config == 4:
            orden, _ = rrf(self._bm25_onto.buscar(consulta),
                           self._dense_onto.buscar(consulta), self.k_rrf)
            return orden
        if config == 5:
            _, fusion = rrf(self._bm25_onto.buscar(consulta),
                            self._dense_onto.buscar(consulta), self.k_rrf)
            final = {d: s * (1 + self.lambda_realce * self._indicador_entidad(consulta, d))
                     for d, s in fusion.items()}
            return sorted(final, key=lambda d: (-final[d], d))   # desempate determinista
        raise ValueError(f"Configuración desconocida: {config}")
