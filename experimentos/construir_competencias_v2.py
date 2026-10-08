#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corpus definitivo de Competencias (v2): Prueba Regional × evento, solo pruebas que existen.

Reemplaza a `construir_competencias.py` (v1), que emitía el producto cartesiano
102 disciplinas × 8 regiones con un texto de plantilla idéntico salvo tres palabras y con
conteos GLOBALES del dominio repetidos en los 816 documentos. Aquí:

  * unidad documental = evento × deporte × categoría × región, y solo si existe al menos un
    grupo inscrito de una organización de esa región (evidencia de Athena, extracción v2);
  * cada documento lleva sus PROPIOS hechos: departamentos participantes, organizaciones,
    grupos, integrantes, fases con grupos inscritos y resultados registrados;
  * las consultas de evaluación del estrato `competencias` se generan con qrels POR FACETAS:
    es relevante (grado 2) toda prueba consistente con todas las facetas que la consulta
    menciona (deporte, categoría, región, evento, fase). Así una consulta como
    "resultados de Porrismo en Orinoquia" no tiene un único relevante arbitrario.

Insumo: `data/competencias_suid/extraccion_v2/` (salida de `athena/extraer_competencias.py`,
solo conteos agregados). Privacidad: ningún nombre de persona ni de grupo entra al corpus.

Uso:
    python3 construir_competencias_v2.py            # corpus + consultas + corpus combinado
    python3 construir_competencias_v2.py --n-consultas 60
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
EXTR = RAIZ.parent / "data" / "competencias_suid" / "extraccion_v2"

# Correcciones de calidad de datos observadas en el catálogo (p. ej. "Infaltil").
CATEGORIA_CANON = {"Infaltil": "Infantil", "": "Única", None: "Única"}
# Nombre corto y legible de cada evento para el texto (el nombre completo va en metadatos).
ALIAS_EVENTO = [
    (r"intercolegiad", "Juegos Intercolegiados"),
    (r"deportivos nacionales", "Juegos Deportivos Nacionales"),
    (r"suramericanos", "Juegos Suramericanos"),
    (r"centroamericanos", "Juegos Centroamericanos y del Caribe"),
]
NOMBRE_FASE = {"municipales": "Fase Municipal", "departamentales": "Fase Departamental",
               "regionales": "Fase Regional", "nacionales": "Fase Nacional", "fase 1": "Fase 1"}


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _mil(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _leer(nombre: str) -> list[dict]:
    ruta = EXTR / f"{nombre}.csv"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta}. Corre primero: python3 athena/extraer_competencias.py")
    return list(csv.DictReader(ruta.open(encoding="utf-8")))


def alias_evento(nombre: str) -> str:
    for patron, alias in ALIAS_EVENTO:
        if re.search(patron, nombre.lower()):
            return alias
    return nombre


def cargar() -> tuple[list[dict], dict]:
    fases_por_evento: dict[str, dict[str, str]] = defaultdict(dict)
    for f in _leer("01_eventos_fases"):
        if f.get("sequence_number"):
            nombre = f["phase_name"] or ""
            fases_por_evento[f["event_name"]][f["sequence_number"]] = \
                NOMBRE_FASE.get(nombre.strip().lower(), nombre.strip())

    resultados: dict[tuple, int] = defaultdict(int)
    ruta_res = EXTR / "04_resultados_por_prueba.csv"
    if ruta_res.exists():
        for f in csv.DictReader(ruta_res.open(encoding="utf-8")):
            cat = CATEGORIA_CANON.get(f["category_name"], f["category_name"])
            resultados[(f["event_name"], f["sport_name"], cat, f["region_name"])] += int(f["n_resultados"] or 0)

    pruebas: dict[tuple, dict] = {}
    for f in _leer("03_pruebas_regionales"):
        if f["region_name"] == "(sin región)" or not f["sport_name"] or int(f["n_grupos"] or 0) < 1:
            continue
        cat = CATEGORIA_CANON.get(f["category_name"], f["category_name"])
        clave = (f["event_name"], f["sport_name"], cat, f["region_name"])
        p = pruebas.setdefault(clave, {"evento": f["event_name"], "sport": f["sport_name"],
                                       "categoria": cat, "region": f["region_name"],
                                       "tipo": f["sport_type_name"] or "Individual",
                                       "n_grupos": 0, "n_orgs": 0, "n_integrantes": 0,
                                       "departamentos": set(), "fases": set()})
        # La corrección de categoría puede fundir dos filas: se suman.
        p["n_grupos"] += int(f["n_grupos"] or 0)
        p["n_orgs"] += int(f["n_organizaciones"] or 0)
        p["n_integrantes"] += int(f["n_integrantes"] or 0)
        p["departamentos"] |= {d.title() for d in (f["departamentos"] or "").split("|") if d}
        fmap = fases_por_evento.get(f["event_name"], {})
        p["fases"] |= {fmap.get(s, f"Fase {s}") for s in (f["fases_con_grupos"] or "").split(",") if s}
    for clave, p in pruebas.items():
        p["n_resultados"] = resultados.get(clave, 0)
    return sorted(pruebas.values(), key=lambda p: (p["evento"], p["sport"], p["categoria"], p["region"])), \
        fases_por_evento


