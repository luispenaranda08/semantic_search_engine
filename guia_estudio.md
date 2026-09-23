# Guía de Estudio y Exposición — Buscador Semántico GovTech

> Documento privado de estudio y preparación para la sustentación.
> Cubre el proyecto completo hasta el último benchmark: EDA, ontología, propuesta, escalera
> de ablación, diagnóstico del realce, eficiencia (Matryoshka y chunking), validez externa,
> expansión a Competencias, ampliación del poder estadístico y las visualizaciones de
> diagnóstico. Incluye diagramas, el significado de cada métrica con ejemplos numéricos, y una
> parte completa sobre **cómo exponer cada bloque**.
>
> Todas las cifras salen de corridas reproducibles con el codificador `jina-embeddings-v3`.
> Todos los nombres propios que aparecen son **sintéticos**.

**Cómo usar esta guía.** Las Partes I a III sirven para *entender* (léelas completas al menos
una vez). La Parte IV sirve para *exponer* (léela la semana de la sustentación y ensaya con
ella). La Parte V es la chuleta del día: cifras de memoria y glosario.

> Nota sobre los diagramas: están en Mermaid. Se ven renderizados en GitHub, Obsidian,
> Notion, VS Code (con extensión) y en la mayoría de visores de Markdown modernos.

---

## Índice

**Parte I — Entender el proyecto**
1. El problema en una página
2. Mapa del proyecto
3. Conceptos base
4. Los datos y el EDA
5. El corpus y la ontología
6. La arquitectura del sistema
7. La matemática, con intuición
8. La escalera de ablación

**Parte II — Métricas, estadística y protocolo**
9. Las métricas, una por una
10. La estadística que usamos
11. El protocolo de evaluación

**Parte III — Los benchmarks, uno por uno**
12. Mapa de notebooks
13. Benchmark 1 — Escalera sobre el conjunto sintético
14. Benchmark 2 — Estratos y significancia
15. Benchmark 3 — Diagnóstico del realce
16. Benchmark 4 — Matryoshka y chunking
17. Benchmark 5 — Validez externa (Escalera 1)
18. Benchmark 6 — Competencias a escala (Escalera 2)
19. Benchmark 7 — Poder estadístico ampliado
20. Cómo leer cada visualización de diagnóstico
21. Tabla maestra y evolución de la evidencia
22. Las seis preguntas, respondidas
23. Configuración recomendada
24. Limitaciones

**Parte IV — Cómo exponer**
25. Principios de la exposición
26. Estructura sugerida y tiempos
27. Cómo exponer el problema
28. Cómo exponer el EDA
29. Cómo exponer la ontología y el corpus
30. Cómo exponer la propuesta y la matemática
31. Cómo exponer las métricas
32. Cómo exponer los benchmarks
33. Cómo exponer el realce
34. Cómo exponer la estadística y el poder
35. Cómo exponer la eficiencia
36. Cómo exponer Competencias y las escaleras de datos
37. Cómo exponer las limitaciones
38. Cómo cerrar
39. Preguntas probables del comité, con respuesta
40. Guiones hablados (30 segundos y 2 minutos)
41. Errores a evitar
42. Checklist del día

**Parte V — Referencia rápida**
43. Cifras que hay que saber de memoria
44. Glosario

---

# PARTE I — ENTENDER EL PROYECTO

## 1. El problema en una página

Una plataforma de software del Estado gestiona procesos deportivos: deportistas,
instituciones, grupos, eventos, documentos, promociones de etapa. Esa plataforma produce
**reportes** ("promoción de deportistas", "reporte de grupos", "instituciones"…) y los
usuarios tienen que encontrar el reporte correcto para hacer su trabajo.

Encontrarlo es difícil por tres razones concretas:

1. **Desajuste de vocabulario.** El usuario escribe "cómo va el avance de los atletas" y el
   sistema lo llama "reporte de promoción por etapa". Las palabras no coinciden.
2. **Búsqueda por nombre propio.** El usuario busca "promoción de la Liga Atlántico". Aquí la
   coincidencia *exacta* del nombre importa mucho, y los modelos que solo entienden
   "significado" a veces la pierden.
3. **Reportes que no existen como tabla.** El reporte más pedido (promoción, 47,5% de la
   demanda) se reconstruye con cruces cada vez que alguien lo pide. Y hay un dominio entero
   (Competencias) que ni siquiera tiene reporte.

**Objetivo:** un buscador semántico que entienda la intención del usuario y devuelva el
reporte correcto aunque no use las palabras exactas, con especial cuidado en las consultas
por nombre propio.

**Disciplina:** esto es **recuperación de información (IR)**, no clasificación ni predicción.
No entrenamos un modelo; tomamos modelos ya entrenados, los combinamos y los **evaluamos con
rigor**. La contribución del trabajo es de evaluación y caracterización en un escenario que
la literatura no cubre: español, dominio específico, vocabulario normativo, entidades exactas
y casi nada de anotación.

## 2. Mapa del proyecto

```{mermaid}
mindmap
  root((Buscador semántico GovTech))
    Problema
      Desajuste de vocabulario
      Nombre propio
      Reportes que no existen
    Datos
      9.051 consultas reales
      Demanda concentrada Gini 0,74
      Competencias con cero demanda
    Propuesta
      BM25 léxico
      Denso jina-v3
      Ontología 13 clases
      Fusión RRF
      Realce por entidad
    Evaluación
      Escalera de 5 configuraciones
      nDCG MRR Recall P AP
      Wilcoxon Cliff bootstrap
    Benchmarks
      Sintético
      Estratos
      Realce
      Matryoshka y chunking
      Validez externa
      Competencias 833 docs
      Poder estadístico n=55
    Resultado
      Híbrido más ontología
      Embedding a 256 dims
      Sin realce en v1
```

## 3. Conceptos base

**Recuperación léxica (BM25).** Representa consulta y documento como bolsas de palabras y
puntúa por coincidencia de términos, dando más peso a las palabras raras. Rapidísima, no se
entrena y es difícil de superar. Su punto débil: si el usuario y el documento usan palabras
distintas para la misma idea, no los conecta.

**Recuperación densa (embeddings).** Un modelo neuronal convierte cada texto en un vector
de números (un *embedding*) que captura su significado. Textos parecidos quedan cerca en ese
espacio, aunque no compartan palabras. Su punto débil: pierde fuerza en la coincidencia
exacta (nombres propios, códigos).

**Recuperación híbrida.** Usa las dos señales y combina sus listas. Lo léxico es fuerte
donde lo denso es débil, y al revés.

**Ontología.** Un mapa formal del dominio: qué entidades existen (Deportista, Institución,
Disciplina, Fase, Región…), cómo se relacionan y qué sinónimos tienen. La usamos para
**enriquecer** la descripción de cada reporte antes de indexarla.

**Fusión por rango (RRF).** Combina dos listas ordenadas usando solo las *posiciones*, no las
puntuaciones. No necesita entrenamiento ni calibración.

**Ablación.** Experimento donde se enciende un componente a la vez para medir cuánto aporta
cada uno por separado.

## 4. Los datos y el EDA

### 4.1 De dónde salen los datos

Del historial de ejecuciones del *data lake* de la plataforma (AWS Athena/Glue, capas
bronze/silver/gold), en una ventana de **seis semanas y media**. Miramos *qué se preguntó*,
no *qué respondió el sistema*; todo valor identificable se eliminó antes de guardarse.

```{mermaid}
flowchart LR
    A["Historial de Athena<br/>ejecuciones SQL"] --> B["Depurar conteos<br/>de paginación"]
    B --> C["9.051 consultas<br/>de datos reales"]
    C --> D["744 firmas de consulta<br/>694 patrones distintos"]
    D --> E["Rollup a 17<br/>reportes lógicos"]
    E --> F["EDA: demanda,<br/>ranking, Gini"]
    E --> G["Corpus v1<br/>17 reportes"]
    H["Catálogo del lake"] --> I["Dominio Competencias<br/>sin ningún reporte"]
    I --> J["Hallazgo:<br/>vacío de cobertura"]
```

Un detalle técnico que vale la pena contar: la plataforma lanza **dos consultas por página**
de resultados, una que trae los datos y otra que solo cuenta cuántos hay (para paginar).
Contarlas por igual infla la demanda casi al doble. Por eso la unidad del análisis es la
**consulta de datos real**, que descarta las de conteo.

### 4.2 Hallazgo 1 — la demanda está muy concentrada

- **9.051** consultas de datos reales en el periodo.
- El reporte de **promoción de deportistas** explica **≈47,5%** él solo.
- Los **cinco reportes** más pedidos suman el **86%**.
- **Índice de Gini = 0,74** (desigualdad muy marcada; 0 sería reparto igual, 1 sería todo en
  un reporte).

```{mermaid}
pie showData
    title Reparto aproximado de la demanda real
    "Promoción de deportistas" : 47.5
    "Otros 4 reportes del top-5" : 38.5
    "Resto (12 reportes)" : 14
```

**Consecuencia:** primero valor, después escala. La v1 prioriza los reportes que concentran
el uso real.

### 4.3 Hallazgo 2 — preguntas de negocio sin fuente dedicada

El reporte de promoción no está guardado en ninguna tabla. Se reconstruye cruzando datos del
deportista, el registro de promociones y la definición de fases **cada vez** que alguien lo
pide, porque el estado de promoción es el resultado de una lógica de negocio. Es una pregunta
real resuelta al vuelo. Ese patrón se repite en el sistema.

### 4.4 Hallazgo 3 — Competencias: gran volumen, cero demanda

El dominio de competencias (eventos, fases, disciplinas, resultados) **no aparece** en el
historial: cero de las 744 firmas lo toca. No porque nadie lo necesite, sino porque **no
existe la puerta**: ningún reporte lo expone. Su tamaño real:

- **47.635** resultados de competencia.
- **732.640** participaciones de deportista por disciplina.
- **0** consultas registradas.

Un cero así no significa "irrelevante"; significa **vacío de cobertura**. Es la mayor
oportunidad de la Versión 2.

### 4.5 La Prueba Regional: por qué hace falta componer conceptos

