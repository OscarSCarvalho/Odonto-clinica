from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.lembrete import ConfigLembrete, LembreteEnviado


class LembreteRepository(ABC):

    # ── config_lembretes ──────────────────────────────────────────────────────

    @abstractmethod
    def listar_configs(self) -> list[ConfigLembrete]:
        ...

    @abstractmethod
    def listar_configs_ativas(self) -> list[ConfigLembrete]:
        ...

    @abstractmethod
    def criar_config(self, config: ConfigLembrete) -> ConfigLembrete:
        ...

    @abstractmethod
    def remover_config(self, id: int) -> None:
        ...

    @abstractmethod
    def toggle_config(self, id: int) -> None:
        ...

    # ── lembretes_enviados ────────────────────────────────────────────────────

    @abstractmethod
    def ja_foi_enviado(self, agendamento_id: int, antecedencia_h: int, tipo: str) -> bool:
        ...

    @abstractmethod
    def buscar_para_retry(
        self, agendamento_id: int, antecedencia_h: int, tipo: str
    ) -> Optional[LembreteEnviado]:
        ...

    @abstractmethod
    def criar_lembrete(
        self, agendamento_id: int, tipo: str, antecedencia_h: int,
        status: str, tentativas: int, erro_msg: Optional[str] = None
    ) -> None:
        ...

    @abstractmethod
    def atualizar_lembrete(
        self, id: int, status: str, tentativas: int, erro_msg: Optional[str] = None
    ) -> None:
        ...