def construir_doc(p: dict, idx: int) -> dict:
    ev = alias_evento(p["evento"])
    nombre = f"Prueba Regional: {p['sport']} {p['categoria']} — Región {p['region']} ({ev})"
    doc_id = f"cr2_{idx:04d}_{_slug(p['sport'])}_{_slug(p['categoria'])}_{_slug(p['region'])}_{_slug(ev)}"
    deps = sorted(p["departamentos"])
    fases = sorted(p["fases"])
    txt_deps = (", ".join(deps[:-1]) + " y " + deps[-1]) if len(deps) > 1 else (deps[0] if deps else "")
    partes = [
        f"La {nombre} agrupa la competencia de {p['sport']} en la categoría {p['categoria']} "
        f"({p['tipo'].lower()}) de los {ev} para las organizaciones de la región {p['region']}.",
        f"Participan {_mil(p['n_orgs'])} organizaciones"
        + (f" de {txt_deps}" if txt_deps else "")
        + f", con {_mil(p['n_grupos'])} grupos o delegaciones inscritos"
        + (f" y {_mil(p['n_integrantes'])} integrantes." if p["n_integrantes"] else "."),
    ]
    if fases:
        partes.append(f"Tiene grupos inscritos en: {', '.join(fases)}.")
    partes.append(
        f"Registra {_mil(p['n_resultados'])} resultados de competencia (posiciones y clasificados)."
        if p["n_resultados"] else
        "Aún no registra resultados de competencia; expone la inscripción y el avance por fase.")
    partes.append("Es una entidad compuesta: no existe como reporte dedicado y se arma cruzando "
                  "disciplina, categoría, evento, fase y región deportiva.")
    descripcion = " ".join(partes)

    entidades = ["Prueba Regional", "Disciplina Deportiva", "Categoría", "Evento", "Etapa/Fase",
                 "Región", "Ubicación Geográfica", "Institución", "Grupo", "Resultado", "Deportista"]
    sinonimos = ["prueba", "competencia", "certamen", "torneo", p["sport"], p["categoria"],
                 ev, "fase", "eliminatoria", "región", p["region"], *deps,
                 "clasificados", "resultados", "posiciones", "delegaciones"]
    conceptos = [f"{p['sport']} {p['categoria']} en Región {p['region']}",
                 f"resultados de {p['sport']} en {p['region']}",
                 f"{p['sport']} {p['categoria']} {ev}",
                 f"delegaciones de {p['region']} en {p['sport']}"]
    phi = (" Entidades: " + ", ".join(entidades) + ". Sinónimos: " + ", ".join(sinonimos) +
           ". Búsquedas: " + "; ".join(conceptos) + ".")
    return {
        "id": doc_id,
        "titulo": nombre,
        "descripcion": descripcion,
        "metadatos_ontologia": {
            "entidades_principales": entidades,
            "relaciones": ["Prueba Regional pertenece_a Evento", "Prueba Regional pertenece_a Disciplina Deportiva",
                           "Prueba Regional tiene Categoría", "Prueba Regional se_disputa_en Región",
                           "Prueba Regional ocurre_en Etapa/Fase", "Grupo compite_en Prueba Regional",
                           "Institución inscribe Grupo", "Prueba Regional produce Resultado"],
            "conceptos_busqueda": conceptos,
            "atributos_filtrables": ["event_name", "sport_name", "category_name", "region_name",
                                     "department_name", "phase_name"],
            "sinonimos": sinonimos,
        },
        "facetas": {"evento": ev, "evento_nombre": p["evento"], "deporte": p["sport"],
                    "categoria": p["categoria"], "region": p["region"], "fases": fases,
                    "departamentos": deps},
        "volumen": {"organizaciones": p["n_orgs"], "grupos": p["n_grupos"],
                    "integrantes": p["n_integrantes"], "resultados": p["n_resultados"]},
        "prioridad": "Núcleo (vacío de cobertura)",
        "cdr": 0,
        "nombre_propio_buscable": False,
        "dominio": "competencias",
        "fuentes": ["bronze_suid_events.events", "bronze_suid_events.phases",
                    "bronze_suid_events.disciplines", "bronze_suid_events.groups",
                    "bronze_suid_events.group_members", "bronze_suid_events.result_configs",
                    "bronze_suid_events.result_entries", "gold_suid.region_progress"],
        "texto_indexable": descripcion + phi,
    }


