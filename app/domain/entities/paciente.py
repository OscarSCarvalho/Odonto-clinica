from dataclasses import dataclass
from typing import Optional


@dataclass
class Paciente:
    id: Optional[int]
    nome: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    cpf: Optional[str] = None
    data_nascimento: Optional[str] = None
    observacoes: Optional[str] = None
    ativo: bool = True
