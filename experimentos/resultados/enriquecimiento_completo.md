# Ontología parcial (9/17) frente a completa

Reportes enriquecidos: parcial = 9, completa = 14 de 17.

Entidades derivadas mecánicamente de las firmas reales:

- `ri_010_reporte_sobre_distribucion_de_usuarios`: — sin clase mapeable; queda sin enriquecer
- `ri_011_reporte_sobre_metricas_por_federacion_deportiva`: Disciplina Deportiva 
- `ri_012_reporte_sobre_pruebas_de_caidas_todas_las_etapas`: Competencia / Prueba Regional, Disciplina Deportiva, Ubicación Geográfica 
- `ri_013_reporte_de_cambios_en_la_intencion_de_participacion`: Participación/Delegación 
- `ri_014_reporte_de_delegaciones_de_participacion`: Participación/Delegación, Ubicación Geográfica 
- `ri_015_reporte_sobre_pruebas_de_caidas`: Competencia / Prueba Regional, Disciplina Deportiva 
- `ri_016_reporte_sobre_resumen_de_pruebas_de_caidas`: — sin clase mapeable; queda sin enriquecer
- `ri_017_reporte_sobre_resumen_de_pruebas_de_caidas_todas_las_etapas`: — sin clase mapeable; queda sin enriquecer

## nDCG@10 medio

| Conjunto | n | denso desc | denso parcial | denso completa | híbrido desc | híbrido parcial | híbrido completa |
|---|---|---|---|---|---|---|---|
| sintetico | 40 | 0.866 | 0.931 | 0.904 | 0.893 | 0.948 | 0.937 |
| ampliado | 127 | 0.932 | 0.928 | 0.921 | 0.943 | 0.960 | 0.960 |
| dificil | 52 | 0.712 | 0.835 | 0.819 | 0.686 | 0.788 | 0.801 |
| dificil_b | 78 | 0.783 | 0.837 | 0.833 | 0.778 | 0.835 | 0.839 |

## sintetico

| Grupo | Comparación | n | Δ | pares≠0 | p Wilcoxon | p permut. |
|---|---|---|---|---|---|---|
| todas | denso: completa − parcial | 40 | -0.028 | 5 | 0.0412 | 0.0625 |
| todas | denso: completa − desc | 40 | +0.037 | 8 | 0.0172 | 0.0156 |
| todas | denso: parcial − desc | 40 | +0.065 | 10 | 0.0068 | 0.0039 |
| todas | hibrido: completa − parcial | 40 | -0.012 | 3 | 0.2850 | 0.5000 |
| todas | hibrido: completa − desc | 40 | +0.044 | 10 | 0.0163 | 0.0176 |
| todas | hibrido: parcial − desc | 40 | +0.056 | 10 | 0.0142 | 0.0117 |
| objetivo_sin_bloque_antes | denso: completa − parcial | 4 | +0.000 | 0 | n/d | n/d |
| objetivo_sin_bloque_antes | denso: completa − desc | 4 | +0.000 | 0 | n/d | n/d |
| objetivo_sin_bloque_antes | denso: parcial − desc | 4 | +0.000 | 0 | n/d | n/d |
| objetivo_sin_bloque_antes | hibrido: completa − parcial | 4 | +0.000 | 0 | n/d | n/d |
| objetivo_sin_bloque_antes | hibrido: completa − desc | 4 | +0.000 | 0 | n/d | n/d |
| objetivo_sin_bloque_antes | hibrido: parcial − desc | 4 | +0.000 | 0 | n/d | n/d |
| objetivo_con_bloque_antes | denso: completa − parcial | 36 | -0.031 | 5 | 0.0412 | 0.0625 |
| objetivo_con_bloque_antes | denso: completa − desc | 36 | +0.042 | 8 | 0.0172 | 0.0156 |
| objetivo_con_bloque_antes | denso: parcial − desc | 36 | +0.072 | 10 | 0.0068 | 0.0039 |
| objetivo_con_bloque_antes | hibrido: completa − parcial | 36 | -0.013 | 3 | 0.2850 | 0.5000 |
| objetivo_con_bloque_antes | hibrido: completa − desc | 36 | +0.049 | 10 | 0.0163 | 0.0176 |
| objetivo_con_bloque_antes | hibrido: parcial − desc | 36 | +0.062 | 10 | 0.0142 | 0.0117 |

