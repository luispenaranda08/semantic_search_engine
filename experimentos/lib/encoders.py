#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Codificadores densos, enchufables tras una interfaz común.

Dos implementaciones:
  * SentenceTransformerEncoder: el modelo real (multilingüe con Matryoshka). Requiere
    descargar el modelo la primera vez. Soporta truncar la dimensión a `m` (MRL).
  * LSAEncoder: fallback offline y determinista (TF-IDF + SVD truncado, es decir,
    Latent Semantic Analysis). No requiere red ni GPU y permite correr el framework
    completo de punta a punta. Es un recuperador denso legítimo, aunque más débil que
    un transformer; se usa para validar la tubería y como línea de referencia offline.

El código de recuperación no sabe cuál está en uso: solo llama a `.encode(textos)`.
"""
from __future__ import annotations

from typing import Protocol, Sequence

import numpy as np


def _l2_normalizar(m: np.ndarray) -> np.ndarray:
    normas = np.linalg.norm(m, axis=1, keepdims=True)
    normas[normas == 0] = 1.0
    return m / normas


class Encoder(Protocol):
    """Interfaz mínima de un codificador de texto a vectores densos normalizados."""
    dim: int
    nombre: str

    def encode(self, textos: Sequence[str]) -> np.ndarray:
        ...

    def encode_consultas(self, textos: Sequence[str]) -> np.ndarray:
        ...

    def encode_documentos(self, textos: Sequence[str]) -> np.ndarray:
        ...


class LSAEncoder:
    """Codificador offline determinista: TF-IDF sobre caracteres y palabras + SVD.

    Se ajusta sobre el propio corpus (`fit`). Produce vectores densos L2-normalizados,
    de modo que el producto interno equivale al coseno. No requiere red.
    """

    def __init__(self, n_componentes: int = 128, semilla: int = 42) -> None:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.nombre = f"lsa-{n_componentes}"
        self._tfidf = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True,
            strip_accents="unicode", lowercase=True)
        self._n_componentes = n_componentes
        self._svd: TruncatedSVD | None = None
        self._svd_cls = TruncatedSVD
        self._semilla = semilla
        self.dim = n_componentes

    def fit(self, textos: Sequence[str]) -> "LSAEncoder":
        X = self._tfidf.fit_transform(textos)
        n_comp = min(self._n_componentes, X.shape[1] - 1, X.shape[0] - 1)
        n_comp = max(n_comp, 2)
        self._svd = self._svd_cls(n_components=n_comp, random_state=self._semilla)
        self._svd.fit(X)
        self.dim = n_comp
        return self

    def encode(self, textos: Sequence[str]) -> np.ndarray:
        if self._svd is None:
            raise RuntimeError("LSAEncoder no ajustado: llama a fit() con el corpus.")
        X = self._tfidf.transform(textos)
        return _l2_normalizar(self._svd.transform(X).astype(np.float32))

    # LSA es simétrico: consulta y documento se codifican igual.
    def encode_consultas(self, textos: Sequence[str]) -> np.ndarray:
        return self.encode(textos)

    def encode_documentos(self, textos: Sequence[str]) -> np.ndarray:
        return self.encode(textos)


class SentenceTransformerEncoder:
    """Codificador denso real (multilingüe, con soporte Matryoshka opcional)."""

    def __init__(self, modelo: str, truncar_dim: int | None = None,
                 tarea_consulta: str | None = None, tarea_documento: str | None = None,
                 revision: str | None = None, sin_conexion: bool = False) -> None:
        # Reproducibilidad: `revision` fija el commit del modelo en Hugging Face y
        # `sin_conexion` impide que la carga consulte la red, de modo que el código remoto
        # (trust_remote_code) sale siempre de la copia ya descargada y no de la rama main.
        if sin_conexion:
            import os
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
        # Shim de compatibilidad: transformers >=5 espera `all_tied_weights_keys`
        # en toda subclase de PreTrainedModel al finalizar la carga, pero el codigo
        # remoto de jina-v3 (XLMRobertaLoRA) no lo define. Un dict vacio es correcto
        # en inferencia (no hay pesos atados que marcar). No invasivo: solo aplica si
        # falta, y sobrevive a re-descargas del cache del modelo.
        from transformers import PreTrainedModel
        if not hasattr(PreTrainedModel, "all_tied_weights_keys"):
            PreTrainedModel.all_tied_weights_keys = {}

        from sentence_transformers import SentenceTransformer

        self._modelo = SentenceTransformer(modelo, trust_remote_code=True, revision=revision)
        dim_nativa = self._modelo.get_sentence_embedding_dimension()
        if truncar_dim is not None and not (0 < truncar_dim <= dim_nativa):
            raise ValueError(f"truncar_dim={truncar_dim} fuera de rango: el modelo tiene "
                             f"{dim_nativa} dimensiones (Matryoshka solo puede truncar).")
        self._truncar = truncar_dim
        # Tareas asimétricas (jina-v3: adaptadores LoRA + prompt distintos para consulta y
        # pasaje). Sin tarea, el modelo codifica ambos lados igual y no activa el adaptador
        # de recuperación.
        self._tarea_q = tarea_consulta
        self._tarea_d = tarea_documento
        self.nombre = (modelo.split("/")[-1] + (f"-mrl{truncar_dim}" if truncar_dim else "")
                       + ("" if tarea_consulta else "-sin-tarea"))
        self.dim = truncar_dim or dim_nativa

    def _codificar(self, textos: Sequence[str], tarea: str | None) -> np.ndarray:
        kw = {"task": tarea, "prompt_name": tarea} if tarea else {}
        vecs = self._modelo.encode(list(textos), convert_to_numpy=True,
                                   normalize_embeddings=False, **kw).astype(np.float32)
        if self._truncar:
            vecs = vecs[:, : self._truncar]      # truncación Matryoshka
        return _l2_normalizar(vecs)

    def encode(self, textos: Sequence[str]) -> np.ndarray:
        """Codificación simétrica (sin tarea); se conserva por compatibilidad."""
        return self._codificar(textos, None)

    def encode_consultas(self, textos: Sequence[str]) -> np.ndarray:
        return self._codificar(textos, self._tarea_q)

    def encode_documentos(self, textos: Sequence[str]) -> np.ndarray:
        return self._codificar(textos, self._tarea_d)


def construir_encoder(cfg: dict, corpus_textos: Sequence[str],
                      truncar_dim: int | None = None) -> Encoder:
    """Fábrica: instancia el encoder según config.yaml, con fallback a LSA."""
    tipo = cfg["encoder"]["tipo"]
    if tipo == "sentence-transformer":
        return SentenceTransformerEncoder(cfg["encoder"]["modelo_st"], truncar_dim,
                                          cfg["encoder"].get("tarea_consulta"),
                                          cfg["encoder"].get("tarea_documento"),
                                          cfg["encoder"].get("revision"),
                                          bool(cfg["encoder"].get("sin_conexion", False)))
    if tipo == "lsa":
        enc = LSAEncoder(cfg["encoder"]["lsa_componentes"])
        enc.fit(corpus_textos)
        return enc
    raise ValueError(f"Tipo de encoder desconocido: {tipo}")
