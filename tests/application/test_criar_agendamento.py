import pytest
from unittest.mock import MagicMock, patch
from app.application.criar_agendamento import CriarAgendamento
from app.domain.entities.agendamento import Agendamento
from app.domain.entities.procedimento import Procedimento
from app.domain.exceptions import ConflitodeHorarioError


def _procedimento(duracao=30):
    return Procedimento(id=1, nome='Limpeza', duracao_minutos=duracao, cor_hex='#e74c3c')


def _agendamento_salvo():
    return Agendamento(
        id=42, profissional_id=1, paciente_id=1, procedimento_id=1,
        data_hora_inicio='2026-07-21 09:00', data_hora_fim='2026-07-21 09:30'
    )


class TestCriarAgendamento:
    def _uc(self, conflito=False, duracao=30):
        ag_repo = MagicMock()
        ag_repo.criar.return_value = _agendamento_salvo()

        proc_repo = MagicMock()
        proc_repo.buscar_por_id.return_value = _procedimento(duracao)

        verificar = MagicMock()
        if conflito:
            verificar.executar.side_effect = ConflitodeHorarioError(
                'Dr. Carlos', 'Limpeza', 'João', '09:00', '09:30'
            )

        return CriarAgendamento(ag_repo, proc_repo, verificar)

    def test_cria_agendamento_com_sucesso(self):
        uc = self._uc()
        resultado = uc.executar(1, 1, 1, '2026-07-21 09:00')
        assert resultado.id == 42

    def test_calcula_fim_automaticamente(self):
        ag_repo = MagicMock()
        ag_repo.criar.side_effect = lambda a: a
        proc_repo = MagicMock()
        proc_repo.buscar_por_id.return_value = _procedimento(45)
        verificar = MagicMock()
        uc = CriarAgendamento(ag_repo, proc_repo, verificar)
        resultado = uc.executar(1, 1, 1, '2026-07-21 09:00')
        assert resultado.data_hora_fim == '2026-07-21 09:45'

    def test_conflito_bloqueia(self):
        uc = self._uc(conflito=True)
        with pytest.raises(ConflitodeHorarioError):
            uc.executar(1, 1, 1, '2026-07-21 09:00')

    def test_origem_autoagendamento(self):
        ag_repo = MagicMock()
        ag_repo.criar.side_effect = lambda a: a
        proc_repo = MagicMock()
        proc_repo.buscar_por_id.return_value = _procedimento()
        verificar = MagicMock()
        uc = CriarAgendamento(ag_repo, proc_repo, verificar)
        resultado = uc.executar(1, 1, 1, '2026-07-21 09:00', origem='autoagendamento')
        assert resultado.origem == 'autoagendamento'
