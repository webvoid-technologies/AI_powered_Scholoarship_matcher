from flask import Blueprint, request
from routes.helpers import handle_rag_request

scholarship_bp = Blueprint('scholarship', __name__)


@scholarship_bp.route('/match-scholarships', methods=['POST'])
def match_scholarships():
    return handle_rag_request(
        'scholarship',
        'scholarship_prompt',
        request,
        profile_keys=[
            'education_level', 'degree_branch', 'year_of_study',
            'cgpa', 'location', 'career_goal'
        ]
    )