La consulta que motivó el proyecto es del tipo *"Atletismo Pre-Juvenil en Región Caribe 1"*.
Esa frase no es un campo del sistema: es la composición de cuatro conceptos que hoy viven en
tablas distintas.

```{mermaid}
flowchart LR
    D["Disciplina<br/>Atletismo"] --> P(("Prueba<br/>Regional"))
    C["Categoría<br/>Pre-Juvenil"] --> P
    F["Fase<br/>regional"] --> P
    R["Región<br/>Caribe 1"] --> P
    P --> Q["Consulta del usuario:<br/>Atletismo Pre-Juvenil<br/>en Región Caribe 1"]
```

Si las preguntas más valiosas se arman componiendo conceptos, un buscador que solo compara
texto contra texto se queda corto. **Por eso hace falta la ontología**: le enseña al sistema
que "Pre-Juvenil" es una categoría y "Caribe 1" una región.

## 5. El corpus y la ontología

### 5.1 Qué indexamos (y qué no)

No indexamos filas de datos (tienen datos personales y son efímeras) ni el volcado de
consultas. Indexamos **descripciones en lenguaje natural de cada reporte**, enriquecidas con
la ontología.

| Campo | Qué es | Quién lo usa |
|---|---|---|
| `descripcion` | Texto base del reporte | Configuraciones **sin** ontología |
| `texto_indexable` | Descripción + serialización de la ontología | Configuraciones **con** ontología |
| `metadatos_ontologia` | Entidades, relaciones, sinónimos, conceptos de búsqueda | Realce y enriquecimiento |
| `nombre_propio_buscable` | Si el reporte se busca por nombre | Realce |
| `prioridad`, `cdr` | Demanda observada | Trazabilidad (no entra al ranking) |

### 5.2 La ontología

**13 clases de negocio y 20 relaciones.** Un fragmento:

```{mermaid}
flowchart LR
    DEP["Deportista"] -- pertenece_a --> GRU["Grupo"]
    DEP -- pertenece_a --> INS["Institución"]
    DEP -- participa_en --> EVE["Evento"]
    DEP -- tiene_estado_de --> PRO["Promoción"]
    DEP -- practica --> DIS["Disciplina"]
    GRU -- compite_en --> EVE
    EVE -- tiene --> FAS["Etapa / Fase"]
    PRO -- habilita_avance_a --> FAS
    INS -- ubicada_en --> UBI["Ubicación / Región"]
    PER["Personal de apoyo"] -- pertenece_a --> GRU
```

Cada clase trae sinónimos ("Deportista" = atleta, competidor, jugador; "Institución" =
colegio, club, escuela…). Esos sinónimos son los que tienden el puente cuando el usuario
escribe con otras palabras.

### 5.3 Privacidad primero

- El índice semántico **nunca** contiene datos personales.
- La resolución de un nombre propio a una persona concreta vive en un **componente aparte con
  control de acceso**.
- Regla del proyecto: los modelos pueden ver nombres reales en uso interno; el documento
  final **jamás** muestra un nombre real. Todo ejemplo público usa nombres sintéticos.

### 5.4 Alcance de la Versión 1

La v1 se limita a los **17 reportes** y la ontología ya definida, con prioridad en los 5 de
mayor demanda (86% del uso). Competencias queda **formalmente fuera** de la v1 y es la
extensión prioritaria de la v2. (Luego lo materializamos como experimento de escala, ver §18,
pero sigue fuera del alcance de *despliegue* de la v1.)

## 6. La arquitectura del sistema

### 6.1 Vista general (fuera de línea y en línea)

```{mermaid}
flowchart TB
    subgraph OFF["Fuera de línea (una vez)"]
        K["Reportes del sistema"] --> O["Enriquecer con ontología<br/>d' = d_desc ⊕ φ(o_d)"]
        O --> I1["Índice invertido<br/>BM25"]
        O --> I2["Índice vectorial<br/>jina-v3 Matryoshka"]
    end
    subgraph ON["En línea (cada consulta)"]
        Q["Consulta del usuario"] --> L["Vista léxica BM25"]
        Q --> DN["Vista densa"]
        Q --> DET["Detector de entidades"]
        L --> RRF["Fusión RRF"]
        DN --> RRF
        DET -. opcional .-> RE["Realce por entidad"]
        RRF --> RE
        RE --> OUT["Ranking de reportes"]
    end
    I1 -.-> L
    I2 -.-> DN
```

### 6.2 Qué pasa con una consulta, paso a paso

```{mermaid}
sequenceDiagram
    participant U as Usuario
    participant S as Buscador
    participant B as BM25
    participant E as Encoder denso
    participant F as Fusión RRF
    U->>S: "estado de promoción del deportista Andrés Torres"
    S->>B: buscar por términos
    B-->>S: lista ordenada léxica
    S->>E: codificar consulta y comparar por coseno
    E-->>S: lista ordenada semántica
    S->>F: fusionar por posiciones (k=60)
    F-->>S: ranking fusionado
    S-->>U: 1. Reporte de Promoción de Deportistas
```

## 7. La matemática, con intuición

Para cada fórmula: primero la intuición, luego la fórmula.

**Documento enriquecido.** *Intuición:* pegarle a la descripción de cada reporte un resumen
de lo que la ontología sabe de él.

```
d' = d_desc ⊕ φ(o_d)
```

`φ(o_d)` serializa un subconjunto *selectivo* de metadatos (entidades, sinónimos, conceptos
de búsqueda) y `⊕` es concatenar. Selectivo importa: volcar todos los atributos rinde peor.

**BM25.** *Intuición:* suma, término a término, cuánto aparece la palabra en el documento,
dando más peso a palabras raras y penalizando documentos muy largos.

```
s_BM25(q,d') = Σ_{t∈q} IDF(t) · f(t,d')·(k1+1) / ( f(t,d') + k1·(1 − b + b·|d'|/avg_dl) )
```

Usamos `k1 = 1,5` y `b = 0,75` (estándar), con analizador en español (minúsculas, sin
tildes, sin palabras vacías).

**Denso.** *Intuición:* qué tan "apuntados en la misma dirección" están los vectores de la
consulta y del documento.

```
s_dense(q,d') = ⟨ f_θ(q), f_θ(d') ⟩      (vectores normalizados → coseno)
```

**Matryoshka.** *Intuición:* el modelo guarda lo más importante en las primeras dimensiones,
así que se puede "recortar" el vector sin reentrenar.

```
s_dense^(m)(q,d') = ⟨ τ_m f_θ(q), τ_m f_θ(d') ⟩,   m ∈ {128, 256, 512, 768, 1024}
```

**RRF.** *Intuición:* cada lista vota por sus documentos; estar arriba en una lista da muchos
puntos, estar abajo da pocos; se suman los votos.

```
s_RRF(q,d') = Σ_{r∈{BM25,denso}} 1 / (k + rank_r(q,d')),   k = 60
```

Ejemplo: un documento en posición 1 de BM25 y posición 3 del denso recibe
`1/61 + 1/63 ≈ 0,0164 + 0,0159 = 0,0323`. Como solo usa posiciones, no hay que calibrar
escalas entre BM25 (puntajes sin techo) y coseno (entre −1 y 1).

**Realce suave.** *Intuición:* si la consulta menciona una entidad que el documento cubre,
darle un empujón pequeño.

```
s_final(q,d') = s_RRF(q,d') · (1 + λ · 1_entidad(q,d')),   λ ∈ [0,1 , 0,3]
```

## 8. La escalera de ablación

```{mermaid}
flowchart LR
    B0["BM25 solo<br/>referencia léxica"]
    C1["C1<br/>Denso puro"] -- "+ ontología" --> C2["C2<br/>Denso + ontología"]
    C1 -- "+ BM25 (fusión)" --> C3["C3<br/>Híbrido<br/>BASE CRÍTICA"]
    C3 -- "+ ontología" --> C4["C4<br/>Híbrido + ontología"]
    C4 -- "+ realce" --> C5["C5<br/>Híbrido + ontología + realce"]
```

| # | Configuración | Qué aísla | Pregunta |
|---|---|---|---|
| — | BM25 solo | Referencia léxica pura | P1 |
| C1 | Denso puro | Línea base neuronal | P1, P2 |
| C2 | Denso + ontología | Efecto de la ontología sobre el denso | P3 |
| C3 | Híbrido sin ontología | Aporte de fusionar lo léxico (**base crítica**) | P1, P2 |
| C4 | Híbrido + ontología | Efecto de la ontología sobre el híbrido | P3 |
| C5 | Híbrido + ontología + realce | Efecto del realce | P5 |

Comparaciones que importan: **C1→C2** y **C3→C4** (ontología), **BM25/C1→C3** (fusión),
**C4→C5** (realce). P4 (chunking) y P6 (dimensión) son barridos **ortogonales** sobre C4.

---

# PARTE II — MÉTRICAS, ESTADÍSTICA Y PROTOCOLO

## 9. Las métricas, una por una

Todas miran dos cosas: el **ranking** (lista ordenada que devuelve el sistema) y los
**juicios de relevancia** (qué documento es el correcto para cada consulta, con un grado:
2 = objetivo, 1 = relacionado, 0 = irrelevante). En todas, **1,0 es el óptimo**.

```{mermaid}
flowchart TD
    Q{"¿Qué quiero saber?"}
    Q --> A["¿Está arriba el correcto,<br/>y qué tan arriba?"] --> A1["nDCG@10 (principal)"]
    Q --> B["¿En qué posición aparece<br/>el primer acierto?"] --> B1["MRR@10"]
    Q --> C["¿Lo encontró aunque<br/>sea mal ordenado?"] --> C1["Recall@100"]
    Q --> D["¿Cuánta de la pantalla<br/>es útil?"] --> D1["Precision@10"]
    Q --> E["¿Está bien ordenado<br/>todo el ranking?"] --> E1["AP@100"]
    Q --> F["¿En qué profundidad<br/>aparece el objetivo?"] --> F1["Success@k"]
```

### 9.1 nDCG@10 — la métrica principal

