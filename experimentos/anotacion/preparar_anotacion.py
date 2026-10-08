#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepara las hojas de anotación de relevancia (pooling ciego) para dos anotadores expertos.

Para cada consulta candidata a gold se reúne un POOL con los documentos que cualquiera de las
seis configuraciones (BM25 y C1–C5) coloca en su top-`--profundidad`. Reunir el pool de varios
sistemas evita sesgar los juicios hacia un solo recuperador (práctica estándar de TREC). Cada
anotador recibe el pool en un orden distinto y SIN nombres de sistema ni posiciones, y juzga
cada par consulta–documento en la escala 0/1/2 (ver INSTRUCCIONES_ANOTACION.md).

Entradas : consultas con capa gold_candidate del conjunto ampliado y todo el conjunto difícil.
Salidas  : anotacion/hoja_anotador_A.csv, hoja_anotador_B.csv  (idénticas en contenido, distinto
           orden; el anotador rellena la columna `grado`), anotacion/pool_clave.json (oculta a
           los anotadores: de qué sistemas vino cada par; sirve al análisis posterior).

Uso:  python3 anotacion/preparar_anotacion.py [--profundidad 3]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import yaml

from lib.encoders import construir_encoder
from lib.retrievers import CONFIGS, CONFIG_BM25, MotorRecuperacion


def cargar(r):
    return [json.loads(l) for l in Path(r).read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profundidad", type=int, default=3)
    a = ap.parse_args()
    cfg = yaml.safe_load((RAIZ / "config.yaml").read_text(encoding="utf-8"))
    docs = cargar(RAIZ / cfg["rutas"]["corpus"])
    por_id = {d["id"]: d for d in docs}
    ontologia = yaml.safe_load((RAIZ / cfg["rutas"]["ontologia"]).read_text(encoding="utf-8"))
    enc = construir_encoder(cfg, [d["texto_indexable"] for d in docs] + [d["descripcion"] for d in docs])
    motor = MotorRecuperacion(docs, enc, ontologia, cfg["bm25"]["k1"], cfg["bm25"]["b"],
                              cfg["fusion"]["k_rrf"], cfg["realce"]["lambda"])

    consultas = [c for c in cargar(RAIZ / "datos/consultas_real_ampliado.jsonl")
                 if c.get("capa") == "gold_candidate"]
    consultas += cargar(RAIZ / "datos/consultas_dificil.jsonl")

    configs = [CONFIG_BM25] + list(CONFIGS)
    pares, clave = [], {}
    for c in consultas:
        pool: dict[str, list[int]] = {}
        for num in configs:
            for d in motor.recuperar(num, c["texto"])[: a.profundidad]:
                pool.setdefault(d, []).append(num)
        for d, sist in pool.items():
            pares.append({"qid": c["id"], "consulta": c["texto"], "doc_id": d,
                          "titulo": por_id[d]["titulo"],
                          "descripcion": por_id[d]["descripcion"][:300]})
            clave[f"{c['id']}|{d}"] = {"sistemas": sorted(sist),
                                       "es_objetivo_silver": d == c.get("reporte_objetivo")}

    campos = ["qid", "consulta", "doc_id", "titulo", "descripcion", "grado", "comentario"]
    for anot, semilla in (("A", 1), ("B", 2)):
        orden = pares[:]
        random.Random(semilla).shuffle(orden)
        with (Path(__file__).parent / f"hoja_anotador_{anot}.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            for p in orden:
                w.writerow({**p, "grado": "", "comentario": ""})
    (Path(__file__).parent / "pool_clave.json").write_text(
        json.dumps(clave, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"consultas={len(consultas)} pares a juzgar={len(pares)} "
          f"(~{len(pares)/max(len(consultas),1):.1f} por consulta); profundidad={a.profundidad}")


if __name__ == "__main__":
    main()
