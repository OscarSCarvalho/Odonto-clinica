from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.paciente import Paciente


class PacienteRepository(ABC):

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Paciente]:
        ...

    @abstractmethod
    def buscar_por_cpf(self, cpf: str) -> Optional[Paciente]:
        ...

    @abstractmethod
    def buscar_por_telefone(self, telefone: str) -> Optional[Paciente]:
        ...

    @abstractmethod
    def buscar_por_nome(self, termo: str, limite: int = 10) -> list[Paciente]:
        ...

    @abstractmethod
    def criar(self, paciente: Paciente) -> Paciente:
        ...

    @abstractmethod
    def atualizar(self, paciente: Paciente) -> Paciente:
        ...

    @abstractmethod
    def desativar(self, id: int) -> None:
        ...

    @abstractmethod
    def listar_aniversariantes_do_dia(self, mes: int, dia: int) -> list[Paciente]:
        ...
