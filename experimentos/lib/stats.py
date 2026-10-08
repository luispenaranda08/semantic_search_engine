#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Análisis estadístico de la comparación entre configuraciones.

Prueba de Wilcoxon pareada, prueba de permutación pareada (aleatorización de signos; control
de robustez, porque Smucker, Allan y Carterette 2007 muestran que Wilcoxon puede discrepar de
t/bootstrap/permutación en evaluación de IR), tamaño de efecto PAREADO (correlación
rank-biserial de pares emparejados), intervalo bootstrap pareado de la diferencia media,
número de pares no nulos (el poder efectivo real) y corrección de Holm por comparaciones
múltiples.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy import stats as sp_stats


def wilcoxon_pareado(a: Sequence[float], b: Sequence[float]) -> dict:
    """Wilcoxon pareado de dos vectores de métricas por consulta (a vs b).

    Devuelve el estadístico, el p-valor y la media de la diferencia (a - b). Si
    todas las diferencias son cero, el test no está definido y se reporta así.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    dif = a - b
    if np.allclose(dif, 0):
        return {"estadistico": None, "p_valor": None, "media_dif": 0.0,
                "n": int(len(a)), "nota": "todas las diferencias son cero"}
    try:
        est, p = sp_stats.wilcoxon(a, b, zero_method="wilcox")
    except ValueError as e:
        return {"estadistico": None, "p_valor": None, "media_dif": float(dif.mean()),
                "n": int(len(a)), "nota": str(e)}
    return {"estadistico": float(est), "p_valor": float(p),
            "media_dif": float(dif.mean()), "n": int(len(a))}


def bootstrap_ic(valores: Sequence[float], n_muestras: int = 1000,
                 alpha: float = 0.05, semilla: int = 42) -> dict:
    """Intervalo de confianza por bootstrap percentil para la media de `valores`."""
    v = np.asarray(valores, dtype=float)
    if len(v) == 0:
        return {"media": None, "ic_bajo": None, "ic_alto": None, "n": 0}
    rng = np.random.default_rng(semilla)
    medias = np.array([rng.choice(v, size=len(v), replace=True).mean()
                       for _ in range(n_muestras)])
    return {
        "media": float(v.mean()),
        "ic_bajo": float(np.percentile(medias, 100 * alpha / 2)),
        "ic_alto": float(np.percentile(medias, 100 * (1 - alpha / 2))),
        "n": int(len(v)),
    }


def permutacion_pareada(a: Sequence[float], b: Sequence[float], n_perm: int = 20000,
                        semilla: int = 42, max_exacto: int = 20) -> dict:
    """Prueba de permutación pareada (aleatorización de signos), bilateral.

    Estadístico: media de d = a - b. Bajo H0 cada diferencia es simétrica alrededor de 0, así
    que se permutan sus signos. Los ceros no aportan (no cambian la media al voltear su signo)
    y se excluyen del conteo de combinaciones. Si hay <= `max_exacto` diferencias no nulas se
    enumeran las 2^n asignaciones de signo (p-valor EXACTO); si no, se usan `n_perm` sorteos
    Monte Carlo con la corrección (b+1)/(n+1) para no reportar p = 0.
    """
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    n_total = len(d)
    nz = d[~np.isclose(d, 0)]
    if len(nz) == 0:
        return {"p_valor": None, "metodo": "sin diferencias", "n_no_nulos": 0}
    obs = abs(nz.sum())          # suma (equivale a la media: el divisor n_total es constante)
    tol = 1e-12
    if len(nz) <= max_exacto:
        n_comb = 1 << len(nz)
        # signos como bits de 0..2^n-1; suma = 2*sum(|d| donde signo +) - sum|d|
        absd = np.abs(nz)
        total = absd.sum()
        idx = np.arange(n_comb, dtype=np.int64)
        sumas = np.zeros(n_comb)
        for j in range(len(nz)):
            sumas += ((idx >> j) & 1) * absd[j]
        sumas = 2 * sumas - total
        p = float((np.abs(sumas) >= obs - tol).sum() / n_comb)
        return {"p_valor": p, "metodo": "exacto", "n_no_nulos": int(len(nz)), "n_total": n_total}
    rng = np.random.default_rng(semilla)
    signos = rng.choice([-1.0, 1.0], size=(n_perm, len(nz)))
    sumas = np.abs(signos @ np.abs(nz))
    p = float(((sumas >= obs - tol).sum() + 1) / (n_perm + 1))
    return {"p_valor": p, "metodo": f"monte_carlo({n_perm})", "n_no_nulos": int(len(nz)),
            "n_total": n_total}


def rank_biserial_pareado(a: Sequence[float], b: Sequence[float]) -> float | None:
    """Tamaño de efecto de Wilcoxon (matched-pairs rank-biserial, Kerby 2014).

    r = (W+ - W-) / (W+ + W-), con W± la suma de rangos de |d| de las diferencias
    positivas/negativas (ceros excluidos). Rango [-1, 1]; signo = dirección de a - b.
    A diferencia de Cliff's delta no pareado, es coherente con el test de Wilcoxon.
    """
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    d = d[~np.isclose(d, 0)]
    if len(d) == 0:
        return None
    r = sp_stats.rankdata(np.abs(d))
    wp, wn = r[d > 0].sum(), r[d < 0].sum()
    return float((wp - wn) / (wp + wn))


def bootstrap_dif_pareada(a: Sequence[float], b: Sequence[float], n_muestras: int = 1000,
                          alpha: float = 0.05, semilla: int = 42) -> dict:
    """IC bootstrap percentil de la media de (a - b), remuestreando consultas (pareado)."""
    return bootstrap_ic(np.asarray(a, float) - np.asarray(b, float), n_muestras, alpha, semilla)


def holm(p_valores: dict[str, float | None]) -> dict[str, float | None]:
    """Corrección de Holm-Bonferroni (FWER) sobre una familia de p-valores."""
    validos = sorted(((p, k) for k, p in p_valores.items() if p is not None))
    m, ajust, acumulado = len(validos), {}, 0.0
    for i, (p, k) in enumerate(validos):
        acumulado = max(acumulado, min(1.0, (m - i) * p))
        ajust[k] = acumulado
    return {k: ajust.get(k) for k in p_valores}


def comparar(a: Sequence[float], b: Sequence[float], n_boot: int = 1000,
             semilla: int = 42) -> dict:
    """Comparación pareada completa de a vs b (mismas consultas, mismo orden)."""
    w = wilcoxon_pareado(a, b)
    d = np.asarray(a, float) - np.asarray(b, float)
    w["n_pares_no_nulos"] = int((~np.isclose(d, 0)).sum())
    w["rank_biserial"] = rank_biserial_pareado(a, b)
    perm = permutacion_pareada(a, b, semilla=semilla)
    w["p_permutacion"] = perm["p_valor"]
    w["metodo_permutacion"] = perm["metodo"]
    ic = bootstrap_dif_pareada(a, b, n_boot, semilla=semilla)
    w["ic95_dif"] = [ic["ic_bajo"], ic["ic_alto"]]
    return w


# Familia de comparaciones de la escalera: (etiqueta, config_a, config_b). a - b > 0 = a mejor.
FAMILIA = [
    ("C3_vs_BM25 (P1)", 3, 0),
    ("C3_vs_C1 (P1,P2)", 3, 1),
    ("C2_vs_C1 (P3 denso)", 2, 1),
    ("C4_vs_C3 (P3 híbrido)", 4, 3),
    ("C5_vs_C4 (P5)", 5, 4),
]


def familia_comparaciones(serie, ids: list[str], nombres: dict[int, str],
                          n_boot: int = 1000, semilla: int = 42) -> dict:
    """Corre FAMILIA sobre `ids` y añade el p-valor ajustado por Holm a cada comparación.

    `serie(nombre_config, ids)` devuelve la métrica por consulta en el orden de `ids`.
    """
    res = {et: comparar(serie(nombres[a], ids), serie(nombres[b], ids), n_boot, semilla)
           for et, a, b in FAMILIA}
    for et, p in holm({et: r["p_valor"] for et, r in res.items()}).items():
        res[et]["p_holm"] = p
    for et, p in holm({et: r["p_permutacion"] for et, r in res.items()}).items():
        res[et]["p_holm_permutacion"] = p
    for r in res.values():
        # "Robusto": Wilcoxon y permutación coinciden en rechazar tras Holm (alfa = 0,05).
        r["robusto"] = bool(r.get("p_holm") is not None and r.get("p_holm_permutacion") is not None
                            and r["p_holm"] < 0.05 and r["p_holm_permutacion"] < 0.05)
    return res


if __name__ == "__main__":
    print("holm:", holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": None}))
    print("rank-biserial:", rank_biserial_pareado([1, 2, 3, 4], [0, 1, 3, 5]))
    a = [0.9, 0.8, 0.7, 0.95, 0.6]
    b = [0.6, 0.5, 0.4, 0.55, 0.3]
    print("wilcoxon:", wilcoxon_pareado(a, b))
    print("bootstrap:", bootstrap_ic(a))
    # Permutación: caso exacto verificable a mano. d = (+1,+1,+1) -> 8 asignaciones de signo,
    # solo +++ y --- alcanzan |suma| = 3 -> p = 2/8 = 0,25.
    r = permutacion_pareada([1, 1, 1], [0, 0, 0])
    assert r["metodo"] == "exacto" and abs(r["p_valor"] - 0.25) < 1e-12, r
    # Ceros se ignoran y diferencias simétricas no rechazan H0 (suma = 0 -> p = 1).
    r = permutacion_pareada([1, 0, 5, 3], [0, 0, 4, 4])
    assert abs(r["p_valor"] - 1.0) < 1e-12, r
    # Concuerda con scipy.stats.permutation_test (exacto) en un caso con 8 diferencias.
    x = [0.9, 0.8, 0.7, 0.95, 0.6, 0.5, 0.85, 0.4]
    y = [0.6, 0.5, 0.4, 0.55, 0.3, 0.45, 0.2, 0.1]
    mine = permutacion_pareada(x, y)["p_valor"]
    ref = sp_stats.permutation_test((np.array(x) - np.array(y),),
                                    lambda d: d.mean(), permutation_type="samples",
                                    vectorized=False, n_resamples=10**6).pvalue
    assert abs(mine - ref) < 1e-9, (mine, ref)
    print("permutación pareada:", permutacion_pareada(a, b))
    print("stats.py: OK")
