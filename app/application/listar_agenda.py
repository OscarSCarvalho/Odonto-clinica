from typing import Optional
from app.domain.repositories.agendamento_repo import AgendamentoRepository


class ListarAgenda:

    def __init__(self, agendamento_repo: AgendamentoRepository):
        self._repo = agendamento_repo

    def executar(
        self,
        inicio: str,
        fim: str,
        profissional_id: Optional[int] = None,
    ) -> list:
        return self._repo.listar_por_periodo(inicio, fim, profissional_id)
