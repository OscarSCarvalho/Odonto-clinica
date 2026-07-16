from dataclasses import dataclass, field
from typing import Optional
from app.domain.exceptions import DadosInvalidosError


@dataclass
class Profissional:
    id: Optional[int]
    nome: str
    especialidade: Optional[str]
    cor_hex: str
    horario_inicio: str  # "HH:MM"
    horario_fim: str     # "HH:MM"
    dias_semana: str     # CSV: "1,2,3,4,5" (0=dom, 6=sab)
    usuario_id: Optional[int] = None
    ativo: bool = True

    def __post_init__(self):
        if not self.nome or not self.nome.strip():
            raise DadosInvalidosError("Nome do profissional é obrigatório")
        if not self.cor_hex.startswith('#') or len(self.cor_hex) != 7:
            raise DadosInvalidosError("Cor deve estar no formato #RRGGBB")

    def trabalha_no_dia(self, weekday: int) -> bool:
        """weekday: 0=seg … 6=dom (padrão Python datetime.weekday())"""
        # Converte de Python weekday (0=seg) para o padrão armazenado (0=dom)
        dia_armazenado = (weekday + 1) % 7
        return str(dia_armazenado) in self.dias_semana.split(',')

    @property
    def dias_lista(self) -> list[int]:
        return [int(d) for d in self.dias_semana.split(',') if d.strip()]
