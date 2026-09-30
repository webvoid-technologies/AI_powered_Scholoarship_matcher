import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-for-poc')

    # Groq API
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    GROQ_MODEL = os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b')
    GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '60'))
    MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '4096'))
    TEMPERATURE = float(os.environ.get('TEMPERATURE', '0.7'))

    # Application branding
    APP_NAME = os.environ.get('APP_NAME', 'AI Scholarship & Opportunity Matcher')
    COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Webvoid Technologies')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'studentprogram@webvoidtechnologies.com')

    # Vector database
    CHROMA_PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR', 'chroma_db')
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    TRANSFORMERS_CACHE = os.environ.get('TRANSFORMERS_CACHE', 'models')

    # RAG defaults
    RAG_TOP_K = int(os.environ.get('RAG_TOP_K', '5'))
    ENABLE_RAG = os.environ.get('ENABLE_RAG', 'true').lower() in ('true', '1', 'yes', 'on')

    # Flask
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes', 'on')
