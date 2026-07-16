class ConflitodeHorarioError(Exception):
    def __init__(self, profissional, procedimento, paciente, inicio, fim):
        self.profissional = profissional
        self.procedimento = procedimento
        self.paciente = paciente
        self.inicio = inicio
        self.fim = fim
        super().__init__(
            f"Conflito: {profissional} já tem {procedimento} com {paciente} "
            f"das {inicio} às {fim}"
        )


class HorarioForaDoExpedienteError(Exception):
    def __init__(self, profissional, inicio, fim):
        super().__init__(
            f"Horário fora do expediente de {profissional} ({inicio}–{fim})"
        )


class AgendamentoNaoEditavelError(Exception):
    def __init__(self, status):
        super().__init__(
            f"Não é possível editar agendamento com status '{status}'"
        )


class PacienteDuplicadoError(Exception):
    def __init__(self, cpf, nome_existente, id_existente):
        self.id_existente = id_existente
        super().__init__(f"CPF já cadastrado para {nome_existente}")


class DadosInvalidosError(Exception):
    pass
