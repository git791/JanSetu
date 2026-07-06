"""
Vertex AI text embeddings wrapper.

Uses `text-multilingual-embedding-002` for semantic similarity.
Falls back to a deterministic hash-based pseudo-embedding (via numpy) when
Vertex AI is not configured — enabling local runs without GCP credentials.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
_EMBEDDING_DIM = 768          # dimension of text-multilingual-embedding-002
_FALLBACK_DIM = 256           # dimension of hash fallback embedding

_VERTEX_AVAILABLE = False
_vertex_model = None


def _init_vertex() -> None:
    global _VERTEX_AVAILABLE, _vertex_model

    if not _PROJECT:
        logger.warning("GOOGLE_CLOUD_PROJECT not set — Vertex AI embeddings using hash fallback.")
        return

    try:
        import vertexai  # type: ignore
        from vertexai.language_models import TextEmbeddingModel  # type: ignore

        vertexai.init(project=_PROJECT, location=_LOCATION)
        _vertex_model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")
        _VERTEX_AVAILABLE = True
        logger.info("Vertex AI Embeddings initialised (text-multilingual-embedding-002).")
    except Exception as exc:
        logger.warning("Failed to init Vertex AI embeddings: %s — using hash fallback.", exc)


_init_vertex()


# ── Public API ────────────────────────────────────────────────────────────────

async def get_embedding(text: str) -> list[float]:
    """
    Return a floating-point embedding vector for *text*.

    If Vertex AI is available, uses `text-multilingual-embedding-002` (768-d).
    Otherwise returns a deterministic 256-d hash-based pseudo-embedding that is
    consistent across calls and still supports cosine similarity comparisons for
    local development / testing.
    """
    if not text or not text.strip():
        dim = _EMBEDDING_DIM if _VERTEX_AVAILABLE else _FALLBACK_DIM
        return [0.0] * dim

    if _VERTEX_AVAILABLE and _vertex_model is not None:
        try:
            embeddings = _vertex_model.get_embeddings([text])
            return embeddings[0].values
        except Exception as exc:
            logger.error("Vertex AI get_embedding error: %s — falling back.", exc)

    return _hash_embedding(text)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Compute cosine similarity between two embedding vectors.
    Returns a float in [-1, 1].  Returns 0.0 if either vector is zero.
    """
    if not a or not b or len(a) != len(b):
        return 0.0

    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)

    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(np.dot(va, vb) / (norm_a * norm_b))


# ── Private helpers ───────────────────────────────────────────────────────────

def _hash_embedding(text: str, dim: int = _FALLBACK_DIM) -> list[float]:
    """
    Deterministic pseudo-embedding via repeated SHA-256 hashing.

    Not semantically meaningful but is consistent — the same text always
    produces the same vector, so cosine similarity at least distinguishes
    very different strings from identical ones.
    """
    text_bytes = text.lower().strip().encode("utf-8")
    raw: list[float] = []
    seed = text_bytes
    while len(raw) < dim:
        digest = hashlib.sha256(seed).digest()
        seed = digest
        # Convert each byte to a signed float in [-1, 1]
        for byte in digest:
            raw.append((byte / 127.5) - 1.0)

    vec = np.asarray(raw[:dim], dtype=np.float64)
    # L2-normalise
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def compute_centroid(embeddings: list[list[float]]) -> list[float]:
    """
    Compute the mean (centroid) of a list of embedding vectors.
    Returns a zero vector if the list is empty.
    """
    if not embeddings:
        dim = _EMBEDDING_DIM if _VERTEX_AVAILABLE else _FALLBACK_DIM
        return [0.0] * dim

    mat = np.asarray(embeddings, dtype=np.float64)
    centroid = mat.mean(axis=0)
    norm = np.linalg.norm(centroid)
    if norm > 0:
        centroid = centroid / norm
    return centroid.tolist()
