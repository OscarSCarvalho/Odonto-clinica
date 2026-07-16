from datetime import date
from unittest.mock import MagicMock
from app.application.listar_planos_vencendo import ListarPlanosVencendo
from app.domain.entities.plano_recorrente import PlanoRecorrente


def _plano(proxima_data, **kwargs):
    defaults = dict(
        id=1, paciente_id=1, profissional_id=1, procedimento_id=1,
        intervalo_dias=30, proxima_data=proxima_data,
    )
    defaults.update(kwargs)
    return PlanoRecorrente(**defaults)


def _uc(planos):
    repo = MagicMock()
    repo.listar_ativos.return_value = planos
    return ListarPlanosVencendo(repo), repo


class TestListarPlanosVencendo:
    def test_inclui_planos_dentro_da_janela(self):
        uc, _ = _uc([_plano('2026-07-20'), _plano('2026-08-15')])
        resultado = uc.executar(dias_janela=14, hoje=date(2026, 7, 16))
        datas = [p.proxima_data for p in resultado]
        assert datas == ['2026-07-20']

    def test_inclui_planos_atrasados(self):
        uc, _ = _uc([_plano('2026-07-01')])
        resultado = uc.executar(dias_janela=14, hoje=date(2026, 7, 16))
        assert len(resultado) == 1

    def test_ordenado_por_proxima_data(self):
        uc, _ = _uc([_plano('2026-07-25', id=2), _plano('2026-07-18', id=1)])
        resultado = uc.executar(dias_janela=30, hoje=date(2026, 7, 16))
        assert [p.id for p in resultado] == [1, 2]

    def test_repassa_apenas_planos_ativos_do_repositorio(self):
        uc, repo = _uc([])
        uc.executar(dias_janela=14, hoje=date(2026, 7, 16))
        repo.listar_ativos.assert_called_once()
