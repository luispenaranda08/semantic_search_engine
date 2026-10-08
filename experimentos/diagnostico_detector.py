#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnóstico del detector de entidades del realce (config 5) con el detector CORREGIDO.

Trata el indicador 1_entidad(q, d) como un clasificador binario sobre pares consulta–documento
cuya etiqueta ideal es «d es el objetivo de q». Reporta precisión, recall y cuántos documentos
activa en promedio por consulta, en cada conjunto. No requiere el modelo denso.
Uso: python3 diagnostico_detector.py   ->  resultados/diagnostico_detector.json
"""
import json, yaml
from pathlib import Path
from lib.retrievers import DetectorEntidades
RAIZ = Path(__file__).resolve().parent
cfg = yaml.safe_load((RAIZ / "config.yaml").read_text(encoding="utf-8"))
docs = [json.loads(l) for l in (RAIZ / cfg["rutas"]["corpus"]).read_text(encoding="utf-8").splitlines() if l.strip()]
onto = yaml.safe_load((RAIZ / cfg["rutas"]["ontologia"]).read_text(encoding="utf-8"))
det = DetectorEntidades(onto, [d["titulo"] for d in docs])
ent = {d["id"]: set(d["metadatos_ontologia"].get("entidades_principales", [])) for d in docs}
npd = {d["id"]: bool(d.get("nombre_propio_buscable", False)) for d in docs}
def ind(q, did):
    return int(bool(det.clases_en(q) & ent[did]) or (det.tiene_nombre_propio(q) and npd[did]))
cargar = lambda r: [json.loads(l) for l in (RAIZ / r).read_text(encoding="utf-8").splitlines() if l.strip()]
out = {}
for nombre, cq, qr in [("sintetico", "datos/consultas_eval.jsonl", "datos/qrels.jsonl"),
                       ("ampliado", "datos/consultas_real_ampliado.jsonl", "datos/qrels_real_ampliado.jsonl"),
                       ("dificil", "datos/consultas_dificil.jsonl", "datos/qrels_dificil.jsonl")]:
    qrels = {r["id"]: r["relevancia"] for r in cargar(qr)}
    tp = fp = fn = act = nq = 0
    for c in cargar(cq):
        tg = {d for d, g in qrels.get(c["id"], {}).items() if g > 0}
        if not tg: continue
        nq += 1
        for d in docs:
            i = ind(c["texto"], d["id"]); act += i
            tp += i and d["id"] in tg; fp += i and d["id"] not in tg; fn += (not i) and d["id"] in tg
    out[nombre] = {"consultas": nq, "precision": tp / (tp + fp) if tp + fp else None,
                   "recall": tp / (tp + fn) if tp + fn else None, "docs_activados_por_consulta": act / nq}
(RAIZ / "resultados/diagnostico_detector.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
