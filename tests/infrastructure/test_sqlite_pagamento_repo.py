from app.domain.entities.pagamento import Pagamento
from app.infrastructure.db.repositories.sqlite_pagamento_repo import SqlitePagamentoRepository


def _repo(conn):
    return SqlitePagamentoRepository(conn)


def _criar_agendamento(conn, profissional_id, paciente_id, procedimento_id, status='concluido'):
    cur = conn.execute(
        "INSERT INTO agendamentos (profissional_id, paciente_id, procedimento_id, "
        "data_hora_inicio, data_hora_fim, status) VALUES (?,?,?,?,?,?)",
        (profissional_id, paciente_id, procedimento_id,
         '2026-07-01 09:00', '2026-07-01 09:30', status)
    )
    conn.commit()
    return cur.lastrowid


def _pag(paciente_id, **kwargs):
    defaults = dict(id=None, paciente_id=paciente_id, valor=150.0, data_vencimento='2026-07-16')
    defaults.update(kwargs)
    return Pagamento(**defaults)


class TestSqlitePagamentoRepo:
    def test_criar_e_buscar_por_id(self, conn, paciente_id):
        repo = _repo(conn)
        p = repo.criar(_pag(paciente_id))
        assert p.id is not None
        buscado = repo.buscar_por_id(p.id)
        assert buscado.valor == 150.0
        assert buscado.status == 'pendente'
        assert buscado.paciente_nome == 'Ana Paula'

    def test_buscar_por_agendamento(self, conn, profissional_id, paciente_id, procedimento_id):
        ag_id = _criar_agendamento(conn, profissional_id, paciente_id, procedimento_id)
        repo = _repo(conn)
        repo.criar(_pag(paciente_id, agendamento_id=ag_id))
        assert repo.buscar_por_agendamento(ag_id) is not None
        assert repo.buscar_por_agendamento(9999) is None

    def test_buscar_por_mensalidade_e_competencia(self, conn, paciente_id):
        cur = conn.execute(
            "INSERT INTO mensalidades (paciente_id, valor, dia_vencimento) VALUES (?, ?, ?)",
            (paciente_id, 150.0, 10),
        )
        conn.commit()
        mensalidade_id = cur.lastrowid

        repo = _repo(conn)
        repo.criar(_pag(paciente_id, mensalidade_id=mensalidade_id, data_vencimento='2026-07-10'))
        assert repo.buscar_por_mensalidade_e_competencia(mensalidade_id, '2026-07') is not None
        assert repo.buscar_por_mensalidade_e_competencia(mensalidade_id, '2026-08') is None

    def test_listar_pendentes_ignora_pagos(self, conn, paciente_id):
        repo = _repo(conn)
        p1 = repo.criar(_pag(paciente_id, data_vencimento='2026-07-10'))
        repo.criar(_pag(paciente_id, data_vencimento='2026-07-20'))
        repo.marcar_pago(p1.id, 'pix', '2026-07-11', None)

        pendentes = repo.listar_pendentes()
        assert len(pendentes) == 1
        assert pendentes[0].data_vencimento == '2026-07-20'

    def test_listar_por_paciente(self, conn, paciente_id):
        repo = _repo(conn)
        repo.criar(_pag(paciente_id))
        repo.criar(_pag(paciente_id))
        assert len(repo.listar_por_paciente(paciente_id)) == 2

    def test_marcar_pago_registra_forma_e_data(self, conn, paciente_id):
        repo = _repo(conn)
        p = repo.criar(_pag(paciente_id))
        repo.marcar_pago(p.id, 'cartao_credito', '2026-07-17', 'Pago na recepção')

        atualizado = repo.buscar_por_id(p.id)
        assert atualizado.status == 'pago'
        assert atualizado.forma_pagamento == 'cartao_credito'
        assert atualizado.data_pagamento == '2026-07-17'
        assert atualizado.observacoes == 'Pago na recepção'

    def test_buscar_inexistente(self, conn):
        assert _repo(conn).buscar_por_id(9999) is None
