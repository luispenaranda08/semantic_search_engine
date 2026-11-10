# Método

## Evaluar sin consultas humanas

La plataforma no tiene un registro de búsquedas en texto libre, de modo que las consultas y sus
juicios de relevancia se derivan de la estructura del sistema. Las fuentes son las firmas de los
reportes que la gente sí ejecuta (tablas, columnas y filtros, sin los valores buscados), las
facetas de las pruebas deportivas y los permisos que definen qué puede hacer cada rol. Cada
consulta tiene un documento objetivo conocido (protocolo *known-item*), y la métrica principal es
nDCG@10 con relevancia graduada.

Para que las consultas no hereden el vocabulario que la ontología inyecta en los documentos, se
usa un léxico dividido: los sinónimos que la ontología agrega a un documento no pueden aparecer
en las consultas que lo buscan. Los conjuntos difíciles A y B están formados por paráfrasis que
no comparten términos con su reporte objetivo.

## La escalera de ablación

Cada peldaño difiere del anterior en un solo componente, con el corpus, las consultas, los
juicios y el codificador fijos. La diferencia entre dos peldaños mide el aporte de ese
componente.

| Peldaño | Configuración | Qué aísla |
|---|---|---|
| — | BM25 sobre la descripción | referencia léxica |
| C1 | Denso puro (`jina-embeddings-v3`, 1.024 dimensiones) | aporte del codificador |
| C2 | Denso sobre el texto con ontología | ontología en el denso (P3) |
| C3 | Híbrido BM25 + denso con RRF ($k=60$) | señal léxica (P1, P2) |
| C4 | Híbrido sobre el texto con ontología | ontología en el híbrido (P3) |
| C5 | C4 con realce por entidad ($\lambda=0{,}2$) | realce (P5) |
| Convexa | $0{,}8\cdot$denso $+ 0{,}2\cdot$BM25, puntuaciones normalizadas min–max | fusión por puntuaciones |

RRF suma $1/(k+\text{posición})$ de cada lista y no mira las puntuaciones. La combinación
convexa sí las usa: cuando BM25 no encuentra nada útil, sus puntuaciones normalizadas son bajas y
casi uniformes y apenas mueven el orden del denso. El peso $\alpha=0{,}8$ se eligió dejando fuera
el grupo evaluado y resultó el mismo en los seis cortes del corpus v3.

## La ontología

Una ontología del dominio con clases como deportista, institución, evento, fase, disciplina y
región, y sus relaciones, se recorre para cada documento y produce un bloque de sinónimos,
entidades y preguntas de negocio que se añade a su descripción antes de indexarla. La ontología
solo cambia el texto del documento; el recuperador no cambia.

Se construyó desde la evidencia del propio sistema, siguiendo la guía de Noy y McGuinness: las
$744$ firmas de consulta del historial, unas $90$ columnas técnicas agrupadas en $13$ clases con
$20$ relaciones, y sinónimos tomados del vocabulario de la plataforma y del deporte escolar.

```{figure} ../images/recorrido/diagrama_3_mapa_relaciones.png
:width: 100%

Clases principales de la ontología, organizadas alrededor del deportista.
```

## Estadística

Todas las comparaciones son pareadas sobre las mismas consultas. Cada contraste se prueba con
Wilcoxon de rangos con signo y con una prueba de permutación de signos, ambas bilaterales ($20.000$ sorteos, o
exacta con veinte o menos diferencias no nulas). Se corrige por Holm dentro de cada familia, y una
diferencia se declara *concordante* solo si las dos pruebas la rechazan tras la corrección. Como
las consultas que comparten objetivo no son independientes, los intervalos se calculan con un
*bootstrap* que remuestrea grupos de consultas con el mismo documento objetivo. Se reportan
también tamaños del efecto (correlación biserial por rangos), efecto mínimo detectable y un
análisis de dosis-respuesta del efecto de la ontología. Los intervalos usan $10.000$ remuestreos.
Las definiciones formales, con sus fórmulas, están en el Anexo A de la monografía.

## Extensión exploratoria: el registro completo (P7)

Para probar el método a escala se construyó un corpus con todo el registro de la plataforma
($757.538$ documentos, entre ellos $643.107$ deportistas, $45.224$ grupos y $13.097$
instituciones). Sobre él se evaluaron tres cosas: la escalera con las mismas $450$ consultas del
corpus v3 y $756.743$ distractores; la búsqueda persona a persona con un diccionario de entidades
(índice de trigramas con puntuación Damerau–Levenshtein y Jaro–Winkler), y la restricción de
cada búsqueda a los tipos de objeto de su función. Una validación posterior, con un protocolo publicado en
`experimentos/resultados/validacion_colab/protocolo.txt`, repitió la escalera con todos los documentos en el índice denso y comparó la
ontología con tres controles de la misma longitud en subpalabras.
