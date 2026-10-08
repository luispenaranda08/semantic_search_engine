# Experimentos: escalera de ablación del buscador semántico híbrido

Código, conjuntos de evaluación sintéticos y resultados del proyecto de grado (Universidad del Norte, Ciencia de Datos).
Documento principal: [`../monografia/monografia_buscador_semantico_PRIME.tex`](../monografia/monografia_buscador_semantico_PRIME.tex).
Guía de comprensión y sustentación: [`../guias/GUIA_SUSTENTACION_DETALLADA.md`](../guias/GUIA_SUSTENTACION_DETALLADA.md).

## Qué contiene

| Carpeta | Contenido |
|---|---|
| `lib/` | BM25 propio (Snowball ES), índice denso, RRF y fusiones alternativas, detector de entidades, métricas, estadística (Wilcoxon, permutación pareada, rank-biserial, bootstrap, Holm) |
| `corpus/` | `corpus_v1.jsonl`: 17 descripciones de reportes enriquecidas con la ontología (sin datos personales) |
| `datos/` | Consultas y juicios de relevancia: sintético, ampliado (127), difícil A (52), difícil B (78) y unión. Todos los nombres propios son **sintéticos** |
| `resultados/` | JSON, tablas y figuras de todas las corridas (jina-embeddings-v3 con tareas de recuperación) |
| `anotacion/` | Scripts para hojas de anotación ciega (pooling) y κ de Cohen; instrucciones a anotadores |
| `tests/` | 19 pruebas del núcleo (`python3 tests/test_nucleo.py`) |
| `../data/ontologia_suid/` | Ontología del dominio (13 clases, 20 relaciones) y metadatos por reporte |

## Reproducir

```bash
cd experimentos
python3 -m pip install -r requirements.txt
make test          # pruebas, sin modelo
make all           # escalera sobre el conjunto sintético (descarga jina-embeddings-v3 la primera vez)
make eval_real control dificil dificil_b fusion ontologia_completa errores barridos tablas
```

## Qué NO está publicado, a propósito

- Las ejecuciones y firmas del historial real de consultas (`data/athena_suid/`) y los scripts de extracción contra el almacén de datos:
  son datos de producción de la organización del caso de estudio. Por eso `construir_eval_real*.py`, `enriquecimiento_completo.py` y
  `preprocess_corpus.py` no corren desde este repositorio sin esos insumos; sus salidas (`datos/`, `corpus/`, `resultados/`) sí están.
- Las hojas de anotación generadas y su clave de *pooling* (se regeneran con `make anotacion`).
- Los PDF de los artículos citados y los resultados obsoletos anteriores a la auditoría del 2026-09-30.

## Lectura honesta de los resultados

Los juicios son *silver* (el reporte ejecutado) o redactados por el autor; no hay anotación por expertos todavía. El nDCG absoluto
no es precisión de producción: lo válido es la comparación relativa entre configuraciones. Ver la sección «Amenazas a la validez» de la monografía.
