"""Genera la imagen de portada del libro (images/portada.png).

Espacio de embeddings estilizado: documentos agrupados por clase de la ontología,
aristas de la ontología entre clases, una consulta que recupera sus vecinos más
cercanos, y la fusión de las señales léxica y densa.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

rng = np.random.default_rng(7)
FONDO, TINTA, SUAVE = "#0b1a2e", "#eef3fa", "#8fa6c4"
CLASES = {
    "Deportista": ((7.2, 6.4), "#5aa9e6"),
    "Institución": ((10.6, 7.3), "#7fc8a9"),
    "Promoción": ((8.2, 3.6), "#f2b84b"),
    "Competencia": ((12.4, 4.4), "#e8746b"),
    "Grupo": ((10.0, 1.9), "#b394e6"),
    "Región": ((13.6, 7.9), "#63d2c6"),
}
ARISTAS = [("Deportista", "Institución"), ("Deportista", "Promoción"),
           ("Deportista", "Grupo"), ("Institución", "Región"),
           ("Competencia", "Región"), ("Competencia", "Deportista"),
           ("Grupo", "Institución")]

fig = plt.figure(figsize=(16, 6.4), dpi=150)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 16); ax.set_ylim(0, 9.6); ax.axis("off")
fig.patch.set_facecolor(FONDO); ax.set_facecolor(FONDO)

# retícula tenue del espacio vectorial
for x in np.arange(5.5, 16, 0.6):
    ax.plot([x, x], [0.4, 9.2], color="#16304f", lw=0.5, zorder=0)
for y in np.arange(0.4, 9.4, 0.6):
    ax.plot([5.5, 15.8], [y, y], color="#16304f", lw=0.5, zorder=0)

# aristas de la ontología entre centros de clase
for a, b in ARISTAS:
    (xa, ya), _ = CLASES[a]; (xb, yb), _ = CLASES[b]
    ax.plot([xa, xb], [ya, yb], color="#3a5a82", lw=1.4, alpha=0.7, zorder=1)

# nubes de documentos por clase
docs = []
for nombre, ((cx, cy), color) in CLASES.items():
    pts = rng.normal([cx, cy], [0.55, 0.45], size=(26, 2))
    ax.scatter(pts[:, 0], pts[:, 1], s=26, color=color, alpha=0.85,
               edgecolors="none", zorder=2)
    ax.scatter([cx], [cy], s=260, color=color, alpha=0.18, zorder=1)
    ax.text(cx, cy + 0.95, nombre, color=color, fontsize=11, ha="center",
            fontweight="bold", zorder=4)
    docs.extend(pts.tolist())
docs = np.array(docs)

# consulta y sus vecinos más cercanos
q = np.array([8.9, 5.3])
d = np.linalg.norm(docs - q, axis=1)
for i in np.argsort(d)[:6]:
    ax.plot([q[0], docs[i, 0]], [q[1], docs[i, 1]], color="#ffffff", lw=1.1,
            ls=(0, (3, 2)), alpha=0.75, zorder=3)
    ax.scatter(*docs[i], s=70, facecolors="none", edgecolors="#ffffff", lw=1.2, zorder=4)
for r, a in [(1.35, 0.06), (0.95, 0.09), (0.55, 0.14)]:
    ax.add_patch(plt.Circle(q, r, color="#ffffff", alpha=a, zorder=2))
ax.scatter(*q, marker="*", s=620, color="#ffd23f", edgecolors=FONDO, lw=1.2, zorder=6)
ax.text(q[0] + 0.25, q[1] - 0.55, "consulta", color="#ffd23f", fontsize=10.5, zorder=6)

# panel de título a la izquierda
ax.add_patch(FancyBboxPatch((0.45, 0.55), 5.0, 8.5, boxstyle="round,pad=0.02,rounding_size=0.25",
                            facecolor="#0e2239", edgecolor="#1f3d63", lw=1.2, zorder=5))
ax.text(0.85, 7.9, "BUSCADOR", color=TINTA, fontsize=30, fontweight="bold", zorder=6)
ax.text(0.85, 7.0, "SEMÁNTICO", color="#5aa9e6", fontsize=30, fontweight="bold", zorder=6)
ax.text(0.88, 6.35, "GovTech · español · entidades exactas", color=SUAVE, fontsize=12, zorder=6)

y = 5.25
for etq, color in [("BM25  (léxico)", "#f2b84b"), ("Denso  (jina-v3)", "#5aa9e6"),
                   ("Ontología  (13 clases)", "#7fc8a9")]:
    ax.add_patch(FancyBboxPatch((0.9, y - 0.2), 3.2, 0.55, boxstyle="round,pad=0.02,rounding_size=0.12",
                                facecolor=FONDO, edgecolor=color, lw=1.4, zorder=6))
    ax.text(1.1, y + 0.03, etq, color=color, fontsize=11.5, va="center", zorder=7)
    ax.annotate("", xy=(4.85, 2.85), xytext=(4.1, y + 0.05),
                arrowprops=dict(arrowstyle="-", color="#3a5a82", lw=1.1), zorder=5)
    y -= 0.8
ax.add_patch(FancyBboxPatch((4.25, 2.45), 1.1, 0.8, boxstyle="round,pad=0.02,rounding_size=0.15",
                            facecolor="#ffd23f", edgecolor="none", zorder=6))
ax.text(4.8, 2.85, "RRF", color=FONDO, fontsize=13, fontweight="bold", ha="center", va="center", zorder=7)
ax.text(0.88, 2.0, "Recuperación híbrida · Escalera de ablación", color=TINTA, fontsize=11.5, zorder=6)
ax.text(0.88, 1.5, "nDCG@10 · MRR@10 · Recall@100 · Wilcoxon", color=SUAVE, fontsize=11, zorder=6)
ax.text(0.88, 0.95, "Proyecto de grado · Ciencia de Datos · Uninorte", color=SUAVE, fontsize=10, zorder=6)

salida = Path(__file__).resolve().parents[1] / "images" / "portada.png"
salida.parent.mkdir(exist_ok=True)
fig.savefig(salida, dpi=150, facecolor=FONDO)
print("escrita:", salida)
