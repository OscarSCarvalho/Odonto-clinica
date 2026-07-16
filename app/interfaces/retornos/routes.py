from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.interfaces.auth.decorators import requer_perfil
from app.infrastructure.container import tarefa_retorno_repo

retornos_bp = Blueprint('retornos', __name__, url_prefix='/retornos')


@retornos_bp.route('/')
@retornos_bp.route('')
@requer_perfil('admin', 'recepcao')
def index():
    tarefas = tarefa_retorno_repo().listar_pendentes()
    return render_template('retornos/index.html', tarefas=tarefas)


@retornos_bp.route('/<int:id>/contatar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def contatar(id):
    observacoes = request.form.get('observacoes', '').strip() or None
    tarefa_retorno_repo().marcar_contatado(id, observacoes)
    flash('Contato registrado.', 'sucesso')
    return redirect(url_for('retornos.index'))
