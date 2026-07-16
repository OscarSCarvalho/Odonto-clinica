from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.anexo import Anexo


class AnexoRepository(ABC):

    @abstractmethod
    def listar_por_paciente(self, paciente_id: int) -> list[Anexo]:
        ...

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Anexo]:
        ...

    @abstractmethod
    def criar(self, anexo: Anexo) -> Anexo:
        ...

    @abstractmethod
    def excluir(self, id: int) -> None:
        ...
