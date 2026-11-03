# El registro completo

Los corpus anteriores tenían $17$, $177$ y $811$ documentos. Para observar el método a la escala de
la plataforma, el corpus se extendió a todo su registro: cada deportista, integrante del personal
de apoyo, grupo e institución pasó a ser un documento, junto con los escenarios deportivos, los
eventos y sus disciplinas, las competencias, las acreditaciones, los usuarios de gestión y el
contenido de los reportes. Sobre ese corpus se midieron tres cosas: la escalera de ablación con
las mismas consultas y juicios del corpus v3, en dos corridas; la búsqueda de una persona o una
institución por su nombre, que contesta la parte de P2 que la Versión 1 no podía contestar; y el
efecto de la heterogeneidad del corpus sobre el ranking, con la restricción por función que lo
corrige. Al final de la página se contrasta el método con las cajas de búsqueda que la
plataforma ofrece hoy.

## Composición

| Tipo de objeto | Documentos |
|---|---|
| Deportistas | $643.107$ |
| Grupos | $45.224$ |
| Personas de apoyo | $30.220$ |
| Instituciones | $13.097$ |
| Escenarios | $12.342$ |
| Acreditaciones | $9.685$ |
| Disciplinas de evento | $1.837$ |
| Reportes y cortes de reporte por departamento | $581$ |
| Competencias | $310$ |
| Usuarios de gestión | $222$ |
| Total, incluido el conocimiento funcional del corpus v3 | $757.538$ |

El corpus completo es unas $935$ veces el corpus v3 y unas $44.000$ veces el de la Versión 1, pero
su crecimiento es heterogéneo. El $85\%$ son fichas de personas, cuyo texto es un nombre y unos
atributos, y solo unos $26.000$ documentos describen objetos de conocimiento u operación.

```{note}
Estas evaluaciones usan el registro de la plataforma, que contiene datos de personas, muchas de
ellas menores de edad. Se hicieron con autorización de la organización y con fines académicos.
Ningún nombre ni número de documento queda en el repositorio, en la monografía ni en este sitio:
los informes guardan solo métricas por consulta, la clase de cada consulta y si hubo acierto.
```

## La escalera entre 757.554 documentos: primera corrida

Se repitió la escalera con las mismas $450$ consultas y los mismos juicios del
[corpus v3](04_corpus_v3_811.md) (las $320$ del conjunto final y las $130$ paráfrasis), en dos
universos: los $811$ documentos de v3 solos, y esos mismos documentos más $756.743$ objetos del
registro como distractores, $757.554$ en total. Del registro se excluyeron los objetos que
duplican a los de v3 (reportes curados, Pruebas Regionales, pruebas, reglas y funcionalidades),
de modo que los relevantes son exactamente los mismos en los dos universos. Por esa construcción
el total difiere ligeramente de los $757.538$ documentos del registro, que incluye sus propias
versiones de esos objetos.

Las configuraciones son las de la escalera: BM25, C1 y C3 sobre la descripción; C2, C4 y la
convexa ($\alpha=0{,}8$) sobre el texto con ontología. En esta corrida el índice léxico cubre los
$757.554$ documentos y el denso solo los $15.974$ que describen objetos de conocimiento u
operación; las fichas de personas, grupos e instituciones entran solo al índice léxico. Como
control de implementación, en el universo de $811$ documentos C2 y C4 reproducen consulta por
consulta los resultados de la evaluación original, con un error máximo del orden de $10^{-16}$. La
estadística es la del resto del trabajo, con el *bootstrap* agrupado por documento objetivo.

nDCG@10 promedio de las $450$ consultas. «Tipo conocido» restringe el ranking al tipo del documento
objetivo, tomado de los juicios: es una referencia ideal de contexto perfecto, no una predicción.

| Configuración | 811 documentos | 757.554 documentos | Cambio |
|---|---|---|---|
| BM25 (descripción) | 0,465 | 0,138 | −0,327 |
| C1 · Denso sin ontología | 0,615 | 0,454 | −0,161 |
| C2 · Denso con ontología | 0,714 | 0,576 | −0,139 |
| C3 · RRF sin ontología | 0,634 | 0,319 | −0,315 |
| C4 · RRF con ontología | 0,710 | 0,459 | −0,251 |
| Convexa con ontología | 0,799 | 0,588 | −0,211 |
| C4, tipo conocido | 0,848 | 0,597 | −0,251 |
| Convexa, tipo conocido | 0,889 | 0,685 | −0,205 |

