#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conteos agregados en producción SUID: usuarios de organismos deportivos y escenarios.

Solo lectura y solo agregados (COUNT / COUNT DISTINCT / GROUP BY sobre columnas de tipo,
estado o catálogo). No imprime códigos de usuario, nombres ni documentos.

El script NO supone nombres de columna: primero lee information_schema y arma cada conteo
con las columnas que realmente existen (id/code para distinguir, *_type*/status/deleted_at
para segmentar). Así no falla aunque el esquema difiera de lo esperado.

Uso:  python3 experimentos/athena/conteos_usuarios_escenarios.py [--perfil X]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extraer_competencias import ejecutar  # noqa: E402

TABLAS = {
    "bronze_suid_users": ["users", "user_types", "user_roles", "platform_roles",
                          "organizations_details", "user_relationships"],
    "bronze_suid_events": ["organization_lookup", "venues"],
    "bronze_venue_ms": ["venues", "venue_disciplinas"],
    "bronze_staging_venue_ms": ["venues"],
    "gold_suid": ["user_distribution"],
}
# Catálogos pequeños sin datos personales: se imprimen completos.
CATALOGOS = [("bronze_suid_users", "user_types"), ("bronze_suid_users", "platform_roles")]
SEGMENTO = re.compile(r"(^|_)(type|tipo|status|estado|role|rol|fictional|kind|category)(_|$)", re.I)
SENSIBLE = re.compile(r"name|nombre|email|phone|tel|document|password|token|address|direcc", re.I)


VIGENTE_ROL = ("ur.deleted_at IS NULL AND (ur.valid_until IS NULL OR ur.valid_until > current_timestamp)")
DIRIGIDAS = [
    ("Usuarios por naturaleza, tipo y estado de cuenta",
     "SELECT nature, user_type_code, account_status, is_active, deleted_at IS NULL AS no_borrado, "
     "COUNT(*) AS filas, COUNT(DISTINCT code) AS usuarios FROM bronze_suid_users.users "
     "GROUP BY 1,2,3,4,5 ORDER BY usuarios DESC"),
    ("Cuentas de organismo cruzadas con su usuario (activas = is_active y no borradas)",
     "SELECT o.organization_type, COUNT(DISTINCT o.user_code) AS organismos, "
     "COUNT(DISTINCT CASE WHEN u.is_active AND u.deleted_at IS NULL THEN o.user_code END) AS activos, "
     "COUNT(DISTINCT CASE WHEN u.has_login THEN o.user_code END) AS con_login, "
     "COUNT(DISTINCT CASE WHEN u.code IS NULL THEN o.user_code END) AS sin_usuario "
     "FROM bronze_suid_users.organizations_details o "
     "LEFT JOIN bronze_suid_users.users u ON u.code = o.user_code "
     "WHERE o.deleted_at IS NULL GROUP BY 1 ORDER BY organismos DESC"),
    ("Personas con rol vigente, por rol de plataforma",
     f"SELECT pr.code AS rol, COUNT(DISTINCT ur.user_code) AS usuarios, "
     f"COUNT(DISTINCT CASE WHEN o.user_code IS NOT NULL THEN ur.user_code END) AS de_ellos_son_cuenta_organismo "
     f"FROM bronze_suid_users.user_roles ur "
     f"JOIN bronze_suid_users.platform_roles pr ON pr.id = ur.platform_role_id "
     f"LEFT JOIN bronze_suid_users.organizations_details o ON o.user_code = ur.user_code "
     f"WHERE {VIGENTE_ROL} GROUP BY 1 ORDER BY usuarios DESC"),
    ("Escenarios en PRODUCCIÓN (bronze_venue_ms) por estado",
     "SELECT status, COUNT(*) AS filas, COUNT(DISTINCT id) AS escenarios "
     "FROM bronze_venue_ms.venues GROUP BY 1 ORDER BY escenarios DESC"),
    ("Escenarios en PRODUCCIÓN por tipo de infraestructura y de escenario (sin DELETED)",
     "SELECT infrastructure_type, venue_type, COUNT(DISTINCT id) AS escenarios "
     "FROM bronze_venue_ms.venues WHERE status <> 'DELETED' GROUP BY 1,2 ORDER BY escenarios DESC"),
    ("Escenarios en PRODUCCIÓN por departamento (sin DELETED)",
     "SELECT department_name, COUNT(DISTINCT id) AS escenarios, "
     "COUNT(DISTINCT municipality_code) AS municipios FROM bronze_venue_ms.venues "
     "WHERE status <> 'DELETED' GROUP BY 1 ORDER BY escenarios DESC"),
    ("Producción vs staging (control)",
     "SELECT 'produccion' AS capa, COUNT(DISTINCT id) AS escenarios, "
     "COUNT(DISTINCT CASE WHEN status = 'ACTIVE' THEN id END) AS activos FROM bronze_venue_ms.venues "
     "UNION ALL SELECT 'staging', COUNT(DISTINCT id), "
     "COUNT(DISTINCT CASE WHEN status = 'ACTIVE' THEN id END) FROM bronze_staging_venue_ms.venues"),
]


