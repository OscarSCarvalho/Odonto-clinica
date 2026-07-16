from app.domain.repositories.agendamento_repo import AgendamentoRepository
from app.domain.exceptions import AgendamentoNaoEditavelError


class CancelarAgendamento:

    def __init__(self, agendamento_repo: AgendamentoRepository):
        self._repo = agendamento_repo

    def executar(self, agendamento_id: int):
        ag = self._repo.buscar_por_id(agendamento_id)
        if not ag.pode_cancelar():
            raise AgendamentoNaoEditavelError(ag.status)
        ag.status = 'cancelado'
        return self._repo.atualizar(ag)
