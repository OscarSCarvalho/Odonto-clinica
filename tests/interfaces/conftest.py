import os
import tempfile
import pytest
from run import create_app


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    application = create_app({'TESTING': True, 'DB_PATH': db_path})

    yield application

    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['perfil']  = 'admin'
        sess['nome']    = 'Admin Teste'
    return client


@pytest.fixture
def recepcao_client(client, app):
    with app.app_context():
        from app.infrastructure.db.connection import get_db
        from werkzeug.security import generate_password_hash
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES (?,?,?,?)",
            ('Recep', 'recep@test.com', generate_password_hash('123'), 'recepcao')
        )
        db.commit()
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['perfil']  = 'recepcao'
        sess['nome']    = 'Recepcionista'
    return client
