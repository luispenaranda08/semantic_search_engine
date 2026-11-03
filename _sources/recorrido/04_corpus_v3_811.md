# Corpus v3: 811 documentos de cinco tipos

Los dos corpus anteriores contienen un solo tipo de objeto por dominio: reportes, y luego
reportes y Pruebas Regionales. Una plataforma pública, sin embargo, guarda su conocimiento
funcional en objetos de naturaleza distinta. Quien la usa necesita saber qué puede hacer cada
rol, qué reglas rigen una inscripción o qué pruebas existen en el catálogo, y esas preguntas no
se responden con un reporte. El corpus v3 se construyó para contrastar las conclusiones en ese
escenario y responder a la objeción de que todo se había probado con un solo tipo de documento.
Terminó mostrando que ninguna configuración fija de la escalera domina, y eso llevó a la fusión
sensible a la confianza que se describe en la segunda mitad de esta página.

## De dónde salen los documentos

Los documentos nuevos se tomaron del catálogo de la base operativa del módulo de competencias,
con la autorización de la organización y mediante consultas de solo lectura que devuelven textos
de catálogo y conteos. La salida pasó la misma auditoría de datos personales que la extracción
del [corpus definitivo](03_corpus_definitivo_177.md), con dos reglas adicionales: se excluyen por
nombre todas las columnas que identifican usuarios, creadores o correos, y las menciones a la
organización operadora se anonimizan.

| Tipo de objeto | Documentos | Qué describe cada documento |
|---|---|---|
| Reportes | $17$ | un reporte de la plataforma, como en la Versión 1 |
| Pruebas Regionales | $160$ | una combinación real de evento, deporte, categoría y región, como en el corpus definitivo |
| Funcionalidades | $75$ | un rol o un permiso, con su descripción |
| Pruebas del catálogo | $549$ | una combinación distinta de deporte, disciplina, rama y categoría |
| Reglas de participación | $10$ | los cupos de grupos y de deportistas por deporte de conjunto |
| Total | $811$ | |

Cada documento nuevo tiene, como los anteriores, una descripción y un bloque de ontología con sus
entidades, sinónimos y búsquedas típicas. Un permiso, por ejemplo, se describe con su código, lo
que permite hacer y los roles que lo incluyen; su bloque de ontología lo relaciona con las clases
Permiso, Rol y Usuario y con el objeto sobre el que actúa.

## Consultas derivadas de la estructura

La plataforma no tiene un registro de búsquedas, así que las $140$ consultas nuevas se derivaron
de la estructura del propio sistema, cada una con un juicio que se sigue de esa estructura:

| Tipo de consulta | Consultas | Cuándo un documento es relevante |
|---|---|---|
| Funcionalidades | $53$ | es el permiso o el rol que responde la pregunta; el permiso `medal:delete` es la respuesta correcta a una consulta sobre quién puede quitar una medalla |
| Pruebas del catálogo | $60$ | la prueba coincide en todas las facetas que la consulta menciona |
| Reglas de participación | $27$ | la regla corresponde al deporte nombrado |

Estas $140$ se evalúan junto con las $180$ del corpus definitivo ($127$ de reportes y $53$ de
Pruebas Regionales), para un total de $320$ consultas. Para la fusión se añaden además las $130$
paráfrasis de los conjuntos difíciles A y B, y el total llega a $450$.

### El léxico dividido

Si las consultas nuevas usaran los mismos sinónimos que la ontología inyecta en el documento, la
ontología ganaría por construcción, que es la circularidad que la tesis reconoce en los conjuntos
difíciles. Para controlarla, el diseño usa un *léxico dividido*. Cada familia de sinónimos se parte
en dos mitades deterministas: la primera se inyecta en el enriquecimiento ontológico del
documento y la segunda se reserva para redactar las consultas. Ninguna consulta contiene, por
tanto, un sinónimo que la ontología haya copiado en el documento. El léxico dividido se aplica a
las $140$ consultas nuevas; las $180$ heredadas del corpus definitivo conservan su redacción.

