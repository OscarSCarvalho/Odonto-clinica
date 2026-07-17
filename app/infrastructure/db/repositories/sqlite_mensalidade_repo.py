import sqlite3
from typing import Optional
from app.domain.entities.mensalidade import Mensalidade
from app.domain.repositories.mensalidade_repo import MensalidadeRepository


def _row_to_entity(row: sqlite3.Row) -> Mensalidade:
    m = Mensalidade(
        id=row['id'],
        paciente_id=row['paciente_id'],
        valor=row['valor'],
        dia_vencimento=row['dia_vencimento'],
        observacoes=row['observacoes'],
        ativo=bool(row['ativo']),
    )
    if 'paciente_nome' in row.keys():
        m.paciente_nome = row['paciente_nome']
    return m


_SELECT_COM_JOIN = '''
    SELECT m.*, pac.nome AS paciente_nome
    FROM mensalidades m
    JOIN pacientes pac ON pac.id = m.paciente_id
'''


class SqliteMensalidadeRepository(MensalidadeRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def buscar_por_id(self, id: int) -> Optional[Mensalidade]:
        row = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE m.id = ?', (id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def listar_por_paciente(self, paciente_id: int) -> list[Mensalidade]:
        rows = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE m.paciente_id = ? ORDER BY m.criado_em', (paciente_id,)
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def listar_ativas(self) -> list[Mensalidade]:
        rows = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE m.ativo = 1 ORDER BY m.dia_vencimento'
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def criar(self, mensalidade: Mensalidade) -> Mensalidade:
        cur = self._conn.execute(
            '''INSERT INTO mensalidades (paciente_id, valor, dia_vencimento, observacoes, ativo)
               VALUES (?, ?, ?, ?, 1)''',
            (mensalidade.paciente_id, mensalidade.valor, mensalidade.dia_vencimento, mensalidade.observacoes),
        )
        self._conn.commit()
        mensalidade.id = cur.lastrowid
        return mensalidade

    def desativar(self, id: int) -> None:
        self._conn.execute('UPDATE mensalidades SET ativo = 0 WHERE id = ?', (id,))
        self._conn.commit()

    def reativar(self, id: int) -> None:
        self._conn.execute('UPDATE mensalidades SET ativo = 1 WHERE id = ?', (id,))
        self._conn.commit()
