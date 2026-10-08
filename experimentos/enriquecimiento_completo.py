#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""¿Qué pasa si la ontología cubre (casi) todos los reportes? Prueba de la hipótesis «todo o nada».

Hallazgo previo (exploratorio): solo 9 de 17 reportes tienen bloque de ontología y los no
enriquecidos pierden con el híbrido (−0,161 en el conjunto difícil A). Aquí se enriquecen
también los reportes restantes de forma MECÁNICA, sin redactar texto libre ni mirar las consultas:

  entidades(reporte) = clases de la ontología cuyas propiedades de datos aparecen entre las columnas
                       y palabras clave de las firmas reales de ese reporte (suid_query_signatures.csv),
                       descartando «Promoción» salvo que la firma use el registro de promociones
                       (regla de lib/etiquetado.py; evita el falso positivo de la columna `status`).
  texto = «Entidades: …» + «También llamado: …» (sinónimos de la ontología), con el mismo
          serializador que el corpus original, SIN el bloque «Responde a» (que es texto de negocio
          redactado a mano).

Un reporte cuyas columnas no se mapean a ninguna clase (distribución de usuarios: rol/tipo) queda sin
enriquecer: no se inventan entidades. Se comparan tres variantes del documento:
  desc     : solo la descripción (sin ontología)            -> C1 (denso) y C3 (híbrido)
  parcial  : ontología en 9 de 17 reportes (corpus actual)   -> C2 y C4 de la escalera
  completa : ontología en los 9 + los que se pueden mapear   -> C2' y C4'
en los cuatro conjuntos (sintético, ampliado, difícil A y B), y separando las consultas cuyo objetivo
era un reporte no enriquecido.

