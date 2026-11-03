# Corpus definitivo: 177 documentos

La Versión 1 dejó tres preguntas abiertas: la hipótesis de entidad exacta no era contrastable
porque los nombres no figuraban en ningún documento, Recall@100 no discriminaba con diecisiete
documentos y varias diferencias quedaban por debajo de lo que el número de consultas permitía
detectar (ver [la Versión 1](02_version1_17_reportes.md)). El corpus definitivo responde a las
tres con un dominio en el que las entidades forman parte del texto de cada documento: las
Pruebas Regionales del dominio de competencias, que el [análisis de la demanda](01_demanda.md)
había señalado como el gran vacío de cobertura de la plataforma.

## De dónde salen los documentos

Cada documento nuevo es una Prueba Regional que existe realmente en la base de datos: una
combinación de evento, deporte, categoría y región deportiva con al menos un grupo inscrito.
Cada uno describe sus propios hechos agregados: cuántos departamentos, organizaciones, grupos e
integrantes participan, en qué fases hay grupos inscritos y cuántos resultados de competencia
registra. El texto incluye el nombre compuesto de la prueba (deporte, categoría y región), que
es justo la entidad que la Versión 1 no podía buscar.

La extracción se hizo con consultas de solo lectura que devuelven conteos y catálogos por
combinación, nunca filas individuales, y la ejecutó sobre el almacén de datos el responsable de
datos con su acceso autorizado. Una auditoría automática verificó que la salida no contiene
correos, teléfonos ni identificadores personales. Resultaron $160$ Pruebas Regionales, que junto
con los diecisiete reportes forman un corpus de $177$ documentos.

El texto con ontología de cada prueba se construye con la misma tubería de la Versión 1: la
ontología ya incluía la fórmula de composición de la Prueba Regional (disciplina, categoría,
fase y región) y sus relaciones con el evento, el grupo, la institución y los resultados, de
modo que no hizo falta rediseñarla.

### El corpus que se descartó

Antes de la auditoría del 30 de septiembre se había construido un corpus cartesiano de $816$
Pruebas Regionales, el producto de $102$ disciplinas por $8$ regiones. Muchas de esas
combinaciones no existen en la base, y sus descripciones eran plantillas casi idénticas entre
sí, de modo que el corpus tenía muchos documentos que se distinguían en una o dos palabras y no
representaban pruebas reales. El corpus definitivo lo reemplazó por las $160$ combinaciones que
existen, cada una con hechos propios. Las cifras calculadas sobre el corpus cartesiano se
descartaron con las demás anteriores a la auditoría; el cuaderno de
[expansión del corpus de competencias](../notebooks/06_Expansion_Corpus_Competencias.ipynb) del
archivo todavía lo muestra.

## Las consultas y sus juicios

Se evalúan $180$ consultas: las $127$ derivadas de las firmas del historial, que apuntan a los
reportes, y $53$ consultas nuevas de competencias. Las de reportes conservan su juicio de objetivo
conocido. Las de competencias se juzgan por facetas: es relevante toda prueba consistente con
todas las facetas que la consulta menciona (deporte, categoría, región, evento o fase). Una
consulta que nombra solo un deporte y una región tiene como relevantes todas las pruebas de ese
deporte en esa región, y una que además nombra la categoría tiene menos. La mediana es de dos
documentos relevantes por consulta.

A esas $180$ se suman dos evaluaciones complementarias sobre el mismo corpus: las $55$ consultas de
entidad exacta de los reportes con el nombre propio borrado, como en el control de la Versión 1,
y las $130$ paráfrasis de los conjuntos difíciles A y B, que ahora compiten con $160$ documentos
adicionales.

Estas comparaciones son confirmatorias: el plan de análisis se fijó después de la auditoría y
antes de construir el corpus definitivo.

## Resultados

nDCG@10 salvo la segunda columna (Recall@100).

