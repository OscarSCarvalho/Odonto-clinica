from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.agendamento import Agendamento


class AgendamentoRepository(ABC):

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Agendamento]:
        ...

    @abstractmethod
    def listar_por_periodo(
        self, inicio: str, fim: str, profissional_id: Optional[int] = None
    ) -> list[Agendamento]:
        ...

    @abstractmethod
    def buscar_conflitos(
        self, profissional_id: int, inicio: str, fim: str,
        excluir_id: Optional[int] = None
    ) -> list[Agendamento]:
        ...

    @abstractmethod
    def criar(self, agendamento: Agendamento) -> Agendamento:
        ...

    @abstractmethod
    def atualizar(self, agendamento: Agendamento) -> Agendamento:
        ...
