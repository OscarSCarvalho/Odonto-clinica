from flask import Blueprint, render_template
from app.interfaces.auth.decorators import requer_login
from app.infrastructure.container import obter_dashboard_uc, gerar_cobrancas_mensalidades_uc, orcamento_repo

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

_STATUS_LABEL = {
    'agendado': 'Agendado',
    'confirmado': 'Confirmado',
    'em_atendimento': 'Em atendimento',
    'concluido': 'Concluído',
    'cancelado': 'Cancelado',
    'falta': 'Falta',
}


@dashboard_bp.route('/')
@dashboard_bp.route('')
@requer_login
def index():
    from app.application.obter_dashboard import ObterDashboard
    from app.infrastructure.container import (
        agendamento_repo, paciente_repo, plano_recorrente_repo,
        tarefa_retorno_repo, pagamento_repo,
    )
    gerar_cobrancas_mensalidades_uc().executar()
    uc = ObterDashboard(
        agendamento_repo(), paciente_repo(), plano_recorrente_repo(),
        tarefa_retorno_repo(), pagamento_repo(), orcamento_repo(),
    )
    dados = uc.executar()
    return render_template('dashboard/index.html', dados=dados, status_label=_STATUS_LABEL)
