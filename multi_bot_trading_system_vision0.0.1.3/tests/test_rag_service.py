import json

from backend.rag.rag_config import RagConfig
from backend.rag.rag_service import RagService


def _service(tmp_path):
    config = RagConfig.from_dict({
        "json_files_dir": tmp_path,
        "chunk_size": 1000,
        "chunk_overlap": 100,
        "embedding_dimensions": 128,
        "max_context_tokens": 1000,
    })
    return RagService(config=config, api_key="test-api-key")


def _write_source(path, records):
    path.write_text(json.dumps(records), encoding="utf-8")


def test_builds_multiple_json_sources_and_returns_hybrid_analysis(tmp_path):
    _write_source(
        tmp_path / "markets.json",
        [
            {"id": "btc", "title": "Bitcoin", "text": "Bitcoin spot market history."},
            {"id": "eth", "title": "Ethereum", "text": "Ethereum network history."},
        ],
    )
    _write_source(
        tmp_path / "rules.json",
        [{"id": "risk", "text": "Risk limits must protect trading capital."}],
    )
    service = _service(tmp_path)

    build = service.build_indices()
    result = service.search("Bitcoin spot market", top_k=3)

    assert build["status"] == "success"
    assert set(build["source_files"]) == {"markets.json", "rules.json"}
    assert result["status"] == "success"
    assert result["sources"][0]["citation_id"] == "markets.json#btc"
    assert result["analysis"]["keyword_results"][0]["record_id"] == "btc"
    assert result["analysis"]["vector_results"]
    assert result["analysis"]["combined_results"][0]["record_id"] == "btc"
    assert result["analysis"]["context_documents"][0]["source_file"] == "markets.json"


def test_invalid_source_does_not_replace_the_active_index(tmp_path):
    source = tmp_path / "market.json"
    _write_source(source, [{"id": "safe", "text": "The original trusted record."}])
    service = _service(tmp_path)
    service.build_indices()
    source.write_text("{invalid json", encoding="utf-8")

    sync = service.build_indices()
    result = service.search("original trusted record")

    assert sync["status"] == "invalid_data"
    assert sync["invalid_files"] == ["market.json"]
    assert result["sources"][0]["record_id"] == "safe"


def test_chat_accepts_only_citations_from_retrieved_records(tmp_path, monkeypatch):
    _write_source(
        tmp_path / "market.json",
        [{"id": "bitcoin", "text": "Bitcoin is a digital asset."}],
    )
    service = _service(tmp_path)
    service.build_indices()
    monkeypatch.setattr(
        service,
        "_ask_claude",
        lambda question, search, history: {
            "answer": "Bitcoin is described as a digital asset.",
            "sources": ["market.json#bitcoin"],
            "insufficient_information": False,
        },
    )

    response = service.chat("What is Bitcoin?")
    analysis = service.get_analysis(response["request_id"])

    assert response["status"] == "grounded"
    assert response["sources"][0]["citation_id"] == "market.json#bitcoin"
    assert analysis["response"]["answer"] == response["answer"]
    assert analysis["context_documents"][0]["record_id"] == "bitcoin"


def test_chat_downgrades_unrecognized_citations_to_insufficient(tmp_path, monkeypatch):
    _write_source(
        tmp_path / "market.json",
        [{"id": "bitcoin", "text": "Bitcoin is a digital asset."}],
    )
    service = _service(tmp_path)
    service.build_indices()
    monkeypatch.setattr(
        service,
        "_ask_claude",
        lambda question, search, history: {
            "answer": "Unsupported claim.",
            "sources": ["other.json#missing"],
            "insufficient_information": False,
        },
    )

    response = service.chat("What is Bitcoin?")

    assert response["status"] == "insufficient_information"
    assert response["sources"] == []
    assert response["insufficient_information"] is True
