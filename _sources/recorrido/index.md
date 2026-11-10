# Recorrido por los corpus

La monografía se apoya en cuatro corpus de tamaño creciente: diecisiete reportes, $177$
documentos, $811$ documentos de cinco tipos y el registro completo de la plataforma, con
$757.538$ documentos. Los cuadernos del [archivo exploratorio](../archivo/index.md) cuentan bien
la primera etapa, pero se escribieron antes de la auditoría del 30 de septiembre de 2026 y
muchas de sus cifras ya no son las de la tesis. Las páginas de esta parte recorren cada etapa
desde el principio, con las cifras definitivas de la monografía, y explican qué se construyó,
cómo se evaluó, qué salió y qué límite llevó a la etapa siguiente.

Los resúmenes cortos siguen en [la monografía](../tesis/resumen.md), [el método](../tesis/metodo.md),
[los resultados](../tesis/resultados.md) y [el código](../tesis/codigo.md). Aquí está el detalle.

## Las etapas y por qué cada una siguió a la anterior

| Etapa | Fecha (2026) | Datos o corpus | Pregunta que respondía | Límite que dejó |
|---|---|---|---|---|
| Análisis de la demanda | mediados de septiembre | historial de $14.718$ ejecuciones de reportes en seis semanas y media | qué reportes se piden de verdad y qué conviene indexar primero | la demanda solo se observa sobre los diecisiete reportes existentes; el dominio de competencias no tiene punto de entrada |
| Ontología del dominio | mediados de septiembre | firmas de las consultas y catálogo de datos | qué conceptos y sinónimos necesita el buscador y qué propiedades se buscan por nombre propio | la entidad Prueba Regional no existe en ninguna tabla y hay que componerla |
| Escalera de la Versión 1 | desde el 17 de septiembre | diecisiete reportes | cuánto aporta cada componente (léxico, denso, fusión, ontología, realce) | las primeras cifras resultaron afectadas por errores de implementación y de análisis |
| Auditoría interna | 30 de septiembre | todo lo anterior | si las cifras resistían una lectura crítica | todas las cifras previas se descartaron y el plan de análisis quedó fijado por escrito |
| Conjuntos difíciles y estadística | 5 y 6 de octubre | diecisiete reportes, paráfrasis A ($52$) y B ($78$) | si las diferencias sobrevivían al techo del protocolo de objetivo conocido | con diecisiete documentos la hipótesis de entidad exacta no era contrastable y varias diferencias quedaban sin poder |
| Corpus definitivo | 20 de octubre | $160$ Pruebas Regionales y $17$ reportes | si las conclusiones se sostenían a mayor escala y con las entidades dentro de los documentos | un solo tipo de objeto por dominio |
| Corpus v3 y fusión convexa | 20 de octubre | $811$ documentos de cinco tipos | si las conclusiones generalizan a roles, permisos, pruebas y reglas, y qué fusión resuelve el reparto entre denso e híbrido | faltaba ver el método a la escala de la plataforma |
| Registro completo | 27 y 28 de octubre | $757.538$ documentos (y $757.554$ como universo de evaluación) | cómo se comporta la escalera con cientos de miles de distractores, cómo se busca una persona y cómo se controla la heterogeneidad | la primera corrida tenía un índice denso parcial y no comparaba la ontología con controles de la misma longitud |
| Validación con cobertura densa completa | 28 de octubre | $757.554$ documentos, todos con vector denso | si el aporte de la ontología se explica por algo más simple, si el tipo de objeto puede predecirse y si un ordenamiento en dos etapas mejora la convexa | quedan los límites comunes a todo el trabajo: consultas del autor y ninguna evaluación independiente |

Cada paso respondió a un límite concreto del anterior. El análisis de la demanda mostró que
cinco reportes concentran el $83\%$ de las solicitudes reales y que un dominio entero, el de
las competencias, tiene cientos de miles de registros y ninguna consulta, porque ningún reporte
lo expone. Eso llevó a la ontología, que nombra los conceptos con los que se componen las
preguntas de negocio, y a una primera versión del buscador limitada a los diecisiete reportes.

