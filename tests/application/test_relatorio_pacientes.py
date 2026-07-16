from datetime import date
from unittest.mock import MagicMock
from app.application.relatorio_pacientes import RelatorioPacientes
from app.domain.entities.paciente import Paciente


def _paciente(**kwargs):
    defaults = dict(id=1, nome='Teste', data_nascimento=None)
    defaults.update(kwargs)
    return Paciente(**defaults)


def _uc(pacientes=None, sem_retorno=None):
    repo = MagicMock()
    repo.listar_todos_ativos.return_value = pacientes or []
    repo.listar_sem_retorno.return_value = sem_retorno or []
    return RelatorioPacientes(repo), repo


class TestRelatorioPacientes:
    def test_agrupa_por_faixa_etaria(self):
        pacientes = [
            _paciente(data_nascimento='2020-01-01'),   # crianca
            _paciente(data_nascimento='2000-01-01'),   # 26 (a depender do hoje)
            _paciente(data_nascimento=None),            # sem data, ignorado
        ]
        uc, _ = _uc(pacientes=pacientes)
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['faixas_etarias']['0-12'] == 1
        assert resultado['faixas_etarias']['26-35'] == 1
        assert sum(resultado['faixas_etarias'].values()) == 2

    def test_faixa_etaria_considera_aniversario_ainda_nao_ocorrido(self):
        # Nasceu em 2000-12-31: em 2026-07-16 ainda nao fez 26 anos (so em dezembro)
        pacientes = [_paciente(data_nascimento='2000-12-31')]
        uc, _ = _uc(pacientes=pacientes)
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['faixas_etarias']['18-25'] == 1
        assert resultado['faixas_etarias']['26-35'] == 0

    def test_repassa_janela_de_dias_sem_retorno_ao_repositorio(self):
        uc, repo = _uc()
        uc.executar(dias_sem_retorno=60, hoje=date(2026, 7, 16))
        repo.listar_sem_retorno.assert_called_once_with('2026-05-17', '2026-07-16')

    def test_retorna_pacientes_sem_retorno_do_repositorio(self):
        pac = _paciente(nome='João')
        uc, _ = _uc(sem_retorno=[pac])
        resultado = uc.executar(hoje=date(2026, 7, 16))
        assert resultado['pacientes_sem_retorno'] == [pac]
