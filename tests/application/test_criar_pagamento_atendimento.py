from unittest.mock import MagicMock
from app.application.criar_pagamento_atendimento import CriarPagamentoAtendimento
from app.domain.entities.agendamento import Agendamento
from app.domain.entities.procedimento import Procedimento


def _ag(**kwargs):
    defaults = dict(
        id=1, profissional_id=1, paciente_id=2, procedimento_id=3,
        data_hora_inicio='2026-07-16 09:00', data_hora_fim='2026-07-16 09:30', status='concluido',
    )
    defaults.update(kwargs)
    return Agendamento(**defaults)


def _proc(**kwargs):
    defaults = dict(id=3, nome='Consulta', duracao_minutos=30, cor_hex='#2563eb', preco_base=150.0)
    defaults.update(kwargs)
    return Procedimento(**defaults)


def _uc(pagamento_existente=None, procedimento=None):
    pag_repo = MagicMock()
    pag_repo.buscar_por_agendamento.return_value = pagamento_existente
    proc_repo = MagicMock()
    proc_repo.buscar_por_id.return_value = procedimento
    return CriarPagamentoAtendimento(pag_repo, proc_repo), pag_repo, proc_repo


class TestCriarPagamentoAtendimento:
    def test_cria_pagamento_com_valor_do_procedimento(self):
        uc, pag_repo, _ = _uc(procedimento=_proc(preco_base=200.0))

        uc.executar(_ag())

        criado = pag_repo.criar.call_args[0][0]
        assert criado.paciente_id == 2
        assert criado.agendamento_id == 1
        assert criado.valor == 200.0
        assert criado.data_vencimento == '2026-07-16'

    def test_nao_cria_quando_procedimento_sem_preco(self):
        uc, pag_repo, _ = _uc(procedimento=_proc(preco_base=None))

        resultado = uc.executar(_ag())

        assert resultado is None
        pag_repo.criar.assert_not_called()

    def test_nao_duplica_pagamento_do_mesmo_agendamento(self):
        from app.domain.entities.pagamento import Pagamento
        existente = Pagamento(id=1, paciente_id=2, agendamento_id=1, valor=150.0, data_vencimento='2026-07-16')
        uc, pag_repo, proc_repo = _uc(pagamento_existente=existente)

        resultado = uc.executar(_ag())

        assert resultado is None
        pag_repo.criar.assert_not_called()
        proc_repo.buscar_por_id.assert_not_called()
