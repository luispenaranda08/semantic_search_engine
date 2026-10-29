#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extracción agregada del dominio de Competencias para depurar el corpus (Prueba Regional × evento).

Objetivo: quedarse SOLO con las pruebas (evento × deporte × categoría × región) que existen
realmente en producción, y dar a cada una conteos propios (grupos, integrantes, departamentos,
fases), en lugar del producto cartesiano 102 disciplinas × 8 regiones del corpus anterior.

Privacidad: todas las consultas son de solo lectura y AGREGADAS (COUNT / COUNT DISTINCT /
DISTINCT sobre catálogos). Ninguna devuelve códigos de usuario, nombres de persona, nombres de
grupo ni literales individuales. Al terminar se corre una auditoría de patrones de PII sobre los
CSV escritos; si encuentra algo, borra la salida y aborta.

Uso (con TU usuario de AWS):
    python3 experimentos/athena/extraer_competencias.py              # perfil por defecto
    python3 experimentos/athena/extraer_competencias.py --perfil X   # otro perfil
Salida: data/competencias_suid/extraccion_v2/*.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "data" / "competencias_suid" / "extraccion_v2"
WORKGROUP = "datalake-production"

# Organizaciones: catálogo real + organizaciones ficticias del evento, deduplicadas por código.
_ORG = """
org AS (
  SELECT org_code, max(department_code) AS department_code FROM (
    SELECT organization_id AS org_code, department_code FROM bronze_suid_events.organization_lookup
    UNION ALL
    SELECT code AS org_code, department_code FROM bronze_suid_events.event_fictional_organizations
  ) GROUP BY org_code
),
reg AS (
  SELECT department_code, max(region_name) AS region_name, max(department_name) AS department_name
  FROM gold_suid.region_progress WHERE region_name IS NOT NULL GROUP BY department_code
)"""

CONSULTAS: dict[str, str] = {
    # 0. Diagnóstico de llaves de unión (tasas de coincidencia), para validar los JOIN.
    "00_diagnostico_llaves": f"""
WITH {_ORG.strip()}
SELECT
  (SELECT COUNT(*) FROM bronze_suid_events.groups) AS grupos_total,
  (SELECT COUNT(*) FROM bronze_suid_events.groups g
     JOIN bronze_suid_events.disciplines d ON d.code = g.discipline_code) AS grupos_match_disc_code,
  (SELECT COUNT(*) FROM bronze_suid_events.groups g
     JOIN (SELECT DISTINCT discipline_code FROM bronze_suid_events.disciplines) d
       ON d.discipline_code = g.discipline_code) AS grupos_match_disc_discipline_code,
  (SELECT COUNT(*) FROM bronze_suid_events.groups g JOIN org o ON o.org_code = g.organization_code) AS grupos_match_org,
  (SELECT COUNT(*) FROM bronze_suid_events.groups g JOIN org o ON o.org_code = g.organization_code
     JOIN reg r ON r.department_code = o.department_code) AS grupos_match_region,
  (SELECT COUNT(*) FROM bronze_suid_events.participant_disciplines) AS pd_total,
  (SELECT COUNT(*) FROM bronze_suid_events.participant_disciplines pd
     JOIN bronze_suid_events.disciplines d ON d.code = pd.discipline_code) AS pd_match_disc_code
""",
    # 1. Eventos y fases (catálogo, sin personas).
    "01_eventos_fases": """
SELECT e.code AS event_code, e.name AS event_name, e.event_type, e.scope, e.status,
       p.sequence_number, p.name AS phase_name, p.status AS phase_status
FROM bronze_suid_events.events e
LEFT JOIN bronze_suid_events.phases p ON p.event_code = e.code
ORDER BY e.name, p.sequence_number
""",
    # 2. Disciplinas por evento, con inscripciones individuales agregadas (no hay región aquí).
    "02_disciplinas_por_evento": """
SELECT e.name AS event_name, d.sport_name, COALESCE(d.category_name, 'Única') AS category_name,
       d.sport_type_name, COUNT(DISTINCT d.code) AS n_disciplinas,
       COUNT(DISTINCT pd.participant_code) AS n_participantes_inscritos
FROM bronze_suid_events.disciplines d
JOIN bronze_suid_events.events e ON e.code = d.event_code
LEFT JOIN bronze_suid_events.participant_disciplines pd ON pd.discipline_code = d.code
GROUP BY 1, 2, 3, 4
""",
    # 3. NÚCLEO: pruebas que existen = evento × deporte × categoría × región con ≥1 grupo.
    "03_pruebas_regionales": f"""
WITH {_ORG.strip()},
d AS (
  SELECT code AS discipline_code, event_code, sport_name,
         COALESCE(category_name, 'Única') AS category_name, sport_type_name
  FROM bronze_suid_events.disciplines
),
gm AS (
  SELECT group_code, COUNT(DISTINCT participant_code) AS n
  FROM bronze_suid_events.group_members GROUP BY group_code
)
SELECT e.name AS event_name, d.sport_name, d.category_name, d.sport_type_name,
       COALESCE(r.region_name, '(sin región)') AS region_name,
       COUNT(DISTINCT g.code) AS n_grupos,
       COUNT(DISTINCT g.organization_code) AS n_organizaciones,
       COUNT(DISTINCT o.department_code) AS n_departamentos,
       SUM(COALESCE(gm.n, 0)) AS n_integrantes,
       array_join(array_sort(array_agg(DISTINCT CAST(g.phase_sequence AS varchar))), ',') AS fases_con_grupos,
       array_join(array_sort(array_agg(DISTINCT r.department_name)), '|') AS departamentos
FROM bronze_suid_events.groups g
JOIN d ON d.discipline_code = g.discipline_code
JOIN bronze_suid_events.events e ON e.code = g.event_code
LEFT JOIN org o ON o.org_code = g.organization_code
LEFT JOIN reg r ON r.department_code = o.department_code
LEFT JOIN gm ON gm.group_code = g.code
GROUP BY 1, 2, 3, 4, 5
""",
    # 4. Resultados registrados por evento × fase × deporte (result_configs trae sport/category
    #    cifrados, por eso se cruza por discipline_code contra el catálogo en claro).
    "04_resultados_por_prueba": f"""
WITH {_ORG.strip()}
SELECT e.name AS event_name, p.name AS phase_name, d.sport_name,
       COALESCE(d.category_name, 'Única') AS category_name,
       COALESCE(r.region_name, '(sin región)') AS region_name,
       COUNT(DISTINCT rc.code) AS n_configuraciones, COUNT(re.code) AS n_resultados
FROM bronze_suid_events.result_configs rc
JOIN bronze_suid_events.events e ON e.code = rc.event_code
LEFT JOIN bronze_suid_events.phases p ON p.code = rc.phase_code
LEFT JOIN bronze_suid_events.disciplines d ON d.code = rc.discipline_code
LEFT JOIN org o ON o.org_code = rc.organization_code
LEFT JOIN reg r ON r.department_code = o.department_code
LEFT JOIN bronze_suid_events.result_entries re ON re.config_code = rc.code AND re.deleted_at IS NULL
WHERE rc.deleted_at IS NULL
GROUP BY 1, 2, 3, 4, 5
""",
}

EXENTAS_NUMERICAS = {"event_code"}   # código del catálogo de eventos (institucional, no personal)
PII = [re.compile(p) for p in (r"[\w.+-]+@[\w-]+\.[\w.]+", r"\b\d{7,}\b", r"\+?57\s?3\d{9}")]


def aws(args: list[str], perfil: str | None) -> dict:
    cmd = ["aws", *args] + (["--profile", perfil] if perfil else [])
    return json.loads(subprocess.check_output(cmd))


def ejecutar(sql: str, perfil: str | None) -> list[dict]:
    qid = aws(["athena", "start-query-execution", "--work-group", WORKGROUP,
               "--query-string", sql], perfil)["QueryExecutionId"]
    while True:
        st = aws(["athena", "get-query-execution", "--query-execution-id", qid],
                 perfil)["QueryExecution"]["Status"]
        if st["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1.5)
    if st["State"] != "SUCCEEDED":
        raise RuntimeError(f"{st['State']}: {st.get('StateChangeReason')}")
    filas, token = [], None
    while True:
        args = ["athena", "get-query-results", "--query-execution-id", qid, "--max-items", "1000"]
        if token:
            args += ["--starting-token", token]
        out = aws(args, perfil)
        filas += [[c.get("VarCharValue") for c in f["Data"]] for f in out["ResultSet"]["Rows"]]
        token = out.get("NextToken")
        if not token:
            break
    cab = filas[0]
    return [dict(zip(cab, f)) for f in filas[1:] if f != cab]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perfil", default=None)
    ap.add_argument("--solo", nargs="*", help="nombres de consulta a correr (por defecto todas)")
    a = ap.parse_args()
    SALIDA.mkdir(parents=True, exist_ok=True)
    escritos = []
    for nombre, sql in CONSULTAS.items():
        if a.solo and nombre not in a.solo:
            continue
        print(f"→ {nombre} ...", flush=True)
        filas = ejecutar(sql, a.perfil)
        ruta = SALIDA / f"{nombre}.csv"
        with ruta.open("w", encoding="utf-8", newline="") as f:
            if filas:
                w = csv.DictWriter(f, fieldnames=list(filas[0]))
                w.writeheader()
                w.writerows(filas)
        escritos.append(ruta)
        print(f"  {len(filas)} filas → {ruta.relative_to(RAIZ)}")
    # Auditoría de PII sobre lo escrito, columna por columna (se reporta el nombre de la columna,
    # nunca el valor). Las columnas de CATÁLOGO listadas en EXENTAS_NUMERICAS son códigos de
    # entidades institucionales (eventos, disciplinas, departamentos), no de personas; para ellas
    # se omite solo la regla de "7 o más dígitos". Correo y teléfono se revisan en todas.
    hallazgos = []
    for r in escritos:
        with r.open(encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                for col, val in fila.items():
                    for pat in PII:
                        if pat.pattern == r"\b\d{7,}\b" and col in EXENTAS_NUMERICAS:
                            continue
                        if val and pat.search(val):
                            hallazgos.append((r.name, col, pat.pattern))
    hallazgos = sorted(set(hallazgos))
    if hallazgos:
        for r in escritos:
            r.unlink()
        sys.exit(f"ABORTADO: patrones de PII en la salida {hallazgos}; se borraron los CSV.")
    print("Auditoría PII: limpio (0 hallazgos).")


if __name__ == "__main__":
    main()
