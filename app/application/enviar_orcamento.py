import uuid
from app.domain.repositories.orcamento_repo import OrcamentoRepository
from app.domain.repositories.paciente_repo import PacienteRepository
from app.domain.exceptions import DadosInvalidosError


class EnviarOrcamento:

    def __init__(
        self,
        orcamento_repo: OrcamentoRepository,
        paciente_repo: PacienteRepository,
        whatsapp_adapter,
        email_adapter,
    ):
        self._orcamento_repo = orcamento_repo
        self._paciente_repo = paciente_repo
        self._whatsapp = whatsapp_adapter
        self._email = email_adapter

    def executar(self, orcamento_id: int, base_url: str):
        orcamento = self._orcamento_repo.buscar_por_id(orcamento_id)
        if not orcamento:
            raise DadosInvalidosError("Orçamento não encontrado")

        paciente = self._paciente_repo.buscar_por_id(orcamento.paciente_id)
        if not paciente:
            raise DadosInvalidosError("Paciente não encontrado")

        token = str(uuid.uuid4())
        url = f"{base_url}/orcamento/{token}"

        itens_texto = "\n".join(
            f"  - {item.procedimento_nome or 'Procedimento'} (x{item.quantidade}): R$ {item.subtotal:.2f}"
            for item in orcamento.itens
        )
        mensagem = (
            f"Olá {paciente.nome},\n\n"
            f"Seu orçamento da OdontoClinica está pronto!\n\n"
            f"Itens:\n{itens_texto}\n\n"
            f"Total: R$ {orcamento.total_liquido:.2f}\n"
            f"Validade: {orcamento.validade_dias} dias\n\n"
            f"Acesse para aprovar ou recusar:\n{url}"
        )

        if paciente.telefone:
            try:
                self._whatsapp.enviar(paciente.telefone, mensagem)
            except Exception:
                pass

        if paciente.email:
            try:
                self._email.enviar(paciente.email, mensagem)
            except Exception:
                pass

        self._orcamento_repo.atualizar_status(orcamento_id, 'enviado', token=token)
        orcamento.status = 'enviado'
        orcamento.token_aprovacao = token
        return orcamento