Contrastes principales sobre los $757.554$ documentos. Los cuatro son concordantes: Wilcoxon y
permutación rechazan tras Holm, con un $p$ ajustado de permutación cercano a $0{,}00025$.

| Contraste | Δ nDCG@10 | IC 95 % agrupado por objetivo |
|---|---|---|
| C3 − BM25: aporte de la fusión sobre lo léxico | +0,181 | [+0,144; +0,231] |
| C3 − C1: fusión frente al denso, sin ontología | −0,135 | [−0,199; −0,075] |
| C2 − C1: aporte de la ontología al denso | +0,122 | [+0,085; +0,158] |
| C4 − C3: aporte de la ontología al híbrido | +0,140 | [+0,097; +0,183] |

Todas las configuraciones pierden al crecer el universo unas $935$ veces, pero no por igual. BM25
es la que más pierde: con más de seiscientas mil fichas que comparten nombres de deportes,
regiones e instituciones, la coincidencia de palabras deja de discriminar, y la fusión por rango
hereda ese daño. C3 cae $0{,}315$ y queda claramente por debajo del denso sin ontología ($-0{,}135$),
la dirección que el corpus v3 ya mostraba y que a esta escala se vuelve concordante. La ontología,
en cambio, conserva su aporte: mejora al denso en $0{,}122$ y al híbrido en $0{,}140$. Su efecto sobre
el híbrido incluso crece entre universos de forma concordante, mientras que el crecimiento de su
efecto sobre el denso no es concordante. La convexa con ontología es la mejor configuración libre
($0{,}588$) y supera a C4, pero frente al denso con ontología la diferencia ($+0{,}013$) no es
concordante y su intervalo incluye el cero.

A esta escala, P1 se sostiene solo en parte: el híbrido supera a la búsqueda léxica pero no al
denso, y la fusión por rango es la configuración que más se degrada con los distractores. P3 sale
reforzada, porque el aporte de la ontología no se diluye cuando los relevantes compiten con
setecientos cincuenta mil distractores.

### Los tres límites de la primera corrida

La primera corrida tenía tres límites. El índice denso cubría solo $15.974$ documentos, de modo
que las fichas de personas, grupos e instituciones no competían en la lista densa y las cifras de
C1, C2 y la convexa quedaban sobrestimadas. Los contrastes de la ontología comparaban el texto
enriquecido con la descripción original, sin descartar que cualquier texto más largo produjera la
misma mejora. Y los juicios son los del corpus v3, así que un objeto nuevo pertinente que no fue
juzgado cuenta como no relevante; la evaluación mide la recuperación de objetivos conocidos. La
segunda corrida corrige los dos primeros límites. El tercero sigue en pie.

## Validación con cobertura densa completa

La segunda ejecución sobre el registro se fijó por escrito el 28 de octubre de 2026, antes de
calcular los resultados. El protocolo conserva las $450$ consultas y sus juicios, no añade ninguna
evaluación independiente y congela el mismo universo de $757.554$ documentos.

### Qué cambió respecto de la primera corrida

Cada uno de los $757.554$ documentos recibió un vector real de `jina-embeddings-v3` ($1.024$
dimensiones, tarea de pasaje), cada consulta se codificó con la tarea de consulta y se comparó por
coseno exacto con todos los documentos, sin búsqueda aproximada y sin dejar fuera ninguna ficha.
En total se codificaron $760.267$ textos únicos: los $757.554$ documentos más las variantes de los
$811$ documentos de v3. Deduplicar textos solo evita repetir cómputo; no saca documentos del
ranking. La revisión del modelo y el criterio de desempate por identificador no cambiaron.

El cómputo se hizo en una GPU A100 de un entorno temporal en la nube, con autorización de la
organización; los textos y los vectores se usaron solo para la evaluación y no se conservan en
él. Antes de usar los vectores se comprobó que coinciden con los calculados en el equipo local:
el coseno entre ambos fue superior a $0{,}99999$ y el error absoluto máximo de $2{,}6\times10^{-7}$.
Como control de implementación, BM25 sobre la descripción original reproduce el $0{,}138$ de la
primera corrida.

### Los cinco brazos

Para que la única diferencia entre brazos fuera la representación de los documentos evaluados,
los $756.743$ distractores conservan su descripción original en todos los brazos y solo cambia el
texto de los $811$ documentos de v3.

