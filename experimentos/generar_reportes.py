#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera tablas, figura, recomendación y análisis de fallos desde resultados.json.

Uso:
    python3 generar_reportes.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from lib import reportes, error_analysis

RAIZ = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(RAIZ / "config.yaml"))
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    dir_res = RAIZ / cfg["rutas"]["dir_resultados"]
    reportes.generar_todo(RAIZ / cfg["rutas"]["resultados"], dir_res)
    error_analysis.generar(cfg, RAIZ, dir_res / "error_analysis.md")
    print(f"Reportes escritos en {dir_res}/:")
    for nombre in ["tabla_resultados.md", "tabla_resultados.tex", "recomendacion.md",
                   "fig_escalera_ablacion.png", "error_analysis.md"]:
        print(f"  - {nombre}")


if __name__ == "__main__":
    main()
