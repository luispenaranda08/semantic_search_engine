#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corre la escalera de ablación completa y computa todas las métricas.

Para cada configuración (BM25 de referencia más las cinco de la escalera) y cada
consulta con juicios de relevancia en la v1, calcula nDCG@10, Recall@100, MRR@10,
Precisión@10 y AP@100, y mide la latencia por consulta. Agrega los resultados de
forma global y por estrato, corre la prueba de Wilcoxon en las comparaciones
críticas (config. 4 y 5 frente a 3, en el estrato de entidad exacta) y guarda todo
en resultados/resultados.json.

Las consultas de competencias no tienen documento relevante en la v1 por diseño; se
excluyen de las métricas de calidad y se reportan aparte como vacío de cobertura.

Uso:
    python3 run_ablation.py            # usa config.yaml (encoder segun el archivo)
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import yaml

from lib import metrics as M
from lib.encoders import construir_encoder
from lib.retrievers import CONFIGS, CONFIG_BM25, NOMBRE_BM25, MotorRecuperacion
from lib.stats import bootstrap_ic, familia_comparaciones

RAIZ = Path(__file__).resolve().parent
METRICAS = ["ndcg@10", "recall@100", "mrr@10", "p@10", "ap@100"]


def cargar_jsonl(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def metricas_consulta(ranking: list[str], qrel: dict[str, float]) -> dict[str, float]:
    return {
        "ndcg@10": M.ndcg(ranking, qrel, 10),
        "recall@100": M.recall(ranking, qrel, 100),
        "mrr@10": M.mrr(ranking, qrel, 10),
        "p@10": M.precision(ranking, qrel, 10),
        "ap@100": M.average_precision(ranking, qrel, 100),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(RAIZ / "config.yaml"))
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    docs = cargar_jsonl(RAIZ / cfg["rutas"]["corpus"])
    consultas = cargar_jsonl(RAIZ / cfg["rutas"]["consultas"])
    qrels = {r["id"]: r["relevancia"] for r in cargar_jsonl(RAIZ / cfg["rutas"]["qrels"])}
    ontologia = yaml.safe_load((RAIZ / cfg["rutas"]["ontologia"]).read_text(encoding="utf-8"))

    # Encoder: el texto para ajustar el fallback LSA es el enriquecido más la descripción.
    textos_fit = [d["texto_indexable"] for d in docs] + [d["descripcion"] for d in docs]
    encoder = construir_encoder(cfg, textos_fit)

    motor = MotorRecuperacion(
        docs, encoder, ontologia,
        k1=cfg["bm25"]["k1"], b=cfg["bm25"]["b"],
        k_rrf=cfg["fusion"]["k_rrf"], lambda_realce=cfg["realce"]["lambda"])

    configuraciones = [(CONFIG_BM25, NOMBRE_BM25)] + list(CONFIGS.items())

    # consultas con y sin cobertura en la v1
    con_gold = [c for c in consultas if M.tiene_gold(qrels.get(c["id"], {}))]
    sin_gold = [c for c in consultas if not M.tiene_gold(qrels.get(c["id"], {}))]

    por_consulta: dict[str, dict[str, dict[str, float]]] = {}
    latencias: dict[str, list[float]] = {}

    for num, nombre in configuraciones:
        por_consulta[nombre] = {}
        latencias[nombre] = []
        for c in consultas:
            t0 = time.perf_counter()
            ranking = motor.recuperar(num, c["texto"])
            latencias[nombre].append((time.perf_counter() - t0) * 1000)
            if M.tiene_gold(qrels.get(c["id"], {})):
                por_consulta[nombre][c["id"]] = metricas_consulta(ranking, qrels[c["id"]])

    def agrega(nombre: str, ids: list[str]) -> dict[str, float]:
        filas = [por_consulta[nombre][i] for i in ids if i in por_consulta[nombre]]
        if not filas:
            return {m: 0.0 for m in METRICAS}
        return {m: float(np.mean([f[m] for f in filas])) for m in METRICAS}

    estratos = sorted({c["estrato"] for c in con_gold})
    ids_por_estrato = {e: [c["id"] for c in con_gold if c["estrato"] == e] for e in estratos}
    ids_global = [c["id"] for c in con_gold]

    resultado = {
        "encoder": encoder.nombre,
        "n_consultas_total": len(consultas),
        "n_consultas_con_gold": len(con_gold),
        "n_consultas_sin_cobertura_v1": len(sin_gold),
        "estratos_sin_cobertura": sorted({c["estrato"] for c in sin_gold}),
        "global": {nombre: agrega(nombre, ids_global) for _, nombre in configuraciones},
        "por_estrato": {e: {nombre: agrega(nombre, ids_por_estrato[e])
                            for _, nombre in configuraciones} for e in estratos},
        "eficiencia": {nombre: {
            "latencia_p50_ms": float(np.percentile(latencias[nombre], 50)),
            "latencia_p95_ms": float(np.percentile(latencias[nombre], 95)),
        } for _, nombre in configuraciones},
        "indice": {
            "n_documentos": len(docs),
            "dimension_densa": int(encoder.dim),
            "bytes_aprox_matriz_densa": int(len(docs) * encoder.dim * 4),
        },
    }

    # ---- Estadística: comparaciones críticas en entidad exacta (P1, P3, P5) ----
    def serie(nombre: str, ids: list[str], metrica: str = "ndcg@10") -> list[float]:
        return [por_consulta[nombre][i][metrica] for i in ids if i in por_consulta[nombre]]

    ee = ids_por_estrato.get("entidad_exacta", [])
    nombres = {CONFIG_BM25: NOMBRE_BM25, **CONFIGS}
    nb, sem = cfg["evaluacion"]["bootstrap_muestras"], cfg["evaluacion"]["semilla"]
    resultado["estadistica_global"] = familia_comparaciones(serie, ids_global, nombres, nb, sem)
    resultado["estadistica_entidad_exacta"] = familia_comparaciones(serie, ee, nombres, nb, sem)
    resultado["ic_bootstrap_ndcg10_global"] = {
        nombre: bootstrap_ic(serie(nombre, ids_global),
                             cfg["evaluacion"]["bootstrap_muestras"],
                             semilla=cfg["evaluacion"]["semilla"])
        for _, nombre in configuraciones}

    ruta = RAIZ / cfg["rutas"]["resultados"]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Encoder: {encoder.nombre}  |  consultas con gold: {len(con_gold)}  |  "
          f"sin cobertura v1: {len(sin_gold)}")
    print("Resultado global (nDCG@10):")
    for _, nombre in configuraciones:
        print(f"  {nombre:34s} {resultado['global'][nombre]['ndcg@10']:.3f}")
    print(f"Guardado en {ruta}")


if __name__ == "__main__":
    main()