## Una observación de calidad de datos

La extracción dejó una observación que respalda la premisa del trabajo. El catálogo oficial
registra el mismo deporte con dos nombres y dos códigos distintos (Fútbol de Salón y Fútbol
sala), escribe las distancias de atletismo de dos maneras (MTS y MTRS) y alterna mayúsculas sin
regla. Ni siquiera los datos del sistema usan una forma única de nombrar las cosas, de modo que la
coincidencia exacta de palabras no puede ser el único mecanismo de búsqueda. En la evaluación,
las dos variantes del deporte se consideran relevantes para una misma consulta.

## Resultados por tipo de consulta

nDCG@10 de las $320$ consultas del corpus v3. La columna C4 − C2 compara el híbrido con ontología
con el denso con ontología; su intervalo se obtiene por *bootstrap* que remuestrea grupos de
consultas con el mismo conjunto de documentos relevantes. El asterisco marca las diferencias
concordantes tras Holm en la familia de cuatro contrastes del estrato. Los contrastes por estrato
son exploratorios en el sentido del plan: no hay una corrección global entre estratos.

| Estrato | $n$ | BM25 | C1 | C2 | C3 | C4 | C4 − C2 | IC 95 % por objetivo |
|---|---|---|---|---|---|---|---|---|
| Entidad exacta (reportes) | 55 | 0,580 | 0,386 | 0,585 | 0,813 | 0,870 | +0,286 \* | [+0,134; +0,416] |
| Operacional (reportes) | 35 | 0,667 | 0,868 | 0,919 | 0,895 | 0,844 | −0,075 | [−0,169; +0,041] |
| Documento largo (reportes) | 25 | 0,618 | 0,760 | 0,905 | 0,862 | 0,844 | −0,061 | [−0,186; +0,040] |
| Ambigua (reportes) | 12 | 0,730 | 0,765 | 0,792 | 0,783 | 0,689 | −0,103 | [−0,341; +0,094] |
| Pruebas Regionales | 53 | 0,880 | 0,951 | 0,954 | 0,948 | 0,970 | +0,016 | [−0,018; +0,048] |
| Pruebas del catálogo | 60 | 0,712 | 0,774 | 0,836 | 0,894 | 0,917 | +0,081 | [+0,014; +0,156] |
| Funcionalidades | 53 | 0,204 | 0,619 | 0,654 | 0,466 | 0,417 | −0,236 \* | [−0,332; −0,140] |
| Reglas de participación | 27 | 0,241 | 0,912 | 0,926 | 0,430 | 0,443 | −0,483 \* | [−0,642; −0,310] |
| Total | 320 | 0,582 | 0,731 | 0,803 | 0,773 | 0,773 | −0,030 | [−0,099; +0,030] |

Con cinco tipos de objeto, ninguna configuración domina. En el total, el denso con ontología
($0{,}803$) queda por encima del híbrido con ontología ($0{,}773$), sin significancia. Ese promedio
esconde efectos grandes y de signo opuesto.

C4 gana con claridad donde la consulta comparte vocabulario con el documento. En las consultas
de entidad exacta de los reportes la ventaja es de $+0{,}286$, concordante, y el denso puro cae a
$0{,}386$. En las pruebas del catálogo, cuyas consultas nombran el deporte y la disciplina,
la ventaja es de $+0{,}081$, con un intervalo que excluye el cero.

C2 gana con claridad donde la consulta no comparte vocabulario con el documento, que es lo que el
léxico dividido impone: en las funcionalidades ($-0{,}236$) y, sobre todo, en las reglas de
participación ($-0{,}483$), ambas concordantes. En las reglas el denso por sí solo alcanza $0{,}912$
y añadir BM25 por RRF lo hunde a $0{,}430$. BM25 solo, en esos dos estratos, apenas llega a $0{,}204$
y $0{,}241$.

