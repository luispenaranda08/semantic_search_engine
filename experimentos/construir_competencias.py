#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Escalera 2 — Materialización del dominio de Competencias (entidad Prueba Regional).

Compone la entidad sintética Prueba Regional = disciplina (deporte + categoría) x región,
con la fase como atributo, a partir de los catálogos locales de `data/competencias_suid/`.
Emite documentos en el MISMO esquema que `preprocess_corpus.py` (id/titulo/descripcion/
metadatos_ontologia/prioridad/cdr/nombre_propio_buscable/fuentes/texto_indexable), de modo
que se integran al corpus sin rediseñar la tubería.

Privacidad: solo usa catálogos (deportes, categorías, regiones) y conteos AGREGADOS; no
toca ninguna fila con datos de personas. Los conteos de volumen entran como metadatos.

Uso:
    python3 construir_competencias.py           # escribe corpus/corpus_competencias.jsonl
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATA = RAIZ.parent / "data" / "competencias_suid"

FASES = ["Fase Municipal", "Fase Departamental", "Fase Regional", "Fase Nacional"]


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def cargar_catalogos() -> tuple[list[dict], list[str], dict]:
    disciplinas = json.loads((DATA / "catalogo_disciplinas.json").read_text(encoding="utf-8"))
    # distintas combinaciones (deporte, categoría), preservando tipo
    vistos, discs = set(), []
    for d in disciplinas:
        clave = (d["sport_name"], d.get("category_name") or "Única")
        if clave not in vistos:
            vistos.add(clave)
            discs.append({"sport": d["sport_name"],
                          "categoria": d.get("category_name") or "Única",
                          "tipo": d.get("sport_type_name") or "Individual"})
    regiones = sorted({r["region_name"] for r in
                       csv.DictReader((DATA / "departamento_a_region.csv").open(encoding="utf-8"))})
    conteos = json.loads((DATA / "conteos.json").read_text(encoding="utf-8")).get("conteos", {})
    return discs, regiones, conteos


def construir_doc(disc: dict, region: str, conteos: dict, idx: int) -> dict:
    sport, categoria, tipo = disc["sport"], disc["categoria"], disc["tipo"]
    nombre = f"Prueba Regional: {sport} ({categoria}) — Región {region}"
    doc_id = f"cr_{idx:04d}_prueba_regional_{_slug(sport)}_{_slug(categoria)}_{_slug(region)}"

    mil = lambda n: f"{n:,}".replace(",", ".")     # separador de miles con punto (es)
    part_total = mil(conteos.get("bronze_suid_events.participant_disciplines", 0))
    res_total = mil(conteos.get("bronze_suid_events.result_entries", 0))
    combos = conteos.get("combinaciones_evento_fase_disciplina", 0)

    descripcion = (
        f"La {nombre} es una prueba de competencia del sistema de gestión deportiva, "
        f"correspondiente a la disciplina {sport} en la categoría {categoria} "
        f"({tipo.lower()}), disputada en la región {region}. Es una entidad de negocio "
        f"compuesta: no existe hoy como un reporte dedicado, sino que se arma componiendo la "
        f"disciplina, su categoría, la fase de competencia y la región deportiva. Expone los "
        f"resultados, marcas y clasificados de la prueba a lo largo de sus fases "
        f"({', '.join(FASES)}). El dominio de competencias reúne en total {part_total} "
        f"participaciones de deportista por disciplina y {res_total} resultados de "
        f"competencia registrados, distribuidos en {combos} combinaciones de evento, fase y "
        f"disciplina; ninguno de estos datos está expuesto hoy por un reporte del sistema."
    )

    entidades = ["Disciplina Deportiva", "Categoría", "Etapa/Fase", "Región",
                 "Evento", "Prueba Regional", "Resultado", "Deportista", "Ubicación Geográfica"]
    relaciones = [
        "Prueba Regional pertenece_a Disciplina Deportiva",
        "Prueba Regional tiene Categoría",
        "Prueba Regional se_disputa_en Región",
        "Prueba Regional ocurre_en Etapa/Fase",
        "Prueba Regional pertenece_a Evento",
        "Prueba Regional produce Resultado",
        "Deportista compite_en Prueba Regional",
        "Disciplina Deportiva se_practica_en Región",
    ]
    conceptos = [
        f"Buscar la prueba de {sport} en la región {region}",
        f"Resultados y clasificados de {sport} categoría {categoria}",
        f"Pruebas de la disciplina {sport} por fase de competencia",
        f"Competencias de {sport} en {region}",
    ]
    atributos = ["sport_name", "category_name", "region_name", "phase_name",
                 "discipline_type", "event_code", "result_position"]
    sinonimos = ["Prueba Regional", "prueba", "competencia", "certamen", sport, categoria,
                 "Disciplina Deportiva", "deporte", "modalidad", "Etapa/Fase", "fase",
                 "ronda", "eliminatoria", "Región", region, "zona", "Resultado",
                 "marca", "clasificados", "ranking", "podio"]

    phi = (" Entidades: " + ", ".join(entidades) + ". Sinónimos: " + ", ".join(sinonimos) +
           ". Búsquedas: " + "; ".join(conceptos) + ".")
    texto_indexable = descripcion + phi

    return {
        "id": doc_id,
        "titulo": nombre,
        "descripcion": descripcion,
        "metadatos_ontologia": {
            "entidades_principales": entidades,
            "relaciones": relaciones,
            "conceptos_busqueda": conceptos,
            "atributos_filtrables": atributos,
            "sinonimos": sinonimos,
        },
        "prioridad": "V2 (vacío de cobertura)",
        "cdr": 0,                       # cero demanda observada: es el hallazgo, no un error
        "nombre_propio_buscable": False,
        "dominio": "competencias",
        "fuentes": ["bronze_suid_events.disciplines", "bronze_suid_events.events",
                    "bronze_suid_events.phases", "bronze_suid_events.result_entries",
                    "departamento_a_region"],
        "texto_indexable": texto_indexable,
    }


def main() -> None:
    discs, regiones, conteos = cargar_catalogos()
    docs, idx = [], 0
    for disc in discs:
        for region in regiones:
            idx += 1
            docs.append(construir_doc(disc, region, conteos, idx))

    salida = RAIZ / "corpus" / "corpus_competencias.jsonl"
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    resumen = {
        "n_documentos_competencias": len(docs),
        "disciplinas_distintas": len(discs),
        "regiones": len(regiones),
        "fases_como_atributo": len(FASES),
        "ejemplo_titulo": docs[0]["titulo"] if docs else None,
    }
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
