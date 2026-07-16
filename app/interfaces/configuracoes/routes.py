from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.interfaces.auth.decorators import requer_perfil
from app.infrastructure.container import lembrete_repo
from app.domain.entities.lembrete import ConfigLembrete

configuracoes_bp = Blueprint('configuracoes', __name__, url_prefix='/configuracoes')


@configuracoes_bp.route('/lembretes')
@requer_perfil('admin')
def lembretes():
    repo = lembrete_repo()
    configs = repo.listar_configs()
    return render_template('configuracoes/lembretes.html', configs=configs)


@configuracoes_bp.route('/lembretes/novo', methods=['POST'])
@requer_perfil('admin')
def lembretes_novo():
    antecedencia_h = request.form.get('antecedencia_h', '').strip()
    tipo = request.form.get('tipo', '').strip()

    if not antecedencia_h or not antecedencia_h.isdigit():
        flash('Informe a antecedência em horas.', 'erro')
        return redirect(url_for('configuracoes.lembretes'))

    if tipo not in ('whatsapp', 'email'):
        flash('Tipo de lembrete inválido.', 'erro')
        return redirect(url_for('configuracoes.lembretes'))

    config = ConfigLembrete(id=None, antecedencia_h=int(antecedencia_h), tipo=tipo)
    lembrete_repo().criar_config(config)
    flash('Lembrete configurado com sucesso.', 'sucesso')
    return redirect(url_for('configuracoes.lembretes'))


@configuracoes_bp.route('/lembretes/<int:id>/toggle', methods=['POST'])
@requer_perfil('admin')
def lembretes_toggle(id):
    lembrete_repo().toggle_config(id)
    return redirect(url_for('configuracoes.lembretes'))


@configuracoes_bp.route('/lembretes/<int:id>/remover', methods=['POST'])
@requer_perfil('admin')
def lembretes_remover(id):
    lembrete_repo().remover_config(id)
    flash('Configuração removida.', 'sucesso')
    return redirect(url_for('configuracoes.lembretes'))
