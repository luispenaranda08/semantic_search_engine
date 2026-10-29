# Experimentación: preprocesamiento y escalera de ablación

Framework reproducible para construir el corpus de la Versión 1 del buscador y evaluar
la escalera de ablación de cinco configuraciones, orientado a las seis preguntas de
investigación P1–P6.

## Reproducción con una sola orden

```bash
cd experimentos
python3 -m pip install -r requirements.txt   # numpy, scipy, scikit-learn, pyyaml, matplotlib
make all
```

`make all` encadena: `preprocess_corpus.py` → `generar_consultas.py` → `run_ablation.py`
→ `generar_reportes.py`. Toda la configuración vive en `config.yaml`. `make test` corre
los auto-tests de métricas y estadística; `make clean` borra los artefactos generados.

## Estructura

```
experimentos/
  config.yaml              # rutas e hiperparámetros (única fuente de verdad)
  preprocess_corpus.py     # PARTE 1: construye corpus/corpus_v1.jsonl (+ stats)
  generar_consultas.py     # PARTE 2: conjunto de evaluación estratificado + qrels
  run_ablation.py          # PARTE 2: corre las 5 configs, computa métricas + estadística
  generar_reportes.py      # PARTE 2: tablas, figura, recomendación, análisis de fallos
  lib/
    metrics.py             # nDCG, Recall, MRR, P@k, AP (con auto-test)
    stats.py               # Wilcoxon pareado, bootstrap
    encoders.py            # encoder denso enchufable (real / fallback LSA)
    indexes.py             # BM25 propio + índice denso por coseno
    retrievers.py          # las 5 configuraciones, RRF y realce por entidad
    reportes.py            # tablas (md/tex) y figura de la escalera
    error_analysis.py      # análisis de fallos en entidad exacta
  corpus/  datos/  resultados/   # artefactos generados
```

## Las cinco configuraciones y su relación con P1–P6

| # | Configuración | Aísla | Pregunta |
|---|---|---|---|
| 1 | Denso puro | línea base neuronal | P1, P2 (base) |
| 2 | Denso + ontología | inyección de metadatos en el denso | P3 |
| 3 | Híbrido BM25 + denso (sin ontología) | aporte de la señal léxica — **base crítica** | P1, P2 |
| 4 | Híbrido + ontología | inyección de metadatos en el híbrido | P3 |
| 5 | Híbrido + ontología + realce por entidad | realce suave por entidad (λ) | P5 |

Se reporta además BM25 solo como referencia léxica (P1). Los barridos de tamaño de
fragmento (P4) y de dimensión Matryoshka (P6) son ortogonales a la escalera.

## Encoder: fallback offline y modelo real

El codificador denso es enchufable (`config.yaml → encoder.tipo`):

- `lsa` (por defecto): TF-IDF + SVD truncado, offline y determinista. Permite correr el
  framework completo sin descargar modelos ni GPU. Es un recuperador denso legítimo pero
  débil; sirve para **validar la tubería**, no como resultado científico.
- `sentence-transformer`: el modelo real (`encoder.modelo_st`, p. ej.
  `jinaai/jina-embeddings-v3`). Descarga el modelo la primera vez y soporta truncación
  Matryoshka para el barrido de P6.

Para el experimento definitivo: `encoder.tipo: sentence-transformer` y `make all`.

> Nota de compatibilidad (Python 3.14): el código remoto de jina-v3 espera el atributo
> `all_tied_weights_keys` que `transformers` 5.x exige a toda subclase; `lib/encoders.py`
> aplica un shim no invasivo (un `dict` vacío, correcto en inferencia) antes de cargar el
> modelo, de modo que funciona con la pila actual sin fijar versiones antiguas de
> `tokenizers` (que no compilan en 3.14). Requiere además `einops`.

## Notebooks de benchmark

En `../notebooks/` hay dos notebooks **autocontenidos**: incluyen todo el código inline
(métricas, BM25, índice denso, encoder con shim, RRF, realce, las cinco configuraciones y
la estadística), no importan `lib/` y recomputan de punta a punta. Solo leen los datos ya
construidos (`corpus_v1.jsonl`, `consultas_eval.jsonl`, `qrels.jsonl`).

