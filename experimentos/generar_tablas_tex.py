#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera las tablas LaTeX de la sección «Resultados» de la monografía directamente desde los JSON.

Evita transcribir cifras a mano: cada celda sale de resultados/*.json. Salida:
resultados/tablas_monografia.tex (un bloque `% === NOMBRE ===` por tabla, para insertar tal cual).

Entradas: resultados.json (sintético), resultados_real_ampliado_v1(.json, _sin_nombre.json),
resultados_dificil_v1.json, cobertura_ontologia.json, barridos.json.
Uso: python3 generar_tablas_tex.py
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
R = RAIZ / "resultados"
CARGA = lambda n: json.loads((R / n).read_text(encoding="utf-8"))

ORDEN = ["BM25 (referencia léxica)", "Denso puro", "Denso + ontología", "Híbrido (sin ontología)",
         "Híbrido + ontología", "Híbrido + ontología + realce"]
ETQ = {"BM25 (referencia léxica)": "BM25 (referencia)", "Denso puro": "C1 · Denso puro",
       "Denso + ontología": "C2 · Denso $+$ ontología", "Híbrido (sin ontología)": "C3 · Híbrido (sin ontología)",
       "Híbrido + ontología": "C4 · Híbrido $+$ ontología", "Híbrido + ontología + realce": "C5 · Híbrido $+$ ont. $+$ realce"}
COMPARACIONES = [("C3_vs_BM25 (P1)", "C3 frente a BM25 (P1)"), ("C3_vs_C1 (P1,P2)", "C3 frente a C1 (P1)"),
                 ("C2_vs_C1 (P3 denso)", "C2 frente a C1 (P3, denso)"),
                 ("C4_vs_C3 (P3 híbrido)", "C4 frente a C3 (P3, híbrido)"),
                 ("C5_vs_C4 (P5)", "C5 frente a C4 (P5)")]


def n(x: float, d: int = 3, signo: bool = False) -> str:
    s = f"{x:+.{d}f}" if signo else f"{x:.{d}f}"
    return "$" + s.replace(".", "{,}").replace("-", "-") + "$"


def p(x) -> str:
    if x is None:
        return "n/d"
    return "$<\\!0{,}001$" if x < 0.001 else "$" + f"{x:.3f}".replace(".", "{,}") + "$"


def negrita_si(txt: str, cond: bool) -> str:
    return f"{{\\boldmath\\bfseries {txt}}}" if cond else txt


def dos(a, b) -> str:
    """Celda de encabezado en dos líneas centradas."""
    return f"\\begin{{tabular}}[b]{{@{{}}c@{{}}}}\\textbf{{{a}}}\\\\{b}\\end{{tabular}}"


def tabla(etiqueta, caption, colspec, cabecera, filas, nota=None):
    L = ["\\begin{table}[htbp]", "\\centering", "\\footnotesize", "\\setlength{\\tabcolsep}{5pt}",
         "\\renewcommand{\\arraystretch}{1.25}", f"\\caption{{{caption}}}", f"\\label{{{etiqueta}}}",
         f"\\begin{{tabularx}}{{\\textwidth}}{{{colspec}}}", "\\toprule", cabecera + " \\\\", "\\midrule"]
    L += [f + " \\\\" for f in filas]
    L += ["\\bottomrule", "\\end{tabularx}"]
    if nota:
        L += [f"\\par\\smallskip{{\\footnotesize {nota}}}"]
    L += ["\\end{table}", ""]
    return "\n".join(L)


def main() -> None:
    sint = CARGA("resultados.json")
    amp = CARGA("resultados_real_ampliado_v1.json")
    ctrl = CARGA("resultados_real_ampliado_v1_sin_nombre.json")
    dif = CARGA("resultados_dificil_v1.json")
    difb = CARGA("resultados_dificil_b_v1.json")
    difab = CARGA("resultados_dificil_ab_v1.json")
    cob = CARGA("cobertura_ontologia.json")
    bar = CARGA("barridos.json")
    out = []

    # 1. global por conjunto -------------------------------------------------------------
    conj = [("sintético", sint, sint["n_consultas_con_gold"]), ("ampliado", amp, amp["n_con_gold"]),
            ("difícil A", dif, dif["n_con_gold"]), ("difícil B", difb, difb["n_con_gold"])]
    cab = "\\textbf{Configuración} & " + " & ".join(
        dos(nm, f"($n{{=}}{k}$)") for nm, _, k in conj)
    filas = []
    for c in ORDEN:
        vals = [d["global"][c]["ndcg@10"] for _, d, _ in conj]
        mejores = [max(d["global"][x]["ndcg@10"] for x in ORDEN) for _, d, _ in conj]
        celdas = [negrita_si(n(v), abs(v - m) < 1e-12) for v, m in zip(vals, mejores)]
        filas.append(f"{ETQ[c]} & " + " & ".join(celdas))
    out.append(("TABLA_GLOBAL", tabla(
        "tab:global", "nDCG@10 global de las seis configuraciones en los tres conjuntos de evaluación "
        "(corpus de diecisiete reportes, \\texttt{jina-embeddings-v3} con tareas de recuperación). "
        "En negrita, el mejor de cada conjunto. El conjunto difícil B es una réplica con consultas nuevas.", "@{}l C C C C@{}", cab, filas)))

    # 2. estadística: Δ (p de Holm conservador) -----------------------------------------
    def stat_sint():
        return sint["estadistica_global"]

    fuentes = [("sintético", stat_sint()), ("ampliado", amp["estadistica"]["global"]),
               ("difícil A", dif["estadistica"]["global"]),
               ("difícil B", difb["estadistica"]["global"]), ("A+B", difab["estadistica"]["global"])]
    cab = "\\textbf{Comparación} & " + " & ".join(f"\\textbf{{{nm}}}" for nm, _ in fuentes)
    filas = []
    for k, etq in COMPARACIONES:
        celdas = []
        for _, st in fuentes:
            r = st[k]
            ph = [x for x in (r.get("p_holm"), r.get("p_holm_permutacion")) if x is not None]
            pm = max(ph) if ph else None
            celdas.append(negrita_si(f"{n(r['media_dif'], 3, True)} ({p(pm).replace('$', '') if pm is None else p(pm)})"
                                     , bool(r.get("robusto"))))
        filas.append(f"{etq} & " + " & ".join(celdas))
    out.append(("TABLA_ESTADISTICA", tabla(
        "tab:estadistica", "Diferencia media de nDCG@10 (primera configuración menos segunda) y, entre paréntesis, "
        "el mayor de los dos $p$-valores ajustados por Holm (Wilcoxon y permutación pareadas). En negrita, las "
        "comparaciones \\emph{concordantes}: ambas pruebas rechazan con $\\alpha=0{,}05$ tras la corrección.",
        "@{}l C C C C C@{}", cab, filas)))

    # 2b. detalle de pares no nulos
    filas = []
    for k, etq in COMPARACIONES:
        filas.append(f"{etq} & " + " & ".join(
            f"${st[k]['n_pares_no_nulos']}/{st[k]['n']}$" for _, st in fuentes))
    out.append(("TABLA_PARES", tabla(
        "tab:pares", "Pares de consultas con diferencia no nula frente al total de consultas de cada comparación. "
        "Este número, y no el total, determina el poder efectivo de la prueba.",
        "@{}l C C C C C@{}", "\\textbf{Comparación} & " + " & ".join(f"\\textbf{{{nm}}}" for nm, _ in fuentes), filas)))

    # 3. por estrato: ampliado y sintético ------------------------------------------------
    def estratos_tabla(d, etiqueta, caption, estratos, nombres):
        cab = "\\textbf{Configuración} & " + " & ".join(
            dos(nm, f"($n{{=}}{k}$)") for nm, k in nombres)
        filas = []
        for c in ORDEN:
            mej = {e: max(d["por_estrato"][e][x]["ndcg@10"] for x in ORDEN) for e in estratos}
            celdas = [negrita_si(n(d["por_estrato"][e][c]["ndcg@10"]),
                                 abs(d["por_estrato"][e][c]["ndcg@10"] - mej[e]) < 1e-12) for e in estratos]
            filas.append(f"{ETQ[c]} & " + " & ".join(celdas))
        return tabla(etiqueta, caption, "@{}l" + " C" * len(estratos) + "@{}", cab, filas)

    out.append(("TABLA_ESTRATOS_AMPLIADO", estratos_tabla(
        amp, "tab:estratos-ampliado", "nDCG@10 por estrato en el conjunto ampliado. En negrita, el mejor de cada estrato.",
        ["entidad_exacta", "operacional", "documento_largo", "ambigua"],
        [("entidad exacta", 55), ("operacional", 35), ("doc. largo", 25), ("ambigua", 12)])))
    out.append(("TABLA_ESTRATOS_SINTETICO", estratos_tabla(
        sint, "tab:estratos-sintetico", "nDCG@10 por estrato en el conjunto sintético. En negrita, el mejor de cada estrato.",
        ["entidad_exacta", "ambigua", "documento_largo"],
        [("entidad exacta", 17), ("ambigua", 13), ("doc. largo", 10)])))

    # 4. control sin nombre -------------------------------------------------------------
    cab = "\\textbf{Configuración} & \\textbf{con nombre} & \\textbf{sin nombre} & \\textbf{diferencia}"
    filas = []
    for c in ORDEN:
        a = amp["por_estrato"]["entidad_exacta"][c]["ndcg@10"]
        b = ctrl["por_estrato"]["entidad_exacta"][c]["ndcg@10"]
        filas.append(f"{ETQ[c]} & {n(a)} & {n(b)} & {n(b - a, 3, True)}")
    out.append(("TABLA_CONTROL", tabla(
        "tab:control", "Control sin nombre propio en el estrato de entidad exacta ($n=55$): nDCG@10 con la consulta original y con el "
        "nombre propio borrado. Si el nombre contribuyera a la recuperación, la columna ``sin nombre'' debería ser menor.",
        "@{}l C C C@{}", cab, filas)))

    # 5. conjunto difícil por nivel ----------------------------------------------------
    qd = [json.loads(l) for l in (RAIZ / "datos/consultas_dificil_ab.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    niv = {e: sum(1 for c in qd if c["estrato"] == e) for e in ["A_puente_ontologia", "B_sin_puente", "C_con_solape"]}
    nombres = [("Nivel A: puente", "A_puente_ontologia"), ("Nivel B: sin puente", "B_sin_puente"),
               ("Nivel C: con solape", "C_con_solape")]
    cab = "\\textbf{Configuración} & " + " & ".join(dos(a, f"($n{{=}}{niv[k]}$)") for a, k in nombres) + \
          " & " + dos("Global", "($n{=}130$)")
    filas = []
    for c in ORDEN:
        cel = [n(difab["por_estrato"][k][c]["ndcg@10"]) for _, k in nombres] + [n(difab["global"][c]["ndcg@10"])]
        filas.append(f"{ETQ[c]} & " + " & ".join(cel))
    out.append(("TABLA_DIFICIL", tabla(
        "tab:dificil", "nDCG@10 en los conjuntos difíciles unidos (A y B, $n=130$) por nivel de solape léxico (calculado, no asignado a mano). "
        "En los niveles A y B la consulta no comparte raíces con la descripción del documento, de modo que BM25 sobre la "
        "descripción no puede recuperar el objetivo por construcción.", "@{}l C C C C@{}", cab, filas)))

    # 6. cobertura de la ontología -------------------------------------------------------
    filas = []
    for cn in ("dificil", "ampliado"):
        for etq, nom in (("objetivo_enriquecido", "objetivo enriquecido"), ("objetivo_sin_enriquecer", "objetivo sin enriquecer")):
            f = cob["conjuntos"][cn][etq]
            for k, lab in (("C2_vs_C1", "C2 $-$ C1"), ("C4_vs_C3", "C4 $-$ C3")):
                r = f[k]
                filas.append(f"{'difícil' if cn == 'dificil' else 'ampliado'} & {nom} ($n{{=}}{f['n']}$) & {lab} & "
                             f"{n(r['delta'], 3, True)} & ${r['pares_no_nulos']}$ & {p(r['p_wilcoxon'])} & {p(r['p_permutacion'])}")
    out.append(("TABLA_COBERTURA", tabla(
        "tab:cobertura", "Análisis exploratorio: efecto de la ontología según el reporte objetivo tenga o no bloque de ontología "
        "(9 de los 17 reportes lo tienen). Sin corrección de Holm; debe leerse como generador de hipótesis.",
        "@{}l l l c c c c@{}", "\\textbf{Conjunto} & \\textbf{Grupo} & \\textbf{Comparación} & $\\boldsymbol{\\Delta}$ & \\textbf{pares $\\neq 0$} & "
        "\\textbf{$p$ Wilcoxon} & \\textbf{$p$ permut.}", filas)))

    # 7. sensibilidad ---------------------------------------------------------------------
    s = dict(bar["sensibilidad"]); s["dificil_ab"] = CARGA("barridos_dificiles.json")["sensibilidad"]["dificil_ab"]
    filas = []
    for k in ["1", "10", "30", "60", "100", "200"]:
        filas.append(f"$k={k}$ & " + " & ".join(
            f"{n(s[c]['k_rrf'][k]['C3'])} / {n(s[c]['k_rrf'][k]['C4'])}" for c in ("sintetico", "ampliado", "dificil_ab")))
    for lv in ["0.0", "0.05", "0.1", "0.2", "0.3", "0.5"]:
        filas.append(f"$\\lambda={lv.replace('.', '{,}')}$ (C5) & " + " & ".join(
            f"{n(s[c]['lambda'][lv]['C5'])} ({n(s[c]['lambda'][lv]['delta_vs_C4'], 3, True)})" for c in ("sintetico", "ampliado", "dificil_ab")))
    for k1 in ["0.9", "1.5", "2.0"]:
        for b in ["0.5", "0.9"]:
            filas.append(f"$k_1={k1.replace('.', '{,}')},\\ b={b.replace('.', '{,}')}$ (BM25 / C4) & " + " & ".join(
                f"{n(s[c]['bm25_k1_b'][k1 + '|' + b]['BM25'])} / {n(s[c]['bm25_k1_b'][k1 + '|' + b]['C4'])}"
                for c in ("sintetico", "ampliado", "dificil_ab")))
    out.append(("TABLA_SENSIBILIDAD", tabla(
        "tab:sensibilidad", "Sensibilidad de los hiperparámetros fijados sin ajuste (nDCG@10). Filas de $k$: C3 / C4. Filas de $\\lambda$: "
        "C5 y, entre paréntesis, su diferencia con C4. Filas de $k_1$ y $b$: BM25 solo / C4; los valores de referencia son $k=60$, "
        "$\\lambda=0{,}2$, $k_1=1{,}5$ y $b=0{,}75$.", "@{}l C C C@{}",
        "\\textbf{Parámetro} & \\textbf{sintético} & \\textbf{ampliado} & \\textbf{difíciles A+B}", filas)))

    # 8. Matryoshka --------------------------------------------------------------------
    p6 = dict(bar["P6"]["por_conjunto"]); p6["dificil_ab"] = CARGA("barridos_dificiles.json")["P6"]["por_conjunto"]["dificil_ab"]
    filas = []
    for m in sorted(p6["ampliado"], key=int, reverse=True):
        a, b = p6["sintetico"][m], p6["ampliado"][m]
        def cel(f):
            return f"{n(f['C4'])} ({n(f['dif_C4_vs_nativa'], 3, True)}; {'eq.' if f['equivalente_eps'] else 'no eq.'})"
        filas.append(f"${m}$ & {cel(a)} & {cel(b)} & {cel(p6['dificil_ab'][m])} & " + f"${100 * a['ahorro_indice']:.1f}".replace(".", "{,}") + "\\%$".replace(".", "{,}", 1)
                     if False else f"${m}$ & {cel(a)} & {cel(b)} & {cel(p6['dificil_ab'][m])} & " + f"${100 * a['ahorro_indice']:.1f}".replace(".", "{,}") + "\\%$")
    out.append(("TABLA_MATRYOSHKA", tabla(
        "tab:matryoshka", "Barrido de la dimensión Matryoshka $m$ sobre C4: nDCG@10 y, entre paréntesis, la diferencia con $m=1.024$ y si el "
        "intervalo de confianza del $95\\%$ de esa diferencia permite declarar equivalencia (límite inferior mayor que $-0{,}01$). "
        "``eq.'' = equivalente, ``no eq.'' = no concluyente.", "@{}c C C C c@{}",
        "$\\boldsymbol{m}$ & \\textbf{sintético} & \\textbf{ampliado} & \\textbf{difíciles A+B} & \\textbf{ahorro}", filas)))

    # 9. chunking ----------------------------------------------------------------------
    p4 = bar["P4"]["por_conjunto"]
    filas = []
    for tam, lab in (("doc", "documento completo"), ("128", "128 palabras"), ("64", "64 palabras"),
                     ("40", "40 palabras"), ("24", "24 palabras")):
        fila = [lab]
        for c in ("sintetico", "ampliado"):
            for so in ("0.0", "0.25"):
                v = p4[c][f"{tam}|{so}"]
                fila.append(f"{n(v['nDCG@10'])} ({n(v['delta_vs_doc_completo'], 3, True)})")
        fila.append(f"${p4['sintetico'][tam + '|0.0']['frag_por_doc']:.2f}$".replace(".", "{,}"))
        filas.append(" & ".join(fila))
    out.append(("TABLA_CHUNKING", tabla(
        "tab:chunking", "Fragmentación de los documentos (nDCG@10 de C4 y, entre paréntesis, la diferencia con el documento completo) "
        "para solapamiento de $0\\%$ y de $25\\%$.", "@{}l c c c c c@{}",
        "\\textbf{Tamaño} & \\textbf{sint., 0\\%} & \\textbf{sint., 25\\%} & \\textbf{amp., 0\\%} & \\textbf{amp., 25\\%} & "
        "\\textbf{frag./doc.}", filas)))

    # 10. fusión ----------------------------------------------------------------------
    fu = CARGA("fusion.json")
    cs = list(fu["n"])
    nm = {"sintetico": "sintético", "ampliado": "ampliado", "dificil": "difícil A", "dificil_b": "difícil B"}
    cab = "\\textbf{Variante (base enriquecida)} & " + " & ".join(f"\\textbf{{{nm[c]}}}" for c in cs)
    filas = [f"BM25 solo & " + " & ".join(n(fu["curvas"]["onto"][c]["bm25"]) for c in cs),
             f"Denso puro (C2) & " + " & ".join(n(fu["curvas"]["onto"][c]["denso"]) for c in cs),
             f"RRF $k=60$ (C4) & " + " & ".join(n(fu["curvas"]["onto"][c]["rrf60"]) for c in cs)]
    for fam, etq in (("convexa_minmax", "Convexa min--max"), ("convexa_z", "Convexa $z$-score"),
                     ("rrf_ponderado", "RRF ponderado"), ("rrf_compuerta", "RRF con compuerta")):
        cel = []
        for c in cs:
            e, l = fu["estadistica"]["onto"][c][fam], fu["loso"]["onto"][c][fam]
            cel.append(negrita_si(f"{n(l['ndcg'])} ({n(e['delta_vs_rrf60'], 3, True)})", bool(e["robusto"])))
        filas.append(f"{etq} (LOSO) & " + " & ".join(cel))
    out.append(("TABLA_FUSION", tabla(
        "tab:fusion", "Alternativas de fusión frente a RRF (nDCG@10 y, entre paréntesis, la diferencia con RRF $k=60$). El parámetro de cada "
        "variante se elige con los otros tres conjuntos (\\textit{leave-one-set-out}) y se aplica sin retocar. Ninguna diferencia es concordante.",
        "@{}l C C C C@{}", cab, filas)))

    # 11. ontología completa ---------------------------------------------------------------
    en = CARGA("enriquecimiento_completo.json")
    filas = []
    for c, lab in (("sintetico", "sintético"), ("ampliado", "ampliado"), ("dificil", "difícil A"), ("dificil_b", "difícil B")):
        m = en["conjuntos"][c]["medias"]
        g = en["conjuntos"][c]["comparaciones"].get("objetivo_sin_bloque_antes", {}).get("hibrido: completa − parcial")
        extra = f"{n(g['delta'], 3, True)} ($n{{=}}{g['n']}$)" if g and g["pares_no_nulos"] else "---"
        filas.append(f"{lab} & {n(m['desc|denso'])} / {n(m['parcial|denso'])} / {n(m['completa|denso'])} & "
                     f"{n(m['desc|hibrido'])} / {n(m['parcial|hibrido'])} / {n(m['completa|hibrido'])} & {extra}")
    out.append(("TABLA_ONTO_COMPLETA", tabla(
        "tab:onto-completa", "Ontología sin / parcial (9 de 17) / ampliada (14 de 17) reportes: nDCG@10 del denso y del híbrido. La última columna es la "
        "diferencia del híbrido (ampliada menos parcial) en las consultas cuyo objetivo no tenía bloque de ontología.",
        "@{}l C C C@{}", "\\textbf{Conjunto} & " + dos("Denso", "sin / parcial / ampliada") + " & " + dos("Híbrido", "sin / parcial / ampliada") + " & " + dos("Objetivo antes", "sin bloque"), filas)))

    # 12. errores (acc@1) ------------------------------------------------------------------
    er = CARGA("analisis_errores.json")
    sis = ["BM25", "C1", "C2", "C3", "C4"]
    filas = [f"{nm[c]} ($n{{=}}{er[c]['n']}$) & " + " & ".join(n(er[c]["acc1"][x]) for x in sis) for c in cs]
    out.append(("TABLA_ERRORES", tabla(
        "tab:errores", "Exactitud en la primera posición (el reporte objetivo queda primero) por sistema y conjunto.",
        "@{}l C C C C C@{}", "\\textbf{Conjunto} & " + " & ".join(f"\\textbf{{{x}}}" for x in sis), filas)))

    # 13. escalamiento ---------------------------------------------------------------------
    es = CARGA("escalamiento.json")
    dm = sorted({c["m"] for c in es["celdas"]})
    nn = sorted({c["N"] for c in es["celdas"]})
    filas = []
    for N in nn:
        fila = [f"${N:,}$".replace(",", ".")]
        for m in dm:
            c = next(x for x in es["celdas"] if x["N"] == N and x["m"] == m)
            fila.append(f"${c['indice_MiB']:.1f}$ / ${c['p50_ms']:.2f}$".replace(".", "{,}"))
        filas.append(" & ".join(fila))
    out.append(("TABLA_ESCALAMIENTO", tabla(
        "tab:escalamiento", "Búsqueda exacta por fuerza bruta con vectores aleatorios: memoria del índice (MiB) y latencia mediana (ms) según el número de "
        "documentos $N$ y la dimensión $m$. No mide calidad ni la codificación de la consulta ($\\approx 351$ ms). Medido en un equipo personal con otras tareas activas.",
        "@{}r " + "c " * len(dm) + "@{}", "$\\boldsymbol{N}$ & " + " & ".join(f"\\textbf{{$m={m}$}}" for m in dm), filas)))

    # 14. corpus definitivo ------------------------------------------------------------
    import numpy as _np
    from lib.stats import comparar as _comparar, holm as _holm
    fin = CARGA("resultados_final.json"); fsn = CARGA("resultados_final_sin_nombre.json"); fdab = CARGA("resultados_final_dificil_ab.json")
    def _m(d, est, c, met="ndcg@10"):
        return d["global"][c][met] if est is None else d["por_estrato"][est][c][met]
    cols = [("Global", "($n{=}180$)", lambda c: _m(fin, None, c)), ("Recall@100", "global", lambda c: _m(fin, None, c, "recall@100")),
            ("Competencias", "($n{=}53$)", lambda c: _m(fin, "competencias", c)), ("Entidad exacta", "con nombre ($n{=}55$)", lambda c: _m(fin, "entidad_exacta", c)),
            ("Entidad exacta", "sin nombre ($n{=}55$)", lambda c: _m(fsn, "entidad_exacta", c)), ("Difíciles A+B", "($n{=}130$)", lambda c: _m(fdab, None, c))]
    cab = "\\textbf{Configuración} & " + " & ".join(dos(a, b) for a, b, _ in cols)
    filas = []
    for c in ORDEN:
        celdas = []
        for _, _, f in cols:
            mejor = max(f(x) for x in ORDEN)
            celdas.append(negrita_si(n(f(c)), abs(f(c) - mejor) < 1e-12))
        filas.append(f"{ETQ[c]} & " + " & ".join(celdas))
    out.append(("TABLA_FINAL", tabla(
        "tab:final", "Resultados sobre el corpus definitivo de $177$ documentos ($160$ Pruebas Regionales y $17$ reportes): nDCG@10 salvo la segunda columna "
        "(Recall@100). Las consultas de entidad exacta se evalúan con el nombre propio y con el nombre borrado; los conjuntos difíciles se evalúan "
        "ahora con $160$ documentos adicionales que compiten. En negrita, el mejor de cada columna.", "@{}l" + " C" * len(cols) + "@{}", cab, filas)))

    IDX = {"BM25": "BM25 (referencia léxica)", "C1": "Denso puro", "C2": "Denso + ontología", "C3": "Híbrido (sin ontología)",
           "C4": "Híbrido + ontología", "C5": "Híbrido + ontología + realce"}
    FAM = [("C3", "BM25", "C3 frente a BM25 (P1)"), ("C3", "C1", "C3 frente a C1 (P1, P2)"), ("C2", "C1", "C2 frente a C1 (P3, denso)"),
           ("C4", "C3", "C4 frente a C3 (P3, híbrido)"), ("C5", "C4", "C5 frente a C4 (P5)")]
    EXTRA = [("C1", "BM25", "C1 frente a BM25 (aporte del codificador)"), ("C4", "C2", "C4 frente a C2 (elección de la configuración)")]
    qf = {json.loads(l)["id"]: json.loads(l) for l in (RAIZ / "datos/consultas_final.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    subconj = [("Global", fin, None), ("Competencias", fin, "competencias"), ("Entidad exacta", fin, "entidad_exacta"), ("Difíciles A+B", fdab, None)]
    def _serie(d, est, c):
        por = d["por_consulta"][IDX[c]]
        ids = [i for i in por if est is None or (i in qf and qf[i]["estrato"] == est)]
        return [por[i]["ndcg@10"] for i in ids]
    res_cols = []
    for nm, d, est in subconj:
        r = {lab: _comparar(_serie(d, est, a), _serie(d, est, b)) for a, b, lab in FAM}
        hw = _holm({k: v["p_valor"] for k, v in r.items()}); hp = _holm({k: v["p_permutacion"] for k, v in r.items()})
        for k in r:
            r[k]["robusto"] = bool(hw[k] is not None and hp[k] is not None and hw[k] < 0.05 and hp[k] < 0.05)
            r[k]["pmax"] = max([x for x in (hw[k], hp[k]) if x is not None], default=None)
        for a, b, lab in EXTRA:
            r[lab] = _comparar(_serie(d, est, a), _serie(d, est, b)); r[lab]["robusto"] = None
            r[lab]["pmax"] = max([x for x in (r[lab]["p_valor"], r[lab]["p_permutacion"]) if x is not None], default=None)
        res_cols.append(r)
    filas = []
    for a, b, lab in FAM + EXTRA:
        cel = []
        for r in res_cols:
            v = r[lab]
            txt = f"{n(v['media_dif'], 3, True)} ({p(v['pmax'])})"
            cel.append(negrita_si(txt, bool(v["robusto"])))
        filas.append((r"\\midrule " if lab == EXTRA[0][2] else "") + f"{lab} & " + " & ".join(cel))
    out.append(("TABLA_FINAL_STATS", tabla(
        "tab:final-stats", "Comparaciones sobre el corpus definitivo: diferencia media de nDCG@10 y, entre paréntesis, el mayor de los $p$-valores de Wilcoxon y "
        "permutación. En las cinco primeras filas los $p$ están ajustados por Holm dentro de la familia y la negrita marca las concordantes; las dos "
        "últimas son complementarias, sin ajuste.", "@{}l C C C C@{}",
        "\\textbf{Comparación} & " + " & ".join(f"\\textbf{{{nm}}}" for nm, _, _ in subconj), filas)))

    # 15. robustez por reporte -----------------------------------------------------------
    rb = CARGA("robustez.json")
    sets_rb = [("ampliado (17 docs)", "ampliado"), ("difíciles A+B (17 docs)", "difíciles (17)"), ("definitivo (177 docs)", "definitivo"), ("difíciles A+B (177 docs)", "difíciles (177)")]
    filas = []
    for comp, lab in (("C3-BM25", "C3 $-$ BM25"), ("C3-C1", "C3 $-$ C1"), ("C2-C1", "C2 $-$ C1"), ("C4-C3", "C4 $-$ C3"), ("C5-C4", "C5 $-$ C4"), ("C4-C2", "C4 $-$ C2")):
        cel = []
        for k, _ in sets_rb:
            v = rb[k]["comparaciones"][comp]
            txt = f"{n(v['delta'], 3, True)} [{n(v['ic95_bootstrap_reporte'][0], 3, True)}; {n(v['ic95_bootstrap_reporte'][1], 3, True)}]"
            cel.append(negrita_si(txt, v["excluye_cero"]))
        filas.append(f"{lab} & " + " & ".join(cel))
    out.append(("TABLA_ROBUSTEZ", tabla(
        "tab:robustez", "Robustez frente a la dependencia por reporte: diferencia media de nDCG@10 e intervalo del $95\\%$ por \\textit{bootstrap} remuestreando "
        "reportes (o pruebas) objetivo, no consultas. En negrita, los intervalos que excluyen el cero. Dejar fuera un reporte a la vez no cambia el signo "
        "de ninguna diferencia que excluye el cero.", "@{}l C C C C@{}",
        "\\textbf{Comparación} & " + " & ".join(f"\\textbf{{{b}}}" for _, b in sets_rb), filas)))

    # 16. dosis-respuesta ---------------------------------------------------------------
    filas = []
    for k, lab in (("difíciles A+B (17 docs)", "17 documentos"), ("difíciles A+B (177 docs)", "177 documentos")):
        for comp, cl in (("C2-C1", "C2 $-$ C1"), ("C4-C3", "C4 $-$ C3")):
            v = rb[k]["dosis_respuesta"][comp]; t = v["tramos"]
            filas.append(f"{lab} & {cl} & {n(t['0']['delta'], 3, True)} & {n(t['1']['delta'], 3, True)} & {n(t['2 o más']['delta'], 3, True)} & "
                         f"{n(v['spearman_rho'], 2, True)} ({p(v['p'])})")
    out.append(("TABLA_DOSIS", tabla(
        "tab:dosis", "Dosis-respuesta de la ontología en los conjuntos difíciles: diferencia media de nDCG@10 según cuántas raíces comparte la consulta con el "
        "bloque de ontología del reporte objetivo ($0$: $n=57$; $1$: $n=34$; $2$ o más: $n=39$), y correlación de Spearman entre ese número y la diferencia.",
        "@{}l l C C C C@{}", "\\textbf{Corpus} & \\textbf{Comparación} & " + dos("0 raíces", "") + " & " + dos("1 raíz", "") + " & " + dos("2 o más", "") + " & " + dos("Spearman", "($p$)"), filas)))

    # 17. metaanálisis, éxito y EMD ------------------------------------------------------
    co = CARGA("complementario.json")
    filas = []
    for comp, lab in (("C1-BM25", "C1 $-$ BM25"), ("C3-C1", "C3 $-$ C1"), ("C2-C1", "C2 $-$ C1"), ("C4-C3", "C4 $-$ C3"), ("C5-C4", "C5 $-$ C4"), ("C4-C2", "C4 $-$ C2")):
        v = co["metaanalisis"][comp]
        excl = v["ic95"][0] > 0 or v["ic95"][1] < 0
        filas.append(f"{lab} & {n(v['A'], 3, True)} & {n(v['B'], 3, True)} & " + negrita_si(f"{n(v['combinado'], 3, True)} [{n(v['ic95'][0], 3, True)}; {n(v['ic95'][1], 3, True)}]", excl)
                     + f" & {n(v['Q_heterogeneidad'], 2)}")
    out.append(("TABLA_META", tabla(
        "tab:meta", "Metaanálisis de efectos fijos de los conjuntos difíciles A ($n=52$) y B ($n=78$), corpus de 17 documentos. $Q$ mide la heterogeneidad "
        "entre ambos (con un grado de libertad, valores menores que $3{,}84$ no indican heterogeneidad significativa). En negrita, los efectos combinados "
        "cuyo intervalo excluye el cero.", "@{}l C C C C@{}", "\\textbf{Comparación} & \\textbf{Difícil A} & \\textbf{Difícil B} & \\textbf{Combinado [IC 95\\%]} & $\\boldsymbol{Q}$", filas)))
    sets_ex = [("ampliado", "Ampliado"), ("dificil_a", "Difícil A"), ("dificil_b", "Difícil B"), ("definitivo_177", "Definitivo"), ("dificiles_177", "Difíciles (177)")]
    filas = []
    for c, lab in (("BM25", "BM25"), ("C1", "C1 · Denso puro"), ("C2", "C2 · Denso $+$ ontología"), ("C3", "C3 · Híbrido"), ("C4", "C4 · Híbrido $+$ ontología"), ("C5", "C5 · $+$ realce")):
        filas.append(f"{lab} & " + " & ".join(f"{n(co['exito'][k][c]['@1'], 2)} / {n(co['exito'][k][c]['@3'], 2)}" for k, _ in sets_ex))
    out.append(("TABLA_EXITO", tabla(
        "tab:exito", "Éxito en la primera posición y entre las tres primeras (fracción de consultas con un documento relevante en esas posiciones). Es la "
        "lectura más directa para el usuario: con qué frecuencia el reporte correcto aparece de inmediato.", "@{}l C C C C C@{}",
        "\\textbf{Configuración} & " + " & ".join(dos(b, "@1 / @3") for _, b in sets_ex), filas)))
    filas = []
    for comp, lab in (("C3-C1", "C3 $-$ C1"), ("C2-C1", "C2 $-$ C1"), ("C4-C3", "C4 $-$ C3"), ("C5-C4", "C5 $-$ C4"), ("C4-C2", "C4 $-$ C2")):
        filas.append(f"{lab} & " + " & ".join(f"{n(co['comparaciones'][k][comp]['media_dif'], 3, True)} / {n(co['emd'][k][comp], 3)}" for k, _ in sets_ex))
    out.append(("TABLA_EMD", tabla(
        "tab:emd", "Diferencia observada frente al efecto mínimo detectable (EMD) con potencia de $0{,}8$ y $\\alpha=0{,}05$ bilateral, aproximado como "
        "$2{,}8\\,s_d/\\sqrt{n}$. Una diferencia observada menor que el EMD no se habría podido distinguir del azar con ese número de consultas.",
        "@{}l C C C C C@{}", "\\textbf{Comparación} & " + " & ".join(dos(b, "obs. / EMD") for _, b in sets_ex), filas)))

    # ROBUSTEZ_PEQUENA: la tabla de robustez usa letra más pequeña para que cada celda quepa en una línea
    out = [(nm_, t.replace("\\footnotesize", "\\scriptsize", 1).replace("{\\tabcolsep}{5pt}", "{\\tabcolsep}{3pt}", 1) if nm_ == "TABLA_ROBUSTEZ" else t) for nm_, t in out]
    texto = "\n".join(f"% === {nm_} ===\n{t}" for nm_, t in out)
    (R / "tablas_monografia.tex").write_text(texto, encoding="utf-8")
    print(f"{len(out)} tablas -> resultados/tablas_monografia.tex")


if __name__ == "__main__":
    main()