def esquema(perfil):
    filtro = " OR ".join(
        f"(table_schema='{s}' AND table_name IN ({', '.join(repr(t) for t in ts)}))"
        for s, ts in TABLAS.items())
    filas = ejecutar(f"SELECT table_schema, table_name, column_name, data_type FROM information_schema.columns "
                     f"WHERE {filtro} ORDER BY table_schema, table_name, ordinal_position", perfil)
    cols: dict[str, list[str]] = {}
    for f in filas:
        if "binary" in (f.get("data_type") or "").lower():
            continue          # columnas cifradas (varbinary): no se pueden agrupar ni leer
        cols.setdefault(f"{f['table_schema']}.{f['table_name']}", []).append(f["column_name"])
    return cols


def llave(cols):
    for c in ("id", "code", "user_code", "organization_id", "venue_code", "scenario_code"):
        if c in cols:
            return c
    return None


def correr(sql, perfil, titulo):
    try:
        tabla(ejecutar(sql, perfil), titulo)
    except Exception as e:  # una consulta fallida no detiene el resto
        print(f"\n### {titulo}\n(ERROR: {e})")


def tabla(filas, titulo):
    print(f"\n### {titulo}")
    if not filas:
        print("(sin filas)")
        return
    ks = list(filas[0])
    print(" | ".join(ks))
    for f in filas:
        print(" | ".join(str(f[k]) for k in ks))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perfil", default=None)
    ap.add_argument("--detalle-organismos", action="store_true",
                    help="detalle por organismo DEPARTMENTAL/NATIONAL/CLUB (sin datos del representante)")
    ap.add_argument("--verificar-llave", action="store_true",
                    help="verifica la llave groups.organization_code contra las cuentas de organización")
    ap.add_argument("--deleted-at", action="store_true",
                    help="tablas con columna deleted_at y cuántos registros están borrados")
    ap.add_argument("--organismos", action="store_true",
                    help="organismos deportivos (sin instituciones) por tipo y departamento")
    ap.add_argument("--pendientes", action="store_true",
                    help="corre solo las consultas dirigidas (los pendientes del README)")
    a = ap.parse_args()
    perfil = a.perfil
    if a.deleted_at:
        esquemas = ("bronze_suid_users", "bronze_suid_events", "bronze_venue_ms")
        tablas = ejecutar("SELECT table_schema, table_name, "
                          "max(CASE WHEN column_name = 'deleted_at' THEN 1 ELSE 0 END) AS tiene, "
                          "max(CASE WHEN column_name = 'status' THEN 1 ELSE 0 END) AS tiene_status "
                          "FROM information_schema.columns WHERE table_schema IN "
                          f"{esquemas} GROUP BY 1, 2 ORDER BY 1, 2", perfil)
        print("\n### Tablas y si tienen deleted_at / status")
        for t in tablas:
            print(f"{t['table_schema']}.{t['table_name']} | deleted_at={'sí' if t['tiene']=='1' else 'no'}"
                  f" | status={'sí' if t['tiene_status']=='1' else 'no'}")
        for t in tablas:
            if t["tiene"] == "1":
                nombre = f"{t['table_schema']}.{t['table_name']}"
                correr(f"SELECT COUNT(*) AS filas, COUNT(deleted_at) AS borradas, "
                       f"CAST(min(deleted_at) AS varchar) AS primer_borrado, "
                       f"CAST(max(deleted_at) AS varchar) AS ultimo_borrado FROM {nombre}",
                       perfil, f"deleted_at en {nombre}")
        return
    if a.verificar_llave:
        correr("SELECT o.organization_type, COUNT(DISTINCT o.user_code) AS organismos, "
               "COUNT(DISTINCT g.organization_code) AS con_grupos, COUNT(DISTINCT g.code) AS grupos "
               "FROM bronze_suid_users.organizations_details o "
               "LEFT JOIN bronze_suid_events.groups g ON g.organization_code = o.user_code "
               "GROUP BY 1 ORDER BY organismos DESC", perfil, "Cruce groups.organization_code = user_code")
        correr("SELECT COUNT(DISTINCT g.organization_code) AS codigos_en_groups, "
               "COUNT(DISTINCT CASE WHEN o.user_code IS NOT NULL THEN g.organization_code END) AS casan_user_code, "
               "COUNT(DISTINCT CASE WHEN l.organization_id IS NOT NULL THEN g.organization_code END) AS casan_lookup "
               "FROM bronze_suid_events.groups g "
               "LEFT JOIN bronze_suid_users.organizations_details o ON o.user_code = g.organization_code "
               "LEFT JOIN bronze_suid_events.organization_lookup l ON l.organization_id = g.organization_code",
               perfil, "Cobertura de la llave")
        return
    if a.detalle_organismos:
        sql = """
WITH org AS (
  SELECT o.user_code, o.legal_name, o.organization_type, o.department_name, o.municipality_name,
         o.federation_code, o.company_type_name, o.coverage_name, o.organization_size_name,
         o.snd_sector_entity_name, CAST(date(o.created_at) AS varchar) AS creado,
         u.user_type_code, u.account_status, u.has_login, u.is_active
  FROM bronze_suid_users.organizations_details o
  JOIN bronze_suid_users.users u ON u.code = o.user_code
  WHERE o.deleted_at IS NULL AND o.organization_type IN ('DEPARTMENTAL', 'NATIONAL', 'CLUB')
),
roles AS (
  SELECT ur.user_code, array_join(array_sort(array_agg(DISTINCT pr.code)), ',') AS roles
  FROM bronze_suid_users.user_roles ur
  JOIN bronze_suid_users.platform_roles pr ON pr.id = ur.platform_role_id
  WHERE ur.deleted_at IS NULL AND (ur.valid_until IS NULL OR ur.valid_until > current_timestamp)
  GROUP BY ur.user_code
),
grp AS (
  SELECT g.organization_code, COUNT(DISTINCT g.code) AS grupos, COUNT(DISTINCT g.event_code) AS eventos,
         COUNT(DISTINCT g.discipline_code) AS disciplinas
  FROM bronze_suid_events.groups g GROUP BY g.organization_code
),
mem AS (
  SELECT g.organization_code, COUNT(DISTINCT gm.participant_code) AS integrantes
  FROM bronze_suid_events.groups g
  JOIN bronze_suid_events.group_members gm ON gm.group_code = g.code
  GROUP BY g.organization_code
)
SELECT org.organization_type AS tipo, org.legal_name AS organismo,
       COALESCE(org.department_name, '-') AS departamento, COALESCE(org.municipality_name, '-') AS municipio,
       COALESCE(org.snd_sector_entity_name, '-') AS sector_snd, COALESCE(org.coverage_name, '-') AS cobertura,
       COALESCE(org.company_type_name, '-') AS tipo_empresa, COALESCE(org.organization_size_name, '-') AS tamano,
       COALESCE(org.federation_code, '-') AS cod_federacion,
       org.user_type_code AS tipo_usuario, org.account_status AS estado_cuenta, org.has_login AS login,
       COALESCE(roles.roles, '-') AS roles_vigentes,
       COALESCE(grp.eventos, 0) AS eventos, COALESCE(grp.grupos, 0) AS grupos,
       COALESCE(grp.disciplinas, 0) AS disciplinas, COALESCE(mem.integrantes, 0) AS integrantes,
       org.creado
FROM org
LEFT JOIN roles ON roles.user_code = org.user_code
LEFT JOIN grp ON grp.organization_code = org.user_code
LEFT JOIN mem ON mem.organization_code = org.user_code
ORDER BY CASE org.organization_type WHEN 'NATIONAL' THEN 1 WHEN 'DEPARTMENTAL' THEN 2 ELSE 3 END,
         org.department_name, org.legal_name
"""
        filas = ejecutar(sql, perfil)
        tabla(filas, "Detalle de organismos DEPARTMENTAL / NATIONAL / CLUB")
        import csv
        destino = Path(__file__).resolve().parents[2] / "data" / "usuarios_escenarios_suid" / "organismos_dep_nac_club.csv"
        destino.parent.mkdir(parents=True, exist_ok=True)
        if filas:
            with destino.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)
            print(f"\nGuardado: {destino}")
        return
    if a.organismos:
        base = ("FROM bronze_suid_users.organizations_details o "
                "JOIN bronze_suid_users.users u ON u.code = o.user_code "
                "WHERE o.deleted_at IS NULL AND o.organization_type <> 'INSTITUTION'")
        correr("SELECT o.organization_type, COUNT(DISTINCT o.user_code) AS organismos, "
               "COUNT(DISTINCT CASE WHEN u.has_login THEN o.user_code END) AS con_login, "
               "COUNT(DISTINCT o.department_code) AS departamentos, "
               "COUNT(DISTINCT o.federation_code) AS codigos_federacion " + base +
               " GROUP BY 1 ORDER BY organismos DESC", perfil, "Organismos por tipo")
        correr("SELECT COALESCE(o.department_name, '(sin departamento)') AS departamento, "
               "COUNT(DISTINCT CASE WHEN o.organization_type='MUNICIPAL' THEN o.user_code END) AS municipal, "
               "COUNT(DISTINCT CASE WHEN o.organization_type='DEPARTMENTAL' THEN o.user_code END) AS departamental, "
               "COUNT(DISTINCT CASE WHEN o.organization_type='NATIONAL' THEN o.user_code END) AS nacional, "
               "COUNT(DISTINCT CASE WHEN o.organization_type='CLUB' THEN o.user_code END) AS club, "
               "COUNT(DISTINCT o.user_code) AS total " + base +
               " GROUP BY 1 ORDER BY total DESC", perfil, "Organismos por departamento")
        correr("SELECT o.organization_type, COALESCE(o.snd_sector_entity_name, '(sin dato)') AS sector_snd, "
               "COALESCE(o.coverage_name, '(sin dato)') AS cobertura, COUNT(DISTINCT o.user_code) AS organismos " + base +
               " GROUP BY 1,2,3 ORDER BY 1, organismos DESC", perfil, "Organismos por sector SND y cobertura")
        return
    if a.pendientes:
        correr("SELECT tipo, COUNT(*) AS filas, COUNT(DISTINCT user_code) AS usuarios "
               "FROM gold_suid.user_distribution GROUP BY tipo ORDER BY usuarios DESC",
               perfil, "gold_suid.user_distribution por tipo")
        for titulo, sql in DIRIGIDAS:
            correr(sql, perfil, titulo)
        return

    cols = esquema(perfil)
    print("## Columnas encontradas")
    for t, cs in cols.items():
        print(f"- {t}: {', '.join(cs)}")
    faltan = [f"{s}.{t}" for s, ts in TABLAS.items() for t in ts if f"{s}.{t}" not in cols]
    if faltan:
        print("No existen / sin acceso:", ", ".join(faltan))

    for s, t in CATALOGOS:
        if f"{s}.{t}" in cols:
            seguras = [c for c in cols[f"{s}.{t}"] if not SENSIBLE.search(c) or c in ("name", "nombre")]
            correr(f"SELECT {', '.join(seguras)} FROM {s}.{t} LIMIT 200", perfil, f"Catálogo {s}.{t}")

    for t, cs in cols.items():
        if t.startswith("gold_suid.user_distribution"):
            correr(f"SELECT tipo, COUNT(*) AS filas, COUNT(DISTINCT user_code) AS usuarios FROM {t} "
                   f"GROUP BY tipo ORDER BY usuarios DESC", perfil, t + " por tipo")
            continue
        if t.startswith(("bronze_suid_users.platform_roles", "bronze_suid_users.user_types")):
            continue          # catálogos ya impresos arriba
        k = llave(cs)
        borrado = "deleted_at" in cs
        sel = ["COUNT(*) AS filas"]
        if k:
            sel.append(f"COUNT(DISTINCT {k}) AS distintos_{k}")
            if borrado:
                sel.append(f"COUNT(DISTINCT CASE WHEN deleted_at IS NULL THEN {k} END) AS distintos_no_borrados")
        correr(f"SELECT {', '.join(sel)} FROM {t}", perfil, f"Total {t}")
        for seg in [c for c in cs if SEGMENTO.search(c) and not SENSIBLE.search(c)]:
            cuenta = f"COUNT(DISTINCT {k})" if k else "COUNT(*)"
            correr(f"SELECT CAST({seg} AS varchar) AS {seg}, {cuenta} AS n FROM {t} "
                   f"GROUP BY 1 ORDER BY n DESC LIMIT 50", perfil, f"{t} por {seg}")

    # Usuarios vinculados a organismos: si existe una tabla de relaciones con dos columnas
    # de usuario, cuenta personas distintas por cada lado (sin listar ninguna).
    rel = cols.get("bronze_suid_users.user_relationships", [])
    lados = [c for c in rel if re.search(r"user_code|user_id", c)]
    if len(lados) >= 2:
        correr(f"SELECT {', '.join(f'COUNT(DISTINCT {c}) AS distintos_{c}' for c in lados)} "
               f"FROM bronze_suid_users.user_relationships", perfil,
               "Relaciones usuario↔organismo (distintos por lado)")

    # ---- Consultas dirigidas (columnas ya verificadas en information_schema) ----
    for titulo, sql in DIRIGIDAS:
        correr(sql, perfil, titulo)


if __name__ == "__main__":
    main()
