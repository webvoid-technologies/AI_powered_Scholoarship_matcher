from flask import Blueprint, request
from routes.helpers import handle_rag_request

certification_bp = Blueprint('certification', __name__)


@certification_bp.route('/match-certifications', methods=['POST'])
def match_certifications():
    return handle_rag_request(
        'certification',
        'certification_prompt',
        request,
        profile_keys=[
            'education_level', 'degree_branch', 'year_of_study', 'career_goal'
        ]
    )
