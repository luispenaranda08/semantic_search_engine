# Cómo explicar los resultados en palabras sencillas

Esta guía es para decir los resultados en voz alta, ante cualquier público: jurado, asesor, gente de la empresa o tu familia.
Cada sección trae tres cosas:

- **La idea**, en una frase.
- **Cómo decirlo**, un texto que puedes leer casi tal cual.
- **Si te preguntan**, la respuesta corta a la duda más probable.

Las cifras son las vigentes al 20 de octubre de 2026. Si alguna no coincide con la monografía, manda la monografía.

---

## 1. El problema, en una frase

**La idea:** la plataforma tiene muchos reportes y la gente no sabe cuál abrir. Queremos que escriba lo que necesita, como en Google, y el sistema le muestre el reporte correcto.

**Cómo decirlo:**
> "Imaginen una biblioteca con diecisiete libros, cada uno con un título técnico. La persona sabe qué quiere saber, por ejemplo en qué etapa va un deportista, pero no sabe en qué libro está. Mi proyecto es el bibliotecario: la persona le dice lo que busca con sus propias palabras y él le entrega el libro correcto."

**Las cifras que lo justifican:**
- En seis semanas y media hubo **6.620 consultas reales**, unas **145 por día**.
- Cinco reportes concentran el **83 %** de las consultas. El más pedido, el Reporte Individual de Deportistas, se lleva el **40,4 %**.
- No hay ningún ejemplo etiquetado de "esta pregunta corresponde a este reporte". Por eso no se puede entrenar un modelo propio y hay que usar modelos ya entrenados.

---

## 2. Qué se comparó (las seis configuraciones)

**La idea:** se probaron seis maneras de buscar, cada una con una pieza más que la anterior, para saber qué aporta cada pieza.

**Cómo decirlo:**
> "Es como probar una receta agregando un ingrediente a la vez. Si el plato mejora al añadir la sal, fue la sal."

| Nombre | En palabras sencillas |
|---|---|
| **BM25** | Busca por palabras iguales, como el Ctrl+F de un documento. Si usted escribe "jugador" y el reporte dice "deportista", no lo encuentra. |
| **C1 · Denso** | Busca por significado. Un modelo de inteligencia artificial convierte cada texto en una lista de números, y los textos que significan algo parecido quedan cerca. Entiende que "jugador" y "deportista" son parecidos. |
| **C2 · Denso + ontología** | Lo mismo, pero a cada reporte se le agrega un "diccionario" del tema: sinónimos y preguntas típicas. |
| **C3 · Híbrido** | Combina las dos búsquedas: por palabras y por significado. |
| **C4 · Híbrido + ontología** | El híbrido, con el diccionario del tema. **Es la configuración recomendada.** |
| **C5 · C4 + realce** | Le da un empujón extra a los reportes que mencionan la misma "entidad" que la consulta (deportista, institución…). **No sirvió y se descartó.** |

**Si te preguntan qué es la ontología:**
> "Es un mapa del tema: qué cosas existen (deportista, institución, evento, región), cómo se llaman también (atleta, colegio, torneo) y cómo se relacionan. Se lo pegamos a cada reporte para que el buscador sepa de qué trata aunque el usuario use otras palabras."

---

## 3. Cómo se midió (las métricas, sin fórmulas)

### 3.1 La principal: nDCG@10

**La idea:** mide si el reporte correcto aparece entre los diez primeros y qué tan arriba.

**Cómo decirlo:**
> "Es como calificar la primera página de Google. Si el resultado que usted buscaba sale de primero, la nota es 1. Si sale segundo, se le descuenta un poco porque tuvo que mirar más abajo. Si no aparece entre los diez primeros, la nota es 0. Al final se promedian las notas de todas las preguntas."

| Dónde aparece el reporte correcto | Nota (nDCG@10) |
|---|---|
| 1.º lugar | 1,00 |
| 2.º lugar | 0,63 |
| 3.º lugar | 0,50 |
| 4.º lugar | 0,43 |
| 10.º lugar | 0,29 |
| No aparece en los diez primeros | 0 |

