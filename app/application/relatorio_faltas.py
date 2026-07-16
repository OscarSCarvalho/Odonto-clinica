from typing import Optional
from app.domain.repositories.agendamento_repo import AgendamentoRepository

STATUS_AUSENCIA = {'falta', 'cancelado'}


class RelatorioFaltas:

    def __init__(self, agendamento_repo: AgendamentoRepository):
        self._ag_repo = agendamento_repo

    def executar(self, inicio: str, fim: str, profissional_id: Optional[int] = None) -> dict:
        agendamentos = self._ag_repo.listar_por_periodo(inicio, fim, profissional_id)
        ausencias = [a for a in agendamentos if a.status in STATUS_AUSENCIA]

        por_profissional: dict = {}
        por_paciente: dict = {}
        for a in ausencias:
            prof_nome = getattr(a, 'profissional_nome', '?')
            pac_nome = getattr(a, 'paciente_nome', '?')
            por_profissional.setdefault(prof_nome, {'falta': 0, 'cancelado': 0})
            por_profissional[prof_nome][a.status] += 1
            por_paciente.setdefault(pac_nome, {'falta': 0, 'cancelado': 0})
            por_paciente[pac_nome][a.status] += 1

        return {
            'total_agendamentos': len(agendamentos),
            'total_faltas': sum(1 for a in ausencias if a.status == 'falta'),
            'total_cancelamentos': sum(1 for a in ausencias if a.status == 'cancelado'),
            'taxa_ausencia': (len(ausencias) / len(agendamentos) * 100) if agendamentos else 0.0,
            'por_profissional': por_profissional,
            'por_paciente': sorted(
                por_paciente.items(), key=lambda kv: sum(kv[1].values()), reverse=True
            ),
        }
