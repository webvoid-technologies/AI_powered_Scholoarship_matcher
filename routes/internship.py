from flask import Blueprint, request
from routes.helpers import handle_rag_request

internship_bp = Blueprint('internship', __name__)


@internship_bp.route('/match-internships', methods=['POST'])
def match_internships():
    return handle_rag_request(
        'internship',
        'internship_prompt',
        request,
        profile_keys=[
            'education_level', 'degree_branch', 'year_of_study',
            'cgpa', 'career_goal'
        ]
    )
