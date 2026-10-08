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
        f"\\textbf{{{nm}}} ($n{{=}}{k}$)" for nm, _, k in conj)
    filas = []
    for c in ORDEN:
        vals = [d["global"][c]["ndcg@10"] for _, d, _ in conj]
        mejores = [max(d["global"][x]["ndcg@10"] for x in ORDEN) for _, d, _ in conj]
        celdas = [negrita_si(n(v), abs(v - m) < 1e-12) for v, m in zip(vals, mejores)]
        filas.append(f"{ETQ[c]} & " + " & ".join(celdas))
    out.append(("TABLA_GLOBAL", tabla(
        "tab:global", "nDCG@10 global de las seis configuraciones en los tres conjuntos de evaluación "
        "(corpus de diecisiete reportes, \\texttt{jina-embeddings-v3} con tareas de recuperación). "
        "En negrita, el mejor de cada conjunto. El conjunto difícil B es una réplica con consultas nuevas.", "@{}Y c c c c@{}", cab, filas)))

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
        "comparaciones \\emph{robustas}: ambas pruebas rechazan con $\\alpha=0{,}05$ tras la corrección.",
        "@{}Y c c c c c@{}", cab, filas)))

    # 2b. detalle de pares no nulos
    filas = []
    for k, etq in COMPARACIONES:
        filas.append(f"{etq} & " + " & ".join(
            f"${st[k]['n_pares_no_nulos']}/{st[k]['n']}$" for _, st in fuentes))
    out.append(("TABLA_PARES", tabla(
        "tab:pares", "Pares de consultas con diferencia no nula frente al total de consultas de cada comparación. "
        "Este número, y no el total, determina el poder efectivo de la prueba.",
        "@{}Y c c c c c@{}", "\\textbf{Comparación} & " + " & ".join(f"\\textbf{{{nm}}}" for nm, _ in fuentes), filas)))

    # 3. por estrato: ampliado y sintético ------------------------------------------------
    def estratos_tabla(d, etiqueta, caption, estratos, nombres):
        cab = "\\textbf{Configuración} & " + " & ".join(
            f"\\textbf{{{nm}}} ($n{{=}}{k}$)" for nm, k in nombres)
        filas = []
        for c in ORDEN:
            mej = {e: max(d["por_estrato"][e][x]["ndcg@10"] for x in ORDEN) for e in estratos}
            celdas = [negrita_si(n(d["por_estrato"][e][c]["ndcg@10"]),
                                 abs(d["por_estrato"][e][c]["ndcg@10"] - mej[e]) < 1e-12) for e in estratos]
            filas.append(f"{ETQ[c]} & " + " & ".join(celdas))
        return tabla(etiqueta, caption, "@{}Y" + " c" * len(estratos) + "@{}", cab, filas)

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
        "@{}Y c c c@{}", cab, filas)))

    # 5. conjunto difícil por nivel ----------------------------------------------------
    qd = [json.loads(l) for l in (RAIZ / "datos/consultas_dificil_ab.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    niv = {e: sum(1 for c in qd if c["estrato"] == e) for e in ["A_puente_ontologia", "B_sin_puente", "C_con_solape"]}
    nombres = [("A: puente de ontología", "A_puente_ontologia"), ("B: sin puente", "B_sin_puente"),
               ("C: con solape", "C_con_solape")]
    cab = "\\textbf{Configuración} & " + " & ".join(f"\\textbf{{{a}}} ($n{{=}}{niv[k]}$)" for a, k in nombres) + \
          " & \\textbf{global} ($n{=}130$)"
    filas = []
    for c in ORDEN:
        cel = [n(difab["por_estrato"][k][c]["ndcg@10"]) for _, k in nombres] + [n(difab["global"][c]["ndcg@10"])]
        filas.append(f"{ETQ[c]} & " + " & ".join(cel))
    out.append(("TABLA_DIFICIL", tabla(
        "tab:dificil", "nDCG@10 en los conjuntos difíciles unidos (A y B, $n=130$) por nivel de solape léxico (calculado, no asignado a mano). "
        "En los niveles A y B la consulta no comparte raíces con la descripción del documento, de modo que BM25 sobre la "
        "descripción no puede recuperar el objetivo por construcción.", "@{}Y c c c c@{}", cab, filas)))

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
    s = bar["sensibilidad"]
    filas = []
    for k in ["1", "10", "30", "60", "100", "200"]:
        filas.append(f"$k={k}$ & " + " & ".join(
            f"{n(s[c]['k_rrf'][k]['C3'])} / {n(s[c]['k_rrf'][k]['C4'])}" for c in ("sintetico", "ampliado")))
    for lv in ["0.0", "0.05", "0.1", "0.2", "0.3", "0.5"]:
        filas.append(f"$\\lambda={lv.replace('.', '{,}')}$ (C5) & " + " & ".join(
            f"{n(s[c]['lambda'][lv]['C5'])} ({n(s[c]['lambda'][lv]['delta_vs_C4'], 3, True)})" for c in ("sintetico", "ampliado")))
    for k1 in ["0.9", "1.5", "2.0"]:
        for b in ["0.5", "0.9"]:
            filas.append(f"$k_1={k1.replace('.', '{,}')},\\ b={b.replace('.', '{,}')}$ (BM25 / C4) & " + " & ".join(
                f"{n(s[c]['bm25_k1_b'][k1 + '|' + b]['BM25'])} / {n(s[c]['bm25_k1_b'][k1 + '|' + b]['C4'])}"
                for c in ("sintetico", "ampliado")))
    out.append(("TABLA_SENSIBILIDAD", tabla(
        "tab:sensibilidad", "Sensibilidad de los hiperparámetros fijados sin ajuste (nDCG@10). Filas de $k$: C3 / C4. Filas de $\\lambda$: "
        "C5 y, entre paréntesis, su diferencia con C4. Filas de $k_1$ y $b$: BM25 solo / C4; los valores de referencia son $k=60$, "
        "$\\lambda=0{,}2$, $k_1=1{,}5$ y $b=0{,}75$.", "@{}Y c c@{}",
        "\\textbf{Parámetro} & \\textbf{sintético} & \\textbf{ampliado}", filas)))

    # 8. Matryoshka --------------------------------------------------------------------
    p6 = bar["P6"]["por_conjunto"]
    filas = []
    for m in sorted(p6["ampliado"], key=int, reverse=True):
        a, b = p6["sintetico"][m], p6["ampliado"][m]
        def cel(f):
            return f"{n(f['C4'])} ({n(f['dif_C4_vs_nativa'], 3, True)}; {'eq.' if f['equivalente_eps'] else 'no eq.'})"
        filas.append(f"${m}$ & {cel(a)} & {cel(b)} & ${100 * a['ahorro_indice']:.1f}\\%$".replace(".", "{,}", 1)
                     if False else f"${m}$ & {cel(a)} & {cel(b)} & ${100 * a['ahorro_indice']:.1f}\\%$")
    out.append(("TABLA_MATRYOSHKA", tabla(
        "tab:matryoshka", "Barrido de la dimensión Matryoshka $m$ sobre C4: nDCG@10 y, entre paréntesis, la diferencia con $m=1.024$ y si el "
        "intervalo de confianza del $95\\%$ de esa diferencia permite declarar equivalencia (límite inferior mayor que $-0{,}01$). "
        "``eq.'' = equivalente, ``no eq.'' = no concluyente.", "@{}c c c c@{}",
        "$\\boldsymbol{m}$ & \\textbf{sintético} & \\textbf{ampliado} & \\textbf{ahorro de índice}", filas)))

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
        "variante se elige con los otros tres conjuntos (\\textit{leave-one-set-out}) y se aplica sin retocar. Ninguna diferencia es robusta.",
        "@{}Y c c c c@{}", cab, filas)))

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
        "@{}l c c c@{}", "\\textbf{Conjunto} & \\textbf{denso} (sin / parcial / ampl.) & \\textbf{híbrido} (sin / parcial / ampl.) & \\textbf{objetivo antes sin bloque}", filas)))

    # 12. errores (acc@1) ------------------------------------------------------------------
    er = CARGA("analisis_errores.json")
    sis = ["BM25", "C1", "C2", "C3", "C4"]
    filas = [f"{nm[c]} ($n{{=}}{er[c]['n']}$) & " + " & ".join(n(er[c]["acc1"][x]) for x in sis) for c in cs]
    out.append(("TABLA_ERRORES", tabla(
        "tab:errores", "Exactitud en la primera posición (el reporte objetivo queda primero) por sistema y conjunto.",
        "@{}Y c c c c c@{}", "\\textbf{Conjunto} & " + " & ".join(f"\\textbf{{{x}}}" for x in sis), filas)))

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
        "documentos $N$ y la dimensión $m$. No mide calidad ni la codificación de la consulta ($\\approx 349$ ms). Medido en un equipo personal con otras tareas activas.",
        "@{}r " + "c " * len(dm) + "@{}", "$\\boldsymbol{N}$ & " + " & ".join(f"\\textbf{{$m={m}$}}" for m in dm), filas)))

    texto = "\n".join(f"% === {nm_} ===\n{t}" for nm_, t in out)
    (R / "tablas_monografia.tex").write_text(texto, encoding="utf-8")
    print(f"{len(out)} tablas -> resultados/tablas_monografia.tex")


if __name__ == "__main__":
    main()
