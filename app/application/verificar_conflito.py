from datetime import datetime, time
from typing import Optional
from app.domain.repositories.agendamento_repo import AgendamentoRepository
from app.domain.repositories.profissional_repo import ProfissionalRepository
from app.domain.exceptions import ConflitodeHorarioError, HorarioForaDoExpedienteError


class VerificarConflito:

    def __init__(
        self,
        agendamento_repo: AgendamentoRepository,
        profissional_repo: ProfissionalRepository,
    ):
        self._ag_repo = agendamento_repo
        self._prof_repo = profissional_repo

    def executar(
        self,
        profissional_id: int,
        inicio: str,
        fim: str,
        excluir_id: Optional[int] = None,
    ) -> None:
        profissional = self._prof_repo.buscar_por_id(profissional_id)
        inicio_dt = datetime.fromisoformat(inicio)
        fim_dt = datetime.fromisoformat(fim)

        self._verificar_expediente(profissional, inicio_dt, fim_dt)
        self._verificar_sobreposicao(profissional_id, inicio, fim, excluir_id, profissional)

    def _verificar_expediente(self, profissional, inicio_dt, fim_dt):
        if not profissional.trabalha_no_dia(inicio_dt.weekday()):
            raise HorarioForaDoExpedienteError(
                profissional.nome,
                profissional.horario_inicio,
                profissional.horario_fim,
            )

        exp_inicio = time.fromisoformat(profissional.horario_inicio)
        exp_fim = time.fromisoformat(profissional.horario_fim)

        if inicio_dt.time() < exp_inicio or fim_dt.time() > exp_fim:
            raise HorarioForaDoExpedienteError(
                profissional.nome,
                profissional.horario_inicio,
                profissional.horario_fim,
            )

    def _verificar_sobreposicao(self, profissional_id, inicio, fim, excluir_id, profissional):
        conflitos = self._ag_repo.buscar_conflitos(
            profissional_id, inicio, fim, excluir_id
        )
        if conflitos:
            c = conflitos[0]
            raise ConflitodeHorarioError(
                profissional=profissional.nome,
                procedimento=getattr(c, 'procedimento_nome', 'procedimento'),
                paciente=getattr(c, 'paciente_nome', 'paciente'),
                inicio=c.data_hora_inicio[11:16],
                fim=c.data_hora_fim[11:16],
            )