**Qué mide.** Si los documentos relevantes aparecen en el top-10 **y qué tan arriba**.
- *Cumulative Gain*: suma la relevancia de lo que aparece.
- *Discounted*: un acierto abajo vale menos (se divide por `log2(posición + 1)`).
- *Normalized*: se divide por el mejor orden posible, para que quede entre 0 y 1.

```
DCG@k  = Σ_{i=1..k} (2^rel_i − 1) / log2(i + 1)
nDCG@k = DCG@k / IDCG@k
```

**Ejemplo 1 (un solo relevante, grado 2).** El objetivo está en la posición 3.
DCG = (2² − 1)/log2(4) = 3/2 = 1,5. IDCG (objetivo en posición 1) = 3/1 = 3.
**nDCG@10 = 0,5.**

**Tabla clave para exponer — qué nDCG da cada posición del objetivo (un relevante):**

| Posición del objetivo | nDCG@10 | MRR@10 |
|---|---|---|
| 1 | 1,000 | 1,000 |
| 2 | 0,631 | 0,500 |
| 3 | 0,500 | 0,333 |
| 5 | 0,387 | 0,200 |
| 10 | 0,289 | 0,100 |
| > 10 | 0 | 0 |

Con esta tabla se traduce cualquier cifra: un **nDCG@10 medio de 0,936** significa que en la
gran mayoría de consultas el reporte correcto sale **primero**, y en unas pocas sale segundo o
tercero.

**Ejemplo 2 (relevancia graduada).** Juicios: A = 2, B = 1. Ranking: [B, X, A].
DCG = (2¹−1)/log2(2) + (2²−1)/log2(4) = 1 + 1,5 = 2,5.
IDCG (orden ideal [A, B]) = 3/1 + 1/log2(3) = 3 + 0,631 = 3,631.
**nDCG@10 = 0,689.**

**Por qué es la principal.** El usuario mira las primeras respuestas; la posición importa
tanto como el acierto, y la relevancia graduada distingue el reporte exacto de uno solo
relacionado.

**Trampa típica.** Leerla como "porcentaje de aciertos". No lo es: es calidad de orden.

### 9.2 MRR@10 — Mean Reciprocal Rank

**Qué mide.** El inverso de la posición del **primer** relevante, promediado entre consultas.

```
MRR@k = (1/|Q|) · Σ_q 1 / rank_q      (0 si no aparece en el top-k)
```

**Lectura.** 1,0 = el objetivo siempre en la posición 1; 0,5 = en promedio en la 2.

**Por qué importa aquí.** Con un objetivo por consulta (*known-item*), MRR mide directamente
el objetivo de negocio: poner el reporte correcto **primero**.

**Diferencia con nDCG** en nuestro protocolo: ambos dependen solo de la posición del único
relevante, pero MRR castiga más fuerte (1/2 en la posición 2) que nDCG (0,631). Por eso MRR
siempre sale igual o más bajo.

### 9.3 Recall@100 — cobertura

**Qué mide.** Qué fracción de los relevantes aparece en los primeros 100.

```
Recall@k = |relevantes ∩ top-k| / |relevantes|
```

**Por qué importa.** Separa "no lo encontró" de "lo encontró pero lo ordenó mal". Es la
garantía de que la primera etapa no pierde el documento correcto.

**Trampa crítica.** Con **17 documentos** el top-100 los contiene a todos, así que
Recall@100 = 1,0 **siempre**, para cualquier sistema. No discrimina. Solo se vuelve
informativo con el corpus ampliado a **833 documentos**, donde el denso puro baja a
**0,950–0,958** (§18, §19).

### 9.4 Precision@10 — densidad de aciertos

**Qué mide.** Qué fracción del top-10 es relevante.

```
P@k = |relevantes ∩ top-k| / k
```

**Trampa.** Con un solo relevante por consulta, el máximo posible es **1/10 = 0,1**. Ver
P@10 ≈ 0,117 no es "malo": es el techo del protocolo (algunas consultas tienen un segundo
relevante de grado 1). Es métrica secundaria.

### 9.5 AP@100 — Average Precision

**Qué mide.** El promedio de la precisión en cada posición donde aparece un relevante, hasta
100. Es la base de MAP.

```
AP@k = (1 / min(|rel|, k)) · Σ_{i=1..k} 1[rel_i > 0] · P@i
```

**Ejemplo.** Un relevante en la posición 3 → AP = P@3 = 1/3 = 0,333 (igual que MRR cuando
hay un solo relevante).

**Por qué importa.** Resume el orden **completo**, no solo el primer acierto. Brilla cuando
hay varios relevantes por consulta (lo que tendremos con la capa gold).

### 9.6 Success@k — cobertura acumulada

**Qué mide.** La fracción de consultas cuyo objetivo aparece dentro del top-k.
Success@1 = porcentaje de consultas con el correcto en primer lugar.

**Por qué la usamos.** Bajo *known-item* es la curva de cobertura más clara: responde "¿a qué
profundidad encuentra el usuario lo que busca?". Lo que importa es el **arranque** (k = 1–3).

### 9.7 Resumen

| Métrica | Pregunta | Rango | En nuestro caso |
|---|---|---|---|
| nDCG@10 | ¿Está arriba y qué tan arriba? | 0–1 | **Principal** |
| MRR@10 | ¿Posición del primer acierto? | 0–1 | Objetivo de negocio directo |
| Recall@100 | ¿Lo encontró? | 0–1 | Trivial con 17 docs; útil con 833 |
| P@10 | ¿Qué tanto del top-10 sirve? | 0–1 | Techo ≈ 0,1 por el protocolo |
| AP@100 | ¿Todo el orden es bueno? | 0–1 | ≈ MRR con un relevante |
| Success@k | ¿A qué profundidad aparece? | 0–1 | Mejor curva de cobertura |

## 10. La estadística que usamos

### 10.1 p-valor, en una frase

La probabilidad de ver una diferencia **al menos así de grande** si en realidad las dos
configuraciones fueran iguales. p < 0,05 se considera evidencia suficiente. Un p grande **no**
prueba que sean iguales; dice que con esta muestra no alcanza para afirmarlo.

### 10.2 Wilcoxon pareado

Compara dos configuraciones **consulta por consulta** (pareado: la misma consulta evaluada
con ambas). Es no paramétrico: no asume normalidad, algo apropiado porque nDCG está acotado y
suele amontonarse cerca de 1.

### 10.3 Tamaño del efecto: Cliff's δ

Mide *cuánto* gana una sobre otra, no solo si gana. Va de −1 a 1.
Umbrales: < 0,147 insignificante · < 0,33 pequeño · < 0,474 mediano · ≥ 0,474 grande.

### 10.4 Intervalos por bootstrap

Remuestreamos las consultas con reemplazo 1.000–2.000 veces y recalculamos la media cada vez.
El 95% central de esas medias es el intervalo de confianza. Si el intervalo de una diferencia
**cruza el cero**, la diferencia no es concluyente.

### 10.5 Poder estadístico y el problema del n pequeño

El **poder** es la capacidad de detectar un efecto que sí existe. Depende sobre todo del
tamaño muestral. Con **n = 17** consultas en el estrato clave, efectos reales y consistentes
daban p ≈ 0,07: no por falta de efecto, sino por falta de muestra.

### 10.6 Pseudo-replicación (clave para defender el notebook 07)

```{mermaid}
flowchart LR
    subgraph MAL["Pseudo-replicación (lo que NO hay que hacer)"]
        P1["1 patrón real de filtro"] --> V1["variante con<br/>nombre sintético A"]
        P1 --> V2["variante con<br/>nombre sintético B"]
        P1 --> V3["variante con<br/>nombre sintético C"]
        V1 & V2 & V3 --> X["n inflado,<br/>observaciones casi idénticas"]
    end
    subgraph BIEN["Unidad correcta"]
        Q1["patrón real 1"] --> Y["n honesto:<br/>1 consulta por patrón distinto"]
        Q2["patrón real 2"] --> Y
        Q3["patrón real 3"] --> Y
    end
```

Repetir el mismo patrón con distintos nombres sintéticos **infla el n sin añadir información**,
porque el nombre sintético no aparece en ningún documento: el sistema devuelve casi lo mismo.
Eso viola el supuesto de independencia de Wilcoxon. La solución fue usar el **patrón real
distinto** como unidad (§19).

## 11. El protocolo de evaluación

### 11.1 ¿Hubo entrenamiento y prueba?

**No, y es correcto.** Esto es IR:
- `jina-embeddings-v3` está **preentrenado y congelado**: solo inferencia.
- BM25 **no se entrena**.
- **No hay partición train/test**: el corpus es el índice y las consultas son el conjunto de
  evaluación; nada aprende de ellas.
- Hiperparámetros estándar de la literatura (`k1`, `b`, `k`, `λ`), no ajustados a los datos.

### 11.2 Los tres tipos de juicio

```{mermaid}
flowchart LR
    KI["Known-item sintético<br/>consultas inventadas<br/>desde los documentos"] --> SI["Silver<br/>firma real del log:<br/>el reporte que se ejecutó"]
    SI --> GO["Gold<br/>anotación de expertos<br/>0-3, doble, κ de Cohen"]
    KI -. "v1: compara<br/>configuraciones" .-> R1["validez relativa"]
    SI -. "E1: uso real" .-> R2["validez externa parcial"]
    GO -. "siguiente paso" .-> R3["validez externa plena"]
```

- **Known-item sintético** (v1): cada consulta se arma desde títulos, entidades y sinónimos y
  apunta a un reporte conocido (grado 2). Limitación: comparte vocabulario con los documentos,
  así que el valor absoluto está optimista. Vale para comparar configuraciones.
- **Silver** (Escalera 1): cada firma real del log apunta al reporte que de verdad ejecutó.
  El texto de la consulta se sintetiza desde los filtros reales (la plataforma no tiene caja de
  búsqueda que registre texto libre).
- **Gold** (pendiente): una muestra de 50 consultas ya marcada para anotación experta.

### 11.3 Estratos de consulta

