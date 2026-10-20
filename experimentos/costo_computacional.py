#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Costo computacional de cada componente del recuperador, medido en el equipo del autor.

Mide: tiempo de carga del modelo denso y memoria residente del proceso; número de parámetros;
tiempo de codificar los documentos (descripción y texto enriquecido) y las consultas; tiempo de
construir y consultar el índice BM25; tiempo de la búsqueda densa y de la fusión RRF. Se corre
un solo proceso, con baja prioridad, y se repiten las mediciones para tomar medianas.

Uso: nice -n 19 python3 costo_computacional.py -> resultados/costo_computacional.json
"""
from __future__ import annotations

import json
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import fusion as F
from lib.banco import cargar_config, cargar_conjunto, cargar_jsonl, RAIZ
from lib.encoders import construir_encoder
from lib.indexes import BM25Index


def rss_mib() -> float:
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 2**20 if sys.platform == "darwin" else r / 2**10   # macOS: bytes; Linux: KiB


def ms(f, reps=1):
    t = []
    for _ in range(reps):
        t0 = time.perf_counter(); f(); t.append((time.perf_counter() - t0) * 1000)
    return t


def main() -> None:
    cfg = cargar_config()
    docs = cargar_jsonl(RAIZ / cfg["rutas"]["corpus"])
    desc = [d["descripcion"] for d in docs]
    onto = [d["texto_indexable"] for d in docs]
    cons, _ = cargar_conjunto("ampliado")
    qs = [c["texto"] for c in cons[:40]]
    out = {"equipo": {"cpu": subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip(),
                      "so": platform.platform(), "python": platform.python_version()},
           "rss_antes_modelo_MiB": rss_mib()}

    t0 = time.perf_counter()
    enc = construir_encoder(cfg, [])
    out["carga_modelo_s"] = time.perf_counter() - t0
    out["rss_tras_modelo_MiB"] = rss_mib()
    try:
        out["parametros_millones"] = sum(p.numel() for p in enc._modelo.parameters()) / 1e6
        out["dispositivo"] = str(next(enc._modelo.parameters()).device)
    except Exception as e:                       # noqa: BLE001
        out["parametros_millones"] = None; out["nota_parametros"] = str(e)

    enc.encode_documentos(desc[:2])              # calentamiento
    t_doc = ms(lambda: enc.encode_documentos(desc), 3) + ms(lambda: enc.encode_documentos(onto), 3)
    out["codificar_17_docs_ms_mediana"] = float(np.median(t_doc))
    out["codificar_por_doc_ms"] = float(np.median(t_doc)) / len(docs)
    tq = [ms(lambda q=q: enc.encode_consultas([q]))[0] for q in qs]
    out["codificar_consulta_ms"] = {"p50": float(np.percentile(tq, 50)), "p95": float(np.percentile(tq, 95))}
    out["rss_pico_MiB"] = rss_mib()

    out["bm25_construir_indice_ms"] = float(np.median(ms(lambda: BM25Index().indexar([d["id"] for d in docs], onto), 20)))
    bm = BM25Index().indexar([d["id"] for d in docs], onto)
    out["bm25_consulta_ms_p50"] = float(np.median([ms(lambda q=q: bm.buscar(q))[0] for q in qs]))
    mat = enc.encode_documentos(onto)
    qv = enc.encode_consultas(qs)
    out["busqueda_densa_ms_p50"] = float(np.median([ms(lambda v=v: np.argsort(-(mat @ v)))[0] for v in qv]))
    b0, d0 = dict(bm.buscar(qs[0])), {d["id"]: float(s) for d, s in zip(docs, mat @ qv[0])}
    out["fusion_rrf_ms_p50"] = float(np.median(ms(lambda: F.rrf(b0, d0, 60), 200)))
    out["indice_denso_KiB"] = {"1024": len(docs) * 1024 * 4 / 1024, "256": len(docs) * 256 * 4 / 1024}
    try:
        out["precision_numerica"] = str(next(enc._modelo.parameters()).dtype)
    except Exception:                               # noqa: BLE001
        pass

    # Latencia de punta a punta por configuración, en ESTA misma corrida (mismo proceso, mismo estado
    # del equipo): el motor codifica la consulta en cada llamada, sin caché.
    import yaml
    from lib.retrievers import CONFIGS, CONFIG_BM25, MotorRecuperacion
    onto_yaml = yaml.safe_load((RAIZ / cfg["rutas"]["ontologia"]).read_text(encoding="utf-8"))
    motor = MotorRecuperacion(docs, enc, onto_yaml, cfg["bm25"]["k1"], cfg["bm25"]["b"],
                              cfg["fusion"]["k_rrf"], cfg["realce"]["lambda"])
    nombres = {CONFIG_BM25: "BM25", 1: "C1", 2: "C2", 3: "C3", 4: "C4", 5: "C5"}
    motor.recuperar(4, qs[0])                       # calentamiento
    lat = {}
    for num, nm in nombres.items():
        ts = [ms(lambda q=q: motor.recuperar(num, q))[0] for q in qs]
        lat[nm] = {"p50": float(np.percentile(ts, 50)), "p95": float(np.percentile(ts, 95))}
    out["latencia_extremo_a_extremo_ms"] = lat

    # Solo CPU (sin la GPU integrada): codificación de la consulta.
    try:
        enc._modelo.to("cpu")
        enc.encode_consultas([qs[0]])
        tq_cpu = [ms(lambda q=q: enc.encode_consultas([q]))[0] for q in qs[:20]]
        out["codificar_consulta_cpu_ms"] = {"p50": float(np.percentile(tq_cpu, 50)), "p95": float(np.percentile(tq_cpu, 95))}
    except Exception as e:                          # noqa: BLE001
        out["codificar_consulta_cpu_ms"] = {"error": str(e)}
    (RAIZ / "resultados/costo_computacional.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
