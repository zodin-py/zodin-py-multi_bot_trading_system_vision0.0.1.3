"""RAG API endpoints for the backend Flask application."""

from flask import Blueprint, request, jsonify
from backend.rag.rag_service import RagService
from backend.rag.rag_config import RagConfig
import logging

logger = logging.getLogger(__name__)

rag_bp = Blueprint("rag", __name__, url_prefix="/api/rag")


def _get_service() -> RagService:
    """Get or create a RagService instance configured from the default config."""
    config = RagConfig()
    return RagService(config=config)


@rag_bp.route("/chat", methods=["POST"])
def rag_chat():
    """POST /api/rag/chat - Chat with RAG grounding."""
    try:
        data = request.get_json()
        if not data or "question" not in data:
            return jsonify({
                "status": "error",
                "message": "Frage-Parameter erforderlich"
            }), 400

        question = data["question"]
        top_k = data.get("top_k", 5)

        service = _get_service()
        response = service.chat(question=question, top_k=top_k)

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"RAG chat error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@rag_bp.route("/search", methods=["POST"])
def rag_search():
    """POST /api/rag/search - Search the knowledge base."""
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({
                "status": "error",
                "message": "Query-Parameter erforderlich"
            }), 400

        query = data["query"]
        top_k = data.get("top_k", 10)

        service = _get_service()
        response = service.search(query=query, top_k=top_k)

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@rag_bp.route("/status", methods=["GET"])
def rag_status():
    """GET /api/rag/status - Get RAG system status."""
    try:
        service = _get_service()
        info = service.get_system_info()

        # Add build state
        build_info = {
            "is_built": service._is_built,
            "num_documents": len(service._documents) if service._documents else 0,
            "num_chunks": len(service._documents) if service._documents else 0,
            "source_files": [src["source_file"] for src in service.get_sources()],
        }

        return jsonify({
            "status": "success",
            "configured": service.api_key_configured,
            "embedding_model": service.embedding_service.model,
            "build": build_info,
        }), 200

    except Exception as e:
        logger.error(f"RAG status error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@rag_bp.route("/sync", methods=["POST"])
def rag_sync():
    """POST /api/rag/sync - Force rebuild of the knowledge index."""
    try:
        data = request.get_json() or {}
        force = data.get("force", False)

        service = _get_service()
        result = service.build_indices(force_rebuild=force)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"RAG sync error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@rag_bp.route("/sources", methods=["GET"])
def rag_sources():
    """GET /api/rag/sources - List knowledge source files."""
    try:
        service = _get_service()
        sources = service.get_sources()

        return jsonify({
            "status": "success",
            "sources": sources,
        }), 200

    except Exception as e:
        logger.error(f"RAG sources error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@rag_bp.route("/analysis/<request_id>", methods=["GET"])
def rag_analysis(request_id: str):
    """GET /api/rag/analysis/{request_id} - Get retrieval analysis."""
    try:
        service = _get_service()
        analysis = service.get_analysis(request_id)

        if analysis is None:
            return jsonify({
                "status": "not_found",
                "message": "Analyse nicht gefunden"
            }), 404

        return jsonify({
            "status": "success",
            "analysis": analysis,
        }), 200

    except Exception as e:
        logger.error(f"RAG analysis error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500