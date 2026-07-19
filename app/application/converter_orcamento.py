from datetime import date
from app.domain.entities.pagamento import Pagamento
from app.domain.repositories.orcamento_repo import OrcamentoRepository
from app.domain.repositories.pagamento_repo import PagamentoRepository
from app.domain.exceptions import DadosInvalidosError


class ConverterOrcamentoEmAgendamentos:

    def __init__(
        self,
        orcamento_repo: OrcamentoRepository,
        criar_agendamento_uc,
        pagamento_repo: PagamentoRepository,
    ):
        self._orcamento_repo = orcamento_repo
        self._criar_agendamento = criar_agendamento_uc
        self._pagamento_repo = pagamento_repo

    def executar(self, orcamento_id: int, agendamentos_data: list) -> list:
        orcamento = self._orcamento_repo.buscar_por_id(orcamento_id)
        if not orcamento:
            raise DadosInvalidosError("Orçamento não encontrado")
        if orcamento.status != 'aprovado':
            raise DadosInvalidosError("Somente orçamentos aprovados podem ser convertidos em agendamentos")

        agendamentos_criados = []
        for dados in agendamentos_data:
            ag = self._criar_agendamento.executar(
                profissional_id=dados['profissional_id'],
                paciente_id=orcamento.paciente_id,
                procedimento_id=dados['procedimento_id'],
                data_hora_inicio=dados['data_hora_inicio'],
            )
            agendamentos_criados.append(ag)

        total = orcamento.total_liquido
        if total > 0:
            pagamento = Pagamento(
                id=None,
                paciente_id=orcamento.paciente_id,
                valor=total,
                data_vencimento=date.today().isoformat(),
                observacoes=f"Orçamento #{orcamento_id}",
            )
            self._pagamento_repo.criar(pagamento)

        return agendamentos_criados
