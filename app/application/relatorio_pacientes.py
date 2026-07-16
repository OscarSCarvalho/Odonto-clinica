from datetime import date, timedelta
from app.domain.repositories.paciente_repo import PacienteRepository

_FAIXAS = [
    (0, 12, '0-12'),
    (13, 17, '13-17'),
    (18, 25, '18-25'),
    (26, 35, '26-35'),
    (36, 50, '36-50'),
    (51, 65, '51-65'),
    (66, 999, '66+'),
]


def _calcular_idade(data_nascimento: str, hoje: date) -> int:
    nascimento = date.fromisoformat(data_nascimento)
    idade = hoje.year - nascimento.year
    if (hoje.month, hoje.day) < (nascimento.month, nascimento.day):
        idade -= 1
    return idade


def _faixa_de(idade: int) -> str:
    for minimo, maximo, rotulo in _FAIXAS:
        if minimo <= idade <= maximo:
            return rotulo
    return '66+'


class RelatorioPacientes:

    def __init__(self, paciente_repo: PacienteRepository):
        self._pac_repo = paciente_repo

    def executar(self, dias_sem_retorno: int = 90, hoje: date = None) -> dict:
        hoje = hoje or date.today()

        faixas_etarias = {rotulo: 0 for _, _, rotulo in _FAIXAS}
        for paciente in self._pac_repo.listar_todos_ativos():
            if not paciente.data_nascimento:
                continue
            idade = _calcular_idade(paciente.data_nascimento, hoje)
            faixas_etarias[_faixa_de(idade)] += 1

        limite = (hoje - timedelta(days=dias_sem_retorno)).isoformat()
        pacientes_sem_retorno = self._pac_repo.listar_sem_retorno(limite, hoje.isoformat())

        return {
            'faixas_etarias': faixas_etarias,
            'pacientes_sem_retorno': pacientes_sem_retorno,
        }
