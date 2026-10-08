#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera las tablas y la figura de resultados a partir de resultados.json.

Produce:
  * tabla_resultados.md y tabla_resultados.tex (global + por estrato, booktabs)
  * fig_escalera_ablacion.png (nDCG@10 por configuración, global vs entidad exacta)
  * recomendacion.md (configuración sugerida para despliegue local, P6)
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AZUL = "#00529B"
NARANJA = "#F18520"
GRIS = "#B9C2CE"
ORDEN_CONFIG = ["BM25 (referencia léxica)", "Denso puro", "Denso + ontología",
                "Híbrido (sin ontología)", "Híbrido + ontología",
                "Híbrido + ontología + realce"]
METRICAS = ["ndcg@10", "recall@100", "mrr@10", "p@10"]


def _fmt(x: float) -> str:
    return f"{x:.3f}"


def tabla_markdown(res: dict) -> str:
    lin = [f"# Resultados de la escalera de ablación",
           "",
           f"Encoder: `{res['encoder']}`. Consultas con juicios en la v1: "
           f"{res['n_consultas_con_gold']}. Consultas de competencias sin cobertura en "
           f"la v1 (vacío de cobertura): {res['n_consultas_sin_cobertura_v1']}.",
           "",
           "## Global (consultas con documento relevante en la v1)",
           "",
           "| Configuración | nDCG@10 | Recall@100 | MRR@10 | P@10 | Lat. p50 (ms) |",
           "|---|---|---|---|---|---|"]
    for nombre in ORDEN_CONFIG:
        g = res["global"].get(nombre, {})
        lat = res["eficiencia"].get(nombre, {}).get("latencia_p50_ms", 0.0)
        lin.append(f"| {nombre} | {_fmt(g.get('ndcg@10',0))} | {_fmt(g.get('recall@100',0))} "
                   f"| {_fmt(g.get('mrr@10',0))} | {_fmt(g.get('p@10',0))} | {lat:.1f} |")
    lin.append("")
    for estrato, tabla in res["por_estrato"].items():
        lin += [f"## Estrato: {estrato}", "",
                "| Configuración | nDCG@10 | Recall@100 | MRR@10 | P@10 |",
                "|---|---|---|---|---|"]
        for nombre in ORDEN_CONFIG:
            g = tabla.get(nombre, {})
            lin.append(f"| {nombre} | {_fmt(g.get('ndcg@10',0))} | {_fmt(g.get('recall@100',0))} "
                       f"| {_fmt(g.get('mrr@10',0))} | {_fmt(g.get('p@10',0))} |")
        lin.append("")
    # estadística
    for clave, titulo in [("estadistica_global", "global"),
                          ("estadistica_entidad_exacta", "estrato de entidad exacta")]:
        lin += [f"## Estadística ({titulo})", "",
                "| Comparación | Δ nDCG@10 | IC95 Δ | pares ≠0 / n | r rank-biserial | p Wilcoxon | p Holm | p permut. (Holm) | robusto |",
                "|---|---|---|---|---|---|---|---|---|"]
        for etiqueta, r in res.get(clave, {}).items():
            p, ph, rb, ic = r.get("p_valor"), r.get("p_holm"), r.get("rank_biserial"), r.get("ic95_dif", [None, None])
            f = lambda x, d=4: "n/d" if x is None else f"{x:.{d}f}"
            lin.append(f"| {etiqueta} | {r.get('media_dif',0):+.3f} | [{f(ic[0],3)}, {f(ic[1],3)}] | "
                       f"{r.get('n_pares_no_nulos','?')}/{r.get('n','?')} | {f(rb,3)} | {f(p)} | {f(ph)} | "
                       f"{f(r.get('p_holm_permutacion'))} | {'sí' if r.get('robusto') else 'no'} |")
        lin.append("")
    return "\n".join(lin) + "\n"


def tabla_latex(res: dict) -> str:
    filas = []
    for nombre in ORDEN_CONFIG:
        g = res["global"].get(nombre, {})
        filas.append(f"{nombre} & {_fmt(g.get('ndcg@10',0))} & {_fmt(g.get('recall@100',0))} "
                     f"& {_fmt(g.get('mrr@10',0))} & {_fmt(g.get('p@10',0))} \\\\")
    cuerpo = "\n".join(filas)
    return ("% Tabla de resultados (global). Requiere booktabs.\n"
            "\\begin{table}[htbp]\\centering\\footnotesize\n"
            f"\\caption{{Escalera de ablación, resultados globales (encoder: {res['encoder']}).}}\n"
            "\\label{tab:resultados}\n"
            "\\begin{tabular}{@{}lcccc@{}}\n\\toprule\n"
            "\\textbf{Configuración} & \\textbf{nDCG@10} & \\textbf{Recall@100} & "
            "\\textbf{MRR@10} & \\textbf{P@10} \\\\\n\\midrule\n"
            f"{cuerpo}\n\\bottomrule\n\\end{{tabular}}\n\\end{{table}}\n")


