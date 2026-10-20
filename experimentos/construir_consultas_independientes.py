#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consultas redactadas por personas ajenas al diseño (formulario de necesidades).

Lee `anotacion/respuestas_necesidades.csv` (columnas: participante, necesidad, consulta), la
clave privada `anotacion/clave_necesidades.json`, fijada antes de recoger respuestas, y el
corpus v3. Escribe `datos/consultas_indep.jsonl` y `datos/qrels_indep.jsonl`.

Cada consulta conserva el participante y la necesidad, para que el análisis pueda remuestrear
por participante o por necesidad (las consultas de una misma persona no son independientes).

Uso:
    python3 construir_consultas_independientes.py
    python3 eval_flexible.py --corpus corpus/corpus_v3.jsonl \
        --consultas datos/consultas_indep.jsonl --qrels datos/qrels_indep.jsonl \
        --salida resultados/resultados_indep.json
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PII = [re.compile(p) for p in (r"[\w.+-]+@[\w-]+\.[\w.]+", r"\b\d{7,}\b")]


def main() -> None:
    clave = json.loads((RAIZ / "anotacion" / "clave_necesidades.json").read_text(encoding="utf-8"))
    docs = [json.loads(l) for l in (RAIZ / "corpus" / "corpus_v3.jsonl").open(encoding="utf-8")]
    ids = {d["id"] for d in docs}
    ruta = RAIZ / "anotacion" / "respuestas_necesidades.csv"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta} (columnas: participante, necesidad, consulta)")

    def relevantes(k: dict) -> dict[str, float]:
        rel = {i: 2.0 for i in k.get("ids", [])}
        rel.update({i: 1.0 for i in k.get("ids_parciales", [])})
        if "facetas" in k:
            for d in docs:
                f = d.get("facetas", {})
                if d.get("dominio") == "pruebas_catalogo" and all(f.get(a) == v for a, v in k["facetas"].items()) \
                        and k.get("disciplina_contiene", "") in f.get("disciplina", "").lower():
                    rel[d["id"]] = 2.0
        faltan = set(rel) - ids
        assert not faltan, f"ids de la clave que no están en el corpus: {faltan}"
        return rel

    cons, qrels, descartadas = [], [], 0
    for i, fila in enumerate(csv.DictReader(ruta.open(encoding="utf-8-sig")), 1):
        texto = (fila.get("consulta") or "").strip()
        nec = (fila.get("necesidad") or "").strip().upper()
        if not texto or nec not in clave or any(p.search(texto) for p in PII):
            descartadas += 1
            continue
        rel = relevantes(clave[nec])
        if not rel:
            descartadas += 1
            continue
        qid = f"in_{i:04d}"
        cons.append({"id": qid, "texto": texto, "estrato": f"indep_{clave[nec]['tipo']}",
                     "necesidad": nec, "participante": fila.get("participante", "").strip(),
                     "n_relevantes": len(rel), "menciona_nombre_propio": False,
                     "origen": "persona_independiente"})
        qrels.append({"id": qid, "relevancia": rel})

    for nombre, filas in (("consultas_indep", cons), ("qrels_indep", qrels)):
        with (RAIZ / "datos" / f"{nombre}.jsonl").open("w", encoding="utf-8") as f:
            for x in filas:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(f"{len(cons)} consultas válidas de {len({c['participante'] for c in cons})} participantes; "
          f"{descartadas} descartadas (vacías, necesidad desconocida o con posible dato personal)")


if __name__ == "__main__":
    main()
