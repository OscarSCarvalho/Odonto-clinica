from app.domain.entities.tarefa_retorno import TarefaRetorno
from app.infrastructure.db.repositories.sqlite_tarefa_retorno_repo import SqliteTarefaRetornoRepository


def _repo(conn):
    return SqliteTarefaRetornoRepository(conn)


def _criar_agendamento(conn, profissional_id, paciente_id, procedimento_id):
    cur = conn.execute(
        "INSERT INTO agendamentos (profissional_id, paciente_id, procedimento_id, "
        "data_hora_inicio, data_hora_fim, status) VALUES (?,?,?,?,?,?)",
        (profissional_id, paciente_id, procedimento_id,
         '2026-07-01 09:00', '2026-07-01 09:30', 'concluido')
    )
    conn.commit()
    return cur.lastrowid


def _tarefa(agendamento_id, paciente_id, **kwargs):
    defaults = dict(id=None, agendamento_id=agendamento_id, paciente_id=paciente_id,
                     data_sugerida='2026-08-01')
    defaults.update(kwargs)
    return TarefaRetorno(**defaults)


class TestSqliteTarefaRetornoRepo:
    def test_criar_e_buscar_por_id(self, conn, profissional_id, paciente_id, procedimento_id):
        ag_id = _criar_agendamento(conn, profissional_id, paciente_id, procedimento_id)
        repo = _repo(conn)
        t = repo.criar(_tarefa(ag_id, paciente_id))
        assert t.id is not None
        buscada = repo.buscar_por_id(t.id)
        assert buscada.status == 'pendente'
        assert buscada.paciente_nome == 'Ana Paula'

    def test_buscar_por_agendamento(self, conn, profissional_id, paciente_id, procedimento_id):
        ag_id = _criar_agendamento(conn, profissional_id, paciente_id, procedimento_id)
        repo = _repo(conn)
        repo.criar(_tarefa(ag_id, paciente_id))
        assert repo.buscar_por_agendamento(ag_id) is not None
        assert repo.buscar_por_agendamento(9999) is None

    def test_listar_pendentes_ignora_contatados(self, conn, profissional_id, paciente_id, procedimento_id):
        ag1 = _criar_agendamento(conn, profissional_id, paciente_id, procedimento_id)
        ag2 = _criar_agendamento(conn, profissional_id, paciente_id, procedimento_id)
        repo = _repo(conn)
        t1 = repo.criar(_tarefa(ag1, paciente_id))
        repo.criar(_tarefa(ag2, paciente_id))
        repo.marcar_contatado(t1.id, 'Falou com o paciente')

        pendentes = repo.listar_pendentes()
        assert len(pendentes) == 1
        assert pendentes[0].agendamento_id == ag2

    def test_marcar_contatado_registra_observacao_e_data(self, conn, profissional_id, paciente_id, procedimento_id):
        ag_id = _criar_agendamento(conn, profissional_id, paciente_id, procedimento_id)
        repo = _repo(conn)
        t = repo.criar(_tarefa(ag_id, paciente_id))
        repo.marcar_contatado(t.id, 'Paciente vai remarcar')

        atualizada = repo.buscar_por_id(t.id)
        assert atualizada.status == 'contatado'
        assert atualizada.observacoes == 'Paciente vai remarcar'
        assert atualizada.contato_em is not None
