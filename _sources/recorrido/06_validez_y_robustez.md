# Validez y robustez

Las páginas anteriores recorren los corpus uno por uno. Aquí se reúne lo que atraviesa a todos: los
errores que se encontraron y corrigieron, las amenazas a la validez con el riesgo que queda en cada
una, las pruebas de robustez de las conclusiones, el estado de cada hipótesis y los límites que
siguen abiertos. En la discusión de la monografía se lee que los controles de validez son la parte
del trabajo que más se puede llevar a otros proyectos: sin ellos la evaluación habría dado una
imagen más favorable del sistema y menos cierta.

## Errores encontrados y controles

La mayoría de estos problemas los encontró la auditoría interna del 30 de septiembre de 2026; otros
aparecieron al revisar resultados posteriores. Todas las cifras afectadas se recalcularon, y las
anteriores a la auditoría se guardan aparte, solo para trazabilidad.

| # | Problema | Cómo se detectó | Efecto si no se hubiera corregido | Corrección |
|---|---|---|---|---|
| 1 | El estrato de entidad exacta no medía entidades | control con el nombre propio borrado | se habría «confirmado» P2 con un estrato que mide el tema | H2 se declara no contrastable con 17 reportes y se contrasta después en competencias y en el registro |
| 2 | Un nombre sintético de las consultas figuraba en los metadatos de un documento | auditoría | inflaba el estrato de entidad exacta | se eliminó; el control sin nombre comprueba que ya no influye |
| 3 | Pseudo-replicación en el conjunto ampliado | auditoría | tamaño muestral inflado y significancias falsas | unidad de muestreo igual al patrón distinto de firma y deduplicación global |
| 4 | Empate espurio en BM25 | auditoría del código | el primer documento del corpus ganaba todos los empates a cero y entraba a la fusión | BM25 devuelve solo puntuaciones positivas; desempate por identificador |
| 5 | RRF daba aporte a documentos ausentes de una lista | auditoría | aporte espurio en la fusión | un documento ausente no recibe aporte de esa lista |
| 6 | Codificador sin tarea de recuperación declarada | auditoría | el adaptador de recuperación no se activaba, sin ningún error visible | tareas de consulta y de pasaje fijadas en la configuración |
| 7 | Dimensión Matryoshka mayor que la nativa ($1.536$ en un modelo de $1.024$) | auditoría | fila inválida en el barrido de P6 | el codificador rechaza dimensiones mayores que la nativa |
| 8 | Detector de entidades por subcadena | auditoría | «etapa» se activaba dentro de «etapas» y «Caribe» pasaba por nombre propio | coincidencia por palabra completa y filtro del vocabulario del dominio |
| 9 | BM25 sin reducción a raíces | auditoría | «deportista» y «deportistas» contaban como términos distintos | Snowball en español |
| 10 | Tamaño del efecto no pareado y sin corrección múltiple | auditoría | incoherencia con la prueba de Wilcoxon | correlación biserial por rangos y Holm por familia |
| 11 | Wilcoxon como única prueba | lectura de Smucker, Allan y Carterette | riesgo de que Wilcoxon discrepe de otras pruebas | prueba de permutación pareada y regla de concordancia |
| 12 | Orden de iteración no determinista en la fusión | variación de las métricas entre corridas | resultados distintos según el proceso | orden estable y desempate por identificador |
| 13 | Promoción con el $47{,}5\%$ de la demanda | auditoría del análisis exploratorio | otro reporte líder y otra prioridad de indexación | regla de promoción corregida: $4{,}2\%$, séptimo lugar |
| 14 | Paginación «cerca del $50\%$» y «cero consultas a competencias» | auditoría del análisis exploratorio | el problema mal dimensionado | $38{,}5\%$; la frase se acota a eventos, resultados y sedes |
| 15 | Corpus cartesiano de $816$ pruebas casi duplicadas | revisión del corpus | documentos casi idénticos que no representan pruebas reales | corpus definitivo con las $160$ Pruebas Regionales que existen |
| 16 | Techo del protocolo de objetivo conocido | tabla de pares no nulos | poco poder: C4 frente a C3 se apoyaba en $13$ de $127$ consultas | conjuntos difíciles con nivel calculado; pares no nulos en todas las tablas |
| 17 | Dependencia entre consultas del mismo objetivo | diseño | significancia inflada | *bootstrap* agrupado por objetivo o por componente y exclusión de un reporte a la vez |
| 18 | Circularidad entre ontología y consultas | diseño | el efecto de la ontología podría ser un artefacto del redactor | niveles calculados, dosis-respuesta, réplica B y léxico dividido; no se elimina del todo |
| 19 | Cobertura densa parcial en la primera corrida sobre el registro ($15.974$ de $757.554$) | revisión de la primera corrida | C1, C2 y la convexa sobrestimados | segunda corrida con todos los documentos en el índice denso |
| 20 | Ontología comparada solo con la descripción original | revisión de la primera corrida | no se descartaba que cualquier texto más largo diera la misma mejora | tres controles de la misma longitud en subpalabras |
| 21 | Artefacto de la validación cruzada en el clasificador de tipo | matriz de confusión: $0$ de $53$ en competencias | se habría leído como que el clasificador no reconoce competencias | se explica la causa, se reporta la exactitud sin esa clase ($97{,}5\%$) y se añade una ruta sin entrenamiento |
| 22 | Hallazgos formulados al mirar el difícil A | diseño | sobreajuste del relato a un conjunto | réplica B sin ajustarla a ningún sistema y metaanálisis de A y B |

