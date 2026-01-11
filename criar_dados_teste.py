# -*- coding: utf-8 -*-
from app import app, db, User, Product, AdminConfig
from werkzeug.security import generate_password_hash

with app.app_context():
    # Limpar dados existentes
    Product.query.delete()
    User.query.filter_by(is_admin=False).delete()

    # Criar usuarios
    users = [
        {'username': 'cliente1', 'password': '123456'},
        {'username': 'joao', 'password': 'senha123'},
    ]

    for user_data in users:
        user = User(
            username=user_data['username'],
            password=generate_password_hash(user_data['password']),
            is_admin=False
        )
        db.session.add(user)
        print(f"Usuario criado: {user_data['username']} / {user_data['password']}")

    # Criar produtos
    products = [
        {'name': 'Parafuso M8 x 50mm', 'brand': '3M', 'description': 'Parafuso de aco inoxidavel M8 com 50mm.'},
        {'name': 'Porca Sextavada M8', 'brand': '3M', 'description': 'Porca sextavada em aco galvanizado M8.'},
        {'name': 'Arruela Lisa M8', 'brand': 'Vonder', 'description': 'Arruela lisa em aco carbono 8mm.'},
        {'name': 'Fita Isolante 19mm', 'brand': '3M', 'description': 'Fita isolante PVC preta 19mm x 10m.'},
        {'name': 'Abracadeira Nylon 200mm', 'brand': 'Tramontina', 'description': 'Abracadeira nylon branca 200mm.'},
    ]

    for product_data in products:
        product = Product(
            name=product_data['name'],
            brand=product_data['brand'],
            description=product_data['description']
        )
        db.session.add(product)
        print(f"Produto criado: {product_data['name']}")

    # Configurar WhatsApp exemplo
    config = AdminConfig.query.first()
    if not config:
        config = AdminConfig(whatsapp_number='5511999999999')
        db.session.add(config)

    db.session.commit()

    print("\n=== DADOS CRIADOS ===")
    print("Usuarios: cliente1/123456, joao/senha123")
    print("Produtos: 5 produtos de exemplo")
    print("WhatsApp: 5511999999999 (ALTERE NAS CONFIGURACOES!)")
