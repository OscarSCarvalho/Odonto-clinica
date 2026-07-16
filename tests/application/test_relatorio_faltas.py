from unittest.mock import MagicMock
from app.application.relatorio_faltas import RelatorioFaltas
from app.domain.entities.agendamento import Agendamento


def _ag(status, profissional='Dr. Carlos', paciente='Maria'):
    a = Agendamento(
        id=1, profissional_id=1, paciente_id=1, procedimento_id=1,
        data_hora_inicio='2026-07-01 09:00', data_hora_fim='2026-07-01 09:30', status=status,
    )
    a.profissional_nome = profissional
    a.paciente_nome = paciente
    return a


def _uc(agendamentos):
    ag_repo = MagicMock()
    ag_repo.listar_por_periodo.return_value = agendamentos
    return RelatorioFaltas(ag_repo), ag_repo


class TestRelatorioFaltas:
    def test_totais_de_faltas_e_cancelamentos(self):
        uc, _ = _uc([_ag('falta'), _ag('cancelado'), _ag('concluido'), _ag('agendado')])
        resultado = uc.executar('2026-07-01 00:00', '2026-07-31 23:59')
        assert resultado['total_agendamentos'] == 4
        assert resultado['total_faltas'] == 1
        assert resultado['total_cancelamentos'] == 1

    def test_taxa_ausencia_calculada_sobre_total(self):
        uc, _ = _uc([_ag('falta'), _ag('falta'), _ag('concluido'), _ag('concluido')])
        resultado = uc.executar('2026-07-01 00:00', '2026-07-31 23:59')
        assert resultado['taxa_ausencia'] == 50.0

    def test_taxa_ausencia_zero_sem_agendamentos(self):
        uc, _ = _uc([])
        resultado = uc.executar('2026-07-01 00:00', '2026-07-31 23:59')
        assert resultado['taxa_ausencia'] == 0.0

    def test_agrupamento_por_profissional(self):
        uc, _ = _uc([
            _ag('falta', profissional='Dr. Carlos'),
            _ag('falta', profissional='Dr. Carlos'),
            _ag('cancelado', profissional='Dra. Ana'),
        ])
        resultado = uc.executar('2026-07-01 00:00', '2026-07-31 23:59')
        assert resultado['por_profissional']['Dr. Carlos'] == {'falta': 2, 'cancelado': 0}
        assert resultado['por_profissional']['Dra. Ana'] == {'falta': 0, 'cancelado': 1}

    def test_agrupamento_por_paciente_ordenado_por_total(self):
        uc, _ = _uc([
            _ag('falta', paciente='Maria'),
            _ag('falta', paciente='João'),
            _ag('cancelado', paciente='João'),
        ])
        resultado = uc.executar('2026-07-01 00:00', '2026-07-31 23:59')
        assert resultado['por_paciente'][0][0] == 'João'
        assert resultado['por_paciente'][0][1] == {'falta': 1, 'cancelado': 1}

    def test_repassa_filtro_de_profissional_ao_repositorio(self):
        uc, ag_repo = _uc([])
        uc.executar('2026-07-01 00:00', '2026-07-31 23:59', profissional_id=5)
        ag_repo.listar_por_periodo.assert_called_once_with(
            '2026-07-01 00:00', '2026-07-31 23:59', 5
        )
