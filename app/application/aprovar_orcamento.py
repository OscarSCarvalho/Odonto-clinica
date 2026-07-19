from app.domain.repositories.orcamento_repo import OrcamentoRepository
from app.domain.exceptions import DadosInvalidosError


class AprovarOrcamento:

    def __init__(self, orcamento_repo: OrcamentoRepository):
        self._orcamento_repo = orcamento_repo

    def executar(self, token: str = None, id: int = None):
        if token:
            orcamento = self._orcamento_repo.buscar_por_token(token)
        elif id:
            orcamento = self._orcamento_repo.buscar_por_id(id)
        else:
            raise DadosInvalidosError("Informe token ou id do orçamento")

        if not orcamento:
            raise DadosInvalidosError("Orçamento não encontrado")
        if orcamento.status not in ('rascunho', 'enviado'):
            raise DadosInvalidosError(f"Orçamento com status '{orcamento.status}' não pode ser aprovado")

        self._orcamento_repo.atualizar_status(orcamento.id, 'aprovado')
        orcamento.status = 'aprovado'
        return orcamento
