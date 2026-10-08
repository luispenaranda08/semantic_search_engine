#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Efecto de la ontología según el documento OBJETIVO esté enriquecido o no (análisis EXPLORATORIO).

Hallazgo que lo motiva: solo 9 de los 17 documentos tienen bloque de ontología (los 8 restantes
cumplen d' = d_desc). Al enriquecer solo una parte del corpus, los documentos enriquecidos
(más largos, con más términos) compiten con ventaja frente a los no enriquecidos. Este script
separa las consultas por ese criterio y compara C2 vs C1 y C4 vs C3 en cada grupo, con Wilcoxon
y permutación pareadas. NO es una comparación de la familia confirmatoria (no lleva Holm): es un
análisis post-hoc que debe leerse como generador de hipótesis.

Entradas : resultados/resultados_dificil_v1.json, resultados/resultados_real_ampliado_v1.json
Salida   : resultados/cobertura_ontologia.json y .md
Uso      : python3 analisis_cobertura_ontologia.py
"""
from __future__ import annotations
import json
from pathlib import Path
from lib.stats import comparar

RAIZ = Path(__file__).resolve().parent
N = {"C1": "Denso puro", "C2": "Denso + ontología", "C3": "Híbrido (sin ontología)",
     "C4": "Híbrido + ontología"}
CONJUNTOS = {
    "dificil": ("resultados/resultados_dificil_v1.json", "datos/qrels_dificil.jsonl"),
    "ampliado": ("resultados/resultados_real_ampliado_v1.json", "datos/qrels_real_ampliado.jsonl"),
}


def main() -> None:
    docs = {json.loads(l)["id"]: json.loads(l) for l in
            (RAIZ / "corpus/corpus_v1.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    enr = {i: len(d["texto_indexable"]) > len(d["descripcion"]) for i, d in docs.items()}
    out = {"documentos_enriquecidos": sum(enr.values()), "documentos": len(enr), "conjuntos": {}}
    for nombre, (res, qr) in CONJUNTOS.items():
        d = json.loads((RAIZ / res).read_text(encoding="utf-8"))
        qrel = {json.loads(l)["id"]: json.loads(l)["relevancia"]
                for l in (RAIZ / qr).read_text(encoding="utf-8").splitlines() if l.strip()}
        por = d["por_consulta"]
        tgt = {i: max(qrel[i], key=qrel[i].get) for i in por[N["C1"]]}
        filas = {}
        for etq, cond in (("objetivo_enriquecido", True), ("objetivo_sin_enriquecer", False)):
            ids = [i for i in tgt if enr[tgt[i]] == cond]
            f = {"n": len(ids)}
            for a, b in (("C2", "C1"), ("C4", "C3")):
                if not ids:
                    continue
                r = comparar([por[N[a]][i]["ndcg@10"] for i in ids],
                             [por[N[b]][i]["ndcg@10"] for i in ids])
                f[f"{a}_vs_{b}"] = {"delta": r["media_dif"], "pares_no_nulos": r["n_pares_no_nulos"],
                                    "p_wilcoxon": r["p_valor"], "p_permutacion": r["p_permutacion"]}
            filas[etq] = f
        out["conjuntos"][nombre] = filas
    (RAIZ / "resultados/cobertura_ontologia.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    L = ["# Efecto de la ontología según el objetivo esté enriquecido (exploratorio)", "",
         f"Documentos con bloque de ontología: {out['documentos_enriquecidos']} de {out['documentos']}.", "",
         "| Conjunto | Objetivo | n | Comparación | Δ nDCG@10 | pares ≠0 | p Wilcoxon | p permut. |",
         "|---|---|---|---|---|---|---|---|"]
    fm = lambda x: "n/d" if x is None else f"{x:.4f}"
    for cn, filas in out["conjuntos"].items():
        for etq, f in filas.items():
            for k in ("C2_vs_C1", "C4_vs_C3"):
                if k in f:
                    r = f[k]
                    L.append(f"| {cn} | {etq.replace('_', ' ')} | {f['n']} | {k.replace('_vs_', ' − ')} | "
                             f"{r['delta']:+.3f} | {r['pares_no_nulos']} | {fm(r['p_wilcoxon'])} | {fm(r['p_permutacion'])} |")
    (RAIZ / "resultados/cobertura_ontologia.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
