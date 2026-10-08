# Guía de comprensión y sustentación — Buscador semántico híbrido para GovTech

> **Para qué sirve este documento.** Es la guía para *entender de verdad* qué se hizo, por qué, qué
> resultó y cuánto de eso se puede afirmar. Está escrita para que puedas responder a un jurado
> que pregunte "¿y por qué hiciste eso?" tres niveles hacia abajo.
>
> **Relación con `GUIA_ESTUDIO_BUSCADOR_SEMANTICO.md`.** Esa guía (1.515 líneas) es anterior a la
> auditoría del 30-sep-2026 y contiene cifras que hoy están invalidadas. Esta la **reemplaza como
> fuente de verdad numérica**. La otra sigue siendo útil para el guion de exposición, pero no
> cites sus cifras sin cruzarlas con la sección 14 de aquí.
>
> **Actualizado el 2026-10-06** con la réplica difícil B (78 consultas), fusión alternativa, ontología ampliada (14/17), análisis de errores,
> escalamiento y 19 pruebas unitarias (ver §14.12–14.16). Antes (2026-10-05): prueba de permutación, conjunto difícil, análisis de cobertura de la ontología,
> barridos de sensibilidad/P4/P6 con las tareas LoRA activas y hojas de anotación. Las secciones 14–18 están reescritas.
>
> **Regla de oro de este documento.** Cada cifra lleva una etiqueta de estado:
> 🟢 *vigente* (recomputada con el código corregido) · 🟡 *vigente pero pendiente de rehacer sobre el
> corpus definitivo* · 🔴 *obsoleta* (viene de una versión con bugs; no la uses).

---

## Índice