Uso: python3 enriquecimiento_completo.py -> resultados/enriquecimiento_completo.json y .md
"""
from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import fusion as F
from lib import metrics as M
from lib.banco import (CONJUNTOS, EncoderCacheado, Puntuaciones, cargar_conjunto, cargar_config, cargar_jsonl, ranking, RAIZ)
from lib.encoders import construir_encoder
from lib.etiquetado import es_promocion
from lib.stats import comparar, holm
from preprocess_corpus import serializar_metadatos, sinonimos_de, normalizar

# id de corpus (slug) -> nombre lógico en las firmas
FIRMA_DE = {
    "reporte_sobre_distribucion_de_usuarios": "Reporte sobre user_distribution",
    "reporte_sobre_metricas_por_federacion_deportiva": "Reporte sobre federation_sport_metrics",
    "reporte_sobre_pruebas_de_caidas_todas_las_etapas": "Reporte sobre pruebas_caidas_todas_etapas",
    "reporte_de_cambios_en_la_intencion_de_participacion": "Reporte sobre participation_intent_changes_report",
    "reporte_de_delegaciones_de_participacion": "Reporte sobre participation_intent_delegations_report",
    "reporte_sobre_pruebas_de_caidas": "Reporte sobre pruebas_caidas",
    "reporte_sobre_resumen_de_pruebas_de_caidas": "Reporte sobre pruebas_caidas_resumen",
    "reporte_sobre_resumen_de_pruebas_de_caidas_todas_las_etapas": "Reporte sobre pruebas_caidas_todas_etapas_resumen",
}


def entidades_desde_firmas(nombre_logico: str, firmas: list[dict], col2cls: dict) -> list[str]:
    cols: set[str] = set()
    tablas: set[str] = set()
    for s in firmas:
        if s["nombre_logico"] != nombre_logico:
            continue
        for k in ("columnas_clave", "keywords_where"):
            cols |= {c.strip() for c in s[k].split("|") if c.strip()}
        tablas |= {t.strip() for t in s["tablas"].split("|") if t.strip()}
    clases = set()
    for c in cols:
        clases |= col2cls.get(c, set())
    if "Promoción" in clases and not es_promocion(tablas, cols):
        clases.discard("Promoción")
    return sorted(clases)


def main() -> None:
    cfg = cargar_config()
    docs = cargar_jsonl(RAIZ / cfg["rutas"]["corpus"])
    onto = yaml.safe_load((RAIZ / cfg["rutas"]["ontologia"]).read_text(encoding="utf-8"))
    firmas = list(csv.DictReader((RAIZ.parent / "data/athena_suid/suid_query_signatures.csv").open(encoding="utf-8")))
    col2cls: dict[str, set] = collections.defaultdict(set)
    for c, b in onto["clases"].items():
        for p in b.get("propiedades_de_datos", []):
            col2cls[p["nombre"]].add(c)

    desc = {d["id"]: d["descripcion"] for d in docs}
    parcial = {d["id"]: d["texto_indexable"] for d in docs}
    completa, nuevos = dict(parcial), {}
    for d in docs:
        slug = d["id"].split("_", 2)[-1]
        if len(d["texto_indexable"]) > len(d["descripcion"]) or slug not in FIRMA_DE:
            continue
        ents = entidades_desde_firmas(FIRMA_DE[slug], firmas, col2cls)
        if not ents:
            nuevos[d["id"]] = {"entidades": [], "nota": "sin clase mapeable; queda sin enriquecer"}
            continue
        bloque = serializar_metadatos({"entidades_principales": ents, "conceptos_busqueda": [],
                                       "sinonimos": sinonimos_de(ents, onto)})
        completa[d["id"]] = normalizar(d["descripcion"] + " " + bloque)
        nuevos[d["id"]] = {"entidades": ents}
    enriquecidos = {"parcial": sum(parcial[i] != desc[i] for i in desc), "completa": sum(completa[i] != desc[i] for i in desc)}
    print("[ontologia completa]", enriquecidos, json.dumps(nuevos, ensure_ascii=False))

    enc = EncoderCacheado(construir_encoder(cfg, []))
    k1, b = cfg["bm25"]["k1"], cfg["bm25"]["b"]
    P = {n: Puntuaciones(t, enc, k1, b) for n, t in (("desc", desc), ("parcial", parcial), ("completa", completa))}
    ids = P["desc"].ids
    sin_bloque_antes = {i for i in desc if parcial[i] == desc[i]}
    res = {"enriquecidos": enriquecidos, "nuevos": nuevos, "conjuntos": {}}

    def serie(nom, tipo, cons, qr):
        Pn = P[nom]
        if tipo == "denso":
            fn = lambda q: Pn.puntaje_denso(q)
        else:
            fn = lambda q: F.rrf(Pn.puntaje_bm25(q), Pn.puntaje_denso(q), 60)
        return np.array([M.ndcg(ranking(fn(c["texto"]), ids), qr[c["id"]], 10) for c in cons])

    for cn in CONJUNTOS:
        cons, qr = cargar_conjunto(cn)
        tgt = {c["id"]: max(qr[c["id"]], key=qr[c["id"]].get) for c in cons}
        grupos = {"todas": [True] * len(cons),
                  "objetivo_sin_bloque_antes": [tgt[c["id"]] in sin_bloque_antes for c in cons],
                  "objetivo_con_bloque_antes": [tgt[c["id"]] not in sin_bloque_antes for c in cons]}
        S = {(nom, tipo): serie(nom, tipo, cons, qr) for nom in P for tipo in ("denso", "hibrido")}
        out = {"n": len(cons), "medias": {f"{nom}|{tipo}": float(v.mean()) for (nom, tipo), v in S.items()}, "comparaciones": {}}
        for g, mask in grupos.items():
            m = np.array(mask)
            if m.sum() == 0:
                continue
            comps = {}
            for tipo in ("denso", "hibrido"):
                for a, bb in (("completa", "parcial"), ("completa", "desc"), ("parcial", "desc")):
                    r = comparar(S[(a, tipo)][m], S[(bb, tipo)][m])
                    comps[f"{tipo}: {a} − {bb}"] = {"delta": r["media_dif"], "pares_no_nulos": r["n_pares_no_nulos"], "n": int(m.sum()),
                                                      "p_wilcoxon": r["p_valor"], "p_permutacion": r["p_permutacion"]}
            out["comparaciones"][g] = comps
        res["conjuntos"][cn] = out
        print(f"[ontologia completa] {cn} listo")
    (RAIZ / "resultados/enriquecimiento_completo.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    (RAIZ / "resultados/enriquecimiento_completo.md").write_text(a_md(res), encoding="utf-8")


def a_md(r: dict) -> str:
    fm = lambda x: "n/d" if x is None else f"{x:.4f}"
    L = ["# Ontología parcial (9/17) frente a completa", "",
         f"Reportes enriquecidos: parcial = {r['enriquecidos']['parcial']}, completa = {r['enriquecidos']['completa']} de 17.", "",
         "Entidades derivadas mecánicamente de las firmas reales:", ""]
    for k, v in r["nuevos"].items():
        L.append(f"- `{k}`: {', '.join(v['entidades']) or '—'} {v.get('nota', '')}")
    L += ["", "## nDCG@10 medio", "", "| Conjunto | n | denso desc | denso parcial | denso completa | híbrido desc | híbrido parcial | híbrido completa |", "|---|---|---|---|---|---|---|---|"]
    for cn, o in r["conjuntos"].items():
        m = o["medias"]
        L.append(f"| {cn} | {o['n']} | " + " | ".join(f"{m[f'{n}|{t}']:.3f}" for t in ('denso', 'hibrido') for n in ('desc', 'parcial', 'completa')) + " |")
    for cn, o in r["conjuntos"].items():
        L += ["", f"## {cn}", "", "| Grupo | Comparación | n | Δ | pares≠0 | p Wilcoxon | p permut. |", "|---|---|---|---|---|---|---|"]
        for g, comps in o["comparaciones"].items():
            for k, v in comps.items():
                L.append(f"| {g} | {k} | {v['n']} | {v['delta']:+.3f} | {v['pares_no_nulos']} | {fm(v['p_wilcoxon'])} | {fm(v['p_permutacion'])} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
