#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conjunto de evaluación DIFÍCIL: paráfrasis y consultas coloquiales con brecha de vocabulario.

Motivo. En los conjuntos anteriores la mayoría de las consultas ya cae en la posición 1 para
todas las configuraciones (techo de nDCG), y por eso hay pocos pares con diferencia no nula
y poco poder estadístico (ver GUIA_SUSTENTACION_DETALLADA.md §16.2). Este conjunto fuerza
consultas que NO comparten vocabulario con la descripción del reporte, que es donde la
señal densa y el puente de la ontología deberían diferenciarse de BM25.

Diseño (para no sesgar a favor de la ontología):
  * Las consultas son paráfrasis escritas a mano del propósito de cada reporte. Cubren los 13
    reportes cuyo propósito es inequívoco; se omiten los 4 reportes de «pruebas de caídas»
    (su significado de negocio debe confirmarlo el autor antes de redactar consultas).
  * El NIVEL de dificultad NO se asigna a mano: se calcula con el solape de raíces (Snowball)
    entre la consulta y (a) la descripción del documento (sin las palabras de plantilla) y
    (b) el bloque de ontología que se inyecta.
        A_puente_ontologia : 0 raíces compartidas con la descripción y >= 1 con el bloque de
                             ontología  -> la ontología PUEDE ayudar (cierra la brecha).
        B_sin_puente       : 0 raíces compartidas con ambos -> ni BM25 ni la ontología pueden
                             ayudar; solo la semántica densa. Es el control contra el sesgo
                             de haber redactado consultas con los sinónimos de la ontología.
        C_con_solape       : comparte al menos una raíz con la descripción.
  * Juicio: el reporte objetivo recibe grado 2 (known-item). Capa «sintetico_dificil»,
    pendiente de revisión por el autor y de anotación de expertos (ver hoja_anotacion).

Salida: datos/consultas_dificil.jsonl, datos/qrels_dificil.jsonl (campo `estrato` = nivel).
Uso:  python3 construir_eval_dificil.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.etiquetado import SLUG_POR_CLAVE, id_por_slug
from lib.indexes import tokenizar_es

RAIZ = Path(__file__).resolve().parent

# Palabras de la plantilla de descripción que no aportan significado de dominio.
PLANTILLA = {"reporte", "sistema", "gestion", "deportiva", "construye", "combinando", "informacion",
             "periodo", "analizado", "solicito", "veces", "consulta", "real", "datos", "representa",
             "aproximadamente", "toda", "demanda", "reportes", "observada", "solicitud", "tipica",
             "mediana", "procesa", "alrededor", "megabytes", "uno", "resumen", "metricas", "sobre"}

