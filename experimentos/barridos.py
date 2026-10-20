#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Barridos de sensibilidad y eficiencia sobre la escalera de ablación (P4, P6 y robustez).

Corre con el encoder real de config.yaml (jina-embeddings-v3 con las tareas de recuperación
activas) sobre DOS conjuntos de evaluación y el corpus v1:
  * sintetico : datos/consultas_eval.jsonl      (40 consultas con juicio)
  * ampliado  : datos/consultas_real_ampliado.jsonl (127 consultas, patrones distintos)

Barridos:
  1. SENSIBILIDAD de hiperparámetros que se fijaron en valores estándar sin ajustar:
       k de RRF  in {1, 10, 30, 60, 100, 200}   (C3 y C4)
       lambda    in {0, .05, .1, .2, .3, .5}    (C5)
       k1 x b    in {.9,1.2,1.5,2.0} x {.5,.75,.9}  (BM25 solo y C4)
     Objetivo: mostrar si las conclusiones dependen de la elección (no se re-ajusta nada).
  2. P6  - dimensión Matryoshka m in dims (C1 y C4): efectividad, retención, ahorro de índice,
     latencia de búsqueda y de codificación, y equivalencia con m = dim nativa (H6, eps = 0,01).
  3. P4  - fragmentación (tamaño x solapamiento, agregación por máximo) sobre C4.

Los vectores se calculan UNA vez por texto y se truncan/reutilizan (el barrido de m no vuelve
a invocar al modelo). La latencia de codificación se mide aparte, sin caché.

Uso:  python3 barridos.py            -> resultados/barridos.json y resultados/barridos.md
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import yaml

from lib import metrics as M
from lib.encoders import construir_encoder
from lib.indexes import BM25Index, DenseIndex
from lib.retrievers import MotorRecuperacion, rrf
from lib.stats import bootstrap_dif_pareada, permutacion_pareada

RAIZ = Path(__file__).resolve().parent
EPS_EQUIV = 0.01          # margen de equivalencia práctico de H6 (fijado antes de ver resultados)


