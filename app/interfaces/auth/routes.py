from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from app.infrastructure.db.connection import get_db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('agenda.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        db = get_db()
        usuario = db.execute(
            'SELECT * FROM usuarios WHERE email = ? AND ativo = 1', (email,)
        ).fetchone()

        if usuario and check_password_hash(usuario['senha_hash'], senha):
            session.clear()
            session['user_id'] = usuario['id']
            session['perfil'] = usuario['perfil']
            session['nome'] = usuario['nome']
            return redirect(url_for('agenda.index'))

        flash('E-mail ou senha inválidos.', 'erro')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.errorhandler(403)
def acesso_negado(e):
    return render_template('auth/403.html'), 403
