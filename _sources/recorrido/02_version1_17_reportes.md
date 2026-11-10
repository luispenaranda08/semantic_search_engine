# Versión 1: diecisiete reportes

La primera versión del buscador se limita a los diecisiete reportes que la plataforma ofrece,
con prioridad en los cinco que concentran el $83\%$ de la demanda real (ver
[la demanda observada](01_demanda.md)). Sobre ese corpus se corrió la escalera de ablación
completa con cinco conjuntos de consultas, la estadística del plan de análisis, los barridos de
hiperparámetros, de dimensión y de fragmentación, las fusiones alternativas y la campaña de
costo computacional. Todas las cifras de esta página se calcularon sobre los diecisiete
reportes, con el codificador `jina-embeddings-v3` de $1.024$ dimensiones y sus tareas de
recuperación de consulta y de pasaje activadas, salvo donde se indique otro corpus.

## El corpus y el documento enriquecido

Cada documento es la descripción en lenguaje natural de un reporte. Las descripciones tienen
entre $64$ y $184$ palabras, con una media de $103$, y no contienen datos personales: la
construcción del corpus aborta si encuentra correos electrónicos o secuencias numéricas largas.

Cada reporte $d$ tiene dos componentes: su descripción $d_{\text{desc}}$ y sus metadatos de
ontología $o_d$ (entidades que cubre, sinónimos y preguntas de negocio que responde). El
documento enriquecido concatena a la descripción la serialización de un subconjunto selectivo
de esos metadatos:

$$
d' = d_{\text{desc}} \oplus \phi(o_d).
$$

El subconjunto se elige a propósito, siguiendo el resultado de ECLASS de que inyectar
metadatos escogidos rinde más que volcar todos los atributos. Solo $9$ de los $17$ reportes
tienen bloque de ontología; para los otros $8$, el documento enriquecido coincide con la
descripción y la ontología no puede cambiar nada. Esa cobertura parcial resultó importante, como
se ve más abajo.

## Las configuraciones

La escalera tiene cinco configuraciones anidadas y una referencia léxica. El detalle de cada
una está en [el método](../tesis/metodo.md); aquí basta con lo que distingue a cada peldaño.

| Configuración | Puntuación | Qué aísla |
|---|---|---|
| BM25 (referencia) | BM25 sobre $d_{\text{desc}}$ | línea base léxica clásica |
| C1 · Denso puro | coseno entre vectores de la consulta y de $d_{\text{desc}}$ | línea base neuronal |
| C2 · Denso con ontología | coseno con $d'$ | efecto de la ontología en el denso (P3) |
| C3 · Híbrido sin ontología | RRF de BM25 y denso sobre $d_{\text{desc}}$ | aporte de la señal léxica (P1, P2) |
| C4 · Híbrido con ontología | RRF sobre $d'$ | efecto de la ontología en el híbrido (P3) |
| C5 · C4 con realce | $s_{\text{RRF}}\cdot(1+\lambda\,\mathbb{1}_{\text{entidad}})$ | efecto del realce por entidad (P5) |

BM25 usa $k_1=1{,}5$ y $b=0{,}75$, con un analizador en español que pasa a minúsculas, quita
tildes, descarta palabras vacías y reduce cada palabra a su raíz con Snowball; solo puntúa los
documentos que comparten al menos un término con la consulta. La fusión por rango recíproco
suma, para cada documento, $1/(k+\text{posición})$ en cada lista, con $k=60$. El realce multiplica
la puntuación fusionada por $1+\lambda$, con $\lambda=0{,}2$, cuando la consulta menciona una
clase de entidad que el documento cubre. Ninguno de estos valores se ajustó sobre los datos de
evaluación, y ningún componente se entrena: el codificador se usa congelado, de modo que no hay
partición entre entrenamiento y prueba y todas las consultas son de evaluación.

## Los conjuntos de evaluación

Todos los conjuntos usan un protocolo de objetivo conocido (*known-item*): cada consulta apunta
a un reporte objetivo, que recibe grado de relevancia $2$, y algunas añaden reportes secundarios
con grado $1$. El protocolo es estándar y no fabrica juicios humanos, pero las consultas
derivadas de los documentos comparten vocabulario con ellos. Por eso el valor absoluto de las
métricas no debe leerse como precisión de producción; lo que se interpreta es la comparación
entre configuraciones bajo el mismo protocolo.

| Conjunto | Consultas con juicio | Cómo se construyó | Estratos o niveles |
|---|---|---|---|
| Sintético | $40$ (de $51$) | escrito a partir de títulos, entidades y sinónimos de la ontología y del mapeo de competencias | entidad exacta $17$, ambigua $13$, documento largo $10$; las $11$ de competencias no tienen documento relevante en la Versión 1 y se excluyen de las métricas |
| Ampliado desde firmas | $127$ | una consulta por patrón distinto de firma del historial; relevante el reporte que se ejecutó (juicio *silver*) | entidad exacta $55$, operacional $35$, documento largo $25$, ambigua $12$; $50$ marcadas como candidatas a anotación por expertos |
| Control sin nombre | $55$ | las consultas de entidad exacta del ampliado con el nombre propio borrado | un solo estrato |
| Difícil A | $52$ | paráfrasis y expresiones coloquiales del propósito de $13$ reportes, redactadas para no compartir vocabulario con la descripción | niveles A, B y C calculados por solape de raíces |
| Difícil B | $78$ | réplica con consultas nuevas, seis por reporte en cuatro registros (pregunta, telegráfico, coloquial y administrativo) | mismos niveles calculados |
| Difíciles A y B | $130$ | unión de los dos anteriores para la estadística | con puente $52$, sin puente $21$, con solape $57$ |

### El conjunto sintético

Es el conjunto original de la escalera: $51$ consultas escritas a mano a partir de artefactos
reales (títulos de reporte, entidades y sinónimos de la ontología, mapeo de competencias). Las
$11$ consultas de competencias no tienen documento relevante en la Versión 1, por diseño; miden
el vacío de cobertura del dominio de competencias y quedan fuera de las métricas de calidad. Los
nombres propios de las consultas de entidad exacta son sintéticos: dan forma realista a la
consulta, cuyo objetivo es el reporte y no la persona.

### El conjunto ampliado desde firmas

