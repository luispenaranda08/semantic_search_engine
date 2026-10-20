#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corpus v3: varios tipos de objeto funcional de la plataforma, no solo reportes.

Parte del corpus definitivo (17 reportes + 160 Pruebas Regionales) y le agrega, desde la base
operativa de competencias (catálogo exportado por el autor y auditado con pg/auditar_csv_pg.py):

  * funcionalidades: roles y permisos con su descripción (qué rol puede hacer qué);
  * pruebas del catálogo: combinaciones deporte × disciplina × rama × categoría;
  * reglas de participación: cupos de grupos y de deportistas por deporte de conjunto.

Premisa del caso de estudio: en la plataforma no existe una consulta humana en texto libre. La
gente llega a la información navegando menús, filtros y reportes preexistentes, de modo que la
"verdad" de la evaluación no puede salir de un registro de búsquedas. Aquí sale de la propia
estructura del sistema: el permiso `medal:delete` ES la respuesta a "quién puede quitar una
medalla", y una prueba ES relevante para una consulta si coincide en todas las facetas que la
consulta menciona.

Control de circularidad (léxico dividido): cada familia de sinónimos se parte en dos mitades
deterministas. Los términos de posición par entran al enriquecimiento ontológico φ del
documento; los de posición impar se reservan para redactar las consultas. Así ninguna consulta
usa literalmente un sinónimo que la ontología haya inyectado: lo que la ontología aporte debe
venir de términos vecinos y de la generalización del codificador, no de una copia.

Privacidad: solo textos de catálogo y conteos; ningún nombre de persona ni de organización.
Las menciones a la organización operadora se anonimizan.

Uso:
    python3 construir_corpus_v3.py
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PG = RAIZ.parent / "data" / "competencias_suid" / "esquema_pg"

# El nombre de la organización operadora no se escribe en el código publicado: se lee de un
# archivo privado (pg/ no se publica). Sin ese archivo, el anonimizador no tiene nada que cambiar.
_ARCH_ORG = RAIZ / "pg" / "nombre_organizacion.txt"
_NOMBRE_ORG = _ARCH_ORG.read_text(encoding="utf-8").strip() if _ARCH_ORG.exists() else ""
ORG = re.compile(re.escape(_NOMBRE_ORG), re.I) if _NOMBRE_ORG else re.compile(r"(?!x)x")


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _anon(s: str) -> str:
    s = s or ""
    if not _NOMBRE_ORG:
        return s
    s = re.sub(r"\b" + re.escape(_NOMBRE_ORG.upper()) + "_", "OPERADORA_", s)
    s = re.sub("de " + re.escape(_NOMBRE_ORG), "de la organización operadora", s, flags=re.I)
    return ORG.sub("de la organización operadora", s)


def _leer(nombre: str) -> list[dict]:
    ruta = PG / f"{nombre}.csv"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta}. Exporta las consultas de pg/consultas_catalogo.sql")
    filas = list(csv.DictReader(ruta.open(encoding="utf-8-sig")))
    return [{k: (None if v in ("NULL", "") else v) for k, v in f.items()} for f in filas]


def _par(lista: list[str]) -> list[str]:      # mitad para la ontología φ
    return lista[0::2]


def _impar(lista: list[str]) -> list[str]:    # mitad reservada para redactar consultas
    return lista[1::2]