La escalera de ablación de esa Versión 1 se corrió varias veces antes de la auditoría del 30 de
septiembre, que encontró errores en el análisis de la demanda y en los benchmarks y obligó a
descartar todas las cifras anteriores. Después de la auditoría se fijó el plan de análisis y se
construyeron conjuntos de consultas difíciles, porque con las consultas fáciles casi todas las
configuraciones dejaban el reporte correcto en la primera posición y las diferencias se
apoyaban en muy pocas consultas.

Un control con el nombre propio borrado mostró que el estrato de entidad exacta de la Versión 1
medía el tema del reporte y no la búsqueda de una entidad, porque los nombres no figuraban en
ningún documento. El corpus definitivo de $177$ documentos se construyó para tener las
entidades dentro de los documentos. El corpus v3 de $811$ documentos respondió a la objeción de
que todo se había probado con un solo tipo de objeto, y mostró que ninguna configuración fija
domina, lo que llevó a la fusión convexa. El registro completo llevó el método a la escala de la
plataforma, y la validación final cerró los dos límites que dejó su primera corrida.

## Los corpus

| Corpus | Documentos | Composición | Consultas | Juicios de relevancia |
|---|---|---|---|---|
| [Versión 1](02_version1_17_reportes.md) | $17$ | descripciones de reportes; $9$ con bloque de ontología (luego $14$ con un enriquecimiento mecánico) | sintético $40$ (de $51$; las $11$ de competencias no tienen documento relevante), ampliado desde firmas $127$, control sin nombre $55$, difícil A $52$, difícil B $78$ (unión $130$) | objetivo conocido con grado 2, a veces reportes secundarios con grado 1; en el ampliado, el reporte que se ejecutó (juicio *silver*) |
| [Definitivo](03_corpus_definitivo_177.md) | $177$ | $160$ Pruebas Regionales que existen en la base y $17$ reportes | $180$ ($127$ de firmas y $53$ de competencias), las $55$ de entidad sin nombre y las $130$ difíciles | objetivo conocido en los reportes; por facetas en competencias, con una mediana de dos relevantes por consulta |
| [v3](04_corpus_v3_811.md) | $811$ | $17$ reportes, $160$ Pruebas Regionales, $75$ funcionalidades, $549$ pruebas del catálogo y $10$ reglas de participación | $320$ ($180$ anteriores y $140$ nuevas: $53$ de funcionalidades, $60$ de pruebas y $27$ de reglas), más las $130$ difíciles ($450$ en total) | derivados de la estructura: el permiso que responde la pregunta, la coincidencia de facetas, el deporte de la regla |
| [Registro completo](05_registro_completo.md) | $757.538$ | $643.107$ deportistas, $45.224$ grupos, $30.220$ personas de apoyo, $13.097$ instituciones, $12.342$ escenarios, $9.685$ acreditaciones, $1.837$ disciplinas de evento, $581$ reportes y cortes por departamento, $310$ competencias, $222$ usuarios de gestión y el corpus v3 | búsqueda persona a persona ($300$ deportistas en cinco formas y $75$ instituciones en dos), $30$ consultas de precisión, $1.826$ consultas cruzadas a $22$ contextos | la persona o el objeto buscado; el tipo de objeto permitido en cada contexto |
| [Registro como universo de evaluación](05_registro_completo.md) | $757.554$ | los $811$ documentos de v3 y $756.743$ objetos del registro como distractores | las mismas $450$ de v3 | los de v3; los distractores no recibieron juicios |

El universo de $757.554$ documentos difiere ligeramente del registro de $757.538$ porque, para
evaluar la escalera, se excluyeron del registro los objetos que duplican a los de v3 (reportes
curados, Pruebas Regionales, pruebas, reglas y funcionalidades) y se añadieron los $811$
documentos de v3 con sus juicios. Así los documentos relevantes son exactamente los mismos con
y sin distractores.

## Cómo leer estas páginas