| Brazo | Qué es | Qué descarta si la ontología le gana |
|---|---|---|
| Descripción original | el texto sin cambios | es la base |
| Ontología | la descripción enriquecida, como en C2 y C4 | es el tratamiento |
| Repetición | la descripción repetida hasta igualar la longitud del texto con ontología | que la mejora se deba solo a tener un texto más largo |
| Vecinos por TF-IDF | la descripción ampliada con los términos más pesados de sus cinco vecinos por TF-IDF, sin usar la ontología ni las consultas | que baste con añadir vocabulario relacionado tomado del propio corpus |
| Metadatos planos | la descripción ampliada con título, subtítulo y facetas del propio documento, sin recorrer clases ni relaciones | que baste con poner en el texto la información estructurada del documento |

Los tres controles se recortaron al mismo número de subpalabras que el texto con ontología,
medido con el tokenizador del modelo, y la auditoría confirmó la igualdad en los $811$ documentos:
$160{,}4$ subpalabras en promedio, frente a $68{,}2$ de la descripción original. El control de
metadatos planos comparte origen de dominio con la ontología, así que la comparación con él pone a
prueba la organización del conocimiento en clases y relaciones, con el mismo conocimiento de
partida. Es el control más exigente.

### Ontología frente a los controles

nDCG@10 promedio de las $450$ consultas, búsqueda libre (sin restricción de tipo).

| Texto de los documentos v3 | BM25 | Denso | RRF | Convexa |
|---|---|---|---|---|
| Descripción original | 0,138 | 0,426 | 0,294 | 0,413 |
| Repetición | 0,182 | 0,405 | 0,348 | 0,417 |
| Vecinos por TF-IDF | 0,134 | 0,374 | 0,285 | 0,366 |
| Metadatos planos | 0,255 | 0,433 | 0,400 | 0,454 |
| Ontología | 0,299 | 0,484 | 0,439 | 0,533 |

Diferencia de nDCG@10 entre el texto con ontología y cada alternativa, con su intervalo del $95\%$
por *bootstrap* agrupado por componentes de objetivos compartidos ($2.000$ réplicas). Los doce
contrastes forman una familia corregida por Holm y los doce son concordantes. El símbolo † marca
el único intervalo agrupado que incluye el cero.

| Ontología frente a | Denso | RRF | Convexa |
|---|---|---|---|
| Descripción original | +0,058 [+0,028; +0,091] | +0,145 [+0,097; +0,192] | +0,120 [+0,080; +0,166] |
| Repetición | +0,078 [+0,045; +0,115] | +0,090 [+0,035; +0,137] | +0,116 [+0,069; +0,167] |
| Vecinos por TF-IDF | +0,110 [+0,077; +0,149] | +0,154 [+0,095; +0,208] | +0,167 [+0,114; +0,231] |
| Metadatos planos | +0,050 [+0,022; +0,085] | +0,039 [−0,017; +0,090] † | +0,079 [+0,041; +0,121] |

Estas cifras no se comparan directamente con las de la primera corrida, que usaba otra cobertura
densa y otro texto para los distractores. Con todos los documentos en el índice denso, el denso
con ontología queda en $0{,}484$, frente al $0{,}576$ de la primera corrida. Lo que sí es claro es el
orden entre brazos dentro de esta corrida. El texto con ontología es el mejor en las cuatro
configuraciones y supera a los cuatro controles en el denso, en RRF y en la convexa.

Repetir la descripción no ayuda al denso ($0{,}405$ frente a $0{,}426$). Ampliarla con los términos de
sus vecinos lo empeora en todas las configuraciones, porque arrastra vocabulario de documentos
parecidos y los vuelve menos distinguibles. Los metadatos planos son el control más fuerte, y su
ventaja sobre la descripción original muestra que una parte del aporte viene simplemente de poner
en el texto la información estructurada del documento. La ontología añade a eso una mejora
concordante en el denso ($+0{,}050$) y en la convexa ($+0{,}079$). En RRF las dos pruebas también
rechazan tras Holm ($p$ ajustados de $0{,}011$ con Wilcoxon y $0{,}008$ con permutación), pero el
intervalo agrupado de la diferencia ($+0{,}039$) incluye el cero, así que ese contraste es el menos
firme de la familia.

