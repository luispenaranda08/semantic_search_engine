"""R4 (3.ª revisión): compara los vectores de pasaje que calculó la implementación en Rust (Candle)
para los 811 documentos del corpus v3 (lince/indice_tesis/denso.f32) con los de la implementación
de investigación en Python (sentence-transformers), con los mismos pesos y la tarea retrieval.passage."""
import json, sys
from pathlib import Path
import numpy as np
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from lib.banco import cargar_config
from lib.encoders import construir_encoder

def fnv(t):
    h = 0xcbf29ce484222325
    for b in t.encode("utf-8"):
        h ^= b; h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h

L = RAIZ.parent / "lince" / "indice_tesis"
hs = np.fromfile(L / "huellas.u64", dtype="<u8")
V = np.fromfile(L / "denso.f32", dtype="<f4").reshape(len(hs), -1)
rust = {int(h): V[i] for i, h in enumerate(hs)}
docs = [json.loads(l) for l in (RAIZ / "corpus/corpus_v3.jsonl").read_text().splitlines() if l.strip()]
textos = [d["texto_indexable"] for d in docs]
enc = construir_encoder(cargar_config(), textos)
P = np.asarray(enc.encode_documentos(textos), dtype=np.float32)
pares = [(rust[fnv(t)], P[i]) for i, t in enumerate(textos) if fnv(t) in rust]
R = np.stack([a for a, _ in pares]); Q = np.stack([b for _, b in pares])
R /= np.linalg.norm(R, axis=1, keepdims=True); Q /= np.linalg.norm(Q, axis=1, keepdims=True)
cos = (R * Q).sum(1); err = np.abs(R - Q).max()
out = {"documentos": len(pares), "coseno_min": float(cos.min()), "coseno_medio": float(cos.mean()), "error_abs_max": float(err)}
print(out)
(RAIZ / "rerun_boot10k" / "verificacion_rust_python.json").write_text(json.dumps(out, indent=2))
