#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Análisis de fallos en el estrato de entidad exacta.

Para la línea base crítica (config. 3, híbrido sin ontología) y la configuración
completa (config. 5), lista las consultas de entidad exacta cuyo documento objetivo
no quedó en la primera posición, con el rango donde sí apareció. Es la evidencia
cualitativa que acompaña las métricas de P2 y P5.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from lib.retrievers import CONFIGS, MotorRecuperacion
from lib.encoders import construir_encoder


def _cargar(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def rango_objetivo(ranking: list[str], objetivo: str) -> int | None:
    for i, d in enumerate(ranking, start=1):
        if d == objetivo:
            return i
    return None


def analizar(cfg: dict, raiz: Path) -> str:
    docs = _cargar(raiz / cfg["rutas"]["corpus"])
    consultas = _cargar(raiz / cfg["rutas"]["consultas"])
    ontologia = yaml.safe_load((raiz / cfg["rutas"]["ontologia"]).read_text(encoding="utf-8"))
    textos_fit = [d["texto_indexable"] for d in docs] + [d["descripcion"] for d in docs]
    encoder = construir_encoder(cfg, textos_fit)
    motor = MotorRecuperacion(docs, encoder, ontologia, cfg["bm25"]["k1"], cfg["bm25"]["b"],
                              cfg["fusion"]["k_rrf"], cfg["realce"]["lambda"])

    ee = [c for c in consultas if c["estrato"] == "entidad_exacta" and c["reporte_objetivo"]]
    lin = ["# Análisis de fallos — estrato de entidad exacta", "",
           f"Encoder: `{encoder.nombre}`. Se listan las consultas cuyo reporte objetivo "
           "no quedó en la posición 1.", ""]
    for num in (3, 5):
        lin += [f"## {CONFIGS[num]} (config. {num})", "",
                "| Consulta | Objetivo (rango) | Nombre propio |", "|---|---|---|"]
        fallos = 0
        for c in ee:
            ranking = motor.recuperar(num, c["texto"])
            r = rango_objetivo(ranking, c["reporte_objetivo"])
            if r != 1:
                fallos += 1
                lin.append(f"| {c['texto']} | pos. {r} | {'sí' if c['menciona_nombre_propio'] else 'no'} |")
        if fallos == 0:
            lin.append("| (sin fallos: todos en posición 1) | | |")
        lin += ["", f"Fallos (objetivo fuera de la posición 1): {fallos} de {len(ee)}.", ""]
    return "\n".join(lin) + "\n"


def generar(cfg: dict, raiz: Path, ruta_salida: Path) -> None:
    ruta_salida.write_text(analizar(cfg, raiz), encoding="utf-8")
