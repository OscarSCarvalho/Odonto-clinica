from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.procedimento import Procedimento


class ProcedimentoRepository(ABC):

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Procedimento]:
        ...

    @abstractmethod
    def listar_ativos(self) -> list[Procedimento]:
        ...

    @abstractmethod
    def criar(self, procedimento: Procedimento) -> Procedimento:
        ...

    @abstractmethod
    def atualizar(self, procedimento: Procedimento) -> Procedimento:
        ...

    @abstractmethod
    def desativar(self, id: int) -> None:
        ...
