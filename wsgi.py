# -*- coding: utf-8 -*-
"""
WSGI server para produção usando Waitress
Execute: python wsgi.py
"""
import os
import sys
import io

# Configurar encoding no Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from waitress import serve
from app import app, init_db

if __name__ == '__main__':
    # Configurar para produção
    os.environ['FLASK_ENV'] = 'production'

    # Inicializar banco de dados
    init_db()

    # Obter IP local
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print("=" * 60)
    print("  SERVIDOR DE PRODUCAO - PAULICEIA TINTAS")
    print("=" * 60)
    print("\nServidor iniciado com sucesso!")
    print(f"\nAcesse em:")
    print(f"   - Local: http://localhost:5000")
    print(f"   - Rede: http://{local_ip}:5000")
    print(f"\nModo: PRODUCAO (Waitress)")
    print(f"Usuarios simultaneos: 50-100")
    print(f"\nPara parar: Ctrl+C")
    print("=" * 60)
    print()

    # Iniciar servidor Waitress
    serve(app, host='0.0.0.0', port=5000, threads=6)
