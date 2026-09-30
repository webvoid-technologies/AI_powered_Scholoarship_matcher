from flask import jsonify, current_app
from services.groq_service import GroqService, GroqServiceError
from services.rag_service import RAGService
from services.validation import validate_profile, normalize_profile


def handle_module_request(module_name, prompt_name, request, profile_keys=None):
    """Generic handler for matcher endpoints with optional RAG fallback."""
    data = request.get_json(silent=True) or {}
    data = normalize_profile(data)
    valid, error = validate_profile(data)
    if not valid:
        return jsonify({'success': False, 'error': error}), 400

    config = current_app.config
    use_rag = config.get('ENABLE_RAG', True)
    kwargs = {key: data.get(key) for key in (profile_keys or [])}
    for key in ('skills', 'interests'):
        if key not in kwargs:
            kwargs[key] = data.get(key, [])

    if use_rag:
        try:
            rag = RAGService()
            result = rag.generate(prompt_name, profile=data)
            result.setdefault('module', module_name)
            result.setdefault('rag', True)
            return jsonify(result)
        except Exception:
            # Fall through to direct LLM if RAG fails
            pass

    service = GroqService()
    try:
        result = service.generate(prompt_name, **kwargs)
        result.setdefault('module', module_name)
        result.setdefault('rag', False)
        return jsonify(result)
    except GroqServiceError as e:
        if not service.api_key:
            result = service.generate_mock(prompt_name, **kwargs)
            result.setdefault('module', module_name)
            result.setdefault('rag', False)
            result.setdefault('mock', True)
            return jsonify(result)
        return jsonify({'success': False, 'error': str(e)}), 502


def handle_rag_request(module_name, prompt_name, request, profile_keys=None):
    """Explicit RAG handler that fails gracefully when vector store is unavailable."""
    data = request.get_json(silent=True) or {}
    data = normalize_profile(data)
    valid, error = validate_profile(data)
    if not valid:
        return jsonify({'success': False, 'error': error}), 400

    rag = RAGService()
    try:
        result = rag.generate(prompt_name, profile=data)
        result.setdefault('module', module_name)
        result.setdefault('rag', True)
        return jsonify(result)
    except Exception as exc:
        current_app.logger.warning(f'RAG failed for {module_name}: {exc}')
        return jsonify({'success': False, 'error': f'Retrieval failed: {str(exc)}'}), 503
