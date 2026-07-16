from typing import Optional
from app.domain.repositories.agendamento_repo import AgendamentoRepository


class RelatorioDesempenho:

    def __init__(self, agendamento_repo: AgendamentoRepository):
        self._ag_repo = agendamento_repo

    def executar(self, inicio: str, fim: str, profissional_id: Optional[int] = None) -> dict:
        agendamentos = self._ag_repo.listar_por_periodo(inicio, fim, profissional_id)
        concluidos = [a for a in agendamentos if a.status == 'concluido']

        por_profissional: dict = {}
        por_procedimento: dict = {}
        for a in concluidos:
            prof_nome = getattr(a, 'profissional_nome', '?')
            proc_nome = getattr(a, 'procedimento_nome', '?')
            preco = getattr(a, 'procedimento_preco', None) or 0

            d = por_profissional.setdefault(prof_nome, {'atendimentos': 0, 'faturamento': 0.0})
            d['atendimentos'] += 1
            d['faturamento'] += preco

            por_procedimento[proc_nome] = por_procedimento.get(proc_nome, 0) + 1

        return {
            'total_concluidos': len(concluidos),
            'por_profissional': sorted(
                por_profissional.items(), key=lambda kv: kv[1]['faturamento'], reverse=True
            ),
            'procedimentos_mais_realizados': sorted(
                por_procedimento.items(), key=lambda kv: kv[1], reverse=True
            ),
        }
