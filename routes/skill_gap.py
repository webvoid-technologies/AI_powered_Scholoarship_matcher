from flask import Blueprint, request
from routes.helpers import handle_rag_request

skill_gap_bp = Blueprint('skill_gap', __name__)


@skill_gap_bp.route('/skill-gap', methods=['POST'])
def skill_gap():
    return handle_rag_request(
        'skill_gap',
        'skill_gap_prompt',
        request,
        profile_keys=[
            'education_level', 'degree_branch', 'year_of_study',
            'cgpa', 'career_goal'
        ]
    )
