import sqlite3
import os
import pytest


@pytest.fixture
def conn():
    """Banco sqlite3 em memória com schema completo."""
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')

    schema_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'app', 'infrastructure', 'db', 'schema.sql'
    )
    with open(schema_path, encoding='utf-8') as f:
        c.executescript(f.read())

    yield c
    c.close()


@pytest.fixture
def profissional_id(conn):
    cur = conn.execute(
        "INSERT INTO profissionais (nome, cor_hex, horario_inicio, horario_fim, dias_semana) "
        "VALUES ('Dr. Carlos', '#3498db', '08:00', '18:00', '1,2,3,4,5')"
    )
    conn.commit()
    return cur.lastrowid


@pytest.fixture
def procedimento_id(conn):
    cur = conn.execute(
        "INSERT INTO procedimentos (nome, duracao_minutos, cor_hex) VALUES ('Limpeza', 30, '#e74c3c')"
    )
    conn.commit()
    return cur.lastrowid


@pytest.fixture
def paciente_id(conn):
    cur = conn.execute(
        "INSERT INTO pacientes (nome, telefone) VALUES ('Ana Paula', '11999990000')"
    )
    conn.commit()
    return cur.lastrowid
