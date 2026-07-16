import sqlite3
from typing import Optional
from app.domain.entities.lembrete import ConfigLembrete, LembreteEnviado
from app.domain.repositories.lembrete_repo import LembreteRepository


class SqliteLembreteRepository(LembreteRepository):

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # ── config_lembretes ──────────────────────────────────────────────────────

    def listar_configs(self) -> list[ConfigLembrete]:
        rows = self._conn.execute(
            'SELECT id, antecedencia_h, tipo, ativo FROM config_lembretes ORDER BY antecedencia_h'
        ).fetchall()
        return [self._row_to_config(r) for r in rows]

    def listar_configs_ativas(self) -> list[ConfigLembrete]:
        rows = self._conn.execute(
            'SELECT id, antecedencia_h, tipo, ativo FROM config_lembretes WHERE ativo=1 ORDER BY antecedencia_h'
        ).fetchall()
        return [self._row_to_config(r) for r in rows]

    def criar_config(self, config: ConfigLembrete) -> ConfigLembrete:
        cur = self._conn.execute(
            'INSERT INTO config_lembretes (antecedencia_h, tipo, ativo) VALUES (?, ?, ?)',
            (config.antecedencia_h, config.tipo, 1 if config.ativo else 0),
        )
        self._conn.commit()
        config.id = cur.lastrowid
        return config

    def remover_config(self, id: int) -> None:
        self._conn.execute('DELETE FROM config_lembretes WHERE id=?', (id,))
        self._conn.commit()

    def toggle_config(self, id: int) -> None:
        self._conn.execute(
            'UPDATE config_lembretes SET ativo = CASE WHEN ativo=1 THEN 0 ELSE 1 END WHERE id=?',
            (id,),
        )
        self._conn.commit()

    # ── lembretes_enviados ────────────────────────────────────────────────────

    def ja_foi_enviado(self, agendamento_id: int, antecedencia_h: int, tipo: str) -> bool:
        row = self._conn.execute(
            "SELECT id FROM lembretes_enviados "
            "WHERE agendamento_id=? AND antecedencia_h=? AND tipo=? AND status='enviado'",
            (agendamento_id, antecedencia_h, tipo),
        ).fetchone()
        return row is not None

    def buscar_para_retry(
        self, agendamento_id: int, antecedencia_h: int, tipo: str
    ) -> Optional[LembreteEnviado]:
        row = self._conn.execute(
            "SELECT id, agendamento_id, tipo, antecedencia_h, tentativas, enviado_em, status, erro_msg "
            "FROM lembretes_enviados "
            "WHERE agendamento_id=? AND antecedencia_h=? AND tipo=? AND status='erro'",
            (agendamento_id, antecedencia_h, tipo),
        ).fetchone()
        return self._row_to_lembrete(row) if row else None

    def criar_lembrete(
        self, agendamento_id: int, tipo: str, antecedencia_h: int,
        status: str, tentativas: int, erro_msg: Optional[str] = None
    ) -> None:
        if status == 'enviado':
            self._conn.execute(
                "INSERT INTO lembretes_enviados "
                "(agendamento_id, tipo, antecedencia_h, status, tentativas, enviado_em, erro_msg) "
                "VALUES (?, ?, ?, ?, ?, datetime('now'), ?)",
                (agendamento_id, tipo, antecedencia_h, status, tentativas, erro_msg),
            )
        else:
            self._conn.execute(
                "INSERT INTO lembretes_enviados "
                "(agendamento_id, tipo, antecedencia_h, status, tentativas, erro_msg) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (agendamento_id, tipo, antecedencia_h, status, tentativas, erro_msg),
            )
        self._conn.commit()

    def atualizar_lembrete(
        self, id: int, status: str, tentativas: int, erro_msg: Optional[str] = None
    ) -> None:
        if status == 'enviado':
            self._conn.execute(
                "UPDATE lembretes_enviados "
                "SET status=?, tentativas=?, erro_msg=?, enviado_em=datetime('now') WHERE id=?",
                (status, tentativas, erro_msg, id),
            )
        else:
            self._conn.execute(
                "UPDATE lembretes_enviados SET status=?, tentativas=?, erro_msg=? WHERE id=?",
                (status, tentativas, erro_msg, id),
            )
        self._conn.commit()

    @staticmethod
    def _row_to_config(row: sqlite3.Row) -> ConfigLembrete:
        return ConfigLembrete(
            id=row['id'],
            antecedencia_h=row['antecedencia_h'],
            tipo=row['tipo'],
            ativo=bool(row['ativo']),
        )

    @staticmethod
    def _row_to_lembrete(row: sqlite3.Row) -> LembreteEnviado:
        return LembreteEnviado(
            id=row['id'],
            agendamento_id=row['agendamento_id'],
            tipo=row['tipo'],
            antecedencia_h=row['antecedencia_h'],
            tentativas=row['tentativas'],
            enviado_em=row['enviado_em'],
            status=row['status'],
            erro_msg=row['erro_msg'],
        )
