#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conjunto difícil B (réplica): 78 consultas NUEVAS sobre los mismos 13 reportes que el conjunto difícil A.

Por qué existe. El conjunto difícil A (52 consultas) se redactó antes de ver resultados, pero sus
hallazgos (ontología +0,122 sobre el denso; el híbrido por RRF no supera al denso) se formularon
mirándolo. Este conjunto B pone a prueba esos hallazgos con consultas distintas. HONESTIDAD:
fue redactado DESPUÉS de conocer los resultados de A (aunque no se ajustó a ningún sistema ni se
descartó ninguna consulta por su resultado), de modo que es una réplica, no una prueba ciega.
Se redactaron 6 consultas por reporte en cuatro registros: pregunta, telegráfico, coloquial y
administrativo. Se evita deliberadamente copiar el título del reporte.

Igual que en A, el nivel de dificultad (A_puente_ontologia / B_sin_puente / C_con_solape) se
CALCULA por solape de raíces, no se asigna a mano. Las consultas deben ser revisadas por el autor.

Salida: datos/consultas_dificil_b.jsonl y datos/qrels_dificil_b.jsonl (ids e001…).
Uso:  python3 construir_eval_dificil_b.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.etiquetado import SLUG_POR_CLAVE, id_por_slug
from lib.indexes import tokenizar_es
from construir_eval_dificil import CONSULTAS as CONSULTAS_A, PLANTILLA

RAIZ = Path(__file__).resolve().parent

# (texto, registro)  registro in {pregunta, telegrafico, coloquial, administrativo}
CONSULTAS_B = {
    "individual": [
        ("¿quiénes están inscritos en natación categoría juvenil?", "pregunta"),
        ("datos de contacto y documento de un jugador", "telegrafico"),
        ("jugadores de comunidades indígenas por departamento", "telegrafico"),
        ("necesito ubicar a una muchacha que compite en atletismo", "coloquial"),
        ("nómina de atletas con su modalidad y ciudad de residencia", "administrativo"),
        ("lista de participantes por deporte y categoría", "telegrafico"),
    ],
    "grupos": [
        ("¿qué equipos tiene registrados este colegio?", "pregunta"),
        ("conformación de la delegación por disciplina y fase", "administrativo"),
        ("cuáles son los conjuntos que compiten en la ronda actual", "coloquial"),
        ("integrantes de cada equipo de una escuela", "telegrafico"),
        ("listado de agrupaciones deportivas por institución", "administrativo"),
        ("quiénes pertenecen a un equipo determinado", "pregunta"),
    ],
    "personal": [
        ("¿quién acompaña a los equipos durante el torneo?", "pregunta"),
        ("técnicos y acompañantes inscritos por evento", "telegrafico"),
        ("entrenadores de una delegación", "telegrafico"),
        ("relación de profesores que viajan con cada grupo", "administrativo"),
        ("la gente que apoya a los deportistas en la competencia", "coloquial"),
        ("staff de apoyo por equipo y por torneo", "telegrafico"),
    ],
    "documentacion": [
        ("¿a quién le falta algún soporte por subir?", "pregunta"),
        ("papeles aprobados y rechazados de cada deportista", "coloquial"),
        ("estado de los certificados de los participantes", "administrativo"),
        ("qué requisitos documentales cumplió un atleta", "pregunta"),
        ("deportistas con documentos pendientes de revisión", "telegrafico"),
        ("seguimiento de la entrega de soportes por jugador", "administrativo"),
    ],
    "participacion": [
        ("¿qué colegios confirmaron que participan en el evento?", "pregunta"),
        ("instituciones inscritas para competir este año", "administrativo"),
        ("quién manifestó interés en participar", "coloquial"),
        ("participantes registrados por entidad", "telegrafico"),
        ("relación de planteles que van a asistir", "administrativo"),
        ("intención de asistencia de una escuela", "telegrafico"),
    ],
    "dashboard": [
        ("¿cómo va el evento en general?", "pregunta"),
        ("tablero con los indicadores principales de la competencia", "telegrafico"),
        ("resumen ejecutivo del estado del torneo", "administrativo"),
        ("cifras globales por región y disciplina", "telegrafico"),
        ("visión de conjunto de lo que ha pasado en el certamen", "coloquial"),
        ("panel con los totales del evento", "telegrafico"),
    ],
    "promocion": [
        ("¿en qué ronda va este atleta?", "pregunta"),
        ("quiénes avanzaron a la siguiente fase", "pregunta"),
        ("estado de clasificación de un deportista", "administrativo"),
        ("jugadores que pasaron de etapa y quiénes no", "coloquial"),
        ("avance de categoría de un competidor", "telegrafico"),
        ("seguimiento del paso de cada atleta a la ronda siguiente", "administrativo"),
    ],
    "instituciones": [
        ("¿qué colegios hay en el Atlántico?", "pregunta"),
        ("buscar una escuela por su nombre", "telegrafico"),
        ("entidades participantes por municipio", "telegrafico"),
        ("clubes deportivos registrados por región", "administrativo"),
        ("listado de centros educativos inscritos", "administrativo"),
        ("ficha de una escuela con su ciudad y departamento", "coloquial"),
    ],
    "metas": [
        ("¿cuánto hemos cubierto frente a lo esperado?", "pregunta"),
        ("porcentaje de avance de la cobertura por región", "telegrafico"),
        ("metas alcanzadas y pendientes por zona del país", "administrativo"),
        ("comparativo entre lo planeado y lo logrado por departamento", "administrativo"),
        ("regiones que ya cumplieron su objetivo", "coloquial"),
        ("nivel de cumplimiento de la cobertura", "telegrafico"),
    ],
    "distribucion": [
        ("¿cuántas cuentas hay por tipo de usuario?", "pregunta"),
        ("reparto de los usuarios según su perfil", "telegrafico"),
        ("cantidad de personas registradas por rol", "telegrafico"),
        ("cómo se distribuyen los usuarios de la plataforma", "pregunta"),
        ("usuarios activos agrupados por perfil de acceso", "administrativo"),
        ("número de administradores, entrenadores y deportistas con cuenta", "coloquial"),
    ],
    "federacion": [
        ("¿cómo le va a cada federación?", "pregunta"),
        ("indicadores por organismo rector de cada deporte", "administrativo"),
        ("balance de resultados por ente federativo", "administrativo"),
        ("comparar federaciones deportivas entre sí", "telegrafico"),
        ("métricas agrupadas por federación", "telegrafico"),
        ("desempeño de las ligas y federaciones", "coloquial"),
    ],
    "cambios": [
        ("¿quién se retractó de participar?", "pregunta"),
        ("modificaciones recientes a la inscripción de un colegio", "administrativo"),
        ("instituciones que cambiaron su decisión", "telegrafico"),
        ("historial de cambios en la asistencia confirmada", "administrativo"),
        ("quiénes pasaron de confirmar a retirarse", "coloquial"),
        ("variaciones en lo que habían manifestado antes", "telegrafico"),
    ],
    "delegaciones": [
        ("¿cuántas delegaciones envía cada club?", "pregunta"),
        ("comitivas inscritas por entidad", "telegrafico"),
        ("delegaciones oficiales que viajan al evento", "administrativo"),
        ("relación de delegaciones por institución", "administrativo"),
        ("grupos de representantes de cada escuela en la competencia", "coloquial"),
        ("listado de delegaciones registradas y su composición", "telegrafico"),
    ],
}


