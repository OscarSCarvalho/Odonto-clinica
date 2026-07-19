import pytest
from app.domain.entities.orcamento import Orcamento, OrcamentoItem
from app.infrastructure.db.repositories.sqlite_orcamento_repo import SqliteOrcamentoRepository


@pytest.fixture
def repo(conn):
    return SqliteOrcamentoRepository(conn)


@pytest.fixture
def procedimento_com_preco_id(conn):
    cur = conn.execute(
        "INSERT INTO procedimentos (nome, duracao_minutos, cor_hex, preco_base) VALUES ('Extração', 45, '#0d9488', 250.0)"
    )
    conn.commit()
    return cur.lastrowid


class TestSqliteOrcamentoRepo:

    def test_criar_e_buscar_por_id(self, repo, conn, paciente_id):
        o = Orcamento(id=None, paciente_id=paciente_id, validade_dias=30)
        criado = repo.criar(o)

        assert criado.id is not None
        encontrado = repo.buscar_por_id(criado.id)
        assert encontrado is not None
        assert encontrado.paciente_id == paciente_id
        assert encontrado.status == 'rascunho'
        assert encontrado.paciente_nome == 'Ana Paula'

    def test_buscar_por_id_inexistente(self, repo):
        assert repo.buscar_por_id(9999) is None

    def test_buscar_por_token(self, repo, conn, paciente_id):
        o = Orcamento(id=None, paciente_id=paciente_id)
        criado = repo.criar(o)
        repo.atualizar_status(criado.id, 'enviado', token='meu-token-unico')

        encontrado = repo.buscar_por_token('meu-token-unico')
        assert encontrado is not None
        assert encontrado.status == 'enviado'
        assert encontrado.token_aprovacao == 'meu-token-unico'

    def test_buscar_por_token_inexistente(self, repo):
        assert repo.buscar_por_token('token-falso') is None

    def test_listar_todos_com_join(self, repo, conn, paciente_id):
        repo.criar(Orcamento(id=None, paciente_id=paciente_id, status='rascunho'))
        repo.criar(Orcamento(id=None, paciente_id=paciente_id, status='enviado'))

        lista = repo.listar_todos()
        assert len(lista) == 2
        assert all(o.paciente_nome == 'Ana Paula' for o in lista)

    def test_listar_por_paciente(self, repo, conn, paciente_id):
        outro_id = conn.execute(
            "INSERT INTO pacientes (nome) VALUES ('João')"
        ).lastrowid
        conn.commit()

        repo.criar(Orcamento(id=None, paciente_id=paciente_id))
        repo.criar(Orcamento(id=None, paciente_id=outro_id))

        lista = repo.listar_por_paciente(paciente_id)
        assert len(lista) == 1
        assert lista[0].paciente_id == paciente_id

    def test_atualizar_status(self, repo, conn, paciente_id):
        o = repo.criar(Orcamento(id=None, paciente_id=paciente_id))
        repo.atualizar_status(o.id, 'aprovado')

        encontrado = repo.buscar_por_id(o.id)
        assert encontrado.status == 'aprovado'

    def test_atualizar_status_com_token(self, repo, conn, paciente_id):
        o = repo.criar(Orcamento(id=None, paciente_id=paciente_id))
        repo.atualizar_status(o.id, 'enviado', token='abc-def')

        encontrado = repo.buscar_por_id(o.id)
        assert encontrado.status == 'enviado'
        assert encontrado.token_aprovacao == 'abc-def'

    def test_criar_e_buscar_itens(self, repo, conn, paciente_id, procedimento_com_preco_id):
        o = repo.criar(Orcamento(id=None, paciente_id=paciente_id))

        item = OrcamentoItem(
            id=None, orcamento_id=o.id,
            procedimento_id=procedimento_com_preco_id,
            quantidade=2, valor_unitario=100.0,
            desconto_item=0, desconto_tipo='percentual',
        )
        criado = repo.criar_item(item)
        assert criado.id is not None

        orcamento_com_itens = repo.buscar_por_id(o.id)
        assert len(orcamento_com_itens.itens) == 1
        assert orcamento_com_itens.itens[0].quantidade == 2
        assert orcamento_com_itens.itens[0].procedimento_nome == 'Extração'

    def test_deletar_item(self, repo, conn, paciente_id, procedimento_com_preco_id):
        o = repo.criar(Orcamento(id=None, paciente_id=paciente_id))
        item = repo.criar_item(OrcamentoItem(
            id=None, orcamento_id=o.id,
            procedimento_id=procedimento_com_preco_id,
            quantidade=1, valor_unitario=50.0,
        ))

        repo.deletar_item(item.id)
        orcamento_atualizado = repo.buscar_por_id(o.id)
        assert len(orcamento_atualizado.itens) == 0

    def test_deletar_itens_do_orcamento(self, repo, conn, paciente_id, procedimento_com_preco_id):
        o = repo.criar(Orcamento(id=None, paciente_id=paciente_id))
        for _ in range(3):
            repo.criar_item(OrcamentoItem(
                id=None, orcamento_id=o.id,
                procedimento_id=procedimento_com_preco_id,
                quantidade=1, valor_unitario=100.0,
            ))

        repo.deletar_itens(o.id)
        orcamento_atualizado = repo.buscar_por_id(o.id)
        assert len(orcamento_atualizado.itens) == 0

    def test_atualizar_orcamento(self, repo, conn, paciente_id):
        o = repo.criar(Orcamento(id=None, paciente_id=paciente_id))
        o.validade_dias = 60
        o.desconto_global = 15.0
        o.desconto_tipo = 'percentual'
        o.observacoes = 'Desconto especial'
        repo.atualizar(o)

        atualizado = repo.buscar_por_id(o.id)
        assert atualizado.validade_dias == 60
        assert atualizado.desconto_global == 15.0
        assert atualizado.observacoes == 'Desconto especial'

    def test_listar_todos_retorna_multiplos(self, repo, conn, paciente_id):
        o1 = repo.criar(Orcamento(id=None, paciente_id=paciente_id))
        o2 = repo.criar(Orcamento(id=None, paciente_id=paciente_id))

        lista = repo.listar_todos()
        ids = [o.id for o in lista]
        assert o1.id in ids
        assert o2.id in ids
        assert len(lista) == 2
