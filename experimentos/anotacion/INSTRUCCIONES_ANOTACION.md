# Instrucciones de anotación de relevancia

**Qué vas a hacer.** Para cada consulta de usuario verás varios reportes del sistema y deberás
decir cuánto sirve cada uno para responder esa consulta. Tus juicios se usan como "respuesta
correcta" para evaluar el buscador. No hay respuestas buenas o malas por parecerse a lo que
hizo el sistema: juzga solo con tu criterio de persona que conoce la plataforma.

**Archivo.** `hoja_anotador_A.csv` (o `_B`). Cada fila es un par *consulta–reporte*. Rellena
solo la columna `grado` (y, si quieres, `comentario`). No cambies las demás columnas ni el orden.
Trabaja **sin consultar** al otro anotador ni la hoja del otro.

## Escala

| Grado | Significado | Pregunta de control |
|---|---|---|
| **2** | **Responde la consulta.** Es el reporte que el usuario abriría para resolver su necesidad. | «Si el usuario abre este reporte, ¿encuentra lo que busca?» → sí |
| **1** | **Ayuda en parte.** Contiene información relacionada o sirve como paso intermedio, pero no es el reporte principal. | «¿Le sirve, aunque tenga que complementar con otro?» → sí |
| **0** | **No sirve** para esa consulta. | «¿Se equivocó de reporte?» → sí |

## Reglas

1. Juzga el **reporte** (título y descripción), no la consulta aislada. Si dudas de qué contiene
   un reporte, abre el sistema real y míralo.
2. Una consulta puede tener **más de un** reporte con grado 2 si dos reportes la responden por
   igual. También puede no tener ninguno; en ese caso usa 1 para el mejor y no fuerces un 2.
3. **No** premies a un reporte por tener palabras iguales a las de la consulta. Importa lo que
   el usuario quiere lograr.
4. Si la consulta menciona un nombre propio (de persona o institución), asume que el nombre es
   un ejemplo cualquiera: juzga el **tipo** de información que pide.
5. Si no puedes decidir entre dos grados, elige el **menor** y anota el motivo en `comentario`.
6. No dejes filas vacías: el cálculo del acuerdo rechaza hojas incompletas.

## Ejemplos

| Consulta | Reporte | Grado | Por qué |
|---|---|---|---|
| «certificados pendientes de un atleta» | Reporte de Documentación de Deportistas | 2 | Es el reporte de documentos por estado. |
| «certificados pendientes de un atleta» | Reporte Individual de Deportistas | 1 | Lista al atleta pero no el estado de sus documentos. |
| «certificados pendientes de un atleta» | Reporte de Instituciones | 0 | No trata documentos de deportistas. |

## Tiempo y entrega

La hoja tiene **511 pares** (unos 5 por consulta, 102 consultas). A 1–2 minutos por par son entre 8 y 17 horas por anotador. Para repartirlo,
anota **primero las consultas `d001`–`d052`** (el conjunto difícil, ~260 pares): son las que más valor dan. Si no es posible completar todo, se puede
reducir la profundidad del pool (`python3 anotacion/preparar_anotacion.py --profundidad 2`). Devuelve el CSV con el mismo nombre. Después se calcula el
acuerdo entre anotadores (kappa de Cohen, ponderado lineal) y los desacuerdos se resuelven en una reunión corta; el grado final queda en
`datos/qrels_gold.jsonl`.

## Privacidad

Las hojas no contienen datos personales: los nombres que aparezcan en las consultas son
inventados. No añadas nombres reales en `comentario`.
