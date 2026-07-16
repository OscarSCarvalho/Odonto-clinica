from unittest.mock import MagicMock
from app.application.avancar_plano_recorrente import AvancarPlanoRecorrente
from app.domain.entities.plano_recorrente import PlanoRecorrente


def _plano(**kwargs):
    defaults = dict(
        id=1, paciente_id=1, profissional_id=1, procedimento_id=1,
        intervalo_dias=30, proxima_data='2026-07-16', ativo=True,
    )
    defaults.update(kwargs)
    return PlanoRecorrente(**defaults)


class TestAvancarPlanoRecorrente:
    def test_avanca_proxima_data_pelo_intervalo(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = _plano(intervalo_dias=30)
        uc = AvancarPlanoRecorrente(repo)

        uc.executar(1, '2026-07-16 09:00')

        atualizado = repo.atualizar.call_args[0][0]
        assert atualizado.proxima_data == '2026-08-15'

    def test_nao_avanca_plano_pausado(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = _plano(ativo=False)
        uc = AvancarPlanoRecorrente(repo)

        uc.executar(1, '2026-07-16 09:00')

        repo.atualizar.assert_not_called()

    def test_nao_falha_quando_plano_nao_encontrado(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = None
        uc = AvancarPlanoRecorrente(repo)

        uc.executar(999, '2026-07-16 09:00')

        repo.atualizar.assert_not_called()
