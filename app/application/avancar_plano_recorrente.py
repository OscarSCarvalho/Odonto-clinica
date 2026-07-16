from datetime import datetime, timedelta
from app.domain.repositories.plano_recorrente_repo import PlanoRecorrenteRepository


class AvancarPlanoRecorrente:

    def __init__(self, plano_recorrente_repo: PlanoRecorrenteRepository):
        self._repo = plano_recorrente_repo

    def executar(self, plano_id: int, data_hora_base: str) -> None:
        plano = self._repo.buscar_por_id(plano_id)
        if not plano or not plano.ativo:
            return
        base_data = datetime.strptime(data_hora_base, '%Y-%m-%d %H:%M').date()
        plano.proxima_data = (base_data + timedelta(days=plano.intervalo_dias)).isoformat()
        self._repo.atualizar(plano)
