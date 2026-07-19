from app.domain.repositories.orcamento_repo import OrcamentoRepository
from app.domain.repositories.profissional_repo import ProfissionalRepository
from app.domain.exceptions import DadosInvalidosError


class AtualizarOrcamento:

    def __init__(
        self,
        orcamento_repo: OrcamentoRepository,
        profissional_repo: ProfissionalRepository,
    ):
        self._orcamento_repo = orcamento_repo
        self._profissional_repo = profissional_repo

    def executar(
        self,
        id: int,
        profissional_id: int = None,
        validade_dias: int = 30,
        desconto_global: float = 0.0,
        desconto_tipo: str = 'percentual',
        observacoes: str = None,
    ):
        orcamento = self._orcamento_repo.buscar_por_id(id)
        if not orcamento:
            raise DadosInvalidosError("Orçamento não encontrado")
        if orcamento.status != 'rascunho':
            raise DadosInvalidosError("Só é possível editar orçamentos em rascunho")

        if profissional_id:
            profissional = self._profissional_repo.buscar_por_id(profissional_id)
            if not profissional:
                raise DadosInvalidosError("Profissional não encontrado")

        orcamento.profissional_id = profissional_id
        orcamento.validade_dias = validade_dias
        orcamento.desconto_global = desconto_global
        orcamento.desconto_tipo = desconto_tipo
        orcamento.observacoes = observacoes

        return self._orcamento_repo.atualizar(orcamento)
