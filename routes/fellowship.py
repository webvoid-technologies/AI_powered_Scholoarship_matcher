from flask import Blueprint, request
from routes.helpers import handle_rag_request

fellowship_bp = Blueprint('fellowship', __name__)


@fellowship_bp.route('/match-fellowships', methods=['POST'])
def match_fellowships():
    return handle_rag_request(
        'fellowship',
        'fellowship_prompt',
        request,
        profile_keys=[
            'education_level', 'degree_branch', 'year_of_study',
            'cgpa', 'location', 'career_goal'
        ]
    )
