import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.domain.repositories.notificacao_adapter import NotificacaoAdapter


class EmailAdapter(NotificacaoAdapter):
    """Envia e-mails via SMTP (stdlib smtplib, sem dependências externas)."""

    def __init__(self, host: str, port: int, user: str, password: str, from_addr: str):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._from = from_addr

    def enviar(self, destino: str, mensagem: str) -> bool:
        if not self._host or not self._user or not destino:
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Lembrete de consulta — OdontoClinica'
        msg['From'] = self._from or self._user
        msg['To'] = destino
        msg.attach(MIMEText(mensagem, 'plain', 'utf-8'))

        try:
            with smtplib.SMTP(self._host, self._port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._from or self._user, [destino], msg.as_string())
            return True
        except smtplib.SMTPException:
            return False
        except Exception:
            return False