La causa es la misma que en las paráfrasis del corpus definitivo. Cuando la consulta no tiene
términos en común con su documento, la lista de BM25 se llena de distractores que comparten
palabras genéricas, y RRF los promueve porque suma posiciones sin ponderar la confianza de cada
lista. El mecanismo, observado antes en paráfrasis redactadas por el autor, se reproduce aquí en
tipos de documento distintos y con consultas construidas por otro procedimiento.

### La ontología

La ontología vuelve a ser el componente más estable. Mejora al denso en el total ($+0{,}071$,
concordante) y no lo perjudica en ningún estrato, con un efecto que va de $+0{,}004$ en las Pruebas
Regionales a $+0{,}199$ en las consultas de entidad exacta.

### Las paráfrasis con más documentos

Las $130$ paráfrasis de los conjuntos difíciles, evaluadas con $177$ y con $811$ documentos que
compiten. Los niveles A, B y C se definen por el solape de raíces entre la consulta, el documento
y su ontología, como en [la Versión 1](02_version1_17_reportes.md).

| Estrato | $n$ | BM25 | C1 | C2 | C3 | C4 | C4 − C2 | IC 95 % por objetivo |
|---|---|---|---|---|---|---|---|---|
| Total con 177 documentos | 130 | 0,251 | 0,503 | 0,652 | 0,398 | 0,590 | −0,062 | n/d |
| A: con puente ontológico | 52 | 0,000 | 0,119 | 0,409 | 0,029 | 0,587 | +0,178 \* | [+0,104; +0,256] |
| C: con solape léxico | 57 | 0,404 | 0,514 | 0,614 | 0,570 | 0,664 | +0,050 | [−0,058; +0,174] |
| B: sin puente | 21 | 0,000 | 0,341 | 0,393 | 0,199 | 0,177 | −0,216 \* | [−0,331; −0,105] |
| Total con 811 documentos | 130 | 0,177 | 0,328 | 0,496 | 0,294 | 0,555 | +0,058 | [−0,048; +0,152] |

Las filas de los niveles A, C y B corresponden al corpus de $811$ documentos. Al pasar de $177$ a
$811$ documentos todas las configuraciones pierden, pero no por igual. El denso con ontología cae
de $0{,}652$ a $0{,}496$ y el híbrido con ontología solo de $0{,}590$ a $0{,}555$, de modo que el orden
entre ambos se invierte ($+0{,}058$ a favor de C4, sin significancia). La inversión se concentra en
el nivel A, donde la ontología tiende el puente entre la consulta y el documento: allí BM25 sobre
el texto enriquecido encuentra los términos que la consulta comparte con la ontología y C4 supera
a C2 en $+0{,}178$, de forma concordante. En el nivel B, sin puente, ocurre lo contrario
($-0{,}216$, también concordante).

La señal léxica ayuda, entonces, cuando existe algún vocabulario compartido, sea en el documento
o en su ontología, y perjudica cuando no existe ninguno. Con varios tipos de objeto y sin saber
cómo escribirán los usuarios, que es la situación de una plataforma que hoy no tiene buscador,
C4 y C2 se reparten los estratos según ese vocabulario compartido y ninguna configuración fija es
la mejor en todos los casos. Hacía falta una fusión que conservara lo mejor de ambas.

## La fusión sensible a la confianza

RRF combina posiciones. El primer documento de BM25 pesa lo mismo cuando BM25 encontró una
coincidencia clara que cuando solo encontró una palabra genérica. Una fusión que use las
puntuaciones, y no solo el orden, puede dar a BM25 un peso proporcional a lo que realmente
encontró. Sobre el texto enriquecido del corpus v3 se evaluaron tres fusiones de ese tipo frente a
C4 (RRF) y C2 (denso):

| Variante | Cómo combina | Parámetro |
|---|---|---|
| RRF ponderado por cobertura | RRF con el peso de BM25 igual a su cobertura léxica de la consulta | ninguno |
| RRF con compuerta | descarta BM25 si su cobertura de la consulta no alcanza un umbral | el umbral |
| Combinación convexa | $\alpha\cdot\tilde s_{\text{denso}} + (1-\alpha)\cdot\tilde s_{\text{BM25}}$, con puntuaciones normalizadas por mínimo y máximo | $\alpha$ |

