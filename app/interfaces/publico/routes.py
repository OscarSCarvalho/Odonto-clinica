from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.domain.exceptions import ConflitodeHorarioError, HorarioForaDoExpedienteError
from app.infrastructure.container import (
    profissional_repo, procedimento_repo, agendamento_repo,
    listar_slots_uc, autoagendar_paciente_uc,
)

publico_bp = Blueprint('publico', __name__, url_prefix='/agendar')

_DIAS_PT = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']


# ── Step 1: Escolha do profissional ──────────────────────────────────────────

@publico_bp.route('/')
@publico_bp.route('')
def step1_profissional():
    profissionais = profissional_repo().listar_ativos()
    return render_template('publico/step1_profissional.html', profissionais=profissionais)


# ── Step 2: Escolha do procedimento ──────────────────────────────────────────

@publico_bp.route('/procedimento')
def step2_procedimento():
    prof_id = request.args.get('profissional_id', type=int)
    if not prof_id:
        return redirect(url_for('publico.step1_profissional'))

    profissional = profissional_repo().buscar_por_id(prof_id)
    if not profissional:
        return redirect(url_for('publico.step1_profissional'))

    procedimentos = procedimento_repo().listar_ativos()
    return render_template('publico/step2_procedimento.html',
                           profissional=profissional,
                           procedimentos=procedimentos)


# ── Step 3: Escolha da data e exibição de slots ───────────────────────────────

@publico_bp.route('/data')
def step3_data():
    prof_id = request.args.get('profissional_id', type=int)
    proc_id = request.args.get('procedimento_id', type=int)
    data_str = request.args.get('data', '')

    if not prof_id or not proc_id:
        return redirect(url_for('publico.step1_profissional'))

    profissional = profissional_repo().buscar_por_id(prof_id)
    procedimento = procedimento_repo().buscar_por_id(proc_id)
    if not profissional or not procedimento:
        return redirect(url_for('publico.step1_profissional'))

    slots = []
    data_valida = None
    erro_dia = False

    if data_str:
        try:
            data_valida = datetime.strptime(data_str, '%Y-%m-%d').date()
            if data_valida < date.today():
                data_str = ''
                data_valida = None
            else:
                slots = listar_slots_uc().executar(prof_id, proc_id, data_str)
                if not slots:
                    erro_dia = True
        except ValueError:
            data_str = ''

    data_min = date.today().strftime('%Y-%m-%d')
    data_max = (date.today() + timedelta(days=60)).strftime('%Y-%m-%d')

    return render_template('publico/step3_data.html',
                           profissional=profissional,
                           procedimento=procedimento,
                           data_str=data_str,
                           data_min=data_min,
                           data_max=data_max,
                           slots=slots,
                           erro_dia=erro_dia)


# ── Step 4: Dados pessoais ────────────────────────────────────────────────────

@publico_bp.route('/confirmar')
def step4_confirmar():
    prof_id = request.args.get('profissional_id', type=int)
    proc_id = request.args.get('procedimento_id', type=int)
    data_str = request.args.get('data', '')
    slot = request.args.get('slot', '')

    if not all([prof_id, proc_id, data_str, slot]):
        return redirect(url_for('publico.step1_profissional'))

    profissional = profissional_repo().buscar_por_id(prof_id)
    procedimento = procedimento_repo().buscar_por_id(proc_id)
    if not profissional or not procedimento:
        return redirect(url_for('publico.step1_profissional'))

    try:
        data_fmt = datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        dia_semana = _DIAS_PT[datetime.strptime(data_str, '%Y-%m-%d').weekday()]
    except ValueError:
        return redirect(url_for('publico.step1_profissional'))

    return render_template('publico/step4_confirmar.html',
                           profissional=profissional,
                           procedimento=procedimento,
                           data_str=data_str,
                           data_fmt=data_fmt,
                           dia_semana=dia_semana,
                           slot=slot)


# ── Step 5: Finalizar agendamento ─────────────────────────────────────────────

@publico_bp.route('/finalizar', methods=['POST'])
def finalizar():
    prof_id = request.form.get('profissional_id', type=int)
    proc_id = request.form.get('procedimento_id', type=int)
    data_str = request.form.get('data', '')
    slot = request.form.get('slot', '')
    nome = request.form.get('nome', '').strip()
    telefone = request.form.get('telefone', '').strip()
    email = request.form.get('email', '').strip() or None

    if not all([prof_id, proc_id, data_str, slot, nome, telefone]):
        flash('Preencha todos os campos obrigatórios.', 'erro')
        return redirect(url_for('publico.step4_confirmar',
                                profissional_id=prof_id, procedimento_id=proc_id,
                                data=data_str, slot=slot))

    data_hora_inicio = f'{data_str} {slot}'

    try:
        ag = autoagendar_paciente_uc().executar(
            profissional_id=prof_id,
            procedimento_id=proc_id,
            data_hora_inicio=data_hora_inicio,
            nome=nome,
            telefone=telefone,
            email=email,
        )
        return redirect(url_for('publico.sucesso', id=ag.id))

    except ConflitodeHorarioError:
        # Race condition: slot ocupado entre a seleção e o envio (CB no SPEC)
        flash('Este horário acabou de ser reservado por outro paciente. Escolha outro.', 'aviso')
        return redirect(url_for('publico.step3_data',
                                profissional_id=prof_id,
                                procedimento_id=proc_id,
                                data=data_str))

    except (HorarioForaDoExpedienteError, Exception) as e:
        flash(f'Não foi possível realizar o agendamento: {e}', 'erro')
        return redirect(url_for('publico.step3_data',
                                profissional_id=prof_id,
                                procedimento_id=proc_id,
                                data=data_str))


# ── Step 6: Confirmação ───────────────────────────────────────────────────────

@publico_bp.route('/sucesso/<int:id>')
def sucesso(id):
    ag = agendamento_repo().buscar_por_id(id)
    if not ag:
        return redirect(url_for('publico.step1_profissional'))

    try:
        data_fmt = datetime.strptime(ag.data_hora_inicio[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        dia_semana = _DIAS_PT[datetime.strptime(ag.data_hora_inicio[:10], '%Y-%m-%d').weekday()]
        hora_fmt = ag.data_hora_inicio[11:16]
    except (ValueError, IndexError):
        data_fmt = dia_semana = hora_fmt = '—'

    google_cal_url = _google_calendar_url(ag, data_fmt)

    return render_template('publico/sucesso.html',
                           ag=ag,
                           data_fmt=data_fmt,
                           dia_semana=dia_semana,
                           hora_fmt=hora_fmt,
                           google_cal_url=google_cal_url)


def _google_calendar_url(ag, data_fmt) -> str:
    try:
        inicio = ag.data_hora_inicio.replace(' ', 'T').replace(':', '').replace('-', '')
        fim = ag.data_hora_fim.replace(' ', 'T').replace(':', '').replace('-', '')
        titulo = f'Consulta%20{getattr(ag, "procedimento_nome", "")}%20-%20{getattr(ag, "profissional_nome", "")}'
        return (f'https://calendar.google.com/calendar/render?action=TEMPLATE'
                f'&text={titulo}&dates={inicio}/{fim}')
    except Exception:
        return ''
