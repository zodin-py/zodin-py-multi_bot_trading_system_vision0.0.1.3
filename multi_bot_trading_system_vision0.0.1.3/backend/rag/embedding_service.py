"""Dependency-free local vectorizer for the RAG knowledge base.

This feature-hashing vectorizer is intentionally local; it does not call an
unsupported Claude embeddings endpoint or send knowledge-base content elsewhere.
"""

import hashlib
import re
from typing import Dict, List, Optional

import numpy as np
from .rag_config import default_config


class EmbeddingService:
    """Create normalized feature-hashing vectors from words and character n-grams."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
    ):
        self.model = model or default_config.embedding_model
        self.dimensions = dimensions or default_config.embedding_dimensions
        self._cache: Dict[str, np.ndarray] = {}

    def create_embedding(self, text: str) -> np.ndarray:
        if text in self._cache:
            return self._cache[text]

        vector = np.zeros(self.dimensions, dtype=np.float32)
        normalized = re.sub(r"\s+", " ", text.casefold()).strip()
        features: List[tuple[str, float]] = []
        words = re.findall(r"\w+", normalized, flags=re.UNICODE)

        for word in words:
            if len(word) > 1:
                features.append((f"w:{word}", 1.0))
            padded = f"^{word}$"
            for size in (3, 4):
                features.extend(
                    (f"n:{padded[index:index + size]}", 0.25)
                    for index in range(max(0, len(padded) - size + 1))
                )

        for feature, weight in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            number = int.from_bytes(digest, "little")
            index = number % self.dimensions
            sign = 1.0 if number & (1 << 63) else -1.0
            vector[index] += sign * weight

        magnitude = float(np.linalg.norm(vector))
        if magnitude:
            vector /= magnitude
        self._cache[text] = vector
        return vector

    def create_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        return [self.create_embedding(text) for text in texts]

    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> List[str]:
        size = chunk_size or default_config.chunk_size
        overlap = chunk_overlap or default_config.chunk_overlap
        if size < 1 or overlap < 0 or overlap >= size:
            raise ValueError("chunk size must be positive and overlap smaller than size")
        if len(text) <= size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            chunks.append(text[start:end])
            if end == len(text):
                break
            start = end - overlap
        return chunks

    def preprocess_document(self, document: dict) -> List[dict]:
        text = document.get("text", document.get("content", str(document)))
        title = document.get("title", document.get("filename", "unknown"))
        chunks = self.chunk_text(str(text))
        return [
            {
                "chunk_index": index,
                "text": chunk,
                "embedding": self.create_embedding(chunk),
                "metadata": {
                    "source": title,
                    "chunk_id": f"{title}_chunk_{index}",
                },
            }
            for index, chunk in enumerate(chunks)
        ]
