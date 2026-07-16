from datetime import datetime, timedelta
from typing import Optional
from app.domain.repositories.procedimento_repo import ProcedimentoRepository


class SugerirRetorno:

    def __init__(self, procedimento_repo: ProcedimentoRepository):
        self._proc_repo = procedimento_repo

    def executar(self, procedimento_id: int, data_hora_inicio: str) -> Optional[datetime]:
        procedimento = self._proc_repo.buscar_por_id(procedimento_id)
        if not procedimento or not procedimento.retorno_dias:
            return None
        inicio_dt = datetime.strptime(data_hora_inicio, '%Y-%m-%d %H:%M')
        return inicio_dt + timedelta(days=procedimento.retorno_dias)
