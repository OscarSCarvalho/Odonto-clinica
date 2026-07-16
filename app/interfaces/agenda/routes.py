from datetime import datetime
from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, session)
from app.interfaces.auth.decorators import requer_login, requer_perfil
from app.domain.exceptions import ConflitodeHorarioError, HorarioForaDoExpedienteError, AgendamentoNaoEditavelError
from app.infrastructure.container import (
    profissional_repo, procedimento_repo, paciente_repo, agendamento_repo,
    criar_agendamento_uc, editar_agendamento_uc,
    cancelar_agendamento_uc, listar_agenda_uc, sugerir_retorno_uc, avancar_plano_uc,
)
from app.infrastructure.color_utils import darken_hex

agenda_bp = Blueprint('agenda', __name__, url_prefix='/agenda')

_STATUS_LABEL = {
    'agendado': 'Agendado',
    'confirmado': 'Confirmado',
    'aguardando': 'Aguardando atendimento',
    'em_atendimento': 'Em atendimento',
    'concluido': 'Concluído',
    'cancelado': 'Cancelado',
    'falta': 'Falta',
}

_STATUS_PROXIMOS = {
    'agendado': ['confirmado', 'aguardando', 'cancelado', 'falta'],
    'confirmado': ['aguardando', 'em_atendimento', 'cancelado', 'falta'],
    'aguardando': ['em_atendimento', 'cancelado', 'falta'],
    'em_atendimento': ['concluido'],
    'concluido': [],
    'cancelado': [],
    'falta': [],
}


# ── Página principal ──────────────────────────────────────────────────────────

@agenda_bp.route('/')
@agenda_bp.route('')
@requer_login
def index():
    profissionais = profissional_repo().listar_ativos()
    return render_template('agenda/index.html', profissionais=profissionais)


# ── API JSON para FullCalendar ────────────────────────────────────────────────

@agenda_bp.route('/api/eventos')
@requer_login
def api_eventos():
    inicio = request.args.get('start', '')[:16].replace('T', ' ')
    fim    = request.args.get('end',   '')[:16].replace('T', ' ')
    prof_id = request.args.get('profissional_id', type=int)

    # Profissional autenticado vê apenas seus próprios eventos (CB-08)
    if session.get('perfil') == 'profissional':
        from app.infrastructure.db.connection import get_db
        row = get_db().execute(
            'SELECT id FROM profissionais WHERE usuario_id = ?', (session['user_id'],)
        ).fetchone()
        if row:
            prof_id = row['id']

    agendamentos = listar_agenda_uc().executar(inicio, fim, prof_id)
    eventos = []
    for ag in agendamentos:
        cor = getattr(ag, 'procedimento_cor', '#2563eb')
        eventos.append({
            'id': ag.id,
            'title': f"{getattr(ag,'paciente_nome','?')} — {getattr(ag,'procedimento_nome','?')}",
            'start': ag.data_hora_inicio.replace(' ', 'T'),
            'end':   ag.data_hora_fim.replace(' ', 'T'),
            'backgroundColor': cor,
            'borderColor': darken_hex(cor),
            'extendedProps': {
                'paciente':     getattr(ag, 'paciente_nome', ''),
                'procedimento': getattr(ag, 'procedimento_nome', ''),
                'profissional': getattr(ag, 'profissional_nome', ''),
                'status':       ag.status,
            },
        })
    return jsonify(eventos)


@agenda_bp.route('/api/expedientes')
@requer_login
def api_expedientes():
    """Retorna businessHours por profissional para o FullCalendar."""
    _dia_armazenado_para_fc = {
        '0': 0,  # dom
        '1': 1,  # seg
        '2': 2,  # ter
        '3': 3,  # qua
        '4': 4,  # qui
        '5': 5,  # sex
        '6': 6,  # sáb
    }
    profissionais = profissional_repo().listar_ativos()
    result = []
    for p in profissionais:
        dias_fc = [_dia_armazenado_para_fc[d] for d in p.dias_semana.split(',') if d in _dia_armazenado_para_fc]
        result.append({
            'profissional_id': p.id,
            'daysOfWeek': dias_fc,
            'startTime': p.horario_inicio,
            'endTime':   p.horario_fim,
        })
    return jsonify(result)


@agenda_bp.route('/api/profissionais')
@requer_login
def api_profissionais():
    profs = profissional_repo().listar_ativos()
    return jsonify([{'id': p.id, 'nome': p.nome, 'cor': p.cor_hex} for p in profs])


# ── CRUD de agendamentos ──────────────────────────────────────────────────────

@agenda_bp.route('/novo', methods=['GET', 'POST'])
@requer_perfil('admin', 'recepcao')
def novo():
    if request.method == 'POST':
        return _criar()

    profissionais = profissional_repo().listar_ativos()
    procedimentos = procedimento_repo().listar_ativos()
    # Pré-preenchimento via querystring (clique no calendário, retorno sugerido ou recorrência)
    pre = {
        'profissional_id':      request.args.get('profissional_id', ''),
        'procedimento_id':      request.args.get('procedimento_id', ''),
        'data':                 request.args.get('data', ''),
        'hora':                 request.args.get('hora', ''),
        'paciente_id':          request.args.get('paciente_id', ''),
        'paciente_nome':        '',
        'plano_recorrente_id':  request.args.get('plano_recorrente_id', ''),
    }
    if pre['paciente_id']:
        pac = paciente_repo().buscar_por_id(int(pre['paciente_id']))
        pre['paciente_nome'] = pac.nome if pac else ''
    return render_template('agenda/form.html',
                           ag=None,
                           profissionais=profissionais,
                           procedimentos=procedimentos,
                           pre=pre,
                           status_label=_STATUS_LABEL)


