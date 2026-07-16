from typing import Optional
from app.domain.entities.agendamento import Agendamento
from app.domain.entities.tarefa_retorno import TarefaRetorno
from app.domain.repositories.tarefa_retorno_repo import TarefaRetornoRepository
from app.application.sugerir_retorno import SugerirRetorno


class CriarTarefaRetorno:

    def __init__(self, tarefa_retorno_repo: TarefaRetornoRepository, sugerir_retorno: SugerirRetorno):
        self._tarefa_repo = tarefa_retorno_repo
        self._sugerir = sugerir_retorno

    def executar(self, agendamento: Agendamento) -> Optional[TarefaRetorno]:
        if self._tarefa_repo.buscar_por_agendamento(agendamento.id):
            return None

        sugestao = self._sugerir.executar(agendamento.procedimento_id, agendamento.data_hora_inicio)
        if not sugestao:
            return None

        tarefa = TarefaRetorno(
            id=None,
            agendamento_id=agendamento.id,
            paciente_id=agendamento.paciente_id,
            data_sugerida=sugestao.strftime('%Y-%m-%d'),
        )
        return self._tarefa_repo.criar(tarefa)