- `Benchmark_Escalera_Ablacion.ipynb`: corre la escalera completa en vivo con el encoder
  real; incluye la aclaración de *entrenamiento/prueba* (IR, modelo congelado, sin split),
  el protocolo *known-item* inline, tablas por estrato, figura con IC bootstrap, Wilcoxon
  (P1, P2, P3, P5), análisis de fallos e interpretación por pregunta. Reproduce
  exactamente las cifras de `make all`.
- `Benchmark_Matryoshka_P6.ipynb`: recomputa en vivo el barrido de dimensión
  (1024→768→512→256→128) truncando el embedding real (MRL) y mide efectividad vs. latencia
  vs. memoria del índice (P6).

Reejecutar ambos: `jupyter nbconvert --to notebook --execute --inplace ../notebooks/Benchmark_*.ipynb`.

### Entrega de análisis (notebooks 01–04)

Serie de notebooks de alta calidad (estilo del repo de referencia de Luis: secciones
numeradas + tríada Contexto/Descripción/Interpretación), cada uno autónomo con el núcleo de
recuperación inline:

- `01_Analisis_por_Estratos_y_Estadistica.ipynb`: tablas completas por estrato (nDCG@10,
  MRR@10, Recall@100, P@10 × 6 configs), heatmap y barras agrupadas, y Wilcoxon + Cliff's δ
  + IC bootstrap (Config 4 vs Config 3, énfasis en entidad_exacta). Puntos 1 y 3.
- `02_Diagnostico_Realce_Entidad.ipynb`: por qué Config 5 empeora. Detector de realce con
  **precision=0.13 / recall=0.94** (activa 7.5 docs/consulta → no discrimina); barrido de λ
  (todo λ>0 empeora); realce mejorado (V1 solo-clase, V2 ponderado) que no supera a "sin
  realce". Recomendación: **descartar el realce en v1**. Punto 2.
- `03_Matryoshka_y_Chunking_P4_P6.ipynb`: barrido de dimensión (P6: dim 256 retiene 1.000
  con −75% índice) y barrido de chunk/solapamiento (P4: nunca supera al documento completo;
  mantener 1 doc = 1 unidad en v1). Punto 4.
- `04_Resumen_Ejecutivo_y_Roadmap_v2.ipynb`: resumen ejecutivo, spec de consultas realistas,
  plan de corpus de competencias v2 y sección lista para el LaTeX. Puntos 5–7.

Reejecutar la serie: `jupyter nbconvert --to notebook --execute --inplace ../notebooks/0*_*.ipynb`.

### Escaleras de datos (validez externa y expansión de corpus)

Dos scripts reproducibles y sus notebooks amplían el alcance más allá de la v1 controlada:

- `construir_eval_real.py` → `datos/consultas_real.jsonl` + `qrels_real.jsonl` (silver) y
  `consultas_paper.jsonl` (anonimizado). **Escalera 1:** convierte las firmas reales del
  historial (`data/athena_suid/suid_query_signatures.csv`, mapeadas por el rollup) en un
  conjunto de evaluación con juicios silver (el reporte ejecutado = grado 2), muestreo
  estratificado y textos sintetizados desde los filtros reales. Notebook
  `../notebooks/05_Evaluacion_Validez_Externa.ipynb`.
- `construir_competencias.py` → `corpus/corpus_competencias.jsonl` (816 Pruebas Regionales =
  102 disciplinas × 8 regiones). **Escalera 2:** materializa la entidad Prueba Regional
  (disciplina × categoría × fase × región) desde `data/competencias_suid/`, en el esquema del
  corpus. Notebook `../notebooks/06_Expansion_Corpus_Competencias.ipynb`.
- `eval_flexible.py --corpus … --consultas … --qrels … --salida …`: corre la escalera sobre
  cualquier corpus/conjunto (sintético, real, o combinado con competencias).
