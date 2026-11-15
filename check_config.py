"""Check RAG configuration."""
import sys
sys.path.insert(0, 'multi_bot_trading_system_vision0.0.1.3')

from backend.rag.rag_config import default_config

print('json_files_dir:', default_config.json_files_dir)
print('data_dir:', default_config.data_dir)
print('embedding_model:', default_config.embedding_model)
print('chunk_size:', default_config.chunk_size)
print('chunk_overlap:', default_config.chunk_overlap)
print('max_context_tokens:', default_config.max_context_tokens)
print('similarity_threshold:', default_config.similarity_threshold)
print('keyword_weight:', default_config.keyword_weight)
print('vector_weight:', default_config.vector_weight)
print('max_documents_per_query:', default_config.max_documents_per_query)
print('cache_ttl_seconds:', default_config.cache_ttl_seconds)