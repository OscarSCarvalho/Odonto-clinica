from flask import current_app
from app.infrastructure.db.connection import get_db
from app.infrastructure.db.repositories.sqlite_profissional_repo import SqliteProfissionalRepository
from app.infrastructure.db.repositories.sqlite_procedimento_repo import SqliteProcedimentoRepository
from app.infrastructure.db.repositories.sqlite_paciente_repo import SqlitePacienteRepository
from app.infrastructure.db.repositories.sqlite_agendamento_repo import SqliteAgendamentoRepository
from app.infrastructure.db.repositories.sqlite_lembrete_repo import SqliteLembreteRepository
from app.infrastructure.db.repositories.sqlite_anexo_repo import SqliteAnexoRepository
from app.infrastructure.db.repositories.sqlite_plano_recorrente_repo import SqlitePlanoRecorrenteRepository
from app.infrastructure.db.repositories.sqlite_tarefa_retorno_repo import SqliteTarefaRetornoRepository
from app.infrastructure.db.repositories.sqlite_pagamento_repo import SqlitePagamentoRepository
from app.infrastructure.db.repositories.sqlite_mensalidade_repo import SqliteMensalidadeRepository
from app.infrastructure.notifications.whatsapp_adapter import WhatsAppAdapter
from app.infrastructure.notifications.email_adapter import EmailAdapter
from app.application.verificar_conflito import VerificarConflito
from app.application.criar_agendamento import CriarAgendamento
from app.application.editar_agendamento import EditarAgendamento
from app.application.cancelar_agendamento import CancelarAgendamento
from app.application.listar_agenda import ListarAgenda
from app.application.listar_slots_disponiveis import ListarSlotsDisponiveis
from app.application.autoagendar_paciente import AutoagendarPaciente
from app.application.enviar_lembretes import EnviarLembretes
from app.application.obter_dashboard import ObterDashboard
from app.application.sugerir_retorno import SugerirRetorno
from app.application.relatorio_faltas import RelatorioFaltas
from app.application.listar_planos_vencendo import ListarPlanosVencendo
from app.application.avancar_plano_recorrente import AvancarPlanoRecorrente
from app.application.criar_tarefa_retorno import CriarTarefaRetorno
from app.application.relatorio_pacientes import RelatorioPacientes
from app.application.relatorio_desempenho import RelatorioDesempenho
from app.application.criar_pagamento_atendimento import CriarPagamentoAtendimento
from app.application.gerar_cobrancas_mensalidades import GerarCobrancasMensalidades
from app.application.listar_contas_receber import ListarContasReceber
from app.infrastructure.db.repositories.sqlite_orcamento_repo import SqliteOrcamentoRepository
from app.application.criar_orcamento import CriarOrcamento
from app.application.obter_orcamento import ObterOrcamento
from app.application.listar_orcamentos import ListarOrcamentos
from app.application.adicionar_item_orcamento import AdicionarItemOrcamento
from app.application.remover_item_orcamento import RemoverItemOrcamento
from app.application.atualizar_orcamento import AtualizarOrcamento
from app.application.enviar_orcamento import EnviarOrcamento
from app.application.aprovar_orcamento import AprovarOrcamento
from app.application.recusar_orcamento import RecusarOrcamento
from app.application.converter_orcamento import ConverterOrcamentoEmAgendamentos


def profissional_repo():
    return SqliteProfissionalRepository(get_db())


def procedimento_repo():
    return SqliteProcedimentoRepository(get_db())


def paciente_repo():
    return SqlitePacienteRepository(get_db())


def agendamento_repo():
    return SqliteAgendamentoRepository(get_db())


def _verificar_conflito():
    return VerificarConflito(agendamento_repo(), profissional_repo())


def criar_agendamento_uc():
    return CriarAgendamento(agendamento_repo(), procedimento_repo(), _verificar_conflito())


def editar_agendamento_uc():
    return EditarAgendamento(agendamento_repo(), procedimento_repo(), _verificar_conflito())


def cancelar_agendamento_uc():
    return CancelarAgendamento(agendamento_repo())


