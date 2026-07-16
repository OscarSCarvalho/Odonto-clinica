from datetime import datetime, timedelta
from typing import Optional
from app.domain.repositories.agendamento_repo import AgendamentoRepository
from app.domain.repositories.lembrete_repo import LembreteRepository
from app.domain.repositories.notificacao_adapter import NotificacaoAdapter

_JANELA_MINUTOS = 15
_MAX_TENTATIVAS = 3
_STATUS_ATIVOS = ('agendado', 'confirmado')


def _montar_mensagem(ag) -> str:
    dt = datetime.fromisoformat(ag.data_hora_inicio)
    return (
        f"Olá, {getattr(ag, 'paciente_nome', 'paciente')}! "
        f"Lembramos que você tem uma consulta agendada em "
        f"{dt.strftime('%d/%m/%Y às %H:%M')} "
        f"com {getattr(ag, 'profissional_nome', 'o profissional')}. "
        f"Procedimento: {getattr(ag, 'procedimento_nome', '')}. "
        f"Aguardamos você!"
    )


class EnviarLembretes:

    def __init__(
        self,
        agendamento_repo: AgendamentoRepository,
        lembrete_repo: LembreteRepository,
        whatsapp: Optional[NotificacaoAdapter],
        email: Optional[NotificacaoAdapter],
    ):
        self._ag_repo = agendamento_repo
        self._lem_repo = lembrete_repo
        self._whatsapp = whatsapp
        self._email = email

    def executar(self) -> dict:
        agora = datetime.now()
        enviados = 0
        erros = 0

        configs = self._lem_repo.listar_configs_ativas()
        if not configs:
            return {'enviados': 0, 'erros': 0}

        for config in configs:
            alvo_inicio = agora + timedelta(hours=config.antecedencia_h)
            alvo_fim = alvo_inicio + timedelta(minutes=_JANELA_MINUTOS)

            agendamentos = self._ag_repo.listar_por_periodo(
                inicio=alvo_inicio.strftime('%Y-%m-%d %H:%M'),
                fim=alvo_fim.strftime('%Y-%m-%d %H:%M'),
            )

            for ag in agendamentos:
                if ag.status not in _STATUS_ATIVOS:
                    continue

                # True = enviado, False = falha, None = skip intencional
                resultado = self._processar(ag, config.antecedencia_h, config.tipo)
                if resultado is True:
                    enviados += 1
                elif resultado is False:
                    erros += 1

        return {'enviados': enviados, 'erros': erros}

    def _processar(self, ag, antecedencia_h: int, tipo: str) -> Optional[bool]:
        """True=enviado, False=falha no envio, None=skip intencional."""
        if self._lem_repo.ja_foi_enviado(ag.id, antecedencia_h, tipo):
            return True

        registro_erro = self._lem_repo.buscar_para_retry(ag.id, antecedencia_h, tipo)
        if registro_erro and registro_erro.tentativas >= _MAX_TENTATIVAS:
            return None  # esgotou retries — skip silencioso

        destino = self._obter_destino(ag, tipo)
        if not destino:
            return None  # sem contato configurado — skip silencioso

        adapter = self._whatsapp if tipo == 'whatsapp' else self._email
        if adapter is None:
            return None

        mensagem = _montar_mensagem(ag)
        sucesso = adapter.enviar(destino, mensagem)
        tentativas = (registro_erro.tentativas if registro_erro else 0) + 1

        if registro_erro:
            self._lem_repo.atualizar_lembrete(
                id=registro_erro.id,
                status='enviado' if sucesso else 'erro',
                tentativas=tentativas,
                erro_msg=None if sucesso else 'Falha ao enviar notificação',
            )
        else:
            self._lem_repo.criar_lembrete(
                agendamento_id=ag.id,
                tipo=tipo,
                antecedencia_h=antecedencia_h,
                status='enviado' if sucesso else 'erro',
                tentativas=tentativas,
                erro_msg=None if sucesso else 'Falha ao enviar notificação',
            )

        return sucesso

    @staticmethod
    def _obter_destino(ag, tipo: str) -> Optional[str]:
        if tipo == 'whatsapp':
            return getattr(ag, 'paciente_telefone', None) or ''
        if tipo == 'email':
            return getattr(ag, 'paciente_email', None) or ''
        return None
