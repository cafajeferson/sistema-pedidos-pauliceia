# Sistema de Pedidos B2B com WhatsApp

Sistema completo de catálogo de produtos e pedidos B2B integrado com WhatsApp, desenvolvido em Python Flask.

## 🎯 Funcionalidades

### Para Clientes:
- ✅ Login seguro (usuários criados apenas pelo admin)
- ✅ Catálogo de produtos com fotos
- ✅ Busca fuzzy (busca por similaridade)
- ✅ Filtros por marca
- ✅ Carrinho de compras
- ✅ Envio de pedido via WhatsApp
- ✅ Modal com detalhes do produto
- ✅ Interface responsiva (funciona em celular)

### Para Administradores:
- ✅ Painel administrativo completo
- ✅ Gerenciamento de produtos (adicionar, editar, excluir)
- ✅ Upload de imagens
- ✅ Gerenciamento de usuários
- ✅ Configuração do número do WhatsApp
- ✅ Dashboard com estatísticas

## 📁 Estrutura de Pastas

```
automa/
├── app.py                          # Aplicação principal
├── requirements.txt                # Dependências
├── README.md                       # Este arquivo
├── pedidos.db                      # Banco de dados SQLite (gerado automaticamente)
├── static/
│   ├── css/
│   │   └── style.css              # Estilos CSS
│   └── uploads/                   # Imagens dos produtos (gerado automaticamente)
└── templates/
    ├── base.html                  # Template base
    ├── login.html                 # Página de login
    ├── index.html                 # Catálogo de produtos
    └── admin/
        ├── dashboard.html         # Dashboard admin
        ├── products.html          # Lista de produtos
        ├── add_product.html       # Adicionar produto
        ├── edit_product.html      # Editar produto
        ├── users.html             # Lista de usuários
        ├── add_user.html          # Adicionar usuário
        └── config.html            # Configurações
```

## 🚀 Como Instalar e Executar

### 1. Pré-requisitos
- Python 3.8 ou superior instalado
- pip (gerenciador de pacotes Python)

### 2. Instalação

**Abra o terminal/cmd na pasta do projeto e execute:**

```bash
# Instalar as dependências
pip install -r requirements.txt
```

### 3. Executar o Sistema

```bash
# Rodar a aplicação
python app.py
```

O sistema estará disponível em: **http://localhost:5000**

### 4. Primeiro Acesso

**Credenciais do administrador padrão:**
- **Usuário:** admin
- **Senha:** admin123

⚠️ **IMPORTANTE:** Altere a senha do admin após o primeiro acesso!

## 📋 Configuração Inicial

### Passo 1: Configurar WhatsApp
1. Acesse o painel admin: `http://localhost:5000/admin`
2. Vá em "Configurações"
3. Insira o número do WhatsApp no formato: `5511999999999`
   - 55 = código do Brasil
   - 11 = DDD
   - 999999999 = número

### Passo 2: Criar Usuários
1. No painel admin, vá em "Gerenciar Usuários"
2. Clique em "Adicionar Usuário"
3. Crie login e senha para seus clientes

### Passo 3: Cadastrar Produtos
1. No painel admin, vá em "Gerenciar Produtos"
2. Clique em "Adicionar Produto"
3. Preencha: Nome, Marca, Descrição e faça upload da foto

## 🎨 Como Usar (Cliente)

1. **Login:** Acesse com usuário e senha fornecidos
2. **Buscar:** Use a barra de busca ou filtros por marca
3. **Adicionar ao carrinho:** Use os botões +/- ou digite a quantidade
4. **Ver detalhes:** Clique na foto do produto
5. **Ver carrinho:** Clique no botão flutuante do carrinho
6. **Enviar pedido:** Clique em "Enviar Pedido via WhatsApp"

## 💰 Custo Total: R$ 0,00

✅ Totalmente gratuito
✅ Sem custos mensais
✅ Sem APIs pagas
✅ Sem licenças

## 🔧 Tecnologias Utilizadas

- **Backend:** Python + Flask
- **Banco de Dados:** SQLite
- **Frontend:** HTML5 + CSS3 + JavaScript
- **Autenticação:** Werkzeug (hash de senhas)
- **Busca Fuzzy:** FuzzyWuzzy
- **Upload de Arquivos:** Werkzeug

## 📱 Recursos Mobile

- Design 100% responsivo
- Menu adaptável
- Carrinho em tela cheia no mobile
- Cards de produtos otimizados
- Formulários mobile-friendly

## 🔒 Segurança

- ✅ Senhas com hash (bcrypt)
- ✅ Proteção de rotas admin
- ✅ Validação de sessões
- ✅ Upload seguro de arquivos
- ✅ Prevenção de SQL Injection (SQLAlchemy ORM)

## 📊 Banco de Dados

O sistema usa SQLite com 3 tabelas:

1. **User:** Usuários do sistema
2. **Product:** Produtos do catálogo
3. **AdminConfig:** Configurações (número WhatsApp)

## 🛠️ Manutenção

### Backup do Banco de Dados
Copie o arquivo `pedidos.db` para fazer backup.

### Resetar Senha do Admin
Execute no Python:
```python
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.password = generate_password_hash('nova_senha')
    db.session.commit()
```

### Limpar Imagens Antigas
As imagens ficam em `static/uploads/`. Exclua manualmente se necessário.

## 🐛 Troubleshooting

**Erro: "ModuleNotFoundError"**
- Solução: Execute `pip install -r requirements.txt`

**Erro: "Address already in use"**
- Solução: Mude a porta no `app.py`: `app.run(debug=True, port=5001)`

**Upload de imagem não funciona**
- Verifique se a pasta `static/uploads` existe e tem permissão de escrita

**WhatsApp não abre**
- Verifique se o número está no formato correto: 5511999999999
- Teste o link manualmente: `https://wa.me/5511999999999?text=teste`

## 📞 Suporte

Sistema desenvolvido para automação de pedidos B2B.

## 📝 Licença

Código livre para uso pessoal e comercial.

---

**Desenvolvido com Python Flask 🐍**
