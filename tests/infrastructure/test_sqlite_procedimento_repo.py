import pytest
from app.domain.entities.procedimento import Procedimento
from app.domain.exceptions import DadosInvalidosError
from app.infrastructure.db.repositories.sqlite_procedimento_repo import SqliteProcedimentoRepository


def _repo(conn):
    return SqliteProcedimentoRepository(conn)


def _proc(**kwargs):
    defaults = dict(
        id=None, nome='Consulta', duracao_minutos=30, cor_hex='#2ecc71', preco_base=150.0
    )
    defaults.update(kwargs)
    return Procedimento(**defaults)


class TestSqliteProcedimentoRepo:
    def test_criar_e_buscar(self, conn):
        repo = _repo(conn)
        p = repo.criar(_proc())
        assert p.id is not None
        buscado = repo.buscar_por_id(p.id)
        assert buscado.nome == 'Consulta'
        assert buscado.duracao_minutos == 30

    def test_listar_ativos(self, conn):
        repo = _repo(conn)
        repo.criar(_proc(nome='Extração'))
        repo.criar(_proc(nome='Canal'))
        nomes = [p.nome for p in repo.listar_ativos()]
        assert 'Extração' in nomes
        assert 'Canal' in nomes

    def test_atualizar(self, conn):
        repo = _repo(conn)
        p = repo.criar(_proc())
        p.duracao_minutos = 45
        p.preco_base = 200.0
        repo.atualizar(p)
        assert repo.buscar_por_id(p.id).duracao_minutos == 45

    def test_desativar(self, conn):
        repo = _repo(conn)
        p = repo.criar(_proc())
        repo.desativar(p.id)
        assert repo.buscar_por_id(p.id).ativo is False
        nomes = [x.nome for x in repo.listar_ativos()]
        assert 'Consulta' not in nomes

    def test_duracao_invalida_no_criar(self, conn):
        # CB-05: duração < 5 min deve ser rejeitada na camada de infra também
        with pytest.raises(DadosInvalidosError):
            _proc(duracao_minutos=4)  # domínio já rejeita via __post_init__

    def test_buscar_inexistente(self, conn):
        assert _repo(conn).buscar_por_id(9999) is None