| Estrato | Qué es | Ejemplo sintético |
|---|---|---|
| entidad exacta | Menciona nombre propio o filtra por persona/institución | "estado de promoción del deportista Andrés Torres" |
| ambigua | Término corto con varias lecturas | "grupos" |
| documento largo | Necesidad descrita en frase larga | "quiero ver en qué etapa está cada deportista…" |
| operacional | Tema + filtros reales del log | "promoción de deportistas por categoría, por etapa" |
| competencias | Pregunta sobre pruebas regionales | "Atletismo Pre Juvenil en Región Caribe 1" |

---

# PARTE III — LOS BENCHMARKS, UNO POR UNO

## 12. Mapa de notebooks

| Notebook | Qué contiene | Preguntas |
|---|---|---|
| `EDA_SUID.ipynb` | Demanda, ranking, Gini, Competencias | Motivación |
| `Exploracion_Ontologia_Metadatos_SUID.ipynb` | Ontología, entidades, nombre propio | Diseño |
| `Benchmark_Escalera_Ablacion.ipynb` | Escalera completa, estadística, visualizaciones | P1, P2, P3, P5 |
| `Benchmark_Matryoshka_P6.ipynb` | Barrido de dimensión | P6 |
| `01_Analisis_por_Estratos_y_Estadistica.ipynb` | Tablas por estrato, Wilcoxon, Cliff, IC | P1, P2, P3 |
| `02_Diagnostico_Realce_Entidad.ipynb` | Detector, barrido de λ, variantes | P5 |
| `03_Matryoshka_y_Chunking_P4_P6.ipynb` | Dimensión y fragmentación | P4, P6 |
| `04_Resumen_Ejecutivo_y_Roadmap_v2.ipynb` | Resumen, plan v2, texto para LaTeX | Cierre |
| `05_Evaluacion_Validez_Externa.ipynb` | Conjunto real silver (71) | Validez externa |
| `06_Expansion_Corpus_Competencias.ipynb` | Prueba Regional, 833 docs | Escala, P3 |
| `07_Poder_Estadistico_Eval_Ampliado.ipynb` | n=55 en entidad exacta, 833 docs | Poder |

```{mermaid}
flowchart TD
    EDA["EDA + Ontología"] --> ESC["Benchmark_Escalera_Ablacion<br/>sintético, 17 docs"]
    ESC --> N01["01 Estratos + estadística"]
    ESC --> N02["02 Diagnóstico del realce"]
    ESC --> N03["03 Matryoshka + chunking"]
    N01 & N02 & N03 --> N04["04 Resumen y roadmap"]
    N04 --> N05["05 Validez externa<br/>Escalera 1, silver"]
    N04 --> N06["06 Competencias<br/>Escalera 2, 833 docs"]
    N05 & N06 --> N07["07 Poder estadístico<br/>n=55, 161 consultas"]
```

Los notebooks de benchmark (`Benchmark_Escalera_Ablacion`, `01`, `05`, `06`) incluyen al
final el bloque **"Visualizaciones de diagnóstico"** (barras con IC, boxplot/violín, Success@k
con Precision@k y Recall@k, y scatter de score vs relevancia). Se explica cómo leerlas en §20.

## 13. Benchmark 1 — Escalera sobre el conjunto sintético

**Setup.** 17 reportes, 51 consultas sintéticas (17 entidad exacta, 13 ambigua, 10 documento
largo, 11 competencias). Las 11 de competencias no tienen objetivo en la v1 (vacío de
cobertura) y se excluyen: quedan **40 con juicio**.

**Resultados globales:**

| Configuración | nDCG@10 | MRR@10 | Recall@100 | P@10 | AP@100 | Latencia p50 |
|---|---|---|---|---|---|---|
| BM25 | 0,843 | 0,836 | 1,000 | 0,113 | 0,807 | < 1 ms |
| C1 Denso puro | 0,874 | 0,843 | 1,000 | 0,117 | 0,827 | 22,5 ms |
| C2 Denso + ontología | 0,917 | 0,898 | 1,000 | 0,117 | 0,888 | 22,2 ms |
| C3 Híbrido | 0,878 | 0,863 | 1,000 | 0,117 | 0,842 | 22,1 ms |
| **C4 Híbrido + ontología** | **0,936** | **0,925** | 1,000 | 0,117 | **0,910** | 22,1 ms |
| C5 + realce | 0,911 | 0,894 | 1,000 | 0,117 | 0,880 | 22,9 ms |

```{mermaid}
xychart-beta
    title "nDCG@10 global — conjunto sintético (17 docs)"
    x-axis ["BM25", "C1", "C2", "C3", "C4", "C5"]
    y-axis "nDCG@10" 0.8 --> 1.0
    bar [0.843, 0.874, 0.917, 0.878, 0.936, 0.911]
```

**Por estrato (nDCG@10):**

| Configuración | entidad exacta | ambigua | documento largo |
|---|---|---|---|
| BM25 | 0,866 | 0,781 | 0,884 |
| C1 | 0,861 | 0,919 | 0,837 |
| C2 | 0,927 | **0,928** | 0,888 |
| C3 | 0,900 | 0,835 | **0,896** |
| **C4** | **0,976** | 0,923 | 0,884 |
| C5 | 0,957 | 0,923 | 0,819 |

**Lectura.**
- El denso supera a BM25 (0,874 vs 0,843): la señal semántica aporta.
- La ontología sube tanto al denso (+0,043) como al híbrido (+0,058).
- El híbrido con ontología llega a **0,976** en entidad exacta: la ventaja se concentra ahí.
- En ambiguas mandan las configuraciones con señal densa (BM25 cae a 0,781).
- La latencia densa (~22 ms) está dominada por **codificar la consulta**, no por buscar.

## 14. Benchmark 2 — Estratos y significancia (notebook 01)

**Wilcoxon pareado en entidad exacta (n = 17):**

| Comparación | Δ nDCG@10 | p-valor | Pregunta |
|---|---|---|---|
| C3 vs BM25 | +0,034 | 0,068 | P1 |
| C3 vs C1 | +0,039 | 0,917 | P1, P2 |
| C4 vs C3 | **+0,076** | 0,068 | P3 |
| C5 vs C3 | +0,057 | 0,345 | P3, P5 |

**Lectura.** El mayor efecto es la ontología (C4 vs C3). Los p-valores rozan 0,05 porque
**n = 17 es poco**: el efecto es consistente en dirección, pero la muestra no alcanza para
cerrarlo. Esto motivó directamente el Benchmark 7.

## 15. Benchmark 3 — Diagnóstico del realce (notebook 02)

**El síntoma.** Añadir el realce baja el nDCG@10 global de 0,936 a 0,911, y en entidad exacta
de 0,976 a 0,957.

**El diagnóstico.** Tratamos la indicadora de entidad como un clasificador sobre pares
(consulta, documento), donde la etiqueta ideal es "este es el objetivo":

| TP | FP | FN | Precisión | Recall | F1 |
|---|---|---|---|---|---|
| 16 | 111 | 1 | **0,126** | 0,941 | 0,222 |

Se activa en promedio para **7,5 de 17 documentos por consulta**.

```{mermaid}
flowchart TD
    Q["Consulta con nombre propio"] --> D{"Detector"}
    D --> R1["Regla 1: la clase de la consulta<br/>coincide con el documento"]
    D --> R2["Regla 2: consulta con nombre propio<br/>Y documento marcado como buscable"]
    R2 --> G["Se activa para TODOS<br/>los reportes de nombre propio"]
    G --> M["El factor (1 + λ) multiplica<br/>a un grupo entero por igual"]
    M --> N["No reordena a favor del correcto;<br/>a veces sube un distractor"]
```

**Barrido de λ (realce original):**

| λ | nDCG@10 global | nDCG@10 entidad exacta |
|---|---|---|
| 0 (= C4) | **0,936** | **0,976** |
| 0,05 | 0,918 | 0,964 |
| 0,10 | 0,913 | 0,960 |
| 0,15 | 0,912 | 0,958 |
| 0,20 | 0,911 | 0,957 |
| 0,30 | 0,911 | 0,957 |

Cualquier λ > 0 empeora, y el daño crece con λ. Dos variantes más estrictas (V1 solo
coincidencia de clase; V2 ponderada por especificidad) degradan menos pero **no superan a "sin
realce"**.

**Lectura honesta de todos los benchmarks sobre el realce** (se resume en §21): perjudica en el
sintético, ayudó en el conjunto real de 71 consultas, y resultó neutro o levemente negativo en
el conjunto ampliado de mayor poder. Es **inestable**. Conclusión: no va por defecto en la v1;
queda para v2 con un detector que reconozca la *mención* concreta y no un atributo genérico.

## 16. Benchmark 4 — Matryoshka y chunking (notebooks 03 y Benchmark_Matryoshka_P6)

### 16.1 Matryoshka (P6)

| Dimensión m | nDCG@10 C4 | nDCG@10 C1 denso | Retención C4 | Ahorro de índice |
|---|---|---|---|---|
| 128 | 0,908 | 0,811 | 0,970 | 87,5% |
| **256** | **0,936** | 0,857 | **1,000** | **75,0%** |
| 512 | 0,933 | 0,882 | 0,998 | 50,0% |
| 768 | 0,934 | 0,889 | 0,998 | 25,0% |
| 1024 | 0,936 | 0,874 | 1,000 | 0% |

```{mermaid}
xychart-beta
    title "Retención de nDCG@10 (C4) vs dimensión"
    x-axis ["128", "256", "512", "768", "1024"]
    y-axis "retención" 0.9 --> 1.01
    line [0.970, 1.000, 0.998, 0.998, 1.000]
```

**Lectura.** Truncar a **256** dimensiones deja la calidad intacta con **75% menos índice**.
El denso puro es más sensible a la compresión que el híbrido: la señal léxica amortigua la
pérdida de dimensión. Replica sobre nuestro corpus lo que reporta Uber Eats (1536 → 256 con
caída de recall ≈ 0,002).

### 16.2 Chunking (P4)

Reportes de 65 a 184 palabras. Se parte cada uno en fragmentos (con solapamiento) y el
documento toma el mejor fragmento (agregación por máximo). Sobre C4:

