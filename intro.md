# Buscadores semánticos para la recuperación de conocimiento funcional en plataformas GovTech

**Autor:** Luis David Peñaranda · **Asesor:** [Carlos De Oro Aguado](https://www.linkedin.com/in/cdeoroaguado/)

**Proyecto de grado · Pregrado en Ciencia de Datos · Universidad del Norte · 2026**

```{image} images/portada.png
:alt: Buscador semántico GovTech
:width: 100%
```

Este sitio acompaña la monografía de grado y reúne el código, los conjuntos de evaluación y los
resultados que producen sus cifras. La versión exacta que corresponde a la monografía es la
etiqueta [`v1.0-tesis`](https://github.com/luispenaranda08/semantic_search_engine/tree/v1.0-tesis)
del repositorio.

{download}`Descargar la monografía (PDF) <monografia/monografia_buscador_semantico.pdf>`

## El problema

Las plataformas con las que el sector público gestiona sus programas acumulan reportes, roles,
permisos y reglas que sus usuarios no saben dónde encontrar. El caso de estudio es una
plataforma pública colombiana de gestión deportiva. Allí el usuario navega menús, y las únicas
cajas de texto son filtros de lista que no guardan lo que se escribe, así que no existe una sola
consulta humana escrita ni un par consulta–reporte etiquetado. El trabajo construye y evalúa un
buscador semántico en español en esas condiciones, y deriva las consultas y sus juicios de
relevancia de la estructura del propio sistema.

## Lo que se encontró

- La demanda real está muy concentrada: de $6.620$ solicitudes reales de datos en seis semanas y
  media, cinco de diecisiete reportes reúnen el $83\%$ (Gini de $0{,}70$).
- Casi toda la ventaja sobre BM25 la aporta el codificador denso preentrenado. La fusión por
  rango (RRF) no supera al denso y lo perjudica cuando la consulta no comparte vocabulario con
  el documento.
- Con $811$ documentos de cinco tipos, una combinación convexa de puntuaciones
  ($0{,}8\cdot$denso $+ 0{,}2\cdot$BM25) supera a RRF y al denso de forma concordante
  ($0{,}799$ frente a $0{,}710$ y $0{,}714$ de nDCG@10).
- La ontología del dominio mejora la recuperación en proporción a los términos que la consulta
  comparte con ella. Sobre $757.554$ documentos, todos con vector denso, supera a la descripción
  original y a tres controles de la misma longitud.
- Para buscar personas hace falta resolver entidades. Entre $643.107$ deportistas, un
  diccionario de entidades acierta en primer lugar el $97{,}7\%$ de las veces con un error de
  digitación, frente al $57{,}3\%$ del ranking híbrido sin él.
- El realce por entidad no mejora el orden en ningún conjunto y se descarta.

## Cómo está organizado

La primera parte resume la monografía, su método y sus resultados, y explica cómo reproducir
cada cifra con el código. La segunda recorre en detalle cada etapa y cada corpus: la demanda
observada, los diecisiete reportes, el corpus de $177$ documentos, el corpus v3 de $811$, el
registro completo de la plataforma y los controles de validez. La tercera guarda los notebooks de las primeras etapas con sus salidas
originales; muchas de sus cifras son anteriores a la auditoría del 30 de septiembre de 2026 y la
monografía ya no las usa, pero se conservan como registro del proceso.

Todos los nombres propios de las consultas de evaluación son sintéticos, y ningún dato personal
forma parte del repositorio ni de este sitio.
