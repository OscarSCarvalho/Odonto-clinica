import sqlite3
from typing import Optional
from app.domain.entities.plano_recorrente import PlanoRecorrente
from app.domain.repositories.plano_recorrente_repo import PlanoRecorrenteRepository


def _row_to_entity(row: sqlite3.Row) -> PlanoRecorrente:
    p = PlanoRecorrente(
        id=row['id'],
        paciente_id=row['paciente_id'],
        profissional_id=row['profissional_id'],
        procedimento_id=row['procedimento_id'],
        intervalo_dias=row['intervalo_dias'],
        proxima_data=row['proxima_data'],
        horario_preferido=row['horario_preferido'],
        observacoes=row['observacoes'],
        ativo=bool(row['ativo']),
    )
    for campo in ('paciente_nome', 'paciente_telefone', 'profissional_nome', 'procedimento_nome'):
        if campo in row.keys():
            setattr(p, campo, row[campo])
    return p


_SELECT_COM_JOIN = '''
    SELECT
        pr.*,
        pac.nome     AS paciente_nome,
        pac.telefone AS paciente_telefone,
        prof.nome    AS profissional_nome,
        proc.nome    AS procedimento_nome
    FROM planos_recorrentes pr
    JOIN pacientes     pac  ON pac.id  = pr.paciente_id
    JOIN profissionais prof ON prof.id = pr.profissional_id
    JOIN procedimentos proc ON proc.id = pr.procedimento_id
'''


class SqlitePlanoRecorrenteRepository(PlanoRecorrenteRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def buscar_por_id(self, id: int) -> Optional[PlanoRecorrente]:
        row = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE pr.id = ?', (id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def listar_por_paciente(self, paciente_id: int) -> list[PlanoRecorrente]:
        rows = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE pr.paciente_id = ? ORDER BY pr.proxima_data',
            (paciente_id,),
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def listar_ativos(self) -> list[PlanoRecorrente]:
        rows = self._conn.execute(
            _SELECT_COM_JOIN + ' WHERE pr.ativo = 1 ORDER BY pr.proxima_data'
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def criar(self, plano: PlanoRecorrente) -> PlanoRecorrente:
        cur = self._conn.execute(
            '''INSERT INTO planos_recorrentes
               (paciente_id, profissional_id, procedimento_id, intervalo_dias,
                proxima_data, horario_preferido, observacoes, ativo)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)''',
            (
                plano.paciente_id,
                plano.profissional_id,
                plano.procedimento_id,
                plano.intervalo_dias,
                plano.proxima_data,
                plano.horario_preferido,
                plano.observacoes,
            ),
        )
        self._conn.commit()
        plano.id = cur.lastrowid
        return plano

    def atualizar(self, plano: PlanoRecorrente) -> PlanoRecorrente:
        self._conn.execute(
            '''UPDATE planos_recorrentes
               SET profissional_id=?, procedimento_id=?, intervalo_dias=?,
                   proxima_data=?, horario_preferido=?, observacoes=?, ativo=?
               WHERE id=?''',
            (
                plano.profissional_id,
                plano.procedimento_id,
                plano.intervalo_dias,
                plano.proxima_data,
                plano.horario_preferido,
                plano.observacoes,
                int(plano.ativo),
                plano.id,
            ),
        )
        self._conn.commit()
        return plano

    def desativar(self, id: int) -> None:
        self._conn.execute('UPDATE planos_recorrentes SET ativo = 0 WHERE id = ?', (id,))
        self._conn.commit()

    def reativar(self, id: int) -> None:
        self._conn.execute('UPDATE planos_recorrentes SET ativo = 1 WHERE id = ?', (id,))
        self._conn.commit()