def stems(texto: str) -> set[str]:
    return {t for t in tokenizar_es(texto) if t not in PLANTILLA}


def main() -> None:
    docs = [json.loads(l) for l in (RAIZ / "corpus/corpus_v1.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = [d["id"] for d in docs]
    por_id = {d["id"]: d for d in docs}
    textos_a = {t for lst in CONSULTAS_A.values() for t in lst}
    consultas, qrels, cont = [], {}, 0
    for clave, items in CONSULTAS_B.items():
        obj = id_por_slug(SLUG_POR_CLAVE[clave], ids)
        d = por_id[obj]
        s_desc = stems(d["descripcion"]) | stems(d["titulo"])
        s_onto = stems(d["texto_indexable"]) - s_desc
        for t, reg in items:
            assert t not in textos_a, f"duplicada con A: {t}"
            sq = stems(t)
            nivel = "C_con_solape" if sq & s_desc else ("A_puente_ontologia" if sq & s_onto else "B_sin_puente")
            cont += 1
            qid = f"e{cont:03d}"
            consultas.append({"id": qid, "texto": t, "estrato": nivel, "registro": reg, "reporte_objetivo": obj,
                              "menciona_nombre_propio": False, "capa": "sintetico_dificil_replica",
                              "solape_desc": sorted(sq & s_desc), "solape_onto": sorted(sq & s_onto),
                              "doc_con_ontologia": len(d["texto_indexable"]) > len(d["descripcion"])})
            qrels[qid] = {obj: 2.0}
    datos = RAIZ / "datos"
    with (datos / "consultas_dificil_b.jsonl").open("w", encoding="utf-8") as f:
        for c in consultas:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with (datos / "qrels_dificil_b.jsonl").open("w", encoding="utf-8") as f:
        for qid, rel in qrels.items():
            f.write(json.dumps({"id": qid, "relevancia": rel}, ensure_ascii=False) + "\n")
    # Unión A+B (para estadística con más poder): mismas consultas, capa indicando el origen.
    a = [json.loads(l) for l in (datos / "consultas_dificil.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    qa = [json.loads(l) for l in (datos / "qrels_dificil.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    with (datos / "consultas_dificil_ab.jsonl").open("w", encoding="utf-8") as f:
        for c in a + consultas:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with (datos / "qrels_dificil_ab.jsonl").open("w", encoding="utf-8") as f:
        for r in qa + [{"id": q, "relevancia": rel} for q, rel in qrels.items()]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"n": len(consultas),
                      "por_nivel": dict(collections.Counter(c["estrato"] for c in consultas)),
                      "por_registro": dict(collections.Counter(c["registro"] for c in consultas)),
                      "objetivo_sin_ontologia": sum(1 for c in consultas if not c["doc_con_ontologia"])},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