Salvo que se indique otra métrica, todas las cifras son nDCG@10, que vale $1$ cuando el
documento correcto queda en la primera posición, $0{,}631$ en la segunda, $0{,}500$ en la tercera
y $0$ fuera de las diez primeras. Cada cifra pertenece a un corpus y a un conjunto de consultas
concretos, y cada tabla lo dice. Dos cifras de filas o corpus distintos no se comparan entre sí,
porque cambian los documentos que compiten, las consultas y, entre las dos corridas sobre el
registro, la cobertura del índice denso.

Las configuraciones se nombran como en la monografía. BM25 es la referencia léxica sobre la
descripción del documento. C1 es el denso puro, C2 el denso sobre el texto con ontología, C3 el
híbrido BM25 más denso fusionado por rango recíproco (RRF, $k=60$), C4 el híbrido sobre el texto
con ontología y C5 el C4 con realce por entidad ($\lambda=0{,}2$). La convexa suma
$0{,}8\cdot$denso $+ 0{,}2\cdot$BM25 con puntuaciones normalizadas.

Una diferencia es *concordante* cuando la prueba de Wilcoxon pareada y la de permutación de
signos la rechazan con $\alpha=0{,}05$ después de la corrección de Holm. Las comparaciones
fijadas en el plan de análisis posterior a la auditoría son confirmatorias; las que se
definieron después de ver resultados (el conjunto difícil B como réplica, los análisis de
cobertura de la ontología, los desgloses por estrato) se reportan como exploratorias. Cada
página marca a cuál de los dos grupos pertenece cada resultado y conserva las salvedades de la
monografía. La [última página](06_validez_y_robustez.md) reúne los controles de validez, los
errores encontrados y corregidos, la robustez de las conclusiones y los límites que siguen
abiertos.

```{note}
Los cuadernos del archivo exploratorio conservan sus salidas originales. Cifras como una
demanda real de $9.051$ consultas, un índice de Gini de $0{,}74$ o un reporte de promoción con
el $47{,}5\%$ de la demanda son anteriores a la auditoría y la monografía ya no las usa. Cuando
una cifra de un cuaderno no coincide con la de estas páginas, vale la de estas páginas.
```

## Páginas

1. [La demanda observada y la ontología](01_demanda.md): el historial de consultas, la unidad de
   análisis, la concentración de la demanda, el dominio de competencias, la entidad Prueba
   Regional, la ontología y las correcciones de la auditoría.
2. [Versión 1: diecisiete reportes](02_version1_17_reportes.md): los cinco conjuntos de
   evaluación, la escalera completa, la estadística, la ontología, el realce, las fusiones
   alternativas, los barridos y el costo computacional.
3. [Corpus definitivo: 177 documentos](03_corpus_definitivo_177.md): las Pruebas Regionales que
   existen en la base y el daño de la fusión por rango con paráfrasis.
4. [Corpus v3: 811 documentos de cinco tipos](04_corpus_v3_811.md): roles, permisos, pruebas y
   reglas, el léxico dividido y la fusión sensible a la confianza.
5. [El registro completo](05_registro_completo.md): la escalera entre $757.554$ documentos, la
   validación con controles de la misma longitud, la búsqueda persona a persona y la restricción
   por función, con el contraste frente a las cajas de búsqueda actuales de la plataforma.
6. [Validez y robustez](06_validez_y_robustez.md): errores corregidos, amenazas a la validez,
   remuestreo por reporte, dosis-respuesta, metaanálisis y límites abiertos.

## Cómo reproducirlo

El código de todas las etapas está en la carpeta
[`experimentos/`](https://github.com/luispenaranda08/semantic_search_engine/tree/main/experimentos)
y la etiqueta `v1.1-tesis` fija la versión que produce las cifras de la monografía. Cada página
termina con los objetivos de `make` y los scripts que producen sus tablas. Los corpus de $17$,
$177$ y $811$ documentos, las consultas y los juicios están publicados, así que todo lo que va de
la Versión 1 al corpus v3 se puede volver a correr. El historial de consultas, la base operativa
y las fichas del registro completo contienen datos de personas, muchas de ellas menores de
edad, y no se publican; de esas etapas el repositorio guarda los agregados y las métricas por
consulta.
