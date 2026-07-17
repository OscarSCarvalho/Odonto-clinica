import sqlite3
from typing import Optional
from app.domain.entities.pagamento import Pagamento
from app.domain.repositories.pagamento_repo import PagamentoRepository


def _row_to_entity(row: sqlite3.Row) -> Pagamento:
    p = Pagamento(
        id=row['id'],
        paciente_id=row['paciente_id'],
        agendamento_id=row['agendamento_id'],
        mensalidade_id=row['mensalidade_id'],
        valor=row['valor'],
        data_vencimento=row['data_vencimento'],
        forma_pagamento=row['forma_pagamento'],
        status=row['status'],
        data_pagamento=row['data_pagamento'],
        observacoes=row['observacoes'],
        criado_em=row['criado_em'],
    )
    for campo in ('paciente_nome', 'paciente_telefone', 'procedimento_nome'):
        if campo in row.keys():
            setattr(p, campo, row[campo])
    return p


_SELECT_COM_JOIN = '''
    SELECT
        pg.*,
        pac.nome     AS paciente_nome,
        pac.telefone AS paciente_telefone,
        proc.nome    AS procedimento_nome
    FROM pagamentos pg
    JOIN pacientes pac       ON pac.id = pg.paciente_id
    LEFT JOIN agendamentos a ON a.id    = pg.agendamento_id
    LEFT JOIN procedimentos proc ON proc.id = a.procedimento_id
'''


class SqlitePagamentoRepository(PagamentoRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def buscar_por_id(self, id: int) -> Optional[Pagamento]:
        row = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE pg.id = ?', (id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def buscar_por_agendamento(self, agendamento_id: int) -> Optional[Pagamento]:
        row = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE pg.agendamento_id = ?', (agendamento_id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def buscar_por_mensalidade_e_competencia(self, mensalidade_id: int, competencia: str) -> Optional[Pagamento]:
        row = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE pg.mensalidade_id = ? AND pg.data_vencimento LIKE ?',
            (mensalidade_id, f'{competencia}%'),
        ).fetchone()
        return _row_to_entity(row) if row else None

    def listar_pendentes(self) -> list[Pagamento]:
        rows = self._conn.execute(
            _SELECT_COM_JOIN + " WHERE pg.status = 'pendente' ORDER BY pg.data_vencimento"
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def listar_por_paciente(self, paciente_id: int) -> list[Pagamento]:
        rows = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE pg.paciente_id = ? ORDER BY pg.data_vencimento DESC',
            (paciente_id,),
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def criar(self, pagamento: Pagamento) -> Pagamento:
        cur = self._conn.execute(
            '''INSERT INTO pagamentos
               (paciente_id, agendamento_id, mensalidade_id, valor, data_vencimento, observacoes)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                pagamento.paciente_id,
                pagamento.agendamento_id,
                pagamento.mensalidade_id,
                pagamento.valor,
                pagamento.data_vencimento,
                pagamento.observacoes,
            ),
        )
        self._conn.commit()
        pagamento.id = cur.lastrowid
        return pagamento

    def marcar_pago(
        self, id: int, forma_pagamento: str, data_pagamento: str, observacoes: Optional[str]
    ) -> None:
        self._conn.execute(
            '''UPDATE pagamentos
               SET status = 'pago', forma_pagamento = ?, data_pagamento = ?, observacoes = ?
               WHERE id = ?''',
            (forma_pagamento, data_pagamento, observacoes, id),
        )
        self._conn.commit()