Cada consulta parte de una firma del historial, la estructura de una solicitud real (reporte
ejecutado, columnas y filtros) sin los valores buscados, y su texto se sintetiza a partir de
los filtros reales. La unidad de muestreo es el *patrón distinto* de firma. Si se hubiera tomado
cada combinación con un nombre propio sustituible, la misma consulta se habría repetido con
distintos nombres sintéticos, inflando el tamaño muestral sin añadir información
(pseudo-replicación). Además se eliminaron los textos duplicados entre estratos. Es el conjunto
más parecido al uso real, porque sus consultas reproducen lo que la gente efectivamente pidió,
y también el más cercano al techo, porque comparten el vocabulario de los filtros del propio
reporte.

### El control sin nombre propio

Cada consulta del estrato de entidad exacta del ampliado se repite con el nombre propio
borrado. Si el nombre contribuyera a la recuperación, el desempeño debería bajar al quitarlo. Su
resultado, más abajo, decide qué mide en realidad ese estrato.

### Los conjuntos difíciles A y B

En los conjuntos sintético y ampliado la mayoría de las consultas queda en la primera posición
para todas las configuraciones, lo que limita el poder estadístico. El conjunto difícil A
contiene paráfrasis del propósito de $13$ reportes; los reportes de pruebas de caídas se
excluyeron porque su significado de negocio no está confirmado. La dificultad se calcula, en
lugar de asignarse a mano, con el solape de raíces Snowball entre la consulta y el documento:

| Nivel | Definición | Qué puede ayudar |
|---|---|---|
| Con puente | la consulta no comparte raíces con la descripción, pero sí con el bloque de ontología | la ontología |
| Sin puente | no comparte raíces ni con la descripción ni con la ontología | solo la semántica densa |
| Con solape | comparte al menos una raíz con la descripción | también la señal léxica |

El nivel sin puente sirve de control contra el sesgo de haber redactado consultas con sinónimos de la
ontología. Conviene no confundir los nombres: el *conjunto* difícil A es el primer grupo de $52$
paráfrasis, y el *nivel* A es una categoría de solape que existe dentro de los dos conjuntos.

El conjunto difícil B se redactó después de conocer los resultados de A, para poner a prueba los
hallazgos formulados al mirarlo. No se ajustó a ningún sistema ni se descartó ninguna consulta
por su resultado, pero no es una prueba ciega, y la tesis lo presenta como réplica. Las consultas
de los dos conjuntos las redactó el autor y deben someterse a revisión de expertos.

## Resultados globales

| Configuración | Sintético ($n=40$) | Ampliado ($n=127$) | Difícil A ($n=52$) | Difícil B ($n=78$) |
|---|---|---|---|---|
| BM25 (referencia) | 0,819 | 0,887 | 0,186 | 0,422 |
| C1 · Denso puro | 0,866 | 0,932 | 0,712 | 0,783 |
| C2 · Denso con ontología | 0,931 | 0,928 | 0,835 | 0,837 |
| C3 · Híbrido sin ontología | 0,893 | 0,943 | 0,686 | 0,778 |
| C4 · Híbrido con ontología | 0,948 | 0,960 | 0,788 | 0,835 |
| C5 · C4 con realce | 0,924 | 0,944 | 0,739 | 0,773 |

El híbrido con ontología (C4) es la mejor configuración en el sintético y en el ampliado. En los
dos conjuntos difíciles gana el denso con ontología (C2), y el híbrido queda igual o por debajo.
BM25 es la configuración de menor desempeño en los cuatro conjuntos. En el sintético su
Recall@100 es $0{,}950$, por debajo de $1{,}000$, porque BM25 solo devuelve documentos que
comparten algún término con la consulta y, cuando no hay coincidencia, el objetivo no aparece.
En el difícil A su nDCG@10 es bajo por construcción, porque en los niveles con puente y sin puente la consulta no
comparte raíces con la descripción del documento. Las demás configuraciones devuelven los
diecisiete documentos, de modo que su Recall@100 vale trivialmente $1$ y no discrimina.

## Estadística de la escalera

Las cinco comparaciones de la escalera forman una familia: C3 frente a BM25, C3 frente a C1, C2
frente a C1, C4 frente a C3 y C5 frente a C4. Cada una se contrasta con la prueba de Wilcoxon
pareada y con una prueba de permutación de signos, los $p$-valores se ajustan con Holm dentro de
la familia y la diferencia se declara concordante solo si las dos pruebas la rechazan. Las
comparaciones sobre los conjuntos fijados en el plan (sintético, ampliado, difícil A) son
confirmatorias; el difícil B es una réplica.

Diferencia media de nDCG@10 (primera configuración menos segunda) y, entre paréntesis, el mayor
de los dos $p$-valores ajustados por Holm. El asterisco marca las concordantes.

| Comparación | Sintético | Ampliado | Difícil A | Difícil B | A+B |
|---|---|---|---|---|---|
| C3 − BM25 (P1) | +0,073 (0,021) \* | +0,056 (0,009) \* | +0,500 (<0,001) \* | +0,356 (<0,001) \* | +0,413 (<0,001) \* |
| C3 − C1 (P1) | +0,026 (0,820) | +0,011 (0,672) | −0,026 (0,214) | −0,005 (0,814) | −0,013 (0,356) |
| C2 − C1 (P3, denso) | +0,065 (0,027) \* | −0,004 (0,672) | +0,122 (0,002) \* | +0,054 (0,006) \* | +0,081 (<0,001) \* |
| C4 − C3 (P3, híbrido) | +0,056 (0,043) \* | +0,016 (0,406) | +0,102 (0,072) | +0,058 (0,157) | +0,075 (0,011) \* |
| C5 − C4 (P5) | −0,024 (0,820) | −0,016 (0,250) | −0,049 (0,035) \* | −0,063 (0,023) \* | −0,057 (0,001) \* |

La prueba de Wilcoxon descarta las consultas en las que las dos configuraciones obtienen la
misma métrica, así que el poder real de cada contraste lo da el número de pares con diferencia
no nula y no el total de consultas.

| Comparación | Sintético | Ampliado | Difícil A | Difícil B | A+B |
|---|---|---|---|---|---|
| C3 − BM25 | 11/40 | 31/127 | 45/52 | 45/78 | 90/130 |
| C3 − C1 | 11/40 | 16/127 | 19/52 | 23/78 | 42/130 |
| C2 − C1 | 10/40 | 11/127 | 21/52 | 21/78 | 42/130 |
| C4 − C3 | 10/40 | 13/127 | 34/52 | 30/78 | 64/130 |
| C5 − C4 | 3/40 | 5/127 | 8/52 | 15/78 | 23/130 |

