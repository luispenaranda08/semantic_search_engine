#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pipeline de preprocesamiento: construye el corpus indexable de la Versión 1.

Toma los artefactos ya validados del análisis exploratorio (descripciones en
lenguaje natural, tabla maestra de demanda, ontología y metadatos por reporte) y
produce un documento enriquecido por Reporte Indexable, con el esquema exacto que
consume el framework de evaluación.

Principios de diseño:
  * Inyección SELECTIVA de metadatos de ontología (lección de ECLASS): al texto
    indexable se le añaden entidades, sinónimos y conceptos de búsqueda, no el
    volcado completo de atributos.
  * Dos textos por documento: la descripción cruda (para las configuraciones sin
    ontología, 1 y 3) y el texto enriquecido (para las configuraciones 2, 4 y 5).
  * Privacidad estricta: el corpus no contiene ningún dato personal. Una auditoría
    anti-PII corre sobre la salida antes de darla por buena.

Uso:
    python3 preprocess_corpus.py            # usa config.yaml
    python3 preprocess_corpus.py --config otra_config.yaml
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

import yaml

RAIZ_EXP = Path(__file__).resolve().parent
TAG_NOMBRE_PROPIO = "entidad_exacta_nombre_propio"


# --------------------------------------------------------------------------- #
# Normalización
# --------------------------------------------------------------------------- #
def normalizar(s: str) -> str:
    """Normaliza para texto legible: NFC, espacios colapsados, sin saltos."""
    if not s:
        return ""
    s = unicodedata.normalize("NFC", str(s)).replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def slug(s: str) -> str:
    """Convierte un título a un identificador estable en snake_case sin tildes."""
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


# --------------------------------------------------------------------------- #
# Carga de fuentes
# --------------------------------------------------------------------------- #
def cargar_descripciones(ruta: Path) -> dict[str, str]:
    with ruta.open(encoding="utf-8") as f:
        return {r["reporte"]: r["descripcion_semantica"] for r in csv.DictReader(f)}


def cargar_tabla_maestra(ruta: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with ruta.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["Reporte (nombre en lenguaje natural)"]] = {
                "cdr": int(r["Frecuencia de consultas de datos"]),
                "prioridad": r["Prioridad de indexación"].strip(),
                "fuentes": [x.strip() for x in r["Fuentes de datos principales"].split(",")],
            }
    return out


def cargar_ontologia(ruta: Path) -> dict:
    with ruta.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def cargar_metadatos(ruta: Path) -> dict[str, dict]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return {e["reporte"]: e for e in datos}


# --------------------------------------------------------------------------- #
# Construcción del documento enriquecido
# --------------------------------------------------------------------------- #
def sinonimos_de(entidades: list[str], ontologia: dict) -> list[str]:
    """Reúne, sin duplicar, los sinónimos de las clases que cubre el documento."""
    clases = ontologia.get("clases", {})
    vistos, out = set(), []
    for ent in entidades:
        cuerpo = clases.get(ent, {})
        for termino in [ent, *cuerpo.get("sinonimos", [])]:
            clave = slug(termino)
            if clave and clave not in vistos:
                vistos.add(clave)
                out.append(normalizar(termino))
    return out


def serializar_metadatos(meta: dict) -> str:
    """Serializa los metadatos de ontología como texto puente (inyección selectiva)."""
    partes: list[str] = []
    if meta.get("entidades_principales"):
        partes.append("Entidades: " + ", ".join(meta["entidades_principales"]) + ".")
    if meta.get("conceptos_busqueda"):
        partes.append("Responde a: " + "; ".join(meta["conceptos_busqueda"]) + ".")
    if meta.get("sinonimos"):
        partes.append("También llamado: " + ", ".join(meta["sinonimos"][:20]) + ".")
    return " ".join(partes)