| Tamaño (palabras) | Frag./doc | 0% solape | 25% | 50% |
|---|---|---|---|---|
| 24 | 4,71 | 0,868 | 0,827 | 0,833 |
| 40 | 2,94 | 0,834 | 0,827 | 0,865 |
| 64 | 2,12 | 0,894 | 0,890 | 0,873 |
| 128 | 1,24 | 0,934 | 0,913 | 0,930 |
| Documento completo | 1,00 | **0,936** | 0,936 | 0,936 |

**Lectura.** Nunca supera al documento completo. Con documentos cortos, partir solo quita
contexto. **Unidad de indexación de la v1: el reporte completo.** La maquinaria queda lista
para documentos largos en la v2.

## 17. Benchmark 5 — Validez externa, Escalera 1 (notebook 05)

**Qué se hizo.** Se convirtieron las **firmas reales** del log en consultas: cada firma
apunta al reporte que ejecutó (silver, grado 2) y su texto se sintetiza desde los filtros
reales que usó. Muestreo estratificado, no proporcional. **71 consultas** (30 entidad exacta,
29 operacional, 8 ambigua, 4 documento largo), corpus de 17 reportes.

| Configuración | nDCG@10 |
|---|---|
| BM25 | 0,925 |
| C1 | 0,948 |
| C2 | 0,951 |
| C3 | 0,946 |
| C4 | 0,952 |
| **C5** | **0,973** |

**Lectura.** La jerarquía general se sostiene con consultas de uso real. El realce, que
empeoraba en el sintético, aquí sube (0,952 → 0,973). **Advertencia que luego se confirmó:**
las 30 de entidad exacta se habían generado repitiendo patrones con distintos nombres
sintéticos (pseudo-replicación), así que este conjunto sobrerrepresenta ese caso. El Benchmark
7 lo corrige.

## 18. Benchmark 6 — Competencias a escala, Escalera 2 (notebook 06)

**Qué se hizo.** Se materializó la **Prueba Regional** = disciplina × categoría × fase ×
región, desde los catálogos del lake: **816 documentos** (102 disciplinas × 8 regiones), mismo
esquema del corpus, volúmenes solo como conteos agregados. Corpus total: **833 documentos**.
Se añadieron 25 consultas de competencias con objetivo real (96 en total).

```{mermaid}
flowchart LR
    CAT["Catálogo de disciplinas<br/>102 deporte × categoría"] --> PR["Generador de<br/>Pruebas Regionales"]
    REG["Departamento → región<br/>8 regiones"] --> PR
    CNT["Conteos agregados<br/>sin datos personales"] --> PR
    PR --> DOC["816 documentos<br/>mismo esquema del corpus"]
    DOC --> COMB["Corpus combinado<br/>17 + 816 = 833"]
```

| Configuración | nDCG@10 | Recall@100 |
|---|---|---|
| BM25 | 0,890 | 1,000 |
| C1 Denso puro | 0,840 | **0,958** |
| C2 | 0,905 | 1,000 |
| C3 | 0,896 | 1,000 |
| C4 | 0,929 | 1,000 |
| C5 | 0,941 | 1,000 |

**Por estrato (nDCG@10):**

| Config. | entidad exacta | ambigua | competencias | operacional |
|---|---|---|---|---|
| BM25 | 0,951 | 0,954 | 0,770 | 0,899 |
| C1 | 0,783 | 0,661 | 0,847 | 0,919 |
| C2 | 0,888 | 0,750 | **0,866** | 0,987 |
| C3 | 0,919 | 0,852 | 0,815 | 0,941 |
| C4 | 0,926 | 0,917 | 0,859 | 0,987 |
| C5 | **0,963** | 0,917 | 0,859 | 0,987 |

**Lectura.**
- **Recall@100 dejó de ser trivial:** el denso puro pierde documentos relevantes del top-100.
- El denso puro **colapsa** en entidad exacta (0,783) y en ambiguas (0,661) cuando hay cientos
  de distractores.
- En competencias gana **denso + ontología** (0,866): el dominio construido por composición
  ontológica es la prueba más dura de P3, y la ontología la pasa.

## 19. Benchmark 7 — Poder estadístico ampliado (notebook 07)

### 19.1 El diagnóstico

- n = 17 en el estrato clave era poco.
- El n = 30 del Benchmark 5 estaba **inflado por pseudo-replicación** (§10.6).
- En el log hay **101 patrones distintos** con columna de nombre propio (promoción 48,
  documentación 25, individuales 12, personal 8, grupos 6, participación 2).

### 19.2 El diseño

Unidad de muestreo = **patrón de firma real distinto** (reporte × combinación de filtros).
Cupos por estrato, tope de 18 patrones por reporte en entidad exacta (para que promoción no
lo llene todo), texto sintetizado desde todos los filtros reales del patrón.

```{mermaid}
flowchart LR
    LOG["744 firmas"] --> PAT["694 patrones distintos"]
    PAT --> EE["entidad exacta: 101 disponibles → 55"]
    PAT --> OP["operacional: 283 → 35"]
    PAT --> DL["documento largo: 217 → 25"]
    PAT --> AM["ambigua: 93 → 14"]
    EE & OP & DL & AM --> SET["129 consultas silver<br/>50 marcadas gold_candidate"]
    SET --> PAPER["versión _paper<br/>sin PII"]
```

### 19.3 Escenario A — 17 reportes, 129 consultas

| Configuración | nDCG@10 global | nDCG@10 entidad exacta |
|---|---|---|
| BM25 | 0,880 | 0,864 |
| C1 | 0,951 | 0,948 |
| **C2** | **0,967** | **0,983** |
| C3 | 0,924 | 0,914 |
| C4 | 0,949 | 0,936 |
| C5 | 0,938 | 0,936 |

**Wilcoxon en entidad exacta, antes y ahora:**

| Comparación | Δ (n=55) | p (n=17) | **p (n=55)** |
|---|---|---|---|
| C3 vs BM25 (P1) | +0,050 | 0,068 | **0,011** |
| C4 vs C3 (P3) | +0,022 | 0,068 | 0,653 |
| C4 vs C1 | −0,012 | — | 0,541 |
| C5 vs C4 (P5) | 0,000 | — | sin diferencia |

**Lectura.**
- **P1 queda confirmado con significancia:** el híbrido supera a BM25 en entidad exacta
  (p ≈ 0,01). El poder subió y la conclusión aguantó.
- El aporte **marginal** de la ontología sobre el híbrido **no** es significativo con consultas
  reales. Sí ayuda sobre el denso (C2 es la mejor en el corpus pequeño).
- El realce es neutro.

### 19.4 Escenario B — 833 documentos, 161 consultas (incluye 32 de competencias)

| Configuración | nDCG@10 | Recall@100 |
|---|---|---|
| BM25 | 0,867 | 0,963 |
| C1 Denso puro | 0,826 | **0,950** |
| C2 | 0,918 | 1,000 |
| C3 | 0,877 | 0,963 |
| **C4** | **0,948** | 1,000 |
| C5 | 0,942 | 1,000 |

Entidad exacta: C4 0,976 · C2 0,933 · C1 0,762. Competencias: C4 0,868 · C2 0,852 · C1 0,849 ·
BM25 0,799.

**La lectura que une los dos escenarios:**

```{mermaid}
flowchart LR
    S["Corpus pequeño<br/>17 reportes"] --> S1["Denso + ontología basta<br/>C2 lidera"]
    L["Corpus a escala<br/>833 documentos"] --> L1["Híbrido + ontología lidera<br/>C4 = 0,948"]
    L --> L2["Denso puro se degrada<br/>0,826 y pierde recall"]
    S1 & L1 & L2 --> K["El valor de la señal léxica<br/>crece con el tamaño del corpus"]
```

## 20. Cómo leer cada visualización de diagnóstico

Están al final de `Benchmark_Escalera_Ablacion`, `01`, `05` y `06`.

**Barras con IC95 bootstrap (nDCG@10, MRR@10, Recall@100).** Altura = media; bigotes =
intervalo. Si los bigotes de dos configuraciones se solapan mucho, la diferencia no es
concluyente por sí sola. *Qué decir:* "C4 lidera y es la única, junto a las que llevan
ontología, que mantiene cobertura completa a escala."

**Boxplot y violín de nDCG@10 por consulta.** La caja es el 50% central; la línea, la mediana;
el triángulo, la media; los puntos sueltos, consultas atípicas. El violín muestra dónde se
concentran. *Qué decir:* "No solo promedia más alto: es más estable, con menos consultas
fallidas en la cola."

**Success@k.** Eje x = profundidad; eje y = fracción de consultas resueltas. Todas llegan a
1,0 si k crece; lo que importa es **el arranque**. *Qué decir:* "Con C4 el usuario encuentra
el reporte en el primer resultado más veces."

**Precision@k y Recall@k.** Precision cae con k por diseño (techo 1/k con un relevante);
se compara entre curvas, no en absoluto. Recall sube; la curva que sube antes es mejor.

**Curva Precisión–Cobertura (notebook de la escalera y 07).** Con un relevante por consulta
degenera en un escalón; su área resume lo mismo que MRR. Se vuelve plenamente útil con la capa
gold (varios relevantes graduados).

**Scatter de score semántico vs relevancia (+ histograma).** Cada punto es un par (consulta,
documento) del top-20 del denso con ontología. Si los relevantes quedan más arriba (mayor
coseno), el embedding captura la señal correcta. El solapamiento en la zona media explica por
qué el denso solo no basta. *Qué decir:* "El coseno sí separa relevantes de no relevantes; lo
que queda en la zona gris lo resuelven la señal léxica y la ontología."

**Heatmap por estrato (notebooks 01, 06, escalera).** Filas = configuraciones, columnas =
estratos. Sirve para ubicar dónde gana o pierde cada pieza.

## 21. Tabla maestra y evolución de la evidencia