Por grupos, de forma exploratoria, la ganancia de la convexa se concentra en las paráfrasis de los
conjuntos difíciles ($0{,}151$ con la descripción original, $0{,}281$ con ontología y a lo sumo $0{,}170$
con los controles), en los reportes y en las pruebas del catálogo. En las reglas de participación
ningún brazo se distingue. La convexa con ontología es la configuración libre con el promedio más
alto ($0{,}533$), aunque su diferencia con el denso con ontología no se contrastó en esta familia.

La conclusión formal es acotada: la ontología supera a las alternativas evaluadas, que son
concretas y no agotan las formas posibles de enriquecer un texto. Con esa salvedad, su aporte no
se explica por la longitud del texto, por el vocabulario de documentos vecinos ni por la sola
presencia de información estructurada.

### ¿Se puede predecir el tipo de objeto?

La primera corrida había mostrado que restringir el ranking al tipo del objetivo sube mucho la
efectividad, pero tomaba el tipo de los juicios. La segunda corrida evaluó si el beneficio se
conserva cuando el tipo hay que predecirlo a partir de la consulta. Se probaron dos predictores,
los dos aplicados sobre el texto con ontología.

| Predictor | Cómo funciona | Entrenamiento |
|---|---|---|
| Clasificador | TF-IDF de palabras (de una y dos) y de caracteres (de tres a cinco) con regresión logística ($C=1$, clases balanceadas), solo con el texto de la consulta | validación cruzada de cinco particiones agrupadas por $114$ componentes de consultas que comparten algún documento relevante; vocabulario y modelo ajustados solo en el entrenamiento de cada partición |
| Ruta semántica | asigna a la consulta el tipo del documento v3 cuya descripción original es más parecida a ella por coseno | ninguno; no consulta los juicios |

nDCG@10 según de dónde sale el tipo ($757.554$ documentos, texto con ontología, cobertura densa
completa).

| Configuración | Libre | Clasificador | Semántico | Tipo conocido |
|---|---|---|---|---|
| Denso | 0,484 | 0,533 | 0,541 | 0,655 |
| RRF | 0,439 | 0,500 | 0,492 | 0,622 |
| Convexa | 0,533 | 0,589 | 0,563 | 0,712 |

El clasificador acierta el tipo en el $86\%$ de las consultas ($387$ de $450$), pero no acierta
ninguna de las $53$ de competencias. Su matriz de confusión (filas: tipo verdadero; columnas: tipo
predicho) muestra dónde caen:

| Tipo verdadero | Competencia | Funcionalidad | Prueba | Regla | Reporte |
|---|---|---|---|---|---|
| Competencia ($53$) | 0 | 0 | 26 | 0 | 27 |
| Funcionalidad ($53$) | 0 | 50 | 0 | 0 | 3 |
| Prueba ($60$) | 0 | 0 | 60 | 0 | 0 |
| Regla ($27$) | 0 | 0 | 0 | 27 | 0 |
| Reporte ($257$) | 0 | 3 | 3 | 1 | 250 |

El fallo en competencias lo produce la propia validación cruzada. Las $53$ consultas de
competencias tienen juicios por facetas que se solapan, así que comparten documentos relevantes
entre sí, forman un único componente y caen completas en la misma partición. Al evaluarlas, el
clasificador no ha visto en entrenamiento ningún ejemplo de esa clase y no puede predecirla. La
validación agrupada es la correcta, porque evita que el clasificador vea en entrenamiento
consultas casi iguales a las de prueba; el 0 de 53 es su efecto secundario y no dice que el
clasificador sea incapaz de reconocer competencias. Sin esa clase acierta $387$ de $397$ consultas
($97{,}5\%$).

Su mejora frente a la búsqueda libre es de $+0{,}050$ en el denso, $+0{,}061$ en RRF y $+0{,}056$ en la
convexa, pero no es concordante. La permutación la detecta ($p$ de Holm entre $0{,}021$ y $0{,}035$) y
Wilcoxon no ($0{,}21$), y los intervalos agrupados son muy anchos (de $-0{,}18$ a $+0{,}21$ en el denso)
porque ese grupo de $53$ consultas pesa en bloque.

La ruta semántica acierta menos, el $69\%$ ($311$ de $450$):

| Tipo verdadero | Competencia | Funcionalidad | Prueba | Regla | Reporte |
|---|---|---|---|---|---|
| Competencia ($53$) | 53 | 0 | 0 | 0 | 0 |
| Funcionalidad ($53$) | 0 | 50 | 1 | 0 | 2 |
| Prueba ($60$) | 0 | 0 | 60 | 0 | 0 |
| Regla ($27$) | 0 | 0 | 0 | 27 | 0 |
| Reporte ($257$) | 31 | 33 | 65 | 7 | 121 |

