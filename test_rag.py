"""Test script for RAG system with new JSON data files."""
import sys
sys.path.insert(0, 'multi_bot_trading_system_vision0.0.1.3')

from backend.rag.rag_config import RagConfig
from backend.rag.rag_service import RagService

config = RagConfig.from_dict({
    'json_files_dir': 'multi_bot_trading_system_vision0.0.1.3/backend/data/json_files',
    'chunk_size': 1800,
    'chunk_overlap': 200,
    'embedding_dimensions': 128,
    'max_context_tokens': 8000,
})

service = RagService(config=config, api_key='test-key')

# Build the index
print('Building indices...')
build = service.build_indices()
print(f'Build status: {build["status"]}')
print(f'Num documents: {build["num_documents"]}')
print(f'Num chunks: {build["num_chunks"]}')
print(f'Source files: {build["source_files"]}')

# Search
print()
print('Searching for Bitcoin...')
result = service.search('Bitcoin', top_k=3)
print(f'Search status: {result["status"]}')
print(f'Num results: {result["num_results"]}')
print(f'Context length: {result["analysis"]["context_characters"]}')

for i, src in enumerate(result['sources']):
    print(f'  Source {i+1}: {src["source_file"]} - record_id: {src["record_id"]}')

print()
print('Analysis:')
analysis = result['analysis']
print(f'  Keyword results: {len(analysis["keyword_results"])}')
print(f'  Vector results: {len(analysis["vector_results"])}')
print(f'  Combined results: {len(analysis["combined_results"])}')
print(f'  Context documents: {len(analysis["context_documents"])}')

# Test chat
print()
print('Testing chat...')
chat = service.chat('Was ist Bitcoin?', top_k=3)
print(f'Chat status: {chat["status"]}')
print(f'Answer: {chat.get("answer", "N/A")}')
print(f'Sources: {chat.get("sources", [])}')
print(f'Insufficient info: {chat.get("insufficient_information", "N/A")}')