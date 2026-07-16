from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.plano_recorrente import PlanoRecorrente


class PlanoRecorrenteRepository(ABC):

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[PlanoRecorrente]:
        ...

    @abstractmethod
    def listar_por_paciente(self, paciente_id: int) -> list[PlanoRecorrente]:
        ...

    @abstractmethod
    def listar_ativos(self) -> list[PlanoRecorrente]:
        ...

    @abstractmethod
    def criar(self, plano: PlanoRecorrente) -> PlanoRecorrente:
        ...

    @abstractmethod
    def atualizar(self, plano: PlanoRecorrente) -> PlanoRecorrente:
        ...

    @abstractmethod
    def desativar(self, id: int) -> None:
        ...

    @abstractmethod
    def reativar(self, id: int) -> None:
        ...