Resuelve las $53$ de competencias, las $60$ pruebas y las $27$ reglas y $50$ de $53$ funcionalidades,
y confunde muchas de reportes ($121$ de $257$ correctas). Aun así, mejora a la búsqueda libre de
forma concordante en las tres configuraciones: $+0{,}057$ en el denso, $+0{,}053$ en RRF y $+0{,}030$
en la convexa, este último con un intervalo agrupado que apenas excluye el cero ($[+0{,}001;
+0{,}066]$).

Las dos rutas quedan lejos del tipo conocido. El clasificador queda unos $0{,}12$ por debajo del
techo en las tres configuraciones ($-0{,}121$, $-0{,}122$ y $-0{,}123$), de forma concordante.
Restringir por tipo ayuda aun cuando el tipo se predice con errores, pero la mayor parte del margen
hasta el techo depende de predecirlo mejor.

### ¿Mejora la convexa un ordenamiento en dos etapas?

Para comprobar si un ordenamiento en dos etapas mejora la convexa, se reunieron como candidatos
los primeros $100$ documentos de BM25, del denso, de RRF y de la convexa, hasta $400$ por consulta,
sin insertar a mano los relevantes. Sobre ellos se probaron dos variantes con la misma validación
cruzada agrupada en cinco particiones. Una elige el peso $\alpha$ de la convexa solo con las
particiones de entrenamiento, entre $0{,}0$ y $1{,}0$ en pasos de $0{,}1$. La otra es un reordenador
supervisado, una regresión logística ($C=1$, balanceada, con el escalado ajustado solo en
entrenamiento) sobre las puntuaciones normalizadas y las posiciones léxica y densa, sin
identificadores de documento.

nDCG@10 de cada variante y diferencia con la convexa de $\alpha=0{,}8$ en el mismo modo de búsqueda.
El asterisco marca las diferencias concordantes tras Holm en la familia de ocho comparaciones.

| Modo de búsqueda | Convexa ($\alpha=0{,}8$) | $\alpha$ por validación cruzada | Diferencia | Reordenador supervisado | Diferencia |
|---|---|---|---|---|---|
| Libre | 0,533 | 0,523 | −0,010 | 0,482 | −0,051 \* |
| Tipo del clasificador | 0,589 | 0,554 | −0,035 \* | 0,521 | −0,068 \* |
| Tipo semántico | 0,563 | 0,555 | −0,008 | 0,520 | −0,042 \* |
| Tipo conocido | 0,712 | 0,677 | −0,036 \* | 0,643 | −0,070 \* |

Ninguna de las dos variantes supera a la convexa con $\alpha=0{,}8$. El $\alpha$ elegido fue $0{,}8$ en
tres particiones y $0{,}9$ en las otras dos, y su diferencia con la convexa fija no es significativa
en la búsqueda libre ni con la ruta semántica; con el clasificador y con el tipo conocido incluso
empeora de forma concordante. El reordenador empeora a la convexa de forma concordante en las
cuatro variantes, entre $-0{,}042$ y $-0{,}070$.

Si los candidatos se ordenaran de forma perfecta, el nDCG@10 llegaría a $0{,}876$. Los documentos
relevantes casi siempre están entre los candidatos y lo que falta es ordenarlos mejor. Con $450$
consultas y los atributos usados, un reordenador supervisado no aprende ese orden mejor que la
regla convexa, que no necesita entrenamiento.

### Lo que la validación no resuelve

Las consultas y los juicios son los mismos de v3, sin evaluación independiente, y los
distractores agregados no recibieron juicios nuevos. Los controles son alternativas concretas y
no agotan las formas posibles de enriquecer un texto. La predicción del tipo y el reordenador se
validaron de forma interna por grupos, y eso tampoco equivale a una validación externa.

## Búsqueda persona a persona (P2)

El control sin nombre propio de la Versión 1 dejó a P2 sin contrastar, porque las entidades no
figuraban en ningún documento (ver [la Versión 1](02_version1_17_reportes.md)). En el registro
completo cada persona sí es un documento, y la pregunta se puede plantear de forma directa: dado un
nombre escrito como lo escribiría un usuario, ¿qué componente devuelve a la persona correcta?

### Los dos componentes que se comparan

