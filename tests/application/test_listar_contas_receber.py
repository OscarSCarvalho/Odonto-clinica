from datetime import date
from unittest.mock import MagicMock
from app.application.listar_contas_receber import ListarContasReceber
from app.domain.entities.pagamento import Pagamento


def _pag(valor, vencimento, **kwargs):
    defaults = dict(id=1, paciente_id=1, valor=valor, data_vencimento=vencimento)
    defaults.update(kwargs)
    return Pagamento(**defaults)


def _uc(pendentes):
    repo = MagicMock()
    repo.listar_pendentes.return_value = pendentes
    return ListarContasReceber(repo), repo


class TestListarContasReceber:
    def test_soma_total_pendente(self):
        uc, _ = _uc([_pag(100, '2026-07-20'), _pag(200, '2026-07-25')])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['total_pendente'] == 300

    def test_calcula_total_atrasado(self):
        uc, _ = _uc([_pag(100, '2026-07-10'), _pag(200, '2026-07-25')])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['total_atrasado'] == 100
        assert resultado['quantidade_atrasada'] == 1

    def test_ordena_por_data_de_vencimento(self):
        uc, _ = _uc([_pag(200, '2026-07-25', id=2), _pag(100, '2026-07-18', id=1)])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert [p.id for p in resultado['pagamentos']] == [1, 2]

    def test_sem_pendencias_totais_zerados(self):
        uc, _ = _uc([])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['total_pendente'] == 0
        assert resultado['total_atrasado'] == 0
        assert resultado['quantidade_atrasada'] == 0