| Configuración | Global ($n=180$) | Recall@100 global | Competencias ($n=53$) | Entidad, con nombre ($n=55$) | Entidad, sin nombre ($n=55$) | Difíciles A+B ($n=130$) |
|---|---|---|---|---|---|---|
| BM25 | 0,774 | 0,928 | 0,899 | 0,674 | 0,674 | 0,251 |
| C1 · Denso puro | 0,865 | 0,994 | 0,951 | 0,749 | 0,966 | 0,503 |
| C2 · Denso con ontología | 0,910 | 1,000 | 0,954 | 0,836 | 1,000 | 0,652 |
| C3 · Híbrido sin ontología | 0,868 | 0,967 | 0,961 | 0,824 | 0,853 | 0,398 |
| C4 · Híbrido con ontología | 0,960 | 1,000 | 0,973 | 0,975 | 1,000 | 0,590 |
| C5 · C4 con realce | 0,950 | 1,000 | 0,973 | 0,975 | 1,000 | 0,563 |

C4 es la mejor configuración global ($0{,}960$), seguida de C5 ($0{,}950$) y C2 ($0{,}910$). En las
paráfrasis la mejor es C2 ($0{,}652$).

### Recall@100 deja de ser trivial

Con $160$ documentos nuevos compitiendo con los diecisiete reportes, el ranking se vuelve más
exigente y Recall@100, que con diecisiete documentos valía $1$ para casi todo, empieza a
discriminar. BM25 recupera el $92{,}8\%$ de los relevantes entre los cien primeros, el denso puro
el $99{,}4\%$ y el híbrido sin ontología el $96{,}7\%$, frente al $100\%$ de las tres configuraciones
con ontología. El híbrido sin ontología deja fuera de los cien primeros relevantes que el denso
puro sí trae.

## La estadística

Diferencia media de nDCG@10 y, entre paréntesis, el mayor de los $p$-valores de Wilcoxon y de
permutación. En las cinco primeras filas los $p$ están ajustados por Holm dentro de la familia de
la escalera y el asterisco marca las concordantes; las dos últimas filas son comparaciones
complementarias, sin ajuste.

| Comparación | Global | Competencias | Entidad exacta | Difíciles A+B |
|---|---|---|---|---|
| C3 − BM25 (P1) | +0,093 (<0,001) \* | +0,061 (0,005) \* | +0,151 (<0,001) \* | +0,147 (<0,001) \* |
| C3 − C1 (P1, P2) | +0,002 (0,896) | +0,010 (1,000) | +0,076 (0,033) \* | −0,104 (<0,001) \* |
| C2 − C1 (P3, denso) | +0,045 (0,001) \* | +0,004 (1,000) | +0,087 (0,007) \* | +0,150 (<0,001) \* |
| C4 − C3 (P3, híbrido) | +0,093 (<0,001) \* | +0,012 (0,430) | +0,150 (0,001) \* | +0,192 (<0,001) \* |
| C5 − C4 (P5) | −0,010 (0,125) | +0,000 (n/d) | +0,000 (n/d) | −0,027 (0,018) \* |
| C1 − BM25 (aporte del codificador) | +0,091 (<0,001) | +0,052 (0,095) | +0,075 (0,090) | +0,252 (<0,001) |
| C4 − C2 (elección de la configuración) | +0,050 (<0,001) | +0,019 (0,294) | +0,139 (<0,001) | −0,062 (0,061) |

Lo observado con diecisiete reportes se mantiene y se refuerza. El híbrido supera a BM25
($+0{,}093$), la ontología mejora al denso ($+0{,}045$) y, ahora también de forma concordante en el
conjunto global, al híbrido ($+0{,}093$). El realce sigue sin aportar ($-0{,}010$, sin significancia
en el global) y es adverso de forma concordante en las paráfrasis ($-0{,}027$).

## C4 frente a C2: la evidencia de la recomendación

