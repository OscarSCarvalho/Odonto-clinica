import json
import urllib.request
import urllib.error
from app.domain.repositories.notificacao_adapter import NotificacaoAdapter


class WhatsAppAdapter(NotificacaoAdapter):
    """Envia mensagens via Evolution API (urllib, sem dependências externas)."""

    def __init__(self, api_url: str, api_key: str, instance: str):
        self._api_url = api_url.rstrip('/')
        self._api_key = api_key
        self._instance = instance

    def enviar(self, destino: str, mensagem: str) -> bool:
        if not self._api_url or not self._api_key or not self._instance:
            return False

        numero = ''.join(filter(str.isdigit, destino))
        if not numero:
            return False

        payload = json.dumps({
            'number': numero,
            'text': mensagem,
        }).encode('utf-8')

        url = f'{self._api_url}/message/sendText/{self._instance}'
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'apikey': self._api_key,
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in (200, 201)
        except urllib.error.URLError:
            return False
        except Exception:
            return False