**Cómo leer un número:**
- Un **0,96** significa que casi siempre el reporte correcto sale de primero.
- Una **diferencia de 0,05** entre dos sistemas equivale, más o menos, a que en una de cada siete preguntas el reporte correcto baja un puesto.

### 3.2 Las demás, en una línea cada una

| Métrica | En palabras sencillas |
|---|---|
| **Éxito en el 1.º lugar** | De cada 100 preguntas, ¿en cuántas el reporte correcto salió de primero? Es la más fácil de explicar. |
| **Éxito entre los 3 primeros** | ¿En cuántas salió en el podio? |
| **MRR** | En promedio, ¿en qué posición sale el primer resultado correcto? 1 = siempre primero; 0,5 = en promedio segundo. |
| **Recall@100** | ¿Lo encontró, aunque sea abajo, entre los 100 primeros? Separa "no lo encontró" de "lo encontró pero lo ordenó mal". |
| **P@10** | De los diez primeros resultados, ¿cuántos sirven? Con una sola respuesta correcta por pregunta, su máximo es 0,1. Que salga baja es normal. |

### 3.3 La estadística: ¿la diferencia es real o es suerte?

**La idea:** que un sistema saque mejor nota en estas preguntas no garantiza que sea mejor en general; podría ser suerte de las preguntas elegidas.

**Cómo decirlo:**
> "Si lanzo una moneda diez veces y salen seis caras, no puedo decir que la moneda esté cargada. Con las pruebas estadísticas pasa lo mismo: verifican si la diferencia es lo bastante grande y consistente como para no ser casualidad. Solo digo que un sistema es mejor cuando dos pruebas distintas lo confirman. A eso le llamo una diferencia **concordante**."

**Si te preguntan:**
- **¿Qué es el p-valor?** "La probabilidad de ver una diferencia así si en realidad no hubiera diferencia. Si es menor que 0,05, la tomamos como real."
- **¿Por qué dos pruebas?** "Porque hay estudios que muestran que la prueba de Wilcoxon, la más común, a veces se equivoca en este tipo de evaluaciones. La confirmo con una prueba de permutación."
- **¿Qué es la corrección de Holm?** "Si hago muchas comparaciones, alguna saldrá 'significativa' por pura suerte. Holm sube la exigencia para compensarlo."
- **¿Qué es el bootstrap por reporte?** "Varias preguntas apuntan al mismo reporte, así que no son independientes. Repito el cálculo miles de veces sorteando reportes en vez de preguntas, para que un solo reporte no infle el resultado."

### 3.4 Si te preguntan cómo entrenaste el modelo

**La idea:** no se entrenó nada. Todo es evaluación.

**Cómo decirlo:**
> "Aquí no hay entrenamiento, así que no hay métricas de entrenamiento ni separación entre datos de entrenamiento y de prueba. Uso un modelo que ya viene entrenado, tal como lo publicaron sus autores, y una fórmula clásica de búsqueda por palabras que no aprende nada. Todo lo que mido es qué tan bien encuentra y cuánto cuesta. Por eso no necesito miles de ejemplos etiquetados, que es justamente lo que no existe en este caso."

---

## 4. Los conjuntos de preguntas: con qué se puso a prueba

**Cómo decirlo:**
> "Probé el buscador con cuatro tipos de examen."

| Examen | En palabras sencillas | Dificultad |
|---|---|---|
| **Sintético (40)** | Preguntas que escribí a partir de los reportes. | Fácil: usan las mismas palabras. |
| **Ampliado (127)** | Preguntas reconstruidas a partir de lo que la gente realmente consultó en el historial. | Media: la más parecida al uso real. |
| **Difícil A (52) y B (78)** | Paráfrasis y lenguaje coloquial **sin** las palabras del reporte, por ejemplo "quién pasó a la etapa que sigue". | Difícil: obliga a entender el significado. |
| **Corpus definitivo (177 documentos)** | Los 17 reportes más **160 pruebas deportivas reales** (por ejemplo, "Fútbol de Salón Juvenil – Región Orinoquía"), con 180 preguntas. | Más realista: hay mucho más dónde confundirse. |

