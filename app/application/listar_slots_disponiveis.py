from datetime import datetime, timedelta
from app.domain.repositories.agendamento_repo import AgendamentoRepository
from app.domain.repositories.profissional_repo import ProfissionalRepository
from app.domain.repositories.procedimento_repo import ProcedimentoRepository


class ListarSlotsDisponiveis:

    def __init__(
        self,
        agendamento_repo: AgendamentoRepository,
        profissional_repo: ProfissionalRepository,
        procedimento_repo: ProcedimentoRepository,
    ):
        self._ag_repo = agendamento_repo
        self._prof_repo = profissional_repo
        self._proc_repo = procedimento_repo

    def executar(self, profissional_id: int, procedimento_id: int, data: str) -> list[str]:
        """
        Retorna lista de horários "HH:MM" disponíveis para a data informada.
        Retorna [] se o profissional não trabalha nesse dia.
        """
        profissional = self._prof_repo.buscar_por_id(profissional_id)
        procedimento = self._proc_repo.buscar_por_id(procedimento_id)

        data_dt = datetime.strptime(data, '%Y-%m-%d')

        if not profissional.trabalha_no_dia(data_dt.weekday()):
            return []

        slots_candidatos = self._gerar_slots(
            data, profissional.horario_inicio,
            profissional.horario_fim, procedimento.duracao_minutos
        )

        slots_livres = []
        for slot in slots_candidatos:
            inicio = f'{data} {slot}'
            fim_dt = datetime.strptime(inicio, '%Y-%m-%d %H:%M') + timedelta(minutes=procedimento.duracao_minutos)
            fim = fim_dt.strftime('%Y-%m-%d %H:%M')

            conflitos = self._ag_repo.buscar_conflitos(profissional_id, inicio, fim)
            if not conflitos:
                slots_livres.append(slot)

        return slots_livres

    @staticmethod
    def _gerar_slots(data: str, h_inicio: str, h_fim: str, duracao: int) -> list[str]:
        inicio = datetime.strptime(f'{data} {h_inicio}', '%Y-%m-%d %H:%M')
        fim = datetime.strptime(f'{data} {h_fim}', '%Y-%m-%d %H:%M')
        slots = []
        atual = inicio
        while atual + timedelta(minutes=duracao) <= fim:
            slots.append(atual.strftime('%H:%M'))
            atual += timedelta(minutes=duracao)
        return slots