def cargar(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


class EncoderCacheado:
    """Envuelve un encoder real: calcula el vector completo una vez por texto y devuelve
    versiones truncadas a `m` (Matryoshka) renormalizadas."""

    def __init__(self, base, m: int | None = None, cache: dict | None = None) -> None:
        self.base = base
        self.m = m
        self.dim = m or base.dim
        self.nombre = f"{base.nombre}-m{self.dim}"
        self._cache = cache if cache is not None else {}

    def con_dim(self, m: int) -> "EncoderCacheado":
        return EncoderCacheado(self.base, m, self._cache)

    def _vecs(self, tipo: str, textos) -> np.ndarray:
        faltan = [t for t in dict.fromkeys(textos) if (tipo, t) not in self._cache]
        if faltan:
            f = (self.base.encode_consultas if tipo == "q" else self.base.encode_documentos)
            for t, v in zip(faltan, f(faltan)):
                self._cache[(tipo, t)] = v
        m = np.vstack([self._cache[(tipo, t)] for t in textos])
        if self.m:
            m = m[:, : self.m]
            n = np.linalg.norm(m, axis=1, keepdims=True)
            n[n == 0] = 1.0
            m = m / n
        return m

    def encode_consultas(self, textos):
        return self._vecs("q", list(textos))

    def encode_documentos(self, textos):
        return self._vecs("d", list(textos))

    def encode(self, textos):
        return self.encode_consultas(textos)


def evaluar(motor: MotorRecuperacion, config: int, consultas, qrels) -> list[float]:
    return [M.ndcg(motor.recuperar(config, c["texto"]), qrels[c["id"]], 10) for c in consultas]


def fragmentar(texto: str, tam: int, solapa: float) -> list[str]:
    palabras = texto.split()
    if tam >= len(palabras):
        return [texto]
    paso = max(1, int(round(tam * (1 - solapa))))
    trozos = [" ".join(palabras[i:i + tam]) for i in range(0, len(palabras), paso)
              if palabras[i:i + tam]]
    return trozos or [texto]


def main() -> None:
    cfg = yaml.safe_load((RAIZ / "config.yaml").read_text(encoding="utf-8"))
    if cfg["encoder"]["tipo"] != "sentence-transformer":
        raise SystemExit("barridos.py exige encoder.tipo: sentence-transformer (P4/P6 no tienen "
                         "sentido con el fallback LSA).")
    docs = cargar(RAIZ / cfg["rutas"]["corpus"])
    ontologia = yaml.safe_load((RAIZ / cfg["rutas"]["ontologia"]).read_text(encoding="utf-8"))
    base = construir_encoder(cfg, [])
    enc = EncoderCacheado(base)
    dim_nativa = base.dim
    k1, b = cfg["bm25"]["k1"], cfg["bm25"]["b"]
    k_rrf, lam = cfg["fusion"]["k_rrf"], cfg["realce"]["lambda"]

    conjuntos = {}
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--conjuntos", default="sintetico,ampliado")
    ap.add_argument("--sufijo", default="", help="sufijo del archivo de salida (p. ej. _dificiles)")
    args = ap.parse_args()
    DISP = {"sintetico": ("datos/consultas_eval.jsonl", "datos/qrels.jsonl"),
            "ampliado": ("datos/consultas_real_ampliado.jsonl", "datos/qrels_real_ampliado.jsonl"),
            "dificil": ("datos/consultas_dificil.jsonl", "datos/qrels_dificil.jsonl"),
            "dificil_b": ("datos/consultas_dificil_b.jsonl", "datos/qrels_dificil_b.jsonl"),
            "dificil_ab": ("datos/consultas_dificil_ab.jsonl", "datos/qrels_dificil_ab.jsonl")}
    for nombre, (cq, qr) in [(n, DISP[n]) for n in args.conjuntos.split(",")]:
        qrels = {r["id"]: r["relevancia"] for r in cargar(RAIZ / qr)}
        cons = [c for c in cargar(RAIZ / cq) if M.tiene_gold(qrels.get(c["id"], {}))]
        conjuntos[nombre] = (cons, qrels)

    def motor(e, k=k_rrf, lam_=lam, k1_=k1, b_=b):
        return MotorRecuperacion(docs, e, ontologia, k1_, b_, k, lam_)

    out: dict = {"encoder": base.nombre, "dim_nativa": dim_nativa, "n_docs": len(docs),
                 "tareas": {"consulta": cfg["encoder"].get("tarea_consulta"),
                            "documento": cfg["encoder"].get("tarea_documento")},
                 "n_consultas": {n: len(c) for n, (c, _) in conjuntos.items()}}

    # ------------------------------------------------------------------ 1. sensibilidad
    sens: dict = {}
    for cn, (cons, qrels) in conjuntos.items():
        s: dict = {"k_rrf": {}, "lambda": {}, "bm25_k1_b": {}}
        ref3 = evaluar(motor(enc), 3, cons, qrels)
        ref4 = evaluar(motor(enc), 4, cons, qrels)
        for k in [1, 10, 30, 60, 100, 200]:
            m = motor(enc, k=k)
            x3, x4 = evaluar(m, 3, cons, qrels), evaluar(m, 4, cons, qrels)
            s["k_rrf"][str(k)] = {"C3": float(np.mean(x3)), "C4": float(np.mean(x4)),
                                  "C4_consultas_distintas_vs_k60":
                                      int(np.sum(~np.isclose(x4, ref4))),
                                  "C3_consultas_distintas_vs_k60":
                                      int(np.sum(~np.isclose(x3, ref3)))}
        for lv in [0.0, 0.05, 0.1, 0.2, 0.3, 0.5]:
            m = motor(enc, lam_=lv)
            x5 = evaluar(m, 5, cons, qrels)
            d = np.array(x5) - np.array(ref4)
            s["lambda"][str(lv)] = {"C5": float(np.mean(x5)), "delta_vs_C4": float(d.mean()),
                                    "consultas_peor": int((d < -1e-9).sum()),
                                    "consultas_mejor": int((d > 1e-9).sum())}
        for k1v in [0.9, 1.2, 1.5, 2.0]:
            for bv in [0.5, 0.75, 0.9]:
                m = motor(enc, k1_=k1v, b_=bv)
                s["bm25_k1_b"][f"{k1v}|{bv}"] = {
                    "BM25": float(np.mean(evaluar(m, 0, cons, qrels))),
                    "C4": float(np.mean(evaluar(m, 4, cons, qrels)))}
        sens[cn] = s
        print(f"[sensibilidad:{cn}] listo")
    out["sensibilidad"] = sens

    # ------------------------------------------------------------------ 2. P6: Matryoshka
    dims = sorted({d for d in cfg["matryoshka"]["dims"] if 0 < d <= dim_nativa} | {dim_nativa})
    p6: dict = {}
    for cn, (cons, qrels) in conjuntos.items():
        filas = {}
        base_c1 = base_c4 = None
        series = {}
        for m_ in sorted(dims, reverse=True):          # primero la dimensión nativa
            e = enc.con_dim(m_)
            mot = motor(e)
            x1, x4 = evaluar(mot, 1, cons, qrels), evaluar(mot, 4, cons, qrels)
            series[m_] = (x1, x4)
            # latencia de BÚSQUEDA con vectores ya calculados (producto matriz-vector + fusión)
            tiempos = []
            for c in cons[:40]:
                t0 = time.perf_counter()
                mot.recuperar(4, c["texto"])
                tiempos.append((time.perf_counter() - t0) * 1000)
            filas[str(m_)] = {"C1": float(np.mean(x1)), "C4": float(np.mean(x4)),
                              "indice_KiB": len(docs) * m_ * 4 / 1024,
                              "lat_busqueda_p50_ms": float(np.percentile(tiempos, 50))}
        x1n, x4n = series[dim_nativa]
        for m_ in dims:
            x1, x4 = series[m_]
            ic = bootstrap_dif_pareada(x4, x4n, 1000, semilla=cfg["evaluacion"]["semilla"])
            perm = permutacion_pareada(x4, x4n, semilla=cfg["evaluacion"]["semilla"])
            f = filas[str(m_)]
            f["retencion_C4"] = f["C4"] / filas[str(dim_nativa)]["C4"]
            f["retencion_C1"] = f["C1"] / filas[str(dim_nativa)]["C1"]
            f["ahorro_indice"] = 1 - f["indice_KiB"] / filas[str(dim_nativa)]["indice_KiB"]
            f["dif_C4_vs_nativa"] = float(np.mean(np.array(x4) - np.array(x4n)))
            f["ic95_dif"] = [ic["ic_bajo"], ic["ic_alto"]]
            f["p_permutacion"] = perm["p_valor"]
            # H6: la pérdida no excede eps  <=>  límite inferior del IC95 > -eps
            f["equivalente_eps"] = bool(ic["ic_bajo"] is not None and ic["ic_bajo"] > -EPS_EQUIV)
        p6[cn] = filas
        print(f"[P6:{cn}] listo")
    out["P6"] = {"eps_equivalencia": EPS_EQUIV, "dims": dims, "por_conjunto": p6}

    # latencia de CODIFICACIÓN de la consulta (sin caché; es la que domina en producción)
    cons_s = next(iter(conjuntos.values()))[0]
    muestra = [c["texto"] for c in cons_s[:30]]
    t_enc = []
    for t in muestra:
        t0 = time.perf_counter()
        base.encode_consultas([t])
        t_enc.append((time.perf_counter() - t0) * 1000)
    out["lat_codificacion_consulta_ms"] = {"p50": float(np.percentile(t_enc, 50)),
                                           "p95": float(np.percentile(t_enc, 95)),
                                           "n": len(t_enc)}

    # ------------------------------------------------------------------ 3. P4: fragmentación
    tams = [24, 40, 64, 128, 10 ** 6]
    solapes = [0.0, 0.25, 0.5]
    longitudes = [len(d["texto_indexable"].split()) for d in docs]
    p4: dict = {"longitud_palabras": {"min": min(longitudes), "max": max(longitudes),
                                       "media": float(np.mean(longitudes))}, "por_conjunto": {}}
    for cn, (cons, qrels) in conjuntos.items():
        tabla = {}
        ref = None
        for tam in tams:
            for so in solapes:
                ids, doc_de, txt = [], {}, []
                for d in docs:
                    for j, ch in enumerate(fragmentar(d["texto_indexable"], tam, so)):
                        fid = f"{d['id']}#{j}"
                        ids.append(fid); doc_de[fid] = d["id"]; txt.append(ch)
                bm = BM25Index(k1, b).indexar(ids, txt)
                dn = DenseIndex(enc).indexar(ids, txt)
                nds = []
                for c in cons:
                    _, fus = rrf(bm.buscar(c["texto"]), dn.buscar(c["texto"]), k_rrf)
                    ds: dict = {}
                    for fid, sc in fus.items():
                        ds[doc_de[fid]] = max(ds.get(doc_de[fid], -1.0), sc)
                    rank = sorted(ds, key=lambda x: (-ds[x], x))
                    nds.append(M.ndcg(rank, qrels[c["id"]], 10))
                clave = f"{'doc' if tam >= 10 ** 6 else tam}|{so}"
                tabla[clave] = {"nDCG@10": float(np.mean(nds)), "frag_por_doc": len(ids) / len(docs)}
                if tam >= 10 ** 6 and so == 0.0:
                    ref = nds
        for clave, v in tabla.items():
            v["delta_vs_doc_completo"] = v["nDCG@10"] - float(np.mean(ref))
        p4["por_conjunto"][cn] = tabla
        print(f"[P4:{cn}] listo")
    out["P4"] = p4

    ruta = RAIZ / "resultados" / f"barridos{args.sufijo}.json"
    ruta.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (RAIZ / "resultados" / f"barridos{args.sufijo}.md").write_text(a_markdown(out), encoding="utf-8")
    print(f"Guardado en {ruta}")


def a_markdown(o: dict) -> str:
    L = [f"# Barridos de sensibilidad y eficiencia", "",
         f"Encoder: `{o['encoder']}` (dim nativa {o['dim_nativa']}); tareas: {o['tareas']}. "
         f"Corpus: {o['n_docs']} documentos. Consultas con juicio: {o['n_consultas']}.", ""]
    for cn in o["sensibilidad"]:
        s = o["sensibilidad"][cn]
        L += [f"## Sensibilidad — conjunto {cn}", "", "### k de RRF (nDCG@10)", "",
              "| k | C3 | C4 | consultas que cambian (C3 / C4) vs k=60 |", "|---|---|---|---|"]
        for k, v in s["k_rrf"].items():
            L.append(f"| {k} | {v['C3']:.3f} | {v['C4']:.3f} | "
                     f"{v['C3_consultas_distintas_vs_k60']} / {v['C4_consultas_distintas_vs_k60']} |")
        L += ["", "### λ del realce (C5)", "",
              "| λ | C5 | Δ vs C4 | consultas peor / mejor |", "|---|---|---|---|"]
        for lv, v in s["lambda"].items():
            L.append(f"| {lv} | {v['C5']:.3f} | {v['delta_vs_C4']:+.3f} | "
                     f"{v['consultas_peor']} / {v['consultas_mejor']} |")
        L += ["", "### BM25 k1 × b (nDCG@10)", "", "| k1 \\ b | 0.5 | 0.75 | 0.9 |", "|---|---|---|---|"]
        for k1v in [0.9, 1.2, 1.5, 2.0]:
            celdas = " | ".join(
                f"{s['bm25_k1_b'][f'{k1v}|{bv}']['BM25']:.3f} / {s['bm25_k1_b'][f'{k1v}|{bv}']['C4']:.3f}"
                for bv in [0.5, 0.75, 0.9])
            L.append(f"| {k1v} | {celdas} |")
        L += ["", "*Cada celda: BM25 solo / C4.*", ""]
    L += ["## P6 — dimensión Matryoshka", "",
          f"Margen de equivalencia ε = {o['P6']['eps_equivalencia']} (IC95 de la diferencia con la dim. nativa).",
          f"Latencia de codificación de la consulta (sin caché): p50 {o['lat_codificacion_consulta_ms']['p50']:.0f} ms, "
          f"p95 {o['lat_codificacion_consulta_ms']['p95']:.0f} ms.", ""]
    for cn, filas in o["P6"]["por_conjunto"].items():
        L += [f"### Conjunto {cn}", "",
              "| m | C1 | C4 | retención C4 | Δ C4 vs nativa [IC95] | p perm. | equiv. | ahorro índice | búsqueda p50 (ms) |",
              "|---|---|---|---|---|---|---|---|---|"]
        for m_, f in sorted(filas.items(), key=lambda kv: int(kv[0])):
            L.append(f"| {m_} | {f['C1']:.3f} | {f['C4']:.3f} | {f['retencion_C4']:.3f} | "
                     f"{f['dif_C4_vs_nativa']:+.3f} [{f['ic95_dif'][0]:+.3f}, {f['ic95_dif'][1]:+.3f}] | "
                     f"{'n/d' if f['p_permutacion'] is None else format(f['p_permutacion'], '.3f')} | "
                     f"{'sí' if f['equivalente_eps'] else 'no'} | {100*f['ahorro_indice']:.1f}% | "
                     f"{f['lat_busqueda_p50_ms']:.1f} |")
        L.append("")
    p4 = o["P4"]
    L += ["## P4 — fragmentación", "",
          f"Longitud de los documentos (palabras): min {p4['longitud_palabras']['min']}, "
          f"máx {p4['longitud_palabras']['max']}, media {p4['longitud_palabras']['media']:.0f}.", ""]
    for cn, tabla in p4["por_conjunto"].items():
        L += [f"### Conjunto {cn} (nDCG@10 de C4; Δ frente al documento completo)", "",
              "| tamaño | solapa 0 | solapa 25 % | solapa 50 % | frag/doc (0 %) |", "|---|---|---|---|---|"]
        for tam in ["24", "40", "64", "128", "doc"]:
            c = [tabla[f"{tam}|{so}"] for so in (0.0, 0.25, 0.5)]
            L.append(f"| {tam} | " + " | ".join(
                f"{x['nDCG@10']:.3f} ({x['delta_vs_doc_completo']:+.3f})" for x in c)
                + f" | {c[0]['frag_por_doc']:.2f} |")
        L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
