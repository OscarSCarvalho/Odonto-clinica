import sqlite3
from typing import Optional
from app.domain.entities.paciente import Paciente
from app.domain.repositories.paciente_repo import PacienteRepository
from app.domain.exceptions import PacienteDuplicadoError


def _row_to_entity(row: sqlite3.Row) -> Paciente:
    return Paciente(
        id=row['id'],
        nome=row['nome'],
        telefone=row['telefone'],
        email=row['email'],
        cpf=row['cpf'],
        data_nascimento=row['data_nascimento'],
        observacoes=row['observacoes'],
        ativo=bool(row['ativo']),
    )


class SqlitePacienteRepository(PacienteRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def buscar_por_id(self, id: int) -> Optional[Paciente]:
        row = self._conn.execute(
            'SELECT * FROM pacientes WHERE id = ?', (id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def buscar_por_cpf(self, cpf: str) -> Optional[Paciente]:
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        row = self._conn.execute(
            'SELECT * FROM pacientes WHERE REPLACE(REPLACE(cpf,".",""),"-","") = ?',
            (cpf_limpo,),
        ).fetchone()
        return _row_to_entity(row) if row else None

    def buscar_por_telefone(self, telefone: str) -> Optional[Paciente]:
        tel_limpo = ''.join(filter(str.isdigit, telefone))
        row = self._conn.execute(
            "SELECT * FROM pacientes WHERE REPLACE(REPLACE(REPLACE(telefone,'(',''),')',''),' ','') LIKE ?",
            (f'%{tel_limpo}%',),
        ).fetchone()
        return _row_to_entity(row) if row else None

    def buscar_por_nome(self, termo: str, limite: int = 10) -> list[Paciente]:
        if len(termo.strip()) < 3:
            return []
        rows = self._conn.execute(
            'SELECT * FROM pacientes WHERE nome LIKE ? AND ativo = 1 ORDER BY nome LIMIT ?',
            (f'%{termo}%', limite),
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def criar(self, paciente: Paciente) -> Paciente:
        if paciente.cpf:
            existente = self.buscar_por_cpf(paciente.cpf)
            if existente:
                raise PacienteDuplicadoError(paciente.cpf, existente.nome, existente.id)

        cur = self._conn.execute(
            '''INSERT INTO pacientes (nome, telefone, email, cpf, data_nascimento, observacoes, ativo)
               VALUES (?, ?, ?, ?, ?, ?, 1)''',
            (
                paciente.nome,
                paciente.telefone,
                paciente.email,
                paciente.cpf,
                paciente.data_nascimento,
                paciente.observacoes,
            ),
        )
        self._conn.commit()
        paciente.id = cur.lastrowid
        return paciente

    def atualizar(self, paciente: Paciente) -> Paciente:
        self._conn.execute(
            '''UPDATE pacientes
               SET nome=?, telefone=?, email=?, cpf=?, data_nascimento=?, observacoes=?, ativo=?
               WHERE id=?''',
            (
                paciente.nome,
                paciente.telefone,
                paciente.email,
                paciente.cpf,
                paciente.data_nascimento,
                paciente.observacoes,
                int(paciente.ativo),
                paciente.id,
            ),
        )
        self._conn.commit()
        return paciente

    def desativar(self, id: int) -> None:
        self._conn.execute(
            'UPDATE pacientes SET ativo = 0 WHERE id = ?', (id,)
        )
        self._conn.commit()

    def listar_aniversariantes_do_dia(self, mes: int, dia: int) -> list[Paciente]:
        rows = self._conn.execute(
            '''SELECT * FROM pacientes
               WHERE ativo = 1
                 AND data_nascimento IS NOT NULL
                 AND CAST(strftime('%m', data_nascimento) AS INTEGER) = ?
                 AND CAST(strftime('%d', data_nascimento) AS INTEGER) = ?
               ORDER BY nome''',
            (mes, dia),
        ).fetchall()
        return [_row_to_entity(r) for r in rows]
