from unittest.mock import MagicMock
from app.application.relatorio_desempenho import RelatorioDesempenho
from app.domain.entities.agendamento import Agendamento


def _ag(status, profissional='Dr. Carlos', procedimento='Limpeza', preco=100.0):
    a = Agendamento(
        id=1, profissional_id=1, paciente_id=1, procedimento_id=1,
        data_hora_inicio='2026-07-01 09:00', data_hora_fim='2026-07-01 09:30', status=status,
    )
    a.profissional_nome = profissional
    a.procedimento_nome = procedimento
    a.procedimento_preco = preco
    return a


def _uc(agendamentos):
    ag_repo = MagicMock()
    ag_repo.listar_por_periodo.return_value = agendamentos
    return RelatorioDesempenho(ag_repo), ag_repo


class TestRelatorioDesempenho:
    def test_conta_apenas_concluidos(self):
        uc, _ = _uc([_ag('concluido'), _ag('agendado'), _ag('cancelado')])
        resultado = uc.executar('2026-07-01 00:00', '2026-07-31 23:59')
        assert resultado['total_concluidos'] == 1

    def test_agrega_faturamento_e_atendimentos_por_profissional(self):
        uc, _ = _uc([
            _ag('concluido', profissional='Dr. Carlos', preco=100.0),
            _ag('concluido', profissional='Dr. Carlos', preco=150.0),
            _ag('concluido', profissional='Dra. Ana', preco=300.0),
        ])
        resultado = uc.executar('2026-07-01 00:00', '2026-07-31 23:59')
        por_profissional = dict(resultado['por_profissional'])
        assert por_profissional['Dr. Carlos'] == {'atendimentos': 2, 'faturamento': 250.0}
        assert por_profissional['Dra. Ana'] == {'atendimentos': 1, 'faturamento': 300.0}

    def test_ordena_profissionais_por_faturamento_desc(self):
        uc, _ = _uc([
            _ag('concluido', profissional='Dr. Carlos', preco=100.0),
            _ag('concluido', profissional='Dra. Ana', preco=300.0),
        ])
        resultado = uc.executar('2026-07-01 00:00', '2026-07-31 23:59')
        assert resultado['por_profissional'][0][0] == 'Dra. Ana'

    def test_procedimentos_mais_realizados_ordenado_por_quantidade(self):
        uc, _ = _uc([
            _ag('concluido', procedimento='Limpeza'),
            _ag('concluido', procedimento='Limpeza'),
            _ag('concluido', procedimento='Canal'),
        ])
        resultado = uc.executar('2026-07-01 00:00', '2026-07-31 23:59')
        assert resultado['procedimentos_mais_realizados'][0] == ('Limpeza', 2)

    def test_repassa_filtro_de_profissional_ao_repositorio(self):
        uc, ag_repo = _uc([])
        uc.executar('2026-07-01 00:00', '2026-07-31 23:59', profissional_id=7)
        ag_repo.listar_por_periodo.assert_called_once_with(
            '2026-07-01 00:00', '2026-07-31 23:59', 7
        )
