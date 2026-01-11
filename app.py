from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from fuzzywuzzy import fuzz
import os
from datetime import datetime

app = Flask(__name__)

# Carregar configuração baseada no ambiente
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    from config import ProductionConfig
    app.config.from_object(ProductionConfig)
else:
    from config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whatsapp_number = db.Column(db.String(20), nullable=False)

# Decoradores
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login primeiro.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Acesso negado. Apenas administradores.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas públicas
@app.route('/')
@login_required
def index():
    brands = db.session.query(Product.brand).distinct().all()
    brands = [b[0] for b in brands]
    products = Product.query.all()

    # Converter produtos para dicionários para uso no JavaScript
    products_json = [{
        'id': p.id,
        'name': p.name,
        'brand': p.brand,
        'description': p.description or '',
        'image': p.image
    } for p in products]

    return render_template('index.html', products=products, brands=brands, products_json=products_json)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin

            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))

        flash('Usuário ou senha inválidos!', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/api/search')
@login_required
def search_products():
    query = request.args.get('q', '').lower()
    brands = request.args.getlist('brands[]')

    products = Product.query.all()

    # Filtro por marca
    if brands:
        products = [p for p in products if p.brand in brands]

    # Busca fuzzy
    if query:
        results = []
        for product in products:
            score = fuzz.partial_ratio(query, product.name.lower())
            if score > 60:  # Threshold de similaridade
                results.append({
                    'product': product,
                    'score': score
                })
        results.sort(key=lambda x: x['score'], reverse=True)
        products = [r['product'] for r in results]

    return jsonify([{
        'id': p.id,
        'name': p.name,
        'brand': p.brand,
        'description': p.description,
        'image': p.image
    } for p in products])

@app.route('/api/whatsapp-config')
@login_required
def get_whatsapp_config():
    config = AdminConfig.query.first()
    if config:
        return jsonify({'number': config.whatsapp_number})
    return jsonify({'number': ''})

# Rotas Admin
@app.route('/admin')
@admin_required
def admin_dashboard():
    total_products = Product.query.count()
    total_users = User.query.filter_by(is_admin=False).count()
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_users=total_users)

@app.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        brand = request.form.get('brand')
        description = request.form.get('description')

        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        product = Product(
            name=name,
            brand=brand,
            description=description,
            image=image_filename
        )
        db.session.add(product)
        db.session.commit()

        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/add_product.html')

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.brand = request.form.get('brand')
        product.description = request.form.get('description')

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Remover imagem antiga
                if product.image:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                image_filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                product.image = image_filename

        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/products/delete/<int:id>')
@admin_required
def admin_delete_product(id):
    product = Product.query.get_or_404(id)

    # Remover imagem
    if product.image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(product)
    db.session.commit()

    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Usuário já existe!', 'danger')
            return redirect(url_for('admin_add_user'))

        user = User(
            username=username,
            password=generate_password_hash(password),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()

        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/add_user.html')

@app.route('/admin/users/delete/<int:id>')
@admin_required
def admin_delete_user(id):
    user = User.query.get_or_404(id)

    if user.is_admin:
        flash('Não é possível excluir administradores!', 'danger')
        return redirect(url_for('admin_users'))

    db.session.delete(user)
    db.session.commit()

    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/config', methods=['GET', 'POST'])
@admin_required
def admin_config():
    config = AdminConfig.query.first()

    if request.method == 'POST':
        whatsapp = request.form.get('whatsapp_number')

        if config:
            config.whatsapp_number = whatsapp
        else:
            config = AdminConfig(whatsapp_number=whatsapp)
            db.session.add(config)

        db.session.commit()
        flash('Configuração salva com sucesso!', 'success')
        return redirect(url_for('admin_config'))

    return render_template('admin/config.html', config=config)

# Inicialização do banco de dados
def init_db():
    with app.app_context():
        db.create_all()

        # Criar admin padrão se não existir
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin criado! Usuário: admin | Senha: admin123")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
