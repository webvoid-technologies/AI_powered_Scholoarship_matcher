from flask import Blueprint, request
from routes.helpers import handle_module_request

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/analyze-profile', methods=['POST'])
def analyze_profile():
    return handle_module_request(
        'profile',
        'profile_prompt',
        request,
        profile_keys=[
            'full_name', 'education_level', 'degree_branch', 'year_of_study',
            'cgpa', 'college_name', 'location', 'career_goal'
        ]
    )
