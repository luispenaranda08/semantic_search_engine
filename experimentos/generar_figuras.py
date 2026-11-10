#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera las figuras de datos de la monografía (PDF vectorial) en ../figuras/.

Cada figura sale de los mismos archivos de resultados/*.json, corpus/ y datos/ que alimentan
las tablas (generar_tablas_tex.py), de modo que figura y tabla no pueden discrepar. Ninguna
cifra se transcribe a mano salvo las de la composición del registro completo (Tabla tab:escala),
que se indican abajo.

Paleta: azules tenues sobre grises neutros.
  - Configuraciones: BM25 en gris, configuraciones sin ontología en azul claro y con ontología
    en azul oscuro; la identidad la llevan la posición y la etiqueta, no el color solo.
  - Series ordenadas (conjuntos, dimensiones): rampa de un solo tono, de claro a oscuro, con
    marcador y etiqueta directa.
  - Diferencias negativas: un único tono cálido apagado.

Uso:  python3 generar_figuras.py        (o `make figuras`)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from statistics import mean, median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

RAIZ = Path(__file__).resolve().parent
R = RAIZ / "resultados"
SALIDA = RAIZ.parent / "figuras"
CARGA = lambda n: json.loads((R / n).read_text(encoding="utf-8"))
JSONL = lambda p: [json.loads(l) for l in (RAIZ / p).read_text(encoding="utf-8").splitlines() if l.strip()]

# --------------------------------------------------------------------------- estilo
TINTA, TINTA2, TENUE, REJILLA = "#1F2124", "#4A4D52", "#9EA2A8", "#E6E6E6"
B1, B2, B3, B4, B5 = "#C9DBEC", "#9DBFDE", "#5B8DBA", "#2F5F86", "#16304A"
GRIS, CALIDO = "#B4B8BD", "#C98B6B"
RAMPA4 = [B2, B3, B4, B5]
SEQ = LinearSegmentedColormap.from_list("azul", ["#F3F7FB", B1, B2, B3, B4])
ANCHO = 6.5  # pulgadas: ancho de texto de la plantilla (carta, márgenes de 2,5 cm)


def _fuentes() -> str:
    try:
        base = Path(subprocess.check_output(["kpsewhich", "lmsans10-regular.otf"], text=True).strip()).parent
        for f in ("lmsans10-regular.otf", "lmsans10-bold.otf", "lmsans10-oblique.otf"):
            fm.fontManager.addfont(str(base / f))
        return "Latin Modern Sans"
    except Exception:  # sin TeX instalado: fuente sin serifa del sistema
        return "DejaVu Sans"


plt.rcParams.update({
    "font.family": _fuentes(), "font.size": 8.5, "axes.titlesize": 9, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.titlepad": 8, "axes.labelsize": 8.5, "axes.labelcolor": TINTA2,
    "axes.edgecolor": TENUE, "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": TINTA2, "ytick.color": TINTA2, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 3, "ytick.major.size": 3,
    "grid.color": REJILLA, "grid.linewidth": 0.6, "legend.frameon": False, "legend.fontsize": 8,
    "text.color": TINTA, "mathtext.fontset": "custom", "mathtext.rm": "Latin Modern Sans",
    "mathtext.it": "Latin Modern Sans:italic", "pdf.fonttype": 3, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03, "figure.dpi": 150,
})


def coma(x: float, d: int = 3, signo: bool = False) -> str:
    s = f"{x:+.{d}f}" if signo else f"{x:.{d}f}"
    return s.replace(".", ",").replace("-", "−")


def miles(n: float) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


FMT = lambda d: FuncFormatter(lambda v, _: coma(v, d))


def texto_sobre(rgba) -> str:
    """Tinta legible sobre un relleno: blanca si el fondo es oscuro (luminancia relativa)."""
    r, g, b = [(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in rgba[:3]]
    return "white" if 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.26 else TINTA


def rejilla(ax, eje="y"):
    ax.grid(True, axis=eje, zorder=0)
    ax.set_axisbelow(True)


def guardar(fig, nombre):
    SALIDA.mkdir(exist_ok=True)
    fig.savefig(SALIDA / f"{nombre}.pdf")
    fig.savefig(SALIDA / f"{nombre}.png", dpi=170)
    plt.close(fig)
    print(f"  figuras/{nombre}.pdf")


# Configuraciones de la escalera (claves de resultados_*.json) y su codificación visual.
ORDEN = ["BM25 (referencia léxica)", "Denso puro", "Denso + ontología", "Híbrido (sin ontología)",
         "Híbrido + ontología", "Híbrido + ontología + realce"]
CORTA = dict(zip(ORDEN, ["BM25", "C1", "C2", "C3", "C4", "C5"]))
LARGA = dict(zip(ORDEN, ["BM25", "C1 · denso", "C2 · denso + ont.", "C3 · híbrido",
                         "C4 · híbrido + ont.", "C5 · + realce"]))
COLOR_CFG = dict(zip(ORDEN, [GRIS, B2, B4, B2, B4, B4]))


def leyenda_cfg(ax, **kw):
    from matplotlib.patches import Patch
    h = [Patch(color=GRIS, label="BM25 (referencia léxica)"), Patch(color=B2, label="sin ontología"),
         Patch(color=B4, label="con ontología")]
    ax.legend(handles=h, **kw)


# =========================================================================== figuras
def fig_corpus_escala():
    """Tamaño de los corpus (Tabla tab:escala) y composición del registro completo."""
    corpus = [("Versión 1", 17), ("Definitivo", 177), ("v3", 811), ("Registro completo", 757538)]
    # Composición del registro completo tal como la reporta la Tabla tab:escala.
    comp = [("Deportistas", 643107), ("Grupos", 45224), ("Personas de apoyo", 30220),
            ("Instituciones", 13097), ("Escenarios", 12342), ("Acreditaciones", 9685),
            ("Disciplinas de evento", 1837), ("Conocimiento funcional y catálogos", 913),
            ("Reportes y cortes por depto.", 581), ("Competencias", 310), ("Usuarios de gestión", 222)]
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.9), gridspec_kw={"width_ratios": [1, 1.35], "wspace": 0.75})
    y = np.arange(len(corpus))[::-1]
    a.barh(y, [v for _, v in corpus], color=[B2, B2, B3, B4], height=0.62, zorder=3)
    for yi, (_, v) in zip(y, corpus):
        a.text(v * 1.25, yi, miles(v), va="center", fontsize=8, color=TINTA)
    a.set_yticks(y, [n for n, _ in corpus])
    a.set_xscale("log"); a.set_xlim(5, 1.2e7)
    a.xaxis.set_major_locator(FixedLocator([10, 1e3, 1e5]))
    a.xaxis.set_major_formatter(FuncFormatter(lambda v, _: miles(v)))
    a.xaxis.set_minor_locator(NullLocator())
    a.set_xlabel("documentos (escala logarítmica)"); rejilla(a, "x")
    a.set_title("(a) Tamaño de cada corpus")
    a.tick_params(axis="y", length=0)
    y = np.arange(len(comp))[::-1]
    b.barh(y, [v for _, v in comp], color=[B4 if "funcional" in n else B2 for n, _ in comp], height=0.62, zorder=3)
    for yi, (_, v) in zip(y, comp):
        b.text(v * 1.25, yi, miles(v), va="center", fontsize=7.5, color=TINTA)
    b.set_yticks(y, [n for n, _ in comp], fontsize=7.5)
    b.set_xscale("log"); b.set_xlim(100, 8e6)
    b.xaxis.set_major_locator(FixedLocator([1e2, 1e4, 1e6]))
    b.xaxis.set_major_formatter(FuncFormatter(lambda v, _: miles(v)))
    b.xaxis.set_minor_locator(NullLocator())
    b.set_xlabel("documentos (escala logarítmica)"); rejilla(b, "x")
    b.set_title("(b) Composición del registro completo")
    b.tick_params(axis="y", length=0)
    guardar(fig, "fig_corpus_escala")


def fig_analizador():
    """Las etapas del analizador léxico en español sobre una consulta de ejemplo."""
    sys.path.insert(0, str(RAIZ))
    import re
    import unicodedata
    from lib.indexes import _STEMMER_ES, _STOPWORDS_ES, tokenizar_es

    consulta = "¿Qué deportistas de las instituciones pasaron a la Fase Regional?"
    minus = consulta.lower()
    sin_tildes = "".join(c for c in unicodedata.normalize("NFKD", minus) if not unicodedata.combining(c))
    tokens = re.findall(r"[a-z0-9]+", sin_tildes)
    conserva = [t not in _STOPWORDS_ES and len(t) > 1 for t in tokens]
    utiles = [t for t, k in zip(tokens, conserva) if k]
    raices = _STEMMER_ES.stemWords(utiles)
    assert raices == tokenizar_es(consulta), "la figura debe reproducir el analizador real"

    filas = [
        ("1. Consulta original", [(consulta, True)]),
        ("2. Minúsculas y sin tildes", [(sin_tildes, True)]),
        ("3. Separación en términos", [(t, True) for t in tokens]),
        ("4. Sin palabras vacías", [(t, k) for t, k in zip(tokens, conserva)]),
        ("5. Raíz Snowball", [(r, True) for r in raices]),
    ]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.55))
    ax.set_xlim(0, 100); ax.set_ylim(-0.6, len(filas) - 0.4); ax.axis("off")
    rend = fig.canvas.get_renderer()
    for i, (etq, fichas) in enumerate(filas):
        yy = len(filas) - 1 - i
        n = sum(v for _, v in fichas) if i >= 2 else None
        ax.text(0, yy + (0.13 if n else 0), etq, va="center", ha="left", fontsize=8.5, color=TINTA2, fontweight="bold")
        if n:
            ax.text(2.6, yy - 0.2, f"{n} términos", va="center", ha="left", fontsize=7.5, color=TENUE)
        x = 30.0
        for txt, vivo in fichas:
            t = ax.text(x, yy, txt, va="center", ha="left", fontsize=8,
                        color=TINTA if vivo else TENUE, zorder=4)
            bb = t.get_window_extent(renderer=rend).transformed(ax.transData.inverted())
            w = bb.width
            ax.add_patch(FancyBboxPatch((x - 0.7, yy - 0.26), w + 1.4, 0.52,
                                        boxstyle="round,pad=0,rounding_size=0.18",
                                        fc=(B1 if i < 4 else B2) if vivo else "white",
                                        ec=B3 if vivo else REJILLA, lw=0.6 if vivo else 0.8,
                                        ls="-" if vivo else (0, (2, 1.5)), zorder=3))
            if not vivo:
                ax.plot([x - 0.3, x + w + 0.3], [yy, yy], color=TENUE, lw=0.7, zorder=5)
            x += w + 2.0
    guardar(fig, "fig_analizador")


def fig_longitud():
    """Longitud en palabras de la descripción y del documento enriquecido, por tipo de objeto (corpus v3)."""
    docs = JSONL("corpus/corpus_v3.jsonl")
    tipos = [("reportes", "Reportes"), ("competencias", "Pruebas regionales"), ("pruebas_catalogo", "Pruebas del catálogo"),
             ("reglas_participacion", "Reglas de participación"), ("funcionalidades", "Funcionalidades")]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.5))
    rng = np.random.default_rng(7)
    for i, (k, etq) in enumerate(tipos):
        d = [x for x in docs if x["dominio"] == k]
        a = np.array([len(x["descripcion"].split()) for x in d])
        b = np.array([len(x["texto_indexable"].split()) for x in d])
        y = len(tipos) - 1 - i
        for vals, off, col in ((a, 0.17, B2), (b, -0.17, B4)):
            ax.scatter(vals, y + off + rng.uniform(-0.07, 0.07, len(vals)), s=4, color=col, alpha=0.35,
                       lw=0, zorder=3)
            ax.plot([np.percentile(vals, 25), np.percentile(vals, 75)], [y + off] * 2, color=col, lw=3.2,
                    solid_capstyle="round", zorder=4, alpha=0.9)
            ax.scatter([np.median(vals)], [y + off], s=26, color="white", edgecolor=col, lw=1.4, zorder=5)
        ax.text(max(b.max(), a.max()) + 6, y, f"mediana {int(np.median(a))} → {int(np.median(b))}   (n = {len(d)})",
                va="center", fontsize=7.5, color=TINTA2)
    ax.set_yticks(range(len(tipos)), [e for _, e in tipos][::-1])
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("palabras por documento"); ax.set_xlim(0, 330); rejilla(ax, "x")
    ax.scatter([], [], s=26, color=B2, label="descripción original")
    ax.scatter([], [], s=26, color=B4, label="documento enriquecido con la ontología")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=2, handletextpad=0.3)
    guardar(fig, "fig_longitud")


def fig_conjuntos():
    """Composición de los conjuntos de evaluación por estrato (número de consultas)."""
    conj = [
        ("Sintético", "resultados.json", None),
        ("Ampliado", "datos/consultas_real_ampliado.jsonl", None),
        ("Difíciles A + B", "datos/consultas_dificil_ab.jsonl", None),
        ("Definitivo", "datos/consultas_final.jsonl", None),
        ("v3", "datos/consultas_final_v3.jsonl", None),
    ]
    est = [("entidad_exacta", "entidad\nexacta"), ("operacional", "opera-\ncional"), ("documento_largo", "documento\nlargo"),
           ("ambigua", "ambigua"), ("A_puente_ontologia", "difícil:\ncon puente"), ("B_sin_puente", "difícil:\nsin puente"),
           ("C_con_solape", "difícil:\ncon solape"), ("competencias", "pruebas\nregionales"),
           ("prueba_catalogo", "pruebas\ncatálogo"), ("funcionalidad", "funcio-\nnalidades"),
           ("regla_participacion", "reglas"),]
    M = np.zeros((len(conj) + 1, len(est)))
    sint = [c for c in JSONL("datos/consultas_eval.jsonl") if c["estrato"] != "competencias"]
    filas = [sint] + [JSONL(p) for _, p, _ in conj[1:]]
    for i, q in enumerate(filas):
        for j, (k, _) in enumerate(est):
            M[i, j] = sum(1 for c in q if c["estrato"] == k)
    M[-1] = M[-2] + M[2]  # registro completo: las 320 de v3 más las 130 difíciles
    nombres = [n for n, _, _ in conj] + ["Registro completo"]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.6))
    Mm = np.ma.masked_equal(M, 0)
    ax.imshow(Mm, cmap=SEQ, vmin=0, vmax=70, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if M[i, j]:
                ax.text(j, i, int(M[i, j]), ha="center", va="center", fontsize=8,
                        color=texto_sobre(SEQ(M[i, j] / 70)))
            else:
                ax.text(j, i, "·", ha="center", va="center", fontsize=8, color=REJILLA)
        ax.text(len(est) - 0.35, i, f"{int(M[i].sum())}", ha="left", va="center", fontsize=8.5,
                fontweight="bold", color=TINTA)
    ax.text(len(est) - 0.35, -0.95, "total", ha="left", va="center", fontsize=7.5, color=TINTA2)
    ax.set_xticks(range(len(est)), [e for _, e in est], fontsize=7)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(nombres)), nombres)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(est)), minor=True); ax.set_yticks(np.arange(-0.5, len(nombres)), minor=True)
    ax.grid(which="minor", color="white", lw=2); ax.tick_params(which="minor", length=0)
    guardar(fig, "fig_conjuntos")


def fig_escalera_global():
    """nDCG@10 de las seis configuraciones en los cuatro conjuntos del corpus de 17 reportes (Tabla tab:global)."""
    conj = [("sintético", CARGA("resultados.json")), ("ampliado", CARGA("resultados_real_ampliado_v1.json")),
            ("difícil B", CARGA("resultados_dificil_b_v1.json")), ("difícil A", CARGA("resultados_dificil_v1.json"))]
    marc = ["o", "s", "D", "^"]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.9))
    x = np.arange(len(ORDEN))
    finales = []
    for (nm, d), col, mk in zip(conj, RAMPA4, marc):
        v = [d["global"][c]["ndcg@10"] for c in ORDEN]
        ax.plot(x, v, color=col, lw=1.6, marker=mk, ms=5, mec="white", mew=0.8, zorder=3)
        finales.append([v[-1], nm])
    finales.sort(reverse=True)
    for k in range(1, len(finales)):  # separa etiquetas que se tocan
        finales[k][0] = min(finales[k][0], finales[k - 1][0] - 0.045)
    for yv, nm in finales:
        ax.text(x[-1] + 0.15, yv, nm, va="center", fontsize=8, color=TINTA)
    ax.axvspan(3.6, 4.4, color=B1, alpha=0.35, lw=0, zorder=0)
    ax.text(4, 0.08, "configuración\nrecomendada", ha="center", va="bottom", fontsize=7, color=TINTA2)
    ax.set_xticks(x, ["BM25", "C1\ndenso", "C2\ndenso + ont.", "C3\nhíbrido", "C4\nhíbrido + ont.", "C5\n+ realce"])
    ax.set_xlim(-0.3, len(ORDEN) - 0.05)
    ax.set_ylim(0.05, 1.02); ax.yaxis.set_major_formatter(FMT(1)); rejilla(ax)
    ax.set_ylabel("nDCG@10")
    guardar(fig, "fig_escalera_global")


def fig_forest():
    """Diferencia media de nDCG@10 con su intervalo bootstrap del 95 % (Tabla tab:estadistica)."""
    fuentes = [("sintético", CARGA("resultados.json")["estadistica_global"]),
               ("ampliado", CARGA("resultados_real_ampliado_v1.json")["estadistica"]["global"]),
               ("difícil A", CARGA("resultados_dificil_v1.json")["estadistica"]["global"]),
               ("difícil B", CARGA("resultados_dificil_b_v1.json")["estadistica"]["global"]),
               ("A + B", CARGA("resultados_dificil_ab_v1.json")["estadistica"]["global"])]
    comps = [("C3_vs_BM25 (P1)", "C3 − BM25\nseñal léxica + densa"), ("C3_vs_C1 (P1,P2)", "C3 − C1\naporte de BM25"),
             ("C2_vs_C1 (P3 denso)", "C2 − C1\nontología, denso"), ("C4_vs_C3 (P3 híbrido)", "C4 − C3\nontología, híbrido"),
             ("C5_vs_C4 (P5)", "C5 − C4\nrealce por entidad")]
    fig, axs = plt.subplots(1, 5, figsize=(ANCHO, 2.5), sharey=True, gridspec_kw={"wspace": 0.12})
    y = np.arange(len(fuentes))[::-1]
    for ax, (k, etq) in zip(axs, comps):
        lo_all, hi_all = [], []
        for yi, (nm, st) in zip(y, fuentes):
            r = st[k]
            m, (lo, hi) = r["media_dif"], r["ic95_dif"]
            lo_all.append(lo); hi_all.append(hi)
            col = B4 if m >= 0 else CALIDO
            ax.plot([lo, hi], [yi, yi], color=col, lw=1.6, solid_capstyle="round", zorder=3)
            ax.scatter([m], [yi], s=30, zorder=4, color=col if r.get("robusto") else "white", edgecolor=col, lw=1.3)
        ax.axvline(0, color=TINTA2, lw=0.8, zorder=2)
        span = max(abs(min(lo_all)), abs(max(hi_all)))
        ax.set_xlim(min(-0.05, min(lo_all) - 0.03), max(0.05, max(hi_all) + 0.03))
        paso = 0.25 if span > 0.3 else 0.1
        ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(paso))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _, p=paso: coma(v, 2 if p == 0.25 else 1, True) if abs(v) > 1e-9 else "0"))
        ax.set_title(etq, fontsize=7.5, fontweight="normal", loc="center")
        rejilla(ax, "x")
        ax.tick_params(axis="y", length=0)
    axs[0].set_yticks(y, [n for n, _ in fuentes])
    fig.text(0.5, -0.04, "diferencia de nDCG@10 (primera menos segunda) e intervalo del 95 % por bootstrap", ha="center",
             fontsize=8, color=TINTA2)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=B4, ms=5.5, label="concordante (Wilcoxon y permutación tras Holm)"),
         Line2D([], [], marker="o", ls="", mfc="white", mec=B4, ms=5.5, label="no concordante")]
    fig.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2)
    guardar(fig, "fig_forest")


def fig_estratos():
    """nDCG@10 por estrato en el conjunto ampliado (Tabla tab:estratos-ampliado), como mapa de calor."""
    d = CARGA("resultados_real_ampliado_v1.json")
    est = [("entidad_exacta", "entidad exacta\n(n = 55)"), ("operacional", "operacional\n(n = 35)"),
           ("documento_largo", "documento largo\n(n = 25)"), ("ambigua", "ambigua\n(n = 12)")]
    M = np.array([[d["por_estrato"][e][c]["ndcg@10"] for e, _ in est] for c in ORDEN])
    fig, ax = plt.subplots(figsize=(ANCHO * 0.78, 2.6))
    ax.imshow(M, cmap=SEQ, vmin=0.82, vmax=1.0, aspect="auto")
    best = M.max(axis=0)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, coma(M[i, j]), ha="center", va="center", fontsize=8.5,
                    color=texto_sobre(SEQ((M[i, j] - 0.82) / 0.18)),
                    fontweight="bold" if abs(M[i, j] - best[j]) < 1e-12 else "normal")
    ax.set_xticks(range(len(est)), [e for _, e in est]); ax.xaxis.tick_top()
    ax.set_yticks(range(len(ORDEN)), [LARGA[c] for c in ORDEN])
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(est)), minor=True); ax.set_yticks(np.arange(-0.5, len(ORDEN)), minor=True)
    ax.grid(which="minor", color="white", lw=2.5); ax.tick_params(which="minor", length=0)
    guardar(fig, "fig_estratos")


def fig_control_nombre():
    """Control sin nombre propio (Tabla tab:control): nDCG@10 con y sin el nombre en la consulta."""
    a = CARGA("resultados_real_ampliado_v1.json")["por_estrato"]["entidad_exacta"]
    b = CARGA("resultados_real_ampliado_v1_sin_nombre.json")["por_estrato"]["entidad_exacta"]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.3))
    y = np.arange(len(ORDEN))[::-1]
    for yi, c in zip(y, ORDEN):
        va, vb = a[c]["ndcg@10"], b[c]["ndcg@10"]
        ax.plot([va, vb], [yi, yi], color=REJILLA, lw=3, zorder=2, solid_capstyle="round")
        ax.scatter([va], [yi], s=46, color=B4, zorder=4)
        ax.scatter([vb], [yi], s=46, facecolor="white", edgecolor=B3, lw=1.4, zorder=5)
        ax.text(1.06, yi, f"{coma(vb - va, 3, True)}", va="center", ha="right", fontsize=8, color=TINTA2,
                transform=ax.get_yaxis_transform())
    ax.text(1.06, y[0] + 0.75, "sin − con", ha="right", fontsize=7.5, color=TINTA2, transform=ax.get_yaxis_transform())
    ax.set_yticks(y, [LARGA[c] for c in ORDEN]); ax.tick_params(axis="y", length=0)
    ax.set_xlim(0.83, 1.01); ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.05))
    ax.xaxis.set_major_formatter(FMT(2)); rejilla(ax, "x")
    ax.set_xlabel("nDCG@10 en el estrato de entidad exacta (n = 55)")
    ax.scatter([], [], s=40, color=B4, label="consulta con el nombre propio")
    ax.scatter([], [], s=40, facecolor="white", edgecolor=B3, lw=1.4, label="mismo texto con el nombre borrado")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, 1.25), ncol=2)
    guardar(fig, "fig_control_nombre")


def fig_dificil():
    """nDCG@10 por nivel de solape léxico en los difíciles A + B (Tabla tab:dificil)."""
    d = CARGA("resultados_dificil_ab_v1.json")
    q = JSONL("datos/consultas_dificil_ab.jsonl")
    niv = [("A_puente_ontologia", "Con puente: solo comparte\nraíces con la ontología"),
           ("B_sin_puente", "Sin puente: no comparte\nraíces con nada"),
           ("C_con_solape", "Con solape: comparte raíces\ncon la descripción")]
    fig, axs = plt.subplots(1, 3, figsize=(ANCHO, 2.55), sharey=True, gridspec_kw={"wspace": 0.1})
    y = np.arange(len(ORDEN))[::-1]
    for ax, (k, etq) in zip(axs, niv):
        v = [d["por_estrato"][k][c]["ndcg@10"] for c in ORDEN]
        ax.barh(y, v, color=[COLOR_CFG[c] for c in ORDEN], height=0.66, zorder=3)
        for yi, vi in zip(y, v):
            ax.text(vi + 0.02, yi, coma(vi), va="center", fontsize=7.5, color=TINTA)
        n = sum(1 for c in q if c["estrato"] == k)
        ax.set_title(f"{etq} (n = {n})", fontsize=7.5, fontweight="normal", loc="left")
        ax.set_xlim(0, 1.15); ax.xaxis.set_major_locator(FixedLocator([0, 0.5, 1]))
        ax.xaxis.set_major_formatter(FMT(1)); rejilla(ax, "x"); ax.tick_params(axis="y", length=0)
    axs[0].set_yticks(y, [LARGA[c] for c in ORDEN])
    axs[1].set_xlabel("nDCG@10")
    leyenda_cfg(axs[1], loc="upper center", bbox_to_anchor=(0.5, 1.36), ncol=3)
    guardar(fig, "fig_dificil")


def fig_matryoshka():
    """Diferencia de nDCG@10 de C4 frente a la dimensión nativa, por dimensión Matryoshka (Tabla tab:matryoshka)."""
    bar = CARGA("barridos.json")["P6"]["por_conjunto"]
    bar = dict(bar); bar["dificil_ab"] = CARGA("barridos_dificiles.json")["P6"]["por_conjunto"]["dificil_ab"]
    conj = [("sintetico", "sintético (n = 40)", "o"), ("ampliado", "ampliado (n = 127)", "s"),
            ("dificil_ab", "difíciles A + B (n = 130)", "D")]
    dims = [64, 128, 256, 512, 768, 1024]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.7))
    ax.axhspan(-0.01, 0.035, color=B1, alpha=0.3, lw=0, zorder=0)
    ax.axhline(-0.01, color=B3, lw=0.8, ls=(0, (4, 2)), zorder=1)
    ax.text(5.45, -0.0115, "margen de no\ninferioridad: −0,01", fontsize=7.5, color=TINTA2, va="top", ha="right")
    ax.axhline(0, color=TINTA2, lw=0.7, zorder=1)
    for (k, etq, mk), col, off in zip(conj, [B2, B3, B5], [-0.12, 0, 0.12]):
        xs, ms, lo, hi = [], [], [], []
        for m in dims:
            f = bar[k][str(m)]
            xs.append(dims.index(m) + off); ms.append(f["dif_C4_vs_nativa"])
            lo.append(f["ic95_dif"][0]); hi.append(f["ic95_dif"][1])
        ax.vlines(xs, lo, hi, color=col, lw=1.4, zorder=3)
        ax.plot(xs, ms, color=col, lw=0.9, alpha=0.6, zorder=3)
        ax.scatter(xs, ms, marker=mk, s=26, color=col, edgecolor="white", lw=0.6, zorder=4, label=etq)
    ax.set_xticks(range(len(dims)), [f"{miles(m)}\nahorro {100 * (1 - m / 1024):.0f} %" for m in dims], fontsize=7.5)
    ax.set_xlim(-0.5, len(dims) - 0.5)
    ax.set_xlabel("dimensión del vector, m")
    ax.set_ylabel("diferencia de nDCG@10\nfrente a m = 1.024")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: coma(v, 2, True) if v else "0"))
    ax.set_ylim(-0.075, 0.035); rejilla(ax)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
    guardar(fig, "fig_matryoshka")


def fig_escalamiento():
    """Latencia y memoria de la búsqueda exacta al crecer el corpus (Tabla tab:escalamiento)."""
    e = CARGA("escalamiento.json")["celdas"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(ANCHO, 2.6), gridspec_kw={"wspace": 0.35})
    for m, col, mk in zip([64, 256, 1024], [B2, B3, B5], ["o", "s", "D"]):
        c = sorted([x for x in e if x["m"] == m], key=lambda x: x["N"])
        N = [x["N"] for x in c]
        for ax, key in ((a, "p50_ms"), (b, "indice_MiB")):
            v = [x[key] for x in c]
            ax.plot(N, v, color=col, lw=1.6, marker=mk, ms=4.5, mec="white", mew=0.6, zorder=3)
            ax.text(N[-1] * 1.25, v[-1], f"m = {miles(m)}", va="center", fontsize=7.5, color=TINTA)
    for ax, tit, yl in ((a, "(a) Latencia mediana de la búsqueda", "milisegundos"),
                        (b, "(b) Memoria del índice denso", "MiB")):
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(700, 6e5)
        ax.xaxis.set_major_locator(FixedLocator([1e3, 1e4, 1e5]))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: miles(v)))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: coma(v, 2) if v < 1 else miles(v)))
        ax.xaxis.set_minor_locator(NullLocator()); ax.yaxis.set_minor_locator(NullLocator())
        ax.set_title(tit); ax.set_ylabel(yl); ax.set_xlabel("documentos en el índice, N")
        rejilla(ax, "both")
    a.yaxis.set_major_locator(FixedLocator([0.01, 0.1, 1, 10]))
    b.yaxis.set_major_locator(FixedLocator([0.1, 1, 10, 100, 1000]))
    guardar(fig, "fig_escalamiento")


def fig_costo():
    """Tiempo de cada componente (Tabla tab:costo-componentes), en escala logarítmica."""
    c = CARGA("costo_computacional.json")
    filas = [
        ("Cargar el codificador (una vez)", c["carga_modelo_s"] * 1000, False),
        ("Codificar un documento", c["codificar_por_doc_ms"], False),
        ("Construir el índice BM25 (17 documentos)", c["bm25_construir_indice_ms"], False),
        ("Codificar la consulta (GPU integrada, p50)", c["codificar_consulta_ms"]["p50"], True),
        ("Codificar la consulta (solo CPU, p50)", c["codificar_consulta_cpu_ms"]["p50"], True),
        ("Consulta BM25 (p50)", c["bm25_consulta_ms_p50"], True),
        ("Fusión RRF (p50)", c["fusion_rrf_ms_p50"], True),
        ("Búsqueda densa exacta (p50)", c["busqueda_densa_ms_p50"], True),
    ]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.7))
    y = np.arange(len(filas))[::-1]
    ax.barh(y, [v for _, v, _ in filas], color=[B4 if l else B2 for _, _, l in filas], height=0.62, zorder=3, left=1e-3)
    for yi, (_, v, _) in zip(y, filas):
        txt = f"{coma(v, 4 if v < 0.01 else 2 if v < 100 else 0)} ms".replace(",0 ms", " ms")
        if v >= 1000:
            txt = f"{miles(v)} ms"
        ax.text(v * 1.4, yi, txt, va="center", fontsize=7.5, color=TINTA)
    ax.set_yticks(y, [n for n, _, _ in filas]); ax.tick_params(axis="y", length=0)
    ax.set_xscale("log"); ax.set_xlim(1e-3, 2e5)
    ax.xaxis.set_major_locator(FixedLocator([1e-3, 1e-2, 1e-1, 1, 10, 100, 1e3, 1e4]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: coma(v, 3).rstrip("0").rstrip(",") if v < 1 else miles(v)))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel("milisegundos (escala logarítmica)"); rejilla(ax, "x")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=B4, label="en línea: se paga en cada consulta"),
                       Patch(color=B2, label="fuera de línea: se paga al construir el índice")],
              loc="lower right")
    guardar(fig, "fig_costo")


def fig_posiciones():
    """Posición del primer documento relevante en el corpus definitivo (180 consultas)."""
    d = CARGA("resultados_final.json")["por_consulta"]
    cats = [("posición 1", B4), ("2 a 3", B3), ("4 a 10", B2), ("fuera de las 10 primeras", "#E3E6EA")]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.35))
    y = np.arange(len(ORDEN))[::-1]
    for yi, c in zip(y, ORDEN):
        rr = [v["mrr@10"] for v in d[c].values()]
        n = len(rr)
        cuenta = [sum(1 for r in rr if r >= 0.999), sum(1 for r in rr if 0.3 <= r < 0.999),
                  sum(1 for r in rr if 0 < r < 0.3), sum(1 for r in rr if r == 0)]
        izq = 0
        for (etq, col), k in zip(cats, cuenta):
            w = 100 * k / n
            ax.barh(yi, w, left=izq, color=col, height=0.64, edgecolor="white", lw=1.2, zorder=3)
            if w >= 4.5:
                ax.text(izq + w / 2, yi, f"{w:.0f} %".replace(".", ","), ha="center", va="center", fontsize=7.5,
                        color="white" if col in (B4, B3) else TINTA)
            izq += w
    ax.set_yticks(y, [LARGA[c] for c in ORDEN]); ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 100); ax.set_xlabel("porcentaje de consultas")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=col, label=etq) for etq, col in cats], loc="upper center",
              bbox_to_anchor=(0.42, 1.2), ncol=4)
    guardar(fig, "fig_posiciones")


def fig_v3():
    """Diferencia C4 − C2 por tipo de consulta en el corpus v3, con intervalo bootstrap por objetivo (Tabla tab:v3)."""
    v = CARGA("analisis_v3.json")["v3_completo"]
    est = [("entidad_exacta", "Entidad exacta (reportes)"), ("operacional", "Operacional (reportes)"),
           ("documento_largo", "Documento largo (reportes)"), ("ambigua", "Ambigua (reportes)"),
           ("competencias", "Pruebas regionales"), ("prueba_catalogo", "Pruebas del catálogo"),
           ("funcionalidad", "Funcionalidades"), ("regla_participacion", "Reglas de participación"),
           ("global", "Total")]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.75))
    y = np.arange(len(est))[::-1].astype(float)
    y[-1] -= 0.4
    for yi, (k, etq) in zip(y, est):
        r = v[k]["comparaciones"]["C4−C2"]
        m, (lo, hi) = r["media_dif"], r["ic95_bootstrap_objetivo"]
        col = B4 if m >= 0 else CALIDO
        ax.plot([lo, hi], [yi, yi], color=col, lw=1.8, solid_capstyle="round", zorder=3)
        ax.scatter([m], [yi], s=34, color=col if r["concordante"] else "white", edgecolor=col, lw=1.4, zorder=4)
        ax.text(0.5, yi, f"{coma(m, 3, True)}   (n = {v[k]['n']})", va="center", fontsize=7.5, color=TINTA2)
    ax.axhline(y[-1] + 0.7, color=REJILLA, lw=0.8)
    ax.axvline(0, color=TINTA2, lw=0.8)
    ax.set_yticks(y, [e for _, e in est]); ax.tick_params(axis="y", length=0)
    ax.set_xlim(-0.7, 0.75)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: coma(v, 1, True) if v else "0"))
    ax.set_xlabel("diferencia de nDCG@10, C4 (híbrido con ontología) − C2 (denso con ontología)")
    ax.text(-0.68, y[0] + 0.75, "← mejor el denso", fontsize=7.5, color=TINTA2)
    ax.text(0.47, y[0] + 0.75, "mejor el híbrido →", fontsize=7.5, color=TINTA2, ha="right")
    rejilla(ax, "x")
    guardar(fig, "fig_v3")


def fig_registro():
    """nDCG@10 con 811 documentos y con el registro completo (Tabla tab:escalera-registro)."""
    a = JSONL_R("escalamiento/v3.json"); b = JSONL_R("escalamiento/registro.json")
    cfg = [("BM25", "BM25 (descripción)"), ("C1_denso", "C1 · denso sin ontología"),
           ("C2_denso_onto", "C2 · denso con ontología"), ("C3_rrf", "C3 · RRF sin ontología"),
           ("C4_rrf_onto", "C4 · RRF con ontología"), ("convexa_onto", "Convexa con ontología"),
           ("C4_funcion", "C4, tipo conocido"), ("convexa_funcion", "Convexa, tipo conocido")]
    fig, ax = plt.subplots(figsize=(ANCHO, 2.75))
    y = np.arange(len(cfg))[::-1].astype(float)
    y[-2:] -= 0.4
    for yi, (k, etq) in zip(y, cfg):
        va, vb = mean(q[k] for q in a), mean(q[k] for q in b)
        ax.annotate("", xy=(vb, yi), xytext=(va, yi),
                    arrowprops=dict(arrowstyle="-|>", color=B3, lw=1.2, shrinkA=4, shrinkB=4, mutation_scale=8), zorder=3)
        ax.scatter([va], [yi], s=40, facecolor="white", edgecolor=B3, lw=1.4, zorder=4)
        ax.scatter([vb], [yi], s=40, color=B5, zorder=4)
        ax.text(0.94, yi, coma(vb - va, 3, True), va="center", ha="left", fontsize=8, color=TINTA2)
    ax.text(0.94, y[0] + 0.8, "cambio", fontsize=7.5, color=TINTA2)
    ax.axhline(y[-2] + 0.7, color=REJILLA, lw=0.8)
    ax.set_yticks(y, [e for _, e in cfg]); ax.tick_params(axis="y", length=0)
    ax.set_xlim(0.05, 0.93); ax.xaxis.set_major_formatter(FMT(1)); rejilla(ax, "x")
    ax.set_xlabel("nDCG@10 promedio de las 450 consultas")
    ax.scatter([], [], s=40, facecolor="white", edgecolor=B3, lw=1.4, label="811 documentos (corpus v3)")
    ax.scatter([], [], s=40, color=B5, label="757.554 documentos (registro completo)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, 1.16), ncol=2)
    guardar(fig, "fig_registro")


def fig_confusion():
    """Matriz de confusión objetivo -> reporte devuelto en primer lugar por C4, difíciles A + B (130 consultas)."""
    d = CARGA("analisis_errores.json")
    docs = {x["id"]: x["titulo"] for x in JSONL("corpus/corpus_v1.jsonl")}
    corto = lambda t: (t.replace("Reporte sobre ", "").replace("Reporte de ", "").replace("Reporte ", "")
                       .replace("Resumen del ", "").replace("Resumen de ", "Resumen ")[:36])
    ids = sorted(docs, key=lambda i: docs[i])
    M = np.zeros((len(ids), len(ids)), int)
    pos = {k: i for i, k in enumerate(ids)}
    for cn in ("dificil", "dificil_b"):
        m = d[cn]["matriz"]["C4"]
        for t, n in m["aciertos"].items():
            M[pos[t], pos[t]] += n
        for t, p, n in m["errores"]:
            M[pos[t], pos[p]] += n
    filas = [i for i in range(len(ids)) if M[i].sum() > 0]
    cols = [j for j in range(len(ids)) if M[:, j].sum() > 0]
    M = M[np.ix_(filas, cols)]
    fig, ax = plt.subplots(figsize=(ANCHO, 4.6))
    ax.imshow(np.ma.masked_equal(M, 0), cmap=SEQ, vmin=0, vmax=max(10, M.max()), aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if M[i, j]:
                diag = ids[filas[i]] == ids[cols[j]]
                ax.text(j, i, M[i, j], ha="center", va="center", fontsize=7.5,
                        color=texto_sobre(SEQ(M[i, j] / max(10, M.max()))), fontweight="bold" if diag else "normal")
    ax.set_yticks(range(len(filas)), [corto(docs[ids[i]]) for i in filas], fontsize=7)
    ax.set_xticks(range(len(cols)), [corto(docs[ids[j]]) for j in cols], fontsize=7, rotation=55, ha="right")
    ax.set_ylabel("reporte objetivo"); ax.set_xlabel("reporte que C4 devuelve en primer lugar")
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(cols)), minor=True); ax.set_yticks(np.arange(-0.5, len(filas)), minor=True)
    ax.grid(which="minor", color="white", lw=1.5); ax.tick_params(which="minor", length=0)
    guardar(fig, "fig_confusion")


def JSONL_R(n):
    return CARGA(n)["consultas"]


FIGURAS = [fig_corpus_escala, fig_analizador, fig_longitud, fig_conjuntos, fig_escalera_global, fig_forest,
           fig_estratos, fig_control_nombre, fig_dificil, fig_matryoshka, fig_escalamiento, fig_costo,
           fig_posiciones, fig_v3, fig_registro, fig_confusion]

if __name__ == "__main__":
    pedidas = set(sys.argv[1:])
    for f in FIGURAS:
        if not pedidas or f.__name__ in pedidas:
            f()