def listar_agenda_uc():
    return ListarAgenda(agendamento_repo())


def listar_slots_uc():
    return ListarSlotsDisponiveis(agendamento_repo(), profissional_repo(), procedimento_repo())


def autoagendar_paciente_uc():
    return AutoagendarPaciente(paciente_repo(), criar_agendamento_uc())


def lembrete_repo():
    return SqliteLembreteRepository(get_db())


def _whatsapp_adapter():
    cfg = current_app.config
    return WhatsAppAdapter(
        api_url=cfg.get('WHATSAPP_API_URL', ''),
        api_key=cfg.get('WHATSAPP_API_KEY', ''),
        instance=cfg.get('WHATSAPP_INSTANCE', ''),
    )


def _email_adapter():
    cfg = current_app.config
    return EmailAdapter(
        host=cfg.get('SMTP_HOST', ''),
        port=cfg.get('SMTP_PORT', 587),
        user=cfg.get('SMTP_USER', ''),
        password=cfg.get('SMTP_PASS', ''),
        from_addr=cfg.get('EMAIL_FROM', ''),
    )


def enviar_lembretes_uc():
    return EnviarLembretes(agendamento_repo(), lembrete_repo(), _whatsapp_adapter(), _email_adapter())


def obter_dashboard_uc():
    return ObterDashboard(
        agendamento_repo(), paciente_repo(), plano_recorrente_repo(), tarefa_retorno_repo(), pagamento_repo()
    )


def sugerir_retorno_uc():
    return SugerirRetorno(procedimento_repo())


def relatorio_faltas_uc():
    return RelatorioFaltas(agendamento_repo())


def anexo_repo():
    return SqliteAnexoRepository(get_db())


def plano_recorrente_repo():
    return SqlitePlanoRecorrenteRepository(get_db())


def listar_planos_vencendo_uc():
    return ListarPlanosVencendo(plano_recorrente_repo())


def avancar_plano_uc():
    return AvancarPlanoRecorrente(plano_recorrente_repo())


def tarefa_retorno_repo():
    return SqliteTarefaRetornoRepository(get_db())


def criar_tarefa_retorno_uc():
    return CriarTarefaRetorno(tarefa_retorno_repo(), sugerir_retorno_uc())


def relatorio_pacientes_uc():
    return RelatorioPacientes(paciente_repo())


def relatorio_desempenho_uc():
    return RelatorioDesempenho(agendamento_repo())


def pagamento_repo():
    return SqlitePagamentoRepository(get_db())


def mensalidade_repo():
    return SqliteMensalidadeRepository(get_db())


def criar_pagamento_atendimento_uc():
    return CriarPagamentoAtendimento(pagamento_repo(), procedimento_repo())


def gerar_cobrancas_mensalidades_uc():
    return GerarCobrancasMensalidades(mensalidade_repo(), pagamento_repo())


def listar_contas_receber_uc():
    return ListarContasReceber(pagamento_repo())


def orcamento_repo():
    return SqliteOrcamentoRepository(get_db())


def criar_orcamento_uc():
    return CriarOrcamento(orcamento_repo(), paciente_repo(), profissional_repo())


def obter_orcamento_uc():
    return ObterOrcamento(orcamento_repo())


def listar_orcamentos_uc():
    return ListarOrcamentos(orcamento_repo())


def adicionar_item_orcamento_uc():
    return AdicionarItemOrcamento(orcamento_repo(), procedimento_repo())


def remover_item_orcamento_uc():
    return RemoverItemOrcamento(orcamento_repo())


def atualizar_orcamento_uc():
    return AtualizarOrcamento(orcamento_repo(), profissional_repo())


def enviar_orcamento_uc():
    return EnviarOrcamento(orcamento_repo(), paciente_repo(), _whatsapp_adapter(), _email_adapter())


def aprovar_orcamento_uc():
    return AprovarOrcamento(orcamento_repo())


def recusar_orcamento_uc():
    return RecusarOrcamento(orcamento_repo())


def converter_orcamento_uc():
    return ConverterOrcamentoEmAgendamentos(orcamento_repo(), criar_agendamento_uc(), pagamento_repo())