| Escenario | Docs | Consultas | Mejor nDCG@10 | Denso puro | Recall@100 denso | Realce vs C4 |
|---|---|---|---|---|---|---|
| Sintético (escalera) | 17 | 40 | C4 0,936 | 0,874 | 1,000 | peor (0,911) |
| Real silver (E1) | 17 | 71 | C5 0,973 | 0,948 | 1,000 | mejor (0,973 vs 0,952) |
| Real + Competencias (E2) | 833 | 96 | C5 0,941 | 0,840 | 0,958 | mejor (0,941 vs 0,929) |
| Real ampliado (07-A) | 17 | 129 | C2 0,967 | 0,951 | 1,000 | peor (0,938 vs 0,949) |
| Real ampliado + Comp. (07-B) | 833 | 161 | C4 0,948 | 0,826 | 0,950 | peor (0,942 vs 0,948) |

```{mermaid}
timeline
    title Cómo cambió la evidencia al subir el rigor
    Sintético 17 docs : C4 gana 0,936 : ontología con p≈0,07 : realce empeora
    Real silver 71 : jerarquía se sostiene : realce parece ayudar : n inflado por pseudo-replicación
    833 docs : Recall ya discrimina : denso puro pierde documentos : ontología gana en Competencias
    Ampliado n=55 : P1 significativo p≈0,01 : ontología sobre híbrido no significativa : realce neutro
    Ampliado a escala : C4 gana 0,948 : el valor del híbrido crece con el corpus
```

**Lo que se mantuvo en todos los escenarios:** la ontología nunca empeora y casi siempre
mejora; el denso puro es la configuración más frágil a escala; el híbrido supera a BM25.

**Lo que cambió:** la magnitud del aporte de la ontología sobre el híbrido (grande en el
sintético, no significativo con consultas reales) y el signo del realce (inestable).

Esta evolución **es un resultado**, no un problema: muestra que las conclusiones se
sometieron a pruebas cada vez más exigentes y que se reportan con honestidad.

## 22. Las seis preguntas, respondidas

- **P1 — ¿El híbrido supera a BM25 y al denso?** Sí. A BM25 con significancia en entidad
  exacta (p ≈ 0,011, n = 55). Al denso puro, sobre todo a escala: con 833 documentos el denso
  cae a 0,826 y pierde recall; el híbrido con ontología llega a 0,948 con recall completo.
- **P2 — ¿La ventaja se concentra en nombre propio?** Sí. Entidad exacta es donde el denso
  puro más se derrumba (0,762–0,783 a escala) y donde el híbrido con ontología llega más alto
  (0,976).
- **P3 — ¿Aporta la ontología?** Sí, de forma consistente sobre el denso y máxima en
  Competencias. Su aporte marginal sobre el híbrido fue grande en el sintético pero no
  significativo con consultas reales: se reporta así.
- **P4 — ¿Importa el tamaño de fragmento?** No con documentos cortos; el reporte completo es la
  mejor unidad en la v1.
- **P5 — ¿Ayuda el realce?** Resultado inestable entre conjuntos y detector de precisión 0,126.
  No va por defecto en la v1.
- **P6 — ¿Mejor equilibrio?** Híbrido + ontología con el embedding a **256 dimensiones**:
  misma calidad, 75% menos índice. A esta escala basta búsqueda exacta por coseno; con miles de
  documentos se migraría a un índice aproximado (HNSW).

## 23. Configuración recomendada

```{mermaid}
flowchart TD
    A{"¿Corpus de despliegue?"} -->|"crece a cientos o miles"| B["Híbrido + ontología (C4)"]
    A -->|"solo 17 reportes"| C["C2 compite,<br/>pero C4 escala mejor"]
    C --> B
    B --> D{"¿Memoria ajustada?"}
    D -->|"sí o no"| E["Embedding truncado a 256 dims<br/>retención 1,0, −75% índice"]
    E --> F{"¿Activar realce?"}
    F -->|"v1"| G["No: resultado inestable,<br/>detector de baja precisión"]
    F -->|"v2"| H["Reconsiderar con detector<br/>de mención de alta precisión"]
    G --> Z["Configuración v1:<br/>C4 + 256 dims + sin realce<br/>+ coseno exacto"]
```

**Justificación en una frase:** C4 es la que gana a la escala donde el sistema va a vivir, no
pierde cobertura, y la truncación a 256 dimensiones sale gratis en calidad.

## 24. Limitaciones

1. **Juicios silver, no gold.** Heredan el reporte que ejecutó cada firma; aproximan la
   intención del usuario pero no la garantizan. Falta la anotación experta (50 consultas ya
   marcadas).
2. **Texto de consulta sintetizado** desde la estructura de filtros, porque la plataforma
   genera reportes por SQL dinámico y no registra una caja de búsqueda con texto libre.
3. **Corpus de reportes pequeño (17).** La parte de Competencias lo lleva a 833, pero los
   documentos de Competencias vienen de un catálogo compuesto, no de reportes existentes.
4. **Protocolo known-item** en la v1: el valor absoluto de las métricas está optimista.
5. **Sin señal de producción** (clics, reformulaciones, A/B): queda fuera de un proyecto de
   grado.

---

# PARTE IV — CÓMO EXPONER

## 25. Principios de la exposición

1. **Una idea por diapositiva.** Si una diapositiva necesita dos titulares, son dos
   diapositivas.
2. **El titular dice la conclusión**, no el tema. No "Resultados globales", sino "El híbrido
   con ontología recupera el reporte correcto primero en casi todas las consultas".
3. **Intuición antes que fórmula.** Primero qué hace, luego cómo se escribe.
4. **Cada número con su traducción.** "0,936, es decir, el reporte correcto sale primero en la
   gran mayoría de consultas."
5. **Las limitaciones las dices tú antes de que te las pregunten.** Suma credibilidad.
6. **Cuenta la historia de rigor creciente**: sintético → real → escala → poder. Es la columna
   vertebral del trabajo.
7. **Nunca un nombre real** en diapositivas, capturas o ejemplos.

## 26. Estructura sugerida y tiempos (≈ 20 minutos)

```{mermaid}
flowchart LR
    A["1 Título<br/>0:30"] --> B["2 Problema<br/>1:30"] --> C["3 Por qué es difícil<br/>1:00"]
    C --> D["4 EDA demanda<br/>1:30"] --> E["5 EDA Competencias<br/>1:30"]
    E --> F["6 Propuesta<br/>2:00"] --> G["7 Escalera<br/>1:00"] --> H["8 Métricas<br/>1:30"]
    H --> I["9 Resultados<br/>2:00"] --> J["10 Realce<br/>1:00"] --> K["11 Validez y poder<br/>2:00"]
    K --> L["12 Escala<br/>1:30"] --> M["13 Eficiencia<br/>1:00"] --> N["14 Limitaciones<br/>1:00"] --> O["15 Cierre<br/>1:00"]
```

| # | Diapositiva | Titular sugerido | Visual |
|---|---|---|---|
| 1 | Título | Buscadores semánticos para conocimiento funcional GovTech | — |
| 2 | Problema | Los usuarios no encuentran el reporte que necesitan | Ejemplo de consulta que falla |
| 3 | Por qué es difícil | Vocabulario distinto, nombres propios, reportes que no existen | 3 íconos |
| 4 | EDA demanda | Cinco reportes concentran el 86% de la demanda real | Curva de Lorenz / ranking |
| 5 | EDA Competencias | Un dominio con 732.640 registros tiene cero consultas | Mapeo diferencial |
| 6 | Propuesta | Combinamos léxico, semántica y ontología | Diagrama de arquitectura |
| 7 | Escalera | Encendemos un componente a la vez para medir su aporte | Diagrama de la escalera |
| 8 | Métricas | nDCG@10 mide si el correcto sale arriba | Tabla posición → nDCG |
| 9 | Resultados | Híbrido + ontología: 0,936 y 0,976 en nombre propio | Barras con IC |
| 10 | Realce | El realce no ayuda: su detector acierta 1 de cada 8 veces | Barrido de λ |
| 11 | Validez y poder | Con consultas reales y n=55, P1 pasa a ser significativo | Tabla p antes/ahora |
| 12 | Escala | A 833 documentos el denso puro pierde reportes; el híbrido no | Recall@100 |
| 13 | Eficiencia | 256 dimensiones bastan: misma calidad, 75% menos memoria | Curva Matryoshka |
| 14 | Limitaciones | Lo que este trabajo todavía no puede afirmar | Lista breve |
| 15 | Cierre | Recomendación v1 y camino a v2 | Configuración recomendada |

**Diapositivas de respaldo (backup)** para preguntas: fórmulas completas, tabla por estrato,
diagnóstico del detector (TP/FP/FN), chunking, pseudo-replicación, lista de notebooks.

## 27. Cómo exponer el problema

**Objetivo:** que el comité sienta el dolor en 60 segundos.

**Guion:**
> "Imaginen que trabajan en una plataforma del Estado y necesitan saber en qué etapa va cada
> deportista. Escriben 'avance de los atletas'. El sistema lo llama 'reporte de promoción por
> etapa'. No lo encuentran. O buscan por el nombre de una institución y el sistema no sabe que
> eso es una institución. Y hay preguntas que ni siquiera tienen un reporte donde vivir. Eso es
> lo que resuelve este trabajo."

**Qué mostrar:** un ejemplo concreto de consulta y el reporte que debería salir.
**Qué evitar:** empezar por la tecnología ("usamos embeddings…"). Primero el problema.

## 28. Cómo exponer el EDA

**Objetivo:** mostrar que las decisiones de diseño salen de datos, no de intuición.

**Estructura en tres golpes:**
1. **La unidad correcta.** "La plataforma cuenta dos veces cada página; depuramos eso y
   quedaron 9.051 consultas reales." (Muestra rigor.)
2. **La concentración.** "Un reporte es casi la mitad de la demanda, cinco son el 86%, Gini de
   0,74. Por eso priorizamos esos cinco." (Muestra criterio.)
3. **El vacío.** "Pero hay un dominio con 732.640 participaciones y cero consultas. No es que
   nadie lo quiera: es que no hay puerta." (Es el giro de la historia.)

**Frase puente a la propuesta:**
> "Las preguntas más valiosas se arman componiendo conceptos: disciplina, categoría, fase y
> región. Un buscador que solo compara palabras no puede componer. Por eso necesitamos una
> ontología."

