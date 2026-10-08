#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Escalera 1 (ampliada) — conjunto de evaluación real de alto poder estadístico.

Mejora clave frente a `construir_eval_real.py`: la unidad de muestreo es el PATRÓN de firma
distinto (reporte × combinación de filtros reales), no el nombre sintético. Esto evita la
pseudo-replicación (repetir el mismo patrón con distintos nombres, que produce consultas casi
idénticas y NO añade poder estadístico) y sube el n honesto del estrato entidad_exacta usando
los patrones reales que de verdad existen en el log (101 disponibles).

Silver: cada patrón hereda el reporte que su firma ejecutó (grado 2). Texto sintetizado desde
los filtros reales. Estratos: entidad_exacta / operacional / ambigua / documento_largo.

Privacidad: las firmas traen nombres de columna, no literales personales. Los nombres propios
de las consultas de entidad son sintéticos (gazetteer). Se emiten dos artefactos: interno y
anonimizado para el paper. Un subconjunto se marca como candidato a anotación gold.

Uso:  python3 construir_eval_real_ampliado.py
"""
from __future__ import annotations
import csv, json, random, unicodedata, collections
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.etiquetado import SLUG_POR_CLAVE, id_por_slug, reetiquetar_firma

RAIZ = Path(__file__).resolve().parent
SIG = RAIZ.parent / "data" / "athena_suid" / "suid_query_signatures.csv"
CORPUS = RAIZ / "corpus" / "corpus_v1.jsonl"
SEMILLA = 42

NOMBRES = ["Andrés Torres", "María Restrepo", "Julián Gómez", "Valentina Ríos",
           "Camilo Duarte", "Laura Ospina", "Sebastián Nieto", "Daniela Córdoba"]
INSTITUCIONES = ["Colegio San Marcos", "Club Deportivo El Faro", "Liga Atlántico",
                 "Escuela Nueva Esperanza", "Club Halcones del Norte"]
COLS_NOMBRE = {"full_name", "first_name", "first_last_name", "second_last_name",
               "document_number", "email", "institution_name", "group_name"}
COLS_INST = {"institution_name"}
COL_A_FRASE = {
    "current_stage": "por etapa", "stage": "por etapa", "stage_sequence": "por etapa",
    "category": "por categoría", "category_name": "por categoría",
    "discipline_status": "por estado de disciplina", "discipline_name": "por disciplina",
    "status": "por estado", "date": "por fecha", "event_code": "de un evento",
    "inst_region_name": "por región", "inst_department_name": "por departamento",
    "inst_municipality_name": "por municipio", "is_reinforcement": "de refuerzo",
    "group_name": "por grupo", "phase": "por fase",
}

CUPOS = {"entidad_exacta": 55, "operacional": 35, "documento_largo": 25, "ambigua": 20}
TOPE_POR_REPORTE = {"entidad_exacta": 18}          # balance: no todo de promoción
GOLD_POR_ESTRATO = {"entidad_exacta": 20, "operacional": 12, "documento_largo": 10, "ambigua": 8}


def _norm(s):
    s = unicodedata.normalize("NFKD", s.lower()); return "".join(c for c in s if not unicodedata.combining(c))


def cargar_corpus_ids():
    docs = [json.loads(l) for l in CORPUS.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [d["id"] for d in docs]


def mapear(nombre_logico, ids):
    n = _norm(nombre_logico)
    reglas = [(["promocion"], SLUG_POR_CLAVE["promocion"]), (["avance"], SLUG_POR_CLAVE["promocion"]), (["phases"], SLUG_POR_CLAVE["promocion"]),
              (["promotions_log"], SLUG_POR_CLAVE["promocion"]), (["grupos"], SLUG_POR_CLAVE["grupos"]), (["personal"], SLUG_POR_CLAVE["personal"]),
              (["documentacion"], SLUG_POR_CLAVE["documentacion"]), (["participacion", "intencion"], SLUG_POR_CLAVE["participacion"]),
              (["participacion"], SLUG_POR_CLAVE["participacion"]), (["individuales"], SLUG_POR_CLAVE["individual"]), (["dashboard"], SLUG_POR_CLAVE["dashboard"]),
              (["instituciones"], SLUG_POR_CLAVE["instituciones"]), (["progreso"], SLUG_POR_CLAVE["metas"]), (["metas"], SLUG_POR_CLAVE["metas"]),
              (["user_distribution"], SLUG_POR_CLAVE["distribucion"]), (["distribucion"], SLUG_POR_CLAVE["distribucion"]),
              (["federation"], SLUG_POR_CLAVE["federacion"]), (["federacion"], SLUG_POR_CLAVE["federacion"]),
              (["caidas_todas_etapas_resumen"], SLUG_POR_CLAVE["caidas_todas_resumen"]), (["caidas_todas_etapas"], SLUG_POR_CLAVE["caidas_todas"]),
              (["intent_changes"], SLUG_POR_CLAVE["cambios"]), (["cambios"], SLUG_POR_CLAVE["cambios"]),
              (["intent_delegations"], SLUG_POR_CLAVE["delegaciones"]), (["delegaciones"], SLUG_POR_CLAVE["delegaciones"]),
              (["caidas_resumen"], SLUG_POR_CLAVE["caidas_resumen"]), (["caidas"], SLUG_POR_CLAVE["caidas"])]
    for palabras, pref in reglas:
        if all(p in n for p in palabras):
            return id_por_slug(pref, ids)
    return None


def tema(nombre_logico):
    n = _norm(nombre_logico)
    for k, frase in [("promocion", "promoción de deportistas"), ("avance", "avance de etapa"),
                     ("grupos", "grupos"), ("personal", "personal de apoyo"),
                     ("documentacion", "documentación de deportistas"), ("participacion", "participación"),
                     ("individuales", "reporte individual de deportistas"), ("dashboard", "tablero de control"),
                     ("instituciones", "instituciones"), ("progreso", "progreso y cumplimiento de metas"),
                     ("metas", "cumplimiento de metas"), ("distribution", "distribución de usuarios"),
                     ("distribucion", "distribución de usuarios"), ("federation", "métricas por federación"),
                     ("federacion", "métricas por federación"), ("caidas", "pruebas de caídas"),
                     ("phases", "fases del evento"), ("delegations", "delegaciones de participación"),
                     ("changes", "cambios en la intención de participación")]:
        if k in n:
            return frase
    return "reporte del sistema"


def frase_persona(nombre_logico, nombre):
    n = _norm(nombre_logico)
    if "documentacion" in n: return f"documentación del deportista {nombre}"
    if "participacion" in n or "intencion" in n: return f"intención de participación de {nombre}"
    if "personal" in n: return f"personal de apoyo del deportista {nombre}"
    if "grupos" in n: return f"grupo del deportista {nombre}"
    if "individuales" in n: return f"reporte individual del deportista {nombre}"
    return f"estado de promoción del deportista {nombre}"


def filtros_de(fila):
    campos = (fila.get("keywords_where", "") + "|" + fila.get("columnas_clave", "")).split("|")
    return [c.strip() for c in campos if c.strip()]


def clasificar(combo):
    fs = set(combo)
    if fs & COLS_NOMBRE: return "entidad_exacta"
    if len(fs) <= 1: return "ambigua"
    if len(fs) >= 5: return "documento_largo"
    return "operacional"


def _frases_filtro(combo):
    frases = [COL_A_FRASE[c] for c in combo if c in COL_A_FRASE]
    return list(dict.fromkeys(frases))[:3]


def sintetizar(nombre_logico, combo, estrato, nombre):
    t = tema(nombre_logico)
    if estrato == "entidad_exacta":
        if set(combo) & COLS_INST and "grupos" not in _norm(nombre_logico):
            base = f"{t} de la institución {nombre}"
        else:
            base = frase_persona(nombre_logico, nombre)
        extra = _frases_filtro(combo)                 # los filtros extra distinguen patrones reales
        return (base + " " + ", ".join(extra)).strip() if extra else base
    if estrato == "ambigua":
        return t.split()[0]
    frases = _frases_filtro(combo)
    return (f"{t} " + ", ".join(frases)).strip() if frases else t


def main():
    rng = random.Random(SEMILLA)
    ids = cargar_corpus_ids()
    # Firmas con la etiqueta de reporte CORREGIDA (ver lib/etiquetado.py).
    rows = [reetiquetar_firma(r) for r in csv.DictReader(SIG.open(encoding="utf-8"))
              if r.get("es_wrapper_count") != "True"]   # sin gemelos COUNT(*) de paginación

    # agregar frecuencia por PATRÓN distinto (reporte × combo de filtros)
    pat = collections.defaultdict(float)
    for r in rows:
        pat[(r["nombre_logico"], tuple(sorted(filtros_de(r))))] += float(r["frecuencia"])
    patrones = [{"nombre_logico": k[0], "combo": k[1], "frecuencia": v} for k, v in pat.items()]

    porestrato = collections.defaultdict(list)
    for p in patrones:
        porestrato[clasificar(p["combo"])].append(p)

    consultas, qrels, cont = [], {}, 0
    disponibles = {e: len(v) for e, v in porestrato.items()}
    # Deduplicación GLOBAL (entre estratos): un mismo texto no puede contarse dos veces
    # como consultas independientes (pseudo-replicación).
    vistos: set[str] = set()

    for est, cupo in CUPOS.items():
        lista = sorted(porestrato[est], key=lambda p: -p["frecuencia"])
        por_reporte = collections.Counter()
        tope = TOPE_POR_REPORTE.get(est)
        n_est, i_nom = 0, 0
        for p in lista:
            if n_est >= cupo: break
            if tope and por_reporte[p["nombre_logico"]] >= tope: continue
            obj = mapear(p["nombre_logico"], ids)
            if not obj: continue
            if est == "entidad_exacta":
                pool = INSTITUCIONES if (set(p["combo"]) & COLS_INST and "grupos" not in _norm(p["nombre_logico"])) else NOMBRES
                nombre = pool[i_nom % len(pool)]; i_nom += 1
            else:
                nombre = None
            texto = sintetizar(p["nombre_logico"], p["combo"], est, nombre)
            if texto in vistos: continue
            cont += 1; qid = f"r{cont:03d}"
            # Control: la misma consulta con el nombre propio borrado. Si la métrica no
            # cambia, el estrato mide el tema del reporte, no la entidad.
            sin_nombre = (" ".join(texto.replace(nombre, " ").split()) if nombre else texto)
            consultas.append({"id": qid, "texto": texto, "texto_sin_nombre": sin_nombre, "estrato": est,
                              "reporte_objetivo": obj, "menciona_nombre_propio": est == "entidad_exacta",
                              "frecuencia_real": int(p["frecuencia"]), "capa": "silver",
                              "firma_reporte": p["nombre_logico"]})
            qrels[qid] = {obj: 2.0}
            vistos.add(texto); por_reporte[p["nombre_logico"]] += 1; n_est += 1

    # marcar subconjunto candidato a GOLD (muestra estratificada, semilla fija)
    porest_q = collections.defaultdict(list)
    for c in consultas: porest_q[c["estrato"]].append(c)
    for est, k in GOLD_POR_ESTRATO.items():
        muestra = rng.sample(porest_q[est], min(k, len(porest_q[est])))
        for c in muestra:
            c["capa"] = "gold_candidate"

    datos = RAIZ / "datos"; datos.mkdir(exist_ok=True)
    with (datos / "consultas_real_ampliado.jsonl").open("w", encoding="utf-8") as f:
        for c in consultas: f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with (datos / "qrels_real_ampliado.jsonl").open("w", encoding="utf-8") as f:
        for qid, rel in qrels.items(): f.write(json.dumps({"id": qid, "relevancia": rel}, ensure_ascii=False) + "\n")
    with (datos / "consultas_real_ampliado_paper.jsonl").open("w", encoding="utf-8") as f:
        for c in consultas: f.write(json.dumps(c, ensure_ascii=False) + "\n")   # ya sin PII (nombres sintéticos)

    est_cnt = collections.Counter(c["estrato"] for c in consultas)
    gold_cnt = collections.Counter(c["estrato"] for c in consultas if c["capa"] == "gold_candidate")
    print(json.dumps({"n_total": len(consultas),
                      "patrones_disponibles": disponibles,
                      "por_estrato": dict(est_cnt),
                      "gold_candidate_por_estrato": dict(gold_cnt),
                      "n_gold_total": sum(gold_cnt.values()),
                      "ejemplos_entidad_exacta": [c["texto"] for c in consultas if c["estrato"]=="entidad_exacta"][:6]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
