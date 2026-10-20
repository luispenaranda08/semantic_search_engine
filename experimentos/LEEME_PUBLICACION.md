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
| `construir_corpus_v3.py`, `analisis_v3.py`, `fusion_v3.py` | Corpus v3 (811 documentos de cinco tipos: reportes, pruebas regionales, roles y permisos, pruebas del catálogo, reglas de participación), su análisis por tipo de consulta y la fusión sensible a la confianza |
| `anotacion/FORMULARIO_NECESIDADES.md` | 32 situaciones para que personas ajenas al diseño redacten consultas; `construir_consultas_independientes.py` las convierte en conjunto de evaluación |
| `../data/ontologia_suid/` | Ontología del dominio (13 clases, 20 relaciones) y metadatos por reporte |

## Reproducir

```bash
cd experimentos
python3 -m pip install -r requirements.txt
make test          # pruebas, sin modelo
make all           # escalera sobre el conjunto sintético (descarga jina-embeddings-v3 la primera vez)
make eval_real control dificil dificil_b fusion ontologia_completa errores barridos tablas
make v3 fusion_v3   # requiere los catálogos privados de la base operativa (ver abajo)
```

## Qué NO está publicado, a propósito

- Las ejecuciones y firmas del historial real de consultas (`data/athena_suid/`) y los scripts de extracción contra el almacén de datos:
  son datos de producción de la organización del caso de estudio. Por eso `construir_eval_real*.py`, `enriquecimiento_completo.py` y
  `preprocess_corpus.py` no corren desde este repositorio sin esos insumos; sus salidas (`datos/`, `corpus/`, `resultados/`) sí están.
- Las hojas de anotación generadas y su clave de *pooling* (se regeneran con `make anotacion`).
- Los catálogos exportados de la base operativa del módulo de competencias, la carpeta `pg/` (consultas y auditoría de datos
  personales) y los corpus y conjuntos derivados de ellos (`corpus_final`, `corpus_v3`, `consultas_*v3`, `qrels_*v3`):
  describen la configuración interna de la plataforma. Sus resultados agregados (`resultados/*v3*`, `fusion_v3.*`) sí están.
- La clave de respuestas del formulario de necesidades, para no contaminar la recolección de consultas independientes.
- Los PDF de los artículos citados y los resultados obsoletos anteriores a la auditoría del 2026-09-30.

## Versión del modelo

`config.yaml` fija el commit de `jinaai/jina-embeddings-v3` (`ab036b0…`) y carga el modelo sin conexión (`sin_conexion: true`),
de modo que el código remoto que usa (`jinaai/xlm-roberta-flash-implementation` @ `bd55a5e…`) sale siempre de la copia local.
La primera vez, con el modelo aún sin descargar, pon `sin_conexion: false`.

## Lectura honesta de los resultados

Los juicios son *silver* (el reporte ejecutado) o redactados por el autor; no hay anotación por expertos todavía. El nDCG absoluto
no es precisión de producción: lo válido es la comparación relativa entre configuraciones. Ver la sección «Amenazas a la validez» de la monografía.