Las dos tablas explican por qué ampliar el número de consultas no bastaba. En el ampliado, la
comparación C4 frente a C3 se apoya en $13$ pares con diferencia no nula entre $127$ consultas,
porque en las demás todas las configuraciones dejan el objetivo primero. En la unión de los
difíciles esa misma comparación tiene $64$ pares de $130$, y con ese poder resulta concordante
($+0{,}075$).

El híbrido sin ontología supera a BM25 de forma concordante en los cuatro conjuntos y en la
unión, incluida la réplica B, así que la primera parte de la hipótesis H1 se sostiene. La
segunda parte, que el híbrido supere también al denso puro, no se sostiene: la diferencia entre
C3 y C1 es pequeña, cambia de signo y no es significativa en ningún conjunto. Casi toda la
ventaja del híbrido sobre BM25 la aporta el codificador denso por sí solo; en el metaanálisis de
los difíciles, C1 frente a BM25 vale $+0{,}442$ (ver [validez y robustez](06_validez_y_robustez.md)).

## Resultados por estrato (P2)

nDCG@10 por estrato en el conjunto ampliado.

| Configuración | Entidad exacta ($n=55$) | Operacional ($n=35$) | Documento largo ($n=25$) | Ambigua ($n=12$) |
|---|---|---|---|---|
| BM25 | 0,862 | 0,893 | 0,910 | 0,938 |
| C1 · Denso puro | 0,925 | 0,961 | 0,945 | 0,854 |
| C2 · Denso con ontología | 0,913 | 0,961 | 0,945 | 0,866 |
| C3 · Híbrido sin ontología | 0,926 | 0,957 | 0,950 | 0,969 |
| C4 · Híbrido con ontología | 0,980 | 0,941 | 0,946 | 0,953 |
| C5 · C4 con realce | 0,980 | 0,930 | 0,880 | 0,953 |

nDCG@10 por estrato en el conjunto sintético.

| Configuración | Entidad exacta ($n=17$) | Ambigua ($n=13$) | Documento largo ($n=10$) |
|---|---|---|---|
| BM25 | 0,883 | 0,846 | 0,677 |
| C1 · Denso puro | 0,875 | 0,894 | 0,815 |
| C2 · Denso con ontología | 0,931 | 0,956 | 0,900 |
| C3 · Híbrido sin ontología | 0,972 | 0,920 | 0,721 |
| C4 · Híbrido con ontología | 0,976 | 0,962 | 0,884 |
| C5 · C4 con realce | 0,957 | 0,962 | 0,819 |

En el estrato de entidad exacta del ampliado, C4 alcanza $0{,}980$, frente a $0{,}926$ de C3,
$0{,}925$ del denso puro y $0{,}862$ de BM25. El híbrido sin ontología no mejora al denso puro en
ese estrato ($+0{,}001$, $p$ de Holm de $1{,}000$), de modo que la ventaja aparece solo cuando se
añade la ontología, y la comparación C4 frente a C3 en el estrato ($+0{,}054$) tampoco es
concordante ($p$ de Holm de $0{,}069$ con Wilcoxon y $0{,}054$ con permutación). En el sintético,
C3 supera al denso puro en el estrato ($0{,}972$ frente a $0{,}875$), sin significancia con $17$
consultas ($p$ de Holm de $0{,}577$). Los contrastes por estrato no tienen una corrección global
entre estratos y se leen como exploratorios; el estrato ambiguo, con $12$ consultas, no admite
conclusiones.

## El control sin nombre propio

nDCG@10 de las $55$ consultas del estrato de entidad exacta del ampliado, con la consulta
original y con el nombre propio borrado.

| Configuración | Con nombre | Sin nombre | Diferencia |
|---|---|---|---|
| BM25 | 0,862 | 0,854 | −0,008 |
| C1 · Denso puro | 0,925 | 0,966 | +0,041 |
| C2 · Denso con ontología | 0,913 | 1,000 | +0,087 |
| C3 · Híbrido sin ontología | 0,926 | 0,953 | +0,027 |
| C4 · Híbrido con ontología | 0,980 | 1,000 | +0,020 |
| C5 · C4 con realce | 0,980 | 1,000 | +0,020 |

Al quitar el nombre, el desempeño sube en cinco de las seis configuraciones; solo BM25 baja, y
marginalmente. Los nombres sintéticos no figuran en ningún documento del corpus, que describe
reportes y no personas. Para la señal léxica son términos sin coincidencia y para la densa, un
elemento de distracción. El estrato mide entonces cuánto describe la consulta el tema de un
reporte, y no la capacidad de localizar una entidad, por lo que la hipótesis H2 no es
contrastable con este diseño.

El problema está en el instrumento de medida. Un estrato de entidad exacta solo es válido si la
entidad objetivo figura en el documento indexado, y esa condición de validez es una de las
contribuciones metodológicas de la tesis. El [corpus definitivo](03_corpus_definitivo_177.md) y
el [registro completo](05_registro_completo.md) se usaron después para contrastar P2 en
condiciones en las que sí se cumple.

## La ontología (P3)

El efecto de la ontología cambia con el conjunto. Sobre el denso (C2 frente a C1) es concordante
en el sintético ($+0{,}065$), en el difícil A ($+0{,}122$) y en la réplica B ($+0{,}054$), y nulo en
el ampliado ($-0{,}004$). Sobre el híbrido (C4 frente a C3) es concordante en el sintético
($+0{,}056$) y en la unión de los difíciles ($+0{,}075$); en A ($+0{,}102$, $p$ de Holm de $0{,}072$) y
en B ($+0{,}058$) por separado el signo y la magnitud coinciden y solo falta poder. El patrón es
coherente con un puente de vocabulario: la ontología ayuda cuando la consulta se aparta del
vocabulario del documento, como en las paráfrasis, y no aporta en el ampliado, cuyas consultas
se sintetizaron desde los filtros del propio reporte.

### Por nivel de solape

nDCG@10 en la unión de los difíciles ($n=130$) por nivel de solape calculado.

