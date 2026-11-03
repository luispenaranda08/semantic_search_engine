# Código y reproducción

El código está en la carpeta
[`experimentos/`](https://github.com/luispenaranda08/semantic_search_engine/tree/v1.0-tesis/experimentos)
del repositorio. La etiqueta `v1.0-tesis` fija la versión que produce las cifras de la monografía.

## Reproducir los resultados

```bash
git clone https://github.com/luispenaranda08/semantic_search_engine.git
cd semantic_search_engine
git checkout v1.0-tesis
cd experimentos
python3 -m pip install -r requirements.txt
make test     # pruebas de métricas y estadística
make smoke    # tubería completa con un codificador offline, sin descargar modelos
make all      # corpus, consultas, escalera de ablación y reportes
```

`make all` encadena la construcción del corpus, la generación de consultas, la escalera de
ablación y los reportes. Otros objetivos reconstruyen partes concretas:

| Objetivo | Qué produce |
|---|---|
| `make eval_real`, `make control` | conjunto ampliado desde el historial y control sin nombre propio |
| `make dificil` | conjunto difícil de paráfrasis |
| `make barridos` | sensibilidad de hiperparámetros, Matryoshka y fragmentación |
| `make cobertura`, `make diagnostico` | cobertura de la ontología y diagnóstico del detector de entidades |
| `make tablas` | las tablas LaTeX de la monografía, generadas desde los archivos de resultados |
| `make anotacion` | hojas ciegas para la anotación por expertos |

Los parámetros están fijados en `config.yaml`: $k_1=1{,}5$, $b=0{,}75$, $k=60$ para RRF,
$\lambda=0{,}2$ para el realce, semilla $42$ y $1.000$ remuestreos *bootstrap*. Ninguno se ajustó
sobre los conjuntos de evaluación. La versión del codificador está fijada por commit
(`ab036b0` de `jinaai/jina-embeddings-v3`) y se carga sin conexión desde la copia local.

## Mapa del código

| Ruta | Contenido |
|---|---|
| `lib/metrics.py` | nDCG, MRR, Recall, P@k y AP, con pruebas propias |
| `lib/stats.py` | Wilcoxon pareada, permutación de signos, Holm y *bootstrap* |
| `lib/indexes.py` | BM25 implementado desde cero e índice denso por coseno exacto |
| `lib/retrievers.py` | las configuraciones de la escalera, RRF y el realce por entidad |
| `lib/encoders.py` | codificador enchufable: `jina-embeddings-v3` o un respaldo offline determinista |
| `construir_*.py` | construcción de los corpus y de los conjuntos de evaluación |
| `run_ablation.py` | la escalera de ablación con su estadística |
| `fusion.py`, `fusion_v3.py` | fusiones alternativas con el parámetro elegido sin fuga |
| `analisis_*.py` | robustez, errores, cobertura de la ontología y análisis del corpus v3 |
| `corpus/`, `datos/` | corpus de descripciones, consultas y *qrels* |
| `resultados/` | resultados de cada experimento, incluidos los del registro completo |
| `resultados/validacion_colab/` | protocolo, scripts, agregados y métricas por consulta de la validación con cobertura densa completa |
| `anotacion/` | procedimiento, hojas y cálculo de $\kappa$ para la anotación por expertos |

## Qué no se publica

El historial de consultas de la plataforma, la base operativa del módulo de competencias y las
fichas del registro completo contienen datos de personas, muchas de ellas menores de edad, y su
uso se autorizó solo con fines académicos. Por eso no están en el repositorio. Los scripts de
`athena/` y `pg/` documentan la extracción, pero solo se pueden ejecutar con el acceso autorizado
de la organización. Del registro completo se publican los agregados y las métricas por consulta.
Todo lo demás (corpus de descripciones, ontología, consultas sintéticas, *qrels* y resultados) se
reconstruye con el código.
