from datetime import date
from flask import Blueprint, render_template, request
from app.interfaces.auth.decorators import requer_perfil
from app.infrastructure.container import (
    relatorio_faltas_uc, relatorio_pacientes_uc, relatorio_desempenho_uc, profissional_repo,
)

relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')


@relatorios_bp.route('/faltas')
@requer_perfil('admin', 'recepcao')
def faltas():
    hoje = date.today()
    inicio = request.args.get('inicio') or hoje.replace(day=1).isoformat()
    fim = request.args.get('fim') or hoje.isoformat()
    profissional_id = request.args.get('profissional_id', type=int)

    dados = relatorio_faltas_uc().executar(f'{inicio} 00:00', f'{fim} 23:59', profissional_id)
    profissionais = profissional_repo().listar_ativos()
    return render_template('relatorios/faltas.html',
                           dados=dados,
                           profissionais=profissionais,
                           inicio=inicio,
                           fim=fim,
                           profissional_id=profissional_id)


@relatorios_bp.route('/pacientes')
@requer_perfil('admin', 'recepcao')
def pacientes():
    dias_sem_retorno = request.args.get('dias', 90, type=int)
    dados = relatorio_pacientes_uc().executar(dias_sem_retorno=dias_sem_retorno)
    return render_template('relatorios/pacientes.html', dados=dados, dias_sem_retorno=dias_sem_retorno)


@relatorios_bp.route('/desempenho')
@requer_perfil('admin', 'recepcao')
def desempenho():
    hoje = date.today()
    inicio = request.args.get('inicio') or hoje.replace(day=1).isoformat()
    fim = request.args.get('fim') or hoje.isoformat()
    profissional_id = request.args.get('profissional_id', type=int)

    dados = relatorio_desempenho_uc().executar(f'{inicio} 00:00', f'{fim} 23:59', profissional_id)
    profissionais = profissional_repo().listar_ativos()
    return render_template('relatorios/desempenho.html',
                           dados=dados,
                           profissionais=profissionais,
                           inicio=inicio,
                           fim=fim,
                           profissional_id=profissional_id)
