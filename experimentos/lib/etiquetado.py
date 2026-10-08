#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reglas compartidas de etiquetado de reportes (EDA ↔ evaluación).

Corrige el sesgo del clasificador original: una consulta se llamaba "Reporte de Promoción"
si tocaba el Reporte Individual de Deportistas y contenía palabras como `category` o `stage`
(que son NOMBRES DE COLUMNA de ese mismo reporte: `category_name`,
`sport_development_stage`, `current_stage`). Así el listado completo de deportistas quedaba
contado como promoción. Regla corregida: hay promoción solo si la consulta usa el registro
de promociones (`promotions_log`/`phases`) o calcula/filtra un estado de promoción.
"""
from __future__ import annotations

import re

PROMO_TABLAS = {"promotions_log", "phases"}
PROMO_COLUMNA = re.compile(r"promo(cion|tion|vi|ted)|estado_log", re.I)
NOMBRE_INDIVIDUAL = "Listado / reporte de atletas individuales"

# Id de corpus por nombre (slug del título), no por posición en el ranking: el prefijo
# ri_00N cambia si cambia el orden de demanda, el slug no.
SLUG_POR_CLAVE = {
    "promocion": "reporte_de_promocion_de_deportistas",
    "grupos": "reporte_de_grupos",
    "personal": "reporte_de_personal_de_apoyo",
    "documentacion": "reporte_de_documentacion_de_deportistas",
    "participacion": "reporte_de_participacion",
    "individual": "reporte_individual_de_deportistas",
    "dashboard": "reporte_sobre_resumen_del_tablero_de_control",
    "instituciones": "reporte_de_instituciones",
    "metas": "reporte_de_progreso_y_cumplimiento_de_metas",
    "distribucion": "reporte_sobre_distribucion_de_usuarios",
    "federacion": "reporte_sobre_metricas_por_federacion_deportiva",
    "caidas_todas": "reporte_sobre_pruebas_de_caidas_todas_las_etapas",
    "cambios": "reporte_de_cambios_en_la_intencion_de_participacion",
    "delegaciones": "reporte_de_delegaciones_de_participacion",
    "caidas": "reporte_sobre_pruebas_de_caidas",
    "caidas_resumen": "reporte_sobre_resumen_de_pruebas_de_caidas",
    "caidas_todas_resumen": "reporte_sobre_resumen_de_pruebas_de_caidas_todas_las_etapas",
}


def es_promocion(tablas, columnas) -> bool:
    return bool(PROMO_TABLAS & set(tablas)) or any(PROMO_COLUMNA.search(c) for c in columnas)


def reetiquetar_firma(f: dict) -> dict:
    """Devuelve la firma con `nombre_logico` corregido (y la etiqueta original aparte)."""
    nombre = f["nombre_logico"]
    tablas = f["tablas"] if isinstance(f["tablas"], list) else [t for t in str(f["tablas"]).split("|") if t]
    cols = []
    for k in ("columnas_clave", "keywords_where"):
        v = f.get(k) or []
        cols += v if isinstance(v, list) else [x for x in str(v).split("|") if x]
    if "promoci" in nombre.lower() and not es_promocion(tablas, cols):
        f = {**f, "nombre_logico": NOMBRE_INDIVIDUAL, "nombre_logico_original": nombre}
    return f


def id_por_slug(slug: str, ids) -> str | None:
    for cid in ids:
        if cid.split("_", 2)[-1] == slug:
            return cid
    return None