El primero es el ranking C4, el híbrido con ontología, aplicado sin cambios a las fichas de
personas. El segundo es un diccionario de entidades, el componente que el diseño de privacidad
separa del índice semántico, que resuelve la mención contra los nombres completos.

Para cada término $t$ de la consulta, el diccionario busca términos $u$ de los nombres con una
similitud

$$
\sigma(t,u)=\begin{cases}
1 & \text{si } u=t,\\
0{,}9 & \text{si } t \text{ es el último término y es prefijo de } u,\\
0{,}97-0{,}05\,e(t,u) & \text{si } e(t,u)\le e_{\max}(t),\\
\mathrm{JW}(t,u)-0{,}08 & \text{si } \mathrm{JW}(t,u)\ge 0{,}93 \text{ y } |t|\ge 5,
\end{cases}
$$

donde $e$ es la distancia de Damerau–Levenshtein (el número mínimo de inserciones, borrados,
sustituciones o trasposiciones de letras vecinas), $e_{\max}$ vale $1$ para términos de cuatro a
siete caracteres y $2$ desde ocho, y $\mathrm{JW}$ es la similitud de Jaro–Winkler, que premia las
coincidencias al principio de la palabra. Los candidatos se preseleccionan con un índice de
trigramas de caracteres: solo se comparan los términos que comparten al menos el $40\%$ de los
trigramas de $t$.

Si $k$ términos de la consulta $q$ encuentran pareja en el nombre de $d$, con similitud media
$\bar\sigma$, el nombre recibe

$$
s(d)=\bar\sigma^{2}\left(0{,}85\,\frac{k}{|q|}+0{,}15\,\min\!\left(1,\frac{k}{|d|}\right)\right)+0{,}02\,\mathbb{1}[\text{orden}]+0{,}03\,\mathbb{1}[\text{exacto}],
$$

donde los dos indicadores premian que los términos aparezcan en el orden escrito y que la consulta
coincida con el nombre completo. Se exige $k\ge\min(2,|q|,|d|)$ y $s(d)\ge0{,}55$. Elevar $\bar\sigma$
al cuadrado hace que una coincidencia exacta gane a una aproximada aunque el nombre aproximado sea
más corto. Un número de documento se empareja de forma exacta y se antepone a cualquier nombre. Los
pesos se fijaron a mano antes de la evaluación y no se ajustaron sobre ella.

### La evaluación

Con una semilla fija se tomó una muestra aleatoria de $300$ deportistas y $75$ instituciones del
registro. La muestra se toma en memoria en cada ejecución y el informe registra solo la clase de
consulta y si hubo acierto. Cada deportista se buscó de cinco formas:

| Forma | Qué se escribe |
|---|---|
| Nombre exacto | el nombre como figura en la ficha |
| Sin tildes y en minúsculas | el mismo nombre normalizado |
| Un error de digitación | una letra cambiada, quitada o traspuesta en la palabra más larga |
| A medio escribir | la última palabra truncada |
| Número de documento | el número, sin el nombre |

Cada institución se buscó con su nombre exacto y con un error de digitación. La medida principal es
Acierto@1, que la persona o la institución buscada sea el primer resultado; se reportan también
Acierto@5 y MRR.

| Clase de consulta | $n$ | Acierto@1 diccionario | Acierto@1 C4 | Acierto@5 diccionario | Acierto@5 C4 | MRR diccionario | MRR C4 |
|---|---|---|---|---|---|---|---|
| Deportista · nombre exacto | 300 | 0,987 | 0,877 | 1,000 | 0,947 | 0,993 | 0,910 |
| Deportista · sin tildes, minúsculas | 300 | 0,987 | 0,877 | 1,000 | 0,947 | 0,993 | 0,910 |
| Deportista · un error de digitación | 300 | 0,977 | 0,573 | 0,993 | 0,727 | 0,985 | 0,645 |
| Deportista · a medio escribir | 300 | 0,970 | 0,513 | 0,990 | 0,707 | 0,979 | 0,600 |
| Deportista · número de documento | 300 | 1,000 | 0,947 | 1,000 | 1,000 | 1,000 | 0,973 |
| Institución · nombre exacto | 75 | 1,000 | 0,867 | 1,000 | 0,933 | 1,000 | 0,895 |
| Institución · un error de digitación | 75 | 0,987 | 0,640 | 1,000 | 0,747 | 0,993 | 0,686 |

En la clase «a medio escribir» el diccionario se evalúa en modo de sugerencia.

### Lectura