def _cargar(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def _escribir(ruta: Path, filas: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as f:
        for x in filas:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")


# ============================================================================ léxicos
# Cuatro términos por familia: posiciones 0 y 2 → ontología; 1 y 3 → consultas.
ACCION = {  # código de acción → (canónica, léxico)
    "read": "ver", "list": "ver", "write": "crear", "create": "crear", "upload": "crear",
    "update": "editar", "update_athlete": "editar", "delete": "eliminar", "manage": "gestionar",
    "approve": "aprobar", "download": "descargar", "assign": "asignar", "report": "resumen",
}
LEX_ACCION = {
    "ver": ["ver", "consultar", "listar", "revisar"],
    "crear": ["crear", "registrar", "cargar", "agregar"],
    "editar": ["editar", "modificar", "actualizar", "corregir"],
    "eliminar": ["eliminar", "quitar", "borrar", "dar de baja"],
    "gestionar": ["gestionar", "administrar", "manejar", "controlar"],
    "aprobar": ["aprobar", "validar", "autorizar", "aceptar"],
    "descargar": ["descargar", "bajar", "exportar", "obtener"],
    "asignar": ["asignar", "designar", "vincular", "nombrar"],
    "resumen": ["resumen", "informe", "consolidado", "conteo"],
}
OBJETO = {  # recurso del código → objeto canónico
    "activity": "programación", "athlete": "deportista", "colombia_quota": "cupo de Colombia",
    "dashboard": "tablero", "event_bulletin": "boletín técnico", "event": "evento",
    "event_lite": "evento de liga", "file": "archivo", "medal": "medalla",
    "methodologist": "metodólogo", "module_user": "usuario del módulo", "opinion": "opinión",
    "registration": "inscripción", "result": "resultado", "user": "usuario",
    "documents": "documento", "draw": "sorteo", "event_access": "acceso",
    "event_users": "usuario del evento", "mission_staff": "personal de misión",
    "phases": "fase", "support_personnel": "personal de apoyo",
}
LEX_OBJETO = {
    "programación": ["programación", "calendario", "agenda", "cronograma"],
    "deportista": ["deportista", "atleta", "atletas", "competidor"],
    "cupo de Colombia": ["cupo de Colombia", "plazas de Colombia", "cupo nacional", "cupos del país"],
    "tablero": ["dashboard", "tablero", "analítica", "indicadores"],
    "boletín técnico": ["boletín técnico", "boletines", "comunicado técnico", "circular técnica"],
    "evento": ["evento", "torneo", "certamen", "competencia"],
    "evento de liga": ["evento ultra-lite", "torneo de liga", "evento de liga", "competencia de liga"],
    "archivo": ["archivo", "plantilla", "formato", "documento descargable"],
    "medalla": ["medalla", "presea", "medallería", "podio"],
    "metodólogo": ["metodólogo", "evaluador técnico", "metodólogos", "asesor técnico"],
    "usuario del módulo": ["usuario del módulo", "invitado", "usuarios del módulo", "colaborador"],
    "opinión": ["opinión", "evaluación cualitativa", "concepto técnico", "valoración"],
    "inscripción": ["inscripción", "registro de participantes", "inscripciones", "matrícula"],
    "resultado": ["resultado", "marca", "resultados", "puntaje"],
    "usuario": ["usuario", "cuenta", "usuarios", "organización invitada"],
    "documento": ["documento", "soporte", "documentos", "papeles"],
    "sorteo": ["sorteo", "llaves", "resorteo", "fixture"],
    "acceso": ["acceso", "ingreso", "accesos", "permiso de entrada"],
    "usuario del evento": ["usuario del evento", "miembro del evento", "usuarios del evento",
                           "integrante del evento"],
    "personal de misión": ["personal de misión", "delegación oficial", "staff de misión",
                           "miembros de la misión"],
    "fase": ["fase", "etapa", "fases", "ronda"],
    "personal de apoyo": ["personal de apoyo", "entrenador", "cuerpo técnico", "delegado"],
}
LEX_SEXO = {
    "Hombre": ["masculino", "hombres", "varones", "rama masculina"],
    "Mujer": ["femenino", "mujeres", "damas", "rama femenina"],
    "Mixto": ["mixto", "mixta", "ambos sexos", "hombres y mujeres"],
}
CATEGORIA_CANON = {"JUV": "Juvenil"}
LEX_CATEGORIA = {
    "Juvenil": ["juvenil", "juveniles", "categoría juvenil", "de la categoría juvenil"],
    "Pre Juvenil": ["prejuvenil", "pre juvenil", "pre-juvenil", "prejuveniles"],
    "Infantil": ["infantil", "infantiles", "categoría infantil", "niños"],
    "Pre Infantil": ["preinfantil", "pre infantil", "pre-infantil", "preinfantiles"],
    "Iniciación": ["iniciación", "iniciados", "escuela deportiva", "principiantes"],
}
# El catálogo oficial nombra el mismo deporte de dos maneras (FUT_SAL / FUTSAL): se unifican en
# la faceta canónica, y una consulta por ese deporte considera relevantes ambas variantes.
DEPORTE_CANON = {"Fútbol sala": "Fútbol de Salón", "Mini Fútbol sala": "Mini Fútbol de Salón"}
LEX_DEPORTE = {
    "Fútbol de Salón": ["fútbol de salón", "futsal", "fútbol sala", "microfútbol"],
    "Mini Fútbol de Salón": ["mini fútbol de salón", "minifutsal", "mini fútbol sala", "mini microfútbol"],
    "Fútbol": ["fútbol", "fútbol once", "balompié", "fútbol de campo"],
    "Voleibol": ["voleibol", "vóley", "volleyball", "voleibol de sala"],
    "Mini Voleibol": ["mini voleibol", "minivóley", "minivoleibol", "vóley infantil"],
    "Baloncesto": ["baloncesto", "básquetbol", "basketball", "básquet"],
    "Mini Baloncesto": ["mini baloncesto", "minibásquet", "minibaloncesto", "básquet infantil"],
    "Baloncesto 3x3": ["baloncesto 3x3", "básquet 3x3", "baloncesto tres contra tres", "3x3"],
    "Balonmano": ["balonmano", "handball", "hándbol", "balón mano"],
    "Ajedrez Integrado": ["ajedrez integrado", "ajedrez", "ajedrez escolar", "partidas de ajedrez"],
    "Tenis de Mesa": ["tenis de mesa", "ping pong", "pimpón", "ping-pong"],
    "Levantamiento de pesas": ["levantamiento de pesas", "pesas", "halterofilia", "levantamiento olímpico"],
    "Para Atletismo": ["para atletismo", "atletismo paralímpico", "paraatletismo", "atletismo adaptado"],
    "Para Natación": ["para natación", "natación paralímpica", "paranatación", "natación adaptada"],
    "Karate Do": ["karate do", "karate", "kárate", "karate-do"],
    "Ciclismo Ruta": ["ciclismo ruta", "ciclismo de ruta", "ciclismo en carretera", "ruta"],
}
REGLAS_NOMBRE = {  # códigos sin nombre en el catálogo de disciplinas (cruce fallido)
    "FUT_SAL": "Fútbol de Salón", "FUTSAL": "Fútbol sala", "MINI_FUTSALA": "Mini Fútbol sala",
    "BAL": "Baloncesto", "MINI_VOL": "Mini Voleibol", "MINI_BAL": "Mini Baloncesto",
}
LEX_REGLA = {
    "cupo": ["cupo", "límite", "tope", "máximo permitido"],
    "grupo": ["grupo", "equipo", "plantel", "equipos"],
    "deportistas": ["deportistas", "jugadores", "integrantes", "atletas"],
}


def lex_deporte(dep: str) -> list[str]:
    return LEX_DEPORTE.get(dep, [dep.lower()] * 4)


# ============================================================================ funcionalidades
def construir_funcionalidades() -> list[dict]:
    docs = []
    for i, f in enumerate(_leer("roles_permisos"), 1):
        tipo, code = f["tipo"], _anon(f["code"])
        nombre, desc = _anon(f["nombre"] or code), _anon(f["descripcion"] or "")
        facetas = {"tipo_funcional": tipo}
        if tipo.startswith("permiso"):
            recurso, _, accion = code.partition(":")
            obj, acc = OBJETO.get(recurso), ACCION.get(accion)
            if accion == "update_athlete":          # edita la ficha del deportista, no la cuenta
                obj = "deportista"
            facetas.update({"recurso": recurso, "accion": accion, "objeto": obj, "accion_canon": acc})
            ambito = "dentro de un evento" if tipo == "permiso_evento" else "de la plataforma"
            titulo = f"Permiso: {nombre}" if tipo == "permiso" else f"Permiso de evento: {desc}"
            descripcion = (f"Permiso {ambito} con código {code}. {desc}. "
                           f"Los usuarios cuyo rol incluye este permiso pueden realizar esta acción.")
            sin = _par(LEX_OBJETO.get(obj, [])) + _par(LEX_ACCION.get(acc, []))
            conceptos = ([f"permiso para {a} {o}" for a in _par(LEX_ACCION.get(acc, []))[:1]
                          for o in _par(LEX_OBJETO.get(obj, []))] if obj and acc else [])
            entidades = ["Permiso", "Rol", "Usuario", "Evento"]
        else:
            ambito = "dentro de un evento" if tipo == "rol_evento" else "de la plataforma"
            titulo = f"Rol: {nombre}"
            descripcion = f"Rol de usuario {ambito}: {nombre} (código {code}). {desc}."
            sin, conceptos = ["rol", "perfil", "cargo"], [f"qué puede hacer el rol {nombre}"]
            entidades = ["Rol", "Permiso", "Usuario", "Evento"]
        phi = (" Entidades: " + ", ".join(entidades) + ". Sinónimos: " + ", ".join(sin) +
               ". Búsquedas: " + "; ".join(conceptos) + ".")
        docs.append({
            "id": f"fn3_{i:03d}_{_slug(tipo)}_{_slug(code)}",
            "titulo": titulo, "descripcion": descripcion,
            "metadatos_ontologia": {"entidades_principales": entidades, "relaciones": [
                "Rol otorga Permiso", "Usuario tiene Rol", "Permiso actúa_sobre Recurso"],
                "conceptos_busqueda": conceptos, "atributos_filtrables": ["tipo", "code"],
                "sinonimos": sin},
            "facetas": facetas, "prioridad": "Funcionalidad", "cdr": 0,
            "nombre_propio_buscable": False, "dominio": "funcionalidades",
            "fuentes": ["roles", "permissions", "event_roles", "event_permissions"],
            "texto_indexable": descripcion + phi,
        })
    return docs


# ============================================================================ pruebas
def canon_disciplina(d: str) -> str:
    s = d.strip()
    s = re.sub(r"\bMTRS?\b|\bMTS\b|\bM\b(?=\s)", "metros", s, flags=re.I)
    s = re.sub(r"\s+-\s*|\s*-\s+", " — ", s)
    return s.lower() if s.isupper() or any(w.isupper() and len(w) > 3 for w in s.split()) else s


def construir_pruebas() -> list[dict]:
    docs = []
    for i, f in enumerate(_leer("pruebas_distintas"), 1):
        dep_raw, disc_raw = f["sport_name"], f["discipline_name"]
        dep = DEPORTE_CANON.get(dep_raw, dep_raw)
        cat = CATEGORIA_CANON.get(f["category_name"], f["category_name"])
        sexo, tipo = f["sex_name"], f["sport_type_name"]
        disc = canon_disciplina(disc_raw)
        conjunto = tipo == "Conjunto"
        titulo = f"Prueba: {dep_raw} — {disc_raw} ({sexo}, {cat})"
        descripcion = (
            f"Prueba del catálogo de competencias: {dep_raw} ({tipo.lower()}), disciplina "
            f"{disc_raw}, rama {sexo}, categoría {cat}. Está configurada para registrar resultados "
            f"de {f['n_organizaciones']} organizaciones en {f['n_fases']} fase(s) del evento.")
        sin = (_par(lex_deporte(dep)) + _par(LEX_SEXO.get(sexo, [])) + _par(LEX_CATEGORIA.get(cat, []))
               + ([] if conjunto else [disc]) + ["prueba", "competencia", "resultados"])
        conceptos = [f"{dep} {cat} {sexo}", f"resultados de {disc} {sexo} {cat}"]
        phi = (" Entidades: Prueba, Disciplina Deportiva, Categoría, Resultado, Deportista. "
               "Sinónimos: " + ", ".join(sin) + ". Búsquedas: " + "; ".join(conceptos) + ".")
        docs.append({
            "id": f"pc3_{i:04d}_{_slug(dep_raw)}_{_slug(disc_raw)[:40]}_{_slug(sexo)}_{_slug(cat)}",
            "titulo": titulo, "descripcion": descripcion,
            "metadatos_ontologia": {"entidades_principales": ["Prueba", "Disciplina Deportiva",
                                                              "Categoría", "Resultado", "Deportista"],
                                    "relaciones": ["Prueba pertenece_a Disciplina Deportiva",
                                                   "Prueba tiene Categoría", "Prueba produce Resultado"],
                                    "conceptos_busqueda": conceptos,
                                    "atributos_filtrables": ["sport_name", "discipline_name",
                                                             "sex_name", "category_name"],
                                    "sinonimos": sin},
            "facetas": {"deporte": dep, "deporte_original": dep_raw, "disciplina": disc,
                        "sexo": sexo, "categoria": cat, "tipo": tipo},
            "volumen": {"organizaciones": int(f["n_organizaciones"]), "fases": int(f["n_fases"])},
            "prioridad": "Catálogo", "cdr": 0, "nombre_propio_buscable": False,
            "dominio": "pruebas_catalogo", "fuentes": ["result_configs"],
            "texto_indexable": descripcion + phi,
        })
    return docs


# ============================================================================ reglas
def construir_reglas() -> list[dict]:
    docs = []
    for i, f in enumerate(_leer("reglas_por_deporte"), 1):
        dep_raw = f["sport_name"] or REGLAS_NOMBRE.get(f["sport_code"], f["sport_code"])
        dep = DEPORTE_CANON.get(dep_raw, dep_raw)
        descripcion = (
            f"Reglas de participación de {dep_raw} (código {f['sport_code']}): cada organización "
            f"puede inscribir entre {f['min_grupos']} y {f['max_grupos']} grupos, y cada grupo debe "
            f"tener entre {f['med_min_por_grupo']} y {f['med_max_por_grupo']} deportistas "
            f"(valores medianos). Se aplica en {f['n_reglas']} configuraciones de participación.")
        sin = (_par(lex_deporte(dep)) + _par(LEX_REGLA["cupo"]) + _par(LEX_REGLA["grupo"])
               + _par(LEX_REGLA["deportistas"]) + ["regla", "requisito"])
        conceptos = [f"cupos de {dep}", f"tamaño de grupo en {dep}"]
        phi = (" Entidades: Regla de participación, Disciplina Deportiva, Grupo, Institución, "
               "Deportista. Sinónimos: " + ", ".join(sin) + ". Búsquedas: " + "; ".join(conceptos) + ".")
        docs.append({
            "id": f"rp3_{i:02d}_{_slug(f['sport_code'])}",
            "titulo": f"Reglas de participación: {dep_raw}", "descripcion": descripcion,
            "metadatos_ontologia": {"entidades_principales": ["Regla de participación",
                                                              "Disciplina Deportiva", "Grupo",
                                                              "Institución", "Deportista"],
                                    "relaciones": ["Regla limita Grupo", "Institución inscribe Grupo"],
                                    "conceptos_busqueda": conceptos,
                                    "atributos_filtrables": ["sport_code"], "sinonimos": sin},
            "facetas": {"deporte": dep, "deporte_original": dep_raw},
            "prioridad": "Regla", "cdr": 0, "nombre_propio_buscable": False,
            "dominio": "reglas_participacion", "fuentes": ["participation_rules"],
            "texto_indexable": descripcion + phi,
        })
    return docs


# ============================================================================ consultas
PLANT_FN = ["quién puede {a} {o}", "cómo {a} {o} en la plataforma", "permiso para {a} {o}",
            "{a} {o}"]
PLANT_PR = [(("deporte", "categoria", "sexo"), "{dep} {cat} {sex}"),
            (("disciplina", "sexo", "categoria"), "{disc} {sex} {cat}"),
            (("deporte", "sexo"), "pruebas de {dep} {sex}"),
            (("disciplina", "categoria"), "resultados de {disc} {cat}")]
PLANT_RG = ["cuántos {jug} por {gru} en {dep}", "{cupo} de {gru} en {dep}",
            "mínimo de {jug} por {gru} para inscribirse en {dep}"]


def consultas_funcionalidades(docs: list[dict], rng: random.Random) -> list[tuple[str, dict, str]]:
    salida, vistos = [], set()
    permisos = [d for d in docs if d["dominio"] == "funcionalidades" and d["facetas"].get("objeto")]
    for j, d in enumerate(permisos):
        o, a = d["facetas"]["objeto"], d["facetas"]["accion_canon"]
        if not (o and a):
            continue
        texto = PLANT_FN[j % len(PLANT_FN)].format(a=rng.choice(_impar(LEX_ACCION[a])),
                                                   o=rng.choice(_impar(LEX_OBJETO[o])))
        if texto in vistos:
            continue
        vistos.add(texto)
        rel = {x["id"]: 2.0 for x in permisos
               if x["facetas"]["objeto"] == o and x["facetas"]["accion_canon"] == a}
        salida.append((texto, rel, "funcionalidad"))
    return salida


def consultas_pruebas(docs: list[dict], rng: random.Random, n: int) -> list[tuple[str, dict, str]]:
    pr = [d for d in docs if d["dominio"] == "pruebas_catalogo"]
    salida, vistos, intentos = [], set(), 0
    while len(salida) < n and intentos < n * 60:
        intentos += 1
        facs, plant = PLANT_PR[len(salida) % len(PLANT_PR)]
        d = rng.choice(pr)
        f = d["facetas"]
        if "disciplina" in facs and f["tipo"] == "Conjunto":
            continue
        menc = {k: f[k] for k in facs}
        rel = {x["id"]: 2.0 for x in pr if all(x["facetas"][k] == v for k, v in menc.items())}
        if not 1 <= len(rel) <= 15:
            continue
        texto = plant.format(dep=rng.choice(_impar(lex_deporte(f["deporte"]))),
                             cat=rng.choice(_impar(LEX_CATEGORIA[f["categoria"]])),
                             sex=rng.choice(_impar(LEX_SEXO[f["sexo"]])),
                             disc=f["disciplina"])
        if texto in vistos:
            continue
        vistos.add(texto)
        salida.append((texto, rel, "prueba_catalogo"))
    return salida


def consultas_reglas(docs: list[dict], rng: random.Random) -> list[tuple[str, dict, str]]:
    rg = [d for d in docs if d["dominio"] == "reglas_participacion"]
    salida, vistos = [], set()
    for dep in sorted({d["facetas"]["deporte"] for d in rg}):
        rel = {d["id"]: 2.0 for d in rg if d["facetas"]["deporte"] == dep}
        for plant in PLANT_RG:
            texto = plant.format(dep=rng.choice(_impar(lex_deporte(dep))),
                                 jug=rng.choice(_impar(LEX_REGLA["deportistas"])),
                                 gru=rng.choice(_impar(LEX_REGLA["grupo"])),
                                 cupo=rng.choice(_impar(LEX_REGLA["cupo"])))
            if texto not in vistos:
                vistos.add(texto)
                salida.append((texto, rel, "regla_participacion"))
    return salida


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-pruebas", type=int, default=60)
    ap.add_argument("--semilla", type=int, default=20261020)
    a = ap.parse_args()
    rng = random.Random(a.semilla)

    base = _cargar(RAIZ / "corpus" / "corpus_final.jsonl")
    nuevos = construir_funcionalidades() + construir_pruebas() + construir_reglas()
    ids = [d["id"] for d in base + nuevos]
    assert len(ids) == len(set(ids)), "ids duplicados en el corpus v3"
    assert not any(ORG.search(json.dumps(d, ensure_ascii=False)) for d in nuevos), "nombre de la organización sin anonimizar"
    _escribir(RAIZ / "corpus" / "corpus_v3.jsonl", base + nuevos)

    crudas = (consultas_funcionalidades(nuevos, rng) + consultas_pruebas(nuevos, rng, a.n_pruebas)
              + consultas_reglas(nuevos, rng))
    cons, qrels = [], []
    for i, (texto, rel, estrato) in enumerate(crudas, 1):
        qid = f"v3_{i:03d}"
        cons.append({"id": qid, "texto": texto, "estrato": estrato, "n_relevantes": len(rel),
                     "menciona_nombre_propio": False, "origen": "estructura_del_sistema"})
        qrels.append({"id": qid, "relevancia": rel})
    _escribir(RAIZ / "datos" / "consultas_v3.jsonl", cons)
    _escribir(RAIZ / "datos" / "qrels_v3.jsonl", qrels)
    base_c = _cargar(RAIZ / "datos" / "consultas_final.jsonl")
    base_q = _cargar(RAIZ / "datos" / "qrels_final.jsonl")
    _escribir(RAIZ / "datos" / "consultas_final_v3.jsonl", base_c + cons)
    _escribir(RAIZ / "datos" / "qrels_final_v3.jsonl", base_q + qrels)

    stats = {
        "docs_total": len(base) + len(nuevos),
        "docs_por_dominio": dict(Counter(d.get("dominio", "reportes") for d in base + nuevos)),
        "consultas_nuevas_por_estrato": dict(Counter(c["estrato"] for c in cons)),
        "relevantes_medios_por_estrato": {
            e: round(sum(c["n_relevantes"] for c in cons if c["estrato"] == e) /
                     max(1, sum(1 for c in cons if c["estrato"] == e)), 2)
            for e in sorted({c["estrato"] for c in cons})},
        "consultas_final_v3": len(base_c) + len(cons),
        "semilla": a.semilla,
    }
    (RAIZ / "corpus" / "corpus_v3_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
