import os
import re
import uuid
from datetime import date
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, jsonify, send_from_directory, current_app, abort)
from werkzeug.utils import secure_filename
from app.interfaces.auth.decorators import requer_login, requer_perfil
from app.domain.entities.paciente import Paciente
from app.domain.entities.anexo import Anexo, EXTENSOES_PERMITIDAS
from app.domain.entities.plano_recorrente import PlanoRecorrente
from app.domain.entities.mensalidade import Mensalidade
from app.domain.exceptions import PacienteDuplicadoError, DadosInvalidosError
from app.infrastructure.container import (
    paciente_repo, anexo_repo, plano_recorrente_repo, profissional_repo, procedimento_repo,
    mensalidade_repo, pagamento_repo,
)


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
    return render_template('pacientes/form.html', pac=pac, **_contexto_form(pac))


@pacientes_bp.route('/desativar/<int:id>', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def desativar(id):
    paciente_repo().desativar(id)
    flash('Paciente desativado.', 'sucesso')
    return redirect(url_for('pacientes.index'))


@pacientes_bp.route('/<int:paciente_id>/anexos', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def upload_anexo(paciente_id):
    arquivo = request.files.get('arquivo')
    if not arquivo or not arquivo.filename:
        flash('Selecione um arquivo para enviar.', 'erro')
        return redirect(url_for('pacientes.editar', id=paciente_id))

    ext = os.path.splitext(arquivo.filename)[1].lower()
    if ext not in EXTENSOES_PERMITIDAS:
        flash('Formato não permitido. Envie JPG, PNG ou PDF.', 'erro')
        return redirect(url_for('pacientes.editar', id=paciente_id))

    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(paciente_id))
    os.makedirs(upload_dir, exist_ok=True)

    nome_salvo = f'{uuid.uuid4().hex}{ext}'
    arquivo.save(os.path.join(upload_dir, nome_salvo))

    anexo_repo().criar(Anexo(
        id=None,
        paciente_id=paciente_id,
        nome_original=secure_filename(arquivo.filename),
        caminho_arquivo=f'{paciente_id}/{nome_salvo}',
    ))
    flash('Arquivo anexado com sucesso.', 'sucesso')
    return redirect(url_for('pacientes.editar', id=paciente_id))


@pacientes_bp.route('/<int:paciente_id>/anexos/<int:anexo_id>/download')
@requer_login
def download_anexo(paciente_id, anexo_id):
    anexo = anexo_repo().buscar_por_id(anexo_id)
    if not anexo or anexo.paciente_id != paciente_id:
        abort(404)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'], anexo.caminho_arquivo,
        as_attachment=True, download_name=anexo.nome_original,
    )


@pacientes_bp.route('/<int:paciente_id>/anexos/<int:anexo_id>/excluir', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def excluir_anexo(paciente_id, anexo_id):
    anexo = anexo_repo().buscar_por_id(anexo_id)
    if anexo and anexo.paciente_id == paciente_id:
        caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], anexo.caminho_arquivo)
        try:
            os.remove(caminho)
        except OSError:
            pass
        anexo_repo().excluir(anexo_id)
        flash('Anexo removido.', 'sucesso')
    return redirect(url_for('pacientes.editar', id=paciente_id))


