import pytest


class TestPublicoStep1:
    def test_step1_sem_login_200(self, client):
        r = client.get('/agendar/')
        assert r.status_code == 200
        assert 'Profissional' in r.data.decode()

    def test_step1_mostra_profissionais_do_seed(self, client):
        r = client.get('/agendar/')
        assert 'Dr. Carlos Silva' in r.data.decode()


class TestPublicoStep2:
    def test_step2_sem_profissional_redireciona(self, client):
        r = client.get('/agendar/procedimento', follow_redirects=False)
        assert r.status_code == 302

    def test_step2_com_profissional_valido_200(self, client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            prof_id = get_db().execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
        r = client.get(f'/agendar/procedimento?profissional_id={prof_id}')
        assert r.status_code == 200
        assert 'Procedimento' in r.data.decode()

    def test_step2_profissional_invalido_redireciona(self, client):
        r = client.get('/agendar/procedimento?profissional_id=9999', follow_redirects=False)
        assert r.status_code == 302


class TestPublicoStep3:
    def _ids(self, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']
        return prof_id, proc_id

    def test_step3_sem_data_200(self, client, app):
        prof_id, proc_id = self._ids(app)
        r = client.get(f'/agendar/data?profissional_id={prof_id}&procedimento_id={proc_id}')
        assert r.status_code == 200
        assert 'Escolha uma data' in r.data.decode()

    def test_step3_com_data_segunda_mostra_slots(self, client, app):
        prof_id, proc_id = self._ids(app)
        # 2026-07-20 é segunda-feira
        r = client.get(f'/agendar/data?profissional_id={prof_id}&procedimento_id={proc_id}&data=2026-07-20')
        assert r.status_code == 200
        assert '08:00' in r.data.decode()

    def test_step3_domingo_sem_slots(self, client, app):
        prof_id, proc_id = self._ids(app)
        # 2026-07-19 é domingo
        r = client.get(f'/agendar/data?profissional_id={prof_id}&procedimento_id={proc_id}&data=2026-07-19')
        assert r.status_code == 200
        assert 'Sem horários disponíveis' in r.data.decode()


class TestPublicoStep4:
    def test_step4_200(self, client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']
        r = client.get(f'/agendar/confirmar?profissional_id={prof_id}'
                       f'&procedimento_id={proc_id}&data=2026-07-20&slot=09:00')
        assert r.status_code == 200
        assert '09:00' in r.data.decode()
        assert 'nome' in r.data.decode().lower()

    def test_step4_sem_params_redireciona(self, client):
        r = client.get('/agendar/confirmar', follow_redirects=False)
        assert r.status_code == 302


class TestPublicoFinalizar:
    def test_finalizar_cria_agendamento(self, client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']

        r = client.post('/agendar/finalizar', data={
            'profissional_id': str(prof_id),
            'procedimento_id': str(proc_id),
            'data': '2026-07-20',
            'slot': '09:00',
            'nome': 'Maria Teste',
            'telefone': '11999990001',
            'email': '',
        }, follow_redirects=False)
        assert r.status_code == 302
        assert '/agendar/sucesso/' in r.headers['Location']

    def test_finalizar_race_condition_redireciona_para_step3(self, client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']
            cur = db.execute("INSERT INTO pacientes (nome, telefone) VALUES ('Bloqueador','11900000001')")
            db.commit()
            pac_id = cur.lastrowid
            # Ocupa o slot 09:00
            db.execute(
                "INSERT INTO agendamentos (profissional_id, paciente_id, procedimento_id, "
                "data_hora_inicio, data_hora_fim, status) VALUES (?,?,?,?,?,?)",
                (prof_id, pac_id, proc_id, '2026-07-20 09:00', '2026-07-20 09:30', 'agendado')
            )
            db.commit()

        r = client.post('/agendar/finalizar', data={
            'profissional_id': str(prof_id),
            'procedimento_id': str(proc_id),
            'data': '2026-07-20',
            'slot': '09:00',
            'nome': 'Outro Paciente',
            'telefone': '11988880002',
        }, follow_redirects=False)
        # Deve redirecionar para step3 com mensagem de aviso
        assert r.status_code == 302
        assert '/agendar/data' in r.headers['Location']

    def test_finalizar_campos_obrigatorios_faltando(self, client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']

        r = client.post('/agendar/finalizar', data={
            'profissional_id': str(prof_id),
            'procedimento_id': str(proc_id),
            'data': '2026-07-20',
            'slot': '09:00',
            'nome': 'Teste',
            # telefone faltando
        }, follow_redirects=False)
        assert r.status_code == 302


class TestPublicoSucesso:
    def test_sucesso_200(self, client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']
            pac_cur = db.execute("INSERT INTO pacientes (nome,telefone) VALUES ('Suc','11911110000')")
            db.commit()
            pac_id = pac_cur.lastrowid
            ag_cur = db.execute(
                "INSERT INTO agendamentos (profissional_id,paciente_id,procedimento_id,"
                "data_hora_inicio,data_hora_fim,status,origem) VALUES (?,?,?,?,?,?,?)",
                (prof_id, pac_id, proc_id, '2026-07-20 10:00', '2026-07-20 10:30', 'agendado', 'autoagendamento')
            )
            db.commit()
            ag_id = ag_cur.lastrowid

        r = client.get(f'/agendar/sucesso/{ag_id}')
        assert r.status_code == 200
        assert 'confirmado' in r.data.decode().lower()
        assert '10:00' in r.data.decode()
