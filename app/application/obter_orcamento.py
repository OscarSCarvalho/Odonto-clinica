from app.domain.entities.orcamento import Orcamento
from app.domain.repositories.orcamento_repo import OrcamentoRepository
from app.domain.exceptions import DadosInvalidosError


class ObterOrcamento:

    def __init__(self, orcamento_repo: OrcamentoRepository):
        self._orcamento_repo = orcamento_repo

    def executar(self, id: int) -> Orcamento:
        orcamento = self._orcamento_repo.buscar_por_id(id)
        if not orcamento:
            raise DadosInvalidosError("Orçamento não encontrado")
        return orcamento
