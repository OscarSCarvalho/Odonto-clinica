from datetime import date, timedelta
from app.domain.repositories.plano_recorrente_repo import PlanoRecorrenteRepository


class ListarPlanosVencendo:

    def __init__(self, plano_recorrente_repo: PlanoRecorrenteRepository):
        self._repo = plano_recorrente_repo

    def executar(self, dias_janela: int = 14, hoje: date = None) -> list:
        hoje = hoje or date.today()
        limite = hoje + timedelta(days=dias_janela)
        vencendo = [
            p for p in self._repo.listar_ativos()
            if date.fromisoformat(p.proxima_data) <= limite
        ]
        return sorted(vencendo, key=lambda p: p.proxima_data)
