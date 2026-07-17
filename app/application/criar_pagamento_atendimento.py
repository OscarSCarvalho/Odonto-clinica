from typing import Optional
from app.domain.entities.agendamento import Agendamento
from app.domain.entities.pagamento import Pagamento
from app.domain.repositories.pagamento_repo import PagamentoRepository
from app.domain.repositories.procedimento_repo import ProcedimentoRepository


class CriarPagamentoAtendimento:

    def __init__(self, pagamento_repo: PagamentoRepository, procedimento_repo: ProcedimentoRepository):
        self._pag_repo = pagamento_repo
        self._proc_repo = procedimento_repo

    def executar(self, agendamento: Agendamento) -> Optional[Pagamento]:
        if self._pag_repo.buscar_por_agendamento(agendamento.id):
            return None

        procedimento = self._proc_repo.buscar_por_id(agendamento.procedimento_id)
        if not procedimento or not procedimento.preco_base:
            return None

        pagamento = Pagamento(
            id=None,
            paciente_id=agendamento.paciente_id,
            agendamento_id=agendamento.id,
            valor=procedimento.preco_base,
            data_vencimento=agendamento.data_hora_inicio[:10],
        )
        return self._pag_repo.criar(pagamento)
