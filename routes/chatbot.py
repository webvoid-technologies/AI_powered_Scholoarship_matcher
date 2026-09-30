"""RAG-powered chatbot route."""

from flask import Blueprint, jsonify, request, current_app
from services.rag_service import RAGService, RAGServiceError
from services.validation import normalize_profile

chatbot_bp = Blueprint('chatbot', __name__)


@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """Chatbot endpoint that uses RAG to answer opportunity-related questions."""
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or data.get('question') or '').strip()
    if not message:
        return jsonify({'success': False, 'error': 'Message is required.'}), 400

    profile = normalize_profile(data.get('profile') or {})
    history = data.get('history') or []
    categories = data.get('categories')
    top_k = data.get('top_k', 5)

    try:
        rag = RAGService()
        result = rag.chat(
            message=message,
            history=history,
            profile=profile,
            categories=categories,
            top_k=top_k
        )
        result.setdefault('module', 'chatbot')
        result.setdefault('rag', True)
        return jsonify(result)
    except RAGServiceError as e:
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        current_app.logger.exception('Chat failed')
        return jsonify({'success': False, 'error': f'Chat failed: {str(e)}'}), 500
