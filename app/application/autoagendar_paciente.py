from app.domain.entities.paciente import Paciente
from app.domain.repositories.paciente_repo import PacienteRepository
from app.application.criar_agendamento import CriarAgendamento


class AutoagendarPaciente:

    def __init__(self, paciente_repo: PacienteRepository, criar_agendamento: CriarAgendamento):
        self._pac_repo = paciente_repo
        self._criar = criar_agendamento

    def executar(
        self,
        profissional_id: int,
        procedimento_id: int,
        data_hora_inicio: str,
        nome: str,
        telefone: str,
        email: str = None,
    ):
        paciente = self._buscar_ou_criar(nome.strip(), telefone.strip(), email)

        # Pode lançar ConflitodeHorarioError (race condition) — propaga para a rota tratar
        return self._criar.executar(
            profissional_id=profissional_id,
            paciente_id=paciente.id,
            procedimento_id=procedimento_id,
            data_hora_inicio=data_hora_inicio,
            origem='autoagendamento',
        )

    def _buscar_ou_criar(self, nome: str, telefone: str, email: str = None) -> Paciente:
        if telefone:
            existente = self._pac_repo.buscar_por_telefone(telefone)
            if existente:
                return existente

        novo = Paciente(id=None, nome=nome, telefone=telefone or None, email=email or None)
        return self._pac_repo.criar(novo)