| Configuración | Con puente ($n=52$) | Sin puente ($n=21$) | Con solape ($n=57$) | Global ($n=130$) |
|---|---|---|---|---|
| BM25 | 0,000 | 0,000 | 0,747 | 0,328 |
| C1 · Denso puro | 0,689 | 0,766 | 0,810 | 0,754 |
| C2 · Denso con ontología | 0,819 | 0,801 | 0,864 | 0,836 |
| C3 · Híbrido sin ontología | 0,636 | 0,744 | 0,836 | 0,741 |
| C4 · Híbrido con ontología | 0,870 | 0,658 | 0,826 | 0,816 |
| C5 · C4 con realce | 0,810 | 0,655 | 0,752 | 0,759 |

En el nivel con puente, donde la consulta comparte raíces con el bloque de ontología pero no con la
descripción, el denso con ontología alcanza $0{,}819$ frente a $0{,}689$ del denso puro, y el
híbrido con ontología $0{,}870$ frente a $0{,}636$ del híbrido sin ella. En el nivel sin puente, sin ese
puente, el denso puro llega a $0{,}766$ y la ontología aporta poco ($0{,}801$), porque la
recuperación depende casi por completo del modelo denso. BM25 vale cero en los niveles con puente y sin puente
por construcción.

### La cobertura parcial: un efecto no previsto

Como solo $9$ de los $17$ reportes tienen bloque de ontología, se separaron las consultas según
el reporte objetivo esté enriquecido o no. Es un análisis exploratorio, sin corrección de Holm,
que debe leerse como generador de hipótesis.

| Conjunto | Grupo | Comparación | Δ | Pares ≠ 0 | $p$ Wilcoxon | $p$ permutación |
|---|---|---|---|---|---|---|
| difícil A | objetivo enriquecido ($n=36$) | C2 − C1 | +0,180 | 16 | <0,001 | <0,001 |
| difícil A | objetivo enriquecido ($n=36$) | C4 − C3 | +0,219 | 26 | <0,001 | <0,001 |
| difícil A | objetivo sin enriquecer ($n=16$) | C2 − C1 | −0,006 | 5 | 0,684 | 0,875 |
| difícil A | objetivo sin enriquecer ($n=16$) | C4 − C3 | −0,161 | 8 | 0,012 | 0,008 |
| ampliado | objetivo enriquecido ($n=112$) | C2 − C1 | −0,005 | 11 | 0,655 | 0,555 |
| ampliado | objetivo enriquecido ($n=112$) | C4 − C3 | +0,019 | 13 | 0,126 | 0,135 |
| ampliado | objetivo sin enriquecer ($n=15$) | C2 − C1 | +0,000 | 0 | n/d | n/d |
| ampliado | objetivo sin enriquecer ($n=15$) | C4 − C3 | +0,000 | 0 | n/d | n/d |

Cuando el objetivo está enriquecido, la ontología aporta mucho en el conjunto difícil. Cuando no
lo está, el híbrido con ontología empeora ($-0{,}161$, $p<0{,}02$ con ambas pruebas), porque los
documentos enriquecidos, más largos y con más términos, compiten con ventaja frente a los que no
lo están. En el ampliado el efecto no aparece porque sus consultas son fáciles.

### La ontología ampliada a catorce reportes

Para poner a prueba esa hipótesis («la ontología tiene que cubrir todo el corpus») se
enriquecieron también los reportes que admiten un mapeo, sin redactar texto libre ni mirar las
consultas. Las entidades de cada reporte se derivaron de las columnas y filtros reales de sus
firmas, cruzados con las propiedades de datos de cada clase de la ontología, y la clase
Promoción se descartó salvo que la firma use el registro de promociones. La cobertura pasó de
$9$ a $14$ reportes; tres quedaron sin enriquecer porque sus columnas no se asocian a ninguna
clase. El enriquecimiento es deliberadamente pobre: entidades y sinónimos, sin las preguntas de
negocio que tienen los nueve originales.

| Conjunto | Denso: sin / parcial / ampliada | Híbrido: sin / parcial / ampliada | Híbrido, objetivos antes sin bloque (ampliada − parcial) |
|---|---|---|---|
| Sintético | 0,866 / 0,931 / 0,904 | 0,893 / 0,948 / 0,937 | n/d |
| Ampliado | 0,932 / 0,928 / 0,921 | 0,943 / 0,960 / 0,960 | +0,009 ($n=15$) |
| Difícil A | 0,712 / 0,835 / 0,819 | 0,686 / 0,788 / 0,801 | +0,071 ($n=16$) |
| Difícil B | 0,783 / 0,837 / 0,833 | 0,778 / 0,835 / 0,839 | +0,066 ($n=24$) |

Ampliar la cobertura no mejora el desempeño global: el híbrido pasa de $0{,}948$ a $0{,}937$ en el
sintético, se mantiene en $0{,}960$ en el ampliado y cambia $+0{,}013$ y $+0{,}004$ en los difíciles,
todo dentro del ruido. Sí recupera a los reportes antes perjudicados, en dirección: $+0{,}071$ en
A y $+0{,}066$ en B, con $p$ de Wilcoxon de $0{,}46$ y $0{,}06$. La dirección coincide en dos muestras
independientes, pero ninguna diferencia es significativa, así que la hipótesis queda con apoyo
sugerente y sin confirmar. Un enriquecimiento mecánico y pobre tampoco equivale al trabajo de
modelado de los nueve originales.

## El realce por entidad (P5)

El realce es el único componente de la escalera que nunca mejora el orden. C5 frente a C4 vale
$-0{,}024$ en el sintético, $-0{,}016$ en el ampliado (donde $5$ consultas empeoran y ninguna mejora),
$-0{,}049$ en el difícil A y $-0{,}063$ en el B, estos dos concordantes, y $-0{,}057$ en la unión.

La causa está en el detector de entidades, diagnosticado con su versión corregida. Visto como un
clasificador de pares consulta–documento cuya etiqueta ideal es que el documento sea el
objetivo, el detector tiene estas cifras en los tres conjuntos diagnosticados (el difícil B no se
incluyó):

| Medida | Rango en los tres conjuntos |
|---|---|
| Precisión | $0{,}17$, $0{,}13$ y $0{,}10$ |
| *Recall* | $0{,}70$, $0{,}74$ y $0{,}38$ |
| Documentos activados por consulta | entre $4{,}0$ y $5{,}7$ de $17$ |
| Precisión de una activación al azar | cercana a $0{,}06$ |

