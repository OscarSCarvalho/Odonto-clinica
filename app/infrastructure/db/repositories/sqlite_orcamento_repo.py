import sqlite3
from typing import Optional
from app.domain.entities.orcamento import Orcamento, OrcamentoItem
from app.domain.repositories.orcamento_repo import OrcamentoRepository


def _row_to_entity(row: sqlite3.Row) -> Orcamento:
    o = Orcamento(
        id=row['id'],
        paciente_id=row['paciente_id'],
        profissional_id=row['profissional_id'],
        status=row['status'],
        validade_dias=row['validade_dias'],
        desconto_global=row['desconto_global'],
        desconto_tipo=row['desconto_tipo'],
        observacoes=row['observacoes'],
        token_aprovacao=row['token_aprovacao'],
        criado_em=row['criado_em'],
    )
    keys = row.keys()
    if 'paciente_nome' in keys:
        o.paciente_nome = row['paciente_nome']
    if 'profissional_nome' in keys:
        o.profissional_nome = row['profissional_nome']
    return o


def _row_to_item(row: sqlite3.Row) -> OrcamentoItem:
    item = OrcamentoItem(
        id=row['id'],
        orcamento_id=row['orcamento_id'],
        procedimento_id=row['procedimento_id'],
        quantidade=row['quantidade'],
        valor_unitario=row['valor_unitario'],
        desconto_item=row['desconto_item'],
        desconto_tipo=row['desconto_tipo'],
    )
    keys = row.keys()
    if 'procedimento_nome' in keys:
        item.procedimento_nome = row['procedimento_nome']
    return item


class SqliteOrcamentoRepository(OrcamentoRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def _carregar_itens(self, orcamento_id: int) -> list:
        rows = self._conn.execute(
            '''SELECT oi.*, p.nome AS procedimento_nome
               FROM orcamento_itens oi
               JOIN procedimentos p ON p.id = oi.procedimento_id
               WHERE oi.orcamento_id = ?
               ORDER BY oi.id''',
            (orcamento_id,),
        ).fetchall()
        return [_row_to_item(r) for r in rows]

    def buscar_por_id(self, id: int) -> Optional[Orcamento]:
        row = self._conn.execute(
            '''SELECT o.*,
                      pac.nome AS paciente_nome,
                      prof.nome AS profissional_nome
               FROM orcamentos o
               JOIN pacientes pac ON pac.id = o.paciente_id
               LEFT JOIN profissionais prof ON prof.id = o.profissional_id
               WHERE o.id = ?''',
            (id,),
        ).fetchone()
        if not row:
            return None
        o = _row_to_entity(row)
        o.itens = self._carregar_itens(id)
        return o

    def buscar_por_token(self, token: str) -> Optional[Orcamento]:
        row = self._conn.execute(
            '''SELECT o.*,
                      pac.nome AS paciente_nome,
                      prof.nome AS profissional_nome
               FROM orcamentos o
               JOIN pacientes pac ON pac.id = o.paciente_id
               LEFT JOIN profissionais prof ON prof.id = o.profissional_id
               WHERE o.token_aprovacao = ?''',
            (token,),
        ).fetchone()
        if not row:
            return None
        o = _row_to_entity(row)
        o.itens = self._carregar_itens(o.id)
        return o

    def listar_todos(self) -> list:
        rows = self._conn.execute(
            '''SELECT o.*,
                      pac.nome AS paciente_nome,
                      prof.nome AS profissional_nome
               FROM orcamentos o
               JOIN pacientes pac ON pac.id = o.paciente_id
               LEFT JOIN profissionais prof ON prof.id = o.profissional_id
               ORDER BY o.criado_em DESC'''
        ).fetchall()
        result = []
        for row in rows:
            o = _row_to_entity(row)
            o.itens = self._carregar_itens(o.id)
            result.append(o)
        return result

    def listar_por_paciente(self, paciente_id: int) -> list:
        rows = self._conn.execute(
            '''SELECT o.*,
                      pac.nome AS paciente_nome,
                      prof.nome AS profissional_nome
               FROM orcamentos o
               JOIN pacientes pac ON pac.id = o.paciente_id
               LEFT JOIN profissionais prof ON prof.id = o.profissional_id
               WHERE o.paciente_id = ?
               ORDER BY o.criado_em DESC''',
            (paciente_id,),
        ).fetchall()
        result = []
        for row in rows:
            o = _row_to_entity(row)
            o.itens = self._carregar_itens(o.id)
            result.append(o)
        return result

    def criar(self, orcamento: Orcamento) -> Orcamento:
        cur = self._conn.execute(
            '''INSERT INTO orcamentos
               (paciente_id, profissional_id, status, validade_dias,
                desconto_global, desconto_tipo, observacoes, token_aprovacao)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                orcamento.paciente_id,
                orcamento.profissional_id,
                orcamento.status,
                orcamento.validade_dias,
                orcamento.desconto_global,
                orcamento.desconto_tipo,
                orcamento.observacoes,
                orcamento.token_aprovacao,
            ),
        )
        self._conn.commit()
        orcamento.id = cur.lastrowid
        return orcamento

    def atualizar_status(self, id: int, status: str, token: Optional[str] = None) -> None:
        if token is not None:
            self._conn.execute(
                "UPDATE orcamentos SET status=?, token_aprovacao=?, atualizado_em=datetime('now') WHERE id=?",
                (status, token, id),
            )
        else:
            self._conn.execute(
                "UPDATE orcamentos SET status=?, atualizado_em=datetime('now') WHERE id=?",
                (status, id),
            )
        self._conn.commit()

    def atualizar(self, orcamento: Orcamento) -> Orcamento:
        self._conn.execute(
            '''UPDATE orcamentos
               SET profissional_id=?, validade_dias=?, desconto_global=?,
                   desconto_tipo=?, observacoes=?, atualizado_em=datetime('now')
               WHERE id=?''',
            (
                orcamento.profissional_id,
                orcamento.validade_dias,
                orcamento.desconto_global,
                orcamento.desconto_tipo,
                orcamento.observacoes,
                orcamento.id,
            ),
        )
        self._conn.commit()
        return orcamento

    def deletar_itens(self, orcamento_id: int) -> None:
        self._conn.execute('DELETE FROM orcamento_itens WHERE orcamento_id=?', (orcamento_id,))
        self._conn.commit()

    def criar_item(self, item: OrcamentoItem) -> OrcamentoItem:
        cur = self._conn.execute(
            '''INSERT INTO orcamento_itens
               (orcamento_id, procedimento_id, quantidade, valor_unitario, desconto_item, desconto_tipo)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                item.orcamento_id,
                item.procedimento_id,
                item.quantidade,
                item.valor_unitario,
                item.desconto_item,
                item.desconto_tipo,
            ),
        )
        self._conn.commit()
        item.id = cur.lastrowid
        return item

    def deletar_item(self, item_id: int) -> None:
        self._conn.execute('DELETE FROM orcamento_itens WHERE id=?', (item_id,))
        self._conn.commit()
