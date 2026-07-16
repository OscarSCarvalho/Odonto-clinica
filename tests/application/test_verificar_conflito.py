import pytest
from unittest.mock import MagicMock
from app.application.verificar_conflito import VerificarConflito
from app.domain.entities.profissional import Profissional
from app.domain.entities.agendamento import Agendamento
from app.domain.exceptions import ConflitodeHorarioError, HorarioForaDoExpedienteError


def _profissional(inicio='08:00', fim='18:00', dias='1,2,3,4,5'):
    return Profissional(
        id=1, nome='Dr. Carlos', especialidade='Ortodontia',
        cor_hex='#3498db', horario_inicio=inicio, horario_fim=fim,
        dias_semana=dias
    )


def _ag_conflito(inicio, fim):
    a = Agendamento(
        id=99, profissional_id=1, paciente_id=2, procedimento_id=1,
        data_hora_inicio=inicio, data_hora_fim=fim
    )
    a.paciente_nome = 'João'
    a.procedimento_nome = 'Limpeza'
    return a


def _uc(conflitos=None, prof=None):
    ag_repo = MagicMock()
    ag_repo.buscar_conflitos.return_value = conflitos or []
    prof_repo = MagicMock()
    prof_repo.buscar_por_id.return_value = prof or _profissional()
    return VerificarConflito(ag_repo, prof_repo)


class TestVerificarConflito:
    def test_sem_conflito_passa(self):
        uc = _uc()
        uc.executar(1, '2026-07-21 09:00', '2026-07-21 09:30')  # segunda-feira

    def test_com_conflito_lanca(self):
        conflito = _ag_conflito('2026-07-21 09:00', '2026-07-21 09:30')
        uc = _uc(conflitos=[conflito])
        with pytest.raises(ConflitodeHorarioError):
            uc.executar(1, '2026-07-21 09:00', '2026-07-21 09:30')

    def test_fora_do_expediente_lanca(self):
        uc = _uc(prof=_profissional(inicio='08:00', fim='18:00'))
        with pytest.raises(HorarioForaDoExpedienteError):
            # CB-02: começa 17:40, 50min → fim 18:30 > 18:00
            uc.executar(1, '2026-07-21 17:40', '2026-07-21 18:30')

    def test_inicio_exato_no_fim_anterior_passa(self):
        # CB-03: sem sobreposição quando início = fim do anterior
        uc = _uc()
        uc.executar(1, '2026-07-21 09:30', '2026-07-21 10:00')

    def test_dia_sem_expediente_lanca(self):
        # Domingo = weekday 6 → armazenado 0, não em '1,2,3,4,5'
        uc = _uc(prof=_profissional(dias='1,2,3,4,5'))
        with pytest.raises(HorarioForaDoExpedienteError):
            uc.executar(1, '2026-07-19 09:00', '2026-07-19 09:30')  # domingo

    def test_excluir_id_passado_ao_repo(self):
        ag_repo = MagicMock()
        ag_repo.buscar_conflitos.return_value = []
        prof_repo = MagicMock()
        prof_repo.buscar_por_id.return_value = _profissional()
        uc = VerificarConflito(ag_repo, prof_repo)
        uc.executar(1, '2026-07-21 09:00', '2026-07-21 09:30', excluir_id=5)
        ag_repo.buscar_conflitos.assert_called_once_with(1, '2026-07-21 09:00', '2026-07-21 09:30', 5)