@pacientes_bp.route('/<int:paciente_id>/planos', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def criar_plano(paciente_id):
    try:
        intervalo_raw = request.form.get('intervalo_dias', '').strip()
        if not intervalo_raw or not intervalo_raw.isdigit():
            raise DadosInvalidosError('Informe um intervalo de recorrência válido, em dias.')

        proxima_data = request.form.get('proxima_data', '').strip() or date.today().isoformat()

        plano_recorrente_repo().criar(PlanoRecorrente(
            id=None,
            paciente_id=paciente_id,
            profissional_id=int(request.form['profissional_id']),
            procedimento_id=int(request.form['procedimento_id']),
            intervalo_dias=int(intervalo_raw),
            proxima_data=proxima_data,
            horario_preferido=request.form.get('horario_preferido', '').strip() or None,
            observacoes=request.form.get('observacoes', '').strip() or None,
        ))
        flash('Plano de recorrência criado.', 'sucesso')
    except (DadosInvalidosError, ValueError, KeyError) as e:
        mensagem = str(e) if isinstance(e, DadosInvalidosError) else 'Preencha profissional e procedimento.'
        flash(mensagem, 'erro')
    return redirect(url_for('pacientes.editar', id=paciente_id))


@pacientes_bp.route('/<int:paciente_id>/planos/<int:plano_id>/pausar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def pausar_plano(paciente_id, plano_id):
    plano_recorrente_repo().desativar(plano_id)
    flash('Plano de recorrência pausado.', 'sucesso')
    return redirect(url_for('pacientes.editar', id=paciente_id))


@pacientes_bp.route('/<int:paciente_id>/planos/<int:plano_id>/reativar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def reativar_plano(paciente_id, plano_id):
    plano_recorrente_repo().reativar(plano_id)
    flash('Plano de recorrência reativado.', 'sucesso')
    return redirect(url_for('pacientes.editar', id=paciente_id))


@pacientes_bp.route('/<int:paciente_id>/mensalidades', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def criar_mensalidade(paciente_id):
    try:
        valor_raw = request.form.get('valor', '').strip().replace(',', '.')
        dia_raw = request.form.get('dia_vencimento', '').strip()
        if not valor_raw or not dia_raw or not dia_raw.isdigit():
            raise DadosInvalidosError('Informe valor e dia de vencimento válidos.')

        mensalidade_repo().criar(Mensalidade(
            id=None,
            paciente_id=paciente_id,
            valor=float(valor_raw),
            dia_vencimento=int(dia_raw),
            observacoes=request.form.get('observacoes', '').strip() or None,
        ))
        flash('Mensalidade cadastrada.', 'sucesso')
    except (DadosInvalidosError, ValueError) as e:
        mensagem = str(e) if isinstance(e, DadosInvalidosError) else 'Valor ou dia de vencimento inválido.'
        flash(mensagem, 'erro')
    return redirect(url_for('pacientes.editar', id=paciente_id))


@pacientes_bp.route('/<int:paciente_id>/mensalidades/<int:mensalidade_id>/pausar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def pausar_mensalidade(paciente_id, mensalidade_id):
    mensalidade_repo().desativar(mensalidade_id)
    flash('Mensalidade pausada.', 'sucesso')
    return redirect(url_for('pacientes.editar', id=paciente_id))


@pacientes_bp.route('/<int:paciente_id>/mensalidades/<int:mensalidade_id>/reativar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def reativar_mensalidade(paciente_id, mensalidade_id):
    mensalidade_repo().reativar(mensalidade_id)
    flash('Mensalidade reativada.', 'sucesso')
    return redirect(url_for('pacientes.editar', id=paciente_id))


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


def _contexto_form(pac_existente):
    if not pac_existente:
        return {}
    return {
        'anexos': anexo_repo().listar_por_paciente(pac_existente.id),
        'planos': plano_recorrente_repo().listar_por_paciente(pac_existente.id),
        'mensalidades': mensalidade_repo().listar_por_paciente(pac_existente.id),
        'pagamentos': pagamento_repo().listar_por_paciente(pac_existente.id),
        'profissionais': profissional_repo().listar_ativos(),
        'procedimentos': procedimento_repo().listar_ativos(),
    }


def _salvar(pac_existente):
    repo = paciente_repo()

    # Validações antecipadas
    cpf_raw = request.form.get('cpf', '').strip()
    cpf_ok, cpf_msg = _validar_cpf(cpf_raw)
    if not cpf_ok:
        flash(cpf_msg, 'erro')
        return render_template('pacientes/form.html', pac=pac_existente, form_data=request.form,
                               **_contexto_form(pac_existente))

    dn_raw = request.form.get('data_nascimento', '').strip()
    if dn_raw:
        try:
            if date.fromisoformat(dn_raw) > date.today():
                flash('Data de nascimento não pode ser no futuro.', 'erro')
                return render_template('pacientes/form.html', pac=pac_existente, form_data=request.form,
                                       **_contexto_form(pac_existente))
        except ValueError:
            flash('Data de nascimento inválida.', 'erro')
            return render_template('pacientes/form.html', pac=pac_existente, form_data=request.form,
                                   **_contexto_form(pac_existente))

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
        return render_template('pacientes/form.html', pac=pac_existente, form_data=request.form,
                               **_contexto_form(pac_existente))
