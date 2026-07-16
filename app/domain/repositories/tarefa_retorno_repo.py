from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.tarefa_retorno import TarefaRetorno


class TarefaRetornoRepository(ABC):

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[TarefaRetorno]:
        ...

    @abstractmethod
    def buscar_por_agendamento(self, agendamento_id: int) -> Optional[TarefaRetorno]:
        ...

    @abstractmethod
    def listar_pendentes(self) -> list[TarefaRetorno]:
        ...

    @abstractmethod
    def criar(self, tarefa: TarefaRetorno) -> TarefaRetorno:
        ...

    @abstractmethod
    def marcar_contatado(self, id: int, observacoes: Optional[str]) -> None:
        ...