---

## 5. Los resultados, uno por uno

### 5.1 Resultado principal
> "La configuración recomendada, el híbrido con ontología, saca **0,96 de 1** en el corpus definitivo y deja el reporte correcto **en primer lugar en el 94 % de las preguntas**. Entre los tres primeros, en el **97 %**."

### 5.2 Buscar por significado le gana a buscar por palabras
> "La búsqueda por palabras sola (BM25) saca 0,77. Con significado y palabras juntos, 0,96. Esta mejora se confirma en todos los exámenes. Pero hay que ser justo: la mayor parte de la mejora la pone el modelo de significado. Mezclarle la búsqueda por palabras no siempre ayuda."

### 5.3 El "diccionario" del tema (la ontología) sí ayuda, cuando el usuario no usa las palabras del sistema
> "Cuando la persona escribe con otras palabras, el diccionario del tema sube la nota del buscador por significado en unos **7 puntos** (0,07). Y cuantas más palabras de la pregunta aparecen en ese diccionario, más ayuda. Eso demuestra que funciona como un puente entre cómo habla la gente y cómo está escrito el sistema."

### 5.4 Mezclar palabras y significado puede estorbar cuando la gente habla distinto
> "Con muchos documentos parecidos y preguntas coloquiales, la búsqueda por palabras se confunde con palabras comunes como 'deportistas' o 'región', y al mezclarla empeora el resultado en unos 10 puntos. Por eso recomiendo el híbrido para las consultas habituales de la plataforma, y digo explícitamente que para preguntas muy coloquiales conviene más el modelo de significado solo."

### 5.5 El empujón por entidad no sirvió
> "Probé darle un empujón a los reportes que mencionan lo mismo que la pregunta (deportista, institución, etc.). Nunca mejoró, con ningún tamaño de empujón. El detector de entidades marcaba cuatro a seis reportes por pregunta, casi como si adivinara, así que empujaba a muchos a la vez y no al correcto. Lo descarté."

### 5.6 El hallazgo más interesante: un examen que no medía lo que decía
> "Tenía un grupo de preguntas con nombres de personas, del tipo 'documentos del deportista Julián Gómez', que supuestamente medía si el buscador encuentra por nombre. Hice una prueba de control: borré el nombre y repetí. Si el nombre importara, el resultado debería empeorar, y en cambio mejoró. Los nombres no están en ningún reporte, así que ese grupo medía el tema del reporte y no el nombre. Lo detecté yo mismo y lo reporto: es parte del rigor."

### 5.7 Partir los documentos en pedazos no ayudó
> "Los reportes son cortos, de unas 100 palabras. Partirlos en fragmentos no mejora nada. Eso sirve para documentos largos, que aquí no hay."

### 5.8 La prueba más grande: 811 documentos de cinco tipos (corpus v3)

**La idea:** se probó el buscador con todo lo que la plataforma sabe hacer, no solo con reportes: quién puede hacer qué (roles y permisos), las pruebas deportivas y las reglas de inscripción.

> "En la industria GovTech nadie escribe en una caja de búsqueda, como en Google o en Rappi: la gente navega menús y reportes que ya existen. Eso significa que no hay una consulta humana que yo pueda tomar como punto de partida. Así que la construí desde el propio sistema: si existe el permiso 'quitar medalla', la pregunta 'quién puede quitar una medalla' tiene una respuesta correcta conocida. Y para no hacer trampa, partí cada lista de sinónimos en dos: una mitad se la di al diccionario del tema y la otra la usé para redactar las preguntas. Así ninguna pregunta usa una palabra que yo le haya regalado al buscador."

