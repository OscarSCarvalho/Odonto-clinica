from app.domain.entities.anexo import Anexo
from app.infrastructure.db.repositories.sqlite_anexo_repo import SqliteAnexoRepository


def _repo(conn):
    return SqliteAnexoRepository(conn)


def _anexo(paciente_id, **kwargs):
    defaults = dict(
        id=None, paciente_id=paciente_id,
        nome_original='exame.pdf', caminho_arquivo=f'{paciente_id}/abc.pdf',
    )
    defaults.update(kwargs)
    return Anexo(**defaults)


class TestSqliteAnexoRepo:
    def test_criar_e_buscar_por_id(self, conn, paciente_id):
        repo = _repo(conn)
        a = repo.criar(_anexo(paciente_id))
        assert a.id is not None
        buscado = repo.buscar_por_id(a.id)
        assert buscado.nome_original == 'exame.pdf'
        assert buscado.paciente_id == paciente_id

    def test_listar_por_paciente(self, conn, paciente_id):
        repo = _repo(conn)
        repo.criar(_anexo(paciente_id, nome_original='foto1.jpg'))
        repo.criar(_anexo(paciente_id, nome_original='foto2.jpg'))
        anexos = repo.listar_por_paciente(paciente_id)
        assert len(anexos) == 2
        nomes = {a.nome_original for a in anexos}
        assert nomes == {'foto1.jpg', 'foto2.jpg'}

    def test_listar_por_paciente_nao_retorna_de_outro_paciente(self, conn, paciente_id):
        repo = _repo(conn)
        repo.criar(_anexo(paciente_id))
        assert repo.listar_por_paciente(paciente_id + 999) == []

    def test_excluir(self, conn, paciente_id):
        repo = _repo(conn)
        a = repo.criar(_anexo(paciente_id))
        repo.excluir(a.id)
        assert repo.buscar_por_id(a.id) is None

    def test_buscar_inexistente(self, conn):
        assert _repo(conn).buscar_por_id(9999) is None