- `construir_eval_real_ampliado.py` → `datos/consultas_real_ampliado.jsonl` (+ qrels y versión
  `_paper`). **Escalera 1 ampliada:** sube el poder estadístico usando el PATRÓN de firma
  distinto como unidad (evita pseudo-replicación). 129 consultas, **55 en entidad_exacta**
  (vs 17), 50 marcadas `gold_candidate`. Notebook
  `../notebooks/07_Poder_Estadistico_Eval_Ampliado.ipynb`, que reporta el escenario v1 (poder)
  y el escenario combinado a 833 docs (Recall@100 informativo). Hallazgos: P1 (híbrido>BM25 en
  entidad exacta) pasa a **significativo** (p≈0,01 vs 0,07 con n=17); el aporte marginal de la
  ontología sobre el híbrido (C4 vs C3) NO es significativo en la distribución real; a escala,
  C4 híbrido+ontología es el mejor y el denso puro se degrada.

Hallazgos: sobre el conjunto **real** el realce por entidad recupera valor en entidad exacta
(matiza P5); con el corpus **combinado** (833 docs) Recall@100 deja de ser trivial y el denso
puro pierde documentos (0,958) mientras el híbrido+ontología los retiene, y en Competencias la
ontología es el mayor aporte (P3). Nota de privacidad: nombres reales permitidos en uso
interno (gazetteer/eval), nunca en el paper; `consultas_paper.jsonl` es la vista segura.

## Protocolo de evaluación

- **Juicios de relevancia por documento conocido (known-item).** Cada consulta se genera
  apuntando a un reporte objetivo conocido, que recibe grado 2. Es un protocolo IR estándar
  y no fabrica juicios humanos. Los expertos pueden extender los juicios con grados 1 sobre
  reportes secundarios sin cambiar el formato.
- **Conjunto estratificado** (`datos/consultas_eval.jsonl`): entidad exacta / nombre propio,
  ambigua, documento largo y competencias, con cobertura fuerte de los Top-5 reportes.
- **Competencias fuera de la v1.** Sus consultas no tienen documento relevante en la v1 por
  diseño; se excluyen de las métricas de calidad y se reportan como vacío de cobertura, lo
  que mide directamente el hallazgo del dominio de competencias.
- **Métricas:** nDCG@10, Recall@100, MRR@10, Precisión@10, AP@100, con latencia p50/p95 y
  tamaño del índice. Prueba de Wilcoxon pareada en las comparaciones críticas del estrato de
  entidad exacta (config. 4 y 5 frente a 3) e intervalos por bootstrap.

## Cómo leer los resultados (advertencias honestas)

- Las cifras con `encoder: lsa-*` son de **validación de la tubería**, no resultados del
  buscador propuesto. El transformer real cambia el cuadro (el denso sube de forma marcada).
- **Recall@100 es trivialmente 1.0** en un corpus de 17 documentos (el top-100 los contiene
  a todos). Se vuelve discriminativo cuando el corpus crece; se deja para trazabilidad.
- **Precisión@10** ronda 0.1 porque el protocolo known-item tiene un relevante por consulta
  (máximo P@10 = 0.1). Es esperado.
- Los nombres propios usados en las consultas son **sintéticos**; no corresponden a ninguna
  persona real. El objetivo de la consulta es el reporte, no la persona.

## Privacidad

El corpus semántico no contiene ningún dato personal. `preprocess_corpus.py` corre una
auditoría anti-PII y aborta si encuentra algo. La resolución de un nombre propio a una
identidad concreta vive fuera de este framework, en un componente con control de acceso.

## Artefactos generados

- `corpus/corpus_v1.jsonl`, `corpus/corpus_stats.json`
- `datos/consultas_eval.jsonl`, `datos/qrels.jsonl`
- `resultados/resultados.json` (todas las métricas + estadística + eficiencia)
- `resultados/tabla_resultados.md`, `resultados/tabla_resultados.tex`
- `resultados/fig_escalera_ablacion.png`
- `resultados/recomendacion.md`, `resultados/error_analysis.md`

## Correcciones del 2026-09-30 (auditoría de benchmarks y EDA)

