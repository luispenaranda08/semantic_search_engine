# La monografía

{download}`Descargar la monografía en PDF <../monografia/monografia_buscador_semantico.pdf>` ·
[fuente LaTeX](https://github.com/luispenaranda08/semantic_search_engine/blob/v1.1-tesis/monografia/monografia_buscador_semantico_PRIME.tex)

## Resumen

Las plataformas públicas concentran su conocimiento operativo en reportes y funcionalidades
difíciles de localizar. En este trabajo se estudió un buscador semántico en español para una
plataforma pública de gestión deportiva. La plataforma no ofrece un buscador sobre sus reportes y
sus cajas de texto son filtros de lista que no registran lo escrito, así que no existen consultas
escritas por usuarios; las consultas y sus juicios de relevancia se derivaron de la estructura
del sistema. Se analizaron $14.718$ ejecuciones registradas en seis semanas y media, de las
cuales $6.620$ fueron solicitudes reales de datos, concentradas en cinco de diecisiete reportes.
Se construyó una ontología del dominio y se evaluaron, con una escalera de ablación, un modelo
léxico, un codificador denso preentrenado, la fusión por rango, metadatos de la ontología y un
realce por entidad, sobre diecisiete reportes, sobre $177$ documentos y sobre $811$ documentos
de cinco tipos.

La fusión por rango superó a la búsqueda léxica, pero perjudicó al codificador denso cuando la
consulta no compartía vocabulario con el documento; un análisis exploratorio mostró que una
combinación convexa de puntuaciones superó a ambas en el corpus de $811$ documentos. La ontología
mejoró la recuperación en proporción a los términos compartidos, conservó su aporte al repetir la
evaluación entre $757.554$ documentos y superó a tres controles de la misma longitud; el realce no
aportó. En la implementación de investigación cada consulta tardó $0{,}35$ segundos, casi todo en
codificarla. En una extensión exploratoria a todo el registro, un diccionario de entidades puso
primera a la persona buscada en el $98{,}7\%$ de los casos con el nombre exacto y en el $97{,}7\%$
con un error de digitación, frente al $87{,}7\%$ y el $57{,}3\%$ del ranking híbrido sin él, y
restringir cada búsqueda a los tipos de objeto de su función eliminó los distractores de un corpus
heterogéneo.

**Recomendación.** Para la Versión 1 se recomienda C4, el híbrido con ontología, sin realce, con el
vector a $512$ dimensiones. La combinación convexa es la opción más prometedora para un buscador
sobre todos los objetos funcionales, y su adopción se confirmará con la validación con usuarios.

## Preguntas de investigación

| | Pregunta | Respuesta corta |
|---|---|---|
| P1 | ¿Supera el híbrido a BM25 y al denso? | A BM25 sí, en todos los conjuntos. Al denso no; con $811$ documentos la combinación convexa sí supera a ambos. |
| P2 | ¿La ventaja se concentra en entidades exactas? | No como ventaja de la fusión. La búsqueda por entidad necesita un diccionario de entidades. |
| P3 | ¿La ontología mejora al denso y al híbrido? | Sí, con condiciones: depende de los términos compartidos y supera a controles de igual longitud. |
| P4 | ¿Ayuda fragmentar los documentos? | No, con documentos de $64$ a $184$ palabras. |
| P5 | ¿Mejora el realce por entidad? | No, para ningún valor de $\lambda$. Se descarta. |
| P6 | ¿Qué configuración y dimensión convienen? | Las neuronales cuestan lo mismo (unos $0{,}35$ s, $2$ GiB). $512$ dimensiones son no inferiores a la nativa en el ampliado y en los difíciles. |
| P7 (exploratoria) | ¿Se mantienen las conclusiones a la escala del registro completo? | Sí, con matices: la ontología conserva su aporte y la búsqueda por entidad necesita un diccionario aparte. |

## Validez

Las consultas y la ontología se construyeron desde la estructura del propio sistema, y la
evaluación usa un protocolo de objetivo conocido. Las conclusiones se apoyan en comparaciones
entre configuraciones bajo ese mismo protocolo, con dos pruebas y corrección de Holm. El primer
paso del trabajo futuro es una validación con personas ajenas al diseño.
