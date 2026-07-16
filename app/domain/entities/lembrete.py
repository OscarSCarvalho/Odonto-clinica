from dataclasses import dataclass
from typing import Optional


@dataclass
class ConfigLembrete:
    id: Optional[int]
    antecedencia_h: int
    tipo: str        # 'whatsapp' | 'email'
    ativo: bool = True


@dataclass
class LembreteEnviado:
    id: Optional[int]
    agendamento_id: int
    tipo: str
    antecedencia_h: int
    tentativas: int = 0
    enviado_em: Optional[str] = None
    status: str = 'pendente'   # 'pendente' | 'enviado' | 'erro'
    erro_msg: Optional[str] = None
