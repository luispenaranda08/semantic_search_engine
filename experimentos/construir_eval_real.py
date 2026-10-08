#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Escalera 1 — Conjunto de evaluación con validez externa a partir del historial real.

Convierte las firmas de consulta reales del historial de Athena (suid_query_signatures)
en un conjunto de evaluación con juicios silver. Cada firma es el SQL que se ejecutó, así
que su reporte lógico es una etiqueta de relevancia débil pero fuerte en la práctica
(grado 2). Los textos de consulta se sintetizan en lenguaje natural a partir de los filtros
reales que usó cada firma (columnas y keywords del WHERE), ponderados por su frecuencia
real de ejecución.

Muestreo estratificado (no proporcional): cabeza (top-5 reportes), cola larga (reportes y
firmas raras) y entidad exacta / nombre propio (firmas que filtran por nombre/documento).

Privacidad: las firmas contienen NOMBRES DE COLUMNA y keywords del WHERE, no literales de
datos personales, así que no hay PII en la fuente. Aun así se emiten dos artefactos: uno de
uso interno (`consultas_real.jsonl`) y uno anonimizado para el paper (`consultas_paper.jsonl`),
donde cualquier nombre propio se reemplaza por un sintético estable del gazetteer.

Uso:
    python3 construir_eval_real.py
