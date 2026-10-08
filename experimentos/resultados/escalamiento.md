# Escalamiento de la búsqueda exacta

Equipo: Apple M4 · macOS-15.7.3-arm64-arm-64bit-Mach-O. Vectores aleatorios; no mide calidad ni la codificación de la consulta (≈ 349 ms).

| N | m=64: MiB / p50 ms | m=256: MiB / p50 ms | m=1024: MiB / p50 ms |
|---|---|---|---|
| 1,000 | 0.2 / 0.02 | 1.0 / 0.02 | 3.9 / 0.03 |
| 10,000 | 2.4 / 0.11 | 9.8 / 0.14 | 39.1 / 0.98 |
| 100,000 | 24.4 / 1.46 | 97.7 / 3.09 | 390.6 / 8.10 |
| 200,000 | 48.8 / 2.98 | 195.3 / 6.63 | 781.2 / 17.73 |
