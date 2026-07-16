import json
import pytest


class TestAuth:
    def test_login_get(self, client):
        assert client.get('/login').status_code == 200

    def test_login_invalido(self, client):
        r = client.post('/login', data={'email': 'x@x.com', 'senha': 'errada'})
        assert r.status_code == 200
        assert 'inválidos' in r.data.decode()

    def test_login_valido_redireciona(self, client):
        r = client.post('/login', data={'email': 'admin@clinica.com', 'senha': 'admin123'},
                        follow_redirects=False)
        assert r.status_code == 302
        assert '/agenda' in r.headers['Location']

    def test_sem_login_redireciona(self, client):
        r = client.get('/agenda/', follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_logout(self, admin_client):
        r = admin_client.get('/logout', follow_redirects=False)
        assert r.status_code == 302


class TestAgendaView:
    def test_index_200(self, admin_client):
        assert admin_client.get('/agenda/').status_code == 200

    def test_novo_form_200(self, admin_client):
        assert admin_client.get('/agenda/novo').status_code == 200

    def test_api_eventos_json(self, admin_client):
        r = admin_client.get('/agenda/api/eventos?start=2026-07-21+00:00&end=2026-07-22+00:00')
        assert r.status_code == 200
        assert r.json == []

    def test_api_expedientes_json(self, admin_client):
        r = admin_client.get('/agenda/api/expedientes')
        assert r.status_code == 200
        data = r.json
        assert isinstance(data, list)
        assert len(data) > 0
        assert 'daysOfWeek' in data[0]
        assert 'startTime' in data[0]

    def test_api_profissionais_json(self, admin_client):
        r = admin_client.get('/agenda/api/profissionais')
        assert r.status_code == 200
        data = r.json
        assert len(data) > 0
        assert 'nome' in data[0]

    def test_recepcao_nao_acessa_profissionais(self, recepcao_client):
        r = recepcao_client.get('/profissionais/')
        assert r.status_code == 403

    def test_criar_agendamento_conflito_retorna_422(self, admin_client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            # Cria paciente
            db.execute("INSERT INTO pacientes (nome) VALUES ('Teste')")
            db.commit()
            pac_id = db.execute("SELECT id FROM pacientes WHERE nome='Teste'").fetchone()['id']
            prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']
            # Cria agendamento existente
            db.execute(
                "INSERT INTO agendamentos (profissional_id, paciente_id, procedimento_id, "
                "data_hora_inicio, data_hora_fim, status) VALUES (?,?,?,?,?,?)",
                (prof_id, pac_id, proc_id, '2026-07-21 09:00', '2026-07-21 09:30', 'agendado')
            )
            db.commit()

        r = admin_client.post('/agenda/novo', data={
            'profissional_id': str(prof_id),
            'paciente_id':     str(pac_id),
            'procedimento_id': str(proc_id),
            'data_hora_inicio': '2026-07-21T09:00',
        })
        assert r.status_code == 422
        assert 'Conflito' in r.data.decode()


class TestProfissionais:
    def test_lista_200(self, admin_client):
        assert admin_client.get('/profissionais/').status_code == 200

    def test_criar_profissional(self, admin_client):
        r = admin_client.post('/profissionais/novo', data={
            'nome': 'Dra. Teste',
            'especialidade': 'Clínico',
            'cor_hex': '#9b59b6',
            'horario_inicio': '08:00',
            'horario_fim': '17:00',
            'dias_semana': ['1', '2', '3', '4', '5'],
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_cor_invalida_retorna_erro(self, admin_client):
        r = admin_client.post('/profissionais/novo', data={
            'nome': 'Dr. X',
            'cor_hex': 'INVALIDA',
            'horario_inicio': '08:00',
            'horario_fim': '18:00',
        })
        assert r.status_code == 200
        assert '#RRGGBB' in r.data.decode()


class TestProcedimentos:
    def test_lista_200(self, admin_client):
        assert admin_client.get('/procedimentos/').status_code == 200

    def test_criar_procedimento(self, admin_client):
        r = admin_client.post('/procedimentos/novo', data={
            'nome': 'Extração',
            'duracao_minutos': '45',
            'cor_hex': '#e74c3c',
        }, follow_redirects=False)
        assert r.status_code == 302


class TestPacientes:
    def test_lista_200(self, admin_client):
        assert admin_client.get('/pacientes/').status_code == 200

    def test_autocomplete_menos_3_chars(self, admin_client):
        r = admin_client.get('/pacientes/api/buscar?q=an')
        assert r.json == []

    def test_autocomplete_retorna_json(self, admin_client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            get_db().execute("INSERT INTO pacientes (nome, telefone) VALUES ('Ana Beatriz','11999990000')")
            get_db().commit()
        r = admin_client.get('/pacientes/api/buscar?q=Ana')
        assert r.status_code == 200
        assert len(r.json) == 1
        assert r.json[0]['nome'] == 'Ana Beatriz'

    def test_criar_paciente(self, admin_client):
        r = admin_client.post('/pacientes/novo', data={
            'nome': 'Carlos Novo',
            'telefone': '11988880000',
        }, follow_redirects=False)
        assert r.status_code == 302
