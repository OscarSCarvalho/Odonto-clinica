from dataclasses import dataclass
from typing import Optional
from app.domain.exceptions import DadosInvalidosError

FORMAS_PAGAMENTO = {'dinheiro', 'pix', 'cartao_debito', 'cartao_credito'}


@dataclass
class Pagamento:
    id: Optional[int]
    paciente_id: int
    valor: float
    data_vencimento: str  # ISO: "YYYY-MM-DD"
    agendamento_id: Optional[int] = None
    mensalidade_id: Optional[int] = None
    forma_pagamento: Optional[str] = None
    status: str = 'pendente'  # 'pendente' | 'pago'
    data_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    criado_em: Optional[str] = None

    def __post_init__(self):
        if self.valor <= 0:
            raise DadosInvalidosError("Valor do pagamento deve ser maior que zero")
