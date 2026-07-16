import pytest
from app.domain.entities.agendamento import Agendamento
from app.domain.entities.profissional import Profissional
from app.domain.entities.procedimento import Procedimento
from app.domain.exceptions import DadosInvalidosError


def ag(inicio, fim, status='agendado', id=1):
    return Agendamento(
        id=id, profissional_id=1, paciente_id=1, procedimento_id=1,
        data_hora_inicio=inicio, data_hora_fim=fim, status=status
    )


class TestSobreposicao:
    def test_sem_sobreposicao(self):
        a = ag('2026-07-20 09:00', '2026-07-20 09:30')
        b = ag('2026-07-20 09:30', '2026-07-20 10:00', id=2)
        assert not a.sobreposicao_com(b)  # CB-03

    def test_com_sobreposicao(self):
        a = ag('2026-07-20 09:00', '2026-07-20 09:30')
        b = ag('2026-07-20 09:15', '2026-07-20 09:45', id=2)
        assert a.sobreposicao_com(b)

    def test_cancelado_nao_bloqueia(self):
        a = ag('2026-07-20 09:00', '2026-07-20 09:30')
        b = ag('2026-07-20 09:15', '2026-07-20 09:45', status='cancelado', id=2)
        assert not a.sobreposicao_com(b)  # CB-04

    def test_falta_nao_bloqueia(self):
        a = ag('2026-07-20 09:00', '2026-07-20 09:30')
        b = ag('2026-07-20 09:15', '2026-07-20 09:45', status='falta', id=2)
        assert not a.sobreposicao_com(b)

    def test_sobreposicao_parcial_inicio(self):
        a = ag('2026-07-20 09:00', '2026-07-20 10:00')
        b = ag('2026-07-20 08:30', '2026-07-20 09:15', id=2)
        assert a.sobreposicao_com(b)

    def test_sobreposicao_completa(self):
        a = ag('2026-07-20 09:00', '2026-07-20 09:30')
        b = ag('2026-07-20 08:00', '2026-07-20 10:00', id=2)
        assert a.sobreposicao_com(b)


class TestProcedimento:
    def test_duracao_minima(self):
        with pytest.raises(DadosInvalidosError, match="5 minutos"):
            Procedimento(id=None, nome='Teste', duracao_minutos=4, cor_hex='#ff0000')

    def test_duracao_zero(self):
        with pytest.raises(DadosInvalidosError):
            Procedimento(id=None, nome='Teste', duracao_minutos=0, cor_hex='#ff0000')

    def test_cor_invalida(self):
        with pytest.raises(DadosInvalidosError, match="#RRGGBB"):
            Procedimento(id=None, nome='Teste', duracao_minutos=30, cor_hex='azul')

    def test_valido(self):
        p = Procedimento(id=1, nome='Limpeza', duracao_minutos=30, cor_hex='#e74c3c')
        assert p.nome == 'Limpeza'


class TestProfissional:
    def _prof(self, dias='1,2,3,4,5'):
        return Profissional(
            id=1, nome='Dr. Carlos', especialidade='Ortodontia',
            cor_hex='#3498db', horario_inicio='08:00', horario_fim='18:00',
            dias_semana=dias
        )

    def test_trabalha_dia_util(self):
        p = self._prof()
        assert p.trabalha_no_dia(0)  # segunda = weekday 0 → armazenado como 1

    def test_nao_trabalha_sabado(self):
        p = self._prof('1,2,3,4,5')
        assert not p.trabalha_no_dia(5)  # sábado = weekday 5 → armazenado como 6

    def test_cor_invalida(self):
        with pytest.raises(DadosInvalidosError):
            Profissional(
                id=None, nome='Dr. X', especialidade=None,
                cor_hex='#ZZZ', horario_inicio='08:00',
                horario_fim='18:00', dias_semana='1,2,3,4,5'
            )


class TestAgendamento:
    def test_pode_cancelar_agendado(self):
        a = ag('2026-07-20 09:00', '2026-07-20 09:30', status='agendado')
        assert a.pode_cancelar()

    def test_nao_pode_cancelar_concluido(self):
        a = ag('2026-07-20 09:00', '2026-07-20 09:30', status='concluido')
        assert not a.pode_cancelar()

    def test_pode_editar_agendado(self):
        a = ag('2026-07-20 09:00', '2026-07-20 09:30', status='agendado')
        assert a.pode_editar_horario()

    def test_nao_pode_editar_concluido(self):
        a = ag('2026-07-20 09:00', '2026-07-20 09:30', status='concluido')
        assert not a.pode_editar_horario()
