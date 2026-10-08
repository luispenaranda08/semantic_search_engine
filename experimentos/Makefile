# Reproducción completa del experimento con una sola orden: `make all`.
# Requiere Python 3.10+ y las dependencias de requirements.txt.

PY := python3

.PHONY: all corpus consultas ablation reportes eval_real control dificil dificil_b fusion ontologia_completa errores escalamiento barridos cobertura diagnostico tablas anotacion final extraer test smoke clean

all: reportes ## pipeline completo: corpus -> consultas -> ablación -> reportes

corpus: ## construye el corpus indexable v1
	$(PY) preprocess_corpus.py

consultas: corpus ## genera el conjunto de evaluación y los qrels
	$(PY) generar_consultas.py

ablation: consultas ## corre la escalera de ablación y computa métricas
	$(PY) run_ablation.py

reportes: ablation ## genera tablas, figura, recomendación y análisis de fallos
	$(PY) generar_reportes.py

eval_real: corpus ## eval real ampliado (129 consultas desde firmas) sobre los 17 reportes
	$(PY) construir_eval_real_ampliado.py
	$(PY) eval_flexible.py --corpus corpus/corpus_v1.jsonl \
	  --consultas datos/consultas_real_ampliado.jsonl --qrels datos/qrels_real_ampliado.jsonl \
	  --salida resultados/resultados_real_ampliado_v1.json

control: eval_real ## control: mismas consultas con el nombre propio borrado
	$(PY) eval_flexible.py --corpus corpus/corpus_v1.jsonl --campo-texto texto_sin_nombre \
	  --consultas datos/consultas_real_ampliado.jsonl --qrels datos/qrels_real_ampliado.jsonl \
	  --salida resultados/resultados_real_ampliado_v1_sin_nombre.json

dificil: corpus ## conjunto difícil (paráfrasis con brecha de vocabulario) + su evaluación
	$(PY) construir_eval_dificil.py
	$(PY) eval_flexible.py --corpus corpus/corpus_v1.jsonl \
	  --consultas datos/consultas_dificil.jsonl --qrels datos/qrels_dificil.jsonl \
	  --salida resultados/resultados_dificil_v1.json

dificil_b: dificil ## réplica del conjunto difícil (78 consultas nuevas) y unión A+B, con su evaluación
	$(PY) construir_eval_dificil_b.py
	$(PY) eval_flexible.py --corpus corpus/corpus_v1.jsonl \
	  --consultas datos/consultas_dificil_b.jsonl --qrels datos/qrels_dificil_b.jsonl \
	  --salida resultados/resultados_dificil_b_v1.json
	$(PY) eval_flexible.py --corpus corpus/corpus_v1.jsonl \
	  --consultas datos/consultas_dificil_ab.jsonl --qrels datos/qrels_dificil_ab.jsonl \
	  --salida resultados/resultados_dificil_ab_v1.json

fusion: dificil_b ## RRF frente a fusión convexa, RRF ponderado y con compuerta (selección leave-one-set-out)
	$(PY) fusion.py

ontologia_completa: dificil_b ## ontología en 14/17 reportes (derivada mecánicamente de las firmas) frente a 9/17
	$(PY) enriquecimiento_completo.py

errores: dificil_b ## acc@1 por reporte y confusiones más frecuentes
	$(PY) analisis_errores.py

escalamiento: ## latencia y memoria de la búsqueda exacta al crecer el corpus (vectores aleatorios)
	$(PY) escalamiento.py

barridos: eval_real ## sensibilidad (k, lambda, k1, b) + P6 (Matryoshka) + P4 (chunking) con tareas LoRA
	$(PY) barridos.py

cobertura: dificil eval_real ## análisis exploratorio: efecto de la ontología según el objetivo esté enriquecido
	$(PY) analisis_cobertura_ontologia.py

diagnostico: ## precisión/recall del detector de entidades (realce) en los tres conjuntos
	$(PY) diagnostico_detector.py

tablas: cobertura diagnostico ## tablas LaTeX de la monografía, generadas desde los JSON
	$(PY) generar_tablas_tex.py

anotacion: dificil ## hojas de anotación ciega para dos expertos (pooling) + auto-test del kappa
	$(PY) anotacion/preparar_anotacion.py
	$(PY) anotacion/calcular_kappa.py --autotest

extraer: ## extracción agregada de Athena (la corre el autor con su usuario de AWS)
	$(PY) athena/extraer_competencias.py

final: eval_real ## CORPUS DEFINITIVO: competencias v2 + 17 reportes (requiere `make extraer`)
	$(PY) construir_competencias_v2.py
	$(PY) eval_flexible.py --corpus corpus/corpus_final.jsonl \
	  --consultas datos/consultas_final.jsonl --qrels datos/qrels_final.jsonl \
	  --salida resultados/resultados_final.json

test: ## auto-tests de las métricas y la estadística
	$(PY) lib/metrics.py
	$(PY) lib/stats.py
	$(PY) anotacion/calcular_kappa.py --autotest
	$(PY) tests/test_nucleo.py

smoke: ## valida la tubería completa con el encoder offline (LSA) de config.yaml
	$(MAKE) all

clean: ## borra artefactos generados (no toca el código)
	rm -f corpus/corpus_v1.jsonl corpus/corpus_stats.json
	rm -f datos/consultas_eval.jsonl datos/qrels.jsonl
	rm -f resultados/*.json resultados/*.md resultados/*.tex resultados/*.png

help: ## lista los objetivos
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'
