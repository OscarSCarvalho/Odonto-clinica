from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.profissional import Profissional


class ProfissionalRepository(ABC):

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Profissional]:
        ...

    @abstractmethod
    def listar_ativos(self) -> list[Profissional]:
        ...

    @abstractmethod
    def criar(self, profissional: Profissional) -> Profissional:
        ...

    @abstractmethod
    def atualizar(self, profissional: Profissional) -> Profissional:
        ...

    @abstractmethod
    def desativar(self, id: int) -> int:
        """Retorna quantidade de agendamentos futuros afetados."""
        ...
