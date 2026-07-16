from dataclasses import dataclass
from typing import Optional
from app.domain.exceptions import DadosInvalidosError


@dataclass
class PlanoRecorrente:
    id: Optional[int]
    paciente_id: int
    profissional_id: int
    procedimento_id: int
    intervalo_dias: int
    proxima_data: str  # ISO: "YYYY-MM-DD"
    horario_preferido: Optional[str] = None  # "HH:MM"
    observacoes: Optional[str] = None
    ativo: bool = True

    def __post_init__(self):
        if self.intervalo_dias < 1:
            raise DadosInvalidosError("Intervalo de recorrência deve ser de ao menos 1 dia")
