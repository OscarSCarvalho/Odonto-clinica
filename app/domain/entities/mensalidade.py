from dataclasses import dataclass
from typing import Optional
from app.domain.exceptions import DadosInvalidosError


@dataclass
class Mensalidade:
    id: Optional[int]
    paciente_id: int
    valor: float
    dia_vencimento: int  # 1-28 (evita problemas em meses curtos)
    observacoes: Optional[str] = None
    ativo: bool = True

    def __post_init__(self):
        if self.valor <= 0:
            raise DadosInvalidosError("Valor da mensalidade deve ser maior que zero")
        if not (1 <= self.dia_vencimento <= 28):
            raise DadosInvalidosError("Dia de vencimento deve ser entre 1 e 28")
