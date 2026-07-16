from dataclasses import dataclass
from typing import Optional

EXTENSOES_PERMITIDAS = {'.jpg', '.jpeg', '.png', '.pdf'}


@dataclass
class Anexo:
    id: Optional[int]
    paciente_id: int
    nome_original: str
    caminho_arquivo: str
    criado_em: Optional[str] = None