La normalización por mínimo y máximo lleva las puntuaciones de cada señal $r$ al intervalo
$[0,1]$ dentro de cada consulta, tomando el mínimo y el máximo sobre los documentos de su lista:

$$
\tilde s_r(q,d) = \frac{s_r(q,d) - \min_{d'} s_r(q,d')}{\max_{d'} s_r(q,d') - \min_{d'} s_r(q,d')}.
$$

El parámetro de las dos últimas variantes se eligió sin fuga, dejando fuera un grupo a la vez
(*leave-one-group-out*). Para evaluar las funcionalidades, por ejemplo, se escogió el valor que
maximiza el promedio de los otros cinco grupos, y así con cada uno. Se usaron las $450$ consultas:
las $320$ del corpus v3 y las $130$ paráfrasis. Este análisis contrasta la hipótesis H7, que era
exploratoria en el plan.

nDCG@10 por grupo de consultas. *Cob.* es el RRF ponderado por cobertura. *Convexa* es
$0{,}8\cdot$denso $+ 0{,}2\cdot$BM25; el valor $\alpha=0{,}8$ se eligió sin mirar el grupo evaluado y
resultó el mismo en los seis cortes. Las diferencias llevan su intervalo del $95\%$ por *bootstrap*
de grupos de consultas con los mismos relevantes, y el asterisco marca las concordantes tras Holm.

| Grupo | $n$ | C2 | C4 | Cob. | Convexa | Convexa − C4 | Convexa − C2 |
|---|---|---|---|---|---|---|---|
| Reportes | 127 | 0,759 | 0,841 | 0,828 | 0,904 | +0,063 \* [+0,018; +0,097] | +0,145 \* [+0,042; +0,209] |
| Pruebas Regionales | 53 | 0,954 | 0,970 | 0,970 | 0,967 | −0,003 [−0,032; +0,027] | +0,012 \* [+0,003; +0,024] |
| Funcionalidades | 53 | 0,654 | 0,417 | 0,506 | 0,634 | +0,216 \* [+0,138; +0,300] | −0,020 [−0,063; +0,022] |
| Pruebas del catálogo | 60 | 0,836 | 0,917 | 0,929 | 0,953 | +0,036 [+0,007; +0,073] | +0,117 \* [+0,054; +0,195] |
| Reglas de participación | 27 | 0,926 | 0,443 | 0,861 | 0,940 | +0,496 \* [+0,318; +0,654] | +0,014 [+0,000; +0,041] |
| Difíciles A+B | 130 | 0,496 | 0,555 | 0,534 | 0,594 | +0,039 [−0,015; +0,096] | +0,097 \* [+0,018; +0,183] |
| Total | 450 | 0,714 | 0,710 | 0,737 | 0,799 | +0,089 \* [+0,060; +0,126] | +0,085 \* [+0,040; +0,122] |

La tabla de la monografía reporta la variante por cobertura y la convexa; la compuerta no aparece
en ella.

La combinación convexa obtiene $0{,}799$ en el total, frente a $0{,}710$ de C4 y $0{,}714$ de C2, y
supera a ambas de forma concordante ($+0{,}089$ y $+0{,}085$), con intervalos por objetivo que excluyen
el cero. En ningún grupo queda por debajo de C4 ni de C2 de forma significativa. Donde C4 era la
mejor, en los reportes y en las pruebas del catálogo, la convexa la iguala o la supera. Donde C2 era
la mejor, en las funcionalidades y en las reglas, recupera casi toda la ventaja del denso; en las
reglas pasa de $0{,}443$ con RRF a $0{,}940$. La variante sin parámetro, con el peso de BM25 igual a su
cobertura, mejora a C4 de forma concordante ($+0{,}028$ en el total), pero queda lejos de la convexa.