El detector es entre $1{,}7$ y $2{,}9$ veces más preciso que el azar, y aun así no sirve. Casi
todos los reportes cubren las mismas clases del dominio (deportista, grupo, institución), así
que el factor multiplicativo eleva a un grupo de documentos a la vez y el correcto no gana
posiciones frente a los demás. El realce se descarta en la Versión 1. Solo tendría sentido con un
detector que resuelva la mención concreta contra un diccionario de entidades, que es lo que se
evaluó después sobre el [registro completo](05_registro_completo.md).

Antes de la auditoría, en una evaluación con consultas desde firmas, el realce parecía ayudar.
Esas cifras se calcularon con un detector que coincidía por subcadena y sin las demás
correcciones, y quedaron invalidadas. Ninguna cifra válida de la tesis muestra un realce que
mejore.

## ¿Es RRF la mejor fusión?

La literatura sugiere que una combinación convexa de puntuaciones supera a RRF, y en los
resultados anteriores el híbrido no supera al denso. Se compararon cuatro alternativas sobre las
puntuaciones crudas de BM25 y del denso, todas sobre el texto enriquecido: la combinación convexa
con normalización min–max o $z$, un RRF ponderado a favor del denso y un RRF con compuerta que
descarta la señal léxica cuando cubre menos de cierta fracción de la consulta. Para evitar la
fuga que supondría elegir el parámetro en el mismo conjunto en que se evalúa, cada parámetro se
elige con los otros tres conjuntos (*leave-one-set-out*) y se aplica sin retocar. Una comprobación
de sanidad confirma que el RRF del código de fusión reproduce exactamente C1 a C4. Este análisis
corresponde a la hipótesis exploratoria H7.

nDCG@10 y, entre paréntesis, la diferencia con RRF ($k=60$).

| Variante (texto enriquecido) | Sintético | Ampliado | Difícil A | Difícil B |
|---|---|---|---|---|
| BM25 solo | 0,920 | 0,906 | 0,545 | 0,730 |
| Denso (C2) | 0,931 | 0,928 | 0,835 | 0,837 |
| RRF $k=60$ (C4) | 0,948 | 0,960 | 0,788 | 0,835 |
| Convexa min–max | 0,958 (+0,010) | 0,959 (−0,000) | 0,802 (+0,014) | 0,875 (+0,039) |
| Convexa $z$ | 0,949 (+0,001) | 0,959 (−0,001) | 0,804 (+0,017) | 0,870 (+0,034) |
| RRF ponderado | 0,952 (+0,004) | 0,959 (−0,001) | 0,784 (−0,004) | 0,854 (+0,019) |
| RRF con compuerta | 0,942 (−0,006) | 0,960 (+0,000) | 0,850 (+0,062) | 0,847 (+0,011) |

Con diecisiete reportes ninguna alternativa supera a RRF de forma concordante. La convexa es
mejor en dirección en los difíciles y en el sintético, pero no en el ampliado, y ninguna
diferencia sobrevive a Holm. La compuerta mejora el difícil A ($+0{,}062$, $p$ de Holm de $0{,}026$ con
Wilcoxon y $0{,}054$ con permutación) pero solo $+0{,}011$ en la réplica, así que la mejora no se
confirma. BM25 sobre el texto enriquecido da $0{,}545$ en el difícil A, frente a $0{,}186$ sobre la
descripción, porque el bloque de ontología le da términos con los que coincidir.

Con diecisiete documentos el híbrido tampoco perjudica al denso de manera consistente: C4 queda
por debajo de C2 en el difícil A ($-0{,}047$, sin significancia), igual en la réplica ($-0{,}002$) y
por encima en el ampliado ($+0{,}032$; $p$ de $0{,}019$ con Wilcoxon y $0{,}012$ con permutación, sin
corregir). La convexa con peso $0{,}8$ para el denso fue la elegida en tres de los cuatro cortes de
este corpus, el mismo valor que luego se eligió sin fuga en el [corpus v3](04_corpus_v3_811.md),
donde la conclusión sobre la fusión cambia.

## Sensibilidad a los hiperparámetros

Los hiperparámetros se tomaron de la literatura sin ajustarlos. El barrido comprueba si las
conclusiones dependen de esa elección. Filas de $k$: C3 / C4. Filas de $\lambda$: C5 y su
diferencia con C4. Filas de $k_1$ y $b$: BM25 / C4.

| Parámetro | Sintético | Ampliado |
|---|---|---|
| $k=1$ | 0,856 / 0,943 | 0,947 / 0,958 |
| $k=10$ | 0,893 / 0,948 | 0,943 / 0,961 |
| $k=30$ | 0,893 / 0,948 | 0,943 / 0,960 |
| $k=60$ | 0,893 / 0,948 | 0,943 / 0,960 |
| $k=100$ | 0,893 / 0,948 | 0,943 / 0,960 |
| $k=200$ | 0,893 / 0,948 | 0,943 / 0,960 |
| $\lambda=0{,}0$ | 0,948 (+0,000) | 0,960 (+0,000) |
| $\lambda=0{,}05$ | 0,929 (−0,019) | 0,949 (−0,011) |
| $\lambda=0{,}1$ | 0,926 (−0,022) | 0,945 (−0,015) |
| $\lambda=0{,}2$ | 0,924 (−0,024) | 0,944 (−0,016) |
| $\lambda=0{,}3$ | 0,924 (−0,024) | 0,944 (−0,016) |
| $\lambda=0{,}5$ | 0,924 (−0,024) | 0,944 (−0,016) |
| $k_1=0{,}9$, $b=0{,}5$ | 0,815 / 0,950 | 0,878 / 0,961 |
| $k_1=0{,}9$, $b=0{,}9$ | 0,819 / 0,948 | 0,863 / 0,963 |
| $k_1=1{,}5$, $b=0{,}5$ | 0,819 / 0,951 | 0,902 / 0,961 |
| $k_1=1{,}5$, $b=0{,}9$ | 0,828 / 0,948 | 0,849 / 0,961 |
| $k_1=2{,}0$, $b=0{,}5$ | 0,819 / 0,952 | 0,905 / 0,967 |
| $k_1=2{,}0$, $b=0{,}9$ | 0,828 / 0,949 | 0,855 / 0,961 |

