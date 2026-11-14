---
name: rag-module-setup
description: RAG module integrated into multi-bot trading system backend
metadata:
  type: project
---

## RAG Module Integration Complete

The **Spect** RAG Copilot specification has been extracted and integrated as a proper LLM component within the multi-bot trading system.

### New Module Structure

Created `backend/rag/` with the following modules:

| File | Purpose |
|------|---------|
| `rag_config.py` | Central configuration for RAG system settings |
| `data_loader.py` | Loads and validates JSON knowledge base files |
| `data_validator.py` | Validates JSON data integrity before indexing |
| `embedding_service.py` | Creates embeddings via Anthropic Claude API |
| `keyword_search.py` | BM25 keyword search implementation |
| `vector_search.py` | Semantic vector search using cosine similarity |
| `hybrid_retriever.py` | Combines BM25 + vector search via RRF |
| `__init__.py` | Module exports |
| `rag_service.py` | Main orchestrator service |

### Backend Integration

- Updated `backend/api_only.py` to integrate RAG service
- Added three new API endpoints:
  - `GET /api/rag/status` - System status check
  - `POST /api/rag/indices` - Build indices from JSON data
  - `POST /api/rag/search` - Search with query and return context

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rag/status` | GET | Returns RAG system readiness and config |
| `/api/rag/indices` | POST | Builds BM25 + vector indices from JSON files |
| `/api/rag/search` | POST | Searches with natural language query, returns results + context |

### How It Works

1. **Data Loading**: JSON files are loaded from `data/json_files/` directory
2. **Validation**: Each document is validated for required content fields
3. **Chunking**: Text is split into overlapping chunks (default: 512 tokens, 50 overlap)
4. **Embedding**: Each chunk gets an embedding via Anthropic `text-embedding-3-small`
5. **Indexing**: Two indices built simultaneously:
   - BM25 keyword index for fast keyword matching
   - Vector index for semantic similarity search
6. **Hybrid Retrieval**: Uses Reciprocal Rank Fusion (RRF) to combine both results
7. **Context Generation**: Returns top-k results with source metadata for Claude prompting

### Configuration

Default settings from `rag_config.py`:
- Embedding model: `text-embedding-3-small`
- Chunk size: 512 tokens
- Chunk overlap: 50 tokens
- Max context tokens: 8000
- Similarity threshold: 0.7
- Max documents per query: 10

### Usage Example

```python
from backend.rag import RagService, default_config

rag = RagService(config=default_config)
result = rag.build_indices()
# Or search:
result = rag.search("What is the best crypto to buy?", top_k=5)
```

### Next Steps

1. Place JSON knowledge base files in `backend/data/json_files/`
2. Set `ANTHROPIC_API_KEY` environment variable
3. Run `POST /api/rag/indices` to build the search indices
4. Use `POST /api/rag/search` to query the RAG system