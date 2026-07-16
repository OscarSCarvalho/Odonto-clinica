from flask import Blueprint, render_template
from app.interfaces.auth.decorators import requer_login
from app.infrastructure.container import obter_dashboard_uc

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
    dados = obter_dashboard_uc().executar()
    return render_template('dashboard/index.html', dados=dados, status_label=_STATUS_LABEL)
