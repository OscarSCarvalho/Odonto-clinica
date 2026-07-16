from datetime import datetime
from unittest.mock import MagicMock
from app.application.sugerir_retorno import SugerirRetorno
from app.domain.entities.procedimento import Procedimento


def _proc(**kwargs):
    defaults = dict(id=1, nome='Limpeza', duracao_minutos=60, cor_hex='#e74c3c', retorno_dias=180)
    defaults.update(kwargs)
    return Procedimento(**defaults)


class TestSugerirRetorno:
    def test_calcula_data_de_retorno_quando_configurado(self):
        proc_repo = MagicMock()
        proc_repo.buscar_por_id.return_value = _proc(retorno_dias=180)
        uc = SugerirRetorno(proc_repo)

        resultado = uc.executar(1, '2026-01-01 09:00')

        assert resultado == datetime(2026, 6, 30, 9, 0)

    def test_retorna_none_quando_procedimento_sem_retorno_configurado(self):
        proc_repo = MagicMock()
        proc_repo.buscar_por_id.return_value = _proc(retorno_dias=None)
        uc = SugerirRetorno(proc_repo)

        assert uc.executar(1, '2026-01-01 09:00') is None

    def test_retorna_none_quando_procedimento_nao_encontrado(self):
        proc_repo = MagicMock()
        proc_repo.buscar_por_id.return_value = None
        uc = SugerirRetorno(proc_repo)

        assert uc.executar(999, '2026-01-01 09:00') is None
