import pytest
from unittest.mock import MagicMock, patch
from app.application.autoagendar_paciente import AutoagendarPaciente
from app.domain.entities.paciente import Paciente
from app.domain.entities.agendamento import Agendamento
from app.domain.exceptions import ConflitodeHorarioError


def _pac(id=1, nome='Ana', telefone='11999990000'):
    return Paciente(id=id, nome=nome, telefone=telefone)


def _ag_salvo():
    return Agendamento(
        id=10, profissional_id=1, paciente_id=1, procedimento_id=1,
        data_hora_inicio='2026-07-21 09:00', data_hora_fim='2026-07-21 09:30',
        origem='autoagendamento'
    )


class TestAutoagendarPaciente:

    def _uc(self, paciente_existente=None, conflito=False):
        pac_repo = MagicMock()
        pac_repo.buscar_por_telefone.return_value = paciente_existente
        pac_repo.criar.return_value = _pac(id=99, nome='Novo', telefone='11988880000')

        criar_ag = MagicMock()
        if conflito:
            criar_ag.executar.side_effect = ConflitodeHorarioError(
                'Dr. Carlos', 'Limpeza', 'Outro', '09:00', '09:30'
            )
        else:
            criar_ag.executar.return_value = _ag_salvo()

        return AutoagendarPaciente(pac_repo, criar_ag)

    def test_vincula_paciente_existente(self):
        uc = self._uc(paciente_existente=_pac(id=5, telefone='11999990000'))
        ag = uc.executar(1, 1, '2026-07-21 09:00', 'Ana', '11999990000')
        assert ag.id == 10
        # Não deve criar novo paciente
        uc._pac_repo.criar.assert_not_called()

    def test_cria_paciente_novo_quando_nao_encontrado(self):
        uc = self._uc(paciente_existente=None)
        ag = uc.executar(1, 1, '2026-07-21 09:00', 'Novo Paciente', '11988880000')
        assert ag is not None
        uc._pac_repo.criar.assert_called_once()

    def test_propaga_race_condition(self):
        uc = self._uc(conflito=True)
        with pytest.raises(ConflitodeHorarioError):
            uc.executar(1, 1, '2026-07-21 09:00', 'Ana', '11999990000')

    def test_origem_autoagendamento(self):
        pac_repo = MagicMock()
        pac_repo.buscar_por_telefone.return_value = _pac()
        criar_ag = MagicMock()
        criar_ag.executar.return_value = _ag_salvo()
        uc = AutoagendarPaciente(pac_repo, criar_ag)
        uc.executar(1, 1, '2026-07-21 09:00', 'Ana', '11999990000')
        _, kwargs = criar_ag.executar.call_args
        assert kwargs.get('origem') == 'autoagendamento'

    def test_email_opcional(self):
        uc = self._uc(paciente_existente=None)
        ag = uc.executar(1, 1, '2026-07-21 09:00', 'Sem Email', '11977770000', email=None)
        assert ag is not None
