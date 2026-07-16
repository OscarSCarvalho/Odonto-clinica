from app.domain.entities.plano_recorrente import PlanoRecorrente
from app.infrastructure.db.repositories.sqlite_plano_recorrente_repo import SqlitePlanoRecorrenteRepository


def _repo(conn):
    return SqlitePlanoRecorrenteRepository(conn)


def _plano(paciente_id, profissional_id, procedimento_id, **kwargs):
    defaults = dict(
        id=None, paciente_id=paciente_id, profissional_id=profissional_id,
        procedimento_id=procedimento_id, intervalo_dias=30, proxima_data='2026-08-01',
    )
    defaults.update(kwargs)
    return PlanoRecorrente(**defaults)


class TestSqlitePlanoRecorrenteRepo:
    def test_criar_e_buscar_por_id(self, conn, paciente_id, profissional_id, procedimento_id):
        repo = _repo(conn)
        p = repo.criar(_plano(paciente_id, profissional_id, procedimento_id))
        assert p.id is not None
        buscado = repo.buscar_por_id(p.id)
        assert buscado.intervalo_dias == 30
        assert buscado.proxima_data == '2026-08-01'
        assert buscado.ativo is True
        assert buscado.paciente_nome == 'Ana Paula'

    def test_listar_por_paciente(self, conn, paciente_id, profissional_id, procedimento_id):
        repo = _repo(conn)
        repo.criar(_plano(paciente_id, profissional_id, procedimento_id))
        planos = repo.listar_por_paciente(paciente_id)
        assert len(planos) == 1

    def test_listar_ativos_ignora_pausados(self, conn, paciente_id, profissional_id, procedimento_id):
        repo = _repo(conn)
        p1 = repo.criar(_plano(paciente_id, profissional_id, procedimento_id))
        p2 = repo.criar(_plano(paciente_id, profissional_id, procedimento_id, proxima_data='2026-09-01'))
        repo.desativar(p2.id)
        ativos = repo.listar_ativos()
        assert [p.id for p in ativos] == [p1.id]

    def test_atualizar_proxima_data(self, conn, paciente_id, profissional_id, procedimento_id):
        repo = _repo(conn)
        p = repo.criar(_plano(paciente_id, profissional_id, procedimento_id))
        p.proxima_data = '2026-09-01'
        repo.atualizar(p)
        assert repo.buscar_por_id(p.id).proxima_data == '2026-09-01'

    def test_desativar_e_reativar(self, conn, paciente_id, profissional_id, procedimento_id):
        repo = _repo(conn)
        p = repo.criar(_plano(paciente_id, profissional_id, procedimento_id))
        repo.desativar(p.id)
        assert repo.buscar_por_id(p.id).ativo is False
        repo.reativar(p.id)
        assert repo.buscar_por_id(p.id).ativo is True

    def test_buscar_inexistente(self, conn):
        assert _repo(conn).buscar_por_id(9999) is None
