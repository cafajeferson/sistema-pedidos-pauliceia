import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

class Config:
    """Configuração base da aplicação"""
    # IMPORTANTE: Configure estas variáveis no arquivo .env ou nas variáveis de ambiente do servidor
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY não configurada! Configure no arquivo .env")

    # Supabase - OBRIGATÓRIO configurar no .env
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY são obrigatórios! Configure no arquivo .env")

    # Banco de dados local (para usuarios e config)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///pedidos.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Upload de arquivos
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Segurança
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento local"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Permite HTTP no localhost
    TESTING = False

class ProductionConfig(Config):
    """Configuração para produção (Hostinger)"""
    DEBUG = False
    TESTING = False

    # IMPORTANTE: Na Hostinger, configure estas variáveis de ambiente:
    # - SECRET_KEY: sua chave secreta única
    # - DATABASE_URL: se usar PostgreSQL ao invés de SQLite

    # Logging em produção
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

class TestingConfig(Config):
    """Configuração para testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