def figura_escalera(res: dict, ruta: Path) -> None:
    etiquetas = ["BM25", "Denso", "Denso\n+onto", "Híbrido", "Híbrido\n+onto", "Híbrido\n+onto+realce"]
    glob = [res["global"].get(n, {}).get("ndcg@10", 0) for n in ORDEN_CONFIG]
    ee = res["por_estrato"].get("entidad_exacta", {})
    ent = [ee.get(n, {}).get("ndcg@10", 0) for n in ORDEN_CONFIG]

    x = range(len(ORDEN_CONFIG))
    ancho = 0.38
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.bar([i - ancho/2 for i in x], glob, ancho, label="Global", color=AZUL)
    ax.bar([i + ancho/2 for i in x], ent, ancho, label="Entidad exacta", color=NARANJA)
    ax.set_xticks(list(x))
    ax.set_xticklabels(etiquetas, fontsize=9)
    ax.set_ylabel("nDCG@10")
    ax.set_ylim(0, 1.0)
    ax.set_title(f"Escalera de ablación (nDCG@10, encoder: {res['encoder']})", fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    for i, (a, b) in enumerate(zip(glob, ent)):
        ax.text(i - ancho/2, a + 0.01, f"{a:.2f}", ha="center", fontsize=7)
        ax.text(i + ancho/2, b + 0.01, f"{b:.2f}", ha="center", fontsize=7)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)


def recomendacion(res: dict) -> str:
    """Elige la configuración con mejor nDCG@10 global, con nota de eficiencia (P6)."""
    candidatos = [(n, res["global"].get(n, {}).get("ndcg@10", 0)) for n in ORDEN_CONFIG]
    mejor = max(candidatos, key=lambda t: t[1])
    lat = res["eficiencia"].get(mejor[0], {})
    idx = res["indice"]
    es_lsa = str(res.get("encoder", "")).startswith("lsa")
    if es_lsa:
        nota = ("> Nota: estas cifras usan el encoder offline `lsa` (validación de tubería). "
                "Para la decisión definitiva, poner `encoder.tipo: sentence-transformer` en "
                "config.yaml, reejecutar `make all` y correr el barrido Matryoshka del "
                "notebook `notebooks/Benchmark_Matryoshka_P6.ipynb`.\n")
    else:
        nota = ("> Nota: el barrido de dimensión Matryoshka (P6) está en "
                "`notebooks/Benchmark_Matryoshka_P6.ipynb`; la matriz densa escala lineal con "
                "la dimensión, de modo que truncar reduce índice y memoria con la retención de "
                "nDCG@10 que ese notebook mide.\n")
    return (f"# Recomendación de configuración (P6)\n\n"
            f"Con el encoder `{res['encoder']}`, la configuración con mejor nDCG@10 global es "
            f"**{mejor[0]}** ({mejor[1]:.3f}).\n\n"
            f"- Latencia p50 / p95: {lat.get('latencia_p50_ms',0):.1f} / "
            f"{lat.get('latencia_p95_ms',0):.1f} ms.\n"
            f"- Índice denso: {idx['n_documentos']} documentos × {idx['dimension_densa']} "
            f"dimensiones ≈ {idx['bytes_aprox_matriz_densa']/1024:.1f} KiB.\n\n"
            + nota)


def generar_todo(ruta_resultados: Path, dir_salida: Path) -> None:
    res = json.loads(ruta_resultados.read_text(encoding="utf-8"))
    dir_salida.mkdir(parents=True, exist_ok=True)
    (dir_salida / "tabla_resultados.md").write_text(tabla_markdown(res), encoding="utf-8")
    (dir_salida / "tabla_resultados.tex").write_text(tabla_latex(res), encoding="utf-8")
    (dir_salida / "recomendacion.md").write_text(recomendacion(res), encoding="utf-8")
    figura_escalera(res, dir_salida / "fig_escalera_ablacion.png")
