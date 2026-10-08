#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runner flexible de la escalera de ablación sobre corpus y conjuntos arbitrarios.

Permite evaluar los escenarios de las escaleras 1 y 2 sin tocar run_ablation.py:
  - corpus a discreción (v1, o v1 + competencias)
  - consultas/qrels a discreción (sintético, real-silver, real+competencias)

Uso:
  python3 eval_flexible.py --corpus corpus/corpus_v1.jsonl \
      --consultas datos/consultas_real.jsonl --qrels datos/qrels_real.jsonl \
      --salida resultados/resultados_real_v1.json
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, yaml

from lib import metrics as M
from lib.encoders import construir_encoder
from lib.stats import familia_comparaciones
from lib.retrievers import CONFIGS, CONFIG_BM25, NOMBRE_BM25, MotorRecuperacion

RAIZ = Path(__file__).resolve().parent
METRICAS = ["ndcg@10", "recall@100", "mrr@10", "p@10", "ap@100"]


def cargar(r): return [json.loads(l) for l in Path(r).read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--consultas", required=True)
    ap.add_argument("--qrels", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--campo-texto", default="texto",
                    help="campo de la consulta a usar (p. ej. texto_sin_nombre para el control)")
    a = ap.parse_args()
    cfg = yaml.safe_load((RAIZ / "config.yaml").read_text(encoding="utf-8"))

    docs = cargar(RAIZ / a.corpus)
    consultas = cargar(RAIZ / a.consultas)
    qrels = {r["id"]: r["relevancia"] for r in cargar(RAIZ / a.qrels)}
    ontologia = yaml.safe_load((RAIZ / cfg["rutas"]["ontologia"]).read_text(encoding="utf-8"))

    textos_fit = [d["texto_indexable"] for d in docs] + [d["descripcion"] for d in docs]
    enc = construir_encoder(cfg, textos_fit)
    motor = MotorRecuperacion(docs, enc, ontologia, cfg["bm25"]["k1"], cfg["bm25"]["b"],
                              cfg["fusion"]["k_rrf"], cfg["realce"]["lambda"])
    configs = [(CONFIG_BM25, NOMBRE_BM25)] + list(CONFIGS.items())
    con_gold = [c for c in consultas if M.tiene_gold(qrels.get(c["id"], {}))]

    por = {n: {} for _, n in configs}
    for num, n in configs:
        for c in consultas:
            rank = motor.recuperar(num, c.get(a.campo_texto) or c["texto"])
            if M.tiene_gold(qrels.get(c["id"], {})):
                por[n][c["id"]] = {"ndcg@10": M.ndcg(rank, qrels[c["id"]], 10),
                                   "recall@100": M.recall(rank, qrels[c["id"]], 100),
                                   "mrr@10": M.mrr(rank, qrels[c["id"]], 10),
                                   "p@10": M.precision(rank, qrels[c["id"]], 10),
                                   "ap@100": M.average_precision(rank, qrels[c["id"]], 100)}
    estratos = sorted({c["estrato"] for c in con_gold})
    idsg = [c["id"] for c in con_gold]
    idse = {e: [c["id"] for c in con_gold if c["estrato"] == e] for e in estratos}

    def agg(n, ids):
        f = [por[n][i] for i in ids if i in por[n]]
        return {m: float(np.mean([x[m] for x in f])) if f else 0.0 for m in METRICAS}

    res = {"encoder": enc.nombre, "n_docs": len(docs), "n_consultas": len(consultas),
           "n_con_gold": len(con_gold),
           "global": {n: agg(n, idsg) for _, n in configs},
           "por_estrato": {e: {n: agg(n, idse[e]) for _, n in configs} for e in estratos}}
    def serie(n, ids):
        return [por[n][i]["ndcg@10"] for i in ids if i in por[n]]
    nombres = {CONFIG_BM25: NOMBRE_BM25, **CONFIGS}
    nb, sem = cfg["evaluacion"]["bootstrap_muestras"], cfg["evaluacion"]["semilla"]
    res["estadistica"] = {"global": familia_comparaciones(serie, idsg, nombres, nb, sem),
                          **{e: familia_comparaciones(serie, idse[e], nombres, nb, sem)
                             for e in estratos}}
    res["por_consulta"] = por
    Path(RAIZ / a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(RAIZ / a.salida).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{a.salida}] docs={len(docs)} consultas={len(consultas)} gold={len(con_gold)} enc={enc.nombre}")
    for _, n in configs:
        print(f"  {n:34s} nDCG@10={res['global'][n]['ndcg@10']:.3f}  Recall@100={res['global'][n]['recall@100']:.3f}")


if __name__ == "__main__":
    main()
