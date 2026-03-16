# -*- coding: utf-8 -*-
"""
Sistema de Gerenciamento de Pedidos
Integração com o app principal Flask
"""
from app import app, db
from flask import session
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

# Modelo de Pedido
class Order(db.Model):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    total_items = Column(Integer, default=0)
    status = Column(String(50), default='pendente')  # pendente, enviado, finalizado
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = relationship('User', backref='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.id} - User {self.user_id}>'

    def get_total_items(self):
        return sum(item.quantity for item in self.items)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Desconhecido',
            'total_items': self.get_total_items(),
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'items': [item.to_dict() for item in self.items]
        }


# Modelo de Item do Pedido
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    product_name = Column(String(200), nullable=False)
    product_brand = Column(String(100))
    quantity = Column(Integer, default=1)
    notes = Column(Text)

    # Relacionamentos
    order = relationship('Order', back_populates='items')
    product = relationship('Product')

    def __repr__(self):
        return f'<OrderItem {self.id} - {self.product_name} x{self.quantity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_brand': self.product_brand,
            'quantity': self.quantity,
            'notes': self.notes
        }


# Funções auxiliares para gerenciamento de pedidos
class OrderManager:
    """Classe para gerenciar operações de pedidos"""

    @staticmethod
    def create_order(user_id, items_data, notes=''):
        """
        Cria um novo pedido
        items_data: lista de dicts com {product_id, quantity, notes}
        """
        try:
            from app import Product

            order = Order(
                user_id=user_id,
                notes=notes,
                status='pendente'
            )
            db.session.add(order)
            db.session.flush()  # Para obter o ID do pedido

            # Adicionar itens ao pedido
            for item_data in items_data:
                product = Product.query.get(item_data['product_id'])
                if product:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.name,
                        product_brand=product.brand,
                        quantity=item_data.get('quantity', 1),
                        notes=item_data.get('notes', '')
                    )
                    db.session.add(order_item)

            order.total_items = order.get_total_items()
            db.session.commit()

            return order
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_user_orders(user_id):
        """Retorna todos os pedidos de um usuário"""
        return Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_order(order_id):
        """Retorna um pedido específico"""
        return Order.query.get(order_id)

    @staticmethod
    def update_order_status(order_id, status):
        """Atualiza o status de um pedido"""
        order = Order.query.get(order_id)
        if order:
            order.status = status
            order.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

    @staticmethod
    def delete_order(order_id):
        """Deleta um pedido"""
        order = Order.query.get(order_id)
        if order:
            db.session.delete(order)
            db.session.commit()
            return True
        return False

    @staticmethod
    def format_whatsapp_message(order):
        """Formata a mensagem do pedido para WhatsApp"""
        from app import User

        user = User.query.get(order.user_id)
        username = user.username if user else 'Cliente'

        message = f"*Novo Pedido #{order.id}*\n"
        message += f"👤 Cliente: {username}\n"
        message += f"📅 Data: {order.created_at.strftime('%d/%m/%Y %H:%M')}\n"
        message += f"📦 Total de itens: {order.get_total_items()}\n\n"
        message += "*Itens do Pedido:*\n"

        for idx, item in enumerate(order.items, 1):
            message += f"\n{idx}. *{item.product_name}*\n"
            message += f"   Marca: {item.product_brand}\n"
            message += f"   Quantidade: {item.quantity}\n"
            if item.notes:
                message += f"   Obs: {item.notes}\n"

        if order.notes:
            message += f"\n📝 *Observações do pedido:*\n{order.notes}"

        return message


# Inicializar tabelas de pedidos
def init_orders_db():
    """Cria as tabelas de pedidos no banco de dados"""
    with app.app_context():
        db.create_all()
        print("Tabelas de pedidos criadas com sucesso!")


if __name__ == '__main__':
    # Se executar este arquivo diretamente, cria as tabelas
    init_orders_db()