Para $k\ge 30$ los resultados de C3 y C4 son idénticos a los de $k=60$ en los dos conjuntos, y con
$k=10$ cambia a lo sumo una consulta; solo $k=1$ altera el orden de unas pocas ($5$ de C3 y $2$ de C4
en el sintético, $9$ y $5$ en el ampliado). Esa insensibilidad se debe en parte al tamaño del
corpus: con diecisiete documentos los rangos van de $1$ a $17$ y la constante apenas altera el
orden relativo de las sumas, así que no debe extrapolarse a corpus grandes. Cualquier
$\lambda>0$ iguala o empeora a $\lambda=0$, y desde $\lambda=0{,}2$ el resultado deja de cambiar,
probablemente porque el factor ya basta para que los documentos activados superen a los demás.
Variar $k_1$ y $b$ mueve a BM25 entre $0{,}815$ y $0{,}828$ en el sintético y entre $0{,}849$ y $0{,}905$
en el ampliado, mientras C4 se mantiene entre $0{,}948$ y $0{,}952$ y entre $0{,}960$ y $0{,}967$: el
híbrido supera a BM25 en toda la rejilla.

## Dimensión del vector (P6)

El codificador fue entrenado con representación Matryoshka, de modo que sus primeras $m$
dimensiones ya forman un vector útil y se puede truncar sin reentrenar. La equivalencia se juzga
con el criterio fijado en el plan: que el límite inferior del intervalo de confianza de la
pérdida no baje de $-0{,}01$. Es una hipótesis de equivalencia (H6) y por eso se evalúa con el
intervalo, no con un $p$-valor.

nDCG@10 de C4 y, entre paréntesis, la diferencia con $m=1.024$ y si permite declarar equivalencia.

| $m$ | Sintético | Ampliado | Ahorro de índice |
|---|---|---|---|
| 1.024 | 0,948 (+0,000; no inf.) | 0,960 (+0,000; no inf.) | 0 % |
| 768 | 0,948 (+0,000; no inf.) | 0,960 (+0,000; no inf.) | 25 % |
| 512 | 0,931 (−0,018; no concl.) | 0,963 (+0,003; no inf.) | 50 % |
| 256 | 0,940 (−0,008; no concl.) | 0,963 (+0,003; no inf.) | 75 % |
| 128 | 0,944 (−0,004; no concl.) | 0,944 (−0,016; no concl.) | 87,5 % |
| 64 | 0,949 (+0,001; no concl.) | 0,923 (−0,037; no concl.) | 93,8 % |

En el ampliado, truncar a $256$ dimensiones no es inferior a la dimensión nativa ($+0{,}003$,
intervalo de $0{,}000$ a $+0{,}009$), igual que $512$ y $768$; a $128$ la pérdida es pequeña pero
detectable y a $64$ es clara. Ese conjunto está cerca del techo, y en un conjunto saturado la
no inferioridad es casi automática. En los difíciles, con $256$ dimensiones la pérdida puntual es de
$-0{,}009$ y el intervalo llega a $-0{,}023$, así que no se puede declarar no inferioridad; con $512$ sí
($+0{,}007$, intervalo de $0{,}000$ a $+0{,}017$), mientras que $768$ no resulta concluyente ($-0{,}008$),
señal de que con $130$ consultas el margen de $0{,}01$ está cerca del límite de resolución. En el
sintético, con $40$ consultas, el intervalo es demasiado ancho para concluir por debajo de $768$. La
dimensión recomendada es $512$, por su ahorro de memoria y porque es no inferior en el ampliado y en
los difíciles; $256$ es aceptable si la memoria se vuelve una restricción. Truncar reduce la memoria
del índice y no la latencia, que la domina la codificación de la consulta.

## Fragmentación de los documentos (P4)

nDCG@10 de C4 al dividir cada documento en fragmentos y agregar por máximo, con solapamiento de
$0\%$ y de $25\%$. Entre paréntesis, la diferencia con el documento completo.

| Tamaño | Sintético, 0 % | Sintético, 25 % | Ampliado, 0 % | Ampliado, 25 % | Fragmentos por documento |
|---|---|---|---|---|---|
| Documento completo | 0,948 (+0,000) | 0,948 (+0,000) | 0,960 (+0,000) | 0,960 (+0,000) | 1,00 |
| 128 palabras | 0,939 (−0,009) | 0,952 (+0,004) | 0,951 (−0,009) | 0,953 (−0,007) | 1,24 |
| 64 palabras | 0,935 (−0,014) | 0,943 (−0,005) | 0,908 (−0,051) | 0,934 (−0,026) | 2,12 |
| 40 palabras | 0,913 (−0,036) | 0,909 (−0,039) | 0,933 (−0,027) | 0,928 (−0,032) | 2,94 |
| 24 palabras | 0,896 (−0,052) | 0,925 (−0,023) | 0,897 (−0,063) | 0,912 (−0,048) | 4,65 |

Fragmentar nunca supera al documento completo de forma apreciable. La única ganancia, $+0{,}004$
en el sintético con fragmentos de $128$ palabras y $25\%$ de solapamiento, está dentro del ruido,
y los fragmentos pequeños empeoran hasta $-0{,}063$. Con documentos de $64$ a $184$ palabras, por
debajo de la ventana efectiva de cualquier codificador actual, era el resultado esperado. La
hipótesis H4 no se sostiene, y la unidad de indexación es el reporte completo.

## Escalamiento de la búsqueda exacta

Para saber qué pasaría al crecer el corpus se midió la búsqueda exacta por fuerza bruta con
vectores aleatorios de la forma real de los *embeddings*. Cada celda da la memoria del índice
(MiB) y la latencia mediana de la búsqueda (ms), sin contar la codificación de la consulta.

| $N$ documentos | $m=64$ | $m=256$ | $m=1.024$ |
|---|---|---|---|
| 1.000 | 0,2 / 0,02 | 1,0 / 0,02 | 3,9 / 0,03 |
| 10.000 | 2,4 / 0,11 | 9,8 / 0,14 | 39,1 / 0,98 |
| 100.000 | 24,4 / 1,46 | 97,7 / 3,09 | 390,6 / 8,10 |
| 200.000 | 48,8 / 2,98 | 195,3 / 6,63 | 781,2 / 17,73 |

Hasta cientos de miles de documentos la búsqueda exacta sigue siendo despreciable frente a los
$351$ ms de codificar la consulta, y la truncación Matryoshka aporta sobre todo ahorro de
memoria. La medida se tomó en un equipo personal con otras tareas activas, depende del equipo y
no dice nada sobre calidad, pero basta para justificar que no se introduzca un índice aproximado
en esta etapa.

## Costo computacional

