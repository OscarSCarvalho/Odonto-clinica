from app.domain.entities.mensalidade import Mensalidade
from app.infrastructure.db.repositories.sqlite_mensalidade_repo import SqliteMensalidadeRepository


def _repo(conn):
    return SqliteMensalidadeRepository(conn)


def _mensalidade(paciente_id, **kwargs):
    defaults = dict(id=None, paciente_id=paciente_id, valor=150.0, dia_vencimento=10)
    defaults.update(kwargs)
    return Mensalidade(**defaults)


class TestSqliteMensalidadeRepo:
    def test_criar_e_buscar_por_id(self, conn, paciente_id):
        repo = _repo(conn)
        m = repo.criar(_mensalidade(paciente_id))
        assert m.id is not None
        buscada = repo.buscar_por_id(m.id)
        assert buscada.valor == 150.0
        assert buscada.ativo is True
        assert buscada.paciente_nome == 'Ana Paula'

    def test_listar_por_paciente(self, conn, paciente_id):
        repo = _repo(conn)
        repo.criar(_mensalidade(paciente_id))
        assert len(repo.listar_por_paciente(paciente_id)) == 1

    def test_listar_ativas_ignora_pausadas(self, conn, paciente_id):
        repo = _repo(conn)
        m1 = repo.criar(_mensalidade(paciente_id))
        m2 = repo.criar(_mensalidade(paciente_id))
        repo.desativar(m2.id)
        ativas = repo.listar_ativas()
        assert [m.id for m in ativas] == [m1.id]

    def test_desativar_e_reativar(self, conn, paciente_id):
        repo = _repo(conn)
        m = repo.criar(_mensalidade(paciente_id))
        repo.desativar(m.id)
        assert repo.buscar_por_id(m.id).ativo is False
        repo.reativar(m.id)
        assert repo.buscar_por_id(m.id).ativo is True

    def test_buscar_inexistente(self, conn):
        assert _repo(conn).buscar_por_id(9999) is None
