from app.domain.repositories.orcamento_repo import OrcamentoRepository


class ListarOrcamentos:

    def __init__(self, orcamento_repo: OrcamentoRepository):
        self._orcamento_repo = orcamento_repo

    def executar(self, status: str = None, paciente_id: int = None) -> list:
        if paciente_id:
            orcamentos = self._orcamento_repo.listar_por_paciente(paciente_id)
        else:
            orcamentos = self._orcamento_repo.listar_todos()

        if status:
            orcamentos = [o for o in orcamentos if o.status == status]

        return orcamentos