**Qué salió:**
> "Con 811 documentos no hay un ganador único. Cuando la pregunta comparte palabras con el documento (por ejemplo 'judo juvenil hombres'), la combinación de palabras y significado gana. Cuando no comparte ninguna (por ejemplo 'cuántos jugadores por equipo en básquet', y el documento dice 'deportistas por grupo en Baloncesto'), la búsqueda por palabras mete ruido y hunde el resultado: de 0,91 a 0,43. El buscador por significado con el diccionario del tema es el más parejo: en promedio saca 0,80 frente a 0,77 del combinado."

> "Además encontré que el propio sistema nombra igual de distinto que la gente: 'Fútbol de Salón' y 'Fútbol sala' aparecen como dos deportes, y las distancias se escriben 'MTS' o 'MTRS'. Si ni los datos oficiales usan una sola palabra, buscar solo por palabras exactas no puede funcionar."

**La solución: mezclar por puntaje, no por posición:**
> "El problema estaba en cómo se mezclaban las dos búsquedas. La mezcla clásica (RRF) solo mira posiciones: el primer resultado por palabras pesa igual cuando encontró algo muy claro que cuando encontró solo una palabra suelta. Probé otra forma: sumar los puntajes, 80 % significado y 20 % palabras. Si la búsqueda por palabras no encuentra nada claro, sus puntajes son bajos y casi no mueven nada; si encuentra algo claro, sí pesa."

> "Con esa mezcla el buscador saca 0,80 en las 450 preguntas, frente a 0,71 de las otras dos opciones, y la diferencia se confirma con dos pruebas estadísticas. Y lo más importante: no pierde en ningún tipo de pregunta. En las reglas pasa de 0,44 a 0,94."

> "¿Cómo sé que el 80/20 no está hecho a la medida? Porque lo elegí seis veces, cada vez sin mirar el grupo que iba a evaluar, y las seis veces salió 80/20. Y en el corpus pequeño de 17 reportes también había salido 80/20."

**Qué recomiendo ahora:**
> "Para la primera versión, solo con reportes, sirve el híbrido con diccionario (C4). Para buscar en todo el sistema, la mezcla por puntajes 80/20 sobre el texto con diccionario. Cuesta lo mismo, porque usa las mismas dos búsquedas."

---

## 6. Los tiempos y el costo (lo más fácil de explicar)

### 6.1 Primero, la unidad
> "Mido en **milisegundos**. Un milisegundo es la milésima parte de un segundo: **1.000 milisegundos son 1 segundo**. Un parpadeo dura entre 100 y 400 milisegundos."

### 6.2 Qué pasa cuando alguien escribe una pregunta

| Paso | Tiempo | Cómo decirlo |
|---|---|---|
| 1. El modelo "lee" la pregunta y la convierte en números | **351 ms** | "Lo que más tarda: un tercio de segundo, lo que dura un parpadeo largo." |
| 2. Busca por palabras | 0,09 ms | "Instantáneo: unas cuatro mil veces más rápido que el paso 1." |
| 3. Compara con los reportes | 0,002 ms | "Instantáneo." |
| 4. Mezcla las dos listas | 0,005 ms | "Instantáneo." |
| **Total que espera la persona** | **≈ 0,35 segundos** | "Menos de medio segundo. Se siente inmediato." |

**Cómo decirlo:**
> "El usuario espera unos 0,35 segundos por respuesta. Casi todo ese tiempo, el 99,9 %, es el modelo leyendo la pregunta. Buscar y mezclar no cuesta nada. En usabilidad se acepta que por debajo de un segundo la persona no siente que tiene que esperar."

### 6.3 Qué significan p50 y p95
> "La mediana, o p50, es lo normal: la mitad de las veces responde más rápido que eso. El p95 es una de las respuestas lentas habituales: solo una de cada veinte tarda más. Aquí la mediana es 351 ms y el p95, 408 ms. Incluso las lentas siguen por debajo de medio segundo."

### 6.4 Lo que se hace una sola vez y lo que se hace siempre
> "Hay cosas que se hacen **una vez**, al prender el sistema o al agregar reportes, y el usuario nunca las espera. Por ejemplo, cargar el modelo tarda 7 segundos, y procesar cada reporte nuevo, una séptima de segundo. Y hay cosas que se hacen **en cada búsqueda**: esas son los 0,35 segundos."

