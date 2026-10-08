#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas del núcleo (sin modelo denso, sin red): se ejecutan en segundos.

Cubren los errores que la auditoría del 2026-09-30 encontró y que no deben volver:
  * BM25 devolvía documentos con score 0 (su orden arbitrario entraba a la fusión),
  * RRF contaba a los documentos ausentes,
  * el detector de entidades coincidía por subcadena,
  * la regla de «promoción» confundía columnas del reporte individual con promoción,
  * un nombre sintético de las consultas figuraba en los metadatos del corpus (fuga),
y la integridad de los conjuntos de evaluación. Corre con `python3 tests/test_nucleo.py` o con pytest.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from lib import fusion as F
from lib import metrics as M
from lib.etiquetado import es_promocion
from lib.indexes import BM25Index, tokenizar_es
from lib.retrievers import DetectorEntidades, rrf
from lib.stats import holm, permutacion_pareada, rank_biserial_pareado


def _jsonl(ruta):
    return [json.loads(l) for l in (RAIZ / ruta).read_text(encoding="utf-8").splitlines() if l.strip()]


# ------------------------------------------------------------------ texto y BM25
def test_tokenizacion_espanol():
    assert tokenizar_es("Deportistas") == tokenizar_es("deportista")
    assert tokenizar_es("Promoción") == tokenizar_es("promocion")
    assert "de" not in tokenizar_es("reporte de grupos") and "la" not in tokenizar_es("la fase")


def test_bm25_solo_devuelve_score_positivo():
    bm = BM25Index().indexar(["a", "b", "c"], ["deportistas inscritos", "grupos de apoyo", "metas por region"])
    assert bm.buscar("xyzzy inexistente") == []
    res = bm.buscar("grupos")
    assert [d for d, _ in res] == ["b"] and res[0][1] > 0


def test_bm25_idf_a_mano():
    # N=2, el término está en 1 documento: idf = ln(1 + (2-1+0,5)/(1+0,5)) = ln 2
    bm = BM25Index(k1=1.5, b=0.75).indexar(["a", "b"], ["alfa beta", "gamma delta"])
    esperado = math.log(2) * 1 * 2.5 / (1 + 1.5 * (1 - 0.75 + 0.75 * 1))   # f=1, |d|=avgdl
    assert abs(bm.buscar("alfa")[0][1] - esperado) < 1e-9


def test_bm25_desempate_por_doc_id():
    bm = BM25Index().indexar(["b", "a"], ["igual texto", "igual texto"])
    assert [d for d, _ in bm.buscar("igual")] == ["a", "b"]


# ------------------------------------------------------------------ fusión
def test_rrf_ejemplo_del_texto():
    orden, s = rrf([("A", 3), ("B", 2)], [("A", .9), ("B", .8), ("C", .7)], k=60)
    assert abs(s["A"] - 2 / 61) < 1e-12 and abs(s["B"] - (1 / 62 + 1 / 62)) < 1e-12
    assert abs(s["C"] - 1 / 63) < 1e-12 and orden[0] == "A"          # C solo recibe aporte de una lista


def test_rrf_ausente_no_aporta():
    _, s = rrf([], [("A", 1.0), ("B", 0.5)], k=60)
    assert abs(s["A"] - 1 / 61) < 1e-12 and abs(s["B"] - 1 / 62) < 1e-12


def test_rrf_empate_determinista():
    orden, _ = rrf([("B", 2), ("A", 1)], [("A", 2), ("B", 1)], k=60)      # A y B empatan exactamente
    assert orden == ["A", "B"]


def test_fusion_convexa_extremos():
    b, d = {"A": 3.0, "B": 1.0}, {"A": .1, "B": .9, "C": .5}
    ids = ["A", "B", "C"]
    solo_denso = F.convexa(b, d, ids, 1.0)
    assert sorted(ids, key=lambda x: -solo_denso[x]) == ["B", "C", "A"]
    solo_lexico = F.convexa(b, d, ids, 0.0)
    assert sorted(ids, key=lambda x: (-solo_lexico[x], x))[:2] == ["A", "B"]


def test_fusion_compuerta():
    b, d = {"A": 3.0}, {"A": .1, "B": .9}
    assert F.rrf_compuerta(b, d, cobertura=0.2, theta=0.5) == d          # cobertura baja: solo denso
    assert F.rrf_compuerta(b, d, cobertura=0.8, theta=0.5) == F.rrf(b, d, 60)


# ------------------------------------------------------------------ métricas y estadística
def test_ndcg_por_posicion():
    qrel = {"x": 2.0}
    for pos, esperado in ((1, 1.0), (2, 1 / math.log2(3)), (3, 0.5), (10, 1 / math.log2(11))):
        ranking = ["z"] * (pos - 1) + ["x"]
        assert abs(M.ndcg(ranking, qrel, 10) - esperado) < 1e-12
    assert M.ndcg(["z"] * 10 + ["x"], qrel, 10) == 0.0


