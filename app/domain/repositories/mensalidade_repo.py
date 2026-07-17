from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.mensalidade import Mensalidade


class MensalidadeRepository(ABC):

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Mensalidade]:
        ...

    @abstractmethod
    def listar_por_paciente(self, paciente_id: int) -> list[Mensalidade]:
        ...

    @abstractmethod
    def listar_ativas(self) -> list[Mensalidade]:
        ...

    @abstractmethod
    def criar(self, mensalidade: Mensalidade) -> Mensalidade:
        ...

    @abstractmethod
    def desativar(self, id: int) -> None:
        ...

    @abstractmethod
    def reativar(self, id: int) -> None:
        ...
