from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.interfaces.auth.decorators import requer_perfil
from app.domain.entities.pagamento import FORMAS_PAGAMENTO
from app.domain.exceptions import DadosInvalidosError
from app.infrastructure.container import listar_contas_receber_uc, gerar_cobrancas_mensalidades_uc, pagamento_repo

financeiro_bp = Blueprint('financeiro', __name__, url_prefix='/financeiro')


@financeiro_bp.route('/')
@financeiro_bp.route('')
@requer_perfil('admin', 'recepcao')
def index():
    gerar_cobrancas_mensalidades_uc().executar()
    dados = listar_contas_receber_uc().executar()
    return render_template('financeiro/index.html', dados=dados, hoje=date.today())


@financeiro_bp.route('/<int:id>/pagar', methods=['POST'])
@requer_perfil('admin', 'recepcao')
def pagar(id):
    try:
        forma_pagamento = request.form.get('forma_pagamento', '').strip()
        if forma_pagamento not in FORMAS_PAGAMENTO:
            raise DadosInvalidosError('Selecione uma forma de pagamento válida.')
        data_pagamento = request.form.get('data_pagamento', '').strip() or date.today().isoformat()
        observacoes = request.form.get('observacoes', '').strip() or None

        pagamento_repo().marcar_pago(id, forma_pagamento, data_pagamento, observacoes)
        flash('Pagamento registrado.', 'sucesso')
    except DadosInvalidosError as e:
        flash(str(e), 'erro')
    return redirect(url_for('financeiro.index'))
