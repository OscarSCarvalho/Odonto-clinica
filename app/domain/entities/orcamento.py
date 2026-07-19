from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from app.domain.exceptions import DadosInvalidosError


@dataclass
class OrcamentoItem:
    id: Optional[int]
    orcamento_id: int
    procedimento_id: int
    quantidade: int
    valor_unitario: float
    desconto_item: float = 0.0
    desconto_tipo: str = 'percentual'
    procedimento_nome: Optional[str] = None

    def __post_init__(self):
        if self.quantidade < 1:
            raise DadosInvalidosError("Quantidade deve ser pelo menos 1")
        if self.valor_unitario <= 0:
            raise DadosInvalidosError("Valor unitário deve ser maior que zero")
        if self.desconto_item < 0:
            raise DadosInvalidosError("Desconto não pode ser negativo")
        if self.desconto_tipo not in ('percentual', 'valor'):
            raise DadosInvalidosError("Tipo de desconto deve ser 'percentual' ou 'valor'")

    @property
    def subtotal(self) -> float:
        if self.desconto_tipo == 'percentual':
            return self.quantidade * self.valor_unitario * (1 - self.desconto_item / 100)
        else:
            return self.quantidade * self.valor_unitario - self.desconto_item


@dataclass
class Orcamento:
    id: Optional[int]
    paciente_id: int
    profissional_id: Optional[int] = None
    status: str = 'rascunho'
    validade_dias: int = 30
    desconto_global: float = 0.0
    desconto_tipo: str = 'percentual'
    observacoes: Optional[str] = None
    token_aprovacao: Optional[str] = None
    criado_em: Optional[str] = None
    itens: list = field(default_factory=list)
    paciente_nome: Optional[str] = None
    profissional_nome: Optional[str] = None

    def __post_init__(self):
        if self.paciente_id <= 0:
            raise DadosInvalidosError("Paciente inválido")
        if self.validade_dias < 1:
            raise DadosInvalidosError("Validade deve ser de pelo menos 1 dia")
        if self.desconto_global < 0:
            raise DadosInvalidosError("Desconto global não pode ser negativo")
        if self.desconto_tipo not in ('percentual', 'valor'):
            raise DadosInvalidosError("Tipo de desconto deve ser 'percentual' ou 'valor'")

    @property
    def total_bruto(self) -> float:
        return sum(item.subtotal for item in self.itens)

    @property
    def total_liquido(self) -> float:
        bruto = self.total_bruto
        if self.desconto_tipo == 'percentual':
            return bruto * (1 - self.desconto_global / 100)
        else:
            return bruto - self.desconto_global

    @property
    def expirado(self) -> bool:
        if not self.criado_em:
            return False
        try:
            criado = datetime.fromisoformat(self.criado_em).date()
            expira = criado
            from datetime import timedelta
            expira = criado + timedelta(days=self.validade_dias)
            return expira < date.today()
        except (ValueError, TypeError):
            return False