Todas las cifras de costo provienen de una única campaña de medición en un equipo personal
(procesador Apple M4 con aceleración por su GPU integrada, Python 3.14 y el modelo en precisión
de $32$ bits), con un solo proceso de medición, prioridad baja y una pasada de calentamiento.
Sirven para comparar componentes y configuraciones entre sí, no para anticipar lo que mediría un
servidor de producción. Las tareas fuera de línea se hacen una vez, al construir el índice; las
en línea se repiten en cada consulta y su suma es lo que espera el usuario.

| Componente | Cuándo | Costo | Qué significa |
|---|---|---|---|
| Entrenamiento o ajuste | nunca | ninguno | no hay que recolectar datos etiquetados ni usar una GPU dedicada |
| Carga del codificador | una vez, al iniciar el servicio | 7,3 s | el usuario no lo espera |
| Memoria del proceso | mientras el servicio está activo | ≈ 2,2 GiB | el requisito de hardware principal |
| Índice BM25 de 17 documentos | fuera de línea | 11 ms | rehacer el índice léxico es instantáneo |
| Codificación de un documento | fuera de línea | ≈ 141 ms | menos de tres segundos para el corpus de la Versión 1 |
| Índice denso a 1.024 / 512 / 256 dimensiones | mientras el servicio está activo | 68 / 34 / 17 KiB | despreciable a esta escala |
| Codificación de la consulta, GPU integrada (p50 / p95) | en cada consulta | 351 / 408 ms | casi todo el tiempo que espera el usuario |
| Codificación de la consulta, solo CPU (p50 / p95) | en cada consulta | 628 / 801 ms | casi el doble, aún por debajo de un segundo |
| Búsqueda BM25 | en cada consulta | 0,09 ms | unas cuatro mil veces más rápida que codificar |
| Búsqueda densa sobre 17 vectores | en cada consulta | 0,002 ms | inmediata |
| Fusión RRF | en cada consulta | 0,005 ms | sin costo perceptible |

Recorrido de una consulta en C4 (medianas de la misma campaña):

| Paso | Qué hace el sistema | Tiempo | Proporción |
|---|---|---|---|
| 1 | convierte la consulta en un vector con el codificador | 351 ms | > 99,9 % |
| 2 | busca la consulta en el índice léxico | 0,09 ms | < 0,1 % |
| 3 | compara el vector con los de los documentos | 0,002 ms | < 0,01 % |
| 4 | fusiona las dos listas por rango recíproco | 0,005 ms | < 0,01 % |
| | Total medido de punta a punta (p50 / p95) | 345 / 380 ms | |

Costo frente a efectividad por configuración. La latencia es el tiempo total por consulta medido
de punta a punta. Las columnas de nDCG@10 mezclan corpus a propósito, para mostrar que el costo
es el mismo en todos: el ampliado y la unión de los difíciles son de este corpus de diecisiete
reportes, y la última columna es del [corpus definitivo](03_corpus_definitivo_177.md).

| Configuración | Latencia p50 / p95 (ms) | Memoria | Ampliado | Difíciles A+B | Definitivo (177) |
|---|---|---|---|---|---|
| BM25 | 0,09 / 0,12 | kilobytes | 0,887 | 0,328 | 0,774 |
| C1 · Denso puro | 344 / 360 | ≈ 2,2 GiB | 0,932 | 0,754 | 0,865 |
| C2 · Denso con ontología | 343 / 351 | ≈ 2,2 GiB | 0,928 | 0,836 | 0,910 |
| C3 · Híbrido | 345 / 370 | ≈ 2,2 GiB | 0,943 | 0,741 | 0,868 |
| C4 · Híbrido con ontología | 345 / 380 | ≈ 2,2 GiB | 0,960 | 0,816 | 0,960 |
| C5 · C4 con realce | 349 / 378 | ≈ 2,2 GiB | 0,944 | 0,759 | 0,950 |

Entre las cinco configuraciones neuronales las latencias van de $343$ a $349$ ms en la mediana,
menos de un $2\%$ de diferencia, porque todas pagan la misma codificación de la consulta. En
tiempo, añadir la señal léxica, la ontología o el realce no cuesta prácticamente nada. BM25
responde en una décima de milisegundo y no necesita el modelo en memoria, pero pierde $0{,}073$ de
nDCG@10 en el ampliado, $0{,}186$ en el corpus definitivo y $0{,}508$ en las paráfrasis frente a la
mejor configuración. Si el equipo no puede reservar unos $2$ GiB de memoria, BM25 es la única
opción; si puede, la elección entre las neuronales se hace solo por efectividad.

Con unos $0{,}35$ segundos por consulta, un solo proceso atiende del orden de tres consultas por
segundo, unas doscientas cincuenta mil al día. La demanda observada es de unas $145$ consultas
reales por día, menos de un minuto de cómputo diario, y en usabilidad suele aceptarse que una
respuesta de menos de un segundo no interrumpe el hilo de pensamiento del usuario.

## Análisis de errores

Exactitud en la primera posición (fracción de consultas cuyo reporte objetivo queda primero).

| Conjunto | BM25 | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|
| Sintético ($n=40$) | 0,650 | 0,725 | 0,825 | 0,750 | 0,875 |
| Ampliado ($n=127$) | 0,748 | 0,882 | 0,866 | 0,874 | 0,921 |
| Difícil A ($n=52$) | 0,135 | 0,404 | 0,654 | 0,442 | 0,615 |
| Difícil B ($n=78$) | 0,372 | 0,577 | 0,641 | 0,615 | 0,641 |

En los conjuntos difíciles solo el $65\%$ (A) y el $64\%$ (B) de las consultas deja el reporte
objetivo en primer lugar con el mejor sistema, frente al $92\%$ en el ampliado. Las confusiones
más frecuentes son entre reportes que describen entidades vecinas: las métricas por federación
devueltas como reporte individual de deportistas, o el personal de apoyo devuelto como grupos.
En muchos de esos casos la consulta es ambigua entre dos reportes, un límite del protocolo de
objetivo único que los juicios de expertos con grados intermedios corregirían.

Éxito en la primera posición y entre las tres primeras, en los conjuntos de este corpus:

