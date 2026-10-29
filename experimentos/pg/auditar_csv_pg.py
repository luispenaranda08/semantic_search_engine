#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría de datos personales para los CSV exportados desde la base operativa (pgAdmin).

Revisa, por archivo y por columna:
  * columnas prohibidas por nombre (usuarios, creadores, correos, enlaces, términos);
  * correos, teléfonos móviles colombianos y secuencias de 7+ dígitos (posibles documentos)
    en los valores, salvo columnas de código de catálogo (uuid/código), exentas de la regla
    numérica igual que `event_code` en la auditoría de Athena.

Nunca imprime el valor encontrado: solo archivo, columna, patrón y número de filas.
Sale con código 1 si hay hallazgos, para que el corpus no se construya con datos sucios.

Uso:
    python3 pg/auditar_csv_pg.py                      # audita data/competencias_suid/esquema_pg/
    python3 pg/auditar_csv_pg.py --dir otra/carpeta
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DIR_DEF = RAIZ.parent / "data" / "competencias_suid" / "esquema_pg"

ESPERADOS = {"roles_permisos", "fases_eventos", "pruebas_distintas", "reglas_por_deporte"}
COLUMNAS_PROHIBIDAS = re.compile(
    r"(user|_by|email|correo|_name_by|opened_by|closed_by|cancel|last_error|terms|link|"
    r"branding|banner|document|cedula|phone|telefono|organization_code)", re.I)
COLUMNAS_PERMITIDAS = {"requires_enrollment_documentation"}   # booleano de catálogo
EXENTAS_NUMERICAS = {"code", "sport_code"}
PII = {
    "correo": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "digitos_7+": re.compile(r"\b\d{7,}\b"),
    "movil_co": re.compile(r"\+?57\s?3\d{9}"),
}


def auditar(ruta: Path) -> list[tuple[str, str, int]]:
    hallazgos: Counter = Counter()
    with ruta.open(encoding="utf-8-sig", newline="") as fh:
        lector = csv.DictReader(fh)
        columnas = lector.fieldnames or []
        for col in columnas:
            if COLUMNAS_PROHIBIDAS.search(col) and col not in COLUMNAS_PERMITIDAS:
                hallazgos[(col, "columna_prohibida")] += 1
        for fila in lector:
            for col, val in fila.items():
                if not val:
                    continue
                for nombre, pat in PII.items():
                    if nombre == "digitos_7+" and col in EXENTAS_NUMERICAS:
                        continue
                    if pat.search(val):
                        hallazgos[(col, nombre)] += 1
    return [(c, p, n) for (c, p), n in sorted(hallazgos.items())]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=DIR_DEF)
    args = ap.parse_args()

    archivos = sorted(p for p in args.dir.glob("*.csv") if p.stem in ESPERADOS)
    faltan = ESPERADOS - {p.stem for p in archivos}
    if faltan:
        print(f"Aviso: faltan {sorted(faltan)} en {args.dir}")
    sucio = False
    for ruta in archivos:
        filas = sum(1 for _ in ruta.open(encoding="utf-8-sig")) - 1
        hallazgos = auditar(ruta)
        estado = "LIMPIO" if not hallazgos else "REVISAR"
        print(f"{ruta.name}: {filas} filas — {estado}")
        for col, patron, n in hallazgos:
            print(f"    columna={col!r} patrón={patron} filas={n}")
        sucio |= bool(hallazgos)
    sys.exit(1 if sucio else 0)


if __name__ == "__main__":
    main()
