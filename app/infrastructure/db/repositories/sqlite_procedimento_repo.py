import sqlite3
from typing import Optional
from app.domain.entities.procedimento import Procedimento
from app.domain.repositories.procedimento_repo import ProcedimentoRepository
from app.domain.exceptions import DadosInvalidosError


def _row_to_entity(row: sqlite3.Row) -> Procedimento:
    return Procedimento(
        id=row['id'],
        nome=row['nome'],
        duracao_minutos=row['duracao_minutos'],
        cor_hex=row['cor_hex'],
        preco_base=row['preco_base'],
        ativo=bool(row['ativo']),
    )


class SqliteProcedimentoRepository(ProcedimentoRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def buscar_por_id(self, id: int) -> Optional[Procedimento]:
        row = self._conn.execute(
            'SELECT * FROM procedimentos WHERE id = ?', (id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def listar_ativos(self) -> list[Procedimento]:
        rows = self._conn.execute(
            'SELECT * FROM procedimentos WHERE ativo = 1 ORDER BY nome'
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def criar(self, procedimento: Procedimento) -> Procedimento:
        if procedimento.duracao_minutos < 5:
            raise DadosInvalidosError("Duração mínima é 5 minutos")
        cur = self._conn.execute(
            '''INSERT INTO procedimentos (nome, duracao_minutos, cor_hex, preco_base, ativo)
               VALUES (?, ?, ?, ?, 1)''',
            (
                procedimento.nome,
                procedimento.duracao_minutos,
                procedimento.cor_hex,
                procedimento.preco_base,
            ),
        )
        self._conn.commit()
        procedimento.id = cur.lastrowid
        return procedimento

    def atualizar(self, procedimento: Procedimento) -> Procedimento:
        if procedimento.duracao_minutos < 5:
            raise DadosInvalidosError("Duração mínima é 5 minutos")
        self._conn.execute(
            '''UPDATE procedimentos
               SET nome=?, duracao_minutos=?, cor_hex=?, preco_base=?, ativo=?
               WHERE id=?''',
            (
                procedimento.nome,
                procedimento.duracao_minutos,
                procedimento.cor_hex,
                procedimento.preco_base,
                int(procedimento.ativo),
                procedimento.id,
            ),
        )
        self._conn.commit()
        return procedimento

    def desativar(self, id: int) -> None:
        self._conn.execute(
            'UPDATE procedimentos SET ativo = 0 WHERE id = ?', (id,)
        )
        self._conn.commit()