**Visuales:** ranking de demanda, curva de Lorenz, mapeo diferencial, diagrama de la Prueba
Regional.
**Trampa a evitar:** mostrar muchas gráficas del EDA. Tres bastan: concentración, Lorenz,
Competencias.
**Pregunta que suele venir:** "¿Por qué el cero no significa baja relevancia?" → "Porque no
existe ningún reporte que exponga ese dominio; nadie puede pedirlo. Es cobertura, no demanda."

## 29. Cómo exponer la ontología y el corpus

**Mensaje:** "No indexamos datos de personas; indexamos descripciones de reportes enriquecidas
con lo que la ontología sabe de ellos."

**Pasos:**
1. Muestra el fragmento del mapa de entidades (Deportista → Grupo → Institución…).
2. Muestra un reporte antes y después del enriquecimiento (descripción vs `texto_indexable`).
3. Remata con privacidad: "El índice nunca ve un dato personal; la resolución de nombres vive
   aparte, con control de acceso."

**Qué evitar:** recorrer las 13 clases y 20 relaciones. Muestra 5 o 6.

## 30. Cómo exponer la propuesta y la matemática

**Regla:** en la diapositiva principal **no hay fórmulas**, hay el diagrama de arquitectura.
Las fórmulas van en backup o en una sola diapositiva con intuición al lado.

**Orden de explicación:**
1. "Dos formas de buscar: por palabras (BM25) y por significado (embeddings)."
2. "Cada una falla donde la otra acierta, así que las combinamos."
3. "Las combinamos por posiciones (RRF): no hay que entrenar nada ni calibrar escalas."
4. "Antes de indexar, le pegamos a cada reporte lo que la ontología sabe de él."
5. "Y probamos un empujón extra cuando la consulta menciona una entidad."

**Si piden la fórmula de RRF:** escríbela y da el ejemplo numérico (posición 1 y 3 →
1/61 + 1/63 ≈ 0,032). Enfatiza "solo posiciones, por eso no necesita entrenamiento".

**Si piden Matryoshka:** "El modelo guarda lo más importante en las primeras dimensiones, como
muñecas rusas; puedo recortar el vector sin reentrenar."

## 31. Cómo exponer las métricas

**Objetivo:** que el comité pueda leer tus números solo.

**Guion para nDCG@10:**
> "Nuestra métrica principal es nDCG@10. Mide si el reporte correcto aparece en los diez
> primeros y qué tan arriba. Vale 1 si sale primero, 0,63 si sale segundo, 0,5 si sale
> tercero. Entonces, cuando digo 0,936, significa que el reporte correcto sale primero en casi
> todas las consultas."

**La diapositiva ideal:** la tabla "posición del objetivo → nDCG → MRR" (§9.1). Es la que más
ayuda a traducir.

**Cómo presentar el resto en una línea cada una:**
- MRR@10: "La posición del primer acierto; es el objetivo de negocio directo."
- Recall@100: "Si lo encontró aunque sea abajo. Con 17 documentos siempre da 1; por eso
  ampliamos a 833, donde sí discrimina."
- P@10: "Techo de 0,1 por diseño: hay un solo reporte correcto por consulta."
- AP@100: "Calidad del orden completo; se volverá útil con varios relevantes."

**Anticípate:** "¿Por qué no accuracy?" → "Porque el problema no es acertar sí o no, sino
ordenar: el usuario ve una lista."

## 32. Cómo exponer los benchmarks

**La idea que organiza todo:** la escalera de ablación. Preséntala como un experimento
controlado: "Encendemos un componente a la vez; así sabemos cuánto aporta cada uno."

**Secuencia narrativa (la historia de rigor creciente):**
1. **Sintético (17 docs):** "Primer resultado: híbrido + ontología gana, 0,936; en nombre
   propio, 0,976."
2. **Estratos:** "La ventaja se concentra en nombre propio. Pero con 17 consultas los
   p-valores rondan 0,07."
3. **Validez externa:** "¿Y con consultas reales? Construimos consultas desde el log real."
4. **Escala:** "¿Y si el corpus crece? Materializamos Competencias: 833 documentos."
5. **Poder:** "Subimos el n a 55 sin trampas estadísticas. P1 pasa a ser significativo."

**Cómo presentar cada tabla:** nunca la leas completa. Señala **una fila y una columna**:
"Miren esta celda: 0,976, híbrido + ontología en nombre propio. Es la cifra más alta de toda
la tabla."

**Cómo presentar las gráficas de diagnóstico:** una sola diapositiva con barras con IC y, si
hay tiempo, el boxplot. Frase: "No solo promedia más alto; es más estable consulta a consulta."

## 33. Cómo exponer el realce

**Es tu mejor momento de honestidad científica; aprovéchalo.**

**Guion:**
> "El realce debía ayudar en nombre propio, y en el primer experimento empeoró. En lugar de
> esconderlo, lo diagnosticamos: tratamos el detector como un clasificador. Acierta cuándo
> debe activarse el 94% de las veces, pero de cada ocho activaciones solo una cae sobre el
> reporte correcto: precisión de 0,13. Se enciende para siete documentos por consulta a la
> vez, así que no distingue. Probamos pesos más pequeños y dos variantes más estrictas; ninguna
> supera a no usarlo. Con consultas reales el resultado fue inestable. Por eso no va en la v1."

**Visual:** barrido de λ (la línea que baja desde λ = 0) o la tabla TP/FP/FN.
**Mensaje de fondo:** "Medimos antes de agregar complejidad."

## 34. Cómo exponer la estadística y el poder

**Objetivo:** mostrar que sabes lo que significa un p-valor y que no inflaste la muestra.

**Guion:**
> "Con 17 consultas en nombre propio, los efectos eran consistentes pero los p-valores
> quedaban en 0,07. La tentación era repetir consultas cambiando el nombre sintético, pero eso
> es pseudo-replicación: el sistema devuelve lo mismo y solo inflas el n. Lo que hicimos fue
> usar los 101 patrones reales distintos del log como unidad. Con n = 55, el híbrido frente a
> BM25 pasa a p = 0,011. Y también fuimos honestos: el aporte extra de la ontología sobre el
> híbrido, con consultas reales, no es significativo."

**Visual:** tabla de p-valores antes/ahora (§19.3).
**Si preguntan por Wilcoxon:** "Prueba pareada no paramétrica; comparo las dos configuraciones
sobre la misma consulta y no asumo normalidad, porque nDCG se amontona cerca de 1."
**Si preguntan por el tamaño del efecto:** "Reportamos Cliff's δ e intervalos por bootstrap
junto al p-valor, para no depender solo de él."

## 35. Cómo exponer la eficiencia

**Guion:**
> "¿Cuánto cuesta? Con Matryoshka puedo recortar el vector de 1024 a 256 dimensiones: la
> calidad queda idéntica y el índice ocupa 75% menos. Y partir los reportes en fragmentos no
> ayuda, porque son cortos: el reporte completo es la mejor unidad."

**Visual:** curva de retención vs dimensión.
**Dato de contexto:** la latencia (~22 ms) la domina codificar la consulta, no buscar.

## 36. Cómo exponer Competencias y las escaleras de datos

**Mensaje:** "Competencias pasa de ser un hallazgo del EDA a un dominio que el buscador puede
recuperar."

**Guion:**
> "Materializamos la Prueba Regional componiendo disciplina, categoría y región: 816
> documentos nuevos, sin un solo dato personal. Con 833 documentos pasa algo que con 17 era
> imposible de ver: el recuperador denso puro empieza a perder reportes del top-100, y el
> híbrido no. Y en Competencias, que es un dominio construido desde la ontología, la ontología
> es lo que más ayuda."

**Visual:** Recall@100 por configuración a 833 documentos.
**Cuida el alcance:** "Esto es un experimento de escala; el despliegue de Competencias es la
v2."

## 37. Cómo exponer las limitaciones

**Regla:** 4 bullets, dichos con calma, seguidos de qué haría para resolver cada uno.

| Limitación | Cómo decirla | Qué sigue |
|---|---|---|
| Juicios silver | "Asumen que el reporte ejecutado era el que se quería." | Anotación gold de 50 consultas ya marcadas |
| Texto sintetizado | "No hay caja de búsqueda; reconstruimos la consulta desde sus filtros." | Logs de la interfaz si se habilitan |
| Corpus pequeño | "17 reportes; Competencias lo lleva a 833." | Corpus v2 de producción |
| Sin producción | "No hay clics ni A/B." | Shadow test offline; A/B fuera de alcance |

## 38. Cómo cerrar

**Tres frases:**
1. "La combinación de búsqueda léxica, semántica y ontología recupera el reporte correcto
   primero en casi todas las consultas, y es la única que no pierde cobertura a escala."
2. "La v1 queda así: híbrido con ontología, vector de 256 dimensiones, sin realce."
3. "La v2 abre Competencias, el dominio que hoy nadie puede consultar."

**Última diapositiva:** la configuración recomendada y el camino a v2. Nada más.

## 39. Preguntas probables del comité, con respuesta

1. **¿Por qué no entrenaron un modelo?** Porque no hay anotación para hacerlo bien y porque
   la pregunta es de evaluación: qué combinación de modelos existentes funciona en este
   dominio. Un fine-tuning sin datos suficientes sobreajusta.
2. **¿No es circular evaluar con consultas derivadas de los documentos?** En la v1 sí hay ese
   sesgo y lo declaramos: por eso leemos el sintético en términos relativos. Luego construimos
   consultas desde el log real (silver) para romper esa circularidad.
3. **¿Cómo construyeron consultas "reales" si no hay caja de búsqueda?** Desde las firmas del
   SQL real: sabemos qué reporte se pidió y con qué filtros; sintetizamos el texto desde esos
   filtros. Es la aproximación más fiel disponible.
4. **¿Por qué confiar en juicios silver?** Porque son una señal de uso real: el usuario lanzó
   esa consulta y obtuvo ese reporte. Pero pueden no reflejar la intención; por eso marcamos 50
   para anotación gold.
5. **¿Por qué el aporte de la ontología no es significativo en el conjunto ampliado?** Sobre
   el híbrido, con consultas reales, el efecto marginal es pequeño (+0,022). La ontología sí
   ayuda de forma clara sobre el denso y en Competencias. Reportamos lo que salió.
