from flask import Blueprint, request
from routes.helpers import handle_rag_request

career_report_bp = Blueprint('career_report', __name__)


@career_report_bp.route('/career-report', methods=['POST'])
def career_report():
    return handle_rag_request(
        'career_report',
        'career_report_prompt',
        request,
        profile_keys=[
            'education_level', 'degree_branch', 'year_of_study',
            'cgpa', 'location', 'career_goal'
        ]
    )
