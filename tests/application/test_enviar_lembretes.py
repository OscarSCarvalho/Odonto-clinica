import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from app.application.enviar_lembretes import EnviarLembretes
from app.domain.entities.lembrete import ConfigLembrete, LembreteEnviado
from app.domain.entities.agendamento import Agendamento


def _ag(id=1, status='agendado', inicio=None, telefone='11999990000', email='p@test.com'):
    dh = inicio or (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M')
    ag = Agendamento(
        id=id, profissional_id=1, paciente_id=1, procedimento_id=1,
        data_hora_inicio=dh, data_hora_fim=dh,
        status=status,
    )
    ag.paciente_nome = 'Ana'
    ag.paciente_telefone = telefone
    ag.paciente_email = email
    ag.profissional_nome = 'Dr. Carlos'
    ag.procedimento_nome = 'Consulta'
    return ag


def _config(tipo='whatsapp', antecedencia_h=24):
    return ConfigLembrete(id=1, antecedencia_h=antecedencia_h, tipo=tipo, ativo=True)


def _build_uc(configs, agendamentos, ja_enviado=False, retry=None,
              whatsapp_ok=True, email_ok=True):
    ag_repo = MagicMock()
    ag_repo.listar_por_periodo.return_value = agendamentos

    lem_repo = MagicMock()
    lem_repo.listar_configs_ativas.return_value = configs
    lem_repo.ja_foi_enviado.return_value = ja_enviado
    lem_repo.buscar_para_retry.return_value = retry

    whatsapp = MagicMock()
    whatsapp.enviar.return_value = whatsapp_ok

    email = MagicMock()
    email.enviar.return_value = email_ok

    return EnviarLembretes(ag_repo, lem_repo, whatsapp, email), lem_repo, whatsapp, email


class TestEnviarLembretes:

    def test_sem_configs_retorna_zero(self):
        uc, *_ = _build_uc(configs=[], agendamentos=[])
        resultado = uc.executar()
        assert resultado == {'enviados': 0, 'erros': 0}

    def test_envia_whatsapp_com_sucesso(self):
        ag = _ag()
        uc, lem_repo, whatsapp, _ = _build_uc(
            configs=[_config('whatsapp')],
            agendamentos=[ag],
        )
        resultado = uc.executar()
        assert resultado['enviados'] == 1
        assert resultado['erros'] == 0
        whatsapp.enviar.assert_called_once()
        lem_repo.criar_lembrete.assert_called_once()
        args = lem_repo.criar_lembrete.call_args
        assert args.kwargs.get('status') == 'enviado' or args[1].get('status') == 'enviado' or 'enviado' in args[0]

    def test_envia_email_com_sucesso(self):
        ag = _ag()
        uc, lem_repo, _, email = _build_uc(
            configs=[_config('email')],
            agendamentos=[ag],
        )
        resultado = uc.executar()
        assert resultado['enviados'] == 1
        email.enviar.assert_called_once()

    def test_pula_agendamento_ja_enviado(self):
        ag = _ag()
        uc, lem_repo, whatsapp, _ = _build_uc(
            configs=[_config('whatsapp')],
            agendamentos=[ag],
            ja_enviado=True,
        )
        resultado = uc.executar()
        # já enviado conta como sucesso (idempotente)
        assert resultado['enviados'] == 1
        whatsapp.enviar.assert_not_called()

    def test_pula_status_cancelado(self):
        ag = _ag(status='cancelado')
        uc, lem_repo, whatsapp, _ = _build_uc(
            configs=[_config('whatsapp')],
            agendamentos=[ag],
        )
        resultado = uc.executar()
        assert resultado['enviados'] == 0
        assert resultado['erros'] == 0
        whatsapp.enviar.assert_not_called()

    def test_pula_status_falta(self):
        ag = _ag(status='falta')
        uc, _, whatsapp, _ = _build_uc(
            configs=[_config('whatsapp')],
            agendamentos=[ag],
        )
        uc.executar()
        whatsapp.enviar.assert_not_called()

    def test_falha_registra_erro(self):
        ag = _ag()
        uc, lem_repo, whatsapp, _ = _build_uc(
            configs=[_config('whatsapp')],
            agendamentos=[ag],
            whatsapp_ok=False,
        )
        resultado = uc.executar()
        assert resultado['erros'] == 1
        assert resultado['enviados'] == 0
        lem_repo.criar_lembrete.assert_called_once()

    def test_retry_atualiza_registro_existente(self):
        ag = _ag()
        registro_erro = LembreteEnviado(
            id=99, agendamento_id=1, tipo='whatsapp',
            antecedencia_h=24, tentativas=1, status='erro',
        )
        uc, lem_repo, whatsapp, _ = _build_uc(
            configs=[_config('whatsapp')],
            agendamentos=[ag],
            retry=registro_erro,
        )
        uc.executar()
        lem_repo.atualizar_lembrete.assert_called_once()
        lem_repo.criar_lembrete.assert_not_called()

    def test_max_tentativas_para_retry(self):
        ag = _ag()
        registro_esgotado = LembreteEnviado(
            id=99, agendamento_id=1, tipo='whatsapp',
            antecedencia_h=24, tentativas=3, status='erro',
        )
        uc, lem_repo, whatsapp, _ = _build_uc(
            configs=[_config('whatsapp')],
            agendamentos=[ag],
            retry=registro_esgotado,
        )
        resultado = uc.executar()
        # esgotou tentativas -> não tenta, não conta como enviado nem erro
        whatsapp.enviar.assert_not_called()
        assert resultado['enviados'] == 0
        assert resultado['erros'] == 0

    def test_sem_telefone_nao_envia_whatsapp(self):
        ag = _ag(telefone='')
        uc, lem_repo, whatsapp, _ = _build_uc(
            configs=[_config('whatsapp')],
            agendamentos=[ag],
        )
        resultado = uc.executar()
        whatsapp.enviar.assert_not_called()
        assert resultado['erros'] == 0

    def test_sem_email_nao_envia_email(self):
        ag = _ag(email='')
        uc, lem_repo, _, email_mock = _build_uc(
            configs=[_config('email')],
            agendamentos=[ag],
        )
        resultado = uc.executar()
        email_mock.enviar.assert_not_called()
        assert resultado['erros'] == 0
