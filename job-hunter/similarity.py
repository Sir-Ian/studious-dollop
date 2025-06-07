import os
import numpy as np
from typing import List

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:
    import openai
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
except Exception:  # pragma: no cover - optional
    openai = None

try:
    from sentence_transformers import SentenceTransformer
    _model = (
        SentenceTransformer('all-MiniLM-L6-v2')
        if not OPENAI_API_KEY or openai is None
        else None
    )
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
