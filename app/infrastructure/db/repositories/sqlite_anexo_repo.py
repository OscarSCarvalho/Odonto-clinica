import sqlite3
from typing import Optional
from app.domain.entities.anexo import Anexo
from app.domain.repositories.anexo_repo import AnexoRepository


def _row_to_entity(row: sqlite3.Row) -> Anexo:
    return Anexo(
        id=row['id'],
        paciente_id=row['paciente_id'],
        nome_original=row['nome_original'],
        caminho_arquivo=row['caminho_arquivo'],
        criado_em=row['criado_em'],
    )


class SqliteAnexoRepository(AnexoRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def listar_por_paciente(self, paciente_id: int) -> list[Anexo]:
        rows = self._conn.execute(
            'SELECT * FROM paciente_anexos WHERE paciente_id = ? ORDER BY criado_em DESC',
            (paciente_id,),
        ).fetchall()
        return [_row_to_entity(r) for r in rows]

    def buscar_por_id(self, id: int) -> Optional[Anexo]:
        row = self._conn.execute(
            'SELECT * FROM paciente_anexos WHERE id = ?', (id,)
        ).fetchone()
        return _row_to_entity(row) if row else None

    def criar(self, anexo: Anexo) -> Anexo:
        cur = self._conn.execute(
            '''INSERT INTO paciente_anexos (paciente_id, nome_original, caminho_arquivo)
               VALUES (?, ?, ?)''',
            (anexo.paciente_id, anexo.nome_original, anexo.caminho_arquivo),
        )
        self._conn.commit()
        anexo.id = cur.lastrowid
        return anexo

    def excluir(self, id: int) -> None:
        self._conn.execute('DELETE FROM paciente_anexos WHERE id = ?', (id,))
        self._conn.commit()
