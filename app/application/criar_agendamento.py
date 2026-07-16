from datetime import datetime, timedelta
from app.domain.entities.agendamento import Agendamento
from app.domain.repositories.agendamento_repo import AgendamentoRepository
from app.domain.repositories.procedimento_repo import ProcedimentoRepository
from app.application.verificar_conflito import VerificarConflito


class CriarAgendamento:

    def __init__(
        self,
        agendamento_repo: AgendamentoRepository,
        procedimento_repo: ProcedimentoRepository,
        verificar_conflito: VerificarConflito,
    ):
        self._ag_repo = agendamento_repo
        self._proc_repo = procedimento_repo
        self._verificar = verificar_conflito

    def executar(
        self,
        profissional_id: int,
        paciente_id: int,
        procedimento_id: int,
        data_hora_inicio: str,
        observacoes: str = None,
        origem: str = 'interno',
    ) -> Agendamento:
        procedimento = self._proc_repo.buscar_por_id(procedimento_id)
        inicio_dt = datetime.fromisoformat(data_hora_inicio)
        fim_dt = inicio_dt + timedelta(minutes=procedimento.duracao_minutos)
        data_hora_fim = fim_dt.strftime('%Y-%m-%d %H:%M')

        self._verificar.executar(profissional_id, data_hora_inicio, data_hora_fim)

        agendamento = Agendamento(
            id=None,
            profissional_id=profissional_id,
            paciente_id=paciente_id,
            procedimento_id=procedimento_id,
            data_hora_inicio=data_hora_inicio,
            data_hora_fim=data_hora_fim,
            observacoes=observacoes,
            origem=origem,
        )
        return self._ag_repo.criar(agendamento)