Los dos componentes se separan con claridad. Con el nombre exacto, el diccionario pone primera a
la persona buscada en el $98{,}7\%$ de los casos. El $1{,}3\%$ restante son homónimos, personas
distintas con el mismo nombre, y en todos esos casos la persona buscada queda entre las cinco
primeras. El ranking C4 llega al $87{,}7\%$. La diferencia crece con la perturbación: con un error de
digitación el diccionario conserva el $97{,}7\%$ y C4 cae al $57{,}3\%$, y con el nombre a medio escribir
C4 baja al $51{,}3\%$.

El término truncado o mal escrito no coincide con ningún término del índice léxico, así que C4 solo
se apoya en las palabras completas, que comparten muchas otras personas, y las fichas de personas
no tienen vector denso que compense, porque su contenido se reduce a un nombre y unos atributos.
Quitar las tildes no cambia ninguno de los dos componentes, lo que confirma que la normalización
del texto absorbe esa variación. Las instituciones se comportan igual.

El diccionario responde en $37$ ms en la mediana y $47$ ms en el percentil $95$ sobre los $757.538$
documentos, y en $3{,}7$ ms en el percentil $95$ en modo de sugerencia, en el mismo equipo personal de
la campaña de costo y con una implementación compilada del recuperador.

Esto contesta la parte de P2 que la Versión 1 no podía contestar, y la respuesta contradice la
formulación original. Para la búsqueda por entidad la fusión del híbrido no basta: hace falta un
componente de resolución de entidades. Sin él, el mejor ranking del trabajo pierde $11$ puntos con
el nombre exacto, $40$ con un error de digitación y $46$ con una palabra a medio escribir. El
análisis del realce ya lo anticipaba, al mostrar que un realce sobre los documentos que comparten
la clase de la entidad no discrimina y que la mención concreta debe resolverse contra un
diccionario. La arquitectura recomendada usa el ranking semántico para el conocimiento funcional y
un diccionario de entidades para los nombres propios, y presenta juntos los resultados de ambos.

## Heterogeneidad del corpus y restricción por función

Al pasar de $811$ a $757.538$ documentos, el corpus mezcla objetos que comparten vocabulario sin
compartir función. En una búsqueda sin restricción, el ranking C4 empeoró en consultas que antes
resolvía. La consulta «halterofilia» devolvió primero un escenario llamado «Coliseo de
Halterofilia» en lugar de la prueba, y siete de las treinta consultas del corpus de precisión
salieron de su posición esperada. Es el mismo mecanismo que perjudicaba a la fusión por rango en el
corpus v3: un documento de otro tipo que comparte palabras con la consulta entra como distractor.

### La restricción

La plataforma ofrece una caja de búsqueda en cada pantalla de listado, y cada una tiene una
función: la de deportistas busca deportistas, la de escenarios busca escenarios. Para
formalizarlo, cada contexto de búsqueda $b$ declara el conjunto $T_b$ de tipos de objeto que puede
devolver, los filtros que acepta y, cuando aplica, un filtro obligatorio que fija el contexto, como
el evento que se está viendo o el usuario que consulta sus propias competencias. El ranking C4 se
calcula sobre todo el corpus y después se conserva solo

$$
\{\,d : \mathrm{tipo}(d)\in T_b\,\},
$$

lo que preserva el orden relativo de la fusión. Cada resultado se verifica contra $T_b$ y contra el
contexto antes de devolverse. La restricción depende solo de la función de la búsqueda; qué
pantallas ve cada rol de usuario lo decide la plataforma. En total se definieron $22$ contextos de
búsqueda.

### Resultados

Con la restricción, las treinta consultas del corpus de precisión volvieron a su posición esperada,
incluidas las nueve que preguntan por el contenido de un reporte, como «documentos rechazados de
deportistas en Magdalena» o «qué reporte trae el tipo de sangre y la EPS».

Para comprobar el aislamiento se enviaron $1.826$ consultas cruzadas a los $22$ contextos, con
nombres de personas, números de documento, escenarios, eventos, deportes, reportes y títulos reales
de cada tipo del índice. Ningún contexto devolvió un tipo de objeto fuera de $T_b$, y dos contextos
con filtros obligatorios distintos (dos eventos, dos usuarios) nunca compartieron un resultado.