Tres de esos controles merecen una explicación aparte. El control sin nombre propio (fila 1) es la
prueba más reveladora del trabajo: al borrar el nombre de las $55$ consultas de entidad exacta, el
desempeño subió en cinco de seis configuraciones, lo que mostró que el estrato medía el tema del
reporte (ver [la Versión 1](02_version1_17_reportes.md)). El empate de BM25 (fila 4) parece un
detalle, pero con diecisiete documentos muchas consultas dejan a varios documentos con puntuación
cero, y si BM25 los devuelve en orden de indexación el primero del corpus queda siempre arriba y la
fusión le da un aporte que no merece. Y la tarea del codificador (fila 6) es un error silencioso:
`jina-embeddings-v3` tiene adaptadores distintos para consulta y para pasaje, y sin declarar la
tarea se usa una codificación simétrica que no da error, solo resultados peores.

## Amenazas a la validez y riesgo que queda

| Clase | Amenaza | Mitigación | Riesgo que queda |
|---|---|---|---|
| Constructo | el estrato de entidad exacta medía el tema | control sin nombre; contraste posterior en competencias y con personas en el registro | ninguno para la conclusión metodológica; P2 se contesta con otro diseño |
| Interna | las consultas derivadas de los documentos o de la ontología comparten vocabulario con ellos | se interpretan comparaciones y no niveles absolutos; conjuntos difíciles; léxico dividido | el nivel absoluto de las métricas sobrestima el de producción |
| Interna | el juicio *silver* (el reporte ejecutado) puede no ser la mejor respuesta | $50$ consultas marcadas como candidatas a anotación experta | la anotación no se hizo |
| Interna | el difícil B se redactó tras ver A; la ontología ampliada es pobre | se reportan como réplica y como evidencia sugerente | no son pruebas ciegas |
| Estadística | techo del protocolo, pocos pares no nulos | pares no nulos en todas las tablas; conjuntos difíciles; efecto mínimo detectable | los estratos pequeños (ambigua, $12$) no admiten conclusiones |
| Estadística | muchas comparaciones | Holm dentro de cada familia (cinco en la escalera, doce en la validación con controles) | no hay corrección global entre conjuntos ni entre estratos; los contrastes por estrato son exploratorios |
| Estadística | dependencia entre consultas | *bootstrap* agrupado y exclusión de un reporte a la vez | controlado en las conclusiones principales |
| Externa | una sola plataforma, una ventana de seis semanas y media, un solo codificador | corpus de $177$, $811$ y $757.554$ documentos | no se extrapola a otras plataformas ni a otros idiomas |
| Externa | consultas y ontología del mismo autor, sin expertos ni usuarios | dosis-respuesta, léxico dividido, réplica | es el límite principal; solo lo resuelven consultas de personas ajenas al diseño |

Con un solo documento relevante por consulta, el protocolo de objetivo conocido impone un techo:
buena parte de las consultas queda en la primera posición para todas las configuraciones y las
diferencias se concentran en pocas. Todas las pruebas son bilaterales. La de Wilcoxon descarta los
empates, y la de permutación es exacta con veinte o menos diferencias no nulas y aproximada con
$20.000$ sorteos en los demás casos.

