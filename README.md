# Buscador Semántico GovTech

Proyecto de grado · Pregrado en Ciencia de Datos · Universidad del Norte
**Autor:** Luis David Peñaranda · **Asesor:** Carlos de Oro

📖 **Libro publicado:** https://luispenaranda08.github.io/semantic_search_engine/

Diseño y evaluación de un buscador semántico en español para una plataforma GovTech de
gestión deportiva: recuperación híbrida (BM25 + `jina-embeddings-v3`), inyección de una
ontología del dominio, fusión por rango (RRF) y una escalera de ablación de cinco
configuraciones, con validez externa a partir del historial real de consultas.

## Contenido

- `intro.md`: introducción del libro.
- `notebooks/`: análisis exploratorio, ontología y todos los benchmarks, con sus salidas ya
  ejecutadas.
- `guia_estudio.md`: guía de estudio con el significado de cada métrica.
- `images/`: portada (generada con `_scripts/portada.py`) y diagramas de la ontología.

Todos los nombres propios de las consultas de ejemplo son sintéticos. El repositorio no
contiene datos personales ni datos crudos de la plataforma.

## Construir el libro localmente

```bash
python3 -m venv .venv-book
.venv-book/bin/pip install "jupyter-book<2" sphinxcontrib-mermaid ghp-import
.venv-book/bin/jupyter-book build .
```

El HTML queda en `_build/html/`. Para publicar en GitHub Pages:

```bash
.venv-book/bin/ghp-import -n -p -f _build/html
```
