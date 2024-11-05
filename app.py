from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
import json
import os
from hashlib import sha256

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Funções de gerenciamento de usuários ---
def carregar_usuarios():
    try:
        with open('usuarios.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def salvar_usuarios(usuarios):
    with open('usuarios.json', 'w') as f:
        json.dump(usuarios, f, indent=4)


# --- Middleware para verificar a sessão ---
@app.before_request
def verificar_sessao():
    if request.endpoint not in ('login', 'registrar', 'static'):
        if 'username' not in session:
            return redirect(url_for('login'))


# --- Rotas de Autenticação ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuarios = carregar_usuarios()
        username = request.form['username']
        password = request.form['password']

        if username in usuarios and usuarios[username]['senha'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        usuarios = carregar_usuarios()
        username = request.form['username']
        password = request.form['password']

        if username in usuarios:
            flash('Nome de usuário já existe.', 'danger')
            return render_template('registrar.html')
        else:
            usuarios[username] = {'senha': password, 'senhas': [], 'plano': 'gratuito'}
            salvar_usuarios(usuarios)
            flash('Registro bem-sucedido! Agora você pode fazer login.', 'success')
            return redirect(url_for('login'))

    return render_template('registrar.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# --- Rotas para gerenciar senhas ---
@app.route('/index', methods=['GET', 'POST'])
def index():
    usuarios = carregar_usuarios()
    username = session['username']
    usuario = usuarios[username]
    senhas = usuario.get('senhas', [])
    plano = usuario.get('plano', 'gratuito')

    if request.method == 'POST':
        senha_plana = request.form["senha"]

        if plano == 'gratuito' and len(senhas) >= 15:
            flash('Você atingiu o limite de senhas do plano gratuito. Assine o plano pago para adicionar mais.', 'warning')
            return redirect(url_for('index'))

        senha_hash = sha256(senha_plana.encode()).hexdigest()
        senhas.append({'id': len(senhas) + 1 if senhas else 1, 'senha': senha_plana, 'hash': senha_hash})
        usuario['senhas'] = senhas
        salvar_usuarios(usuarios)
        return redirect(url_for('index'))

    return render_template('index.html', senhas=senhas, plano=plano)


@app.route('/index/<int:id>', methods=['POST'])
def delete(id):
    usuarios = carregar_usuarios()
    username = session['username']
    senhas = usuarios[username]['senhas']
    senhas = [senha for senha in senhas if senha['id'] != id]
    usuarios[username]['senhas'] = senhas
    salvar_usuarios(usuarios)
    return redirect(url_for('index'))


# --- Rota para "comprar" o plano pago ---
@app.route('/comprar_plano', methods=['GET'])
def comprar_plano():
    usuarios = carregar_usuarios()
    username = session['username']
    usuarios[username]['plano'] = 'pago'
    salvar_usuarios(usuarios)
    flash('Plano pago ativado com sucesso!', 'success')
    return redirect(url_for('index'))


# --- Páginas de Erro ---
@app.errorhandler(401) # Certifique-se de ter os templates HTML para esses erros!
def unauthorized(error):
    return render_template('401.html'), 401

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)