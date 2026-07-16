from dataclasses import dataclass
from typing import Optional


@dataclass
class TarefaRetorno:
    id: Optional[int]
    agendamento_id: int
    paciente_id: int
    data_sugerida: str  # ISO: "YYYY-MM-DD"
    observacoes: Optional[str] = None
    status: str = 'pendente'  # 'pendente' | 'contatado'
    contato_em: Optional[str] = None
    criado_em: Optional[str] = None
