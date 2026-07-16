import sqlite3
from typing import Optional
from app.domain.entities.tarefa_retorno import TarefaRetorno
from app.domain.repositories.tarefa_retorno_repo import TarefaRetornoRepository


def _row_to_entity(row: sqlite3.Row) -> TarefaRetorno:
    t = TarefaRetorno(
        id=row['id'],
        agendamento_id=row['agendamento_id'],
        paciente_id=row['paciente_id'],
        data_sugerida=row['data_sugerida'],
        observacoes=row['observacoes'],
        status=row['status'],
        contato_em=row['contato_em'],
        criado_em=row['criado_em'],
    )
    for campo in ('paciente_nome', 'paciente_telefone', 'profissional_id',
                  'profissional_nome', 'procedimento_id', 'procedimento_nome'):
        if campo in row.keys():
            setattr(t, campo, row[campo])
    return t


_SELECT_COM_JOIN = '''
    SELECT
        t.*,
        pac.nome     AS paciente_nome,
        pac.telefone AS paciente_telefone,
        a.profissional_id AS profissional_id,
        a.procedimento_id AS procedimento_id,
        prof.nome AS profissional_nome,
        proc.nome AS procedimento_nome
    FROM tarefas_retorno t
    JOIN pacientes     pac  ON pac.id  = t.paciente_id
    JOIN agendamentos  a    ON a.id    = t.agendamento_id
    JOIN profissionais prof ON prof.id = a.profissional_id
    JOIN procedimentos proc ON proc.id = a.procedimento_id
'''


class SqliteTarefaRetornoRepository(TarefaRetornoRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def buscar_por_id(self, id: int) -> Optional[TarefaRetorno]:
        row = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE t.id = ?', (id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def buscar_por_agendamento(self, agendamento_id: int) -> Optional[TarefaRetorno]:
        row = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE t.agendamento_id = ?', (agendamento_id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def listar_pendentes(self) -> list[TarefaRetorno]:
        rows = self._conn.execute(
            _SELECT_COM_JOIN + " WHERE t.status = 'pendente' ORDER BY t.data_sugerida"
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def criar(self, tarefa: TarefaRetorno) -> TarefaRetorno:
        cur = self._conn.execute(
            '''INSERT INTO tarefas_retorno (agendamento_id, paciente_id, data_sugerida, observacoes)
               VALUES (?, ?, ?, ?)''',
            (tarefa.agendamento_id, tarefa.paciente_id, tarefa.data_sugerida, tarefa.observacoes),
        )
        self._conn.commit()
        tarefa.id = cur.lastrowid
        return tarefa

    def marcar_contatado(self, id: int, observacoes: Optional[str]) -> None:
        self._conn.execute(
            '''UPDATE tarefas_retorno
               SET status = 'contatado', contato_em = datetime('now'), observacoes = ?
               WHERE id = ?''',
            (observacoes, id),
        )
        self._conn.commit()