## ampliado

| Grupo | Comparación | n | Δ | pares≠0 | p Wilcoxon | p permut. |
|---|---|---|---|---|---|---|
| todas | denso: completa − parcial | 127 | -0.007 | 4 | 0.0633 | 0.1250 |
| todas | denso: completa − desc | 127 | -0.011 | 12 | 0.1640 | 0.1616 |
| todas | denso: parcial − desc | 127 | -0.004 | 11 | 0.6549 | 0.5547 |
| todas | hibrido: completa − parcial | 127 | +0.000 | 2 | 1.0000 | 1.0000 |
| todas | hibrido: completa − desc | 127 | +0.016 | 15 | 0.1205 | 0.1370 |
| todas | hibrido: parcial − desc | 127 | +0.016 | 13 | 0.1262 | 0.1353 |
| objetivo_sin_bloque_antes | denso: completa − parcial | 15 | -0.025 | 1 | 0.3173 | 1.0000 |
| objetivo_sin_bloque_antes | denso: completa − desc | 15 | -0.025 | 1 | 0.3173 | 1.0000 |
| objetivo_sin_bloque_antes | denso: parcial − desc | 15 | +0.000 | 0 | n/d | n/d |
| objetivo_sin_bloque_antes | hibrido: completa − parcial | 15 | +0.009 | 1 | 0.3173 | 1.0000 |
| objetivo_sin_bloque_antes | hibrido: completa − desc | 15 | +0.009 | 1 | 0.3173 | 1.0000 |
| objetivo_sin_bloque_antes | hibrido: parcial − desc | 15 | +0.000 | 0 | n/d | n/d |
| objetivo_con_bloque_antes | denso: completa − parcial | 112 | -0.005 | 3 | 0.1025 | 0.2500 |
| objetivo_con_bloque_antes | denso: completa − desc | 112 | -0.009 | 11 | 0.2812 | 0.2725 |
| objetivo_con_bloque_antes | denso: parcial − desc | 112 | -0.005 | 11 | 0.6549 | 0.5547 |
| objetivo_con_bloque_antes | hibrido: completa − parcial | 112 | -0.001 | 1 | 0.3173 | 1.0000 |
| objetivo_con_bloque_antes | hibrido: completa − desc | 112 | +0.018 | 14 | 0.1429 | 0.1619 |
| objetivo_con_bloque_antes | hibrido: parcial − desc | 112 | +0.019 | 13 | 0.1262 | 0.1353 |

## dificil