def test_holm_ejemplo():
    h = holm({"a": 0.0018, "b": 0.0412, "c": 0.1262, "d": 0.3362, "e": 0.6549})
    assert abs(h["a"] - 0.0090) < 1e-4 and abs(h["b"] - 0.1648) < 1e-3
    assert abs(h["d"] - h["e"]) < 1e-12 and abs(h["e"] - 0.6724) < 1e-3     # monotonía


def test_permutacion_exacta():
    assert abs(permutacion_pareada([1, 1, 1], [0, 0, 0])["p_valor"] - 0.25) < 1e-12
    assert abs(permutacion_pareada([1, 0, 5, 3], [0, 0, 4, 4])["p_valor"] - 1.0) < 1e-12
    assert permutacion_pareada([1, 2], [1, 2])["p_valor"] is None


def test_rank_biserial_signo():
    assert rank_biserial_pareado([2, 3, 4], [1, 1, 1]) == 1.0
    assert rank_biserial_pareado([1, 1, 1], [2, 3, 4]) == -1.0


# ------------------------------------------------------------------ etiquetado y detector
def test_regla_promocion():
    assert not es_promocion({"individual_report"}, {"category_name", "current_stage", "status"})
    assert es_promocion({"promotions_log"}, set())
    assert es_promocion(set(), {"estado_promocion"})


def test_detector_palabra_completa():
    det = DetectorEntidades({"clases": {"Grupo": {"sinonimos": ["equipo"]}, "Etapa/Fase": {"sinonimos": ["fase"]}}},
                            ["Caribe"])
    assert "Grupo" not in det.clases_en("el reporte agrupa datos")        # «grupo» dentro de «agrupa»
    assert "Grupo" in det.clases_en("los grupos de la escuela") and "Etapa/Fase" in det.clases_en("las fases")
    assert not det.tiene_nombre_propio("Región Caribe")                   # vocabulario del dominio, no persona


# ------------------------------------------------------------------ integridad de datos (regresión de fuga)
def test_corpus_sin_nombres_sinteticos():
    prohibidos = {"Andrés Torres", "María Restrepo", "Julián Gómez", "Valentina Ríos", "Camilo Duarte", "Laura Ospina",
                  "Sebastián Nieto", "Daniela Córdoba", "Colegio San Marcos", "Club Deportivo El Faro", "Liga Atlántico",
                  "Escuela Nueva Esperanza", "Club Halcones del Norte"}
    blob = (RAIZ / "corpus/corpus_v1.jsonl").read_text(encoding="utf-8")
    blob += (RAIZ.parent / "data/ontologia_suid/metadatos_por_reporte.json").read_text(encoding="utf-8")
    assert not [n for n in prohibidos if n in blob], "un nombre sintético de las consultas figura en el corpus (fuga)"


def test_corpus_sin_pii():
    import re
    for d in _jsonl("corpus/corpus_v1.jsonl"):
        t = json.dumps(d, ensure_ascii=False)
        assert not re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", t, re.I) and not re.search(r"\b\d{7,}\b", t)


def test_conjuntos_integros():
    ids_corpus = {d["id"] for d in _jsonl("corpus/corpus_v1.jsonl")}
    textos_vistos: dict[str, str] = {}
    for nombre, (cq, qr) in {"sintetico": ("datos/consultas_eval.jsonl", "datos/qrels.jsonl"),
                             "ampliado": ("datos/consultas_real_ampliado.jsonl", "datos/qrels_real_ampliado.jsonl"),
                             "dificil": ("datos/consultas_dificil.jsonl", "datos/qrels_dificil.jsonl"),
                             "dificil_b": ("datos/consultas_dificil_b.jsonl", "datos/qrels_dificil_b.jsonl")}.items():
        cons, qrels = _jsonl(cq), {r["id"]: r["relevancia"] for r in _jsonl(qr)}
        assert len({c["id"] for c in cons}) == len(cons), f"{nombre}: ids repetidos"
        for c in cons:
            assert c["id"] in qrels, f"{nombre}: {c['id']} sin qrel"
            assert set(qrels[c["id"]]) <= ids_corpus, f"{nombre}: qrel apunta a un documento inexistente"
        if nombre in ("dificil", "dificil_b"):
            for c in cons:
                assert c["texto"] not in textos_vistos, f"consulta duplicada entre conjuntos difíciles: {c['texto']}"
                textos_vistos[c["texto"]] = nombre


def test_dedupe_ampliado():
    textos = [c["texto"] for c in _jsonl("datos/consultas_real_ampliado.jsonl")]
    assert len(textos) == len(set(textos)), "pseudo-replicación: hay textos repetidos en el conjunto ampliado"


if __name__ == "__main__":
    pruebas = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    fallos = 0
    for n, f in pruebas:
        try:
            f()
            print(f"  ok   {n}")
        except Exception as e:                       # noqa: BLE001
            fallos += 1
            print(f"  FALLA {n}: {type(e).__name__}: {e}")
    print(f"{len(pruebas) - fallos}/{len(pruebas)} pruebas pasan")
    sys.exit(1 if fallos else 0)