# --------------------------------------------------------------------------- consultas
PLANTILLAS = [  # (facetas mencionadas, plantilla)
    (("deporte", "categoria", "region"), "{deporte} {categoria} en Región {region}"),
    (("deporte", "region"), "resultados de {deporte} en {region}"),
    (("deporte", "categoria", "region", "evento"), "{deporte} {categoria} {region} {evento}"),
    (("deporte", "region", "fase"), "{deporte} {fase} región {region}"),
    (("deporte", "categoria", "evento"), "clasificados de {deporte} {categoria} en los {evento}"),
    (("region", "evento"), "delegaciones de {region} en los {evento}"),
]


def consistente(doc: dict, menc: dict) -> bool:
    f = doc["facetas"]
    for k, v in menc.items():
        if k == "fase":
            if v not in f["fases"]:
                return False
        elif f[k] != v:
            return False
    return True


def generar_consultas(docs: list[dict], n: int, semilla: int) -> tuple[list[dict], list[dict]]:
    rng = random.Random(semilla)
    consultas, qrels, vistos = [], [], set()
    # Consulta ancla del caso de uso, si la prueba existe.
    ancla = {"deporte": "Atletismo", "categoria": "Pre Juvenil", "region": "Caribe 1"}
    candidatos = [(ancla, "Atletismo Pre-Juvenil en Región Caribe 1")] \
        if any(consistente(d, ancla) for d in docs) else []
    intentos = 0
    while len(candidatos) < n and intentos < n * 50:
        intentos += 1
        facs, plantilla = PLANTILLAS[len(candidatos) % len(PLANTILLAS)]
        d = rng.choice(docs)
        menc = {k: (rng.choice(d["facetas"]["fases"]) if k == "fase" else d["facetas"][k])
                for k in facs if k != "fase" or d["facetas"]["fases"]}
        if len(menc) != len(facs):
            continue
        texto = plantilla.format(**menc)
        if texto in vistos:
            continue
        vistos.add(texto)
        candidatos.append((menc, texto))
    for i, (menc, texto) in enumerate(candidatos, 1):
        rel = {d["id"]: 2.0 for d in docs if consistente(d, menc)}
        qid = f"cv2_{i:03d}"
        consultas.append({"id": qid, "texto": texto, "estrato": "competencias",
                          "facetas_mencionadas": sorted(menc), "n_relevantes": len(rel),
                          "menciona_nombre_propio": False})
        qrels.append({"id": qid, "relevancia": rel})
    return consultas, qrels


def _escribir(ruta: Path, filas: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as f:
        for x in filas:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-consultas", type=int, default=60)
    ap.add_argument("--semilla", type=int, default=42)
    a = ap.parse_args()

    pruebas, _ = cargar()
    docs = [construir_doc(p, i) for i, p in enumerate(pruebas, 1)]
    _escribir(RAIZ / "corpus" / "corpus_competencias_v2.jsonl", docs)

    reportes = [json.loads(l) for l in (RAIZ / "corpus" / "corpus_v1.jsonl").open(encoding="utf-8")]
    for r in reportes:
        r.setdefault("dominio", "reportes")
    _escribir(RAIZ / "corpus" / "corpus_final.jsonl", docs + reportes)

    cons, qr = generar_consultas(docs, a.n_consultas, a.semilla)
    _escribir(RAIZ / "datos" / "consultas_comp_v2.jsonl", cons)
    _escribir(RAIZ / "datos" / "qrels_comp_v2.jsonl", qr)
    # Conjunto final = eval real ampliado (reportes, desde firmas) + competencias v2.
    base_c = [json.loads(l) for l in (RAIZ / "datos" / "consultas_real_ampliado.jsonl").open(encoding="utf-8")]
    base_q = [json.loads(l) for l in (RAIZ / "datos" / "qrels_real_ampliado.jsonl").open(encoding="utf-8")]
    _escribir(RAIZ / "datos" / "consultas_final.jsonl", base_c + cons)
    _escribir(RAIZ / "datos" / "qrels_final.jsonl", base_q + qr)

    textos = [d["descripcion"] for d in docs]
    resumen = {
        "n_pruebas": len(docs),
        "n_reportes": len(reportes),
        "n_corpus_final": len(docs) + len(reportes),
        "eventos": sorted({d["facetas"]["evento"] for d in docs}),
        "regiones": len({d["facetas"]["region"] for d in docs}),
        "deporte_x_categoria": len({(d["facetas"]["deporte"], d["facetas"]["categoria"]) for d in docs}),
        "descripciones_distintas": len(set(textos)),
        "pruebas_con_resultados": sum(1 for d in docs if d["volumen"]["resultados"]),
        "consultas_competencias": len(cons),
        "relevantes_por_consulta_mediana": sorted(c["n_relevantes"] for c in cons)[len(cons) // 2] if cons else 0,
        "consultas_final": len(base_c) + len(cons),
    }
    (RAIZ / "corpus" / "corpus_final_stats.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
