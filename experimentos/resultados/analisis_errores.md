# Análisis de errores

Exactitud en la primera posición (acc@1) por sistema:

| Conjunto | n | BM25 | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|---|
| sintetico | 40 | 0.650 | 0.725 | 0.825 | 0.750 | 0.875 |
| ampliado | 127 | 0.748 | 0.882 | 0.866 | 0.874 | 0.921 |
| dificil | 52 | 0.135 | 0.404 | 0.654 | 0.442 | 0.615 |
| dificil_b | 78 | 0.372 | 0.577 | 0.641 | 0.615 | 0.641 |

## sintetico: confusiones más frecuentes

**C1**: promocion_deportistas → sobre_pruebas_caidas_todas_l (4); promocion_deportistas → progreso_y_cumplimiento_meta (2); participacion → cambios_en_la_intencion_part (1); personal_apoyo → individual_deportistas (1); grupos → delegaciones_participacion (1); participacion → delegaciones_participacion (1)

**C2**: promocion_deportistas → sobre_pruebas_caidas_todas_l (2); promocion_deportistas → progreso_y_cumplimiento_meta (1); participacion → cambios_en_la_intencion_part (1); grupos → instituciones (1); participacion → delegaciones_participacion (1); documentacion_deportistas → promocion_deportistas (1)

**C4**: participacion → cambios_en_la_intencion_part (2); promocion_deportistas → sobre_pruebas_caidas_todas_l (1); promocion_deportistas → documentacion_deportistas (1); documentacion_deportistas → promocion_deportistas (1)

Consultas fallidas (primeras 15):

| id | consulta | objetivo | C2: top1 (rango obj.) | C4: top1 (rango obj.) |
|---|---|---|---|---|
| q002 | en qué fase va el deportista Andrés Torres | promocion_deportistas | sobre_pruebas_caidas_todas_l (2) | promocion_deportistas (1) |
| q004 | en qué fase va el deportista María Restrepo | promocion_deportistas | progreso_y_cumplimiento_meta (2) | promocion_deportistas (1) |
| q015 | intención de participación de María Restrepo | participacion | cambios_en_la_intencion_part (2) | cambios_en_la_intencion_part (2) |
| q027 | etapas | promocion_deportistas | sobre_pruebas_caidas_todas_l (4) | sobre_pruebas_caidas_todas_l (3) |
| q033 | cómo saber qué grupos o delegaciones tiene registrada cada i | grupos | instituciones (2) | grupos (1) |
| q034 | resumen de cuántos deportistas han sido promovidos, rechazad | promocion_deportistas | promocion_deportistas (1) | documentacion_deportistas (3) |
| q036 | quiénes manifestaron intención de participar y cómo se distr | participacion | delegaciones_participacion (2) | cambios_en_la_intencion_part (2) |
| q040 | estado de la documentación y los soportes cargados por cada  | documentacion_deportistas | promocion_deportistas (2) | promocion_deportistas (2) |

## ampliado: confusiones más frecuentes

**C1**: documentacion_deportistas → sobre_pruebas_caidas_todas_l (2); promocion_deportistas → instituciones (2); sobre_pruebas_caidas_todas_l → sobre_pruebas_caidas (2); grupos → individual_deportistas (1); participacion → sobre_pruebas_caidas_todas_l (1); individual_deportistas → sobre_resumen_pruebas_caidas (1)

**C2**: documentacion_deportistas → individual_deportistas (2); individual_deportistas → documentacion_deportistas (2); documentacion_deportistas → sobre_pruebas_caidas_todas_l (2); sobre_pruebas_caidas_todas_l → sobre_pruebas_caidas (2); grupos → individual_deportistas (1); participacion → sobre_pruebas_caidas_todas_l (1)

**C4**: sobre_pruebas_caidas_todas_l → sobre_pruebas_caidas (3); individual_deportistas → promocion_deportistas (2); grupos → individual_deportistas (1); promocion_deportistas → sobre_resumen_pruebas_caidas (1); instituciones → grupos (1); promocion_deportistas → sobre_resumen_del_tablero_co (1)

Consultas fallidas (primeras 15):

