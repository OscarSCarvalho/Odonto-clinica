from datetime import date
from flask import Blueprint, render_template, request
from app.interfaces.auth.decorators import requer_perfil
from app.infrastructure.container import listar_planos_vencendo_uc

recorrentes_bp = Blueprint('recorrentes', __name__, url_prefix='/recorrentes')


@recorrentes_bp.route('/')
@recorrentes_bp.route('')
@requer_perfil('admin', 'recepcao')
def index():
    dias_janela = request.args.get('dias', 14, type=int)
    planos = listar_planos_vencendo_uc().executar(dias_janela=dias_janela)
    hoje = date.today()
    return render_template('recorrentes/index.html', planos=planos, dias_janela=dias_janela, hoje=hoje)