Todas las cifras anteriores a esta fecha quedan superadas; los JSON viejos están en
`resultados/obsoletos_pre_2026-09-30/`.

- **BM25** (`lib/indexes.py`): solo devuelve documentos con score > 0 (antes, en un empate a
  cero, el primer documento del corpus quedaba primero y entraba así a la fusión) y usa
  stemming Snowball ES (`snowballstemmer`, ver `requirements.txt`).
- **RRF** (`lib/retrievers.py`): un documento ausente de una lista no recibe aporte de ella.
- **jina-v3** (`lib/encoders.py`, `config.yaml`): tareas asimétricas `retrieval.query` /
  `retrieval.passage`. Poner ambas en `null` reproduce la codificación simétrica anterior.
- **Matryoshka**: el encoder rechaza dimensiones mayores que la nativa (antes se aceptaba 1536
  sobre un modelo de 1024).
- **Detector de entidades**: coincidencia por palabra completa; el heurístico de nombre propio
  ignora el vocabulario del dominio ("Caribe", "Región", "Única").
- **Estadística** (`lib/stats.py`): efecto pareado (rank-biserial), IC bootstrap pareado,
  número de pares no nulos y corrección de Holm sobre la familia C3-BM25, C3-C1, C2-C1, C4-C3, C5-C4.
- **Evaluación real** (`construir_eval_real*.py`, `lib/etiquetado.py`): las firmas se reetiquetan
  con la regla de promoción corregida, se excluyen los gemelos `COUNT(*)`, la deduplicación es
  global entre estratos, el objetivo se mapea por nombre de reporte (no por posición `ri_00N`) y
  cada consulta trae `texto_sin_nombre` para el control.
- **Ontología**: se quitó el nombre de ejemplo que aparecía literal en los metadatos (fuga).

Objetivos nuevos: `make eval_real` (127 consultas desde firmas), `make control` (mismas
consultas sin el nombre propio), `make extraer` (Athena, lo corre el autor) y `make final`
(corpus definitivo: competencias v2 + 17 reportes).


## Ampliaciones del 2026-10-05

| Objetivo `make` | Script | Qué hace |
|---|---|---|
| `dificil` | `construir_eval_dificil.py` | 52 paráfrasis con brecha de vocabulario; nivel A/B/C calculado por solape de raíces |
| `barridos` | `barridos.py` | Sensibilidad (k de RRF, λ, k1, b) + P6 (Matryoshka con equivalencia ε=0,01) + P4 (chunking), tareas LoRA activas |
| `cobertura` | `analisis_cobertura_ontologia.py` | Efecto de la ontología según el objetivo esté enriquecido (exploratorio) |
| `diagnostico` | `diagnostico_detector.py` | Precisión/recall del detector del realce |
| `tablas` | `generar_tablas_tex.py` | Tablas LaTeX de la monografía generadas desde los JSON |
| `anotacion` | `anotacion/` | Hojas de anotación ciega (pooling), instrucciones y κ de Cohen |

`lib/stats.py` incluye ahora la **prueba de permutación pareada** (exacta con ≤ 20 diferencias no nulas, Monte Carlo en otro caso) y marca
cada comparación como *robusta* si Wilcoxon y permutación rechazan tras Holm.

## Versión de la tesis y datos no publicados

La etiqueta `v1.0-tesis` del repositorio corresponde a la versión que produce las cifras de la
monografía. `resultados/validacion_colab/` contiene los agregados, las métricas por consulta, el
protocolo y los scripts de la validación con cobertura densa completa sobre el registro
(757.554 documentos, sección «Validación con cobertura densa completa» de la tesis).

No se publican el historial de consultas de la plataforma, la base operativa del módulo de
competencias ni las fichas del registro completo, porque contienen datos de personas, muchas de
ellas menores de edad, y su uso se autorizó solo con fines académicos. Por eso los scripts de
`athena/` y `pg/` documentan la extracción, pero no pueden ejecutarse sin el acceso autorizado de
la organización. Todo lo demás (corpus de descripciones, ontología, consultas sintéticas, qrels y
resultados) se reconstruye con `make all` y los objetivos descritos arriba.