| Configuración | Ampliado @1 / @3 | Difícil A @1 / @3 | Difícil B @1 / @3 |
|---|---|---|---|
| BM25 | 0,75 / 0,94 | 0,12 / 0,17 | 0,32 / 0,45 |
| C1 · Denso puro | 0,88 / 0,94 | 0,40 / 0,77 | 0,58 / 0,83 |
| C2 · Denso con ontología | 0,87 / 0,96 | 0,65 / 0,88 | 0,64 / 0,94 |
| C3 · Híbrido | 0,87 / 0,99 | 0,44 / 0,60 | 0,62 / 0,77 |
| C4 · Híbrido con ontología | 0,92 / 0,97 | 0,62 / 0,79 | 0,64 / 0,91 |
| C5 · C4 con realce | 0,90 / 0,94 | 0,54 / 0,75 | 0,56 / 0,79 |

## Robustez de las conclusiones en este corpus

Las consultas que comparten reporte objetivo no son independientes, porque comparten documento,
vocabulario y redactor. Para que esa dependencia no infle la significancia, las comparaciones se
repitieron con un *bootstrap* que remuestrea reportes objetivo en lugar de consultas, y dejando
fuera un reporte a la vez. El asterisco marca los intervalos que excluyen el cero.

| Comparación | Ampliado | Difíciles A+B |
|---|---|---|
| C3 − BM25 | +0,056 [+0,022; +0,102] \* | +0,413 [+0,307; +0,517] \* |
| C3 − C1 | +0,011 [−0,016; +0,035] | −0,013 [−0,052; +0,028] |
| C2 − C1 | −0,004 [−0,025; +0,014] | +0,081 [+0,037; +0,132] \* |
| C4 − C3 | +0,016 [−0,017; +0,052] | +0,075 [−0,018; +0,175] |
| C5 − C4 | −0,016 [−0,045; +0,000] | −0,057 [−0,115; −0,008] \* |
| C4 − C2 | +0,032 [−0,011; +0,053] | −0,020 [−0,066; +0,029] |

En el ampliado solo la ventaja del híbrido sobre BM25 sobrevive a este criterio, lo que confirma
que allí las demás diferencias son pequeñas frente a la variación entre reportes. En los
difíciles sobreviven además la ventaja de la ontología sobre el denso y el daño del realce; la
ventaja de la ontología sobre el híbrido, concordante con la prueba por consulta, deja de
excluir el cero al remuestrear reportes.

Este corpus pasó además por tres controles, detallados en [validez y robustez](06_validez_y_robustez.md).
El metaanálisis de efectos fijos de A y B da efectos combinados de $+0{,}070$ para la ontología en el
denso y en el híbrido y de $-0{,}055$ para el realce, sin heterogeneidad entre los dos conjuntos.
El análisis de dosis-respuesta muestra que la ganancia de la ontología en el híbrido crece con el
número de raíces que la consulta comparte con su bloque de ontología, de $-0{,}074$ sin ninguna a
$+0{,}251$ con dos o más. Y si cada consulta del ampliado se pondera según la cuota de su reporte
objetivo en las $6.620$ solicitudes reales, el orden no cambia: C4 obtiene $0{,}964$, el híbrido sin
ontología $0{,}959$ y el denso puro $0{,}944$. En el difícil B, por registro de redacción, C4 es la
mejor en las consultas formuladas como pregunta ($0{,}884$) y C2 en las administrativas ($0{,}817$) y
en las telegráficas ($0{,}866$), sin que ningún registro invierta las conclusiones generales.

## Lo que dejó esta etapa

Con diecisiete reportes, el híbrido supera a BM25 pero no al denso, la ontología ayuda en las
paráfrasis y no en las consultas que ya usan el vocabulario del reporte, el realce no sirve, la
fragmentación no aporta y $512$ dimensiones bastan. La recomendación para una Versión 1 limitada
a reportes es C4 sin realce, con el vector truncado a $512$ dimensiones y un índice denso por
coseno exacto, con C2 como alternativa natural si se esperan consultas muy coloquiales, porque no mostró
diferencias significativas frente a C4.

Quedaron tres límites. La hipótesis de entidad exacta no era contrastable, porque las entidades
no figuraban en ningún documento. Recall@100 era trivial con diecisiete documentos. Y varias
diferencias eran menores que lo que el número de consultas permitía detectar. El
[corpus definitivo](03_corpus_definitivo_177.md) se construyó para atacar los tres.

## Cómo reproducirlo

`make all` encadena
[`preprocess_corpus.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/preprocess_corpus.py),
[`generar_consultas.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/generar_consultas.py),
[`run_ablation.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/run_ablation.py)
y
[`generar_reportes.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/generar_reportes.py),
y produce la escalera con el conjunto sintético. Los demás conjuntos tienen objetivos propios:
`make eval_real` y `make control` para el ampliado y el control sin nombre
([`construir_eval_real_ampliado.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/construir_eval_real_ampliado.py)
y [`eval_flexible.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/eval_flexible.py)),
`make dificil` y `make dificil_b` para los difíciles
([`construir_eval_dificil.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/construir_eval_dificil.py),
[`construir_eval_dificil_b.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/construir_eval_dificil_b.py)),
`make fusion` para las fusiones alternativas
([`fusion.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/fusion.py)),
`make ontologia_completa` para la ontología en catorce reportes
([`enriquecimiento_completo.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/enriquecimiento_completo.py)),
`make cobertura` y `make diagnostico` para la cobertura de la ontología y el detector
([`analisis_cobertura_ontologia.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/analisis_cobertura_ontologia.py),
[`diagnostico_detector.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/diagnostico_detector.py)),
`make barridos` y `make barridos_dificiles` para la sensibilidad, Matryoshka y la fragmentación
([`barridos.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/barridos.py)),
`make errores` para la exactitud en la primera posición
([`analisis_errores.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/analisis_errores.py)),
`make costo` y `make escalamiento` para el costo y la búsqueda con vectores aleatorios
([`costo_computacional.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/costo_computacional.py),
[`escalamiento.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/escalamiento.py)),
y `make robustez` y `make complementario` para la robustez, que no necesitan el modelo
([`analisis_robustez.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/analisis_robustez.py),
[`analisis_complementario.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/analisis_complementario.py)).
El corpus de diecisiete reportes, las consultas y sus juicios están publicados en `corpus/` y
`datos/`; las firmas del historial de las que se derivó el ampliado no, pero el conjunto ya
construido sí, de modo que la evaluación se puede repetir sin ellas. Los cuadernos
[de la escalera](../notebooks/Benchmark_Escalera_Ablacion.ipynb) y
[de estratos y estadística](../notebooks/01_Analisis_por_Estratos_y_Estadistica.ipynb) del
archivo muestran la misma tubería con cifras anteriores a la auditoría.
