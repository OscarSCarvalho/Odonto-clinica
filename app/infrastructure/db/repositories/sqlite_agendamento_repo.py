import sqlite3
from typing import Optional
from app.domain.entities.agendamento import Agendamento
from app.domain.repositories.agendamento_repo import AgendamentoRepository


def _row_to_entity(row: sqlite3.Row) -> Agendamento:
    ag = Agendamento(
        id=row['id'],
        profissional_id=row['profissional_id'],
        paciente_id=row['paciente_id'],
        procedimento_id=row['procedimento_id'],
        data_hora_inicio=row['data_hora_inicio'],
        data_hora_fim=row['data_hora_fim'],
        status=row['status'],
        observacoes=row['observacoes'],
        origem=row['origem'],
        plano_recorrente_id=row['plano_recorrente_id'],
    )
    # Campos extras presentes nos JOINs (opcionais)
    for campo in ('profissional_nome', 'profissional_cor', 'paciente_nome',
                  'paciente_telefone', 'paciente_email',
                  'procedimento_nome', 'procedimento_cor', 'procedimento_duracao',
                  'procedimento_preco'):
        if campo in row.keys():
            setattr(ag, campo, row[campo])
    return ag


_SELECT_COM_JOIN = '''
    SELECT
        a.*,
        p.nome    AS profissional_nome,
        p.cor_hex AS profissional_cor,
        pac.nome  AS paciente_nome,
        pac.telefone AS paciente_telefone,
        pac.email    AS paciente_email,
        pr.nome AS procedimento_nome,
        pr.cor_hex AS procedimento_cor,
        pr.duracao_minutos AS procedimento_duracao,
        pr.preco_base AS procedimento_preco
    FROM agendamentos a
    JOIN profissionais p   ON p.id  = a.profissional_id
    JOIN pacientes    pac  ON pac.id = a.paciente_id
    JOIN procedimentos pr  ON pr.id  = a.procedimento_id
'''


class SqliteAgendamentoRepository(AgendamentoRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def buscar_por_id(self, id: int) -> Optional[Agendamento]:
        row = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE a.id = ?', (id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def listar_por_periodo(
        self,
        inicio: str,
        fim: str,
        profissional_id: Optional[int] = None,
    ) -> list[Agendamento]:
        sql = _SELECT_COM_JOIN + '''
            WHERE a.data_hora_inicio < ?
              AND a.data_hora_fim    > ?
        '''
        params: list = [fim, inicio]

        if profissional_id:
            sql += ' AND a.profissional_id = ?'
            params.append(profissional_id)

        sql += ' ORDER BY a.data_hora_inicio'
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_to_entity(r) for r in rows]

    def buscar_conflitos(
        self,
        profissional_id: int,
        inicio: str,
        fim: str,
        excluir_id: Optional[int] = None,
    ) -> list[Agendamento]:
        # Detecta sobreposição: A.inicio < B.fim AND A.fim > B.inicio
        sql = _SELECT_COM_JOIN + '''
            WHERE a.profissional_id = ?
              AND a.status NOT IN ('cancelado', 'falta')
              AND a.data_hora_inicio < ?
              AND a.data_hora_fim    > ?
        '''
        params: list = [profissional_id, fim, inicio]

        if excluir_id:
            sql += ' AND a.id != ?'
            params.append(excluir_id)

        rows = self._conn.execute(sql, params).fetchall()
        return [_row_to_entity(r) for r in rows]

    def criar(self, agendamento: Agendamento) -> Agendamento:
        cur = self._conn.execute(
            '''INSERT INTO agendamentos
               (profissional_id, paciente_id, procedimento_id,
                data_hora_inicio, data_hora_fim, status, observacoes, origem,
                plano_recorrente_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                agendamento.profissional_id,
                agendamento.paciente_id,
                agendamento.procedimento_id,
                agendamento.data_hora_inicio,
                agendamento.data_hora_fim,
                agendamento.status,
                agendamento.observacoes,
                agendamento.origem,
                agendamento.plano_recorrente_id,
            ),
        )
        self._conn.commit()
        agendamento.id = cur.lastrowid
        return agendamento

    def atualizar(self, agendamento: Agendamento) -> Agendamento:
        self._conn.execute(
            '''UPDATE agendamentos
               SET profissional_id=?, paciente_id=?, procedimento_id=?,
                   data_hora_inicio=?, data_hora_fim=?, status=?,
                   observacoes=?, origem=?,
                   atualizado_em=datetime('now')
               WHERE id=?''',
            (
                agendamento.profissional_id,
                agendamento.paciente_id,
                agendamento.procedimento_id,
                agendamento.data_hora_inicio,
                agendamento.data_hora_fim,
                agendamento.status,
                agendamento.observacoes,
                agendamento.origem,
                agendamento.id,
            ),
        )
        self._conn.commit()
        return agendamento