| id | consulta | objetivo | C2: top1 (rango obj.) | C4: top1 (rango obj.) |
|---|---|---|---|---|
| r005 | grupo del deportista Camilo Duarte por categoría, por etapa, | grupos | individual_deportistas (3) | individual_deportistas (2) |
| r008 | intención de participación de Andrés Torres por categoría, p | participacion | sobre_pruebas_caidas_todas_l (2) | participacion (1) |
| r009 | reporte individual del deportista María Restrepo por categor | individual_deportistas | sobre_resumen_pruebas_caidas (3) | individual_deportistas (1) |
| r011 | documentación del deportista Valentina Ríos por categoría, p | documentacion_deportistas | individual_deportistas (3) | documentacion_deportistas (1) |
| r016 | reporte individual del deportista Andrés Torres por categorí | individual_deportistas | sobre_pruebas_caidas_todas_l (4) | promocion_deportistas (2) |
| r018 | reporte individual del deportista Julián Gómez por categoría | individual_deportistas | documentacion_deportistas (2) | promocion_deportistas (2) |
| r023 | documentación del deportista Andrés Torres por categoría, po | documentacion_deportistas | sobre_pruebas_caidas_todas_l (2) | documentacion_deportistas (1) |
| r026 | reporte individual del deportista Camilo Duarte por discipli | individual_deportistas | documentacion_deportistas (2) | individual_deportistas (1) |
| r030 | reporte individual del deportista María Restrepo por grupo,  | individual_deportistas | personal_apoyo (2) | individual_deportistas (1) |
| r042 | documentación de deportistas de la institución Liga Atlántic | documentacion_deportistas | individual_deportistas (2) | documentacion_deportistas (1) |
| r045 | documentación del deportista Laura Ospina por categoría, por | documentacion_deportistas | sobre_pruebas_caidas_todas_l (3) | documentacion_deportistas (1) |
| r064 | reporte del sistema | promocion_deportistas | sobre_resumen_pruebas_caidas (16) | sobre_resumen_pruebas_caidas (17) |
| r073 | pruebas de caídas | sobre_pruebas_caidas_todas_l | sobre_pruebas_caidas (2) | sobre_pruebas_caidas (3) |
| r077 | instituciones de un evento | instituciones | instituciones (1) | grupos (4) |
| r104 | pruebas de caídas por categoría | sobre_pruebas_caidas_todas_l | sobre_pruebas_caidas_todas_l (1) | sobre_pruebas_caidas (2) |

## dificil: confusiones más frecuentes

**C1**: sobre_metricas_por_federacio → instituciones (3); grupos → instituciones (2); participacion → instituciones (2); delegaciones_participacion → grupos (2); individual_deportistas → delegaciones_participacion (1); individual_deportistas → participacion (1)

**C2**: sobre_metricas_por_federacio → instituciones (3); grupos → instituciones (2); participacion → instituciones (2); sobre_resumen_del_tablero_co → progreso_y_cumplimiento_meta (2); delegaciones_participacion → grupos (2); sobre_resumen_del_tablero_co → sobre_resumen_pruebas_caidas (1)

**C4**: sobre_metricas_por_federacio → individual_deportistas (3); delegaciones_participacion → grupos (2); individual_deportistas → sobre_distribucion_usuarios (1); individual_deportistas → personal_apoyo (1); grupos → instituciones (1); documentacion_deportistas → participacion (1)

Consultas fallidas (primeras 15):

