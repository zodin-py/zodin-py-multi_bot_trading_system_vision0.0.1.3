"""Configuration for the locally indexed RAG knowledge base."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

BACKEND_DIR = Path(__file__).resolve().parents[1]


class RagConfig:
    """Configuration class for RAG system settings."""

    def __init__(self, config_path: Optional[str] = None):
        self.embedding_model = "local-hash-ngram-v1"
        self.embedding_dimensions = 128
        self.chunk_size = 1800
        self.chunk_overlap = 200
        self.max_context_tokens = 8000
        self.similarity_threshold = 0.0
        self.keyword_weight = 0.5
        self.vector_weight = 0.5
        self.max_documents_per_query = 10
        self.cache_ttl_seconds = 300
        self.data_dir = BACKEND_DIR / "data"
        self.index_dir = self.data_dir / "rag_index"
        self.json_files_dir = self.data_dir / "json_files"

        if config_path and Path(config_path).is_file():
            with open(config_path, "r", encoding="utf-8") as file:
                self._update_from_dict(json.load(file))

    def _update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "max_context_tokens": self.max_context_tokens,
            "similarity_threshold": self.similarity_threshold,
            "keyword_weight": self.keyword_weight,
            "vector_weight": self.vector_weight,
            "max_documents_per_query": self.max_documents_per_query,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "json_files_dir": str(self.json_files_dir),
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RagConfig":
        config = cls()
        config._update_from_dict(config_dict)
        return config


default_config = RagConfig()
