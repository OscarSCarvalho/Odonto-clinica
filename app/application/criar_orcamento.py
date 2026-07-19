from app.domain.entities.orcamento import Orcamento
from app.domain.repositories.orcamento_repo import OrcamentoRepository
from app.domain.repositories.paciente_repo import PacienteRepository
from app.domain.repositories.profissional_repo import ProfissionalRepository
from app.domain.exceptions import DadosInvalidosError


class CriarOrcamento:

    def __init__(
        self,
        orcamento_repo: OrcamentoRepository,
        paciente_repo: PacienteRepository,
        profissional_repo: ProfissionalRepository,
    ):
        self._orcamento_repo = orcamento_repo
        self._paciente_repo = paciente_repo
        self._profissional_repo = profissional_repo

    def executar(
        self,
        paciente_id: int,
        profissional_id: int = None,
        validade_dias: int = 30,
        observacoes: str = None,
    ) -> Orcamento:
        paciente = self._paciente_repo.buscar_por_id(paciente_id)
        if not paciente:
            raise DadosInvalidosError("Paciente não encontrado")

        if profissional_id:
            profissional = self._profissional_repo.buscar_por_id(profissional_id)
            if not profissional:
                raise DadosInvalidosError("Profissional não encontrado")

        orcamento = Orcamento(
            id=None,
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            validade_dias=validade_dias,
            observacoes=observacoes,
            status='rascunho',
        )
        return self._orcamento_repo.criar(orcamento)
