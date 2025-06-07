import os
import numpy as np
from typing import List

try:
    import openai  # type: ignore
except Exception:  # pragma: no cover - optional
    openai = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    _model = None
else:
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:  # pragma: no cover - optional
        _model = None


def embed_text(text: str) -> List[float]:
    if openai and OPENAI_API_KEY:
        resp = openai.Embedding.create(input=[text], model='text-embedding-ada-002')
        return resp['data'][0]['embedding']
    if _model:
        return _model.encode([text])[0].tolist()
    raise RuntimeError('No embedding backend available')


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
