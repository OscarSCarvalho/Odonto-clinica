from datetime import datetime, timedelta
from typing import Optional
from app.domain.repositories.agendamento_repo import AgendamentoRepository
from app.domain.repositories.procedimento_repo import ProcedimentoRepository
from app.application.verificar_conflito import VerificarConflito
from app.domain.exceptions import AgendamentoNaoEditavelError


class EditarAgendamento:

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
        agendamento_id: int,
        profissional_id: Optional[int] = None,
        procedimento_id: Optional[int] = None,
        data_hora_inicio: Optional[str] = None,
        observacoes: Optional[str] = None,
        status: Optional[str] = None,
    ):
        ag = self._ag_repo.buscar_por_id(agendamento_id)

        editando_horario = any([profissional_id, procedimento_id, data_hora_inicio])
        if editando_horario and not ag.pode_editar_horario():
            raise AgendamentoNaoEditavelError(ag.status)

        if profissional_id:
            ag.profissional_id = profissional_id
        if procedimento_id:
            ag.procedimento_id = procedimento_id
        if observacoes is not None:
            ag.observacoes = observacoes
        if status:
            ag.status = status

        if data_hora_inicio or procedimento_id:
            inicio = data_hora_inicio or ag.data_hora_inicio
            proc_id = procedimento_id or ag.procedimento_id
            procedimento = self._proc_repo.buscar_por_id(proc_id)
            inicio_dt = datetime.fromisoformat(inicio)
            fim_dt = inicio_dt + timedelta(minutes=procedimento.duracao_minutos)
            ag.data_hora_inicio = inicio
            ag.data_hora_fim = fim_dt.strftime('%Y-%m-%d %H:%M')

            self._verificar.executar(
                ag.profissional_id,
                ag.data_hora_inicio,
                ag.data_hora_fim,
                excluir_id=agendamento_id,
            )

        return self._ag_repo.atualizar(ag)
