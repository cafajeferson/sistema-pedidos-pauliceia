"""
Script para popular o banco de dados com dados de exemplo
Execute: python populate_sample_data.py
"""
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app, db, User, Product, AdminConfig
from werkzeug.security import generate_password_hash

def populate():
    with app.app_context():
        print("Limpando banco de dados...")

        # Limpar dados existentes (exceto admin)
        Product.query.delete()
        User.query.filter_by(is_admin=False).delete()

        print("👥 Criando usuários de exemplo...")

        # Criar usuários de teste
        users = [
            {'username': 'cliente1', 'password': '123456'},
            {'username': 'cliente2', 'password': '123456'},
            {'username': 'joao', 'password': 'senha123'},
        ]

        for user_data in users:
            user = User(
                username=user_data['username'],
                password=generate_password_hash(user_data['password']),
                is_admin=False
            )
            db.session.add(user)
            print(f"  ✅ Usuário criado: {user_data['username']} / {user_data['password']}")

        print("\n📦 Criando produtos de exemplo...")

        # Criar produtos de teste
        products = [
            {
                'name': 'Parafuso M8 x 50mm',
                'brand': '3M',
                'description': 'Parafuso de aço inoxidável M8 com 50mm de comprimento. Ideal para fixações que exigem alta resistência.'
            },
            {
                'name': 'Porca Sextavada M8',
                'brand': '3M',
                'description': 'Porca sextavada em aço galvanizado, rosca métrica M8. Acompanha parafuso M8.'
            },
            {
                'name': 'Arruela Lisa M8',
                'brand': 'Vonder',
                'description': 'Arruela lisa em aço carbono, diâmetro interno 8mm. Para distribuição de carga.'
            },
            {
                'name': 'Fita Isolante 19mm x 10m',
                'brand': '3M',
                'description': 'Fita isolante de PVC, cor preta, 19mm de largura e 10 metros de comprimento.'
            },
            {
                'name': 'Abraçadeira Nylon 200mm',
                'brand': 'Tramontina',
                'description': 'Abraçadeira de nylon branca, 200mm de comprimento. Para organização de cabos.'
            },
            {
                'name': 'Parafuso M6 x 30mm',
                'brand': 'Vonder',
                'description': 'Parafuso de aço carbono M6 com 30mm. Uso geral em montagens leves.'
            },
            {
                'name': 'Bucha S8',
                'brand': 'Fischer',
                'description': 'Bucha de nylon S8 para fixação em alvenaria. Acompanha parafuso.'
            },
            {
                'name': 'Silicone Acético Transparente',
                'brand': '3M',
                'description': 'Silicone acético transparente, tubo de 280ml. Para vedação e colagem.'
            },
            {
                'name': 'Fita Dupla Face 12mm x 2m',
                'brand': '3M',
                'description': 'Fita adesiva dupla face de espuma, 12mm de largura e 2 metros.'
            },
            {
                'name': 'Eletrodo E6013 2.5mm',
                'brand': 'Vonder',
                'description': 'Eletrodo revestido para solda, diâmetro 2.5mm, tipo E6013.'
            },
            {
                'name': 'Disco Corte Inox 115mm',
                'brand': 'Makita',
                'description': 'Disco de corte para inox, 115mm de diâmetro, espessura 1mm.'
            },
            {
                'name': 'Lixa Ferro Grão 80',
                'brand': '3M',
                'description': 'Lixa para ferro e metais, grão 80. Folha 230x280mm.'
            },
            {
                'name': 'Broca Aço Rápido 6mm',
                'brand': 'Bosch',
                'description': 'Broca em aço rápido HSS, diâmetro 6mm. Para furação em metais.'
            },
            {
                'name': 'Serra Copo 32mm',
                'brand': 'Bosch',
                'description': 'Serra copo bimetálica, 32mm de diâmetro. Para madeira e metal.'
            },
            {
                'name': 'Graxa Multiuso 500g',
                'brand': 'Vonder',
                'description': 'Graxa multiuso de lítio, embalagem de 500g. Para lubrificação geral.'
            },
        ]

        for product_data in products:
            product = Product(
                name=product_data['name'],
                brand=product_data['brand'],
                description=product_data['description']
            )
            db.session.add(product)
            print(f"  ✅ Produto criado: {product_data['name']}")

        print("\n⚙️  Configurando WhatsApp...")

        # Configurar WhatsApp de exemplo
        config = AdminConfig.query.first()
        if not config:
            config = AdminConfig(whatsapp_number='5511999999999')
            db.session.add(config)
            print("  ✅ Configuração criada: 5511999999999")
        else:
            config.whatsapp_number = '5511999999999'
            print("  ✅ Configuração atualizada: 5511999999999")

        db.session.commit()

        print("\n" + "="*60)
        print("✅ DADOS DE EXEMPLO CRIADOS COM SUCESSO!")
        print("="*60)
        print("\n📋 USUÁRIOS CRIADOS:")
        print("  Admin:    admin / admin123")
        print("  Cliente1: cliente1 / 123456")
        print("  Cliente2: cliente2 / 123456")
        print("  Cliente3: joao / senha123")
        print(f"\n📦 PRODUTOS CRIADOS: {len(products)}")
        print(f"\n📱 WHATSAPP CONFIGURADO: 5511999999999")
        print("\n⚠️  LEMBRE-SE: Altere o número do WhatsApp nas configurações!")
        print("="*60)

if __name__ == '__main__':
    populate()
