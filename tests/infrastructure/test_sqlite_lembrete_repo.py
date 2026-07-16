import pytest
from app.domain.entities.lembrete import ConfigLembrete
from app.infrastructure.db.repositories.sqlite_lembrete_repo import SqliteLembreteRepository


@pytest.fixture
def repo(conn):
    return SqliteLembreteRepository(conn)


@pytest.fixture
def agendamento_id(conn, profissional_id, procedimento_id, paciente_id):
    cur = conn.execute(
        "INSERT INTO agendamentos (profissional_id, paciente_id, procedimento_id, "
        "data_hora_inicio, data_hora_fim, status) VALUES (?,?,?,?,?,?)",
        (profissional_id, paciente_id, procedimento_id,
         '2026-08-01 09:00', '2026-08-01 09:30', 'agendado'),
    )
    conn.commit()
    return cur.lastrowid


class TestConfigLembretes:

    def test_criar_e_listar(self, repo):
        config = ConfigLembrete(id=None, antecedencia_h=24, tipo='whatsapp')
        salvo = repo.criar_config(config)
        assert salvo.id is not None

        lista = repo.listar_configs()
        assert len(lista) == 1
        assert lista[0].antecedencia_h == 24
        assert lista[0].tipo == 'whatsapp'
        assert lista[0].ativo is True

    def test_listar_configs_ativas_filtra_inativas(self, repo):
        repo.criar_config(ConfigLembrete(id=None, antecedencia_h=24, tipo='whatsapp'))
        repo.criar_config(ConfigLembrete(id=None, antecedencia_h=48, tipo='email'))
        configs = repo.listar_configs()
        repo.toggle_config(configs[1].id)

        ativas = repo.listar_configs_ativas()
        assert len(ativas) == 1
        assert ativas[0].antecedencia_h == 24

    def test_toggle_ativa_e_desativa(self, repo):
        config = repo.criar_config(ConfigLembrete(id=None, antecedencia_h=2, tipo='email'))
        assert repo.listar_configs()[0].ativo is True

        repo.toggle_config(config.id)
        assert repo.listar_configs()[0].ativo is False

        repo.toggle_config(config.id)
        assert repo.listar_configs()[0].ativo is True

    def test_remover_config(self, repo):
        config = repo.criar_config(ConfigLembrete(id=None, antecedencia_h=1, tipo='whatsapp'))
        repo.remover_config(config.id)
        assert repo.listar_configs() == []

    def test_listar_ordenado_por_antecedencia(self, repo):
        repo.criar_config(ConfigLembrete(id=None, antecedencia_h=48, tipo='email'))
        repo.criar_config(ConfigLembrete(id=None, antecedencia_h=2, tipo='whatsapp'))
        repo.criar_config(ConfigLembrete(id=None, antecedencia_h=24, tipo='whatsapp'))
        lista = repo.listar_configs()
        horas = [c.antecedencia_h for c in lista]
        assert horas == sorted(horas)


class TestLembretesEnviados:

    def test_ja_foi_enviado_false_quando_vazio(self, repo, agendamento_id):
        assert repo.ja_foi_enviado(agendamento_id, 24, 'whatsapp') is False

    def test_criar_e_ja_foi_enviado(self, repo, agendamento_id):
        repo.criar_lembrete(agendamento_id, 'whatsapp', 24, 'enviado', 1)
        assert repo.ja_foi_enviado(agendamento_id, 24, 'whatsapp') is True

    def test_ja_foi_enviado_ignora_status_erro(self, repo, agendamento_id):
        repo.criar_lembrete(agendamento_id, 'email', 24, 'erro', 1, 'timeout')
        assert repo.ja_foi_enviado(agendamento_id, 24, 'email') is False

    def test_buscar_para_retry_encontra_erro(self, repo, agendamento_id):
        repo.criar_lembrete(agendamento_id, 'whatsapp', 24, 'erro', 2, 'falha')
        lembrete = repo.buscar_para_retry(agendamento_id, 24, 'whatsapp')
        assert lembrete is not None
        assert lembrete.tentativas == 2
        assert lembrete.status == 'erro'

    def test_buscar_para_retry_retorna_none_quando_enviado(self, repo, agendamento_id):
        repo.criar_lembrete(agendamento_id, 'email', 48, 'enviado', 1)
        assert repo.buscar_para_retry(agendamento_id, 48, 'email') is None

    def test_atualizar_lembrete(self, repo, agendamento_id):
        repo.criar_lembrete(agendamento_id, 'email', 24, 'erro', 1, 'timeout')
        lembrete = repo.buscar_para_retry(agendamento_id, 24, 'email')
        repo.atualizar_lembrete(lembrete.id, 'enviado', 2)
        assert repo.ja_foi_enviado(agendamento_id, 24, 'email') is True

    def test_ja_foi_enviado_por_combinacao_unica(self, repo, agendamento_id):
        repo.criar_lembrete(agendamento_id, 'whatsapp', 24, 'enviado', 1)
        # mesma antecedência, canal diferente -> não enviado
        assert repo.ja_foi_enviado(agendamento_id, 24, 'email') is False
        # canal igual, antecedência diferente -> não enviado
        assert repo.ja_foi_enviado(agendamento_id, 48, 'whatsapp') is False
