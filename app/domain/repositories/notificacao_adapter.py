from abc import ABC, abstractmethod


class NotificacaoAdapter(ABC):

    @abstractmethod
    def enviar(self, destino: str, mensagem: str) -> bool:
        """Retorna True em sucesso, False em falha (nunca lança exceção)."""
        ...