Además se tomaron, para cada contexto, hasta $25$ objetos reales de sus tipos, que se buscaron por
su nombre exacto y con una letra menos. Con el nombre exacto el objeto quedó entre los cinco
primeros en el $100\%$ de los casos, y con el error, entre el $88$ y el $100\%$ según el contexto. La
búsqueda restringida tarda $14$ ms en la mediana y $47$ ms en el percentil $95$.

## Contraste con las cajas de búsqueda actuales

Las cajas de búsqueda que la plataforma ofrece hoy en sus pantallas de listado comparan una
subcadena de un solo campo. Sirven como línea base: con las mismas consultas, la tabla compara lo
que devolvían el 28 de octubre de 2026 con lo que devuelve el método (C4 con diccionario de
entidades y restricción por función). «Posición» es la del primer resultado correcto.

| Contexto | Consulta | Caja actual | Método |
|---|---|---|---|
| Escenarios | colizeo | 0 resultados | posición 1 |
| Escenarios | pisina | 0 resultados | posición 1 |
| Escenarios | cancha de futbol / cancha de fútbol | 472 / 41: la tilde cambia el resultado | los mismos cinco primeros |
| Eventos | juegos nacionales | 0: las palabras no van seguidas en el nombre | posición 2 |
| Eventos | voleibol | 0: no busca por deporte | posición 1 |
| Competencias | futbol salon / futsal | 0 / 16, y 13 con tildes | posición 1 en las tres |
| Deportes | futsal, ping pong, halterofilia | 0: sin sinónimos | posición 1 |
| Disciplinas de un evento | futsal, tenis de mesa | 0 | posición 1 |
| Reportes | documentos rechazados | «Sin reportes» | posición 1 |

La caja actual distingue tildes, no tolera errores de digitación, no conoce sinónimos, exige que
las palabras vayan seguidas y no busca en campos que su propio texto de ayuda promete. Cada una de
esas fallas corresponde a una pieza del método:

| Falla de la caja actual | Pieza del método que la resuelve |
|---|---|
| la tilde cambia el resultado | la normalización del texto |
| un error de digitación da cero resultados | el diccionario de entidades |
| no conoce sinónimos («futsal», «ping pong») | la ontología |
| exige palabras contiguas o no busca en ciertos campos | la recuperación densa |

Las consultas de la tabla las escribió el autor a partir de fallas observadas, de modo que ilustran
el contraste sin estimar una tasa de error de la caja actual. La restricción por función se comparó
con la búsqueda sin restricción, pero queda pendiente compararla con la combinación convexa, que
ataca el mismo daño por otra vía, para saber si basta una de las dos o si se complementan. Como la
restricción se aplica después de fusionar, elimina los distractores de otros tipos y deja intacto el
orden dentro de un mismo tipo.

## Lo que dejó esta etapa

A la escala de la plataforma, la ontología conserva su aporte y supera a tres controles de la misma
longitud, la fusión por rango es la configuración que más se degrada y la convexa es la
configuración libre con el promedio más alto. La búsqueda de personas necesita un diccionario de
entidades separado del ranking, y la heterogeneidad del corpus se controla restringiendo cada
búsqueda a los tipos de su función; cuando el tipo hay que predecirlo, un predictor sin
entrenamiento ya mejora la búsqueda libre, aunque lejos del techo. El mismo recuperador responde en
$47$ ms en el percentil $95$ sobre $757.538$ documentos. Los límites comunes a todo el trabajo, en
especial que las consultas no son de usuarios, se discuten en [validez y robustez](06_validez_y_robustez.md).

## Cómo reproducirlo

Estas evaluaciones no se pueden reconstruir desde el repositorio, porque requieren las fichas del
registro completo, que contienen datos personales y no se publican. Lo que sí está publicado son
los agregados y las métricas por consulta. La primera corrida de la escalera está en
[`resultados/escalamiento/`](https://github.com/luispenaranda08/semantic_search_engine/tree/main/experimentos/resultados/escalamiento)
(`registro.json` para los $757.554$ documentos y `v3.json` para el universo de $811$). La carpeta de
la validación con cobertura densa completa, dentro de `experimentos/resultados/`, guarda el
protocolo escrito antes de calcular, el informe, las estadísticas, la comprobación de paridad de
los vectores, el enrutamiento, el ordenamiento en dos etapas por consulta, las métricas por
consulta de cada brazo y los scripts de cálculo y de estadística. La búsqueda persona a persona y
la restricción por función se reportan con los agregados de la monografía; ningún nombre, número
de documento ni consulta con datos de una persona se conserva.
