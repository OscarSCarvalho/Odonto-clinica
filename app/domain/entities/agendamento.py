from dataclasses import dataclass
from typing import Optional
from datetime import datetime

STATUS_EDITAVEIS = {'agendado', 'confirmado'}
STATUS_FINAIS = {'concluido', 'em_atendimento'}
STATUS_INATIVOS = {'cancelado', 'falta'}


@dataclass
class Agendamento:
    id: Optional[int]
    profissional_id: int
    paciente_id: int
    procedimento_id: int
    data_hora_inicio: str  # ISO: "YYYY-MM-DD HH:MM"
    data_hora_fim: str
    status: str = 'agendado'
    observacoes: Optional[str] = None
    origem: str = 'interno'
    plano_recorrente_id: Optional[int] = None

    @property
    def inicio_dt(self) -> datetime:
        return datetime.fromisoformat(self.data_hora_inicio)

    @property
    def fim_dt(self) -> datetime:
        return datetime.fromisoformat(self.data_hora_fim)

    @property
    def ativo(self) -> bool:
        return self.status not in STATUS_INATIVOS

    def sobreposicao_com(self, outro: 'Agendamento') -> bool:
        if not outro.ativo:
            return False
        return self.inicio_dt < outro.fim_dt and self.fim_dt > outro.inicio_dt

    def pode_editar_horario(self) -> bool:
        return self.status in STATUS_EDITAVEIS

    def pode_cancelar(self) -> bool:
        return self.status != 'concluido'