| Grupo | Comparación | n | Δ | pares≠0 | p Wilcoxon | p permut. |
|---|---|---|---|---|---|---|
| todas | denso: completa − parcial | 52 | -0.016 | 12 | 0.3238 | 0.3398 |
| todas | denso: completa − desc | 52 | +0.107 | 23 | 0.0027 | 0.0012 |
| todas | denso: parcial − desc | 52 | +0.122 | 21 | 0.0006 | 0.0001 |
| todas | hibrido: completa − parcial | 52 | +0.014 | 9 | 0.9055 | 0.5625 |
| todas | hibrido: completa − desc | 52 | +0.116 | 34 | 0.0142 | 0.0121 |
| todas | hibrido: parcial − desc | 52 | +0.102 | 34 | 0.0344 | 0.0359 |
| objetivo_sin_bloque_antes | denso: completa − parcial | 16 | +0.003 | 5 | 0.8918 | 1.0000 |
| objetivo_sin_bloque_antes | denso: completa − desc | 16 | -0.003 | 7 | 0.8646 | 1.0000 |
| objetivo_sin_bloque_antes | denso: parcial − desc | 16 | -0.006 | 5 | 0.6845 | 0.8750 |
| objetivo_sin_bloque_antes | hibrido: completa − parcial | 16 | +0.071 | 6 | 0.4631 | 0.3750 |
| objetivo_sin_bloque_antes | hibrido: completa − desc | 16 | -0.091 | 9 | 0.0730 | 0.0781 |
| objetivo_sin_bloque_antes | hibrido: parcial − desc | 16 | -0.161 | 8 | 0.0117 | 0.0078 |
| objetivo_con_bloque_antes | denso: completa − parcial | 36 | -0.024 | 7 | 0.1261 | 0.1719 |
| objetivo_con_bloque_antes | denso: completa − desc | 36 | +0.156 | 16 | 0.0006 | 0.0001 |
| objetivo_con_bloque_antes | denso: parcial − desc | 36 | +0.180 | 16 | 0.0004 | 0.0000 |
| objetivo_con_bloque_antes | hibrido: completa − parcial | 36 | -0.012 | 3 | 0.2850 | 0.5000 |
| objetivo_con_bloque_antes | hibrido: completa − desc | 36 | +0.207 | 25 | 0.0008 | 0.0006 |
| objetivo_con_bloque_antes | hibrido: parcial − desc | 36 | +0.219 | 26 | 0.0005 | 0.0004 |

## dificil_b

| Grupo | Comparación | n | Δ | pares≠0 | p Wilcoxon | p permut. |
|---|---|---|---|---|---|---|
| todas | denso: completa − parcial | 78 | -0.003 | 8 | 0.8881 | 0.6875 |
| todas | denso: completa − desc | 78 | +0.051 | 19 | 0.0012 | 0.0009 |
| todas | denso: parcial − desc | 78 | +0.054 | 21 | 0.0014 | 0.0009 |
| todas | hibrido: completa − parcial | 78 | +0.003 | 14 | 0.8256 | 0.8209 |
| todas | hibrido: completa − desc | 78 | +0.061 | 32 | 0.0608 | 0.0337 |
| todas | hibrido: parcial − desc | 78 | +0.058 | 30 | 0.0783 | 0.0555 |
| objetivo_sin_bloque_antes | denso: completa − parcial | 24 | +0.012 | 3 | 0.1025 | 0.2500 |
| objetivo_sin_bloque_antes | denso: completa − desc | 24 | +0.007 | 2 | 0.1797 | 0.5000 |
| objetivo_sin_bloque_antes | denso: parcial − desc | 24 | -0.005 | 2 | 0.6547 | 1.0000 |
| objetivo_sin_bloque_antes | hibrido: completa − parcial | 24 | +0.066 | 7 | 0.0625 | 0.0781 |
| objetivo_sin_bloque_antes | hibrido: completa − desc | 24 | -0.007 | 5 | 0.7865 | 0.8750 |
| objetivo_sin_bloque_antes | hibrido: parcial − desc | 24 | -0.074 | 5 | 0.0431 | 0.0625 |
| objetivo_con_bloque_antes | denso: completa − parcial | 54 | -0.010 | 5 | 0.2249 | 0.2500 |
| objetivo_con_bloque_antes | denso: completa − desc | 54 | +0.070 | 17 | 0.0024 | 0.0015 |
| objetivo_con_bloque_antes | denso: parcial − desc | 54 | +0.080 | 19 | 0.0010 | 0.0006 |
| objetivo_con_bloque_antes | hibrido: completa − parcial | 54 | -0.025 | 7 | 0.0176 | 0.0156 |
| objetivo_con_bloque_antes | hibrido: completa − desc | 54 | +0.091 | 27 | 0.0457 | 0.0218 |
| objetivo_con_bloque_antes | hibrido: parcial − desc | 54 | +0.116 | 25 | 0.0060 | 0.0023 |
