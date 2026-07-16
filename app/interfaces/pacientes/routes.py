import re
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.interfaces.auth.decorators import requer_login, requer_perfil
from app.domain.entities.paciente import Paciente
from app.domain.exceptions import PacienteDuplicadoError
from app.infrastructure.container import paciente_repo


def _validar_cpf(cpf_raw: str) -> tuple[bool, str]:
    """Retorna (valido, mensagem). CPF vazio é considerado válido (campo opcional)."""
    digitos = re.sub(r'\D', '', cpf_raw)
    if not digitos:
        return True, ''
    if len(digitos) != 11:
        return False, 'CPF deve ter 11 dígitos.'
    if len(set(digitos)) == 1:
        return False, 'CPF inválido.'
    # Cálculo dos dígitos verificadores
    for pos in range(9, 11):
        soma = sum(int(digitos[i]) * (pos + 1 - i) for i in range(pos))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if int(digitos[pos]) != esperado:
            return False, 'CPF inválido.'
    return True, ''

pacientes_bp = Blueprint('pacientes', __name__, url_prefix='/pacientes')


@pacientes_bp.route('/')
@requer_perfil('admin', 'recepcao')
def index():
    termo = request.args.get('q', '').strip()
    repo = paciente_repo()
    pacientes = repo.buscar_por_nome(termo, limite=50) if len(termo) >= 3 else []
    return render_template('pacientes/lista.html', pacientes=pacientes, termo=termo)


@pacientes_bp.route('/novo', methods=['GET', 'POST'])
@requer_perfil('admin', 'recepcao')
def novo():
    if request.method == 'POST':
        return _salvar(None)
    return render_template('pacientes/form.html', pac=None)


@pacientes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@requer_perfil('admin', 'recepcao')
def editar(id):
    repo = paciente_repo()
    pac = repo.buscar_por_id(id)
    if not pac:
        flash('Paciente não encontrado.', 'erro')
        return redirect(url_for('pacientes.index'))
    if request.method == 'POST':
        return _salvar(pac)
    return render_template('pacientes/form.html', pac=pac)


@pacientes_bp.route('/desativar/<int:id>', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def desativar(id):
    paciente_repo().desativar(id)
    flash('Paciente desativado.', 'sucesso')
    return redirect(url_for('pacientes.index'))


@pacientes_bp.route('/api/buscar')
@requer_login
def api_buscar():
    termo = request.args.get('q', '').strip()
    if len(termo) < 3:
        return jsonify([])
    pacientes = paciente_repo().buscar_por_nome(termo, limite=10)
    return jsonify([
        {'id': p.id, 'nome': p.nome, 'telefone': p.telefone or ''}
        for p in pacientes
    ])


def _salvar(pac_existente):
    repo = paciente_repo()

    # Validações antecipadas
    cpf_raw = request.form.get('cpf', '').strip()
    cpf_ok, cpf_msg = _validar_cpf(cpf_raw)
    if not cpf_ok:
        flash(cpf_msg, 'erro')
        return render_template('pacientes/form.html', pac=pac_existente, form_data=request.form)

    dn_raw = request.form.get('data_nascimento', '').strip()
    if dn_raw:
        try:
            if date.fromisoformat(dn_raw) > date.today():
                flash('Data de nascimento não pode ser no futuro.', 'erro')
                return render_template('pacientes/form.html', pac=pac_existente, form_data=request.form)
        except ValueError:
            flash('Data de nascimento inválida.', 'erro')
            return render_template('pacientes/form.html', pac=pac_existente, form_data=request.form)

    try:
        cpf_formatado = re.sub(r'\D', '', cpf_raw) or None
        dados = Paciente(
            id=pac_existente.id if pac_existente else None,
            nome=request.form['nome'].strip(),
            telefone=request.form.get('telefone', '').strip() or None,
            email=request.form.get('email', '').strip() or None,
            cpf=cpf_formatado,
            data_nascimento=dn_raw or None,
            observacoes=request.form.get('observacoes', '').strip() or None,
        )
        if pac_existente:
            repo.atualizar(dados)
            flash('Paciente atualizado.', 'sucesso')
        else:
            repo.criar(dados)
            flash('Paciente cadastrado.', 'sucesso')
        return redirect(url_for('pacientes.index'))

    except PacienteDuplicadoError as e:
        flash(f'{e} — <a href="{url_for("pacientes.editar", id=e.id_existente)}">ver cadastro</a>', 'erro')
        return render_template('pacientes/form.html', pac=pac_existente, form_data=request.form)
