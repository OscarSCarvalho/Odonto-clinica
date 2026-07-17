import io
import json
import pytest


def _criar_agendamento(app, status='agendado', retorno_dias=None):
    """Insere paciente/profissional/procedimento/agendamento de teste e retorna os IDs."""
    with app.app_context():
        from app.infrastructure.db.connection import get_db
        db = get_db()
        db.execute("INSERT INTO pacientes (nome) VALUES ('Paciente Teste')")
        pac_id = db.execute("SELECT id FROM pacientes WHERE nome='Paciente Teste'").fetchone()['id']
        prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
        if retorno_dias is not None:
            db.execute(
                "INSERT INTO procedimentos (nome, duracao_minutos, cor_hex, retorno_dias) "
                "VALUES ('Limpeza c/ retorno', 30, '#10b981', ?)", (retorno_dias,)
            )
            proc_id = db.execute(
                "SELECT id FROM procedimentos WHERE nome='Limpeza c/ retorno'"
            ).fetchone()['id']
        else:
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']
        db.execute(
            "INSERT INTO agendamentos (profissional_id, paciente_id, procedimento_id, "
            "data_hora_inicio, data_hora_fim, status) VALUES (?,?,?,?,?,?)",
            (prof_id, pac_id, proc_id, '2026-07-21 09:00', '2026-07-21 09:30', status)
        )
        db.commit()
        ag_id = db.execute(
            "SELECT id FROM agendamentos WHERE paciente_id=?", (pac_id,)
        ).fetchone()['id']
    return {'agendamento_id': ag_id, 'paciente_id': pac_id,
            'profissional_id': prof_id, 'procedimento_id': proc_id}


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
        assert '/dashboard' in r.headers['Location']

    def test_sem_login_redireciona(self, client):
        r = client.get('/agenda/', follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_logout(self, admin_client):
        r = admin_client.get('/logout', follow_redirects=False)
        assert r.status_code == 302


class TestDashboardView:
    def test_index_200(self, admin_client):
        assert admin_client.get('/dashboard/').status_code == 200

    def test_sem_login_redireciona(self, client):
        r = client.get('/dashboard/', follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']


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

    def test_checkin_muda_status_para_aguardando(self, admin_client, app):
        ids = _criar_agendamento(app, status='confirmado')
        r = admin_client.post(f"/agenda/status/{ids['agendamento_id']}",
                              data={'status': 'aguardando'}, follow_redirects=False)
        assert r.status_code == 302
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            row = get_db().execute(
                "SELECT status FROM agendamentos WHERE id=?", (ids['agendamento_id'],)
            ).fetchone()
        assert row['status'] == 'aguardando'

    def test_editar_exibe_sugestao_de_retorno_apos_concluido(self, admin_client, app):
        ids = _criar_agendamento(app, status='em_atendimento', retorno_dias=180)
        admin_client.post(f"/agenda/status/{ids['agendamento_id']}", data={'status': 'concluido'})
        r = admin_client.get(f"/agenda/editar/{ids['agendamento_id']}")
        assert r.status_code == 200
        assert 'Retorno sugerido' in r.data.decode()
        assert 'Agendar retorno' in r.data.decode()

    def test_editar_sem_retorno_configurado_nao_exibe_sugestao(self, admin_client, app):
        ids = _criar_agendamento(app, status='em_atendimento')
        admin_client.post(f"/agenda/status/{ids['agendamento_id']}", data={'status': 'concluido'})
        r = admin_client.get(f"/agenda/editar/{ids['agendamento_id']}")
        assert r.status_code == 200
        assert 'Retorno sugerido' not in r.data.decode()


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

    def test_upload_download_e_exclusao_de_anexo(self, admin_client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            db.execute("INSERT INTO pacientes (nome) VALUES ('Paciente Anexo')")
            db.commit()
            pac_id = db.execute(
                "SELECT id FROM pacientes WHERE nome='Paciente Anexo'"
            ).fetchone()['id']

        upload = admin_client.post(
            f'/pacientes/{pac_id}/anexos',
            data={'arquivo': (io.BytesIO(b'conteudo-fake'), 'exame.pdf')},
            content_type='multipart/form-data',
            follow_redirects=False,
        )
        assert upload.status_code == 302

        editar = admin_client.get(f'/pacientes/editar/{pac_id}')
        assert 'exame.pdf' in editar.data.decode()

        with app.app_context():
            from app.infrastructure.container import anexo_repo
            anexo_id = anexo_repo().listar_por_paciente(pac_id)[0].id

        download = admin_client.get(f'/pacientes/{pac_id}/anexos/{anexo_id}/download')
        assert download.status_code == 200
        assert download.data == b'conteudo-fake'

        excluir = admin_client.post(
            f'/pacientes/{pac_id}/anexos/{anexo_id}/excluir', follow_redirects=False
        )
        assert excluir.status_code == 302
        editar_apos = admin_client.get(f'/pacientes/editar/{pac_id}')
        assert 'exame.pdf' not in editar_apos.data.decode()

    def test_upload_rejeita_extensao_nao_permitida(self, admin_client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            db.execute("INSERT INTO pacientes (nome) VALUES ('Paciente Ext')")
            db.commit()
            pac_id = db.execute(
                "SELECT id FROM pacientes WHERE nome='Paciente Ext'"
            ).fetchone()['id']

        r = admin_client.post(
            f'/pacientes/{pac_id}/anexos',
            data={'arquivo': (io.BytesIO(b'x'), 'virus.exe')},
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert 'Formato não permitido' in r.data.decode()

    def test_criar_pausar_e_reativar_plano_recorrente(self, admin_client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            db.execute("INSERT INTO pacientes (nome) VALUES ('Paciente Recorrente')")
            db.commit()
            pac_id = db.execute(
                "SELECT id FROM pacientes WHERE nome='Paciente Recorrente'"
            ).fetchone()['id']
            prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']

        criar = admin_client.post(f'/pacientes/{pac_id}/planos', data={
            'profissional_id': str(prof_id),
            'procedimento_id': str(proc_id),
            'intervalo_dias': '30',
            'proxima_data': '2026-08-01',
        }, follow_redirects=False)
        assert criar.status_code == 302

        editar = admin_client.get(f'/pacientes/editar/{pac_id}')
        assert 'a cada 30 dias' in editar.data.decode()
        assert 'Ativo' in editar.data.decode()

        with app.app_context():
            from app.infrastructure.container import plano_recorrente_repo
            plano_id = plano_recorrente_repo().listar_por_paciente(pac_id)[0].id

        pausar = admin_client.post(
            f'/pacientes/{pac_id}/planos/{plano_id}/pausar', follow_redirects=False
        )
        assert pausar.status_code == 302
        editar_pausado = admin_client.get(f'/pacientes/editar/{pac_id}')
        assert 'Pausado' in editar_pausado.data.decode()

        reativar = admin_client.post(
            f'/pacientes/{pac_id}/planos/{plano_id}/reativar', follow_redirects=False
        )
        assert reativar.status_code == 302
        editar_reativado = admin_client.get(f'/pacientes/editar/{pac_id}')
        assert 'Ativo' in editar_reativado.data.decode()

    def test_criar_pausar_e_reativar_mensalidade(self, admin_client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            db.execute("INSERT INTO pacientes (nome) VALUES ('Paciente Mensalidade')")
            db.commit()
            pac_id = db.execute(
                "SELECT id FROM pacientes WHERE nome='Paciente Mensalidade'"
            ).fetchone()['id']

        criar = admin_client.post(f'/pacientes/{pac_id}/mensalidades', data={
            'valor': '199.90',
            'dia_vencimento': '5',
            'observacoes': 'Plano ortodôntico',
        }, follow_redirects=False)
        assert criar.status_code == 302

        editar = admin_client.get(f'/pacientes/editar/{pac_id}')
        assert 'vence todo dia 5' in editar.data.decode()
        assert 'Ativa' in editar.data.decode()

        with app.app_context():
            from app.infrastructure.container import mensalidade_repo
            mensalidade_id = mensalidade_repo().listar_por_paciente(pac_id)[0].id

        pausar = admin_client.post(
            f'/pacientes/{pac_id}/mensalidades/{mensalidade_id}/pausar', follow_redirects=False
        )
        assert pausar.status_code == 302
        assert 'Pausada' in admin_client.get(f'/pacientes/editar/{pac_id}').data.decode()

        reativar = admin_client.post(
            f'/pacientes/{pac_id}/mensalidades/{mensalidade_id}/reativar', follow_redirects=False
        )
        assert reativar.status_code == 302
        assert 'Ativa' in admin_client.get(f'/pacientes/editar/{pac_id}').data.decode()


class TestRelatorios:
    def test_faltas_200(self, admin_client):
        assert admin_client.get('/relatorios/faltas').status_code == 200

    def test_faltas_recepcao_tem_acesso(self, recepcao_client):
        assert recepcao_client.get('/relatorios/faltas').status_code == 200

    def test_faltas_sem_login_redireciona(self, client):
        r = client.get('/relatorios/faltas', follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_pacientes_200(self, admin_client):
        assert admin_client.get('/relatorios/pacientes').status_code == 200

    def test_desempenho_200(self, admin_client):
        assert admin_client.get('/relatorios/desempenho').status_code == 200


class TestRecorrentes:
    def test_index_200(self, admin_client):
        assert admin_client.get('/recorrentes/').status_code == 200

    def test_sem_login_redireciona(self, client):
        r = client.get('/recorrentes/', follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_fluxo_completo_agendar_e_concluir_avanca_plano(self, admin_client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            from app.infrastructure.container import plano_recorrente_repo
            db = get_db()
            db.execute("INSERT INTO pacientes (nome) VALUES ('Paciente Aparelho')")
            db.commit()
            pac_id = db.execute(
                "SELECT id FROM pacientes WHERE nome='Paciente Aparelho'"
            ).fetchone()['id']
            prof_id = db.execute("SELECT id FROM profissionais LIMIT 1").fetchone()['id']
            proc_id = db.execute("SELECT id FROM procedimentos LIMIT 1").fetchone()['id']

        criar_plano = admin_client.post(f'/pacientes/{pac_id}/planos', data={
            'profissional_id': str(prof_id),
            'procedimento_id': str(proc_id),
            'intervalo_dias': '30',
            'proxima_data': '2026-07-20',
        })
        assert criar_plano.status_code == 302

        with app.app_context():
            from app.infrastructure.container import plano_recorrente_repo
            plano = plano_recorrente_repo().listar_por_paciente(pac_id)[0]

        # A página de recorrentes deve listar o plano e trazer o link de agendar
        listagem = admin_client.get('/recorrentes/?dias=30')
        assert 'Paciente Aparelho' in listagem.data.decode()
        assert f'plano_recorrente_id={plano.id}' in listagem.data.decode()

        # Agenda a partir do plano (simula clique em "Agendar")
        criar_ag = admin_client.post('/agenda/novo', data={
            'profissional_id': str(prof_id),
            'paciente_id': str(pac_id),
            'procedimento_id': str(proc_id),
            'data_hora_inicio': '2026-07-20T09:00',
            'plano_recorrente_id': str(plano.id),
        }, follow_redirects=False)
        assert criar_ag.status_code == 302

        with app.app_context():
            from app.infrastructure.container import agendamento_repo
            ag = agendamento_repo().listar_por_periodo('2026-07-20 00:00', '2026-07-20 23:59')[0]
            assert ag.plano_recorrente_id == plano.id

        # Conclui o agendamento e verifica que o plano avançou
        admin_client.post(f'/agenda/status/{ag.id}', data={'status': 'concluido'})

        with app.app_context():
            from app.infrastructure.container import plano_recorrente_repo
            plano_atualizado = plano_recorrente_repo().buscar_por_id(plano.id)
        assert plano_atualizado.proxima_data == '2026-08-19'


class TestRetornos:
    def test_index_200(self, admin_client):
        assert admin_client.get('/retornos/').status_code == 200

    def test_sem_login_redireciona(self, client):
        r = client.get('/retornos/', follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_concluir_agendamento_com_retorno_cria_tarefa_e_permite_contato(self, admin_client, app):
        ids = _criar_agendamento(app, status='em_atendimento', retorno_dias=180)

        admin_client.post(f"/agenda/status/{ids['agendamento_id']}", data={'status': 'concluido'})

        listagem = admin_client.get('/retornos/')
        assert 'Paciente Teste' in listagem.data.decode()

        with app.app_context():
            from app.infrastructure.container import tarefa_retorno_repo
            tarefa = tarefa_retorno_repo().buscar_por_agendamento(ids['agendamento_id'])
        assert tarefa is not None
        assert tarefa.status == 'pendente'

        contatar = admin_client.post(
            f'/retornos/{tarefa.id}/contatar',
            data={'observacoes': 'Paciente confirmou retorno por telefone'},
            follow_redirects=False,
        )
        assert contatar.status_code == 302

        listagem_apos = admin_client.get('/retornos/')
        assert 'Paciente Teste' not in listagem_apos.data.decode()

    def test_concluir_agendamento_sem_retorno_nao_cria_tarefa(self, admin_client, app):
        ids = _criar_agendamento(app, status='em_atendimento')

        admin_client.post(f"/agenda/status/{ids['agendamento_id']}", data={'status': 'concluido'})

        with app.app_context():
            from app.infrastructure.container import tarefa_retorno_repo
            tarefa = tarefa_retorno_repo().buscar_por_agendamento(ids['agendamento_id'])
        assert tarefa is None

    def test_concluir_agendamento_de_plano_recorrente_nao_cria_tarefa_de_retorno(self, admin_client, app):
        ids = _criar_agendamento(app, status='em_atendimento', retorno_dias=180)

        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            db.execute("INSERT INTO pacientes (nome) VALUES ('Paciente Plano')")
            db.commit()
            pac_id = db.execute(
                "SELECT id FROM pacientes WHERE nome='Paciente Plano'"
            ).fetchone()['id']
            db.execute(
                "INSERT INTO planos_recorrentes (paciente_id, profissional_id, procedimento_id, "
                "intervalo_dias, proxima_data) VALUES (?,?,?,?,?)",
                (pac_id, ids['profissional_id'], ids['procedimento_id'], 30, '2026-07-21')
            )
            db.commit()
            plano_id = db.execute(
                "SELECT id FROM planos_recorrentes WHERE paciente_id=?", (pac_id,)
            ).fetchone()['id']
            db.execute(
                "UPDATE agendamentos SET plano_recorrente_id=? WHERE id=?",
                (plano_id, ids['agendamento_id'])
            )
            db.commit()

        admin_client.post(f"/agenda/status/{ids['agendamento_id']}", data={'status': 'concluido'})

        with app.app_context():
            from app.infrastructure.container import tarefa_retorno_repo
            tarefa = tarefa_retorno_repo().buscar_por_agendamento(ids['agendamento_id'])
        assert tarefa is None


class TestFinanceiro:
    def test_index_200(self, admin_client):
        assert admin_client.get('/financeiro/').status_code == 200

    def test_sem_login_redireciona(self, client):
        r = client.get('/financeiro/', follow_redirects=False)
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_concluir_atendimento_gera_pagamento_e_permite_registrar(self, admin_client, app):
        # O procedimento seed 'Consulta' tem preco_base definido
        ids = _criar_agendamento(app, status='em_atendimento')

        admin_client.post(f"/agenda/status/{ids['agendamento_id']}", data={'status': 'concluido'})

        listagem = admin_client.get('/financeiro/')
        assert 'Paciente Teste' in listagem.data.decode()

        with app.app_context():
            from app.infrastructure.container import pagamento_repo
            pagamento = pagamento_repo().buscar_por_agendamento(ids['agendamento_id'])
        assert pagamento is not None
        assert pagamento.status == 'pendente'

        pagar = admin_client.post(
            f'/financeiro/{pagamento.id}/pagar',
            data={'forma_pagamento': 'pix', 'observacoes': 'Pago via pix'},
            follow_redirects=False,
        )
        assert pagar.status_code == 302

        with app.app_context():
            from app.infrastructure.container import pagamento_repo
            pagamento_atualizado = pagamento_repo().buscar_por_id(pagamento.id)
        assert pagamento_atualizado.status == 'pago'
        assert pagamento_atualizado.forma_pagamento == 'pix'

        listagem_apos = admin_client.get('/financeiro/')
        assert 'Paciente Teste' not in listagem_apos.data.decode()

    def test_pagar_rejeita_forma_de_pagamento_invalida(self, admin_client, app):
        ids = _criar_agendamento(app, status='em_atendimento')
        admin_client.post(f"/agenda/status/{ids['agendamento_id']}", data={'status': 'concluido'})

        with app.app_context():
            from app.infrastructure.container import pagamento_repo
            pagamento = pagamento_repo().buscar_por_agendamento(ids['agendamento_id'])

        r = admin_client.post(
            f'/financeiro/{pagamento.id}/pagar',
            data={'forma_pagamento': 'boleto-invalido'},
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert 'Selecione uma forma de pagamento válida' in r.data.decode()

    def test_gera_cobranca_de_mensalidade_ao_abrir_financeiro(self, admin_client, app):
        with app.app_context():
            from app.infrastructure.db.connection import get_db
            db = get_db()
            db.execute("INSERT INTO pacientes (nome) VALUES ('Paciente Mensal')")
            db.commit()
            pac_id = db.execute(
                "SELECT id FROM pacientes WHERE nome='Paciente Mensal'"
            ).fetchone()['id']
            db.execute(
                "INSERT INTO mensalidades (paciente_id, valor, dia_vencimento) VALUES (?,?,?)",
                (pac_id, 199.90, 10)
            )
            db.commit()

        listagem = admin_client.get('/financeiro/')
        assert 'Paciente Mensal' in listagem.data.decode()
        assert 'Mensalidade' in listagem.data.decode()