Que no haya consultas reales se debe al dominio y no a una decisión del diseño. La plataforma no
ofrece un buscador sobre su conocimiento funcional y los filtros de sus listas no guardan lo que se
escribe, de modo que no existe un registro de consultas en texto libre que pudiera haberse usado.
Más consultas del mismo origen no resolverían el problema; hacen falta consultas redactadas por
personas ajenas al diseño.

## Robustez frente a la dependencia por reporte

Las consultas que comparten un mismo reporte objetivo comparten documento, vocabulario y redactor.
Para que esa dependencia no infle la significancia, las comparaciones se repitieron con un
*bootstrap* que remuestrea reportes (o pruebas) objetivo en lugar de consultas. Diferencia media de
nDCG@10 e intervalo del $95\%$; el asterisco marca los intervalos que excluyen el cero.

| Comparación | Ampliado (17) | Difíciles (17) | Definitivo (177) | Difíciles (177) |
|---|---|---|---|---|
| C3 − BM25 | +0,056 [+0,024; +0,101] \* | +0,413 [+0,312; +0,517] \* | +0,093 [+0,049; +0,136] \* | +0,147 [+0,059; +0,234] \* |
| C3 − C1 | +0,011 [−0,016; +0,034] | −0,013 [−0,053; +0,028] | +0,002 [−0,063; +0,048] | −0,104 [−0,160; −0,047] \* |
| C2 − C1 | −0,004 [−0,025; +0,014] | +0,081 [+0,038; +0,128] \* | +0,045 [+0,008; +0,102] \* | +0,150 [+0,076; +0,239] \* |
| C4 − C3 | +0,016 [−0,016; +0,053] | +0,075 [−0,020; +0,174] | +0,093 [+0,016; +0,185] \* | +0,192 [+0,075; +0,309] \* |
| C5 − C4 | −0,016 [−0,042; +0,000] | −0,057 [−0,113; −0,007] \* | −0,010 [−0,024; +0,000] | −0,027 [−0,062; +0,000] |
| C4 − C2 | +0,032 [−0,009; +0,053] | −0,020 [−0,066; +0,025] | +0,050 [+0,006; +0,079] \* | −0,062 [−0,143; +0,020] |

Dejar fuera un reporte a la vez no cambia el signo de ninguna diferencia cuyo intervalo excluye el
cero. En el corpus definitivo, las ventajas de la ontología sobre el denso y sobre el híbrido y la
de C4 sobre C2 mantienen intervalos que excluyen el cero. Con diecisiete documentos, en el conjunto
ampliado, solo sobrevive la ventaja del híbrido sobre BM25, lo que confirma que allí las demás
diferencias son pequeñas frente a la variación entre reportes. En los corpus v3 y en el registro
completo los intervalos de todas las tablas ya se calcularon por grupos de consultas con los mismos
relevantes (ver [el corpus v3](04_corpus_v3_811.md) y [el registro completo](05_registro_completo.md)).

## Dosis-respuesta de la ontología

El autor escribió la ontología y las consultas difíciles, y el nivel «con puente» se define por
compartir términos con la ontología. Si el efecto fuera un artefacto de esa definición, no debería
crecer con la cantidad de términos compartidos. La tabla agrupa las $130$ paráfrasis por cuántas
raíces comparte la consulta con el bloque de ontología del reporte objetivo ($0$: $n=57$; $1$: $n=34$;
$2$ o más: $n=39$) y da la correlación de Spearman entre ese número y la diferencia.

| Corpus | Comparación | 0 raíces | 1 raíz | 2 o más | Spearman ($p$) |
|---|---|---|---|---|---|
| 17 documentos | C2 − C1 | +0,037 | +0,120 | +0,113 | +0,22 (0,011) |
| 17 documentos | C4 − C3 | −0,074 | +0,125 | +0,251 | +0,46 (<0,001) |
| 177 documentos | C2 − C1 | +0,063 | +0,224 | +0,211 | +0,18 (0,040) |
| 177 documentos | C4 − C3 | −0,065 | +0,288 | +0,484 | +0,54 (<0,001) |

Cuando la consulta no comparte ninguna raíz con el bloque de ontología, la ontología no ayuda al
híbrido. Con una raíz compartida la ganancia es de $+0{,}125$ y $+0{,}288$, y con dos o más, de
$+0{,}251$ y $+0{,}484$. Ese gradiente es el que produciría un puente de vocabulario. La circularidad
de origen no queda eliminada, y solo se resolvería con consultas escritas por otras personas.

## Réplica y metaanálisis