### 6.5 Cuánto aguanta
> "Si cada búsqueda toma un tercio de segundo, un solo computador puede atender unas tres por segundo, del orden de 250.000 al día. Hoy la plataforma recibe unas 145 al día, que equivalen a **menos de un minuto de trabajo diario**. Sobra capacidad."

### 6.6 Sin tarjeta gráfica
> "En un computador normal, sin aceleración gráfica, cada búsqueda tarda unos 0,63 segundos. Sigue siendo menos de un segundo."

### 6.7 Memoria y precio
> "El costo real no es el tiempo: es la memoria. El modelo ocupa unos **2 GB de RAM**, menos que una pestaña pesada del navegador multiplicada por unas cuantas. Y no hubo que entrenar nada, así que no se gastó en servidores con GPU ni en etiquetar datos."

### 6.8 Por qué no elegir lo más rápido
> "La búsqueda solo por palabras responde casi al instante y no necesita memoria. Pero acierta mucho menos: pierde entre 7 y 51 puntos según el examen. Las cinco versiones con inteligencia artificial cuestan lo mismo en tiempo, así que la decisión se toma solo por calidad."

### 6.9 Las 512 "dimensiones"
> "El modelo describe cada texto con 1.024 números. Se puede recortar a 512 sin perder calidad, y así el índice ocupa la mitad. Recortar a 256 funcionó en el examen fácil pero no en el difícil, así que recomiendo 512. A esta escala el ahorro es pequeño; importa si algún día hay cientos de miles de documentos."

---

## 7. La conclusión, en 30 segundos

> "Construí y evalué un buscador semántico en español para una plataforma pública de gestión deportiva, sin datos etiquetados y sin entrenar modelos. La mejor configuración combina búsqueda por significado, búsqueda por palabras y un diccionario del tema. Deja el reporte correcto de primero en el 94 % de las preguntas y responde en un tercio de segundo. Descubrí que el diccionario del tema ayuda más cuanto más se aleja el usuario del vocabulario del sistema, que mezclar la búsqueda por palabras puede estorbar con preguntas coloquiales, y que uno de mis propios exámenes no medía lo que decía; lo corregí y lo reporto. Todo es reproducible con un solo comando."

---

## 8. Lo que todavía falta (y cómo decirlo sin que suene a debilidad)

**Cómo decirlo:**
> "Estos son los límites del trabajo y lo que haría a continuación. Ninguno invalida los resultados, pero hay que tenerlos presentes."

### Limitaciones que debes decir tú, antes de que te las pregunten

| Limitación | Cómo decirlo |
|---|---|
| **No hay jueces humanos expertos** | "La respuesta correcta de cada pregunta salió del historial o la definí yo. No tuve expertos que calificaran los resultados. Por eso las notas sirven para comparar sistemas entre sí, no como promesa de acierto en producción." |
| **No hay preguntas reales escritas por usuarios** | "La plataforma no guarda lo que la gente escribe en texto libre, porque hoy no tiene buscador. Reconstruí las preguntas desde el historial y escribí paráfrasis. Las preguntas difíciles las redacté yo, y eso puede favorecer al diccionario del tema; lo controlé con el análisis de 'dosis-respuesta', pero no lo elimina del todo." |
| **Una sola plataforma y un solo modelo** | "Los resultados son de esta plataforma, en español, con este modelo de inteligencia artificial (jina-embeddings-v3). Con otro modelo podrían cambiar los números." |
| **El diccionario del tema está incompleto** | "Solo cubre 9 de los 17 reportes. Ampliarlo automáticamente a 14 ayudó poco; hay que hacerlo con el mismo cuidado que los primeros." |

### Lo que falta hacer, en orden

