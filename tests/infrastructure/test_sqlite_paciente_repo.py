import pytest
from app.domain.entities.paciente import Paciente
from app.domain.exceptions import PacienteDuplicadoError
from app.infrastructure.db.repositories.sqlite_paciente_repo import SqlitePacienteRepository


def _repo(conn):
    return SqlitePacienteRepository(conn)


def _pac(**kwargs):
    defaults = dict(
        id=None, nome='João Silva', telefone='11999990001',
        email='joao@email.com', cpf='123.456.789-00'
    )
    defaults.update(kwargs)
    return Paciente(**defaults)


class TestSqlitePacienteRepo:
    def test_criar_e_buscar_por_id(self, conn):
        repo = _repo(conn)
        p = repo.criar(_pac())
        assert p.id is not None
        assert repo.buscar_por_id(p.id).nome == 'João Silva'

    def test_buscar_por_cpf(self, conn):
        repo = _repo(conn)
        repo.criar(_pac(cpf='111.222.333-44'))
        encontrado = repo.buscar_por_cpf('11122233344')
        assert encontrado is not None
        assert encontrado.nome == 'João Silva'

    def test_buscar_por_cpf_com_mascara(self, conn):
        repo = _repo(conn)
        repo.criar(_pac(cpf='555.666.777-88'))
        assert repo.buscar_por_cpf('555.666.777-88') is not None

    def test_buscar_por_telefone(self, conn):
        repo = _repo(conn)
        repo.criar(_pac(cpf=None, telefone='11988887777'))
        encontrado = repo.buscar_por_telefone('11988887777')
        assert encontrado is not None

    def test_buscar_por_nome(self, conn):
        repo = _repo(conn)
        repo.criar(_pac(nome='Maria Aparecida', cpf='000.111.222-33'))
        repo.criar(_pac(nome='Maria Clara', cpf='000.111.222-44'))
        resultado = repo.buscar_por_nome('Maria')
        assert len(resultado) == 2

    def test_buscar_por_nome_minimo_3_chars(self, conn):
        repo = _repo(conn)
        repo.criar(_pac(nome='Jo Silva', cpf=None))
        assert repo.buscar_por_nome('Jo') == []

    def test_buscar_por_nome_limite(self, conn):
        repo = _repo(conn)
        for i in range(15):
            repo.criar(_pac(nome=f'Carlos {i}', cpf=None, telefone=None))
        resultado = repo.buscar_por_nome('Carlos', limite=10)
        assert len(resultado) <= 10

    def test_cpf_duplicado_lanca(self, conn):
        repo = _repo(conn)
        repo.criar(_pac(cpf='999.888.777-66'))
        with pytest.raises(PacienteDuplicadoError):
            repo.criar(_pac(nome='Outro Nome', cpf='999.888.777-66'))

    def test_atualizar(self, conn):
        repo = _repo(conn)
        p = repo.criar(_pac(cpf=None))
        p.nome = 'João Atualizado'
        repo.atualizar(p)
        assert repo.buscar_por_id(p.id).nome == 'João Atualizado'

    def test_desativar(self, conn):
        repo = _repo(conn)
        p = repo.criar(_pac(cpf=None))
        repo.desativar(p.id)
        assert repo.buscar_por_id(p.id).ativo is False

    def test_buscar_por_nome_nao_retorna_inativos(self, conn):
        repo = _repo(conn)
        p = repo.criar(_pac(nome='Zezinho Inativo', cpf=None))
        repo.desativar(p.id)
        assert repo.buscar_por_nome('Zezinho') == []

    def test_listar_aniversariantes_do_dia(self, conn):
        repo = _repo(conn)
        repo.criar(_pac(nome='Aniversariante Hoje', cpf=None, telefone=None,
                         data_nascimento='1990-07-16'))
        repo.criar(_pac(nome='Outro Dia', cpf=None, telefone=None,
                         data_nascimento='1990-08-20'))
        resultado = repo.listar_aniversariantes_do_dia(7, 16)
        assert len(resultado) == 1
        assert resultado[0].nome == 'Aniversariante Hoje'

    def test_listar_aniversariantes_ignora_inativos(self, conn):
        repo = _repo(conn)
        p = repo.criar(_pac(nome='Inativo Aniversario', cpf=None, telefone=None,
                             data_nascimento='1990-07-16'))
        repo.desativar(p.id)
        assert repo.listar_aniversariantes_do_dia(7, 16) == []
