from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.interfaces.auth.decorators import requer_perfil
from app.domain.entities.profissional import Profissional
from app.domain.exceptions import DadosInvalidosError
from app.infrastructure.container import profissional_repo

profissionais_bp = Blueprint('profissionais', __name__, url_prefix='/profissionais')

_DIAS = [
    (0, 'Dom'), (1, 'Seg'), (2, 'Ter'),
    (3, 'Qua'), (4, 'Qui'), (5, 'Sex'), (6, 'Sáb'),
]


@profissionais_bp.route('/')
@requer_perfil('admin')
def index():
    repo = profissional_repo()
    todos = repo.listar_ativos()
    return render_template('profissionais/lista.html', profissionais=todos)


@profissionais_bp.route('/novo', methods=['GET', 'POST'])
@requer_perfil('admin')
def novo():
    if request.method == 'POST':
        return _salvar(None)
    return render_template('profissionais/form.html', prof=None, dias=_DIAS)


@profissionais_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@requer_perfil('admin')
def editar(id):
    repo = profissional_repo()
    prof = repo.buscar_por_id(id)
    if not prof:
        flash('Profissional não encontrado.', 'erro')
        return redirect(url_for('profissionais.index'))
    if request.method == 'POST':
        return _salvar(prof)
    return render_template('profissionais/form.html', prof=prof, dias=_DIAS)


@profissionais_bp.route('/desativar/<int:id>', methods=['POST'])
@requer_perfil('admin')
def desativar(id):
    repo = profissional_repo()
    futuros = repo.desativar(id)
    if futuros:
        flash(f'Profissional desativado. {futuros} agendamento(s) futuro(s) foram afetados.', 'aviso')
    else:
        flash('Profissional desativado com sucesso.', 'sucesso')
    return redirect(url_for('profissionais.index'))


def _salvar(prof_existente):
    repo = profissional_repo()
    dias_sel = request.form.getlist('dias_semana')
    dias_str = ','.join(dias_sel) if dias_sel else '1,2,3,4,5'

    try:
        dados = Profissional(
            id=prof_existente.id if prof_existente else None,
            nome=request.form['nome'].strip(),
            especialidade=request.form.get('especialidade', '').strip() or None,
            cor_hex=request.form.get('cor_hex', '#2563eb').strip(),
            horario_inicio=request.form.get('horario_inicio', '08:00'),
            horario_fim=request.form.get('horario_fim', '18:00'),
            dias_semana=dias_str,
        )
    except DadosInvalidosError as e:
        flash(str(e), 'erro')
        return render_template('profissionais/form.html',
                               prof=prof_existente, dias=_DIAS,
                               form_data=request.form)

    if prof_existente:
        repo.atualizar(dados)
        flash('Profissional atualizado com sucesso.', 'sucesso')
    else:
        repo.criar(dados)
        flash('Profissional cadastrado com sucesso.', 'sucesso')

    return redirect(url_for('profissionais.index'))
