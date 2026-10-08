#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el conjunto de evaluación estratificado y sus juicios de relevancia.

Protocolo: evaluación por documento conocido (known-item). Cada consulta se
construye a partir de artefactos reales (reportes, entidades y sinónimos de la
ontología, mapeo de competencias) apuntando a un reporte objetivo conocido; ese
reporte recibe grado 2 en los juicios. Es un protocolo de recuperación estándar y
no fabrica juicios humanos. Los nombres propios usados son SINTÉTICOS (no
corresponden a ninguna persona real) y solo sirven para dar forma realista a las
consultas de nombre propio; el objetivo de la consulta es el reporte, no la persona.

Estratos (proporciones objetivo):
  * entidad_exacta   35 %   nombre de entidad y/o nombre propio (Deportista, Institución)
  * ambigua          22 %   término corto con varias lecturas
  * documento_largo  22 %   descripción de una necesidad
  * competencias     18 %   fuera de la v1; miden el vacío de cobertura (qrel vacío)

Los expertos pueden extender los juicios (grados 1 sobre reportes secundarios) sin
cambiar el formato; el marco los admite.

Uso:
    python3 generar_consultas.py
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent

# Nombres SINTÉTICOS (no reales). "Andrés Torres" aparece como ejemplo sintético en
# la propia ontología; los demás son inventados para este conjunto de prueba.
NOMBRES_SINTETICOS = ["Andrés Torres", "María Restrepo", "Julián Gómez", "Valentina Ríos"]
INSTITUCIONES_SINTETICAS = ["Colegio San Marcos", "Club Deportivo El Faro", "Liga Atlántico"]


def cargar_corpus() -> list[dict]:
    ruta = RAIZ / "corpus" / "corpus_v1.jsonl"
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def id_por_palabra(docs: list[dict], *claves: str) -> str | None:
    """Primer doc cuyo título (en minúsculas) contiene todas las claves."""
    for d in docs:
        t = d["titulo"].lower()
        if all(c in t for c in claves):
            return d["id"]
    return None