### Por qué funciona

Cuando BM25 no encuentra nada relevante, sus puntuaciones normalizadas son bajas y casi
uniformes, y con un peso de $0{,}2$ apenas mueven el orden que dio el denso. Cuando encuentra una
coincidencia clara, la puntuación sobresale y la fusión la aprovecha. RRF trabaja solo con
posiciones y no distingue los dos casos: con $k=60$, el primer documento de la lista de BM25
recibe $1/61$ tanto si es un acierto como si es un distractor.

Las reglas de participación lo muestran con claridad. Sus consultas no comparten palabras con la
regla correcta y BM25 solo llega a $0{,}241$. RRF hunde al denso de $0{,}926$ a $0{,}443$; la convexa
llega a $0{,}940$, un poco por encima del denso, sin que la diferencia con él sea concordante.

### Por qué no es un ajuste a la medida

El peso $\alpha=0{,}8$ fue el mismo en los seis cortes del corpus v3 y en tres de los cuatro del
corpus de diecisiete reportes, y en cada caso se eligió sin ver el grupo evaluado. Más tarde, sobre
el [registro completo](05_registro_completo.md), un $\alpha$ elegido por validación cruzada salió
$0{,}8$ en tres particiones y $0{,}9$ en dos, y no mejoró a $\alpha=0{,}8$ fijo. El resultado coincide
además con lo que Bruch y coautores reportan en colecciones de dominio abierto, donde con un peso
razonable la combinación convexa supera a RRF. Lo que añade este trabajo es la condición en la que
la diferencia se vuelve grande: un corpus con tipos de objeto heterogéneos y consultas que unas
veces comparten vocabulario con el documento y otras no. En el corpus de diecisiete reportes, donde
casi todas las consultas compartían vocabulario, la ventaja de la convexa era solo de dirección.

Una repetición completa de la fusión del corpus v3, con la configuración y la versión del modelo
fijadas, reprodujo los resultados exactamente.

## La recomendación que sale de aquí

Para una versión del buscador que indexe todos los objetos funcionales se recomienda la
combinación convexa con $\alpha=0{,}8$ sobre el texto enriquecido con la ontología. No cuesta más que
C4, porque usa las mismas dos listas. Para la Versión 1, limitada a reportes, la recomendación
sigue siendo C4 (ver [la Versión 1](02_version1_17_reportes.md) y
[el corpus definitivo](03_corpus_definitivo_177.md)).

## Lo que dejó esta etapa

El corpus v3 reprodujo el daño de la fusión por rango con un procedimiento distinto de construir
consultas, mostró que la ontología mejora al denso aun cuando las consultas no pueden repetir sus
sinónimos y encontró una fusión que no pierde en ningún tipo de consulta. Seguía siendo, sin
embargo, un corpus de $811$ documentos, muy lejos de los cientos de miles de objetos que guarda la
plataforma. El [registro completo](05_registro_completo.md) llevó la evaluación a esa escala.

## Cómo reproducirlo

Las consultas de catálogo sobre la base operativa están en
[un archivo de consultas SQL](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/pg/consultas_catalogo.sql)
y la auditoría de datos personales de lo exportado en
[el script de auditoría](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/pg/auditar_csv_pg.py)
(`make auditar_pg`); las dos requieren el acceso autorizado de la organización y las exportaciones
no se publican. `make v3` construye el corpus con
[`construir_corpus_v3.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/construir_corpus_v3.py),
corre la escalera sobre las $320$ consultas y sobre las paráfrasis con
[`eval_flexible.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/eval_flexible.py)
y produce el análisis por estrato con
[`analisis_v3.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/analisis_v3.py).
`make fusion_v3` corre la fusión sensible a la confianza con
[`fusion_v3.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/fusion_v3.py).
El corpus de $811$ documentos (`corpus/corpus_v3.jsonl`), las consultas y los juicios están
publicados, así que las dos evaluaciones se pueden repetir sin acceso a la base operativa.
