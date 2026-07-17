from datetime import date
from app.domain.repositories.pagamento_repo import PagamentoRepository


class ListarContasReceber:

    def __init__(self, pagamento_repo: PagamentoRepository):
        self._pag_repo = pagamento_repo

    def executar(self, hoje: date = None) -> dict:
        hoje = hoje or date.today()
        pendentes = sorted(self._pag_repo.listar_pendentes(), key=lambda p: p.data_vencimento)

        total_pendente = sum(p.valor for p in pendentes)
        atrasados = [p for p in pendentes if date.fromisoformat(p.data_vencimento) < hoje]
        total_atrasado = sum(p.valor for p in atrasados)

        return {
            'pagamentos': pendentes,
            'total_pendente': total_pendente,
            'total_atrasado': total_atrasado,
            'quantidade_atrasada': len(atrasados),
        }
