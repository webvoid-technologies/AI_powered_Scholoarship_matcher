"""Routes for web scraping, embedding generation, and vector store seeding."""

from flask import Blueprint, jsonify, current_app, request
from services.scraper_service import scraper_service, ScraperServiceError
from services.chroma_service import chroma_service, ChromaServiceError, COLLECTION_NAMES
from services.preprocessing_service import preprocessing_service
import json
import os

scraper_bp = Blueprint('scraper', __name__)


def _load_scraped_data(path: str = 'scraped_data/opportunities.json'):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('opportunities', [])


def _seed_collection(category: str, opportunities: list):
    cat_opps = [opp for opp in opportunities if opp.get('category') == category]
    if cat_opps:
        chroma_service.upsert(category, cat_opps)
    return len(cat_opps)


@scraper_bp.route('/scrape', methods=['POST'])
def scrape():
    """Trigger web scraping and save cleaned data to JSON."""
    try:
        body = request.get_json(silent=True) or {}
        # Optionally register custom URLs
        for item in body.get('sources', []):
            scraper_service.register_url(
                item.get('name', 'Custom'),
                item.get('url'),
                item.get('category', 'internships')
            )
        result = scraper_service.run_all(output_dir='scraped_data')
        return jsonify(result)
    except ScraperServiceError as e:
        return jsonify({'success': False, 'error': str(e)}), 502
    except Exception as e:
        current_app.logger.exception('Scrape failed')
        return jsonify({'success': False, 'error': f'Scraping failed: {str(e)}'}), 500


@scraper_bp.route('/generate-embeddings', methods=['POST'])
def generate_embeddings():
    """Generate embeddings from scraped data and populate ChromaDB collections."""
    try:
        opportunities = _load_scraped_data()
        if not opportunities:
            # Seed with built-in sample data if no scraped file exists
            from services.scraper_service import load_builtin_samples
            opportunities = preprocessing_service.process(load_builtin_samples())

        stats = {}
        for category in COLLECTION_NAMES:
            stats[category] = _seed_collection(category, opportunities)

        return jsonify({
            'success': True,
            'message': 'Embeddings generated and stored in ChromaDB.',
            'stats': stats,
            'total': sum(stats.values())
        })
    except ChromaServiceError as e:
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        current_app.logger.exception('Embedding generation failed')
        return jsonify({'success': False, 'error': f'Embedding generation failed: {str(e)}'}), 500


@scraper_bp.route('/vector-store-stats', methods=['GET'])
def vector_store_stats():
    """Return counts of documents in each ChromaDB collection."""
    try:
        stats = chroma_service.stats()
        return jsonify({'success': True, 'stats': stats})
    except ChromaServiceError as e:
        return jsonify({'success': False, 'error': str(e)}), 503