def construir(docs: list[dict]) -> tuple[list[dict], dict]:
    id_promo = id_por_palabra(docs, "promoción")
    id_grupos = id_por_palabra(docs, "grupos")
    id_personal = id_por_palabra(docs, "personal")
    id_doc = id_por_palabra(docs, "documentación")
    id_part = id_por_palabra(docs, "participación")
    id_inst = id_por_palabra(docs, "instituciones")
    id_metas = id_por_palabra(docs, "metas")
    id_tablero = id_por_palabra(docs, "tablero")

    consultas: list[dict] = []
    qrels: dict[str, dict[str, float]] = {}
    cont = 0

    def add(texto: str, estrato: str, objetivo: str | None,
            nombre_propio: bool = False, secundarios: list[str] | None = None) -> None:
        nonlocal cont
        cont += 1
        qid = f"q{cont:03d}"
        consultas.append({
            "id": qid, "texto": texto, "estrato": estrato,
            "reporte_objetivo": objetivo, "menciona_nombre_propio": nombre_propio,
        })
        rel: dict[str, float] = {}
        if objetivo:
            rel[objetivo] = 2.0
        for s in (secundarios or []):
            if s and s != objetivo:
                rel[s] = 1.0
        qrels[qid] = rel

    # ---- ENTIDAD EXACTA / NOMBRE PROPIO (~35 %) ----
    for nom in NOMBRES_SINTETICOS:
        add(f"estado de promoción de {nom}", "entidad_exacta", id_promo, True)
        add(f"en qué fase va el deportista {nom}", "entidad_exacta", id_promo, True)
    for inst in INSTITUCIONES_SINTETICAS:
        add(f"reporte de la institución {inst}", "entidad_exacta", id_inst, True,
            secundarios=[id_grupos])
    add("documentación del deportista Julián Gómez", "entidad_exacta", id_doc, True)
    add("grupos de la institución Colegio San Marcos", "entidad_exacta", id_grupos, True,
        secundarios=[id_inst])
    add("personal de apoyo del deportista Andrés Torres", "entidad_exacta", id_personal, True)
    add("intención de participación de María Restrepo", "entidad_exacta", id_part, True)
    add("cumplimiento de metas del deportista Valentina Ríos", "entidad_exacta", id_metas, True)
    add("reporte individual del deportista Julián Gómez", "entidad_exacta",
        id_por_palabra(docs, "individual"), True)

    # ---- AMBIGUAS (~22 %) ----
    add("grupos", "ambigua", id_grupos)
    add("avance", "ambigua", id_promo)
    add("documentos", "ambigua", id_doc)
    add("participación", "ambigua", id_part)
    add("personal", "ambigua", id_personal)
    add("metas", "ambigua", id_metas)
    add("instituciones", "ambigua", id_inst)
    add("promoción", "ambigua", id_promo)
    add("tablero", "ambigua", id_tablero)
    add("etapas", "ambigua", id_promo)
    add("delegaciones", "ambigua", id_por_palabra(docs, "delegaciones"))
    add("federaciones", "ambigua", id_por_palabra(docs, "federación"))
    add("distribución", "ambigua", id_por_palabra(docs, "distribución"))

    # ---- DOCUMENTO LARGO / NECESIDAD (~22 %) ----
    add("quiero ver en qué etapa está cada deportista y si ya cumplió los requisitos "
        "para pasar a la siguiente fase de la competencia", "documento_largo", id_promo)
    add("necesito el listado de deportistas de una institución con el estado de su "
        "documentación al día", "documento_largo", id_doc, secundarios=[id_grupos])
    add("cómo saber qué grupos o delegaciones tiene registrada cada institución y su "
        "personal de apoyo", "documento_largo", id_grupos, secundarios=[id_personal])
    add("resumen de cuántos deportistas han sido promovidos, rechazados o siguen "
        "pendientes en el evento", "documento_largo", id_promo)
    add("reporte con las metas de cada federación y su nivel de cumplimiento por región",
        "documento_largo", id_metas)
    add("quiénes manifestaron intención de participar y cómo se distribuyen por "
        "delegación", "documento_largo", id_part)
    add("panorama general del tablero de control con los indicadores de la plataforma",
        "documento_largo", id_tablero)
    add("necesito el personal de apoyo, entrenadores y acompañantes asignados a cada "
        "grupo", "documento_largo", id_personal)
    add("cómo va la distribución de usuarios registrados en el sistema", "documento_largo",
        id_por_palabra(docs, "distribución"))
    add("estado de la documentación y los soportes cargados por cada deportista para "
        "habilitar su promoción", "documento_largo", id_doc, secundarios=[id_promo])

    # ---- COMPETENCIAS (~18 %) — fuera de la v1, qrel vacío (vacío de cobertura) ----
    for texto in [
        "Atletismo Pre-Juvenil en Región Caribe 1",
        "resultados de natación en fase regional",
        "disciplinas de la categoría juvenil en los juegos nacionales",
        "qué pruebas hay de atletismo en la región pacífico",
        "resultados de la competencia de la fase departamental",
        "ranking de la prueba de ciclismo en la región centro",
        "eventos deportivos y sus fases de competencia",
        "clasificados de la disciplina de baloncesto por región",
        "marcas y resultados de la final nacional de atletismo",
        "competencias de para-deporte por clasificación funcional",
        "cuántos participantes hay por disciplina en cada región",
    ]:
        add(texto, "competencias", None)

    return consultas, qrels


def main() -> None:
    docs = cargar_corpus()
    consultas, qrels = construir(docs)

    (RAIZ / "datos").mkdir(exist_ok=True)
    with (RAIZ / "datos" / "consultas_eval.jsonl").open("w", encoding="utf-8") as f:
        for c in consultas:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with (RAIZ / "datos" / "qrels.jsonl").open("w", encoding="utf-8") as f:
        for qid, rel in qrels.items():
            f.write(json.dumps({"id": qid, "relevancia": rel}, ensure_ascii=False) + "\n")

    from collections import Counter
    estratos = Counter(c["estrato"] for c in consultas)
    n = len(consultas)
    resumen = {"n_consultas": n,
               "por_estrato": {k: f"{v} ({100*v/n:.0f}%)" for k, v in estratos.items()},
               "con_nombre_propio": sum(c["menciona_nombre_propio"] for c in consultas),
               "con_gold_en_v1": sum(1 for qid in qrels if qrels[qid])}
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
