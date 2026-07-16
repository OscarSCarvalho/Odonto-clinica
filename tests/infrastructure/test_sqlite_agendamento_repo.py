import pytest
from app.domain.entities.agendamento import Agendamento
from app.infrastructure.db.repositories.sqlite_agendamento_repo import SqliteAgendamentoRepository


def _repo(conn):
    return SqliteAgendamentoRepository(conn)


def _ag(profissional_id, paciente_id, procedimento_id, inicio, fim, status='agendado'):
    return Agendamento(
        id=None,
        profissional_id=profissional_id,
        paciente_id=paciente_id,
        procedimento_id=procedimento_id,
        data_hora_inicio=inicio,
        data_hora_fim=fim,
        status=status,
    )


class TestSqliteAgendamentoRepo:
    def test_criar_e_buscar_por_id(self, conn, profissional_id, paciente_id, procedimento_id):
        repo = _repo(conn)
        ag = repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                             '2026-07-21 09:00', '2026-07-21 09:30'))
        assert ag.id is not None
        buscado = repo.buscar_por_id(ag.id)
        assert buscado.data_hora_inicio == '2026-07-21 09:00'
        assert hasattr(buscado, 'profissional_nome')
        assert hasattr(buscado, 'paciente_nome')

    def test_listar_por_periodo(self, conn, profissional_id, paciente_id, procedimento_id):
        repo = _repo(conn)
        repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                        '2026-07-21 09:00', '2026-07-21 09:30'))
        repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                        '2026-07-21 10:00', '2026-07-21 10:30'))
        # Fora do período
        repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                        '2026-07-25 09:00', '2026-07-25 09:30'))

        resultado = repo.listar_por_periodo('2026-07-21 00:00', '2026-07-22 00:00')
        assert len(resultado) == 2

    def test_listar_por_periodo_filtro_profissional(self, conn, profissional_id, paciente_id, procedimento_id):
        cur = conn.execute(
            "INSERT INTO profissionais (nome, cor_hex, horario_inicio, horario_fim, dias_semana) "
            "VALUES ('Dra. X', '#e74c3c', '08:00', '18:00', '1,2,3,4,5')"
        )
        conn.commit()
        outro_id = cur.lastrowid

        repo = _repo(conn)
        repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                        '2026-07-21 09:00', '2026-07-21 09:30'))
        repo.criar(_ag(outro_id, paciente_id, procedimento_id,
                        '2026-07-21 09:00', '2026-07-21 09:30'))

        resultado = repo.listar_por_periodo('2026-07-21 00:00', '2026-07-22 00:00',
                                             profissional_id=profissional_id)
        assert len(resultado) == 1
        assert resultado[0].profissional_id == profissional_id

    def test_buscar_conflitos_detecta_sobreposicao(self, conn, profissional_id, paciente_id, procedimento_id):
        repo = _repo(conn)
        repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                        '2026-07-21 09:00', '2026-07-21 09:30'))
        conflitos = repo.buscar_conflitos(profissional_id, '2026-07-21 09:15', '2026-07-21 09:45')
        assert len(conflitos) == 1

    def test_buscar_conflitos_sem_sobreposicao_borda(self, conn, profissional_id, paciente_id, procedimento_id):
        # CB-03: início = fim do anterior — sem sobreposição
        repo = _repo(conn)
        repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                        '2026-07-21 09:00', '2026-07-21 09:30'))
        conflitos = repo.buscar_conflitos(profissional_id, '2026-07-21 09:30', '2026-07-21 10:00')
        assert len(conflitos) == 0

    def test_buscar_conflitos_ignora_cancelado(self, conn, profissional_id, paciente_id, procedimento_id):
        # CB-04: cancelado não bloqueia
        repo = _repo(conn)
        repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                        '2026-07-21 09:00', '2026-07-21 09:30', status='cancelado'))
        conflitos = repo.buscar_conflitos(profissional_id, '2026-07-21 09:00', '2026-07-21 09:30')
        assert len(conflitos) == 0

    def test_buscar_conflitos_ignora_falta(self, conn, profissional_id, paciente_id, procedimento_id):
        repo = _repo(conn)
        repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                        '2026-07-21 09:00', '2026-07-21 09:30', status='falta'))
        conflitos = repo.buscar_conflitos(profissional_id, '2026-07-21 09:00', '2026-07-21 09:30')
        assert len(conflitos) == 0

    def test_buscar_conflitos_excluir_id(self, conn, profissional_id, paciente_id, procedimento_id):
        # Edição: exclui o próprio agendamento da checagem
        repo = _repo(conn)
        ag = repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                              '2026-07-21 09:00', '2026-07-21 09:30'))
        conflitos = repo.buscar_conflitos(profissional_id,
                                          '2026-07-21 09:00', '2026-07-21 09:30',
                                          excluir_id=ag.id)
        assert len(conflitos) == 0

    def test_atualizar_status(self, conn, profissional_id, paciente_id, procedimento_id):
        repo = _repo(conn)
        ag = repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                              '2026-07-21 09:00', '2026-07-21 09:30'))
        ag.status = 'confirmado'
        repo.atualizar(ag)
        assert repo.buscar_por_id(ag.id).status == 'confirmado'

    def test_diferentes_profissionais_mesmo_horario_sem_conflito(
            self, conn, profissional_id, paciente_id, procedimento_id):
        # CB-06: profissionais diferentes podem ter o mesmo slot
        cur = conn.execute(
            "INSERT INTO profissionais (nome, cor_hex, horario_inicio, horario_fim, dias_semana) "
            "VALUES ('Dra. Y', '#9b59b6', '08:00', '18:00', '1,2,3,4,5')"
        )
        conn.commit()
        outro_id = cur.lastrowid
        repo = _repo(conn)
        repo.criar(_ag(profissional_id, paciente_id, procedimento_id,
                        '2026-07-21 09:00', '2026-07-21 09:30'))
        # Checagem no profissional_id diferente não deve retornar conflito
        conflitos = repo.buscar_conflitos(outro_id, '2026-07-21 09:00', '2026-07-21 09:30')
        assert len(conflitos) == 0
