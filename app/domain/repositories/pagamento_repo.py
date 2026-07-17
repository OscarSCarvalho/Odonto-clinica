from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.pagamento import Pagamento


class PagamentoRepository(ABC):

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Pagamento]:
        ...

    @abstractmethod
    def buscar_por_agendamento(self, agendamento_id: int) -> Optional[Pagamento]:
        ...

    @abstractmethod
    def buscar_por_mensalidade_e_competencia(self, mensalidade_id: int, competencia: str) -> Optional[Pagamento]:
        ...

    @abstractmethod
    def listar_pendentes(self) -> list[Pagamento]:
        ...

    @abstractmethod
    def listar_por_paciente(self, paciente_id: int) -> list[Pagamento]:
        ...

    @abstractmethod
    def criar(self, pagamento: Pagamento) -> Pagamento:
        ...

    @abstractmethod
    def marcar_pago(
        self, id: int, forma_pagamento: str, data_pagamento: str, observacoes: Optional[str]
    ) -> None:
        ...
