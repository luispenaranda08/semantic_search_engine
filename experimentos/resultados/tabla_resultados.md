# Resultados de la escalera de ablación

Encoder: `jina-embeddings-v3`. Consultas con juicios en la v1: 40. Consultas de competencias sin cobertura en la v1 (vacío de cobertura): 11.

## Global (consultas con documento relevante en la v1)

| Configuración | nDCG@10 | Recall@100 | MRR@10 | P@10 | Lat. p50 (ms) |
|---|---|---|---|---|---|
| BM25 (referencia léxica) | 0.819 | 0.950 | 0.790 | 0.113 | 0.1 |
| Denso puro | 0.866 | 1.000 | 0.832 | 0.117 | 345.4 |
| Denso + ontología | 0.931 | 1.000 | 0.919 | 0.117 | 342.3 |
| Híbrido (sin ontología) | 0.893 | 1.000 | 0.867 | 0.117 | 339.9 |
| Híbrido + ontología | 0.948 | 1.000 | 0.942 | 0.117 | 344.3 |
| Híbrido + ontología + realce | 0.924 | 1.000 | 0.911 | 0.117 | 341.5 |

## Estrato: ambigua

| Configuración | nDCG@10 | Recall@100 | MRR@10 | P@10 |
|---|---|---|---|---|
| BM25 (referencia léxica) | 0.846 | 0.846 | 0.846 | 0.085 |
| Denso puro | 0.894 | 1.000 | 0.859 | 0.100 |
| Denso + ontología | 0.956 | 1.000 | 0.942 | 0.100 |
| Híbrido (sin ontología) | 0.920 | 1.000 | 0.896 | 0.100 |
| Híbrido + ontología | 0.962 | 1.000 | 0.949 | 0.100 |
| Híbrido + ontología + realce | 0.962 | 1.000 | 0.949 | 0.100 |

## Estrato: documento_largo

| Configuración | nDCG@10 | Recall@100 | MRR@10 | P@10 |
|---|---|---|---|---|
| BM25 (referencia léxica) | 0.677 | 1.000 | 0.609 | 0.130 |
| Denso puro | 0.815 | 1.000 | 0.787 | 0.130 |
| Denso + ontología | 0.900 | 1.000 | 0.900 | 0.130 |
| Híbrido (sin ontología) | 0.721 | 1.000 | 0.653 | 0.130 |
| Híbrido + ontología | 0.884 | 1.000 | 0.883 | 0.130 |
| Híbrido + ontología + realce | 0.819 | 1.000 | 0.800 | 0.130 |

## Estrato: entidad_exacta

| Configuración | nDCG@10 | Recall@100 | MRR@10 | P@10 |
|---|---|---|---|---|
| BM25 (referencia léxica) | 0.883 | 1.000 | 0.853 | 0.124 |
| Denso puro | 0.875 | 1.000 | 0.838 | 0.124 |
| Denso + ontología | 0.931 | 1.000 | 0.912 | 0.124 |
| Híbrido (sin ontología) | 0.972 | 1.000 | 0.971 | 0.124 |
| Híbrido + ontología | 0.976 | 1.000 | 0.971 | 0.124 |
| Híbrido + ontología + realce | 0.957 | 1.000 | 0.948 | 0.124 |

## Estadística (global)

| Comparación | Δ nDCG@10 | IC95 Δ | pares ≠0 / n | r rank-biserial | p Wilcoxon | p Holm | p permut. (Holm) | robusto |
|---|---|---|---|---|---|---|---|---|
| C3_vs_BM25 (P1) | +0.073 | [0.030, 0.124] | 11/40 | 0.970 | 0.0042 | 0.0212 | 0.0098 | sí |
| C3_vs_C1 (P1,P2) | +0.026 | [-0.030, 0.085] | 11/40 | 0.242 | 0.4758 | 0.5701 | 0.8203 | no |
| C2_vs_C1 (P3 denso) | +0.065 | [0.020, 0.116] | 10/40 | 0.964 | 0.0068 | 0.0274 | 0.0156 | sí |
| C4_vs_C3 (P3 híbrido) | +0.056 | [0.017, 0.102] | 10/40 | 0.873 | 0.0142 | 0.0427 | 0.0352 | sí |
| C5_vs_C4 (P5) | -0.024 | [-0.074, 0.018] | 3/40 | -0.667 | 0.2850 | 0.5701 | 0.8203 | no |

## Estadística (estrato de entidad exacta)

| Comparación | Δ nDCG@10 | IC95 Δ | pares ≠0 / n | r rank-biserial | p Wilcoxon | p Holm | p permut. (Holm) | robusto |
|---|---|---|---|---|---|---|---|---|
| C3_vs_BM25 (P1) | +0.089 | [0.024, 0.174] | 5/17 | 1.000 | 0.0339 | 0.1695 | 0.3125 | no |
| C3_vs_C1 (P1,P2) | +0.097 | [-0.000, 0.218] | 5/17 | 0.600 | 0.2228 | 0.5765 | 1.0000 | no |
| C2_vs_C1 (P3 denso) | +0.055 | [0.000, 0.134] | 4/17 | 0.800 | 0.1441 | 0.5765 | 1.0000 | no |
| C4_vs_C3 (P3 híbrido) | +0.004 | [0.000, 0.011] | 2/17 | 1.000 | 0.1573 | 0.5765 | 1.0000 | no |
| C5_vs_C4 (P5) | -0.019 | [-0.123, 0.065] | 2/17 | -0.333 | 0.6547 | 0.6547 | 1.0000 | no |

