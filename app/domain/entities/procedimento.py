from dataclasses import dataclass
from typing import Optional
from app.domain.exceptions import DadosInvalidosError


@dataclass
class Procedimento:
    id: Optional[int]
    nome: str
    duracao_minutos: int
    cor_hex: str
    preco_base: Optional[float] = None
    ativo: bool = True

    def __post_init__(self):
        if not self.nome or not self.nome.strip():
            raise DadosInvalidosError("Nome do procedimento é obrigatório")
        if self.duracao_minutos < 5:
            raise DadosInvalidosError("Duração mínima é 5 minutos")
        if not self.cor_hex.startswith('#') or len(self.cor_hex) != 7:
            raise DadosInvalidosError("Cor deve estar no formato #RRGGBB")