1. **Que otras personas escriban preguntas**, o generarlas automáticamente sin que el generador vea el diccionario del tema. Así se elimina la sospecha de que el autor las escribió a la medida.
2. **Medir la consistencia de los juicios.** Califico a ciegas una muestra y la repito dos semanas después, o uso un juez automático como segunda opinión. No reemplaza a los expertos, pero da una medida de confiabilidad.
3. **Completar el diccionario del tema** en los 17 reportes.
4. **Probar otro modelo de significado y un reordenador**, para no depender de uno solo. Requiere descargar modelos de 1 a 2 GB.
5. **Una mezcla más inteligente** que le baje el peso a la búsqueda por palabras cuando la pregunta no comparte vocabulario con el sistema. Es la mejora más prometedora según los resultados.
6. **Llevarlo a producción:** ya hay un prototipo en Rust que implementa la configuración recomendada. Falta medir su tiempo de punta a punta y, si se quiere más velocidad, correr el modelo en formato optimizado (ONNX).
7. **Pendientes de forma:** rehacer los notebooks 00c y 01–07 con las cifras nuevas, confirmar si existe una autorización escrita de la organización para el uso académico de los datos (está marcado en la sección de ética), verificar las referencias escritas de memoria y subir la versión final al repositorio.

---

## 9. Preguntas difíciles y respuestas cortas

| Pregunta | Respuesta |
|---|---|
| "¿0,96 significa que acierta el 96 %?" | "No exactamente. Es una nota que premia que salga arriba. El dato directo es que sale de primero en el 94 % de las preguntas y entre los tres primeros en el 97 %, en este examen. Con usuarios reales probablemente sería menor." |
| "¿Por qué no usar ChatGPT?" | "Porque el problema es encontrar el reporte correcto, no redactar una respuesta. Un modelo de lenguaje grande sería más lento y más caro, y se equivoca de forma más difícil de detectar. Lo que uso es la pieza de búsqueda que esos sistemas usan por dentro." |
| "¿Por qué no entrenaste tu propio modelo?" | "Porque no existen ejemplos etiquetados de pregunta y reporte correcto, y sin ellos no se puede entrenar. Lo preentrenado ya funciona bien en español." |
| "¿Un tercio de segundo es rápido?" | "Sí. Por debajo de un segundo el usuario no siente la espera. Y casi todo ese tiempo es el modelo leyendo la pregunta; el resto es instantáneo." |
| "Si C2 le gana a C4 en las difíciles, ¿por qué recomienda C4?" | "Para la versión de reportes, porque C4 gana donde la gente usa el vocabulario de la plataforma (+0,050, comprobado con dos pruebas). Pero con 811 documentos mostré que ni C2 ni C4 ganan siempre, y encontré algo mejor: mezclar por puntajes (80 % significado, 20 % palabras) supera a las dos (+0,09) y no pierde en ningún tipo de pregunta. El 80/20 se eligió sin mirar los datos que se evaluaban y salió igual en todos los cortes." |
| "¿Cómo sabe que funciona si no hay consultas reales?" | "Porque en esta plataforma no existen: nadie escribe, todos navegan. Esa es justamente la diferencia con Google o Rappi. Construí las preguntas desde la estructura del sistema, con un control para no hacer trampa, y preparé un formulario para que personas ajenas al proyecto escriban sus propias preguntas." |
| "¿Por qué no lo más rápido?" | "Porque la búsqueda por palabras acierta bastante menos, y todas las versiones con inteligencia artificial cuestan lo mismo en tiempo." |
| "¿Funciona con millones de documentos?" | "La búsqueda sigue en milisegundos con cientos de miles. Lo que crece es la memoria, y por eso recorto los vectores a 512 números." |
| "¿Hay datos personales?" | "No. El índice tiene descripciones de reportes, no datos de personas. Los nombres de las pruebas son inventados, y lo que extraje de la base de datos son solo conteos." |
| "¿Qué es lo más valioso del trabajo?" | "El método: comparar una pieza a la vez, confirmar con dos pruebas estadísticas, y haber detectado y corregido mis propios errores, incluido un examen que no medía lo que decía." |
