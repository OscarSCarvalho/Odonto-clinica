import sqlite3
from typing import Optional
from datetime import datetime
from app.domain.entities.profissional import Profissional
from app.domain.repositories.profissional_repo import ProfissionalRepository


def _row_to_entity(row: sqlite3.Row) -> Profissional:
    return Profissional(
        id=row['id'],
        nome=row['nome'],
        especialidade=row['especialidade'],
        cor_hex=row['cor_hex'],
        horario_inicio=row['horario_inicio'],
        horario_fim=row['horario_fim'],
        dias_semana=row['dias_semana'],
        usuario_id=row['usuario_id'],
        ativo=bool(row['ativo']),
    )


class SqliteProfissionalRepository(ProfissionalRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def buscar_por_id(self, id: int) -> Optional[Profissional]:
        row = self._conn.execute(
            'SELECT * FROM profissionais WHERE id = ?', (id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def listar_ativos(self) -> list[Profissional]:
        rows = self._conn.execute(
            'SELECT * FROM profissionais WHERE ativo = 1 ORDER BY nome'
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def criar(self, profissional: Profissional) -> Profissional:
        cur = self._conn.execute(
            '''INSERT INTO profissionais
               (nome, especialidade, cor_hex, horario_inicio, horario_fim, dias_semana, usuario_id, ativo)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)''',
            (
                profissional.nome,
                profissional.especialidade,
                profissional.cor_hex,
                profissional.horario_inicio,
                profissional.horario_fim,
                profissional.dias_semana,
                profissional.usuario_id,
            ),
        )
        self._conn.commit()
        profissional.id = cur.lastrowid
        return profissional

    def atualizar(self, profissional: Profissional) -> Profissional:
        self._conn.execute(
            '''UPDATE profissionais
               SET nome=?, especialidade=?, cor_hex=?, horario_inicio=?,
                   horario_fim=?, dias_semana=?, usuario_id=?, ativo=?
               WHERE id=?''',
            (
                profissional.nome,
                profissional.especialidade,
                profissional.cor_hex,
                profissional.horario_inicio,
                profissional.horario_fim,
                profissional.dias_semana,
                profissional.usuario_id,
                int(profissional.ativo),
                profissional.id,
            ),
        )
        self._conn.commit()
        return profissional

    def desativar(self, id: int) -> int:
        agora = datetime.now().strftime('%Y-%m-%d %H:%M')
        futuros = self._conn.execute(
            '''SELECT COUNT(*) FROM agendamentos
               WHERE profissional_id = ? AND data_hora_inicio > ?
               AND status NOT IN ('cancelado', 'falta')''',
            (id, agora),
        ).fetchone()[0]

        self._conn.execute(
            'UPDATE profissionais SET ativo = 0 WHERE id = ?', (id,)
        )
        self._conn.commit()
        return futuros
