from unittest.mock import patch

import numpy as np

from backend.rag.vector_search import VectorSearch


def _api_only_module():
    with patch("backend.services.price_service.PriceService.start"):
        from backend import api_only
    return api_only


def test_rag_api_exposes_sync_sources_chat_and_analysis(monkeypatch):
    api_only = _api_only_module()
    service = api_only.rag_service
    citation = {
        "source_file": "facts.json",
        "record_id": "fact-1",
        "citation_id": "facts.json#fact-1",
    }
    monkeypatch.setattr(service, "build_indices", lambda: {
        "status": "success",
        "message": "Knowledge index updated",
        "num_documents": 1,
        "num_chunks": 1,
        "source_files": ["facts.json"],
    })
    monkeypatch.setattr(service, "get_sources", lambda: [{
        "source_file": "facts.json",
        "record_count": 1,
    }])
    monkeypatch.setattr(service, "chat", lambda question, top_k, history: {
        "request_id": "request-1",
        "answer": "Grounded response.",
        "status": "grounded",
        "sources": [citation],
        "insufficient_information": False,
    })
    monkeypatch.setattr(service, "get_analysis", lambda request_id: {
        "request_id": request_id,
        "query": "Question",
        "search_query": "Question",
    })
    client = api_only.app.test_client()

    sync = client.post("/api/rag/sync", json={})
    sources = client.get("/api/rag/sources")
    chat = client.post("/api/rag/chat", json={
        "question": "Question",
        "history": [],
        "top_k": 5,
    })
    analysis = client.get("/api/rag/analysis/request-1")

    assert sync.status_code == 200
    assert sync.get_json()["success"] is True
    assert sources.get_json()["sources"][0]["source_file"] == "facts.json"
    assert chat.get_json()["sources"] == [citation]
    assert analysis.get_json()["analysis"]["request_id"] == "request-1"


def test_rag_status_includes_vector_statistics(monkeypatch):
    api_only = _api_only_module()
    service = api_only.rag_service
    monkeypatch.setattr(service, "_vector_search", VectorSearch(
        embeddings=np.array([[1.0, 0.0], [0.0, 1.0]]),
        index_data=[{}, {}],
    ))

    response = api_only.app.test_client().get("/api/rag/status")

    assert response.status_code == 200
    assert response.get_json()["system_info"]["vector_stats"] == {
        "num_vectors": 2,
        "embedding_dimension": 2,
    }


def test_rag_chat_rejects_invalid_history():
    api_only = _api_only_module()

    response = api_only.app.test_client().post(
        "/api/rag/chat",
        json={"question": "Question", "history": [{"role": "system", "content": "x"}]},
    )

    assert response.status_code == 400
    assert "history" in response.get_json()["error"]