En el conjunto global, C4 supera al denso con ontología en $+0{,}050$, con $p<0{,}001$. Esa
diferencia resiste el remuestreo por documento objetivo, que es la prueba más exigente frente a
la dependencia entre consultas que comparten reporte o prueba: su intervalo del $95\%$ va de
$+0{,}006$ a $+0{,}079$ y excluye el cero, y dejar fuera un reporte a la vez no cambia su signo. Es la
evidencia medida que respalda recomendar C4 para una versión del buscador limitada a reportes,
porque gana donde las consultas usan el vocabulario de la plataforma, que es el caso de las
consultas reales observadas en el historial.

La ventaja se concentra en las consultas de entidad exacta de los reportes ($+0{,}139$), donde el
nombre propio de la consulta no está en ningún documento. En las paráfrasis la diferencia va en
sentido contrario ($-0{,}062$, $p=0{,}061$), sin significancia. Con diecisiete reportes esa
desventaja no se había confirmado; aquí aparece con más fuerza, por la razón que se explica a
continuación.

## El daño de la fusión por rango en las paráfrasis

En las $130$ paráfrasis, con $160$ documentos adicionales compitiendo, el híbrido sin ontología
queda claramente por debajo del denso puro ($-0{,}104$, concordante) y el híbrido con ontología por
debajo del denso con ontología ($-0{,}062$). Con diecisiete documentos la diferencia entre C3 y C1
había sido pequeña y de signo cambiante.

El mecanismo es el siguiente. Las paráfrasis no comparten vocabulario con su reporte objetivo,
que es como se construyeron, pero sí comparten palabras genéricas como «deportistas», «región»
o «competencia» con muchas Pruebas Regionales. La lista de BM25 se llena entonces de esos
distractores. RRF suma $1/(k+\text{posición})$ de cada lista sin mirar cuánta confianza merece
cada una, de modo que el primer distractor de BM25 recibe el mismo aporte que recibiría una
coincidencia clara, y la fusión lo promueve por encima del documento que el denso había puesto
arriba. El efecto de la fusión depende, por tanto, del tamaño y la composición del corpus: con
pocos documentos casi no hay distractores que promover, y con más documentos del mismo
vocabulario genérico los hay en abundancia. Es el mismo mecanismo que el
[corpus v3](04_corpus_v3_811.md) reproduciría después con otros tipos de documento y otro
procedimiento para construir las consultas, y que llevó a la fusión convexa.

## La entidad con y sin nombre

El estrato de entidad exacta de los reportes también cambia de comportamiento cuando el corpus
crece. Con el nombre propio en la consulta, el denso puro cae a $0{,}749$ y el híbrido lo supera
($+0{,}076$, concordante). Con el nombre borrado, el denso sube a $0{,}966$ y el híbrido sin
ontología queda por debajo ($0{,}853$, es decir, $-0{,}113$).

El nombre, que no figura en ningún documento, perjudica más al denso cuando hay muchos
documentos parecidos que con diecisiete reportes. La señal léxica simplemente ignora el término que no
encuentra y amortigua ese ruido. Es robustez frente a términos ajenos, sin que el híbrido llegue
a reconocer la entidad, y por eso no cuenta como evidencia a favor de P2. Las configuraciones
con ontología quedan en $1{,}000$ sin el nombre, igual que en la Versión 1.

## Las consultas de competencias: P2 donde la entidad sí está

En las $53$ consultas de competencias la entidad que se busca está en el documento, que era la
condición que faltaba para contrastar P2. El resultado no apoya la hipótesis. Todas las
configuraciones neuronales quedan entre $0{,}951$ y $0{,}973$, y el híbrido no se distingue del denso
($+0{,}010$, $p$ ajustado de $1{,}000$). La ontología tampoco cambia nada apreciable en este estrato
($+0{,}004$ en el denso y $+0{,}012$ en el híbrido, sin significancia).

