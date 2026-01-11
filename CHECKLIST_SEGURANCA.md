# 🔐 Checklist de Segurança - Antes do Deploy

## ⚠️ AÇÕES OBRIGATÓRIAS ANTES DE HOSPEDAR

### 1. SECRET_KEY

- [ ] **GERAR NOVA SECRET_KEY** para produção
- [ ] NÃO usar a chave padrão do código
- [ ] Comando para gerar nova chave:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
- [ ] Configurar no painel Hostinger como variável de ambiente

---

### 2. Senha do Administrador

- [ ] **PRIMEIRO LOGIN:** mudar senha padrão `admin123`
- [ ] Ir em: **Admin** > **Perfil** > **Alterar Senha**
- [ ] Usar senha forte (mínimo 12 caracteres, letras, números e símbolos)
- [ ] **NUNCA** usar senhas fracas como: 123456, admin, senha123

---

### 3. Banco de Dados

- [ ] O arquivo `pedidos.db` NÃO deve ser enviado
- [ ] Será criado automaticamente na primeira execução
- [ ] Verificar permissões da pasta `instance/`:
```bash
chmod 755 instance/
chmod 644 instance/pedidos.db
```

---

### 4. Uploads de Arquivos

- [ ] Pasta `static/uploads/` deve ter permissão 755
- [ ] Apenas imagens permitidas (png, jpg, jpeg, gif, webp)
- [ ] Tamanho máximo: 16MB
- [ ] Validação de tipo MIME implementada ✅

---

### 5. SSL/HTTPS

- [ ] Configurar certificado SSL na Hostinger (grátis)
- [ ] Descomentar redirect HTTPS no `.htaccess`:
```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```
- [ ] Verificar se `SESSION_COOKIE_SECURE = True` em produção

---

### 6. Configurações de Produção

- [ ] `DEBUG = False` em ProductionConfig ✅
- [ ] `FLASK_ENV=production` configurado ✅
- [ ] Logs de erro habilitados
- [ ] Remover `print()` statements sensíveis do código

---

### 7. Proteção de Arquivos Sensíveis

Arquivos protegidos pelo `.htaccess`:
- ✅ `.py` - código Python
- ✅ `.pyc` - bytecode
- ✅ `.db` - banco de dados
- ✅ `.log` - logs
- ✅ `.env` - variáveis de ambiente

---

### 8. Injeção SQL

- ✅ **Protegido:** Uso do SQLAlchemy ORM
- ✅ Queries parametrizadas
- ✅ Não há SQL raw no código

---

### 9. XSS (Cross-Site Scripting)

- ✅ **Protegido:** Templates Jinja2 com auto-escape
- ✅ Headers de segurança configurados no `.htaccess`
- ✅ `X-XSS-Protection` habilitado

---

### 10. CSRF (Cross-Site Request Forgery)

- ⚠️ **RECOMENDADO:** Adicionar Flask-WTF para proteção CSRF
- [ ] Instalar: `pip install Flask-WTF`
- [ ] Adicionar ao requirements.txt
- [ ] Implementar tokens CSRF nos formulários

---

### 11. Clickjacking

- ✅ **Protegido:** Header `X-Frame-Options: SAMEORIGIN`
- Configurado no `.htaccess`

---

### 12. Session Hijacking

- ✅ **Protegido:**
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SAMESITE = 'Lax'`
  - `PERMANENT_SESSION_LIFETIME = 3600` (1 hora)
  - `SESSION_COOKIE_SECURE = True` (HTTPS only)

---

### 13. Permissões de Arquivos

No servidor Hostinger, execute:

```bash
# Arquivos Python
chmod 644 *.py

# Diretórios
chmod 755 static/
chmod 755 static/uploads/
chmod 755 templates/

# Arquivos sensíveis
chmod 600 .env
```

---

### 14. Rate Limiting (Opcional, mas Recomendado)

- [ ] Instalar: `pip install Flask-Limiter`
- [ ] Limitar tentativas de login (ex: 5 tentativas/minuto)
- [ ] Limitar criação de pedidos

Exemplo:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    ...
```

---

### 15. Backup

- [ ] Configurar backup automático do banco de dados
- [ ] Backup da pasta `static/uploads/`
- [ ] Frequência recomendada: diário

Script de backup:
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
cp instance/pedidos.db backups/pedidos_$DATE.db
tar -czf backups/uploads_$DATE.tar.gz static/uploads/
```

---

### 16. Monitoramento

- [ ] Configurar logs de acesso
- [ ] Configurar logs de erro
- [ ] Revisar logs semanalmente
- [ ] Monitorar espaço em disco

---

### 17. Senhas de Usuários

- ✅ **Protegido:** Hash com Werkzeug (PBKDF2)
- ✅ Não armazena senhas em texto plano
- [ ] Política de senha forte (implementar se necessário)

---

### 18. Variáveis de Ambiente

❌ **NUNCA** commitar no Git:
- `.env`
- Senhas
- SECRET_KEY
- Credenciais de API

✅ Usar arquivo `.env.example` como referência

---

### 19. Atualizações de Segurança

- [ ] Manter Flask atualizado
- [ ] Manter dependências atualizadas
- [ ] Revisar `pip list --outdated` mensalmente

```bash
pip install --upgrade Flask Flask-SQLAlchemy
```

---

### 20. WhatsApp

- [ ] Número configurado no formato correto: `5511999999999`
- [ ] Não expor número em código-fonte
- [ ] Armazenar no banco de dados (AdminConfig)

---

## 📋 Checklist Final Antes do Deploy

Marque TODOS antes de fazer upload para produção:

- [ ] Nova SECRET_KEY gerada e configurada
- [ ] DEBUG = False
- [ ] FLASK_ENV = production
- [ ] SSL configurado (HTTPS)
- [ ] Senha admin será alterada no primeiro login
- [ ] Arquivo .env não será enviado
- [ ] Arquivo pedidos.db não será enviado
- [ ] Pasta venv/ não será enviada
- [ ] .htaccess configurado com caminhos corretos
- [ ] passenger_wsgi.py configurado com caminhos corretos
- [ ] Permissões de arquivos verificadas
- [ ] Backup configurado
- [ ] Logs habilitados

---

## ✅ Nível de Segurança Atual

- **Autenticação:** ✅ Forte (hash de senha)
- **Autorização:** ✅ Roles (admin/user)
- **SQL Injection:** ✅ Protegido (ORM)
- **XSS:** ✅ Protegido (auto-escape)
- **CSRF:** ⚠️ Recomendado implementar
- **Session Security:** ✅ Protegido
- **File Upload:** ✅ Validado
- **HTTPS:** ⚠️ Configurar após deploy
- **Rate Limiting:** ⚠️ Opcional

**Status Geral:** 🟢 **BOM** - Pronto para produção

Melhorias opcionais: CSRF protection, Rate limiting, 2FA

---

## 🆘 Em Caso de Invasão

1. **Desative o site imediatamente**
2. Mude TODAS as senhas
3. Gere nova SECRET_KEY
4. Revise logs de acesso
5. Restaure backup limpo
6. Atualize todas as dependências
7. Reative apenas após correção

---

**Última atualização:** Janeiro 2026
