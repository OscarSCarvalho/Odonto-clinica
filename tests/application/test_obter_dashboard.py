from datetime import date
from unittest.mock import MagicMock
from app.application.obter_dashboard import ObterDashboard
from app.domain.entities.agendamento import Agendamento
from app.domain.entities.paciente import Paciente
from app.domain.entities.plano_recorrente import PlanoRecorrente


def _ag(status, preco, inicio='2026-07-16 09:00'):
    a = Agendamento(
        id=1, profissional_id=1, paciente_id=1, procedimento_id=1,
        data_hora_inicio=inicio, data_hora_fim='2026-07-16 09:30', status=status,
    )
    a.paciente_nome = 'Maria'
    a.procedimento_nome = 'Limpeza'
    a.procedimento_preco = preco
    return a


def _uc(agendamentos=None, aniversariantes=None, planos=None):
    ag_repo = MagicMock()
    ag_repo.listar_por_periodo.return_value = agendamentos or []
    pac_repo = MagicMock()
    pac_repo.listar_aniversariantes_do_dia.return_value = aniversariantes or []
    plano_repo = MagicMock()
    plano_repo.listar_ativos.return_value = planos or []
    return ObterDashboard(ag_repo, pac_repo, plano_repo), ag_repo, pac_repo, plano_repo


class TestObterDashboard:
    def test_totais_e_contagem_por_status(self):
        uc, _, _, _ = _uc(agendamentos=[
            _ag('agendado', 100),
            _ag('confirmado', 150),
            _ag('cancelado', 200),
        ])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['total_hoje'] == 3
        assert resultado['contagem_status'] == {'agendado': 1, 'confirmado': 1, 'cancelado': 1}

    def test_faturamento_previsto_exclui_cancelado_e_falta(self):
        uc, _, _, _ = _uc(agendamentos=[
            _ag('agendado', 100),
            _ag('cancelado', 200),
            _ag('falta', 300),
        ])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['faturamento_previsto'] == 100

    def test_faturamento_realizado_soma_apenas_concluidos(self):
        uc, _, _, _ = _uc(agendamentos=[
            _ag('concluido', 120),
            _ag('agendado', 80),
        ])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['faturamento_realizado'] == 120

    def test_proximos_atendimentos_ordenados_e_limitados_a_5(self):
        agendamentos = [
            _ag('agendado', 100, inicio=f'2026-07-16 {h:02d}:00') for h in range(9, 16)
        ]
        uc, _, _, _ = _uc(agendamentos=agendamentos)
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert len(resultado['proximos_atendimentos']) == 5
        assert resultado['proximos_atendimentos'][0].data_hora_inicio == '2026-07-16 09:00'

    def test_aniversariantes_consulta_mes_e_dia_de_hoje(self):
        aniversariante = Paciente(id=1, nome='João', data_nascimento='1990-07-16')
        uc, _, pac_repo, _ = _uc(aniversariantes=[aniversariante])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        pac_repo.listar_aniversariantes_do_dia.assert_called_once_with(7, 16)
        assert resultado['aniversariantes'] == [aniversariante]

    def test_recorrentes_vencendo_em_ate_7_dias(self):
        plano_perto = PlanoRecorrente(
            id=1, paciente_id=1, profissional_id=1, procedimento_id=1,
            intervalo_dias=30, proxima_data='2026-07-20',
        )
        plano_longe = PlanoRecorrente(
            id=2, paciente_id=1, profissional_id=1, procedimento_id=1,
            intervalo_dias=30, proxima_data='2026-08-20',
        )
        uc, _, _, _ = _uc(planos=[plano_perto, plano_longe])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['recorrentes_vencendo'] == [plano_perto]
