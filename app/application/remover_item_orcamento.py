from app.domain.repositories.orcamento_repo import OrcamentoRepository
from app.domain.exceptions import DadosInvalidosError


class RemoverItemOrcamento:

    def __init__(self, orcamento_repo: OrcamentoRepository):
        self._orcamento_repo = orcamento_repo

    def executar(self, item_id: int, orcamento_id: int) -> None:
        orcamento = self._orcamento_repo.buscar_por_id(orcamento_id)
        if not orcamento:
            raise DadosInvalidosError("Orçamento não encontrado")
        if orcamento.status != 'rascunho':
            raise DadosInvalidosError("Só é possível remover itens de orçamentos em rascunho")
        self._orcamento_repo.deletar_item(item_id)