# clave -> consultas (paráfrasis; sin copiar el título del reporte)
CONSULTAS = {
    "individual": [
        "listado de atletas por modalidad y municipio",
        "competidores con alguna discapacidad registrados por departamento",
        "relación completa de inscritos con sus datos básicos",
        "ficha con la información de cada muchacho que juega",
    ],
    "grupos": [
        "equipos de cada colegio por deporte",
        "delegación de grupo de una escuela y su nivel de competencia",
        "cómo están conformados los conjuntos que representan a cada centro educativo",
        "cuántas camadas llevó cada plantel a los juegos",
    ],
    "personal": [
        "entrenadores y acompañantes de cada delegación",
        "cuerpo técnico asignado a un torneo",
        "quiénes viajan con los niños además de los jugadores",
        "profesores y directivos que acompañan a los equipos",
    ],
    "documentacion": [
        "certificados pendientes de un atleta",
        "requisitos documentales rechazados por competencia",
        "papeles que faltan por subir de cada participante",
        "qué trámites de soporte siguen sin aprobar",
    ],
    "participacion": [
        "inscripción de la institución en la competencia",
        "qué planteles confirmaron asistencia",
        "quiénes dijeron que sí van a ir al certamen",
        "colegios que ya confirmaron que van a competir",
    ],
    "dashboard": [
        "estado global de la competencia por zona",
        "panorama de cómo va todo",
        "vista rápida con los números principales del evento",
        "indicadores generales del torneo por región",
    ],
    "promocion": [
        "ascenso de categoría de un atleta a la siguiente ronda",
        "clasificación a la siguiente fase de un jugador",
        "quién pasó a la etapa que sigue",
        "avance de los muchachos hacia la final",
    ],
    "instituciones": [
        "colegios por departamento",
        "entidades educativas o deportivas por región",
        "directorio de planteles participantes",
        "dónde queda cada centro y a qué ciudad pertenece",
    ],
    "metas": [
        "porcentaje de cobertura alcanzado por departamento",
        "cobertura por región frente a lo planeado",
        "cuánto falta para llegar al objetivo en cada parte del país",
        "avance frente a lo propuesto territorio por territorio",
    ],
    "distribucion": [
        "cuántas personas hay registradas según su rol en el sistema",
        "reparto de cuentas por tipo de perfil",
        "cuántos entrenadores, deportistas y administradores hay en la plataforma",
        "número de cuentas activas por perfil de acceso",
    ],
    "federacion": [
        "desempeño por organización nacional de cada disciplina",
        "cifras agrupadas por ente federado",
        "comparación entre ligas y organismos rectores del deporte",
        "balance de cada ente que dirige un deporte",
    ],
    "cambios": [
        "quiénes se retiraron o modificaron su inscripción",
        "arrepentimientos de colegios que antes iban a competir",
        "quién cambió de decisión sobre asistir",
        "modificaciones a lo confirmado antes",
    ],
    "delegaciones": [
        "comitivas que viajarán por institución",
        "cuántas delegaciones lleva cada club",
        "conjunto de personas que representa a una escuela en el evento",
        "grupos oficiales enviados por cada entidad",
    ],
}


def stems(texto: str) -> set[str]:
    return {t for t in tokenizar_es(texto) if t not in PLANTILLA}


def main() -> None:
    docs = [json.loads(l) for l in (RAIZ / "corpus/corpus_v1.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    ids = [d["id"] for d in docs]
    por_id = {d["id"]: d for d in docs}

    consultas, qrels, cont = [], {}, 0
    for clave, textos in CONSULTAS.items():
        obj = id_por_slug(SLUG_POR_CLAVE[clave], ids)
        if obj is None:
            raise SystemExit(f"No se encontró el reporte para la clave {clave!r}")
        d = por_id[obj]
        s_desc = stems(d["descripcion"]) | stems(d["titulo"])
        s_onto = stems(d["texto_indexable"]) - s_desc
        for t in textos:
            sq = stems(t)
            if sq & s_desc:
                nivel = "C_con_solape"
            elif sq & s_onto:
                nivel = "A_puente_ontologia"
            else:
                nivel = "B_sin_puente"
            cont += 1
            qid = f"d{cont:03d}"
            consultas.append({"id": qid, "texto": t, "estrato": nivel, "reporte_objetivo": obj,
                              "menciona_nombre_propio": False, "capa": "sintetico_dificil",
                              "solape_desc": sorted(sq & s_desc), "solape_onto": sorted(sq & s_onto),
                              "doc_con_ontologia": len(d["texto_indexable"]) > len(d["descripcion"])})
            qrels[qid] = {obj: 2.0}

    datos = RAIZ / "datos"
    with (datos / "consultas_dificil.jsonl").open("w", encoding="utf-8") as f:
        for c in consultas:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with (datos / "qrels_dificil.jsonl").open("w", encoding="utf-8") as f:
        for qid, rel in qrels.items():
            f.write(json.dumps({"id": qid, "relevancia": rel}, ensure_ascii=False) + "\n")

    cnt = collections.Counter(c["estrato"] for c in consultas)
    sin_onto = sum(1 for c in consultas if not c["doc_con_ontologia"])
    print(json.dumps({"n": len(consultas), "por_nivel": dict(cnt),
                      "consultas_cuyo_objetivo_no_tiene_bloque_de_ontologia": sin_onto,
                      "docs_sin_bloque_de_ontologia": sum(
                          1 for d in docs if len(d["texto_indexable"]) <= len(d["descripcion"]))},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