@agenda_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@requer_perfil('admin', 'recepcao')
def editar(id):
    ag = agendamento_repo().buscar_por_id(id)
    if not ag:
        flash('Agendamento não encontrado.', 'erro')
        return redirect(url_for('agenda.index'))

    if request.method == 'POST':
        return _editar(ag)

    profissionais = profissional_repo().listar_ativos()
    procedimentos = procedimento_repo().listar_ativos()
    proximos_status = _STATUS_PROXIMOS.get(ag.status, [])

    sugestao_retorno = None
    if ag.status == 'concluido':
        sugestao_retorno = sugerir_retorno_uc().executar(ag.procedimento_id, ag.data_hora_inicio)

    return render_template('agenda/form.html',
                           ag=ag,
                           profissionais=profissionais,
                           procedimentos=procedimentos,
                           pre={},
                           status_label=_STATUS_LABEL,
                           proximos_status=proximos_status,
                           sugestao_retorno=sugestao_retorno)


@agenda_bp.route('/cancelar/<int:id>', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def cancelar(id):
    try:
        cancelar_agendamento_uc().executar(id)
        flash('Agendamento cancelado.', 'sucesso')
    except AgendamentoNaoEditavelError as e:
        flash(str(e), 'erro')
    return redirect(url_for('agenda.index'))


@agenda_bp.route('/status/<int:id>', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def mudar_status(id):
    novo_status = request.form.get('status')
    ag = agendamento_repo().buscar_por_id(id)
    try:
        editar_agendamento_uc().executar(id, status=novo_status)
        flash(f'Status atualizado para "{_STATUS_LABEL.get(novo_status, novo_status)}".', 'sucesso')
        if novo_status == 'concluido' and ag and ag.plano_recorrente_id:
            avancar_plano_uc().executar(ag.plano_recorrente_id, ag.data_hora_inicio)
    except AgendamentoNaoEditavelError as e:
        flash(str(e), 'erro')
    return redirect(url_for('agenda.editar', id=id))


# ── Helpers privados ──────────────────────────────────────────────────────────

def _criar():
    try:
        inicio = _parse_datetime(request.form.get('data_hora_inicio', ''))
        inicio_dt = datetime.strptime(inicio, '%Y-%m-%d %H:%M')
        if inicio_dt < datetime.now():
            flash('Não é possível criar agendamentos no passado.', 'erro')
            raise ValueError('data no passado')
        plano_id_raw = request.form.get('plano_recorrente_id', '').strip()
        ag = criar_agendamento_uc().executar(
            profissional_id=int(request.form['profissional_id']),
            paciente_id=int(request.form['paciente_id']),
            procedimento_id=int(request.form['procedimento_id']),
            data_hora_inicio=inicio,
            observacoes=request.form.get('observacoes', '').strip() or None,
            plano_recorrente_id=int(plano_id_raw) if plano_id_raw else None,
        )
        flash('Agendamento criado com sucesso.', 'sucesso')
        return redirect(url_for('agenda.index'))
    except (ConflitodeHorarioError, HorarioForaDoExpedienteError) as e:
        flash(str(e), 'erro')
    except (ValueError, KeyError):
        flash('Preencha todos os campos obrigatórios.', 'erro')

    profissionais = profissional_repo().listar_ativos()
    procedimentos = procedimento_repo().listar_ativos()
    return render_template('agenda/form.html',
                           ag=None, profissionais=profissionais,
                           procedimentos=procedimentos, pre={},
                           status_label=_STATUS_LABEL,
                           form_data=request.form), 422


def _editar(ag):
    try:
        inicio_raw = request.form.get('data_hora_inicio', '')
        inicio = _parse_datetime(inicio_raw) if inicio_raw else None
        editar_agendamento_uc().executar(
            agendamento_id=ag.id,
            profissional_id=int(request.form['profissional_id']),
            procedimento_id=int(request.form['procedimento_id']),
            data_hora_inicio=inicio,
            observacoes=request.form.get('observacoes', '').strip() or None,
        )
        flash('Agendamento atualizado.', 'sucesso')
        return redirect(url_for('agenda.index'))
    except AgendamentoNaoEditavelError as e:
        flash(str(e), 'erro')
    except (ConflitodeHorarioError, HorarioForaDoExpedienteError) as e:
        flash(str(e), 'erro')

    profissionais = profissional_repo().listar_ativos()
    procedimentos = procedimento_repo().listar_ativos()
    return render_template('agenda/form.html',
                           ag=ag, profissionais=profissionais,
                           procedimentos=procedimentos, pre={},
                           status_label=_STATUS_LABEL,
                           form_data=request.form), 422


def _parse_datetime(value: str) -> str:
    """Converte 'YYYY-MM-DDTHH:MM' ou 'YYYY-MM-DD HH:MM' para 'YYYY-MM-DD HH:MM'."""
    return value.replace('T', ' ')[:16]
