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
        "_ask_llm",
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
        "_ask_llm",
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


def test_chat_answers_general_questions_without_sources(tmp_path, monkeypatch):
    from unittest.mock import patch

    from backend.rag.rag_service import RagService

    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:3001/v1")
    monkeypatch.setenv("LLM_MODEL", "auto")
    service = _service(tmp_path)
    response_body = json.dumps({
        "choices": [{
            "message": {
                "content": "Hallo! Ich kann dir bei allgemeinen Fragen und deinen Wissensquellen helfen.",
            },
        }],
    }).encode("utf-8")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return response_body

    with patch(
        "backend.rag.rag_service.urllib.request.urlopen",
        return_value=FakeResponse(),
    ):
        response = service.chat("Hi, wie kannst du mir helfen?")

    assert response["answer"].startswith("Hallo!")
    assert response["status"] == "conversational"
    assert response["sources"] == []
    assert response["insufficient_information"] is False


def test_llm_request_uses_openai_compatible_endpoint_and_response(monkeypatch):
    from unittest.mock import patch

    from backend.rag.rag_service import RagService

    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:3001/v1")
    monkeypatch.setenv("LLM_MODEL", "provider-model-id")
    service = RagService(api_key="test-api-key")
    answer_payload = json.dumps({
        "answer": "Grounded.",
        "sources": ["facts.json#one"],
        "insufficient_information": False,
    })
    response_body = json.dumps({
        "choices": [{
            "message": {
                "content": f"Here is the answer:\n```json\n{answer_payload}\n```",
            },
        }],
    }).encode("utf-8")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return response_body

    with patch(
        "backend.rag.rag_service.urllib.request.urlopen",
        return_value=FakeResponse(),
    ) as urlopen:
        result = service._ask_llm("Question", {
            "context": "Evidence",
            "sources": [{"citation_id": "facts.json#one"}],
        }, [])

    request = urlopen.call_args.args[0]
    request_body = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "http://localhost:3001/v1/chat/completions"
    assert request.get_header("Authorization") == "Bearer test-api-key"
    assert request_body["model"] == "provider-model-id"
    assert request_body["messages"][0]["role"] == "system"
    assert result["answer"] == "Grounded."


def test_llm_plain_text_is_returned_as_unverified_when_sources_exist(monkeypatch):
    from unittest.mock import patch

    from backend.rag.rag_service import RagService

    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:3001/v1")
    monkeypatch.setenv("LLM_MODEL", "auto")
    service = RagService(api_key="test-api-key")
    answer = "Hallo! Ich kann dir bei allgemeinen Fragen helfen."
    response_body = json.dumps({
        "choices": [{
            "message": {"content": answer},
        }],
    }).encode("utf-8")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return response_body

    with patch(
        "backend.rag.rag_service.urllib.request.urlopen",
        return_value=FakeResponse(),
    ):
        result = service._ask_llm("Question", {
            "context": "Evidence",
            "sources": [{"citation_id": "facts.json#one"}],
        }, [])

    assert result == {
        "answer": answer,
        "sources": [],
        "insufficient_information": True,
    }


def test_llm_requires_a_model_id(monkeypatch):
    from backend.rag.rag_service import RagConfigurationError, RagService

    monkeypatch.delenv("LLM_MODEL", raising=False)
    service = RagService(api_key="test-api-key")

    try:
        service._ask_llm("Question", {"context": "Evidence"}, [])
    except RagConfigurationError as error:
        assert "LLM_MODEL" in str(error)
    else:
        raise AssertionError("Expected missing model configuration to fail")


def test_llm_404_explains_endpoint_and_model_configuration(monkeypatch):
    from urllib.error import HTTPError
    from unittest.mock import patch

    import pytest

    from backend.rag.rag_service import RagConfigurationError, RagService

    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:3001/v1")
    monkeypatch.setenv("LLM_MODEL", "provider-model-id")
    service = RagService(api_key="test-api-key")

    with patch(
        "backend.rag.rag_service.urllib.request.urlopen",
        side_effect=HTTPError("http://localhost:3001/v1/chat/completions", 404, "Not Found", {}, None),
    ):
        with pytest.raises(RagConfigurationError, match="LLM_BASE_URL"):
            service._ask_llm("Question", {"context": "Evidence"}, [])