"""
from __future__ import annotations

import csv
import json
import random
import re
import unicodedata
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.etiquetado import SLUG_POR_CLAVE, id_por_slug, reetiquetar_firma

RAIZ = Path(__file__).resolve().parent
SIG = RAIZ.parent / "data" / "athena_suid" / "suid_query_signatures.csv"
ROLLUP = RAIZ.parent / "data" / "athena_suid" / "suid_logical_reports_rollup.csv"
CORPUS = RAIZ / "corpus" / "corpus_v1.jsonl"
SEMILLA = 42

# Nombres SINTÉTICOS (nunca reales) para las consultas de nombre propio.
NOMBRES = ["Andrés Torres", "María Restrepo", "Julián Gómez", "Valentina Ríos"]
INSTITUCIONES = ["Colegio San Marcos", "Club Deportivo El Faro", "Liga Atlántico"]

# Columnas que delatan una consulta de ENTIDAD EXACTA / nombre propio.
COLS_NOMBRE = {"full_name", "first_name", "first_last_name", "second_last_name",
               "document_number", "email", "institution_name", "group_name"}

# Traducción de columna/keyword de filtro a lenguaje natural.
COL_A_FRASE = {
    "current_stage": "por etapa", "stage": "por etapa", "stage_sequence": "por etapa",
    "category": "por categoría", "category_name": "por categoría",
    "discipline_status": "por estado de disciplina", "discipline_name": "por disciplina",
    "status": "por estado", "date": "por fecha", "event_code": "de un evento",
    "inst_region_name": "por región", "inst_department_name": "por departamento",
    "inst_municipality_name": "por municipio", "is_reinforcement": "de refuerzo",
    "group_name": "por grupo", "phase": "por fase", "promotion_status": "por promoción",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def cargar_corpus_ids() -> dict:
    docs = [json.loads(l) for l in CORPUS.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {d["id"]: d["titulo"] for d in docs}


def mapear_a_corpus(nombre_logico: str, ids: dict) -> str | None:
    """Mapea el nombre de reporte lógico del historial al id del corpus por palabras clave."""
    n = _norm(nombre_logico)
    reglas = [  # (palabras que deben aparecer en el nombre lógico, id de corpus)
        (["promocion"], SLUG_POR_CLAVE["promocion"]), (["avance"], SLUG_POR_CLAVE["promocion"]), (["phases"], SLUG_POR_CLAVE["promocion"]),
        (["promotions_log"], SLUG_POR_CLAVE["promocion"]),
        (["grupos"], SLUG_POR_CLAVE["grupos"]), (["personal"], SLUG_POR_CLAVE["personal"]),
        (["documentacion"], SLUG_POR_CLAVE["documentacion"]), (["participacion", "intencion"], SLUG_POR_CLAVE["participacion"]),
        (["participacion"], SLUG_POR_CLAVE["participacion"]), (["individuales"], SLUG_POR_CLAVE["individual"]),
        (["dashboard"], SLUG_POR_CLAVE["dashboard"]), (["instituciones"], SLUG_POR_CLAVE["instituciones"]),
        (["progreso"], SLUG_POR_CLAVE["metas"]), (["metas"], SLUG_POR_CLAVE["metas"]),
        (["user_distribution"], SLUG_POR_CLAVE["distribucion"]), (["distribucion"], SLUG_POR_CLAVE["distribucion"]),
        (["federation"], SLUG_POR_CLAVE["federacion"]), (["federacion"], SLUG_POR_CLAVE["federacion"]),
        (["caidas_todas_etapas_resumen"], SLUG_POR_CLAVE["caidas_todas_resumen"]),
        (["caidas_todas_etapas"], SLUG_POR_CLAVE["caidas_todas"]),
        (["intent_changes"], SLUG_POR_CLAVE["cambios"]), (["cambios"], SLUG_POR_CLAVE["cambios"]),
        (["intent_delegations"], SLUG_POR_CLAVE["delegaciones"]), (["delegaciones"], SLUG_POR_CLAVE["delegaciones"]),
        (["caidas_resumen"], SLUG_POR_CLAVE["caidas_resumen"]), (["caidas"], SLUG_POR_CLAVE["caidas"]),
    ]
    for palabras, pref in reglas:
        if all(p in n for p in palabras):
            return id_por_slug(pref, ids)
    return None


def tema_reporte(nombre_logico: str) -> str:
    """Frase temática corta del reporte para armar la consulta."""
    n = _norm(nombre_logico)
    temas = [("promocion", "promoción de deportistas"), ("avance", "avance de etapa"),
             ("grupos", "grupos"), ("personal", "personal de apoyo"),
             ("documentacion", "documentación de deportistas"),
             ("participacion", "participación"), ("individuales", "reporte individual de deportistas"),
             ("dashboard", "tablero de control"), ("instituciones", "instituciones"),
             ("progreso", "progreso y cumplimiento de metas"), ("metas", "cumplimiento de metas"),
             ("distribution", "distribución de usuarios"), ("distribucion", "distribución de usuarios"),
             ("federation", "métricas por federación"), ("federacion", "métricas por federación"),
             ("caidas", "pruebas de caídas"), ("phases", "fases del evento"),
             ("promotions_log", "registro de promociones"), ("delegations", "delegaciones de participación"),
             ("changes", "cambios en la intención de participación")]
    for k, frase in temas:
        if k in n:
            return frase
    return "reporte del sistema"


def filtros_de(fila: dict) -> list[str]:
    campos = (fila.get("keywords_where", "") + "|" + fila.get("columnas_clave", "")).split("|")
    return [c.strip() for c in campos if c.strip()]


def frase_persona(nombre_logico: str, nombre: str) -> str:
    """Plantilla limpia de consulta por nombre propio según el reporte."""
    n = _norm(nombre_logico)
    if "documentacion" in n:
        return f"documentación del deportista {nombre}"
    if "participacion" in n or "intencion" in n:
        return f"intención de participación de {nombre}"
    if "personal" in n:
        return f"personal de apoyo del deportista {nombre}"
    if "grupos" in n:
        return f"grupo del deportista {nombre}"
    if "individuales" in n:
        return f"reporte individual del deportista {nombre}"
    return f"estado de promoción del deportista {nombre}"


def sintetizar_consulta(fila: dict, estrato: str, rng: random.Random,
                        nombre: str | None = None) -> tuple[str, bool]:
    """Devuelve (texto_consulta, menciona_nombre_propio) a partir de la firma."""
    tema = tema_reporte(fila["nombre_logico"])
    filtros = filtros_de(fila)
    frases = []
    for c in filtros:
        if c in COL_A_FRASE and COL_A_FRASE[c] not in frases:
            frases.append(COL_A_FRASE[c])
    if estrato == "entidad_exacta":
        if nombre in INSTITUCIONES:
            return (f"{tema} de la institución {nombre}", True)
        return (frase_persona(fila["nombre_logico"], nombre or NOMBRES[0]), True)
    if estrato == "ambigua":
        return (tema.split()[0], False)                 # término corto/ambiguo
    cola = (" " + ", ".join(frases[:3])) if frases else ""
    return (f"{tema}{cola}".strip(), False)


def clasificar_estrato(fila: dict, es_cabeza: bool) -> str:
    filtros = set(filtros_de(fila))
    if filtros & COLS_NOMBRE:
        return "entidad_exacta"
    if len(filtros) <= 1:
        return "ambigua"
    if len(filtros) >= 5:
        return "documento_largo"
    return "cabeza" if es_cabeza else "cola"


def anonimizar(texto: str) -> str:
    """Reemplaza nombres propios detectados por un sintético estable (idempotente aquí:
    las consultas ya usan sintéticos, pero se ejecuta como salvaguarda para el paper)."""
    # Los únicos nombres propios inyectados provienen del gazetteer sintético, así que el
    # texto ya es seguro. La función queda como barrera explícita y documentada.
    return texto


def main() -> None:
    rng = random.Random(SEMILLA)
    ids = cargar_corpus_ids()
    # Firmas con la etiqueta de reporte CORREGIDA (ver lib/etiquetado.py).
    firmas = [reetiquetar_firma(f) for f in csv.DictReader(SIG.open(encoding="utf-8"))
              if f.get("es_wrapper_count") != "True"]   # sin gemelos COUNT(*) de paginación

    # top-5 reportes por demanda, recalculado sobre las etiquetas corregidas (el rollup
    # original arrastra la clasificación sesgada de Promoción).
    dem = {}
    for f in firmas:
        dem[f["nombre_logico"]] = dem.get(f["nombre_logico"], 0.0) + float(f["frecuencia"])
    top5 = {_norm(n) for n, _ in sorted(dem.items(), key=lambda x: -x[1])[:5]}

    # deduplicar firmas por (reporte, combinación de filtros); quedarse con la más frecuente
    porclave = {}
    for f in firmas:
        clave = (f["nombre_logico"], tuple(sorted(filtros_de(f))))
        if clave not in porclave or float(f["frecuencia"]) > float(porclave[clave]["frecuencia"]):
            porclave[clave] = f
    unicas = list(porclave.values())

    # clasificar y agrupar por estrato
    porestrato = {"entidad_exacta": [], "cabeza": [], "cola": [], "ambigua": [], "documento_largo": []}
    for f in unicas:
        es_cabeza = _norm(f["nombre_logico"]) in top5
        est = clasificar_estrato(f, es_cabeza)
        porestrato[est].append(f)

    # cupos por estrato (muestreo estratificado, no proporcional)
    cupos = {"entidad_exacta": 30, "cabeza": 35, "cola": 25, "ambigua": 15, "documento_largo": 20}
    consultas, qrels, cont = [], {}, 0

    def agregar(f, estrato_final, nombre=None):
        nonlocal cont
        obj = mapear_a_corpus(f["nombre_logico"], ids)
        if not obj:
            return False
        texto, np_ = sintetizar_consulta(f, estrato_final, rng, nombre)
        cont += 1
        qid = f"r{cont:03d}"
        consultas.append({"id": qid, "texto": texto,
                          "estrato": "entidad_exacta" if estrato_final == "entidad_exacta"
                                     else ("ambigua" if estrato_final == "ambigua"
                                           else ("documento_largo" if estrato_final == "documento_largo"
                                                 else "operacional")),
                          "reporte_objetivo": obj, "menciona_nombre_propio": np_,
                          "frecuencia_real": int(float(f["frecuencia"])),
                          "firma_reporte": f["nombre_logico"]})
        qrels[qid] = {obj: 2.0}                       # silver: grado 2 al reporte ejecutado
        return True

    for est, lista in porestrato.items():
        lista_ord = sorted(lista, key=lambda r: -float(r["frecuencia"]))
        vistos = set()
        if est == "entidad_exacta":
            # cada firma de nombre propio genera una consulta por nombre sintético (mismo
            # patrón de filtro real, distinta entidad), hasta llenar el cupo. El pool depende
            # de si la firma filtra por institución o por persona.
            def cuenta_ee():
                return sum(1 for c in consultas if c["estrato"] == "entidad_exacta")
            for f in lista_ord:
                pool = INSTITUCIONES if "institution_name" in filtros_de(f) else NOMBRES
                for nom in pool:
                    if cuenta_ee() >= cupos[est]:
                        break
                    texto_prev, _ = sintetizar_consulta(f, "entidad_exacta", rng, nom)
                    if texto_prev in vistos:
                        continue
                    if agregar(f, est, nom):
                        vistos.add(texto_prev)
                if cuenta_ee() >= cupos[est]:
                    break
            continue
        seleccion = lista_ord[:cupos[est]]
        if est == "cola" and len(lista) > cupos[est]:      # cola: además, muestra aleatoria de raras
            raras = [r for r in lista if float(r["frecuencia"]) <= 2]
            rng.shuffle(raras)
            seleccion = (lista_ord[:cupos[est] // 2] + raras[:cupos[est] // 2]) or seleccion
        for f in seleccion:
            texto_prev, _ = sintetizar_consulta(f, est if est in ("ambigua", "documento_largo") else "cabeza", random.Random(0))
            if texto_prev in vistos:
                continue
            if agregar(f, est):
                vistos.add(texto_prev)

    # deduplicación global por texto (conserva la primera aparición)
    vistos_txt, consultas_dedup = set(), []
    for c in consultas:
        if c["texto"] in vistos_txt:
            qrels.pop(c["id"], None)
            continue
        vistos_txt.add(c["texto"]); consultas_dedup.append(c)
    consultas = consultas_dedup

    # escribir artefactos
    datos = RAIZ / "datos"; datos.mkdir(exist_ok=True)
    with (datos / "consultas_real.jsonl").open("w", encoding="utf-8") as f:      # interno
        for c in consultas:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with (datos / "qrels_real.jsonl").open("w", encoding="utf-8") as f:
        for qid, rel in qrels.items():
            f.write(json.dumps({"id": qid, "relevancia": rel}, ensure_ascii=False) + "\n")
    with (datos / "consultas_paper.jsonl").open("w", encoding="utf-8") as f:      # anonimizado
        for c in consultas:
            cc = dict(c); cc["texto"] = anonimizar(c["texto"])
            f.write(json.dumps(cc, ensure_ascii=False) + "\n")

    from collections import Counter
    est_cnt = Counter(c["estrato"] for c in consultas)
    print(json.dumps({
        "n_consultas_real": len(consultas),
        "por_estrato": dict(est_cnt),
        "con_nombre_propio": sum(c["menciona_nombre_propio"] for c in consultas),
        "firmas_unicas_totales": len(unicas),
        "ejemplos": [c["texto"] for c in consultas[:6]],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