6. **¿Por qué el realce empeora?** Su detector tiene precisión 0,126: se activa para 7,5
   reportes por consulta y no distingue el correcto.
7. **¿Qué es la pseudo-replicación?** Contar como observaciones independientes varias
   versiones casi idénticas de la misma. Infla el n y los p-valores salen engañosamente bajos.
8. **¿Por qué Recall@100 es 1,0?** Porque con 17 documentos el top-100 los contiene a todos.
   Con 833 deja de serlo (denso puro 0,950).
9. **¿Por qué jina-embeddings-v3?** Multilingüe (español), abierto, 1024 dimensiones con
   Matryoshka nativo, lo que permite estudiar P6 sin reentrenar.
10. **¿Por qué RRF y por qué k = 60?** Porque combina por posiciones, sin entrenar ni calibrar;
    k = 60 es la constante estándar de la literatura y no la ajustamos a los datos.
11. **¿Cómo garantizan privacidad?** El índice solo tiene descripciones de reportes; la
    resolución de nombres vive aparte con control de acceso; las firmas del log traen nombres
    de columna, no valores; todo ejemplo público usa nombres sintéticos.
12. **¿Qué pasa si el corpus crece a miles?** Se migra la búsqueda exacta por coseno a un
    índice aproximado (HNSW) y la truncación a 256 dimensiones gana aún más valor en memoria.
    Nuestros resultados a 833 docs sugieren que el híbrido se vuelve más necesario.
13. **¿Por qué no un re-ranker o un LLM?** Porque primero había que establecer qué recupera
    bien la primera etapa. El re-ranking queda como peldaño futuro evaluado con el mismo
    protocolo.
14. **¿Por qué Competencias está fuera de la v1 si es tan importante?** Porque exige materializar
    una entidad nueva y la v1 prioriza el 86% de la demanda actual. Lo materializamos como
    experimento de escala y es la prioridad de la v2.
15. **¿Cuál es el aporte original?** La evaluación rigurosa de estas familias en un escenario
    que la literatura no cubre (español, dominio GovTech, entidades exactas, sin anotación),
    la materialización de la Prueba Regional y un marco de evaluación reproducible.
16. **¿Por qué la mejor configuración cambia entre escenarios?** Porque depende del tamaño del
    corpus: con 17 reportes la señal léxica aporta poco; con 833 se vuelve necesaria. Es un
    hallazgo, no una contradicción.
17. **¿Por qué 256 dimensiones y no 128?** 256 retiene el 100% de la calidad; 128 retiene el
    97%. Por 8 KiB extra en este corpus, no vale la pena perder calidad.
18. **¿Qué harías distinto?** Arrancaría antes la anotación gold y pediría logs de la interfaz
    de búsqueda para tener texto libre real.
19. **¿Es generalizable a otras plataformas?** El método sí (corpus de descripciones +
    ontología + escalera de ablación); los números son de este dominio.
20. **¿Cuánto tarda una consulta?** Unos 22 ms en la mediana, casi todo en codificar la
    consulta.

## 40. Guiones hablados

**30 segundos (ascensor):**
> "Los usuarios de una plataforma deportiva del Estado no encuentran el reporte que necesitan
> porque buscan con otras palabras o por nombre propio. Construí y evalué un buscador que
> combina búsqueda por palabras, por significado y una ontología del dominio. Recupera el
> reporte correcto primero en casi todas las consultas, no pierde cobertura cuando el corpus
> crece, y con un vector cuatro veces más pequeño mantiene la misma calidad."

**2 minutos:**
> "El problema es de recuperación de información: los usuarios escriben con palabras
> distintas a las del sistema, o buscan por nombre propio, y además hay preguntas de negocio
> que no tienen reporte. Analicé 9.051 consultas reales: cinco reportes concentran el 86% de la
> demanda, y un dominio entero, Competencias, tiene cero consultas porque no existe la puerta.
>
> Propuse un recuperador híbrido: BM25 para lo exacto, embeddings para el significado, fusión
> por posiciones y una ontología que enriquece cada reporte. Lo evalué con una escalera de
> ablación que enciende un componente a la vez.
>
> Resultado: el híbrido con ontología llega a 0,936 de nDCG@10 y 0,976 en consultas de nombre
> propio. El realce por entidad no ayudó: su detector tiene precisión de 0,13. Después subí el
> rigor: consultas construidas desde el log real, 55 consultas de nombre propio sin
> pseudo-replicación, y un corpus de 833 documentos con Competencias. Con eso la ventaja del
> híbrido sobre BM25 pasa a ser significativa, y a escala el denso puro pierde reportes
> mientras el híbrido no. Con 256 dimensiones la calidad no cambia y el índice baja 75%.
>
> La recomendación para la v1 es híbrido con ontología, 256 dimensiones, sin realce. La v2
> abre Competencias."

## 41. Errores a evitar

- Leer las tablas completas en voz alta.
- Decir "accuracy" o "porcentaje de acierto" para nDCG.
- Presentar 0,936 como "precisión en producción".
- Esconder el realce o el resultado no significativo de la ontología sobre el híbrido.
- Decir que "Competencias no se usa" (lo correcto: no se *puede* consultar).
- Mostrar nombres reales en cualquier captura.
- Decir "entrenamos el modelo" (no se entrenó nada).
- Sobrecargar la diapositiva de propuesta con fórmulas.
- Afirmar que el realce "no sirve nunca" (lo correcto: inestable con este detector).

## 42. Checklist del día

- [ ] Sé de memoria las cifras de la §43.
- [ ] Puedo explicar nDCG con la tabla de posiciones sin mirar.
- [ ] Puedo explicar RRF con el ejemplo 1/61 + 1/63.
- [ ] Puedo explicar pseudo-replicación en 20 segundos.
- [ ] Tengo backup con fórmulas, tabla por estrato, TP/FP/FN, chunking y lista de notebooks.
- [ ] Revisé que ninguna diapositiva muestre un nombre real.
- [ ] Ensayé los guiones de 30 s y 2 min.
- [ ] Cronometré la exposición completa (≤ 20 min).
- [ ] Tengo los notebooks abiertos por si piden ver código o una gráfica.

---

# PARTE V — REFERENCIA RÁPIDA

## 43. Cifras que hay que saber de memoria

**Datos**
- 9.051 consultas de datos reales · 6,5 semanas
- Promoción ≈ 47,5% · Top-5 = 86% · Gini = 0,74
- Competencias: 47.635 resultados · 732.640 participaciones · 0 consultas
- 744 firmas · 694 patrones distintos · 101 con nombre propio
- Ontología: 13 clases · 20 relaciones
- Corpus v1: 17 reportes · Competencias: 816 Pruebas Regionales · Total: 833

**Modelo y parámetros**
- `jina-embeddings-v3` · 1024 dims · congelado
- BM25 k1 = 1,5 · b = 0,75 · RRF k = 60 · realce λ = 0,2

**Resultados clave**
- Sintético: C4 = 0,936 global · 0,976 entidad exacta
- Realce: 0,936 → 0,911 · detector precisión 0,126 · recall 0,941 · 7,5 docs/consulta
- Matryoshka: 256 dims → retención 1,000 · −75% índice
- Chunking: nunca supera al documento completo
- 833 docs: denso puro Recall@100 = 0,950–0,958 · C4 = 0,948
- Poder: n entidad exacta 17 → 55 · C3 vs BM25 p = 0,068 → **0,011**
- C4 vs C3 con consultas reales: Δ = +0,022, p = 0,65 (no significativo)
- Latencia p50 ≈ 22 ms

**Recomendación v1:** híbrido + ontología · 256 dims · sin realce · coseno exacto

## 44. Glosario

- **Ablación:** encender un componente a la vez para medir su aporte aislado.
- **AP / MAP:** precisión promedio en las posiciones de los relevantes (y su media).
- **BM25:** método léxico que puntúa por coincidencia de términos ponderada.
- **Bootstrap:** remuestreo con reemplazo para estimar intervalos de confianza.
- **Cliff's δ:** tamaño del efecto no paramétrico entre −1 y 1.
- **Coseno:** cercanía entre dos vectores normalizados.
- **Denso / embedding:** vector numérico que representa el significado de un texto.
- **Estrato:** tipo de consulta (entidad exacta, ambigua, documento largo, operacional, competencias).
- **Firma de consulta:** estructura de un SQL real del log (reporte, tablas, filtros).
- **Gold / silver:** juicios de expertos / juicios automáticos derivados del uso real.
- **HNSW:** índice aproximado de vecinos cercanos para corpus grandes.
- **IR:** recuperación de información.
- **Known-item:** protocolo con un documento objetivo conocido por consulta.
- **Matryoshka (MRL):** entrenamiento que permite truncar el vector sin reentrenar.
- **MRR:** inverso de la posición del primer acierto, promediado.
- **nDCG:** ganancia acumulada descontada por posición y normalizada.
- **Ontología:** mapa formal de entidades, relaciones y sinónimos del dominio.
- **p-valor:** probabilidad de ver esa diferencia si no hubiera diferencia real.
- **Poder estadístico:** capacidad de detectar un efecto que existe.
- **Precision@k / Recall@k:** fracción útil del top-k / fracción de relevantes en el top-k.
- **Prueba Regional:** entidad compuesta disciplina × categoría × fase × región.
- **Pseudo-replicación:** tratar como independientes observaciones casi idénticas.
- **Realce:** empujón multiplicativo cuando consulta y documento comparten entidad.
- **RRF:** fusión de rankings por posiciones.
- **Success@k:** fracción de consultas con el objetivo en el top-k.
- **Vacío de cobertura:** dominio con datos pero sin reporte que lo exponga.
- **Wilcoxon pareado:** prueba no paramétrica que compara dos sistemas consulta por consulta.

---

*Guía de estudio y exposición — actualizada tras el notebook 07 y la integración de las
visualizaciones de diagnóstico. Cifras reproducibles con `jina-embeddings-v3`. Todos los
nombres propios de los ejemplos son sintéticos.*