| id | consulta | objetivo | C2: top1 (rango obj.) | C4: top1 (rango obj.) |
|---|---|---|---|---|
| d003 | relación completa de inscritos con sus datos básicos | individual_deportistas | individual_deportistas (1) | sobre_distribucion_usuarios (8) |
| d004 | ficha con la información de cada muchacho que juega | individual_deportistas | individual_deportistas (1) | personal_apoyo (2) |
| d005 | equipos de cada colegio por deporte | grupos | instituciones (2) | grupos (1) |
| d007 | cómo están conformados los conjuntos que representan a cada  | grupos | instituciones (2) | instituciones (2) |
| d015 | papeles que faltan por subir de cada participante | documentacion_deportistas | documentacion_deportistas (1) | participacion (3) |
| d017 | inscripción de la institución en la competencia | participacion | instituciones (2) | participacion (1) |
| d020 | colegios que ya confirmaron que van a competir | participacion | instituciones (4) | grupos (3) |
| d021 | estado global de la competencia por zona | sobre_resumen_del_tablero_co | progreso_y_cumplimiento_meta (3) | sobre_resumen_del_tablero_co (1) |
| d022 | panorama de cómo va todo | sobre_resumen_del_tablero_co | sobre_resumen_pruebas_caidas (4) | sobre_pruebas_caidas_todas_l (7) |
| d024 | indicadores generales del torneo por región | sobre_resumen_del_tablero_co | progreso_y_cumplimiento_meta (2) | sobre_resumen_del_tablero_co (1) |
| d026 | clasificación a la siguiente fase de un jugador | promocion_deportistas | promocion_deportistas (1) | documentacion_deportistas (2) |
| d027 | quién pasó a la etapa que sigue | promocion_deportistas | sobre_pruebas_caidas_todas_l (4) | sobre_pruebas_caidas_todas_l (3) |
| d028 | avance de los muchachos hacia la final | promocion_deportistas | grupos (5) | promocion_deportistas (1) |
| d031 | directorio de planteles participantes | instituciones | participacion (3) | participacion (10) |
| d032 | dónde queda cada centro y a qué ciudad pertenece | instituciones | instituciones (1) | grupos (2) |

## dificil_b: confusiones más frecuentes

**C1**: sobre_metricas_por_federacio → instituciones (3); grupos → instituciones (2); documentacion_deportistas → personal_apoyo (2); participacion → instituciones (2); participacion → cambios_en_la_intencion_part (2); sobre_resumen_del_tablero_co → sobre_resumen_pruebas_caidas (2)

**C2**: sobre_metricas_por_federacio → instituciones (3); individual_deportistas → participacion (2); grupos → instituciones (2); documentacion_deportistas → personal_apoyo (2); participacion → instituciones (2); participacion → cambios_en_la_intencion_part (2)

**C4**: personal_apoyo → grupos (2); participacion → instituciones (2); sobre_resumen_del_tablero_co → participacion (2); instituciones → grupos (2); individual_deportistas → documentacion_deportistas (1); individual_deportistas → personal_apoyo (1)

Consultas fallidas (primeras 15):

| id | consulta | objetivo | C2: top1 (rango obj.) | C4: top1 (rango obj.) |
|---|---|---|---|---|
| e001 | ¿quiénes están inscritos en natación categoría juvenil? | individual_deportistas | participacion (2) | individual_deportistas (1) |
| e002 | datos de contacto y documento de un jugador | individual_deportistas | documentacion_deportistas (2) | documentacion_deportistas (2) |
| e004 | necesito ubicar a una muchacha que compite en atletismo | individual_deportistas | individual_deportistas (1) | personal_apoyo (3) |
| e006 | lista de participantes por deporte y categoría | individual_deportistas | participacion (2) | participacion (2) |
| e007 | ¿qué equipos tiene registrados este colegio? | grupos | instituciones (2) | grupos (1) |
| e008 | conformación de la delegación por disciplina y fase | grupos | delegaciones_participacion (2) | participacion (2) |
| e011 | listado de agrupaciones deportivas por institución | grupos | instituciones (2) | instituciones (2) |
| e016 | relación de profesores que viajan con cada grupo | personal_apoyo | grupos (2) | grupos (3) |
| e018 | staff de apoyo por equipo y por torneo | personal_apoyo | personal_apoyo (1) | grupos (2) |
| e019 | ¿a quién le falta algún soporte por subir? | documentacion_deportistas | personal_apoyo (6) | promocion_deportistas (2) |
| e021 | estado de los certificados de los participantes | documentacion_deportistas | participacion (4) | participacion (3) |
| e024 | seguimiento de la entrega de soportes por jugador | documentacion_deportistas | personal_apoyo (3) | documentacion_deportistas (1) |
| e026 | instituciones inscritas para competir este año | participacion | instituciones (2) | instituciones (3) |
| e027 | quién manifestó interés en participar | participacion | cambios_en_la_intencion_part (2) | participacion (1) |
| e029 | relación de planteles que van a asistir | participacion | instituciones (2) | instituciones (2) |
