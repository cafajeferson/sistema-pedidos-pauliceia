from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from fuzzywuzzy import fuzz
from supabase import create_client, Client
import os
from datetime import datetime
import time
import uuid

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

# Inicializar Supabase
supabase: Client = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_KEY'])
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'produtos')

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
    categoria_loja = db.Column(db.String(20), nullable=False, default='automotivo', index=True)  # 'automotivo' ou 'imobiliario'
    related_product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)  # Catalisador/produto relacionado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento para obter o produto relacionado
    related_product = db.relationship('Product', remote_side=[id], foreign_keys=[related_product_id])

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

def categoria_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'categoria_loja' not in session:
            return redirect(url_for('selecionar_setor'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas públicas
@app.route('/selecionar-setor')
@login_required
def selecionar_setor():
    return render_template('selecionar_setor.html')

@app.route('/set-setor/<categoria>')
@login_required
def set_setor(categoria):
    if categoria in ['automotivo', 'imobiliario']:
        session['categoria_loja'] = categoria
        # Se for admin, vai para o dashboard admin
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
    flash('Categoria inválida!', 'danger')
    return redirect(url_for('selecionar_setor'))

@app.route('/')
@login_required
@categoria_required
def index():
    categoria = session.get('categoria_loja')

    # Buscar TODOS os produtos do Supabase com paginação (limite padrão é 1000)
    produtos_supabase = []
    page = 0
    page_size = 1000
    
    while True:
        response = supabase.table('produtos').select('*').eq('setor', categoria) \
            .range(page * page_size, (page + 1) * page_size - 1).execute()
        
        if not response.data:
            break
            
        produtos_supabase.extend(response.data)
        page += 1

    # Extrair marcas únicas dos nomes dos produtos (última palavra)
    brands_set = set()
    for p in produtos_supabase:
        parts = p['nome'].split()
        if len(parts) > 1:
            marca = parts[-1]
            brands_set.add(marca)
    brands = sorted(list(brands_set))

    # Converter para formato esperado pelo template
    products_json = []
    for p in produtos_supabase:
        parts = p['nome'].split()
        marca = parts[-1] if len(parts) > 1 else ''
        products_json.append({
            'id': p['id'],
            'name': p['nome'],
            'brand': marca,
            'description': p.get('descricao') or '',
            # Usar URL da imagem se existir (imagem ou image)
            'image': p.get('imagem') or p.get('image'),
            'related_product_ids': p.get('produto_relacionado_ids') or (str(p.get('produto_relacionado_id')) if p.get('produto_relacionado_id') else ''),
            'em_queima_estoque': p.get('em_queima_estoque', False),
            'preco_original': p.get('preco_original'),
            'preco_queima': p.get('preco_queima')
        })

    return render_template('index.html', products=[], brands=brands, products_json=products_json)

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

            # Redirecionar para seleção de setor
            return redirect(url_for('selecionar_setor'))

        flash('Usuário ou senha inválidos!', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/api/search')
@login_required
@categoria_required
def search_products():
    query = request.args.get('q', '').lower()
    brands = request.args.getlist('brands[]')
    categoria = session.get('categoria_loja')

    # Filtrar apenas produtos da categoria selecionada
    products = Product.query.filter_by(categoria_loja=categoria).all()

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

@app.route('/api/search-products')
@admin_required
@categoria_required
def search_products_api():
    """API para buscar produtos para vincular como catalisador/produto relacionado"""
    query = request.args.get('q', '').strip()
    exclude_id = request.args.get('exclude_id', type=int)
    categoria = session.get('categoria_loja')

    if not query or len(query) < 2:
        return jsonify([])

    # Buscar produtos do Supabase - buscar TODOS e filtrar depois para melhor resultado
    all_produtos = []
    page = 0
    page_size = 1000
    
    while True:
        response = supabase.table('produtos').select('*').eq('setor', categoria) \
            .range(page * page_size, (page + 1) * page_size - 1).execute()
        
        if not response.data:
            break
            
        all_produtos.extend(response.data)
        page += 1
    
    # Filtrar produtos que contenham o termo de busca (case-insensitive)
    query_lower = query.lower()
    produtos = [p for p in all_produtos if query_lower in p['nome'].lower()]
    
    # Excluir o próprio produto se estiver editando
    if exclude_id:
        produtos = [p for p in produtos if p['id'] != exclude_id]
    
    # Ordenar por relevância (quanto mais próximo do início, melhor)
    produtos.sort(key=lambda p: p['nome'].lower().index(query_lower))
    
    # Limitar a 50 resultados mais relevantes
    produtos = produtos[:50]

    # Formatar resposta (extrair marca da última palavra)
    result = []
    for p in produtos:
        parts = p['nome'].split()
        marca = parts[-1] if len(parts) > 1 else ''
        result.append({
            'id': p['id'],
            'name': p['nome'],
            'brand': marca
        })

    return jsonify(result)

@app.route('/api/product/<int:product_id>/photo', methods=['POST'])
@admin_required
@categoria_required
def upload_product_photo(product_id):
    """API para upload de foto de produto via AJAX"""
    categoria = session.get('categoria_loja')

    # Verificar se o produto existe e pertence à categoria
    response = supabase.table('produtos').select('*').eq('id', product_id).eq('setor', categoria).execute()
    if not response.data:
        return jsonify({'success': False, 'error': 'Produto não encontrado'}), 404

    product = response.data[0]
    imagem_file = request.files.get('image')

    if not imagem_file or not imagem_file.filename:
        return jsonify({'success': False, 'error': 'Nenhuma imagem enviada'}), 400

    try:
        filename = secure_filename(imagem_file.filename)
        storage_path = f"produtos/{int(time.time())}_{uuid.uuid4().hex}_{filename}"

        file_bytes = imagem_file.read()
        # Upload para bucket configurado
        supabase.storage.from_(SUPABASE_BUCKET).upload(storage_path, file_bytes, {
            "content-type": imagem_file.mimetype or "application/octet-stream"
        })
        public_url_resp = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
        public_url = public_url_resp.get('publicUrl') if isinstance(public_url_resp, dict) else public_url_resp

        # Atualizar o produto com a nova URL da imagem
        image_field = 'imagem' if 'imagem' in product else 'image'
        supabase.table('produtos').update({image_field: public_url}).eq('id', product_id).execute()

        return jsonify({'success': True, 'image_url': public_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Rotas Admin
@app.route('/admin')
@admin_required
@categoria_required
def admin_dashboard():
    categoria = session.get('categoria_loja')
    # Contar produtos do Supabase
    response = supabase.table('produtos').select('id', count='exact').eq('setor', categoria).execute()
    total_products = response.count or 0
    total_users = User.query.filter_by(is_admin=False).count()
    categoria_nome = 'Automotivo' if categoria == 'automotivo' else 'Imobiliário'

    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_users=total_users,
                         categoria_nome=categoria_nome)

@app.route('/admin/products')
@admin_required
@categoria_required
def admin_products():
    categoria = session.get('categoria_loja')
    # Buscar TODOS os produtos do Supabase com paginação
    products = []
    page = 0
    page_size = 1000
    
    while True:
        response = supabase.table('produtos').select('*').eq('setor', categoria).order('nome') \
            .range(page * page_size, (page + 1) * page_size - 1).execute()
        
        if not response.data:
            break
            
        products.extend(response.data)
        page += 1
    
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
@categoria_required
def admin_add_product():
    if request.method == 'POST':
        nome = request.form.get('name')
        descricao = request.form.get('description', '').strip()
        relacionado_ids = request.form.get('related_product_ids', '').strip()
        categoria = session.get('categoria_loja')

        # Preparar dados
        produto_data = {
            'nome': nome,
            'descricao': descricao,
            'setor': categoria
        }

        # Adicionar produtos relacionados (múltiplos catalisadores)
        if relacionado_ids and relacionado_ids != 'None':
            try:
                ids_validos = [str(int(id.strip())) for id in relacionado_ids.split(',') if id.strip()]
                produto_data['produto_relacionado_ids'] = ','.join(ids_validos) if ids_validos else None
            except (ValueError, TypeError):
                pass

        # Inserir no Supabase
        supabase.table('produtos').insert(produto_data).execute()

        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/add_product.html')

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
@categoria_required
def admin_edit_product(id):
    categoria = session.get('categoria_loja')
    # Buscar produto do Supabase
    response = supabase.table('produtos').select('*').eq('id', id).eq('setor', categoria).execute()
    if not response.data:
        flash('Produto não encontrado!', 'danger')
        return redirect(url_for('admin_products'))
    product = response.data[0]

    if request.method == 'POST':
        nome_produto = request.form.get('name')
        marca = request.form.get('brand', '').strip()
        descricao = request.form.get('description', '').strip()
        relacionado_ids = request.form.get('related_product_ids', '').strip()
        imagem_file = request.files.get('image')

        # Se a marca foi apagada, manter a marca anterior
        if not marca:
            # Extrair a marca anterior do nome completo
            partes = product.get('nome', '').split()
            if len(partes) > 1:
                marca = partes[-1]

        # Se houver marca, adicionar ao final do nome
        nome_completo = nome_produto
        if marca:
            nome_completo = f"{nome_produto} {marca}".strip()

        # Preparar dados para atualização
        update_data = {'nome': nome_completo, 'descricao': descricao}

        # Adicionar produtos relacionados (múltiplos catalisadores)
        if relacionado_ids and relacionado_ids != 'None':
            # Validar que são IDs numéricos separados por vírgula
            try:
                ids_validos = [str(int(id.strip())) for id in relacionado_ids.split(',') if id.strip()]
                update_data['produto_relacionado_ids'] = ','.join(ids_validos) if ids_validos else None
            except (ValueError, TypeError):
                update_data['produto_relacionado_ids'] = None
        else:
            update_data['produto_relacionado_ids'] = None

        # Upload de imagem no Supabase Storage, se enviado
        if imagem_file and imagem_file.filename:
            filename = secure_filename(imagem_file.filename)
            storage_path = f"produtos/{int(time.time())}_{uuid.uuid4().hex}_{filename}"

            try:
                file_bytes = imagem_file.read()
                # Upload para bucket configurado
                supabase.storage.from_(SUPABASE_BUCKET).upload(storage_path, file_bytes, {
                    "content-type": imagem_file.mimetype or "application/octet-stream"
                })
                public_url_resp = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
                public_url = public_url_resp.get('publicUrl') if isinstance(public_url_resp, dict) else public_url_resp

                image_field = 'imagem' if 'imagem' in product else ('image' if 'image' in product else None)
                if image_field:
                    update_data[image_field] = public_url
                else:
                    flash('Imagem enviada, mas a coluna de imagem não existe na tabela.', 'warning')
            except Exception as e:
                flash(f'Erro ao enviar imagem para o Supabase Storage: {e}', 'danger')

        # Atualizar no Supabase
        supabase.table('produtos').update(update_data).eq('id', id).execute()

        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin_products'))

    # Separar nome e marca (marca é a última palavra)
    nome_completo = product.get('nome', '')
    partes = nome_completo.split()
    if len(partes) > 1:
        marca = partes[-1]
        nome_base = ' '.join(partes[:-1])
    else:
        marca = ''
        nome_base = nome_completo

    # Buscar dados dos produtos relacionados (múltiplos catalisadores)
    related_products_data = []
    produto_relacionado_ids = product.get('produto_relacionado_ids') or ''

    # Compatibilidade com campo antigo (single ID)
    if not produto_relacionado_ids and product.get('produto_relacionado_id'):
        produto_relacionado_ids = str(product.get('produto_relacionado_id'))

    if produto_relacionado_ids:
        try:
            ids_list = [int(id.strip()) for id in produto_relacionado_ids.split(',') if id.strip()]
            for rel_id in ids_list:
                rel_response = supabase.table('produtos').select('id, nome').eq('id', rel_id).execute()
                if rel_response.data and len(rel_response.data) > 0:
                    related_products_data.append({
                        'id': rel_response.data[0]['id'],
                        'name': rel_response.data[0]['nome']
                    })
        except:
            pass

    product_display = {
        'id': product['id'],
        'nome_completo': nome_completo,
        'nome': nome_base,
        'marca': marca,
        'setor': product['setor'],
        'descricao': product.get('descricao', ''),
        'produto_relacionado_ids': produto_relacionado_ids,
        'related_products_data': related_products_data,
        'imagem': product.get('imagem') or product.get('image')
    }

    return render_template('admin/edit_product.html', product=product_display)

@app.route('/admin/products/delete/<int:id>')
@admin_required
@categoria_required
def admin_delete_product(id):
    categoria = session.get('categoria_loja')
    # Deletar do Supabase
    supabase.table('produtos').delete().eq('id', id).eq('setor', categoria).execute()

    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/users')
@admin_required
@categoria_required
def admin_users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
@categoria_required
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
@categoria_required
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
@categoria_required
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

@app.route('/admin/queima-estoque')
@admin_required
@categoria_required
def admin_queima_estoque():
    """Página de gerenciamento de produtos em queima de estoque"""
    categoria = session.get('categoria_loja')
    
    # Buscar todos os produtos do setor
    all_produtos = []
    page = 0
    page_size = 1000
    
    while True:
        response = supabase.table('produtos').select('*').eq('setor', categoria) \
            .range(page * page_size, (page + 1) * page_size - 1).execute()
        
        if not response.data:
            break
            
        all_produtos.extend(response.data)
        page += 1
    
    # Separar produtos em queima e normais
    produtos_queima = [p for p in all_produtos if p.get('em_queima_estoque', False)]
    produtos_normais = [p for p in all_produtos if not p.get('em_queima_estoque', False)]
    
    return render_template('admin/queima_estoque.html', 
                         produtos_queima=produtos_queima, 
                         produtos_normais=produtos_normais)

@app.route('/admin/queima-estoque/toggle/<int:product_id>', methods=['POST'])
@admin_required
@categoria_required
def toggle_queima_estoque(product_id):
    """Alternar status de queima de estoque"""
    categoria = session.get('categoria_loja')
    
    try:
        # Buscar produto
        response = supabase.table('produtos').select('*').eq('id', product_id).eq('setor', categoria).execute()
        
        if not response.data:
            return jsonify({'error': 'Produto não encontrado'}), 404
        
        produto = response.data[0]
        novo_status = not produto.get('em_queima_estoque', False)
        
        # Atualizar
        update_response = supabase.table('produtos').update({'em_queima_estoque': novo_status}).eq('id', product_id).execute()
        
        print(f"Toggle queima - Produto ID: {product_id}, Status anterior: {produto.get('em_queima_estoque')}, Novo status: {novo_status}")
        
        return jsonify({'success': True, 'em_queima_estoque': novo_status})
    
    except Exception as e:
        print(f"Erro ao toggle queima estoque: {str(e)}")
        return jsonify({'error': f'Erro ao atualizar produto: {str(e)}'}), 500

@app.route('/admin/queima-estoque/save-prices/<int:product_id>', methods=['POST'])
@admin_required
@categoria_required
def save_queima_prices(product_id):
    """Salvar preços de queima de estoque"""
    categoria = session.get('categoria_loja')
    data = request.get_json()
    
    try:
        # Validar dados
        preco_original = float(data.get('preco_original', 0))
        preco_queima = float(data.get('preco_queima', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Preços inválidos'}), 400
    
    if preco_original <= 0 or preco_queima <= 0 or preco_queima >= preco_original:
        return jsonify({'error': 'Preços inválidos. O preço de queima deve ser menor que o original'}), 400
    
    try:
        # Buscar produto para validar
        response = supabase.table('produtos').select('*').eq('id', product_id).eq('setor', categoria).execute()
        
        if not response.data:
            return jsonify({'error': 'Produto não encontrado'}), 404
        
        # Atualizar preços
        supabase.table('produtos').update({
            'preco_original': preco_original,
            'preco_queima': preco_queima
        }).eq('id', product_id).execute()
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Erro ao salvar preços: {str(e)}")
        return jsonify({'error': f'Erro ao salvar preços: {str(e)}'}), 500

# Rota para trocar de setor
@app.route('/trocar-setor')
@login_required
def trocar_setor():
    # Limpar categoria da sessão e redirecionar para seleção
    session.pop('categoria_loja', None)
    return redirect(url_for('selecionar_setor'))

# Inicialização do banco de dados
def init_db():
    with app.app_context():
        db.create_all()

        # Migração: Adicionar categoria_loja aos produtos existentes se não tiver
        try:
            # Verificar se a coluna existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('product')]

            if 'categoria_loja' not in columns:
                # Adicionar coluna manualmente (SQLite não suporta ALTER COLUMN facilmente)
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE product ADD COLUMN categoria_loja VARCHAR(20) DEFAULT "automotivo"'))
                    conn.commit()
                print("Coluna categoria_loja adicionada à tabela product")
            else:
                # Atualizar produtos sem categoria
                products_sem_categoria = Product.query.filter(
                    (Product.categoria_loja == None) | (Product.categoria_loja == '')
                ).all()

                if products_sem_categoria:
                    for product in products_sem_categoria:
                        product.categoria_loja = 'automotivo'
                    db.session.commit()
                    print(f"{len(products_sem_categoria)} produtos atualizados com categoria padrão")

            # Migração: Adicionar coluna related_product_id se não existir
            if 'related_product_id' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE product ADD COLUMN related_product_id INTEGER'))
                    conn.commit()
                print("Coluna related_product_id adicionada à tabela product")
        except Exception as e:
            print(f"Aviso na migração: {e}")

        # Criar admin padrão se não existir
        # IMPORTANTE: Troque a senha após o primeiro login!
        admin_password = os.environ.get('ADMIN_PASSWORD', 'TroqueEstaSenha@2024!')
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin criado! Usuario: admin - TROQUE A SENHA IMEDIATAMENTE!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
