from app.domain.entities.orcamento import OrcamentoItem
from app.domain.repositories.orcamento_repo import OrcamentoRepository
from app.domain.repositories.procedimento_repo import ProcedimentoRepository
from app.domain.exceptions import DadosInvalidosError


class AdicionarItemOrcamento:

    def __init__(
        self,
        orcamento_repo: OrcamentoRepository,
        procedimento_repo: ProcedimentoRepository,
    ):
        self._orcamento_repo = orcamento_repo
        self._procedimento_repo = procedimento_repo

    def executar(
        self,
        orcamento_id: int,
        procedimento_id: int,
        quantidade: int = 1,
        valor_unitario: float = None,
        desconto_item: float = 0.0,
        desconto_tipo: str = 'percentual',
    ) -> OrcamentoItem:
        orcamento = self._orcamento_repo.buscar_por_id(orcamento_id)
        if not orcamento:
            raise DadosInvalidosError("Orçamento não encontrado")
        if orcamento.status != 'rascunho':
            raise DadosInvalidosError("Só é possível adicionar itens a orçamentos em rascunho")

        procedimento = self._procedimento_repo.buscar_por_id(procedimento_id)
        if not procedimento:
            raise DadosInvalidosError("Procedimento não encontrado")

        if valor_unitario is None:
            if not procedimento.preco_base or procedimento.preco_base <= 0:
                raise DadosInvalidosError(
                    f"O procedimento '{procedimento.nome}' não tem preço cadastrado. "
                    f"Configure o preço em Procedimentos antes de usar no orçamento."
                )
            valor_unitario = procedimento.preco_base

        if valor_unitario <= 0:
            raise DadosInvalidosError("Valor unitário deve ser maior que zero")

        item = OrcamentoItem(
            id=None,
            orcamento_id=orcamento_id,
            procedimento_id=procedimento_id,
            quantidade=quantidade,
            valor_unitario=valor_unitario,
            desconto_item=desconto_item,
            desconto_tipo=desconto_tipo,
        )
        return self._orcamento_repo.criar_item(item)
