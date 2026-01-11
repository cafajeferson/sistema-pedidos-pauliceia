# -*- coding: utf-8 -*-
"""
Passenger WSGI para Hostinger
Sistema de Pedidos - Pauliceia Tintas
"""
import sys
import os

# IMPORTANTE: Ajuste o caminho abaixo para o caminho real na Hostinger
# Exemplo: /home/seu-usuario/public_html
INTERP = os.path.join(os.environ['HOME'], 'virtualenv', 'public_html', '3.11', 'bin', 'python')

# Verifica se o interpretador virtual existe
if os.path.isfile(INTERP):
    sys.executable = INTERP

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

# Configura ambiente de produção
os.environ['FLASK_ENV'] = 'production'

# Importa a aplicação Flask
from app import app, init_db

# Inicializa o banco de dados
init_db()

# Exporta a aplicação para o Passenger
application = app

# Caso queira usar Gunicorn ao invés de Passenger, use:
# gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 passenger_wsgi:application