En lugar de unir los conjuntos difíciles A y B, se combinaron por metaanálisis de efectos fijos,
que pondera cada conjunto por su precisión y mide si discrepan. $Q$ mide la heterogeneidad entre los
dos: con un grado de libertad, valores menores que $3{,}84$ no indican heterogeneidad significativa.
Corpus de diecisiete documentos; el asterisco marca los efectos combinados cuyo intervalo excluye el
cero.

| Comparación | Difícil A ($n=52$) | Difícil B ($n=78$) | Combinado [IC 95 %] | $Q$ |
|---|---|---|---|---|
| C1 − BM25 | +0,526 | +0,361 | +0,442 [+0,370; +0,514] \* | 5,07 |
| C3 − C1 | −0,026 | −0,005 | −0,015 [−0,043; +0,013] | 0,58 |
| C2 − C1 | +0,122 | +0,054 | +0,070 [+0,041; +0,099] \* | 3,72 |
| C4 − C3 | +0,102 | +0,058 | +0,070 [+0,021; +0,120] \* | 0,63 |
| C5 − C4 | −0,049 | −0,063 | −0,055 [−0,086; −0,025] \* | 0,21 |
| C4 − C2 | −0,047 | −0,001 | −0,017 [−0,054; +0,020] | 1,36 |

Los efectos de la ontología sobre el denso y sobre el híbrido y el daño del realce tienen intervalos
que excluyen el cero y no muestran heterogeneidad entre A y B. El híbrido frente al denso y C4 frente
a C2 no difieren. La heterogeneidad aparece solo en la magnitud de la ventaja del denso sobre BM25,
mayor en A que en B, lo que es coherente con que B tenga más consultas con alguna raíz en común con
el documento.

## Efecto mínimo detectable

Una diferencia no significativa puede ser un efecto nulo o un efecto menor que lo que el número de
consultas permitía resolver. El efecto mínimo detectable (EMD) con potencia de $0{,}8$ y $\alpha=0{,}05$
bilateral se aproxima como

$$
\mathrm{EMD} \approx 2{,}8\,\frac{s_d}{\sqrt{n}},
$$

donde $s_d$ es la desviación estándar de las diferencias por consulta y $n$ el número de consultas.

| Comparación | Ampliado obs. / EMD | Difícil A obs. / EMD | Difícil B obs. / EMD | Definitivo obs. / EMD | Difíciles (177) obs. / EMD |
|---|---|---|---|---|---|
| C3 − C1 | +0,011 / 0,030 | −0,026 / 0,058 | −0,005 / 0,055 | +0,002 / 0,051 | −0,104 / 0,081 |
| C2 − C1 | −0,004 / 0,019 | +0,122 / 0,087 | +0,054 / 0,048 | +0,045 / 0,037 | +0,150 / 0,076 |
| C4 − C3 | +0,016 / 0,030 | +0,102 / 0,132 | +0,058 / 0,084 | +0,093 / 0,058 | +0,192 / 0,104 |
| C5 − C4 | −0,016 / 0,020 | −0,049 / 0,060 | −0,063 / 0,062 | −0,010 / 0,013 | −0,027 / 0,032 |
| C4 − C2 | +0,032 / 0,035 | −0,047 / 0,089 | −0,001 / 0,065 | +0,050 / 0,040 | −0,062 / 0,092 |

Varias diferencias nulas del corpus de diecisiete documentos son menores que su EMD. C3 frente a C1
en el ampliado, por ejemplo, vale $+0{,}011$ frente a un EMD de $0{,}030$, un resultado compatible con un
efecto real más pequeño de lo que el diseño podía distinguir del azar.

## Éxito en las primeras posiciones

La lectura más directa para el usuario es con qué frecuencia el documento correcto aparece de
inmediato. Fracción de consultas con un documento relevante en la primera posición y entre las tres
primeras.

| Configuración | Ampliado @1 / @3 | Difícil A @1 / @3 | Difícil B @1 / @3 | Definitivo @1 / @3 | Difíciles (177) @1 / @3 |
|---|---|---|---|---|---|
| BM25 | 0,75 / 0,94 | 0,12 / 0,17 | 0,32 / 0,45 | 0,62 / 0,86 | 0,20 / 0,27 |
| C1 · Denso puro | 0,88 / 0,94 | 0,40 / 0,77 | 0,58 / 0,83 | 0,81 / 0,89 | 0,39 / 0,52 |
| C2 · Denso con ontología | 0,87 / 0,96 | 0,65 / 0,88 | 0,64 / 0,94 | 0,86 / 0,94 | 0,54 / 0,68 |
| C3 · Híbrido | 0,87 / 0,99 | 0,44 / 0,60 | 0,62 / 0,77 | 0,81 / 0,91 | 0,33 / 0,40 |
| C4 · Híbrido con ontología | 0,92 / 0,97 | 0,62 / 0,79 | 0,64 / 0,91 | 0,94 / 0,97 | 0,50 / 0,60 |
| C5 · C4 con realce | 0,90 / 0,94 | 0,54 / 0,75 | 0,56 / 0,79 | 0,92 / 0,95 | 0,46 / 0,58 |