def construir_documentos(cfg: dict) -> list[dict]:
    """Construye un documento enriquecido por reporte, ordenados por demanda (CDR)."""
    r = cfg["rutas"]
    descripciones = cargar_descripciones(RAIZ_EXP / r["descripciones"])
    maestra = cargar_tabla_maestra(RAIZ_EXP / r["tabla_maestra"])
    ontologia = cargar_ontologia(RAIZ_EXP / r["ontologia"])
    metadatos = cargar_metadatos(RAIZ_EXP / r["metadatos_reporte"])

    orden = sorted(descripciones, key=lambda t: maestra.get(t, {}).get("cdr", 0), reverse=True)

    docs: list[dict] = []
    for i, titulo in enumerate(orden, start=1):
        fila = maestra.get(titulo, {})
        m = metadatos.get(titulo, {})
        entidades = m.get("entidades_principales", [])
        sinonimos = sinonimos_de(entidades, ontologia)

        meta_onto = {
            "entidades_principales": entidades,
            "relaciones": m.get("relaciones_clave", []),
            "conceptos_busqueda": m.get("conceptos_de_negocio", []),
            "atributos_filtrables": m.get("atributos_filtrables", []),
            "sinonimos": sinonimos,
        }
        descripcion = normalizar(descripciones[titulo])
        bloque = serializar_metadatos(meta_onto)
        texto_indexable = normalizar(descripcion + (" " + bloque if bloque else ""))

        docs.append({
            "id": f"ri_{i:03d}_{slug(titulo)}",
            "titulo": titulo,
            "descripcion": descripcion,
            "metadatos_ontologia": meta_onto,
            "prioridad": fila.get("prioridad", "Baja"),
            "cdr": fila.get("cdr", 0),
            "nombre_propio_buscable": bool(m.get("tiene_busqueda_por_nombre_propio", False)),
            "fuentes": fila.get("fuentes", []),
            "texto_indexable": texto_indexable,
        })
    return docs


# --------------------------------------------------------------------------- #
# Auditoría de privacidad y estadísticas
# --------------------------------------------------------------------------- #
PATRONES_PII = {
    "email": re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I),
    "telefono": re.compile(r"\b\d{7,}\b"),
}


def auditar_pii(docs: list[dict]) -> dict:
    total = 0
    for d in docs:
        blob = d["descripcion"] + " " + d["texto_indexable"] + " " + json.dumps(d["metadatos_ontologia"], ensure_ascii=False)
        for patron in PATRONES_PII.values():
            total += len(patron.findall(blob))
    return {"hallazgos_pii": total, "limpio": total == 0}


def estadisticas(docs: list[dict]) -> dict:
    por_prioridad: dict[str, int] = {}
    tokens = 0
    for d in docs:
        por_prioridad[d["prioridad"]] = por_prioridad.get(d["prioridad"], 0) + 1
        tokens += len(d["texto_indexable"].split())
    cdr_total = sum(d["cdr"] for d in docs)
    top5 = sum(sorted((d["cdr"] for d in docs), reverse=True)[:5])
    return {
        "n_documentos": len(docs),
        "tokens_totales_indexables": tokens,
        "tokens_promedio": round(tokens / max(len(docs), 1), 1),
        "documentos_por_prioridad": por_prioridad,
        "documentos_con_nombre_propio": sum(d["nombre_propio_buscable"] for d in docs),
        "cdr_total": cdr_total,
        "pct_demanda_top5": round(100 * top5 / max(cdr_total, 1), 1),
    }


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Construye el corpus indexable v1.")
    ap.add_argument("--config", default=str(RAIZ_EXP / "config.yaml"))
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    docs = construir_documentos(cfg)
    auditoria = auditar_pii(docs)
    if not auditoria["limpio"]:
        raise SystemExit(f"AUDITORÍA PII FALLÓ: {auditoria}. No se escribe el corpus.")

    ruta_corpus = RAIZ_EXP / cfg["rutas"]["corpus"]
    ruta_corpus.parent.mkdir(parents=True, exist_ok=True)
    with ruta_corpus.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    stats = estadisticas(docs) | {"auditoria_pii": auditoria}
    (RAIZ_EXP / cfg["rutas"]["corpus_stats"]).write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