0. [Resumen de una página](#0-resumen-de-una-página)
1. [El problema y por qué es un problema de búsqueda](#1-el-problema-y-por-qué-es-un-problema-de-búsqueda)
2. [Conceptos base, desde cero](#2-conceptos-base-desde-cero)
3. [Los datos: de dónde sale todo](#3-los-datos-de-dónde-sale-todo)
4. [El EDA y lo que dijo (versión corregida)](#4-el-eda-y-lo-que-dijo-versión-corregida)
5. [La ontología](#5-la-ontología)
6. [El corpus y el preprocesamiento](#6-el-corpus-y-el-preprocesamiento)
7. [El recuperador, pieza por pieza](#7-el-recuperador-pieza-por-pieza)
8. [La escalera de ablación](#8-la-escalera-de-ablación)
9. [Cómo se evalúa: consultas, juicios y protocolo](#9-cómo-se-evalúa-consultas-juicios-y-protocolo)
10. [Las métricas con ejemplos numéricos](#10-las-métricas-con-ejemplos-numéricos)
11. [La estadística, explicada sin miedo](#11-la-estadística-explicada-sin-miedo)
12. [El framework de código, archivo por archivo](#12-el-framework-de-código-archivo-por-archivo)
13. [La auditoría del 30-sep: qué estaba mal y qué se arregló](#13-la-auditoría-del-30-sep-qué-estaba-mal-y-qué-se-arregló)
14. [Resultados vigentes, con su estado](#14-resultados-vigentes-con-su-estado)
15. [Las seis preguntas de investigación, respondidas con honestidad](#15-las-seis-preguntas-de-investigación-respondidas-con-honestidad)
16. [Hallazgos que debes poder explicar](#16-hallazgos-que-debes-poder-explicar)
17. [Limitaciones y amenazas a la validez](#17-limitaciones-y-amenazas-a-la-validez)
18. [Qué está desactualizado hoy y qué falta](#18-qué-está-desactualizado-hoy-y-qué-falta)
19. [Banco de preguntas del jurado, con respuesta](#19-banco-de-preguntas-del-jurado-con-respuesta)
20. [Chuleta final y glosario](#20-chuleta-final-y-glosario)

---

## 0. Resumen de una página

**Qué es el proyecto.** Un trabajo de grado (Ciencia de Datos, Universidad del Norte) que estudia
cómo diseñar un **buscador semántico en español** para una plataforma de software GovTech
(gestión deportiva del sector público). No se entrena un modelo: se **evalúa y caracteriza** una
combinación de piezas preentrenadas.

**Qué se construyó.**
1. Un **EDA** del historial real de consultas (qué reportes pide la gente).
2. Una **ontología** del dominio (13 clases, 20 relaciones).
3. Un **corpus** de documentos (17 reportes descritos en lenguaje natural + enriquecidos con la ontología).
4. Un **recuperador híbrido**: BM25 (léxico) + `jina-embeddings-v3` (denso, con Matryoshka), fusionados con RRF.
5. Una **escalera de ablación** de 5 configuraciones para aislar qué aporta cada pieza.
6. Un **framework reproducible** (`make all`) con métricas, estadística y varios conjuntos de evaluación.

**Qué se encontró (honesto).**
- El **híbrido supera a BM25 solo** de forma robusta (Holm + permutación) en los **tres** conjuntos y en toda la rejilla de k1×b. 🟢
- Su ventaja sobre el **denso puro no se demuestra** (+0,026, +0,011, −0,026, −0,005 en B): el signo depende del conjunto. La idea de que «el híbrido lastra al denso» **no se confirmó en la réplica**. Ninguna fusión alternativa (convexa, RRF ponderado, compuerta) supera a RRF de forma robusta. 🟢
- La **ontología** ayuda donde la consulta se aparta del vocabulario del documento (+0,122 sobre el denso en el conjunto difícil, robusto) y no donde lo comparte (ampliado: nulo). Además solo cubre 9 de 17 reportes y **perjudica a los no enriquecidos** (−0,161, exploratorio). 🟢
- El **realce por entidad nunca mejora** (−0,024, −0,016, −0,049, −0,063 en B; robusto en los dos difíciles) y ningún λ lo salva; el detector apenas supera al azar. Se descarta. 🟢
- **Matryoshka**: 256 dimensiones es equivalente a 1024 en el ampliado con −75 % de índice; la latencia no cambia (la domina codificar la consulta, 349 ms). 🟢
- **Chunking** no aporta con documentos de 64–184 palabras. 🟢
- El **estrato «entidad exacta» no mide lo que dice medir**: al borrar el nombre propio el desempeño *sube*. Mide el *tema* del reporte, así que **P2 no es contrastable** con este corpus. 🟢 Es el hallazgo más importante y el más fácil de malinterpretar.

**Qué falta.** Extraer de Athena el corpus de competencias (lo hace Luis), correr `make final`, anotar con expertos y
rehacer los notebooks 01–07. El `.tex` ya está actualizado con las cifras de este documento. Ver sección 18.

---

## 1. El problema y por qué es un problema de búsqueda

### 1.1 El contexto

Una plataforma de gestión deportiva del sector público (eventos, deportistas, instituciones, grupos,
fases de competencia) expone su información a través de **reportes**. Los usuarios operativos necesitan
encontrar *el reporte correcto* para su pregunta de negocio: "¿en qué etapa va tal deportista?",
"¿qué documentación le falta a tal institución?".

### 1.2 Por qué no basta con un menú

- Hay 17 reportes ya identificados y muchos más conceptos (competencias, pruebas regionales) que **ningún reporte expone**.
- Las preguntas de negocio reales se arman **componiendo conceptos** (disciplina + categoría + región + fase). Una frase como *"Atletismo Pre-Juvenil en Región Caribe 1"* no es un campo de ninguna tabla.
- Las consultas mezclan **nombres propios** (personas, instituciones), **códigos** y **lenguaje natural**.

### 1.3 Por qué la búsqueda léxica sola falla y la densa sola también

| Enfoque | Fortaleza | Debilidad |
|---|---|---|
| **Léxico (BM25)** | Exacto con códigos, siglas, nombres | Desajuste de vocabulario: "jugador" ≠ "deportista" |
| **Denso (embeddings)** | Entiende significado y sinónimos | Se difumina con nombres propios y códigos raros |
| **Híbrido** | Combina las dos señales | Hay que fusionarlas sin entrenar |

Esa es la intuición central. El proyecto la pone a prueba **empíricamente** en un escenario que la
literatura no cubre: español, dominio específico, entidades exactas, poca anotación.

### 1.4 La brecha de investigación (en una frase defendible)

> "Los 12 trabajos revisados evalúan en inglés, sobre corpus abiertos y con anotación abundante.
> Nadie midió cómo se comportan juntas léxica, densa, fusión y metadatos de ontología en un corpus
> GovTech en español con vocabulario normativo y casi sin etiquetas."

Y el argumento de por qué la brecha es *empírica* y no se resuelve leyendo papers: BEIR (Thakur et al.,
2021) mostró que el desempeño dentro del dominio de entrenamiento **no predice** el desempeño fuera de él.

---

## 2. Conceptos base, desde cero

Si algún concepto de esta sección no lo puedes explicar con tus palabras, repásalo antes de seguir.

### 2.1 Recuperación de información (IR)

Dada una **consulta** `q` y una colección de **documentos** `D`, devolver los documentos ordenados de
más a menos relevantes. No es clasificación: lo que importa es el **orden**.

> **Aclaración que te preguntarán:** esto *no es aprendizaje supervisado*. No hay train/test. El
> modelo denso está congelado (solo inferencia), BM25 no se entrena, el corpus es el índice y las
> consultas son el conjunto de evaluación. Los hiperparámetros (k1, b, k, λ) son valores estándar de la
> literatura, no ajustados sobre este conjunto.

### 2.2 Tokenización, stopwords, stemming

- **Tokenizar:** partir el texto en unidades (palabras).
- **Stopwords:** palabras vacías ("de", "la", "que") que se descartan.
- **Stemming:** reducir una palabra a su raíz ("deportistas" → "deportist"). Se usa **Snowball español**.

En el código (`lib/indexes.py`, `tokenizar_es`): minúsculas → quitar tildes (NFKD) → regex alfanumérica
→ quitar stopwords y tokens de 1 carácter → stemming. Por eso "Promoción" y "promocion" son el mismo término.

### 2.3 BM25 (la señal léxica)

Puntúa un documento por cuántos términos de la consulta contiene, ponderando:

- **TF** (frecuencia del término en el documento), con **saturación** (la 10ª aparición vale menos que la 2ª).
- **IDF** (rareza del término en el corpus): un término raro pesa más.
- **Normalización por longitud:** un documento largo no gana solo por ser largo.

Fórmula (la misma de la monografía, Ec. 4.2):

```
s_BM25(q,d) = Σ_{t∈q}  IDF(t) · f(t,d)·(k1+1) / ( f(t,d) + k1·(1 − b + b·|d|/avg|d|) )
IDF(t)      = ln( 1 + (N − df + 0,5) / (df + 0,5) )
```

Parámetros usados: **k1 = 1,5** (saturación) y **b = 0,75** (peso de la longitud). Son los valores por
defecto de la literatura.

**Detalle de implementación que importa (fue un bug corregido):** `BM25Index.buscar` devuelve **solo**
documentos con score > 0. Antes devolvía todos; los de score 0 quedaban en el orden de indexación y
ese orden arbitrario entraba a la fusión RRF favoreciendo siempre al primer documento. Ver sección 13.

### 2.4 Embeddings y búsqueda densa

Un **encoder** (red neuronal) convierte un texto en un vector de, p. ej., 1.024 números. Textos de
significado parecido quedan cerca. Se mide la cercanía con el **producto interno** de vectores
normalizados (= **coseno**).

- Es un **bi-encoder**: consulta y documento se codifican por separado; los vectores de documento se
  precomputan.
- Modelo usado: **`jinaai/jina-embeddings-v3`** (multilingüe, 1.024 dim, ventana larga, Matryoshka nativo).
- **Tareas asimétricas (corregido el 30-sep):** jina-v3 tiene adaptadores LoRA distintos para consulta
  (`retrieval.query`) y documento (`retrieval.passage`). Sin pasar la tarea, el modelo codifica ambos
  lados igual y **no activa el adaptador de recuperación**. Hoy `config.yaml` las fija.

### 2.5 Matryoshka (MRL)

Representación entrenada para que **las primeras m dimensiones ya sean un buen embedding**. Puedes
truncar de 1.024 a 256 y renormalizar sin reentrenar. Es una perilla de despliegue: memoria vs calidad.
`lib/encoders.py` valida que `m ≤ dimensión nativa` (antes aceptaba 1.536, que es imposible en jina-v3).

### 2.6 Fusión híbrida: RRF

**Reciprocal Rank Fusion** combina dos rankings usando solo las **posiciones**, no los scores:

```
s_RRF(d) = Σ_{listas que contienen d}  1 / (k + rank_lista(d)),   k = 60
```

Ventajas: no hay que calibrar escalas (BM25 da 7,3; coseno da 0,41), y **no requiere entrenamiento**.
Esto es lo que lo hace apto para un régimen de baja anotación (la Proposición 4.1 de la monografía).

**Ejemplo numérico (k=60):**

| Doc | Rank BM25 | Rank denso | RRF |
|---|---|---|---|
| A | 1 | 1 | 1/61 + 1/61 = 0,03279 |
| B | 1 | 3 | 1/61 + 1/63 = 0,03226 |
| C | 2 | 2 | 1/62 + 1/62 = 0,03226 |
| D | — (ausente) | 1 | 1/61 = 0,01639 |

Observa: B y C **empatan**. RRF no distingue "uno muy bien y otro regular" de "ambos bien". El
desempate es por `doc_id` (determinista; antes dependía del hash de Python y la métrica variaba entre
corridas). Y D, ausente de BM25, solo recibe aporte de una lista.

### 2.7 Realce suave por entidad (config 5)

`s_final = s_RRF · (1 + λ · 1_entidad)`, con λ = 0,2. La indicadora vale 1 si la consulta menciona una
clase de entidad que el documento cubre, o si hay un nombre propio y el documento es "buscable por
nombre propio". Es "suave" porque multiplica por poco. **Lo descartamos** (sección 16.3).

### 2.8 Ontología como puente

Una ontología es un modelo explícito de las entidades del dominio y sus relaciones. Aquí se usa para
**enriquecer el texto del documento** (no para razonar). Idea tomada de ECLASS (Baumgart et al., 2026):
metadatos estructurados como puente semántico, inyectados **de forma selectiva**.

---

## 3. Los datos: de dónde sale todo

### 3.1 Mapa de carpetas

```
Buscador Semántico/
├── data/
│   ├── athena_suid/           EDA: firmas de consultas, tabla maestra, descripciones, figuras
│   ├── ontologia_suid/        ontología YAML, catálogo, metadatos por reporte, diagramas
│   ├── competencias_suid/     mapeo del dominio Competencias (JSON, catálogos)
│   ├── corpus_v1/             corpus del preprocesamiento original + auditoría PII
│   └── usuarios_escenarios_suid/
├── preprocesamiento/          construir_corpus.py (versión original)
├── experimentos/              EL FRAMEWORK (make all)
├── notebooks/                 EDA, ontología, 01–07, benchmarks
├── monografia_buscador_semantico_PRIME.tex   ← documento principal
├── estado_del_arte_*.tex      ← revisión de literatura (3 variantes)
├── referencias.bib
├── entrega_asesor/            copia para el asesor
└── Artículos - Estado del Arte/   12 PDFs
```

### 3.2 Las fuentes de datos reales

- **`suid_executions_redacted.jsonl`**: ejecuciones SQL del historial de Athena (consultas ya redactadas;
  sin literales personales).
- **`suid_query_signatures.csv`**: **714 firmas únicas** de consulta. Una *firma* es la estructura de la
  consulta (tablas, columnas, palabras clave del WHERE), no sus valores. Esto es lo que da validez externa
  sin tocar PII.
- **`suid_logical_reports_rollup.csv`**: mapea cada firma a uno de los **17 reportes lógicos**.
- **`tabla_maestra_reportes.csv`**: demanda (`cdr` = consultas de datos reales), MB procesados, prioridad.
- **`descripciones_semanticas.csv`**: el texto en lenguaje natural de cada reporte (el que se indexa).

### 3.3 Privacidad: la decisión de diseño más importante

- Las firmas traen **nombres de columna, no valores** → sin PII en la fuente.
- Los **nombres propios en las consultas de evaluación son sintéticos** ("Andrés Torres", "María Restrepo",
  "Colegio San Marcos"…). No corresponden a nadie real.
- El **índice semántico nunca contiene datos personales.** La resolución de "este nombre ↔ esta persona"
  vive en un **gazetteer** aparte con control de acceso (solo existe su `gazetteer_SCHEMA.json`).
- Evidencia real: en `bronze_suid_events.result_entries`, `participant_name` y `group_name` son `VARBINARY`
  de 25 bytes fijos → muy probablemente **cifrados a nivel de columna**. Confirma que el diseño
  "índice sin PII + gazetteer separado" coincide con la realidad de la plataforma.
- Una **auditoría anti-PII** (regex de email y teléfonos de 7+ dígitos) corre antes de escribir el corpus
  y aborta si encuentra algo (`auditar_pii` en `preprocess_corpus.py`).
- Regla de redacción: en el documento final **no se menciona la organización por nombre** ("la organización",
  "el caso de estudio"). Los nombres técnicos internos se mencionan una sola vez.

---

## 4. El EDA y lo que dijo (versión corregida)

### 4.1 Qué se hizo

Se analizó el historial de ejecuciones de reportes durante **6,5 semanas**. La pregunta: *¿qué reportes
se piden realmente y con qué concentración?* Eso da el argumento cuantitativo de qué indexar primero.

### 4.2 La unidad de análisis: "consulta de datos real" (CDR)

La plataforma ejecuta **dos instrucciones por página**: una que trae datos y otra que cuenta
(`SELECT COUNT(*)`, para paginar). Contar ambas infla la demanda. Se descartan los *gemelos COUNT*
(`es_wrapper_count`), y también los `SELECT DISTINCT` que solo alimentan filtros de la UI.

### 4.3 Cifras corregidas 🟢 (EDA reejecutado el 30-sep)

| Medida | Valor **vigente** | Valor **viejo (🔴)** |
|---|---|---|
| Demanda real total | **6.620** CDR (45 % del total bruto) | 9.051 |
| Gemelos COUNT | 38,5 % | "~50 %" |
| SELECT DISTINCT de filtros | 16,5 % | 26,8 % (otra definición) |
| Reporte #1 | **Reporte Individual de Deportistas, 40,4 %** | Promoción, 47,5 % |
| Top-5 | **83 %** (83,4 % en `corpus_stats.json`) | 86 % |
| Gini | **0,70** (IC 0,65–0,75 por bootstrap por día; con la corrección n/(n−1) vale 0,74) | 0,74 sin IC |
| Promoción | **275 consultas = 4,2 %** (#7, prioridad Media) | 47,5 % |

### 4.4 Por qué "Promoción 47,5 %" era un artefacto (explicación para el jurado)

El clasificador original marcaba una consulta como "Promoción" si tocaba el Reporte Individual y contenía
palabras como `category` o `stage`. Pero esos son **nombres de columnas del propio reporte individual**
(`category_name`, `sport_development_stage`, `current_stage`). Resultado: el listado completo de
deportistas se contaba como promoción.

**Regla corregida** (`lib/etiquetado.py`, función `es_promocion`): hay promoción solo si la consulta
usa `promotions_log` o `phases`, o calcula/filtra un estado de promoción (regex `promo(cion|tion|vi|ted)|estado_log`).
Solo 416 ejecuciones tocan `promotions_log`.

> **Lección que puedes decir en voz alta:** "El EDA original tenía un sesgo de clasificación. Lo detecté,
> lo medí y lo corregí; la conclusión cualitativa (demanda muy concentrada) se mantiene, pero el reporte
> líder cambió y la cifra bajó de 47,5 % a 4,2 % para promoción".

### 4.5 El hallazgo de Competencias

- Del historial, **ninguna** consulta toca `events`, `result_entries`, `result_configs`, `venues`.
  (Corrección: sí hay consultas a `groups` — 5.717 — y `participants` — 6.080. La frase "cero consultas a
  competencias" es **falsa en bruto** y verdadera solo para esas cuatro tablas.)
- Volumen real: 47.635 resultados, 732.640 participante-disciplina, 674.186 participaciones, 42.485 grupos.
- `gold_suid` tiene 20 tablas y **ninguna** de eventos/competencias; `silver_suid_events` está vacía.
- **Lectura correcta:** el cero no es "nadie lo necesita", es **"nadie puede pedirlo porque no existe la puerta"**.
  Es un *vacío de cobertura*, el mismo patrón que Promoción (se arma con JOIN al vuelo) llevado al extremo.

### 4.6 Por qué hubo un pivote a Competencias

El 16-sep el asesor/comité señaló que el EDA de reportes **no mostraba necesidad** de buscador semántico:
los reportes ya los resuelve un dashboard estructurado. Competencias es más interesante porque
(a) es la entidad sintética *Prueba Regional* (disciplina × categoría × fase × región), y (b) no tiene punto de entrada.

### 4.7 Limitación del EDA que debes conocer

La **muestra de validación de 296 casos nunca se etiquetó** (`muestra_validacion_clasificacion.csv`).
El EDA tiene un plan de validación, pero no una precisión medida del clasificador.

---

## 5. La ontología

### 5.1 Qué es y qué contiene

`data/ontologia_suid/ontologia_suid.yaml`: **13 clases, 20 relaciones** (después de la extensión a
Competencias; antes eran 11 y 15).

Clases: Deportista, Disciplina Deportiva, Documento, Etapa/Fase, Evento, Grupo, Institución,
Participación/Delegación, Personal de Apoyo, Promoción, Ubicación Geográfica, **Región (deportiva)**,
**Competencia / Prueba Regional** (esta última es `entidad_sintetica`, con fórmula
`{sport_name} {category_name} en Región {region_name} ({fase})`).

Cada clase tiene:
- **sinónimos** (Deportista → atleta, jugador, competidor, participante deportivo),
- **propiedades_de_datos**, cada una con `tipo_busqueda`: `atributo_filtrable` o
  **`entidad_exacta_nombre_propio`** (solo `full_name`, `institution_name`, `legal_name`).

Y **`metadatos_por_reporte.json`**: para cada reporte, `entidades_principales`, `relaciones_clave`,
`conceptos_de_negocio`, `atributos_filtrables`, `sinonimos`, y la bandera `tiene_busqueda_por_nombre_propio`.

### 5.2 Cómo se usa en el sistema

1. **Enriquecimiento del documento** (config 2, 4, 5): `d' = d_desc ⊕ φ(o_d)`.
2. **Detector de entidades** para el realce (config 5).
3. **Sinónimos** para atacar el desajuste de vocabulario del lado del contenido.

### 5.3 Inyección selectiva (lección de ECLASS)

`serializar_metadatos` inyecta **solo tres bloques**, no el esquema completo:

```
"Entidades: Deportista, Grupo, ..."
"Responde a: Buscar por el nombre de un deportista; ..."
"También llamado: atleta, jugador, ...."   (máx. 20 sinónimos)
```

Los `atributos_filtrables` y las `relaciones` están en el JSON del documento pero **no** en el texto
indexable. Es deliberado: ECLASS reportó que inyectar todo rinde peor que inyectar lo seleccionado.

### 5.4 Qué NO es la ontología

No hay razonador, no hay SPARQL, no hay grafo consultado en tiempo real. Es un **vocabulario controlado
que alimenta el texto indexado**. Si el jurado dice "eso no es una ontología formal", la respuesta
honesta es: es un modelo conceptual ligero (OWL-lite en espíritu) usado como fuente de metadatos;
el aporte es *cómo se inyecta y qué efecto mide*, no la formalización lógica.

---

## 6. El corpus y el preprocesamiento

### 6.1 Corpus v1 (el que produjo los resultados de las tablas)

17 documentos, uno por reporte. `experimentos/preprocess_corpus.py` → `corpus/corpus_v1.jsonl`.

| Campo | Contenido |
|---|---|
| `id` | `ri_00N_<slug-del-título>` |
| `titulo` | Nombre en lenguaje natural |
| `descripcion` | Texto base (`d_desc`) |
| `metadatos_ontologia` | entidades, relaciones, conceptos, atributos, sinónimos |
| `texto_indexable` | `descripcion` + bloque de ontología (`d'`) |
| `prioridad`, `cdr`, `fuentes` | Demanda y procedencia |
| `nombre_propio_buscable` | Bandera para el realce |

Estadísticas 🟢: 17 docs, 1.756 tokens, 103,3 tokens promedio, prioridades 5 Alta / 4 Media / 8 Baja,
7 docs con nombre propio, **PII = 0**.

> **Dos hechos del corpus que debes conocer (y que te preguntarán):**
> 1. **Solo 9 de los 17 documentos tienen bloque de ontología.** Los otros 8 (ri_010 a ri_017) cumplen d' = d_desc: para ellos
>    C2 = C1 y C4 = C3 *en su propio texto*. Pero sus competidores sí están enriquecidos (ver §16.6: asimetría).
> 2. **Las descripciones son plantillas**: "El Reporte X es uno de los reportes del sistema... Se construye combinando
>    información de A, B, C... En el periodo analizado se solicitó N veces...". El contenido semántico real es el título y las
>    fuentes. Eso explica por qué las consultas que repiten el título ya caen en la posición 1 (techo) y por qué la ontología
>    pesa tanto cuando la consulta es una paráfrasis.

**Dos textos por documento** es la clave del diseño de la ablación: las configs 1 y 3 indexan
`descripcion`; las 2, 4 y 5 indexan `texto_indexable`. Así la *única* diferencia entre C1↔C2 y C3↔C4 es la ontología.

### 6.2 Un detalle de IDs que da problemas

El `id` lleva un prefijo `ri_00N` que depende del **orden por demanda**. Cuando el EDA se corrigió, el
orden cambió (Individual pasó a ri_001). Por eso `lib/etiquetado.py` mapea por **slug** del título
(`SLUG_POR_CLAVE`), no por posición. Si ves `ri_007_reporte_de_promocion_de_deportistas`: Promoción es #7.

### 6.3 Corpus definitivo (decisión del 30-sep) 🟡 pendiente de materializar

El usuario decidió: **núcleo en competencias + 17 reportes como segundo dominio.**

- Núcleo: **Prueba Regional × evento** (deporte × categoría × región × evento), **solo combinaciones que existen**
  (≥ 1 grupo), con **conteos propios** por prueba.
- Reemplaza el "producto cartesiano de 816 documentos" (102 disciplinas × 8 regiones), que tenía
  **plantillas casi duplicadas (Jaccard 0,87–0,90)** → inflaba artificialmente la dificultad y la
  redundancia, y la mayoría de esas combinaciones **ni existen** en los datos.
- Scripts: `athena/extraer_competencias.py` (agregados, auditoría PII; **lo corre el usuario con su AWS**)
  → `data/competencias_suid/extraccion_v2/` → `construir_competencias_v2.py` → `corpus_final.jsonl`,
  consultas y qrels "por facetas".
- Estado: la carpeta `extraccion_v2/` **todavía no existe**.

### 6.4 `preprocesamiento/construir_corpus.py` vs `experimentos/preprocess_corpus.py`

Dos pipelines. El de `preprocesamiento/` es el original (esquema con `texto_display / texto_denso /
texto_lexico / boost_entidades`, 18 docs con una competencia). El de `experimentos/` es el que alimenta
la ablación (esquema `descripcion / texto_indexable / metadatos_ontologia`). **El segundo supersede al primero.**

---

## 7. El recuperador, pieza por pieza

Sigue el flujo de `lib/retrievers.py::MotorRecuperacion`.

### 7.1 Construcción de índices (una vez)

```
desc  = [d.descripcion for d in docs]
onto  = [d.texto_indexable for d in docs]

bm25_desc  = BM25(desc)       dense_desc  = Dense(desc)
bm25_onto  = BM25(onto)       dense_onto  = Dense(onto)
```

Cuatro índices. Cada config usa un subconjunto.

### 7.2 Respuesta de cada configuración

| Config | Qué hace | Código |
|---|---|---|
| BM25 | ranking léxico sobre `desc` (referencia, no es peldaño) | `_bm25_desc.buscar` |
| C1 | denso sobre `desc` | `_dense_desc.buscar` |
| C2 | denso sobre `onto` | `_dense_onto.buscar` |
| C3 | RRF(BM25 desc, denso desc) | `rrf(...)` |
| C4 | RRF(BM25 onto, denso onto) | `rrf(...)` |
| C5 | C4 × (1 + λ·1_entidad) | `final = {d: s·(1+λ·ind)}` |

### 7.3 El detector de entidades (la causa de que C5 falle)

`DetectorEntidades`:
- `clases_en(consulta)`: busca, por **palabra completa** (regex `\bt(?:e?s)?\b`), el nombre o los sinónimos
  de cada clase de la ontología, sobre texto sin tildes.
- `tiene_nombre_propio(consulta)`: heurística de palabra capitalizada que (a) no abre la consulta y (b) no
  pertenece al vocabulario del dominio (títulos del corpus + términos de la ontología).

`_indicador_entidad(consulta, doc)` = 1 si `clases_q ∩ entidades_doc ≠ ∅` **o** (hay nombre propio **y** el doc
es `nombre_propio_buscable`).

**Por qué falla:** casi todos los reportes cubren las mismas clases (Deportista, Grupo, Institución…),
así que la intersección es no vacía para muchos documentos → el factor `(1+λ)` se aplica a un grupo
entero y no reordena a favor del correcto. Diagnóstico (versión pre-auditoría, 🟡): precisión 0,13,
recall 0,94, activa ~7,5 de 17 documentos por consulta.

### 7.4 Latencia y por qué p50 ≈ 343 ms

La latencia está dominada por **codificar la consulta con el transformer** (en MPS/CPU), no por el
producto matriz-vector. BM25 es < 1 ms. Con 17 documentos, el índice denso es de 17×1024×4 bytes ≈ 68 KiB.
Un índice ANN (HNSW) sería innecesario a esta escala; se usa coseno exacto.

> Nota: la monografía reporta ~22 ms en la tabla vieja y la tabla nueva 343 ms. Son corridas distintas
> (dispositivo, carga del modelo, tareas LoRA). La latencia es un reloj, no una métrica reproducible
> bit a bit; es lo único que varía entre corridas con la misma semilla.

---

## 8. La escalera de ablación

### 8.1 La idea

Una **ablación** enciende un mecanismo a la vez. Comparar dos peldaños consecutivos mide *el aporte del
mecanismo que los separa y nada más*.

```
                        ┌───────────────────────────┐
  BM25 (referencia)     │  solo señal léxica        │
                        └───────────────────────────┘
  C1 Denso puro         ──► punto de partida neuronal
        │  + ontología (φ)
        ▼
  C2 Denso + ontología  ──► P3 (denso)
  
  C3 Híbrido sin onto   ──► LÍNEA BASE CRÍTICA (P1, P2)
        │  + ontología (φ)
        ▼
  C4 Híbrido + onto     ──► P3 (híbrido)
        │  + realce λ
        ▼
  C5 Híbrido+onto+realce ──► P5
```

### 8.2 Por qué C3 es la "línea base crítica"

Si el híbrido solo se compara con BM25 o con denso, no sabes cuánto aporta *la fusión*. C3 es el sistema
más fuerte **sin** nuestras contribuciones propias (ontología, realce). Todo lo que añadimos debe
justificarse frente a C3.

### 8.3 Qué comparación responde cada pregunta

| Pregunta | Comparación | Métrica |
|---|---|---|
| P1 | C3 vs BM25 · C3 vs C1 | Δ nDCG@10, Wilcoxon |
| P2 | C3 vs C1 **por estrato** | interacción sistema × tipo |
| P3 | C2 vs C1 (denso) · C4 vs C3 (híbrido) | Δ nDCG@10 |
| P4 | barrido chunk × solapamiento (sobre C4) | nDCG@10, Recall@100 |
| P5 | C5 vs C4 | Δ nDCG@10, diagnóstico del detector |
| P6 | barrido m ∈ {64…1024} + latencia/memoria | efectividad vs costo |

### 8.4 Por qué no hay re-ranking

El usuario fijó la escalera de **5 configs sin re-ranking** (un cross-encoder como `bge-reranker-v2-m3`
queda como trabajo futuro). Al quitarlo, P5 pasó de "re-ranking" a "realce suave" para mantener 6 preguntas
coherentes con 5 configuraciones.

---

## 9. Cómo se evalúa: consultas, juicios y protocolo

Hay **cuatro conjuntos de evaluación**. Es fundamental distinguirlos.

### 9.1 Conjunto sintético (`generar_consultas.py`) — 51 consultas

- Protocolo **known-item**: cada consulta apunta a un reporte objetivo (**grado 2**), a veces con reportes
  secundarios (grado 1).
- Estratos: entidad_exacta **17** (33 %), ambigua **13**, documento_largo **10**, competencias **11**.
- Las 11 de competencias tienen **qrel vacío** (el corpus v1 no las cubre) → se excluyen de las métricas
  y miden el vacío de cobertura. Quedan **40 consultas con gold**.
- Nombres propios **sintéticos** (4 personas, 3 instituciones).
- **Defecto reconocido:** las consultas están escritas a mano, derivadas de los propios documentos y la
  ontología → comparten vocabulario con ellos → el valor absoluto está inflado.

Ejemplos: `"estado de promoción de Andrés Torres"` (entidad_exacta) · `"grupos"` (ambigua) ·
`"quiero ver en qué etapa está cada deportista y si ya cumplió los requisitos..."` (documento_largo).

### 9.2 Escalera 1 — evaluación "real" con juicios *silver* (`construir_eval_real.py`)

- Fuente: las **714 firmas reales**. Cada firma ya está mapeada a un reporte → ese reporte = grado 2.
- Texto de la consulta **sintetizado** desde los filtros reales (`COL_A_FRASE`: `current_stage` → "por etapa").
- *Silver* significa: el juicio viene de un proceso automático (el reporte que de hecho se ejecutó), no de
  un experto humano. Es mejor que inventar, peor que gold.
- Versión 1 de este conjunto: 71 consultas; **tenía un defecto de pseudo-replicación** (ver abajo).

### 9.3 Escalera 1 ampliada (`construir_eval_real_ampliado.py`) — **127 consultas** 🟢

**El problema que resuelve — pseudo-replicación.** Si tomas un mismo patrón de filtro y le pones 5 nombres
sintéticos distintos, obtienes 5 consultas casi idénticas (el nombre no está en ningún documento). Eso
**infla n sin añadir información**, y vuelve engañosos los p-valores.

**La solución:** la unidad de muestreo es el **patrón de firma distinto** = (reporte × combinación de
filtros). Más una **deduplicación global** por texto.

- Cupos pedidos: entidad_exacta 55, operacional 35, documento_largo 25, ambigua 20 (suman 135). Quedan **127**:
  ambigua llega solo a 12, porque tras la deduplicación global no hay más textos distintos que cumplan
  la regla (≤ 1 filtro). Verifícalo con `patrones_disponibles` que imprime el script si te lo preguntan.
- `TOPE_POR_REPORTE = 18` en entidad_exacta para que no todo sea de un solo reporte. Aun así, el objetivo
  más frecuente es Individual (30 consultas) y Documentación (24).
- 50 marcadas `gold_candidate` (candidatas a que un experto las juzgue después).
- Clasificación de estrato (`clasificar`): si el combo usa columnas de nombre propio → entidad_exacta; ≤1
  filtro → ambigua; ≥5 → documento_largo; otro → operacional.

### 9.4 El **control sin nombre** 🟢 (el experimento más revelador)

Cada consulta guarda `texto_sin_nombre`: la misma consulta con el nombre propio borrado. Se corre toda la
escalera de nuevo. **Si el nombre propio importara, el desempeño caería. Subió.**

| Estrato entidad_exacta (n=55) | Con nombre | Sin nombre |
|---|---|---|
| C4 Híbrido + ontología | 0,980 | **1,000** |
| C2 Denso + ontología | 0,913 | **1,000** |
| C1 Denso puro | 0,925 | 0,966 |
| BM25 | 0,862 | 0,854 |

**Interpretación (memorízala):** los nombres sintéticos **no existen en ningún documento** (el corpus
describe reportes, no personas). Para BM25 son tokens sin coincidencia (ruido); para el denso son
distracción. Por tanto, el estrato "entidad_exacta" **mide cuánto el texto describe el tema del reporte**,
**no** la capacidad de encontrar un nombre propio. La hipótesis P2 ("el híbrido gana en nombre propio")
**no es contrastable con este diseño**: la búsqueda real por nombre propio se resuelve en el gazetteer,
fuera del índice. Para probarla hay que (a) indexar entidades reales (de forma privada) o (b) construir
consultas cuyo objetivo *sea* una entidad (p. ej. una Prueba Regional con nombre en el documento) — que es
precisamente lo que habilita el **corpus de competencias**.

### 9.5 Escalera 2 — corpus combinado de 833 documentos 🔴

17 reportes + 816 Pruebas Regionales (cartesiano). Hallazgo viejo: a escala el híbrido es necesario,
denso puro cae (nDCG 0,826, Recall@100 0,950). **Los resultados viejos están en
`resultados/obsoletos_pre_2026-09-30/`** y deben rehacerse con el corpus definitivo (6.3).

### 9.6 Qué es "known-item" y qué implica

Un protocolo estándar en IR: cada consulta tiene **un** objetivo conocido. Consecuencias:
- P@10 tiene techo de **0,1** (un relevante entre diez). Un P@10 de 0,117 con grados secundarios no es "mal".
- Recall@100 es **trivialmente 1,0** en 17 documentos (el top-100 los contiene a todos).
- MRR y nDCG@10 son las métricas informativas.

---

### 9.7 Conjunto difícil (52 consultas) 🟢 — `construir_eval_dificil.py`

**Por qué existe.** En los otros conjuntos casi todas las consultas ya están en la posición 1 (techo de nDCG), por lo que hay
pocos pares con diferencia y poco poder. Este conjunto fuerza **paráfrasis y lenguaje coloquial** sin el vocabulario del documento.

- Cubre **13 reportes** (4 consultas cada uno). Se omiten los 4 reportes de "pruebas de caídas": su significado de negocio
  no está confirmado y no se redactan consultas sobre algo que no se entiende.
- **El nivel de dificultad no se asigna a mano**, se *calcula* con el solape de raíces Snowball entre la consulta y (a) la
  descripción (sin palabras de plantilla) y (b) el bloque de ontología:
  - **A_puente_ontologia (22)**: 0 raíces con la descripción, ≥1 con la ontología → la ontología *puede* ayudar.
  - **B_sin_puente (13)**: 0 con ambas → solo la semántica densa puede ayudar. **Es el control contra el sesgo** de haber redactado
    las consultas conociendo los sinónimos de la ontología.
  - **C_con_solape (17)**: comparte ≥1 raíz con la descripción.
- **Advertencia:** las consultas las redactó el asistente a partir de los títulos; **Luis debe revisarlas** y luego pasarlas a expertos.
  Por construcción, BM25 sobre la descripción obtiene ≈0 en A y B (no puede encontrar lo que no comparte): su 0,186 global
  **no es un hallazgo**, es una consecuencia del diseño. No lo presentes como "BM25 es malo".
- 16 de las 52 consultas apuntan a reportes **sin** bloque de ontología (distribución de usuarios, federación, cambios, delegaciones).

### 9.8 Anotación por expertos (preparada, no ejecutada) — `experimentos/anotacion/`

- `preparar_anotacion.py`: *pooling* de las 6 configuraciones (top-3 de cada una) sobre las 50 consultas `gold_candidate` + las 52
  difíciles. Genera `hoja_anotador_A.csv` y `_B.csv` (mismo contenido, orden aleatorio distinto, **ciego**: sin nombres de sistema
  ni posiciones) y `pool_clave.json` (qué sistema aportó cada par; no se entrega a los anotadores).
- Escala **0/1/2**; reglas en `INSTRUCCIONES_ANOTACION.md`.
- `calcular_kappa.py`: acuerdo exacto, **κ de Cohen** (sin ponderar y ponderado lineal, porque la escala es ordinal), matriz de
  confusión, lista de desacuerdos para adjudicar, y `datos/qrels_gold.jsonl`. Auto-test: κ=0,4 en un caso 2×2 verificable a mano.
- **Estado:** nadie ha anotado. Mientras tanto todos los juicios siguen siendo *silver*.

## 10. Las métricas con ejemplos numéricos

Todas en `lib/metrics.py`, con auto-test. Operan sobre el **ranking** (lista de ids) y los **qrels** (`doc → grado`).

### 10.1 nDCG@10 (la primaria)

```
DCG@k  = Σ_{i=1..k} (2^rel_i − 1) / log2(i + 1)
nDCG@k = DCG@k / IDCG@k
```

Con **un solo objetivo de grado 2** (ganancia 2²−1 = 3) el IDCG = 3 (está en la posición 1), así que
nDCG = descuento de la posición donde cae el objetivo:

| Posición del objetivo | nDCG@10 | MRR |
|---|---|---|
| 1 | **1,000** | 1,000 |
| 2 | 1/log2(3) = **0,631** | 0,500 |
| 3 | 1/log2(4) = **0,500** | 0,333 |
| 4 | 1/log2(5) = **0,431** | 0,250 |
| 10 | 1/log2(11) = **0,289** | 0,100 |
| 11 o más | 0 | 0 |

**Intuición para el jurado:** pasar de la posición 1 a la 2 cuesta 0,37 de nDCG en esa consulta. Por eso
una diferencia media de 0,05 entre sistemas ≈ "en 1 de cada 7 consultas el objetivo baja una posición".

### 10.2 MRR@10

`1/rank` del primer relevante, promediado. Con un único objetivo es casi equivalente a nDCG pero con
descuento más agresivo (1/rank vs 1/log2(rank+1)).

### 10.3 Recall@100

Fracción de relevantes en el top-100. Distingue "no lo encontró" de "lo ordenó mal". **Trivial** en 17 docs;
se vuelve informativa con 800+ (en la Escalera 2 vieja ya discriminaba).

### 10.4 P@10 y AP@100

P@10 = aciertos en top-10 / 10 (techo 0,1 en known-item). AP@100 = media de las precisiones en cada
posición de acierto (base de MAP).

### 10.5 Qué métrica reportar primero

**nDCG@10** (estándar BEIR, soporta relevancia graduada) y **MRR@10** (interpretación directa: "¿en qué
posición está mi reporte?"). Las otras son soporte.

---

## 11. La estadística, explicada sin miedo

`lib/stats.py`. Se comparan configuraciones **pareadas**: las mismas consultas, dos sistemas.

### 11.1 Wilcoxon de rangos con signo (pareado)

- Toma las diferencias por consulta `d_i = nDCG_A(q_i) − nDCG_B(q_i)`.
- Descarta los ceros (empates), ordena `|d_i|`, suma los rangos de los positivos (W+) y de los negativos (W−).
- No asume normalidad (importante: nDCG en known-item está pegado a 1 y es muy asimétrico).
- **El poder real lo da el número de pares NO nulos.** Con n=127 pero solo 13 pares donde C4≠C3, el test
  "ve" 13 datos. Por eso se reporta `n_pares_no_nulos`. **Esta es la razón por la que n grande no
  garantiza significancia** (techo del known-item: la mayoría de consultas ya están en 1,0).

### 11.1b Prueba de permutación pareada (aleatorización de signos) 🟢 — nuevo

- **Idea:** bajo H0 (no hay diferencia entre sistemas) el signo de cada diferencia `d_i` es intercambiable. Se recalcula la
  media de `d` con todos los signos posibles y se mira qué fracción de asignaciones da un |media| igual o mayor que el observado.
- **Exacta** cuando hay ≤ 20 diferencias no nulas (se enumeran las 2^n asignaciones); **Monte Carlo** (20.000 sorteos, con la corrección
  (b+1)/(n+1) para no reportar p=0) cuando hay más. Bilateral. Los ceros no cuentan.
- **Por qué se añadió:** Smucker, Allan y Carterette (2007) hallaron que Wilcoxon y la prueba de signos discrepan de t/bootstrap/permutación.
  Si una conclusión depende de cuál prueba uses, no es sólida. Regla adoptada: una comparación es **«robusta» solo si Wilcoxon y
  permutación rechazan tras Holm** (campo `robusto` en los JSON).
- **Validación:** el auto-test la compara con `scipy.stats.permutation_test` (coinciden a 1e-9) y con casos de mano (p=2/8=0,25).
- **Respuesta al jurado que cite a Smucker:** "Lo sé, por eso no dependo solo de Wilcoxon; cada p-valor va con permutación y con IC bootstrap".

### 11.2 Tamaño de efecto: rank-biserial pareado (Kerby 2014)

`r = (W+ − W−) / (W+ + W−)`, rango [−1, 1]. Sustituyó a **Cliff's δ**, que no es pareado y era
incoherente con el test. Interpretación: r = 1 → todas las diferencias no nulas favorecen a A.
**Ojo:** r=1,0 con 5 pares no nulos es menos convincente que r=0,6 con 40.

### 11.3 Bootstrap pareado

Remuestrea las **diferencias** (1.000 veces, semilla 42) y toma percentiles 2,5–97,5 de la media. Da un IC
95 % de la diferencia sin supuestos paramétricos. Si el IC incluye 0, la diferencia no es concluyente.

### 11.4 Holm-Bonferroni (por qué existe y qué cambió)

Se hacen 5 comparaciones por familia → con α=0,05 sin corregir esperas ~23 % de probabilidad de al menos un
falso positivo. **Holm** controla el FWER: ordena los p, multiplica el menor por m, el siguiente por m−1…, y
fuerza monotonía.

Ejemplo real (global, ampliado, 127 consultas):

| Comparación | p | Orden | ×factor | p_Holm |
|---|---|---|---|---|
| C3 vs BM25 | 0,0018 | 1º | ×5 | **0,0089** ✔ |
| C5 vs C4 | 0,0412 | 2º | ×4 | 0,165 |
| C4 vs C3 | 0,1262 | 3º | ×3 | 0,379 |
| C3 vs C1 | 0,3362 | 4º | ×2 | 0,672 |
| C2 vs C1 | 0,6549 | 5º | ×1 | 0,672 (monotonía) |

→ **Solo C3 > BM25 sobrevive.** Antes de Holm, "C5 empeora" parecía significativo (p=0,04); después no.

### 11.5 Cómo redactar un resultado no significativo

Nunca "no hay efecto". Sí: *"el efecto es de dirección consistente (Δ=+0,016) pero el intervalo [−0,003; +0,039]
incluye 0 y solo 13 de 127 consultas difieren; la muestra no permite concluir."*

---

## 12. El framework de código, archivo por archivo

### 12.1 Cómo se ejecuta

```bash
cd experimentos
python3 -m pip install -r requirements.txt   # numpy scipy scikit-learn pyyaml matplotlib snowballstemmer
make all        # corpus → consultas → ablación → reportes
make test       # auto-tests de métricas y estadística
make eval_real  # eval ampliado (127 consultas, 17 reportes)
make control    # lo mismo con el nombre borrado
make extraer    # (usuario, AWS) extracción agregada de competencias
make final      # corpus definitivo
make smoke      # tubería completa con encoder LSA offline
make dificil    # conjunto difícil + su evaluación
make barridos   # sensibilidad + P4 + P6
make cobertura  # ontología según objetivo enriquecido
make diagnostico # detector del realce
make tablas     # tablas LaTeX desde los JSON
make anotacion  # hojas para expertos
```

### 12.2 Mapa de archivos

| Archivo | Papel |
|---|---|
| `config.yaml` | **Única fuente de verdad**: rutas, encoder, k1/b, k_rrf, λ, dims, semilla |
| `preprocess_corpus.py` | Construye `corpus_v1.jsonl` + auditoría PII + stats |
| `generar_consultas.py` | 51 consultas sintéticas + qrels |
| `construir_eval_real.py` | Eval real silver v1 (71 consultas) |
| `construir_eval_real_ampliado.py` | Eval ampliado por patrones (127) + `texto_sin_nombre` |
| `construir_competencias.py` | Corpus cartesiano 816 (🔴 sustituido) |
| `construir_competencias_v2.py` | Corpus definitivo de competencias (espera Athena) |
| `athena/extraer_competencias.py` | Extracción agregada en Athena |
| `run_ablation.py` | Corre BM25 + C1–C5, métricas por consulta, agregados, estadística |
| `eval_flexible.py` | Misma escalera sobre cualquier corpus/consultas/qrels |
| `generar_reportes.py` | Tablas md/tex, figura, recomendación, análisis de fallos |
| `lib/metrics.py` | nDCG, Recall, MRR, P@k, AP |
| `lib/indexes.py` | `BM25Index` (propio), `DenseIndex` (coseno exacto), tokenizador |
| `lib/encoders.py` | `SentenceTransformerEncoder` y `LSAEncoder` tras una interfaz común |
| `lib/retrievers.py` | RRF, `DetectorEntidades`, `MotorRecuperacion` (las 5 configs) |
| `lib/stats.py` | Wilcoxon, rank-biserial, bootstrap, Holm, `FAMILIA` de comparaciones |
| `lib/etiquetado.py` | Regla de promoción compartida EDA↔evaluación, mapeo por slug |
| `lib/error_analysis.py` | Fallos del estrato entidad_exacta |
| `construir_eval_dificil.py` | Conjunto difícil de 52 paráfrasis con nivel A/B/C calculado |
| `barridos.py` | Sensibilidad (k, λ, k1, b) + P6 (Matryoshka) + P4 (chunking), con tareas LoRA activas |
| `analisis_cobertura_ontologia.py` | Efecto de la ontología según el objetivo esté enriquecido (exploratorio) |
| `diagnostico_detector.py` | Precisión/recall del detector del realce en los 3 conjuntos |
| `generar_tablas_tex.py` | Genera las tablas LaTeX de la monografía **desde los JSON** (sin transcribir) |
| `anotacion/` | Hojas de anotación ciega, instrucciones y cálculo de κ |

### 12.3 Decisiones de diseño que puedes defender

- **BM25 propio, sin `rank_bm25`:** control total del analizador español y de los empates.
- **Encoder enchufable:** `sentence-transformer` (real) o `lsa` (TF-IDF+SVD, offline). El LSA **valida la
  tubería, no produce resultados científicos**.
- **Coseno exacto, sin ANN:** 17 docs (o cientos). Un HNSW agregaría error de aproximación sin beneficio.
- **Desempates deterministas por `doc_id`:** reproducibilidad entre procesos (el orden de un `set` en Python
  depende del hash aleatorio; eso rompía reproducibilidad).
- **Shim de compatibilidad de jina-v3:** `transformers ≥ 5` exige `all_tied_weights_keys`; el código remoto
  de jina no lo define; se asigna `{}` (correcto en inferencia). Requiere además `einops`. Python 3.14 del
  sistema (no hay venv).
- **Notebooks autocontenidos** (por pedido explícito): todo el núcleo inline, sin importar `lib/`, con la
  estructura *Contexto y Objetivo / Descripción Técnica / Interpretación de Resultados* de su repo de referencia.

---

## 13. La auditoría del 30-sep: qué estaba mal y qué se arregló

**Por qué importa contarla:** demuestra rigor. Un jurado valora más "encontré y corregí mis errores" que
"todo salió perfecto".

### 13.1 Bugs del benchmark (verificados)

| # | Problema | Efecto | Arreglo |
|---|---|---|---|
| 1 | **BM25 devolvía documentos con score 0 en orden de indexación** | El primer documento (`ri_001`) ganaba todos los empates a cero y entraba a RRF | `buscar` devuelve solo score > 0 |
| 2 | **RRF contaba a los ausentes** como si estuvieran al final | Aporte espurio | Ausente → sin aporte de esa lista |
| 3 | **jina-v3 sin `task`** | No se activaba el adaptador de recuperación | `retrieval.query` / `retrieval.passage` |
| 4 | **Sin stemming** en BM25 | "deportista" ≠ "deportistas" | Snowball ES |
| 5 | **Dimensión 1.536 en el barrido Matryoshka** | Inválida (jina-v3 nativo = 1.024) | Validación `0 < m ≤ dim_nativa`; dims `[64…1024]` |
| 6 | **Cliff's δ no pareado** | Inconsistente con Wilcoxon | rank-biserial pareado |
| 7 | **Sin corrección por comparaciones múltiples** | P1 "casi significativo" (p→0,067) | Holm |
| 8 | **Detector de nombre propio por subcadena** | "etapa" activaba dentro de "etapas"; "Caribe" parecía nombre propio | Coincidencia por palabra + filtro de vocabulario del dominio |
| 9 | **Fuga de "Andrés Torres"** en `metadatos_por_reporte.json` | El nombre sintético de las consultas estaba en los metadatos del documento → inflaba entidad_exacta | Eliminado |
| 10 | **`entidad_exacta` no mide nombres** (los sintéticos no están en los docs) | Estrato mal rotulado | Control `texto_sin_nombre`; hallazgo 16.1 |
| 11 | **Pseudo-replicación** en el eval ampliado | n inflado | Unidad = patrón de firma + dedupe global |

### 13.2 Bugs del EDA (verificados)

- "Promoción 47,5 %" = artefacto de clasificación (4.4).
- 26,8 % de la demanda eran `SELECT DISTINCT` de filtros (no pedidos de reporte).
- Gemelos COUNT: 38,5 % y no "~50 %".
- "Cero consultas a competencias": falso para `groups` y `participants`.
- Muestra de 296 casos nunca etiquetada.

### 13.3 Qué cifras cambiaron (ejemplo para cuando te pregunten "¿y entonces?")

| | Antes | Ahora |
|---|---|---|
| Sintético, mejor config | C4 0,936 | **C4 0,948** |
| Sintético, ranking | — | C4 > C2 > C5 > C3 > C1 > BM25 |
| Ampliado, C3 vs BM25 | p=0,011 (n=55 entidad) | **p_Holm = 0,009** (global, n=127) |
| P1 en entidad exacta (sintético) | p=0,068 | **p_Holm = 0,17** (no sig. en el estrato) |

**Moraleja:** la conclusión "el híbrido supera a BM25" se **fortalece** (sobrevive a Holm en 127 consultas);
las conclusiones sobre ontología y entidad exacta se **debilitan**.

---

## 14. Resultados vigentes, con su estado

> Todo lo de esta sección sale de una sola ejecución (2026-10-05) con `jina-embeddings-v3` y las tareas `retrieval.query` /
> `retrieval.passage`, sobre el corpus de 17 reportes. Las cifras 🟢 son las que aparecen en la monografía; **se generaron con
> `generar_tablas_tex.py` desde los JSON**, así que lo que ves aquí y en el `.tex` coincide. Siguen siendo del corpus v1; el
> corpus definitivo (competencias) las complementará, no las reemplazará.

### 14.1 nDCG@10 global, por conjunto 🟢

| Config | Sintético (40) | Ampliado (127) | Difícil (52) |
|---|---|---|---|
| BM25 | 0,819 | 0,887 | 0,186 |
| C1 Denso | 0,866 | 0,932 | 0,712 |
| C2 Denso+onto | 0,931 | 0,928 | **0,835** |
| C3 Híbrido | 0,893 | 0,943 | 0,686 |
| C4 Híbrido+onto | **0,948** | **0,960** | 0,788 |
| C5 +realce | 0,924 | 0,944 | 0,739 |

Cómo se lee: C4 gana en los dos primeros; en el difícil gana **C2** y el híbrido queda *por debajo* del denso (§16.4).
BM25 = 0,186 en el difícil **es por construcción** (§9.7), no un hallazgo. Recall@100 de BM25 en el sintético = 0,950 (no 1,0)
porque solo devuelve documentos con algún término en común.

### 14.2 Estadística de la familia de 5 comparaciones 🟢

Celda = Δ nDCG@10 (primera menos segunda) y, entre paréntesis, **el mayor** de los dos p ajustados por Holm (Wilcoxon, permutación).
**Negrita = robusta** (ambas rechazan con α=0,05).

| Comparación | Sintético | Ampliado | Difícil |
|---|---|---|---|
| C3 vs BM25 (P1) | **+0,073 (0,021)** | **+0,056 (0,009)** | **+0,500 (<0,001)** |
| C3 vs C1 (P1) | +0,026 (0,820) | +0,011 (0,672) | −0,026 (0,214) |
| C2 vs C1 (P3 denso) | **+0,065 (0,027)** | −0,004 (0,672) | **+0,122 (0,002)** |
| C4 vs C3 (P3 híbrido) | **+0,056 (0,043)** | +0,016 (0,406) | +0,102 (0,072) |
| C5 vs C4 (P5) | −0,024 (0,820) | −0,016 (0,250) | **−0,049 (0,035)** |

Pares con diferencia no nula / total (el poder real): sintético 11/40, 11/40, 10/40, 10/40, 3/40 · ampliado 31/127, 16/127, 11/127,
13/127, 5/127 · difícil 45/52, 19/52, 21/52, 34/52, 8/52. **Lectura:** el conjunto difícil tiene 3–7 veces más pares informativos.

### 14.3 Por estrato 🟢

**Ampliado (nDCG@10):**

| Config | entidad (55) | operacional (35) | doc. largo (25) | ambigua (12) |
|---|---|---|---|---|
| BM25 | 0,862 | 0,893 | 0,910 | 0,938 |
| C1 | 0,925 | 0,961 | 0,945 | 0,854 |
| C2 | 0,913 | 0,961 | 0,945 | 0,866 |
| C3 | 0,926 | 0,957 | 0,950 | **0,969** |
| C4 | **0,980** | 0,941 | 0,946 | 0,953 |
| C5 | 0,980 | 0,930 | 0,880 | 0,953 |

**Sintético:** entidad (17): BM25 0,883 · C1 0,875 · C2 0,931 · C3 0,972 · **C4 0,976** · C5 0,957 — ambigua (13): C4 y C5 0,962 — doc. largo (10): C2 0,900 mejor, C4 0,884, C3 0,721.

En entidad exacta del ampliado: C3 vs C1 = +0,001 (p_Holm=1,0); C4 vs C3 = +0,054, p_Holm 0,069 (Wilcoxon) / 0,054 (permutación) → **marginal, no robusto**.

### 14.4 Control sin nombre propio (entidad exacta, n=55) 🟢

| Config | con nombre | sin nombre |
|---|---|---|
| BM25 | 0,862 | 0,854 |
| C1 | 0,925 | 0,966 |
| C2 | 0,913 | **1,000** |
| C3 | 0,926 | 0,953 |
| C4 | 0,980 | **1,000** |
| C5 | 0,980 | 1,000 |

Sube en 5 de 6. **El estrato mide tema, no entidad** (§9.4).

### 14.5 Conjunto difícil por nivel 🟢

| Config | A puente ontología (22) | B sin puente (13) | C con solape (17) |
|---|---|---|---|
| BM25 | 0,000 | 0,000 | 0,569 |
| C1 | 0,624 | 0,804 | 0,757 |
| C2 | **0,864** | 0,818 | 0,810 |
| C3 | 0,597 | 0,778 | 0,730 |
| C4 | 0,856 | 0,650 | 0,657 |

Nivel A: la ontología sube al denso de 0,624 a 0,864 (+0,24). Nivel B (sin puente): el denso puro ya llega a 0,804 y la ontología casi no
agrega (0,818): ahí el mérito es del modelo, no de la ontología. Nótese que **C4 cae en B y C (0,650/0,657)**: el híbrido lastra al denso.

### 14.6 Cobertura de la ontología (exploratorio, sin Holm) 🟢

| Conjunto | Objetivo | n | Comparación | Δ | pares≠0 | p Wilcoxon | p permutación |
|---|---|---|---|---|---|---|---|
| difícil | enriquecido | 36 | C2−C1 | +0,180 | 16 | 0,0004 | <0,001 |
| difícil | enriquecido | 36 | C4−C3 | +0,219 | 26 | 0,0005 | 0,0004 |
| difícil | **sin enriquecer** | 16 | C2−C1 | −0,006 | 5 | 0,68 | 0,88 |
| difícil | **sin enriquecer** | 16 | **C4−C3** | **−0,161** | 8 | 0,0117 | 0,0078 |
| ampliado | enriquecido | 112 | C2−C1 / C4−C3 | −0,005 / +0,019 | 11 / 13 | 0,65 / 0,13 | 0,55 / 0,14 |
| ampliado | sin enriquecer | 15 | ambas | 0,000 | 0 | n/d | n/d |

### 14.7 Realce y detector 🟢

- C5 vs C4: −0,024 / −0,016 / −0,049. En el ampliado, λ=0,2: 5 consultas empeoran, **0 mejoran**.
- Barrido de λ ∈ {0; 0,05; 0,1; 0,2; 0,3; 0,5}: todo λ>0 queda por debajo de λ=0; a partir de 0,2 el resultado no cambia (saturación).
- **Detector corregido** (palabra completa, filtro de vocabulario): precisión 0,17 / 0,13 / 0,10 y recall 0,70 / 0,74 / 0,38 (sint./amp./dif.),
  activa 4–6 de 17 documentos por consulta. Azar ≈ 1/17 = 0,06 → apenas 2–3× mejor que el azar. *(Antes: precisión 0,13, recall 0,94,
  7,5 documentos con el detector por subcadena; ese diagnóstico quedó obsoleto.)*

### 14.8 Sensibilidad a lo que se fijó sin ajustar 🟢

- **k de RRF:** idéntico para k ≥ 30; k=10 cambia 1 consulta (ampliado); k=1 cambia 5 (C3) y 2 (C4) consultas en el sintético, 9 y 5 en el ampliado.
  **Cuidado:** con 17 documentos los rangos van de 1 a 17, así que k apenas altera el orden. Esta insensibilidad **no se extrapola** a un corpus grande.
- **λ:** ver 14.7.
- **BM25 k1 × b:** BM25 solo varía 0,815–0,828 (sint.) y 0,849–0,905 (amp.); C4 se mantiene en 0,948–0,952 y 0,960–0,967.
  El híbrido supera a BM25 en **toda** la rejilla.
- *Respuesta a "¿por qué k=60?":* es el valor estándar (Cormack 2009) y medimos que, en este corpus, k∈[10,200] da lo mismo.

### 14.9 P6 — Matryoshka (con tareas LoRA y dimensiones válidas) 🟢

| m | Sintético: C4 (Δ vs 1024, equivalencia) | Ampliado: C4 (Δ, equivalencia) | Ahorro de índice |
|---|---|---|---|
| 1024 | 0,948 | 0,960 | 0 % |
| 768 | 0,948 (0,000; eq.) | 0,960 (0,000; eq.) | 25 % |
| 512 | 0,931 (−0,018; no eq.) | 0,963 (+0,003; **eq.**) | 50 % |
| **256** | 0,940 (−0,008; no eq.) | 0,963 (+0,003; **eq.**) | **75 %** |
| 128 | 0,944 (−0,004; no eq.) | 0,944 (−0,016; perm. p=0,029; no eq.) | 87,5 % |
| 64 | 0,949 (+0,001; no eq.) | 0,923 (−0,037; perm. p=0,001; no eq.) | 93,8 % |

- **«eq.» = equivalente** con margen ε=0,01 (límite inferior del IC95 de la diferencia > −0,01). «no eq.» = **no concluyente**, no «hay pérdida».
- En el **sintético (n=40) el IC es demasiado ancho** para declarar equivalencia por debajo de 768: es un límite de poder.
- **Latencia:** búsqueda ≈ 0,1 ms; **codificar la consulta** 349 ms (p50), 357 ms (p95). Truncar ahorra memoria, **no** latencia.
- **Recomendación: 256.** *(Cifras antiguas —retención 1,000 en 256, 0,970 en 128— están obsoletas.)*

### 14.10 P4 — Fragmentación 🟢

Documentos de 64–184 palabras (media 103). Ningún tamaño supera de forma apreciable al documento completo: la única ganancia es +0,004
(sintético, 128 palabras, solapamiento 25 %), dentro del ruido; fragmentos de 24 palabras pierden hasta −0,063. **Unidad de indexación v1: el reporte completo.**

### 14.11 Resultados obsoletos 🔴 (no uses)

`resultados_real_v1.json`, `resultados_real_combinado.json` (en `obsoletos_pre_2026-09-30/`), el 0,936/0,976 anterior, "P3 NO significativo
p=0,65" del notebook 07, el corpus de 833 documentos, el barrido Matryoshka anterior (sin tareas LoRA), el detector 0,126/0,941.

### 14.12 Réplica: conjunto difícil B (78 consultas nuevas) 🟢
Redactada **después** de ver los resultados de A (no es prueba ciega). nDCG@10 B: BM25 0,422 · C1 0,783 · C2 **0,837** · C3 0,778 · C4 0,835 · C5 0,773.
Estadística B: C3−BM25 **+0,356** (robusto) · C3−C1 −0,005 · C2−C1 **+0,054** (robusto) · C4−C3 +0,058 (n.s., 30/78 pares) · C5−C4 **−0,063** (robusto).
Unión A+B (n=130): C3−BM25 +0,413 · C3−C1 −0,013 · C2−C1 **+0,081** · **C4−C3 +0,075 (robusto, 64/130 pares)** · C5−C4 **−0,057**.
Por nivel (A+B): nivel A: C1 0,689 → C2 0,819; C3 0,636 → C4 0,870. Nivel B: C1 0,766, C2 0,801. **Todo lo de A se replica en dirección y casi siempre en significancia.**

### 14.13 Fusión alternativa (`fusion.py`, parámetro por leave-one-set-out) 🟢
Base enriquecida, nDCG@10 (Δ vs RRF): convexa min–max sint +0,010 · amp 0,000 · A +0,014 · B +0,039; convexa z +0,001 / −0,001 / +0,017 / +0,034; RRF ponderado +0,004 / −0,001 / −0,004 / +0,019;
compuerta −0,006 / 0,000 / **+0,062** / +0,011. **Ninguna robusta** (Holm + permutación). La compuerta en A (pH 0,026 Wilcoxon, 0,054 permutación) no se replica en B.
Oráculo (mejor α en el propio conjunto, optimista): 0,958 · 0,976 · 0,843 · 0,877. El α óptimo cae entre 0,6 y 0,9 (más peso al denso).
Sanidad: el RRF de este módulo reproduce exactamente C1–C4 (aserción en el script).

### 14.14 Ontología ampliada 14/17 (`enriquecimiento_completo.py`) 🟢
Entidades derivadas **mecánicamente** de las columnas reales de las firmas ↔ propiedades de la ontología (sin texto libre, sin mirar consultas). 5 reportes nuevos; 010 (usuarios), 016 y 017 sin clase mapeable.
Híbrido (sin / parcial / ampliada): sint 0,893/0,948/0,937 · amp 0,943/0,960/0,960 · A 0,686/0,788/0,801 · B 0,778/0,835/0,839. **No mejora el total.**
En las consultas cuyo objetivo antes no tenía bloque: híbrido ampliada − parcial = **+0,071 (A, n=16, p=0,46)** y **+0,066 (B, n=24, p=0,06)**: misma dirección en dos muestras, no significativo → «apoyada, no confirmada».
Advertencia: es un enriquecimiento pobre (solo entidades+sinónimos, sin «Responde a»).

### 14.15 Errores (`analisis_errores.py`) 🟢
acc@1 (BM25/C1/C2/C3/C4): sint 0,65/0,73/0,83/0,75/**0,88** · amp 0,75/0,88/0,87/0,87/**0,92** · A 0,14/0,40/**0,65**/0,44/0,62 · B 0,37/0,58/**0,64**/0,62/**0,64**.
Confusiones típicas: métricas por federación → individual de deportistas (3 en A); personal de apoyo → grupos (2 en B); instituciones → grupos. Muchas son consultas genuinamente ambiguas entre dos reportes → límite del objetivo único.

### 14.16 Escalamiento (`escalamiento.py`, vectores aleatorios, equipo con otras tareas) 🟢
Búsqueda exacta p50: N=10⁴ → 0,1–1 ms; N=2·10⁵ → 3 ms (m=64), 6,6 ms (256), 17,7 ms (1024). Memoria 2·10⁵: 49 / 195 / 781 MiB. Hasta cientos de miles de documentos la búsqueda es despreciable frente a codificar la consulta (349 ms): **truncar ahorra memoria, no latencia**. No mide calidad.

### 14.17 Pruebas unitarias 🟢
`make test`: 19 pruebas (BM25 solo >0, IDF a mano, RRF del ejemplo, ausentes, desempate, fusión convexa/compuerta, nDCG por posición, Holm, permutación, rank-biserial, regla de promoción, detector por palabra, **regresión de fuga de nombres sintéticos**, PII, integridad de conjuntos, dedupe).

---

## 15. Las seis preguntas de investigación, respondidas con honestidad

### P1 — ¿Cuánto supera el híbrido a BM25 y al denso, y es significativo?
- **Frente a BM25: sí, robusto en los cuatro conjuntos** (+0,073, +0,056, +0,500, +0,356 en B; Holm y permutación) y en toda la rejilla de k1×b.
- **Frente al denso: no se demuestra** (+0,026, +0,011, **−0,026**; ninguno significativo). En el difícil el signo se invierte.
- **Frase:** "El híbrido supera de forma robusta a la señal léxica sola; su ventaja sobre el denso puro no se demuestra y puede invertirse cuando la consulta no comparte vocabulario con el documento".

### P2 — ¿La ventaja se concentra en entidad exacta / nombre propio?
- **No es contrastable con este diseño** (control sin nombre, §9.4/§14.4). Descriptivamente C4 = 0,980 vs C1 = 0,925 en entidad (ampliado), pero esa ventaja es de la **ontología**, no del híbrido (C3 vs C1 = +0,001), y no es robusta (p_Holm 0,054–0,069).
- **Frase:** "No pudo contrastarse: el control mostró que el estrato mide el tema del reporte. P2 exige un corpus donde la entidad figure en el documento — el de competencias".
- No es un fracaso: **es un hallazgo sobre el instrumento de medida**.

### P3 — ¿La ontología mejora denso y/o híbrido?
- Denso (C2 vs C1): **robusto** en sintético (+0,065) y difícil (+0,122); nulo en ampliado (−0,004).
- Híbrido (C4 vs C3): robusto en sintético (+0,056) y en la **unión A+B** (+0,075); no en ampliado (+0,016), ni en A (+0,102; p_Holm 0,072) ni en B (+0,058) por separado (mismo signo, falta poder).
- **Mecanismo:** ayuda donde hay brecha de vocabulario (nivel A: +0,24 al denso); no donde la consulta ya usa el vocabulario del reporte.
- **Matiz:** la cobertura parcial perjudica a los no enriquecidos (−0,161, exploratorio); ampliar a 14/17 los recupera en dirección (+0,07 en A y B) sin confirmarse (§14.14).
- **Frase:** "La ontología es un puente de vocabulario: su valor depende de cuánto se aparte la consulta del texto del documento, y debe aplicarse a todo el corpus o a ninguno".

### P4 — ¿Chunking? 
No aporta con documentos de 64–184 palabras. Medido con tareas LoRA, dos conjuntos, tres solapamientos.

### P5 — ¿Realce suave por entidad?
**Se descarta.** Nunca mejora (−0,024, −0,016, −0,049; robusto en el difícil), ningún λ lo salva, y el detector apenas supera al azar (precisión 0,10–0,17).
*(El «matiz» del 18-sep —C5 ayudaba en el eval real v1— era artefacto de pseudo-replicación; con el ampliado deduplicado desaparece.)*

### P6 — ¿Mejor configuración y dimensión?
**Híbrido + ontología, sin realce, 256 dimensiones, coseno exacto,** y ontología sobre todo el corpus. 256 es equivalente a 1024 en el ampliado con −75 % de índice.

---

## 16. Hallazgos que debes poder explicar

### 16.1 "Mi estrato de entidad exacta no mide entidades"
Ver §9.4. Lo descubriste tú con un control propio y lo reportas: es tu mejor muestra de pensamiento crítico.

### 16.2 "Más consultas no dieron más significancia"
n=127 no volvió significativo todo porque el poder lo da el número de **pares no nulos** (13 de 127 para C4 vs C3). El conjunto difícil (34 de 52)
lo corrige. Lección de diseño: para detectar efectos pequeños hacen falta consultas **difíciles**, no más consultas fáciles.

### 16.3 "El realce falla porque el detector no discrimina"
Precisión 0,10–0,17 (azar ≈ 0,06) y 4–6 documentos activados por consulta. Variantes no lo arreglan. v2: detector de **mención** contra el gazetteer.

### 16.4 "¿El híbrido lastra al denso?" (matizado con la réplica)
Hipótesis tras el difícil A: con RRF, si la consulta no comparte vocabulario la lista de BM25 está vacía o es ruidosa y entra a la suma. Evidencia: C4 − C2 = **−0,047** en A (n.s.), pero **−0,002** en la réplica B, y **+0,032 a favor del híbrido** en el ampliado (p 0,019 / 0,012 sin corregir). **Conclusión: el signo depende del conjunto; no se puede afirmar que lastre.** Lo que sí se midió: ninguna fusión convexa/ponderada/con compuerta (parámetro elegido sin fuga, LOSO) supera a RRF de forma robusta (§14.13). Bruch et al. (2024) dicen que la convexa supera a RRF: aquí lo es *en dirección* en los difíciles (+0,014 A, +0,039 B), no significativo.
Elegimos RRF *porque no requiere etiquetas*; su costo frente a una fusión calibrada es pequeño y no demostrado.

### 16.5 "La demanda real cambió de líder"
El reporte más pedido es el **Individual** (40,4 %), no Promoción (4,2 %, #7). Reordena la prioridad de indexación.

### 16.6 "La ontología solo cubre 9 de 17 reportes" (nuevo)
Los documentos enriquecidos son más largos y con más términos, así que compiten con ventaja. Para los 16 casos del difícil cuyo objetivo no está enriquecido,
C4 vs C3 = **−0,161** (p<0,02). No se ve en el ampliado porque sus consultas son fáciles. v2: ontología sobre todos los documentos.

### 16.7 "El valor del híbrido crece con el tamaño del corpus" 🟡
Con 17 documentos el top-100 contiene todo y el denso casi basta. La Escalera 2 anterior (833 docs) lo sugería, pero está **obsoleta**; debe confirmarse
con el corpus definitivo.

---

## 17. Limitaciones y amenazas a la validez

Úsalo casi literal en el capítulo de limitaciones y en la defensa. (Versión formal en la monografía: «Amenazas a la validez».)

**Constructo**
- Known-item mide "¿encuentras el reporte que sé que es?", no "¿resolviste la necesidad?".
- Juicios *silver*; el reporte ejecutado puede no ser el mejor para la intención real.
- El estrato `entidad_exacta` mide tema (§9.4). P2 no es contrastable.

**Interna**
- Consultas sintéticas y difíciles **escritas por nosotros**, con vocabulario compartido (nivel C) o redactadas conociendo la ontología (nivel A; el nivel B es el control).
- El eval ampliado sintetiza el texto desde los filtros: proxy del lenguaje natural real.
- Un solo juez; sin κ (hojas preparadas, sin anotar).
- Descripciones de plantilla: el contenido semántico real del documento es mínimo.
- Ontología parcial (9/17).

**Estadística**
- Techo de nDCG y pocos pares no nulos; estratos pequeños (ambigua n=12).
- Holm solo **dentro** de cada familia de 5; no hay corrección global entre conjuntos ni estratos; el análisis de cobertura es exploratorio.
- Poder insuficiente en el sintético para declarar equivalencia en P6.
- Smucker et al.: Wilcoxon puede discrepar de otras pruebas → se exige coincidencia con permutación.

**Externa**
- Una plataforma, 6,5 semanas, 17 documentos (Recall@100 trivial). La insensibilidad a k **no se extrapola**.

**Reproducibilidad**
- Latencias no reproducibles bit a bit; dependencia de `jina-embeddings-v3` con `trust_remote_code` y un shim.

**Ética/privacidad**
- Sin PII en el índice; nombres sintéticos; gazetteer separado; auditoría anti-PII automática.

---

## 18. Qué está desactualizado hoy y qué falta

### 18.1 Bloqueante (depende de ti)
1. **`make extraer`** (tu AWS) → `data/competencias_suid/extraccion_v2/`; luego `make final` → corpus definitivo.
2. Anotación por dos expertos (`experimentos/anotacion/`).
3. Revisar y aprobar las 52 consultas del conjunto difícil y confirmar qué significa «pruebas de caídas».

### 18.2 Estado de los artefactos

| Artefacto | Estado |
|---|---|
| `monografia_buscador_semantico_PRIME.tex` | 🟢 Actualizado el 05-oct: estado del arte, brecha/hipótesis, resultados nuevos, validez, discusión, ética, reproducibilidad, conclusiones, 60 referencias. **32 páginas con estilo de prueba (ver nota)** |
| `EDA_SUID.ipynb` / `EDA_SUID.md` | 🟢 `.md` regenerado (el anterior queda como `.bak_2026-09-23`) |
| `entrega_asesor/` notebooks 00a, 00b | 🟢 sincronizados |
| `entrega_asesor/` notebooks 00c, 01–07 | 🔴 **siguen con cifras viejas**; se reconstruyen tras el corpus definitivo |
| `notebooks/` 01–07, Benchmark_* | 🔴 idem |
| `GUIA_ESTUDIO_BUSCADOR_SEMANTICO.md` | 🔴 pre-auditoría |
| Repo GH Pages | 🔴 pendiente |
| `resultados/*` | 🟢 regenerados |

> **Nota de extensión.** Con el estilo de reemplazo que uso para compilar (márgenes de 2,5 cm), el documento sale en 32 páginas. El límite del reglamento
> de Uninorte es de 30 y la versión PRIME se planeó en ≤ 21. Compila de verdad en Overleaf con `PRIMEarxiv.sty` para ver el número real y, si hace falta recortar,
> las candidatas son: mover «Evidencia cuantitativa» y las tablas de estratos/sensibilidad a un apéndice, y condensar el estado del arte.

### 18.3 Figuras para Overleaf
`Images/output_001.png`, `output_002.png` y `output_008.png` deben **volver a subirse** desde `notebooks/EDA_SUID_archivos/` (regeneradas con el EDA corregido; la
numeración se conserva: 001 ranking, 002 Lorenz, 008 diferencial).

---

## 19. Banco de preguntas del jurado, con respuesta

**1. ¿Por qué no entrenaste un modelo?**
Por el régimen de baja anotación (no hay pares consulta–documento) y porque el aporte buscado es de
*evaluación y caracterización*. RRF no requiere entrenamiento (Proposición 4.1). Los modelos preentrenados
multilingües ya son competitivos fuera de dominio; BEIR muestra que entrenar dentro de dominio no garantiza
generalizar.

**2. ¿Por qué un híbrido y no solo embeddings?**
Los embeddings se diluyen con identificadores, siglas y nombres raros. BM25 es exacto en ellos. Y la
evidencia propia: el híbrido supera a BM25 de forma robusta en los tres conjuntos; frente al denso **no se demuestra** (y en consultas sin
vocabulario común incluso lo lastra). La literatura (BEIR; Luan 2021; Chen 2022) sugiere que la ventaja crece con la diversidad del corpus: se probará con competencias.

**3. ¿Por qué RRF y no una suma ponderada de scores?**
Los scores de BM25 y coseno viven en escalas distintas; ponderarlos exige calibrar un peso, o sea,
etiquetas. RRF usa rangos, es invariante a transformaciones monótonas y no requiere entrenamiento. Costo:
pierde la magnitud de la diferencia (empata "uno excelente + uno regular" con "ambos buenos").
*Seguimiento probable:* Bruch et al. (2024) muestran que la combinación convexa supera a RRF. Respuesta: es cierto, y lo vimos: en el conjunto difícil
el híbrido por RRF queda por debajo del denso (−0,026) porque la lista léxica ruidosa entra a la suma. Pero la convexa exige juicios para calibrar el peso;
con las hojas de anotación (κ) ese es justo el siguiente paso.

**4. ¿Por qué k=60?**
Es el valor estándar de Cormack et al. (2009). No se ajustó para no sobreajustar. **Sí se midió la sensibilidad** (`barridos.py`): para k ≥ 30 los
resultados son idénticos y k=10 cambia una consulta; solo k=1 altera el orden. Cuidado: con 17 documentos los rangos van de 1 a 17, así que k apenas pesa;
no lo extrapoles a un corpus grande.

**5. ¿Qué es Matryoshka y por qué importa?**
Un embedding entrenado para que sus primeras m dimensiones sean un buen embedding. Permite truncar sin
reentrenar y reducir memoria; Uber Eats lo usa (1.536 → 256 con pérdida de 0,002 en recall).

**6. Tus nDCG son 0,95. ¿Es un buen sistema?**
Esa cifra *no es precisión de producción*. Con 17 documentos y consultas derivadas de los mismos documentos
hay un techo. Lo válido es la comparación relativa entre configuraciones bajo el mismo protocolo, que es lo
que una ablación mide.

**7. ¿Por qué el corpus es tan pequeño?**
Porque la v1 cubre los 17 reportes que existen. Es una limitación declarada y la razón del pivote a
competencias, donde hay cientos de documentos reales.

**8. ¿Cómo sabes que tus juicios de relevancia son correctos?**
No lo sé del todo. Son *silver* (el reporte realmente ejecutado) o, en el conjunto difícil, redactados por nosotros. Por eso están preparadas las hojas
de anotación ciega (pooling de 6 sistemas, escala 0/1/2, κ de Cohen ponderado) para 102 consultas; **faltan los anotadores**. Hasta entonces las cifras son
de comparación relativa, no de precisión en producción.

**9. ¿La ontología es realmente una ontología?**
Es un modelo conceptual ligero (13 clases, 20 relaciones) usado como fuente de metadatos. No hay razonador.
El aporte es medir cuándo y cuánto ayuda inyectarla.

**10. ¿Por qué la ontología no salió significativa en el real ampliado?**
Porque las consultas se sintetizan desde los filtros y ya usan el vocabulario del reporte; la ontología
aporta donde hay brecha de vocabulario: en el conjunto difícil sube al denso en +0,122 (robusto), y en el nivel A +0,24. Además en el ampliado hay
solo 13 de 127 pares no nulos. Y un matiz: solo 9 de 17 reportes tienen ontología, lo que perjudica a los demás (−0,161, exploratorio).

**11. ¿Por qué descartas el realce si en un conjunto ayudó?**
Ayudó en el eval real v1 (71), pero ese conjunto tenía pseudo-replicación. Al deduplicar, desaparece. En los tres conjuntos actuales es ≤ 0
(−0,024, −0,016, −0,049) y ningún λ lo salva. El detector (precisión 0,10–0,17, azar ≈ 0,06) explica el mecanismo.

**12. ¿Qué pasó con el 47,5 % de Promoción?**
Fue un artefacto de clasificación: contaba columnas del reporte individual como si fueran promoción. Corregido:
4,2 %. Lo detecté en la auditoría y quedó documentado.

**13. ¿Qué garantiza que no hay fuga entre consultas y documentos?**
Hubo una (el nombre "Andrés Torres" aparecía en los metadatos). Se detectó y se eliminó. El control sin
nombre es la prueba de que el nombre propio ya no influye.

**14. ¿Por qué un Wilcoxon y no un t-test?**
nDCG en known-item es muy asimétrico y pegado a 1; no es normal. Wilcoxon no asume normalidad y es la
práctica común. Se complementa con bootstrap pareado y rank-biserial.
*Pregunta de seguimiento probable:* "Smucker, Allan y Carterette (2007) encontraron que Wilcoxon y la prueba
de signos discrepan de t, bootstrap y permutación". Respuesta honesta: es cierto; por eso el IC bootstrap
acompaña a cada p-valor, y además se corre una **prueba de permutación pareada** (ya implementada en `lib/stats.py`); solo se declaran «robustos»
los efectos en que ambas pruebas rechazan tras Holm.

**15. ¿Y la corrección por comparaciones múltiples?**
Holm sobre una familia de 5 comparaciones por conjunto y estrato. Cambia conclusiones: por ejemplo, "el
realce empeora" deja de ser significativo (p 0,04 → p_Holm 0,165).

**16. ¿Cómo evitas la fuga de privacidad?**
El índice nunca tiene PII; los nombres de evaluación son sintéticos; la resolución de nombres reales va por
un gazetteer separado; una auditoría automática aborta si encuentra emails o teléfonos.

**17. ¿Qué harías con más tiempo?**
(i) Juicios de expertos y κ (hojas ya preparadas); (ii) corpus de competencias con entidades
indexables para contrastar P2 de verdad; (iii) detector de mención para el realce; (iv) un re-ranker
cross-encoder; (v) comparar otros encoders y una fusión convexa frente a RRF; (vi) evaluación con usuarios.

**18. ¿Cuál es tu contribución?**
No es un modelo. Es: (a) la caracterización empírica de las familias de recuperación en un escenario no
cubierto (español, GovTech, entidades, baja anotación); (b) una metodología de evaluación reproducible con
controles (sin nombre, dedupe, Holm) que descubrió que un estrato mal diseñado mide otra cosa; (c) un
framework abierto y un hallazgo de dominio (el vacío de cobertura de competencias).

**19. ¿Funciona en producción?**
No se probó en producción. Los resultados son de laboratorio con juicios silver.

**20. ¿Por qué `jina-embeddings-v3` y no otro?**
Multilingüe con buen soporte de español, Matryoshka nativo, ventana larga (8.192), pesos abiertos y sin
fine-tuning. Alternativas (Qwen3-Embedding, BGE-M3) quedan como comparación futura; el encoder es
enchufable (`config.yaml`).

---

## 20. Chuleta final y glosario

### Cifras vigentes (memorízalas con su contexto)

- **6.620** consultas de datos reales · **Individual 40,4 %** · **top-5 83 %** · **Gini 0,70** (IC 0,65–0,75) · **Promoción 4,2 %**.
- Ontología: **13 clases, 20 relaciones**, cubre **9 de 17** reportes. Corpus v1: **17 docs**, PII=0.
- nDCG@10 C4: **0,948** sintético · **0,960** ampliado · 0,788 difícil (ahí gana C2 con **0,835**). BM25: 0,819 · 0,887 · 0,186 (por construcción).
- **C3>BM25 es robusto en los 3 conjuntos** (+0,073 · +0,056 · +0,500). **C3 vs C1: no se demuestra** (+0,026 · +0,011 · −0,026).
- Ontología sobre el denso: **+0,122** en el difícil (robusto); nula en el ampliado. Reporte objetivo sin enriquecer: **−0,161** (exploratorio).
- Realce: **−0,024 · −0,016 · −0,049**; detector precisión **0,10–0,17**.
- Control sin nombre: entidad_exacta **sube** (C4 0,980 → 1,000).
- Matryoshka: **256 dim ≡ 1024** (ampliado), **−75 %** de índice; codificar la consulta **349 ms**, buscar **0,1 ms**.
- Parámetros: k1=1,5 · b=0,75 · k=60 · λ=0,2 · ε=0,01 · semilla 42 · 1.000 réplicas bootstrap · dim nativa 1.024.
- Pares no nulos de C4 vs C3: **13/127** (ampliado) frente a **34/52** (difícil).

### Glosario

- **ANN / HNSW:** búsqueda aproximada de vecino más cercano; innecesaria a esta escala.
- **Ablación:** quitar o añadir un componente a la vez para medir su efecto.
- **Bi-encoder:** consulta y documento se codifican por separado.
- **Cross-encoder / re-ranker:** procesa consulta y documento juntos; más preciso, más caro.
- **FWER:** probabilidad de al menos un falso positivo en una familia de pruebas.
- **Gazetteer:** diccionario de entidades (nombres propios) con acceso controlado.
- **Gold / silver:** juicio humano experto / juicio derivado automáticamente.
- **Known-item:** cada consulta tiene un objetivo conocido.
- **LoRA (adaptador):** módulo ligero de ajuste; jina-v3 tiene uno por tarea.
- **MRL (Matryoshka):** embeddings truncables por prefijo.
- **Pseudo-replicación:** repetir casi la misma observación como si fueran independientes.
- **qrels:** archivo de juicios de relevancia consulta→documento→grado.
- **RRF:** fusión de rankings por `Σ 1/(k+rank)`.
- **Silver standard:** etiquetas aproximadas de bajo costo.
- **Vacío de cobertura:** demanda cero porque no existe punto de entrada, no porque no importe.
- **Zero-shot:** usar un modelo sin entrenarlo en el dominio objetivo.

### Los tres mensajes que debes dejar

1. **El híbrido supera de forma robusta a la búsqueda léxica**; frente al denso puro la ventaja no se demuestra y puede invertirse sin vocabulario común.
2. **El valor de la ontología depende de cuánto se aleja la consulta del vocabulario del documento y de que cubra todo el corpus**; el realce por entidad, tal como está, no se justifica.
3. **Lo más valioso es la metodología**: encontré mis errores (clasificador del EDA, BM25 con ceros, estrato mal rotulado, fuga de nombre), los corregí, añadí controles (sin nombre, dedupe, Holm, permutación, conjunto difícil) y dejé constancia de qué mide cada estrato.
