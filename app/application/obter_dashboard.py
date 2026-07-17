from datetime import date, timedelta
from app.domain.repositories.agendamento_repo import AgendamentoRepository
from app.domain.repositories.paciente_repo import PacienteRepository
from app.domain.repositories.plano_recorrente_repo import PlanoRecorrenteRepository
from app.domain.repositories.tarefa_retorno_repo import TarefaRetornoRepository
from app.domain.repositories.pagamento_repo import PagamentoRepository


class ObterDashboard:

    def __init__(
        self,
        agendamento_repo: AgendamentoRepository,
        paciente_repo: PacienteRepository,
        plano_recorrente_repo: PlanoRecorrenteRepository,
        tarefa_retorno_repo: TarefaRetornoRepository,
        pagamento_repo: PagamentoRepository,
    ):
        self._agendamentos = agendamento_repo
        self._pacientes = paciente_repo
        self._planos = plano_recorrente_repo
        self._tarefas_retorno = tarefa_retorno_repo
        self._pagamentos = pagamento_repo

    def executar(self, hoje: date = None) -> dict:
        hoje = hoje or date.today()
        inicio = f'{hoje.isoformat()} 00:00'
        fim = f'{hoje.isoformat()} 23:59'

        agendamentos_hoje = self._agendamentos.listar_por_periodo(inicio, fim)

        contagem_status = {}
        faturamento_previsto = 0.0
        faturamento_realizado = 0.0
        for ag in agendamentos_hoje:
            contagem_status[ag.status] = contagem_status.get(ag.status, 0) + 1
            preco = getattr(ag, 'procedimento_preco', None) or 0
            if ag.status not in ('cancelado', 'falta'):
                faturamento_previsto += preco
            if ag.status == 'concluido':
                faturamento_realizado += preco

        proximos = sorted(
            (ag for ag in agendamentos_hoje if ag.status in ('agendado', 'confirmado')),
            key=lambda ag: ag.data_hora_inicio,
        )[:5]

        aniversariantes = self._pacientes.listar_aniversariantes_do_dia(hoje.month, hoje.day)

        limite_recorrentes = hoje + timedelta(days=7)
        recorrentes_vencendo = [
            p for p in self._planos.listar_ativos()
            if date.fromisoformat(p.proxima_data) <= limite_recorrentes
        ]

        pendentes = self._pagamentos.listar_pendentes()
        total_a_receber = sum(p.valor for p in pendentes)
        total_atrasado = sum(p.valor for p in pendentes if date.fromisoformat(p.data_vencimento) < hoje)

        return {
            'total_hoje': len(agendamentos_hoje),
            'contagem_status': contagem_status,
            'faturamento_previsto': faturamento_previsto,
            'faturamento_realizado': faturamento_realizado,
            'proximos_atendimentos': proximos,
            'aniversariantes': aniversariantes,
            'recorrentes_vencendo': recorrentes_vencendo,
            'retornos_pendentes': len(self._tarefas_retorno.listar_pendentes()),
            'total_a_receber': total_a_receber,
            'total_atrasado': total_atrasado,
        }
