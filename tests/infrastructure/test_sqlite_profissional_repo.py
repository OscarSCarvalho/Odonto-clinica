import pytest
from app.domain.entities.profissional import Profissional
from app.infrastructure.db.repositories.sqlite_profissional_repo import SqliteProfissionalRepository


def _repo(conn):
    return SqliteProfissionalRepository(conn)


def _prof(**kwargs):
    defaults = dict(
        id=None, nome='Dra. Beatriz', especialidade='Clínico Geral',
        cor_hex='#2ecc71', horario_inicio='09:00', horario_fim='17:00',
        dias_semana='1,2,3,4,5',
    )
    defaults.update(kwargs)
    return Profissional(**defaults)


class TestSqliteProfissionalRepo:
    def test_criar_e_buscar_por_id(self, conn):
        repo = _repo(conn)
        criado = repo.criar(_prof())
        assert criado.id is not None
        buscado = repo.buscar_por_id(criado.id)
        assert buscado.nome == 'Dra. Beatriz'

    def test_listar_ativos(self, conn):
        repo = _repo(conn)
        repo.criar(_prof(nome='Dr. A'))
        repo.criar(_prof(nome='Dr. B'))
        ativos = repo.listar_ativos()
        nomes = [p.nome for p in ativos]
        assert 'Dr. A' in nomes
        assert 'Dr. B' in nomes

    def test_atualizar(self, conn):
        repo = _repo(conn)
        p = repo.criar(_prof())
        p.nome = 'Dra. Beatriz Atualizada'
        p.cor_hex = '#9b59b6'
        repo.atualizar(p)
        buscado = repo.buscar_por_id(p.id)
        assert buscado.nome == 'Dra. Beatriz Atualizada'
        assert buscado.cor_hex == '#9b59b6'

    def test_desativar_sem_agendamentos_futuros(self, conn):
        repo = _repo(conn)
        p = repo.criar(_prof())
        futuros = repo.desativar(p.id)
        assert futuros == 0
        buscado = repo.buscar_por_id(p.id)
        assert not buscado.ativo

    def test_desativar_nao_aparece_em_listar_ativos(self, conn):
        repo = _repo(conn)
        p = repo.criar(_prof())
        repo.desativar(p.id)
        ativos = repo.listar_ativos()
        ids = [x.id for x in ativos]
        assert p.id not in ids

    def test_buscar_por_id_inexistente(self, conn):
        repo = _repo(conn)
        assert repo.buscar_por_id(9999) is None
