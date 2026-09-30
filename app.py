import os
from flask import Flask, render_template
from config import Config
from routes.profile import profile_bp
from routes.scholarship import scholarship_bp
from routes.internship import internship_bp
from routes.hackathon import hackathon_bp
from routes.fellowship import fellowship_bp
from routes.certification import certification_bp
from routes.skill_gap import skill_gap_bp
from routes.career_report import career_report_bp
from routes.scraper import scraper_bp
from routes.chatbot import chatbot_bp
from routes.search import search_bp


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static'
    )
    app.config.from_object(config_class)

    # Matcher blueprints
    app.register_blueprint(profile_bp, url_prefix='/api')
    app.register_blueprint(scholarship_bp, url_prefix='/api')
    app.register_blueprint(internship_bp, url_prefix='/api')
    app.register_blueprint(hackathon_bp, url_prefix='/api')
    app.register_blueprint(fellowship_bp, url_prefix='/api')
    app.register_blueprint(certification_bp, url_prefix='/api')
    app.register_blueprint(skill_gap_bp, url_prefix='/api')
    app.register_blueprint(career_report_bp, url_prefix='/api')

    # RAG / scraper / chatbot blueprints
    app.register_blueprint(scraper_bp, url_prefix='/api')
    app.register_blueprint(chatbot_bp, url_prefix='/api')
    app.register_blueprint(search_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return render_template(
            'index.html',
            app_name=app.config.get('APP_NAME'),
            company_name=app.config.get('COMPANY_NAME'),
            support_email=app.config.get('SUPPORT_EMAIL')
        )

    @app.errorhandler(404)
    def not_found(error):
        return {'success': False, 'error': 'Endpoint not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'success': False, 'error': 'Internal server error'}, 500

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = app.config.get('FLASK_DEBUG', True)
    app.run(host='0.0.0.0', port=port, debug=debug)
