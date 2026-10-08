#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Análisis de errores cualitativo y cuantitativo: ¿qué reportes se confunden y por qué?

Para cada conjunto y sistema (BM25, C1 denso, C2 denso+onto, C3 híbrido, C4 híbrido+onto) calcula
la exactitud en la primera posición por reporte objetivo, la matriz de confusión objetivo → reporte
devuelto en primer lugar y las confusiones más frecuentes, y lista consultas fallidas con el
reporte que se devolvió. Sirve para separar dos explicaciones de un error: (a) la consulta es
genuinamente ambigua entre dos reportes (un límite del protocolo de objetivo único) y (b) el sistema
se equivoca de reporte a pesar de que la consulta es clara.

Uso: python3 analisis_errores.py -> resultados/analisis_errores.json y .md
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import fusion as F
from lib.banco import CONJUNTOS, EncoderCacheado, Puntuaciones, cargar_conjunto, cargar_config, cargar_jsonl, ranking, RAIZ
from lib.encoders import construir_encoder

CORTO = lambda i: i.split("_", 2)[-1].replace("reporte_", "").replace("de_", "")[:28]


def main() -> None:
    cfg = cargar_config()
    docs = cargar_jsonl(RAIZ / cfg["rutas"]["corpus"])
    enc = EncoderCacheado(construir_encoder(cfg, []))
    k1, b = cfg["bm25"]["k1"], cfg["bm25"]["b"]
    Pd = Puntuaciones({d["id"]: d["descripcion"] for d in docs}, enc, k1, b)
    Po = Puntuaciones({d["id"]: d["texto_indexable"] for d in docs}, enc, k1, b)
    ids = Pd.ids
    sistemas = {
        "BM25": lambda q: ranking(Pd.puntaje_bm25(q), ids),
        "C1": lambda q: ranking(Pd.puntaje_denso(q), ids),
        "C2": lambda q: ranking(Po.puntaje_denso(q), ids),
        "C3": lambda q: ranking(F.rrf(Pd.puntaje_bm25(q), Pd.puntaje_denso(q), 60), ids),
        "C4": lambda q: ranking(F.rrf(Po.puntaje_bm25(q), Po.puntaje_denso(q), 60), ids),
    }
    out: dict = {}
    for cn in CONJUNTOS:
        cons, qr = cargar_conjunto(cn)
        o = {"n": len(cons), "acc1": {}, "por_reporte_acc1": {}, "confusiones": {}, "fallos": []}
        conf = {s: collections.Counter() for s in sistemas}
        acc = {s: collections.defaultdict(list) for s in sistemas}
        for c in cons:
            tgt = max(qr[c["id"]], key=qr[c["id"]].get)
            for s, fn in sistemas.items():
                r = fn(c["texto"])
                top1 = r[0]
                acc[s][tgt].append(top1 == tgt)
                if top1 != tgt:
                    conf[s][(tgt, top1)] += 1
        for s in sistemas:
            todos = [x for v in acc[s].values() for x in v]
            o["acc1"][s] = float(np.mean(todos))
            o["por_reporte_acc1"][s] = {CORTO(t): [int(sum(v)), len(v)] for t, v in sorted(acc[s].items())}
            o["confusiones"][s] = [{"objetivo": CORTO(t), "devuelto": CORTO(p), "veces": n} for (t, p), n in conf[s].most_common(6)]
        # consultas que fallan en C4 y C2: qué se devolvió
        for c in cons:
            tgt = max(qr[c["id"]], key=qr[c["id"]].get)
            t4, t2 = sistemas["C4"](c["texto"]), sistemas["C2"](c["texto"])
            if t4[0] != tgt or t2[0] != tgt:
                o["fallos"].append({"id": c["id"], "texto": c["texto"], "objetivo": CORTO(tgt),
                                    "C2_top1": CORTO(t2[0]), "C2_rango_objetivo": t2.index(tgt) + 1,
                                    "C4_top1": CORTO(t4[0]), "C4_rango_objetivo": t4.index(tgt) + 1})
        o["fallos"] = o["fallos"][:40]
        out[cn] = o
        print(f"[errores] {cn}: acc@1 " + ", ".join(f"{s}={v:.3f}" for s, v in o["acc1"].items()))
    (RAIZ / "resultados/analisis_errores.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    L = ["# Análisis de errores", "", "Exactitud en la primera posición (acc@1) por sistema:", "",
         "| Conjunto | n | " + " | ".join(sistemas) + " |", "|---|---|" + "---|" * len(sistemas)]
    for cn, o in out.items():
        L.append(f"| {cn} | {o['n']} | " + " | ".join(f"{o['acc1'][s]:.3f}" for s in sistemas) + " |")
    for cn, o in out.items():
        L += ["", f"## {cn}: confusiones más frecuentes", ""]
        for s in ("C1", "C2", "C4"):
            L.append(f"**{s}**: " + "; ".join(f"{x['objetivo']} → {x['devuelto']} ({x['veces']})" for x in o["confusiones"][s]))
            L.append("")
        L += ["Consultas fallidas (primeras 15):", "", "| id | consulta | objetivo | C2: top1 (rango obj.) | C4: top1 (rango obj.) |", "|---|---|---|---|---|"]
        for f in o["fallos"][:15]:
            L.append(f"| {f['id']} | {f['texto'][:60]} | {f['objetivo']} | {f['C2_top1']} ({f['C2_rango_objetivo']}) | {f['C4_top1']} ({f['C4_rango_objetivo']}) |")
    (RAIZ / "resultados/analisis_errores.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
