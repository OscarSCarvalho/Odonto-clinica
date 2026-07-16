import pytest
from unittest.mock import MagicMock
from app.application.listar_slots_disponiveis import ListarSlotsDisponiveis
from app.domain.entities.profissional import Profissional
from app.domain.entities.procedimento import Procedimento


def _prof(inicio='08:00', fim='18:00', dias='1,2,3,4,5'):
    return Profissional(
        id=1, nome='Dr. Carlos', especialidade=None,
        cor_hex='#3498db', horario_inicio=inicio,
        horario_fim=fim, dias_semana=dias
    )


def _proc(duracao=30):
    return Procedimento(id=1, nome='Limpeza', duracao_minutos=duracao, cor_hex='#e74c3c')


def _uc(conflitos_por_slot=None, prof=None, proc=None):
    ag_repo   = MagicMock()
    prof_repo = MagicMock()
    proc_repo = MagicMock()

    prof_repo.buscar_por_id.return_value = prof or _prof()
    proc_repo.buscar_por_id.return_value = proc or _proc()

    # conflitos_por_slot: dict {slot_str: [agendamentos]} ou None (sem conflitos)
    def mock_conflitos(prof_id, inicio, fim, excluir_id=None):
        if conflitos_por_slot is None:
            return []
        slot = inicio[11:16]
        return conflitos_por_slot.get(slot, [])

    ag_repo.buscar_conflitos.side_effect = mock_conflitos
    return ListarSlotsDisponiveis(ag_repo, prof_repo, proc_repo)


class TestListarSlotsDisponiveis:
    def test_retorna_slots_livres(self):
        uc = _uc()
        slots = uc.executar(1, 1, '2026-07-21')  # segunda-feira
        assert '08:00' in slots
        assert '08:30' in slots
        assert '17:30' in slots  # último slot: 17:30 + 30min = 18:00 ≤ 18:00

    def test_exclui_slot_com_conflito(self):
        uc = _uc(conflitos_por_slot={'09:00': [MagicMock()]})
        slots = uc.executar(1, 1, '2026-07-21')
        assert '09:00' not in slots
        assert '08:00' in slots
        assert '09:30' in slots

    def test_dia_sem_expediente_retorna_vazio(self):
        # Domingo = weekday 6, não em '1,2,3,4,5'
        uc = _uc()
        slots = uc.executar(1, 1, '2026-07-19')  # domingo
        assert slots == []

    def test_quantidade_de_slots_correta(self):
        # 08:00 a 18:00, 30 min → 20 slots
        uc = _uc()
        slots = uc.executar(1, 1, '2026-07-21')
        assert len(slots) == 20

    def test_slots_com_duracao_60min(self):
        # 08:00 a 18:00, 60 min → 10 slots
        uc = _uc(proc=_proc(60))
        slots = uc.executar(1, 1, '2026-07-21')
        assert len(slots) == 10
        assert '08:00' in slots
        assert '17:00' in slots

    def test_ultimo_slot_nao_ultrapassa_expediente(self):
        # CB-02: slot que ultrapassa fim do expediente não deve aparecer
        # 17:45 + 30 min = 18:15 > 18:00 → não inclui
        uc = _uc(prof=_prof(inicio='08:00', fim='18:00'), proc=_proc(30))
        slots = uc.executar(1, 1, '2026-07-21')
        assert '17:30' in slots
        # 17:30 + 30 = 18:00 ≤ 18:00 → inclui
        # Garante que não há slot após 17:30 para duracao 30min
        assert all(s <= '17:30' for s in slots)

    def test_todos_slots_ocupados_retorna_vazio(self):
        # Todos os slots têm conflito
        todos = {f'{h:02d}:{m:02d}': [MagicMock()]
                 for h in range(8, 18) for m in (0, 30)}
        uc = _uc(conflitos_por_slot=todos)
        slots = uc.executar(1, 1, '2026-07-21')
        assert slots == []

    def test_sabado_sem_expediente(self):
        # Sábado = weekday 5 → armazenado como '6', não em '1,2,3,4,5'
        uc = _uc(prof=_prof(dias='1,2,3,4,5'))
        slots = uc.executar(1, 1, '2026-07-18')  # sábado
        assert slots == []

    def test_sabado_com_expediente(self):
        # Quando sábado está nos dias (armazenado como '6')
        uc = _uc(prof=_prof(dias='1,2,3,4,5,6'))
        slots = uc.executar(1, 1, '2026-07-18')  # sábado
        assert len(slots) > 0