## Ponderación por la demanda real y registro de redacción

Si cada consulta del conjunto ampliado se pondera según la cuota de su reporte objetivo en las
$6.620$ solicitudes reales, el orden de las configuraciones no cambia: C4 obtiene $0{,}964$, el híbrido
sin ontología $0{,}959$ y el denso puro $0{,}944$. En el conjunto difícil B, desglosado por registro de
redacción, C4 es la mejor en las consultas formuladas como pregunta ($0{,}884$) y C2 en las
administrativas ($0{,}817$) y en las telegráficas ($0{,}866$), sin que ningún registro invierta las
conclusiones generales.

## Estado de las hipótesis

«Confirmatoria» indica evidencia de conjuntos y análisis fijados en el plan posterior a la
auditoría; «exploratoria», evidencia de análisis definidos después de ver resultados.

| Hipótesis | Estado | Evidencia principal |
|---|---|---|
| H1a: el híbrido supera a BM25 | sostenida (confirmatoria) | concordante en los cinco conjuntos y con *bootstrap* por reporte |
| H1b: el híbrido supera al denso | no sostenida | nula en cuatro conjuntos; adversa con paráfrasis en el corpus de $177$ documentos ($-0{,}104$) y entre $757.554$ documentos ($-0{,}135$) |
| H2: la ventaja se concentra en entidades | no sostenida | no contrastable en la Versión 1; en competencias, sin diferencia y cerca del techo; para personas hace falta un diccionario de entidades |
| H3a: la ontología mejora al denso | sostenida con condiciones (confirmatoria) | concordante en el sintético, los difíciles y el definitivo; nula en el ampliado; crece con el solape; supera a tres controles de la misma longitud a escala |
| H3b: la ontología mejora al híbrido | sostenida con condiciones | concordante en el definitivo y en el metaanálisis de A y B; nula sin solape con la ontología |
| H4: la fragmentación mejora | no sostenida | documentos de $64$ a $184$ palabras; ningún tamaño supera al documento completo |
| H5: el realce mejora el orden | rechazada | nunca mejora; adverso y concordante en los difíciles |
| H6: truncar el vector no pierde calidad | sostenida a partir de $512$ dimensiones | equivalencia con margen de $0{,}01$ en todos los conjuntos a $512$; a $256$ solo en el ampliado |
| H7: una fusión distinta de RRF es mejor | sostenida en el corpus v3 (exploratoria en el plan) | con diecisiete reportes ninguna variante es concordante; con $811$ documentos la convexa supera a RRF ($+0{,}089$) y al denso ($+0{,}085$) |

Los resultados negativos pesan tanto como los positivos. Que el híbrido no supere al denso advierte
que no conviene asumir que «híbrido es mejor» y que la fusión por rango puede costar puntos. Que el
realce falle muestra que un detector por clase no sirve cuando todos los documentos cubren las
mismas clases. Que el estrato de entidad exacta midiera el tema es una advertencia para cualquier
evaluación de objetivo conocido. Y que la fragmentación no ayude con documentos cortos ahorra
complejidad.

## Vocabulario estadístico mínimo

