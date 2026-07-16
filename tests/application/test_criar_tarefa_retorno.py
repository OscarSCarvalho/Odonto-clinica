from unittest.mock import MagicMock
from app.application.criar_tarefa_retorno import CriarTarefaRetorno
from app.domain.entities.agendamento import Agendamento


def _ag(**kwargs):
    defaults = dict(
        id=1, profissional_id=1, paciente_id=2, procedimento_id=3,
        data_hora_inicio='2026-07-16 09:00', data_hora_fim='2026-07-16 09:30', status='concluido',
    )
    defaults.update(kwargs)
    return Agendamento(**defaults)


def _uc(tarefa_existente=None, sugestao=None):
    tarefa_repo = MagicMock()
    tarefa_repo.buscar_por_agendamento.return_value = tarefa_existente
    sugerir = MagicMock()
    sugerir.executar.return_value = sugestao
    return CriarTarefaRetorno(tarefa_repo, sugerir), tarefa_repo, sugerir


class TestCriarTarefaRetorno:
    def test_cria_tarefa_quando_ha_sugestao_de_retorno(self):
        from datetime import datetime
        uc, tarefa_repo, _ = _uc(sugestao=datetime(2027, 1, 12, 9, 0))

        uc.executar(_ag())

        criada = tarefa_repo.criar.call_args[0][0]
        assert criada.agendamento_id == 1
        assert criada.paciente_id == 2
        assert criada.data_sugerida == '2027-01-12'

    def test_nao_cria_quando_procedimento_nao_tem_retorno_configurado(self):
        uc, tarefa_repo, _ = _uc(sugestao=None)

        resultado = uc.executar(_ag())

        assert resultado is None
        tarefa_repo.criar.assert_not_called()

    def test_nao_duplica_tarefa_para_o_mesmo_agendamento(self):
        from app.domain.entities.tarefa_retorno import TarefaRetorno
        existente = TarefaRetorno(id=1, agendamento_id=1, paciente_id=2, data_sugerida='2027-01-12')
        uc, tarefa_repo, sugerir = _uc(tarefa_existente=existente)

        resultado = uc.executar(_ag())

        assert resultado is None
        tarefa_repo.criar.assert_not_called()
        sugerir.executar.assert_not_called()
