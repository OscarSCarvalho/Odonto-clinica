import calendar
from datetime import date
from app.domain.entities.pagamento import Pagamento
from app.domain.repositories.mensalidade_repo import MensalidadeRepository
from app.domain.repositories.pagamento_repo import PagamentoRepository


class GerarCobrancasMensalidades:

    def __init__(self, mensalidade_repo: MensalidadeRepository, pagamento_repo: PagamentoRepository):
        self._mens_repo = mensalidade_repo
        self._pag_repo = pagamento_repo

    def executar(self, hoje: date = None) -> None:
        hoje = hoje or date.today()
        competencia = hoje.strftime('%Y-%m')

        for mensalidade in self._mens_repo.listar_ativas():
            if self._pag_repo.buscar_por_mensalidade_e_competencia(mensalidade.id, competencia):
                continue

            ultimo_dia_mes = calendar.monthrange(hoje.year, hoje.month)[1]
            dia = min(mensalidade.dia_vencimento, ultimo_dia_mes)
            vencimento = date(hoje.year, hoje.month, dia)

            self._pag_repo.criar(Pagamento(
                id=None,
                paciente_id=mensalidade.paciente_id,
                mensalidade_id=mensalidade.id,
                valor=mensalidade.valor,
                data_vencimento=vencimento.isoformat(),
            ))
