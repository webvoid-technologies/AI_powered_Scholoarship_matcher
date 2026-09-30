"""Semantic search endpoint across ChromaDB collections."""

from flask import Blueprint, jsonify, request, current_app
from services.chroma_service import chroma_service, ChromaServiceError, COLLECTION_NAMES

search_bp = Blueprint('search', __name__)


@search_bp.route('/search', methods=['GET', 'POST'])
def search():
    """Semantic search across all opportunity collections with optional metadata filters."""
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
    else:
        data = request.args.to_dict()

    query = (data.get('q') or data.get('query') or '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter is required.'}), 400

    categories = data.get('categories') or COLLECTION_NAMES
    if isinstance(categories, str):
        categories = [c.strip() for c in categories.split(',')]

    top_k = int(data.get('top_k', 5))

    # Build ChromaDB where filter from supported metadata keys
    where = {}
    for key in ('country', 'degree', 'organization', 'category'):
        value = data.get(key)
        if value:
            where[key] = value
    if data.get('deadline'):
        where['deadline'] = data.get('deadline')

    try:
        results = {}
        for category in categories:
            matches = chroma_service.search(
                category=category,
                query=query,
                top_k=top_k,
                where=where if where else None
            )
            if matches:
                results[category] = matches

        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total': sum(len(v) for v in results.values())
        })
    except ChromaServiceError as e:
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        current_app.logger.exception('Search failed')
        return jsonify({'success': False, 'error': f'Search failed: {str(e)}'}), 500
