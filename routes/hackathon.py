from flask import Blueprint, request
from routes.helpers import handle_rag_request

hackathon_bp = Blueprint('hackathon', __name__)


@hackathon_bp.route('/match-hackathons', methods=['POST'])
def match_hackathons():
    return handle_rag_request(
        'hackathon',
        'hackathon_prompt',
        request,
        profile_keys=[
            'education_level', 'degree_branch', 'year_of_study', 'career_goal'
        ]
    )