El resultado exige cautela. Las consultas y los juicios por facetas se generaron a partir de las
mismas facetas que contiene cada documento, así que el estrato está cerca del techo y comparte
vocabulario con los documentos, una condición favorable para todos los sistemas y poco
discriminante entre ellos. La conclusión prudente es que, en un corpus donde los nombres de las
entidades están en el texto y las consultas los repiten, el codificador denso ya los resuelve
sin ayuda de la señal léxica. La parte de P2 que se refiere a buscar personas e instituciones
por su nombre se contestó más tarde sobre el [registro completo](05_registro_completo.md).

## Dosis-respuesta de la ontología con 177 documentos

Una objeción natural al efecto de la ontología es la circularidad: el autor escribió la ontología
y las consultas difíciles, y el nivel «con puente» se define por compartir términos con la
ontología. Si el efecto fuera un artefacto de esa definición, no debería crecer con la cantidad
de términos compartidos. La tabla agrupa las paráfrasis por el número de raíces que la consulta
comparte con el bloque de ontología del documento objetivo ($0$: $n=57$; $1$: $n=34$; $2$ o más:
$n=39$).

| Comparación | 0 raíces | 1 raíz | 2 o más | Spearman ($p$) |
|---|---|---|---|---|
| C2 − C1 | +0,063 | +0,224 | +0,211 | +0,18 (0,040) |
| C4 − C3 | −0,065 | +0,288 | +0,484 | +0,54 (<0,001) |

Sin ninguna raíz compartida, la ontología no ayuda al híbrido; con una, la ganancia es de
$+0{,}288$, y con dos o más, de $+0{,}484$. El gradiente es más pronunciado que con diecisiete
reportes, donde los mismos grupos daban $-0{,}074$, $+0{,}125$ y $+0{,}251$. Es el patrón que produciría un puente de vocabulario. La
circularidad de origen, un mismo autor para la ontología y las consultas, no queda eliminada y
solo se resolvería con consultas escritas por otras personas.

## Robustez por documento objetivo

Diferencia media de nDCG@10 con su intervalo del $95\%$ por *bootstrap* que remuestrea reportes o
pruebas objetivo, no consultas. El asterisco marca los intervalos que excluyen el cero; dejar
fuera un reporte a la vez no cambia el signo de ninguno de ellos.

| Comparación | Definitivo ($n=180$) | Difíciles con 177 documentos ($n=130$) |
|---|---|---|
| C3 − BM25 | +0,093 [+0,049; +0,136] \* | +0,147 [+0,059; +0,234] \* |
| C3 − C1 | +0,002 [−0,063; +0,048] | −0,104 [−0,160; −0,047] \* |
| C2 − C1 | +0,045 [+0,008; +0,102] \* | +0,150 [+0,076; +0,239] \* |
| C4 − C3 | +0,093 [+0,016; +0,185] \* | +0,192 [+0,075; +0,309] \* |
| C5 − C4 | −0,010 [−0,024; +0,000] | −0,027 [−0,062; +0,000] |
| C4 − C2 | +0,050 [+0,006; +0,079] \* | −0,062 [−0,143; +0,020] |

En el corpus definitivo las ventajas de la ontología sobre el denso y sobre el híbrido y la de C4
sobre C2 mantienen intervalos que excluyen el cero. Con diecisiete reportes, en cambio, solo la
ventaja del híbrido sobre BM25 sobrevivía a este criterio en el conjunto ampliado.

## Lo que ve el usuario y lo que el diseño podía detectar

Éxito en la primera posición y entre las tres primeras:

| Configuración | Definitivo @1 / @3 | Difíciles con 177 documentos @1 / @3 |
|---|---|---|
| BM25 | 0,62 / 0,86 | 0,20 / 0,27 |
| C1 · Denso puro | 0,81 / 0,89 | 0,39 / 0,52 |
| C2 · Denso con ontología | 0,86 / 0,94 | 0,54 / 0,68 |
| C3 · Híbrido | 0,81 / 0,91 | 0,33 / 0,40 |
| C4 · Híbrido con ontología | 0,94 / 0,97 | 0,50 / 0,60 |
| C5 · C4 con realce | 0,92 / 0,95 | 0,46 / 0,58 |

