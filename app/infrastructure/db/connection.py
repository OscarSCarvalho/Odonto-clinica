import sqlite3
import os
from flask import g, current_app


def get_db():
    if 'db' not in g:
        db_path = current_app.config['DB_PATH']
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        g.db = sqlite3.connect(db_path, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
        g.db.execute('PRAGMA journal_mode = WAL')
    return g.db


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    from flask import current_app
    db_path = current_app.config['DB_PATH']
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')

    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())

    _seed(conn)
    conn.close()


def _seed(conn):
    from werkzeug.security import generate_password_hash

    admin_exists = conn.execute(
        "SELECT id FROM usuarios WHERE email = 'admin@clinica.com'"
    ).fetchone()

    if admin_exists:
        return

    conn.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES (?, ?, ?, ?)",
        ('Administrador', 'admin@clinica.com',
         generate_password_hash('admin123'), 'admin')
    )

    conn.execute(
        "INSERT INTO profissionais (nome, especialidade, cor_hex, horario_inicio, horario_fim, dias_semana) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ('Dr. Carlos Silva', 'Ortodontia', '#3498db', '08:00', '18:00', '1,2,3,4,5')
    )

    conn.execute(
        "INSERT INTO procedimentos (nome, duracao_minutos, cor_hex, preco_base) VALUES (?, ?, ?, ?)",
        ('Consulta', 30, '#2ecc71', 150.00)
    )
    conn.execute(
        "INSERT INTO procedimentos (nome, duracao_minutos, cor_hex, preco_base) VALUES (?, ?, ?, ?)",
        ('Limpeza', 60, '#e67e22', 200.00)
    )

    conn.commit()