| Término | Qué significa en este trabajo |
|---|---|
| Comparación pareada | dos configuraciones evaluadas sobre las mismas consultas, consulta por consulta |
| Prueba de Wilcoxon | prueba de rangos con signo sobre las diferencias por consulta; no supone normalidad y descarta los empates |
| Prueba de permutación de signos | compara la diferencia observada con las que salen al cambiar al azar el signo de cada diferencia; exacta con veinte o menos diferencias no nulas, con $20.000$ sorteos en los demás casos |
| Corrección de Holm | ajusta los $p$-valores de una familia de comparaciones para limitar la probabilidad de al menos un falso positivo |
| Concordante | significativa con Wilcoxon y con permutación después de Holm |
| Pares con diferencia no nula | consultas en las que las dos configuraciones difieren; determinan el poder real de la prueba |
| Correlación biserial por rangos | tamaño del efecto entre $-1$ y $1$ coherente con Wilcoxon |
| Intervalo *bootstrap* | intervalo obtenido al remuestrear muchas veces; si incluye el cero, la diferencia no es concluyente |
| *Bootstrap* agrupado | remuestrea reportes, pruebas o componentes de consultas con relevantes compartidos, en lugar de consultas sueltas |
| *Leave-one-set-out* y *leave-one-group-out* | elegir un parámetro con todos los conjuntos o grupos menos uno y evaluarlo en el excluido, para no ajustar y evaluar sobre los mismos datos |
| Margen de equivalencia | para la dimensión del vector, una pérdida se acepta si el límite inferior de su intervalo no baja de $-0{,}01$ |
| Metaanálisis de efectos fijos | combina los efectos de A y B ponderados por su precisión; $Q$ mide si discrepan |
| Efecto mínimo detectable | la diferencia más pequeña que el número de consultas permitía distinguir del azar |
| Pseudo-replicación | contar como independientes observaciones casi idénticas, lo que infla el tamaño de muestra |

Los parámetros fijos de toda la estadística son la semilla $42$, $1.000$ réplicas *bootstrap* en la
escalera y $2.000$ en los *bootstrap* agrupados.

## Límites que siguen abiertos

Las conclusiones sobre la ontología y sobre la fusión dependen de un protocolo en el que el mismo
autor redactó las consultas difíciles y la ontología, sin juicios de expertos. El léxico dividido y
el análisis de dosis-respuesta reducen esa circularidad sin eliminarla. Esas conclusiones
describen el comportamiento de las configuraciones bajo este protocolo, y todavía no frente a
consultas de usuarios.

No hay juicios de expertos. El procedimiento de anotación está preparado (reunión de candidatos de
las seis configuraciones, hojas ciegas con orden aleatorio distinto para dos anotadores, escala de
$0$ a $2$, $\kappa$ de Cohen ponderado y adjudicación de los desacuerdos), pero no se ha aplicado. Un
$\kappa$ superior a $0{,}6$ sobre al menos las $50$ consultas candidatas respaldaría los juicios
*silver* del conjunto ampliado.

La evidencia procede de una sola plataforma, de una ventana de observación de seis semanas y media
y de un solo codificador denso. Los resultados no se extrapolan a otras plataformas ni a otros
idiomas, y la comparación con otros codificadores multilingües queda pendiente.

Sobre el registro completo quedan dos pendientes concretos: los distractores no recibieron juicios,
así que un objeto pertinente no juzgado cuenta como no relevante, y la restricción por función no se
ha comparado con la combinación convexa, que ataca el mismo daño por otra vía. La ontología también
está por completar en todos los reportes con el mismo cuidado que los nueve originales.

El primer paso del trabajo futuro es una validación con personas ajenas al diseño. Tres a cinco
personas que conozcan la plataforma pero no el buscador, por ejemplo del equipo de soporte o de las
federaciones, escribirían dos o tres preguntas cada una para diez reportes, a partir de una
descripción de la necesidad y sin ver el vocabulario del sistema. Con $60$ a $100$ consultas se puede
repetir la comparación entre C2, C4 y la combinación convexa como validación independiente.

## Cómo reproducirlo

La robustez por reporte, la exclusión de un reporte a la vez y la dosis-respuesta salen de
`make robustez`
([`analisis_robustez.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/analisis_robustez.py)),
y el aporte del codificador sobre BM25, el éxito en las primeras posiciones, el efecto mínimo
detectable, el metaanálisis y la ponderación por la demanda de `make complementario`
([`analisis_complementario.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/analisis_complementario.py)).
Ninguno de los dos necesita el modelo: trabajan sobre las métricas por consulta ya guardadas. Las
funciones estadísticas están en
[`lib/stats.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/lib/stats.py)
y las métricas en
[`lib/metrics.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/lib/metrics.py);
`make test` corre sus pruebas y las diecinueve pruebas automáticas de
[`tests/test_nucleo.py`](https://github.com/luispenaranda08/semantic_search_engine/blob/main/experimentos/tests/test_nucleo.py).
`make anotacion` genera las hojas ciegas para los anotadores y comprueba el cálculo del $\kappa$, y el
formulario de necesidades para la validación con personas ajenas al diseño está en
[`anotacion/`](https://github.com/luispenaranda08/semantic_search_engine/tree/main/experimentos/anotacion).
