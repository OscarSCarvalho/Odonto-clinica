from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.orcamento import Orcamento, OrcamentoItem


class OrcamentoRepository(ABC):

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Orcamento]:
        ...

    @abstractmethod
    def buscar_por_token(self, token: str) -> Optional[Orcamento]:
        ...

    @abstractmethod
    def listar_todos(self) -> list:
        ...

    @abstractmethod
    def listar_por_paciente(self, paciente_id: int) -> list:
        ...

    @abstractmethod
    def criar(self, orcamento: Orcamento) -> Orcamento:
        ...

    @abstractmethod
    def atualizar_status(self, id: int, status: str, token: Optional[str] = None) -> None:
        ...

    @abstractmethod
    def atualizar(self, orcamento: Orcamento) -> Orcamento:
        ...

    @abstractmethod
    def deletar_itens(self, orcamento_id: int) -> None:
        ...

    @abstractmethod
    def criar_item(self, item: OrcamentoItem) -> OrcamentoItem:
        ...

    @abstractmethod
    def deletar_item(self, item_id: int) -> None:
        ...
