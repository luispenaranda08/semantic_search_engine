# Recomendación de configuración (P6)

Con el encoder `jina-embeddings-v3`, la configuración con mejor nDCG@10 global es **Híbrido + ontología** (0.948).

- Latencia p50 / p95: 344.3 / 398.5 ms.
- Índice denso: 17 documentos × 1024 dimensiones ≈ 68.0 KiB.

> Nota: el barrido de dimensión Matryoshka (P6) está en `notebooks/Benchmark_Matryoshka_P6.ipynb`; la matriz densa escala lineal con la dimensión, de modo que truncar reduce índice y memoria con la retención de nDCG@10 que ese notebook mide.