En el corpus definitivo C4 coloca el documento correcto primero en el $94\%$ de las consultas y
entre los tres primeros en el $97\%$. En las paráfrasis el mejor sistema, C2, baja al $54\%$ y al
$68\%$, lo que muestra cuánto margen queda cuando el usuario no usa el vocabulario de la
plataforma.

La comparación con el efecto mínimo detectable (EMD, con potencia de $0{,}8$ y $\alpha=0{,}05$
bilateral, aproximado como $2{,}8\,s_d/\sqrt{n}$) indica qué diferencias podía resolver este diseño.

| Comparación | Definitivo, observada / EMD | Difíciles con 177, observada / EMD |
|---|---|---|
| C3 − C1 | +0,002 / 0,051 | −0,104 / 0,081 |
| C2 − C1 | +0,045 / 0,037 | +0,150 / 0,076 |
| C4 − C3 | +0,093 / 0,058 | +0,192 / 0,104 |
| C5 − C4 | −0,010 / 0,013 | −0,027 / 0,032 |
| C4 − C2 | +0,050 / 0,040 | −0,062 / 0,092 |

En el conjunto global, las diferencias significativas superan su EMD; en las paráfrasis también,
salvo el daño del realce ($-0{,}027$), concordante pero algo menor que su EMD ($0{,}032$). La desventaja de C4 frente a
C2 en las paráfrasis ($-0{,}062$) queda por debajo del suyo ($0{,}092$), que es otra forma de decir
que con $130$ consultas no se podía distinguir del azar.

## Costo

El corpus definitivo no cambia el costo por consulta: todas las configuraciones neuronales pagan
la misma codificación de la consulta, unos $0{,}35$ segundos, y la búsqueda sobre $177$ vectores
sigue siendo despreciable. Indexar el corpus completo toma unos $25$ segundos de codificación
densa, a razón de unos $141$ ms por documento (ver el costo en [la Versión 1](02_version1_17_reportes.md)).

## Lo que dejó esta etapa

El corpus definitivo confirmó las conclusiones de la Versión 1 a mayor escala, añadió la
evidencia de C4 sobre C2 en el conjunto global y convirtió en concordante el daño de la fusión
por rango en las paráfrasis. Pero sigue teniendo un solo tipo de objeto por dominio: reportes y
Pruebas Regionales. Una plataforma pública guarda su conocimiento funcional en objetos de
naturaleza distinta, como roles, permisos, pruebas del catálogo y reglas de participación, y el
usuario que la navega busca también qué puede hacer cada rol o qué reglas rigen una
inscripción. El [corpus v3](04_corpus_v3_811.md) se construyó para comprobar si las conclusiones
se sostienen en ese escenario.

## Cómo reproducirlo

La extracción agregada está en
[un script propio](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/athena/extraer_competencias.py)
(`make extraer`) y requiere el acceso autorizado de la organización al almacén de datos, por lo
que no se puede repetir desde el repositorio. A partir de esa extracción,
[`construir_competencias_v2.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/construir_competencias_v2.py)
construye el corpus, las consultas de competencias y sus juicios por facetas, y `make final`
corre las tres evaluaciones (global, sin nombre y difíciles) con
[`eval_flexible.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/eval_flexible.py).
El corpus de $177$ documentos, que solo contiene descripciones y conteos agregados, está
publicado en `corpus/corpus_final.jsonl`, junto con las consultas y los juicios en `datos/`, así
que la evaluación se puede repetir sin la extracción. La robustez por documento objetivo, la
dosis-respuesta y el efecto mínimo detectable salen de `make robustez` y `make complementario`.
