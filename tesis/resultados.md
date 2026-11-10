# Resultados

Todas las cifras son nDCG@10 salvo que se indique otra métrica. Cada tabla dice sobre qué
corpus se midió, porque la conclusión sobre la fusión cambia con el corpus.

## Diecisiete reportes

| Configuración | Sintético ($n=40$) | Ampliado ($n=127$) | Difícil A ($n=52$) | Difícil B ($n=78$) |
|---|---|---|---|---|
| BM25 | 0,819 | 0,887 | 0,186 | 0,422 |
| C1 · Denso | 0,866 | 0,932 | 0,712 | 0,783 |
| C2 · Denso + ontología | 0,931 | 0,928 | **0,835** | **0,837** |
| C3 · Híbrido | 0,893 | 0,943 | 0,686 | 0,778 |
| C4 · Híbrido + ontología | **0,948** | **0,960** | 0,788 | 0,835 |
| C5 · C4 + realce | 0,924 | 0,944 | 0,739 | 0,773 |

El híbrido supera a BM25 en todos los conjuntos, pero casi toda la ventaja viene del denso. En
las paráfrasis (difíciles A y B) la ontología es lo que más aporta, y el realce empeora el orden.
Con diecisiete reportes ninguna fusión alternativa supera a RRF de forma concordante.

```{figure} ../figuras/fig_escalera_global.png
:width: 100%

nDCG@10 de las seis configuraciones en los cuatro conjuntos del corpus de diecisiete reportes.
```

```{figure} ../figuras/fig_forest.png
:width: 100%

Diferencia de cada peldaño con su intervalo del 95 % (10.000 remuestreos). Relleno: comparación concordante (Wilcoxon y permutación tras Holm).
```

```{figure} ../figuras/fig_dificil.png
:width: 100%

nDCG@10 por nivel de solape léxico en los difíciles A y B: con puente, sin puente y con solape.
```

## Corpus definitivo: 177 documentos

| Configuración | Global ($n=180$) | Recall@100 | Competencias | Difíciles A+B |
|---|---|---|---|---|
| BM25 | 0,774 | 0,928 | 0,899 | 0,251 |
| C1 · Denso | 0,865 | 0,994 | 0,951 | 0,503 |
| C2 · Denso + ontología | 0,910 | 1,000 | 0,954 | **0,652** |
| C3 · Híbrido | 0,868 | 0,967 | 0,961 | 0,398 |
| C4 · Híbrido + ontología | **0,960** | 1,000 | **0,973** | 0,590 |

Con $160$ Pruebas Regionales compitiendo, el híbrido sin ontología queda por debajo del denso en
las paráfrasis ($-0{,}104$, concordante): RRF promueve documentos que solo comparten palabras
genéricas con la consulta.

```{figure} ../figuras/fig_posiciones.png
:width: 100%

Posición del primer documento relevante en las 180 consultas del corpus definitivo.
```

## Corpus v3: 811 documentos de cinco tipos

| Grupo | $n$ | C2 | C4 | Convexa |
|---|---|---|---|---|
| Reportes | 127 | 0,759 | 0,841 | **0,904** |
| Pruebas regionales | 53 | 0,954 | **0,970** | 0,967 |
| Funcionalidades | 53 | **0,654** | 0,417 | 0,634 |
| Pruebas del catálogo | 60 | 0,836 | 0,917 | **0,953** |
| Reglas de participación | 27 | 0,926 | 0,443 | **0,940** |
| Difíciles A+B | 130 | 0,496 | 0,555 | **0,594** |
| **Total** | 450 | 0,714 | 0,710 | **0,799** |

Ninguna configuración fija de la escalera domina: C4 gana donde la consulta comparte vocabulario
con el documento, y C2 donde no. La convexa supera a C4 ($+0{,}089$) y a C2 ($+0{,}085$) de forma
concordante y no pierde en ningún grupo de forma significativa.

```{figure} ../figuras/fig_v3.png
:width: 100%

Diferencia C4 − C2 por tipo de consulta en el corpus v3, con intervalo por objetivo.
```

## Registro completo: ontología frente a controles

Validación con los $757.554$ documentos en el índice denso. Solo cambia el texto de los $811$
documentos evaluados; los controles tienen la misma longitud en subpalabras que el texto con
ontología.

| Texto de los documentos v3 | BM25 | Denso | RRF | Convexa |
|---|---|---|---|---|
| Descripción original | 0,138 | 0,426 | 0,294 | 0,413 |
| Repetición | 0,182 | 0,405 | 0,348 | 0,417 |
| Vecinos por TF-IDF | 0,134 | 0,374 | 0,285 | 0,366 |
| Metadatos planos | 0,255 | 0,433 | 0,400 | 0,454 |
| **Ontología** | **0,299** | **0,484** | **0,439** | **0,533** |

Los doce contrastes de la ontología contra las cuatro alternativas (en denso, RRF y convexa) son
concordantes tras Holm. El menos firme es RRF frente a metadatos planos ($+0{,}039$), cuyo
intervalo agrupado incluye el cero.

Restringir por tipo ayuda también cuando el tipo se predice desde la consulta. Un predictor sin
entrenamiento mejora a la búsqueda libre de forma concordante (convexa $0{,}563$ frente a
$0{,}533$), aunque queda lejos del techo que da el tipo conocido ($0{,}712$). Un reordenador
supervisado en dos etapas no mejora a la convexa: los relevantes casi siempre están entre los
candidatos (techo del conjunto de candidatos $0{,}876$), y lo que falta es ordenarlos mejor.

```{figure} ../figuras/fig_registro.png
:width: 100%

nDCG@10 con 811 documentos y con el registro completo.
```

## Registro completo: búsqueda persona a persona

| Clase de consulta | $n$ | Acierto@1 diccionario | Acierto@1 C4 |
|---|---|---|---|
| Deportista · nombre exacto | 300 | 0,987 | 0,877 |
| Deportista · un error de digitación | 300 | 0,977 | 0,573 |
| Deportista · a medio escribir | 300 | 0,970 | 0,513 |
| Deportista · número de documento | 300 | 1,000 | 0,947 |
| Institución · nombre exacto | 75 | 1,000 | 0,867 |
| Institución · un error de digitación | 75 | 0,987 | 0,640 |

El diccionario responde en $37$ ms en la mediana y $47$ ms en el percentil $95$. La muestra se
toma en memoria en cada ejecución y el informe solo guarda la clase de consulta y si hubo
acierto.

## Restricción por función

Cada contexto de búsqueda de la plataforma declara los tipos de objeto que puede devolver. Con
esa restricción, ninguna de $1.826$ consultas cruzadas devolvió un objeto ajeno a su contexto, y
consultas que la búsqueda por subcadena actual no resuelve (con tildes, errores de digitación o
sinónimos, como «colizeo», «pisina» o «futsal») quedaron en la primera posición.

## Costo

```{figure} ../figuras/fig_costo.png
:width: 100%

Tiempo de cada componente, en escala logarítmica. La latencia la fija la codificación de la consulta.
```


Las configuraciones neuronales responden en unos $0{,}35$ s por consulta con la GPU integrada
del equipo ($0{,}63$ s solo en CPU) y ocupan unos $2$ GiB de memoria por el codificador. Añadir
la señal léxica y la ontología no encarece el sistema. Truncar el vector a $512$ dimensiones es
no inferior a la dimensión nativa en el ampliado y en los difíciles y reduce el índice a la mitad.
