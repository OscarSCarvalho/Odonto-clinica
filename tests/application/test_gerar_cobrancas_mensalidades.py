from datetime import date
from unittest.mock import MagicMock
from app.application.gerar_cobrancas_mensalidades import GerarCobrancasMensalidades
from app.domain.entities.mensalidade import Mensalidade


def _mensalidade(**kwargs):
    defaults = dict(id=1, paciente_id=1, valor=150.0, dia_vencimento=10)
    defaults.update(kwargs)
    return Mensalidade(**defaults)


def _uc(mensalidades=None, ja_existe=None):
    mens_repo = MagicMock()
    mens_repo.listar_ativas.return_value = mensalidades or []
    pag_repo = MagicMock()
    pag_repo.buscar_por_mensalidade_e_competencia.return_value = ja_existe
    return GerarCobrancasMensalidades(mens_repo, pag_repo), mens_repo, pag_repo


class TestGerarCobrancasMensalidades:
    def test_gera_cobranca_no_dia_de_vencimento(self):
        uc, _, pag_repo = _uc(mensalidades=[_mensalidade(dia_vencimento=10)])
        uc.executar(hoje=date(2026, 7, 16))

        criado = pag_repo.criar.call_args[0][0]
        assert criado.mensalidade_id == 1
        assert criado.paciente_id == 1
        assert criado.valor == 150.0
        assert criado.data_vencimento == '2026-07-10'

    def test_ajusta_dia_de_vencimento_maior_que_o_mes(self):
        # Fevereiro (nao bissexto) so tem 28 dias
        uc, _, pag_repo = _uc(mensalidades=[_mensalidade(dia_vencimento=28)])
        uc.executar(hoje=date(2026, 2, 15))
        criado = pag_repo.criar.call_args[0][0]
        assert criado.data_vencimento == '2026-02-28'

    def test_nao_duplica_cobranca_da_mesma_competencia(self):
        from app.domain.entities.pagamento import Pagamento
        existente = Pagamento(id=1, paciente_id=1, mensalidade_id=1, valor=150.0, data_vencimento='2026-07-10')
        uc, _, pag_repo = _uc(mensalidades=[_mensalidade()], ja_existe=existente)

        uc.executar(hoje=date(2026, 7, 16))

        pag_repo.criar.assert_not_called()

    def test_verifica_competencia_no_formato_ano_mes(self):
        uc, _, pag_repo = _uc(mensalidades=[_mensalidade(id=5)])
        uc.executar(hoje=date(2026, 7, 16))
        pag_repo.buscar_por_mensalidade_e_competencia.assert_called_once_with(5, '2026-07')
