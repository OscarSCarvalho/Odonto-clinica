from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.interfaces.auth.decorators import requer_perfil
from app.domain.entities.procedimento import Procedimento
from app.domain.exceptions import DadosInvalidosError
from app.infrastructure.container import procedimento_repo

procedimentos_bp = Blueprint('procedimentos', __name__, url_prefix='/procedimentos')


@procedimentos_bp.route('/')
@requer_perfil('admin')
def index():
    repo = procedimento_repo()
    return render_template('procedimentos/lista.html', procedimentos=repo.listar_ativos())


@procedimentos_bp.route('/novo', methods=['GET', 'POST'])
@requer_perfil('admin')
def novo():
    if request.method == 'POST':
        return _salvar(None)
    return render_template('procedimentos/form.html', proc=None)


@procedimentos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@requer_perfil('admin')
def editar(id):
    repo = procedimento_repo()
    proc = repo.buscar_por_id(id)
    if not proc:
        flash('Procedimento não encontrado.', 'erro')
        return redirect(url_for('procedimentos.index'))
    if request.method == 'POST':
        return _salvar(proc)
    return render_template('procedimentos/form.html', proc=proc)


@procedimentos_bp.route('/desativar/<int:id>', methods=['POST'])
@requer_perfil('admin')
def desativar(id):
    procedimento_repo().desativar(id)
    flash('Procedimento desativado.', 'sucesso')
    return redirect(url_for('procedimentos.index'))


def _salvar(proc_existente):
    repo = procedimento_repo()
    try:
        duracao_raw = request.form.get('duracao_minutos', '').strip()
        preco_raw   = request.form.get('preco_base', '').strip()
        retorno_raw = request.form.get('retorno_dias', '').strip()

        if not duracao_raw or not duracao_raw.lstrip('-').isdigit():
            raise DadosInvalidosError('Duração é obrigatória e deve ser um número inteiro.')

        duracao = int(duracao_raw)
        preco   = float(preco_raw) if preco_raw else None
        retorno_dias = int(retorno_raw) if retorno_raw else None

        if preco is not None and preco < 0:
            raise DadosInvalidosError('Preço não pode ser negativo.')

        dados = Procedimento(
            id=proc_existente.id if proc_existente else None,
            nome=request.form['nome'].strip(),
            duracao_minutos=duracao,
            cor_hex=request.form.get('cor_hex', '#e74c3c').strip(),
            preco_base=preco,
            retorno_dias=retorno_dias,
        )
    except (DadosInvalidosError, ValueError) as e:
        flash(str(e) if isinstance(e, DadosInvalidosError) else 'Valor inválido.', 'erro')
        return render_template('procedimentos/form.html',
                               proc=proc_existente, form_data=request.form)

    if proc_existente:
        repo.atualizar(dados)
        flash('Procedimento atualizado.', 'sucesso')
    else:
        repo.criar(dados)
        flash('Procedimento cadastrado.', 'sucesso')

    return redirect(url_for('procedimentos.index'))
