from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.interfaces.auth.decorators import requer_perfil
from app.domain.exceptions import DadosInvalidosError
from app.infrastructure.container import (
    criar_orcamento_uc,
    obter_orcamento_uc,
    listar_orcamentos_uc,
    adicionar_item_orcamento_uc,
    remover_item_orcamento_uc,
    atualizar_orcamento_uc,
    enviar_orcamento_uc,
    aprovar_orcamento_uc,
    recusar_orcamento_uc,
    converter_orcamento_uc,
    paciente_repo,
    profissional_repo,
    procedimento_repo,
)

orcamentos_bp = Blueprint('orcamentos', __name__, url_prefix='/orcamentos')


@orcamentos_bp.route('/')
@orcamentos_bp.route('')
@requer_perfil('admin', 'recepcao')
def index():
    status = request.args.get('status', '').strip() or None
    orcamentos = listar_orcamentos_uc().executar(status=status)
    return render_template('orcamentos/index.html', orcamentos=orcamentos, status_filtro=status)


@orcamentos_bp.route('/novo', methods=['GET', 'POST'])
@requer_perfil('admin', 'recepcao')
def novo():
    if request.method == 'POST':
        try:
            paciente_id = request.form.get('paciente_id', type=int)
            profissional_id = request.form.get('profissional_id', type=int) or None
            validade_dias = request.form.get('validade_dias', 30, type=int)
            observacoes = request.form.get('observacoes', '').strip() or None

            if not paciente_id:
                raise DadosInvalidosError("Selecione um paciente")

            orcamento = criar_orcamento_uc().executar(
                paciente_id=paciente_id,
                profissional_id=profissional_id,
                validade_dias=validade_dias,
                observacoes=observacoes,
            )
            flash('Orçamento criado com sucesso.', 'sucesso')
            return redirect(url_for('orcamentos.detalhe', id=orcamento.id))
        except DadosInvalidosError as e:
            flash(str(e), 'erro')

    pacientes = paciente_repo().listar_todos_ativos()
    profissionais = profissional_repo().listar_ativos()
    return render_template('orcamentos/novo.html', pacientes=pacientes, profissionais=profissionais)


@orcamentos_bp.route('/<int:id>')
@requer_perfil('admin', 'recepcao')
def detalhe(id):
    try:
        orcamento = obter_orcamento_uc().executar(id)
    except DadosInvalidosError as e:
        flash(str(e), 'erro')
        return redirect(url_for('orcamentos.index'))

    procedimentos = procedimento_repo().listar_ativos()
    return render_template('orcamentos/detalhe.html', orcamento=orcamento, procedimentos=procedimentos)


@orcamentos_bp.route('/<int:id>/item/add', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def item_add(id):
    try:
        procedimento_ids = request.form.getlist('procedimento_id')
        if not procedimento_ids:
            raise DadosInvalidosError("Selecione ao menos um procedimento")

        uc = adicionar_item_orcamento_uc()
        for proc_id_str in procedimento_ids:
            proc_id = int(proc_id_str)
            quantidade = request.form.get(f'quantidade_{proc_id}', 1, type=int) or 1
            uc.executar(
                orcamento_id=id,
                procedimento_id=proc_id,
                quantidade=quantidade,
                valor_unitario=None,
                desconto_item=0,
                desconto_tipo='percentual',
            )

        total = len(procedimento_ids)
        flash(f'{total} procedimento(s) adicionado(s).', 'sucesso')
    except (DadosInvalidosError, ValueError) as e:
        flash(str(e), 'erro')
    return redirect(url_for('orcamentos.detalhe', id=id))


@orcamentos_bp.route('/<int:id>/item/<int:item_id>/remover', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def item_remover(id, item_id):
    try:
        remover_item_orcamento_uc().executar(item_id=item_id, orcamento_id=id)
        flash('Item removido.', 'sucesso')
    except DadosInvalidosError as e:
        flash(str(e), 'erro')
    return redirect(url_for('orcamentos.detalhe', id=id))


@orcamentos_bp.route('/<int:id>/editar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def editar(id):
    try:
        profissional_id = request.form.get('profissional_id', type=int) or None
        validade_dias = request.form.get('validade_dias', 30, type=int)
        desconto_global = request.form.get('desconto_global', 0.0, type=float)
        desconto_tipo = request.form.get('desconto_tipo', 'percentual').strip()
        observacoes = request.form.get('observacoes', '').strip() or None

        atualizar_orcamento_uc().executar(
            id=id,
            profissional_id=profissional_id,
            validade_dias=validade_dias,
            desconto_global=desconto_global,
            desconto_tipo=desconto_tipo,
            observacoes=observacoes,
        )
        flash('Orçamento atualizado.', 'sucesso')
    except DadosInvalidosError as e:
        flash(str(e), 'erro')
    return redirect(url_for('orcamentos.detalhe', id=id))


@orcamentos_bp.route('/<int:id>/enviar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def enviar(id):
    try:
        base_url = request.host_url.rstrip('/')
        enviar_orcamento_uc().executar(orcamento_id=id, base_url=base_url)
        flash('Orçamento enviado ao paciente.', 'sucesso')
    except DadosInvalidosError as e:
        flash(str(e), 'erro')
    return redirect(url_for('orcamentos.detalhe', id=id))


@orcamentos_bp.route('/<int:id>/aprovar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def aprovar(id):
    try:
        aprovar_orcamento_uc().executar(id=id)
        flash('Orçamento aprovado.', 'sucesso')
    except DadosInvalidosError as e:
        flash(str(e), 'erro')
    return redirect(url_for('orcamentos.detalhe', id=id))


@orcamentos_bp.route('/<int:id>/recusar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def recusar(id):
    try:
        recusar_orcamento_uc().executar(id=id)
        flash('Orçamento recusado.', 'sucesso')
    except DadosInvalidosError as e:
        flash(str(e), 'erro')
    return redirect(url_for('orcamentos.detalhe', id=id))


@orcamentos_bp.route('/<int:id>/converter', methods=['GET', 'POST'])
@requer_perfil('admin', 'recepcao')
def converter(id):
    try:
        orcamento = obter_orcamento_uc().executar(id)
    except DadosInvalidosError as e:
        flash(str(e), 'erro')
        return redirect(url_for('orcamentos.index'))

    if request.method == 'POST':
        try:
            agendamentos_data = []
            for item in orcamento.itens:
                profissional_id = request.form.get(f'profissional_id_{item.id}', type=int)
                data = request.form.get(f'data_{item.id}', '').strip()
                hora = request.form.get(f'hora_{item.id}', '').strip()

                if not profissional_id or not data or not hora:
                    raise DadosInvalidosError(f"Preencha todos os campos para o item #{item.id}")

                agendamentos_data.append({
                    'procedimento_id': item.procedimento_id,
                    'profissional_id': profissional_id,
                    'data_hora_inicio': f'{data} {hora}',
                })

            agendamentos = converter_orcamento_uc().executar(
                orcamento_id=id,
                agendamentos_data=agendamentos_data,
            )
            flash(f'{len(agendamentos)} agendamento(s) criado(s) com sucesso.', 'sucesso')
            return redirect(url_for('orcamentos.detalhe', id=id))
        except DadosInvalidosError as e:
            flash(str(e), 'erro')

    profissionais = profissional_repo().listar_ativos()
    return render_template('orcamentos/converter.html', orcamento=orcamento, profissionais=profissionais)
