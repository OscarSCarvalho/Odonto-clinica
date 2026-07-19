import pytest
from app.domain.entities.orcamento import Orcamento, OrcamentoItem
from app.domain.exceptions import DadosInvalidosError


class TestOrcamentoItemSubtotal:

    def test_subtotal_percentual(self):
        item = OrcamentoItem(
            id=None, orcamento_id=1, procedimento_id=1,
            quantidade=2, valor_unitario=100.0,
            desconto_item=10.0, desconto_tipo='percentual',
        )
        # 2 * 100 * (1 - 10/100) = 180.0
        assert item.subtotal == pytest.approx(180.0)

    def test_subtotal_valor(self):
        item = OrcamentoItem(
            id=None, orcamento_id=1, procedimento_id=1,
            quantidade=3, valor_unitario=50.0,
            desconto_item=20.0, desconto_tipo='valor',
        )
        # 3 * 50 - 20 = 130.0
        assert item.subtotal == pytest.approx(130.0)

    def test_subtotal_sem_desconto(self):
        item = OrcamentoItem(
            id=None, orcamento_id=1, procedimento_id=1,
            quantidade=1, valor_unitario=200.0,
        )
        assert item.subtotal == pytest.approx(200.0)

    def test_validacao_quantidade_minima(self):
        with pytest.raises(DadosInvalidosError):
            OrcamentoItem(id=None, orcamento_id=1, procedimento_id=1,
                          quantidade=0, valor_unitario=100.0)

    def test_validacao_valor_unitario_zero(self):
        with pytest.raises(DadosInvalidosError):
            OrcamentoItem(id=None, orcamento_id=1, procedimento_id=1,
                          quantidade=1, valor_unitario=0.0)

    def test_validacao_desconto_negativo(self):
        with pytest.raises(DadosInvalidosError):
            OrcamentoItem(id=None, orcamento_id=1, procedimento_id=1,
                          quantidade=1, valor_unitario=100.0, desconto_item=-5.0)

    def test_validacao_desconto_tipo_invalido(self):
        with pytest.raises(DadosInvalidosError):
            OrcamentoItem(id=None, orcamento_id=1, procedimento_id=1,
                          quantidade=1, valor_unitario=100.0, desconto_tipo='invalido')


class TestOrcamentoTotais:

    def _orcamento_com_itens(self):
        o = Orcamento(id=None, paciente_id=1)
        o.itens = [
            OrcamentoItem(id=1, orcamento_id=1, procedimento_id=1,
                          quantidade=2, valor_unitario=100.0),  # subtotal = 200
            OrcamentoItem(id=2, orcamento_id=1, procedimento_id=2,
                          quantidade=1, valor_unitario=50.0,
                          desconto_item=10.0, desconto_tipo='percentual'),  # subtotal = 45
        ]
        return o

    def test_total_bruto(self):
        o = self._orcamento_com_itens()
        assert o.total_bruto == pytest.approx(245.0)

    def test_total_liquido_percentual(self):
        o = self._orcamento_com_itens()
        o.desconto_global = 10.0
        o.desconto_tipo = 'percentual'
        # 245 * 0.9 = 220.5
        assert o.total_liquido == pytest.approx(220.5)

    def test_total_liquido_valor(self):
        o = self._orcamento_com_itens()
        o.desconto_global = 45.0
        o.desconto_tipo = 'valor'
        # 245 - 45 = 200
        assert o.total_liquido == pytest.approx(200.0)

    def test_total_liquido_sem_desconto(self):
        o = self._orcamento_com_itens()
        assert o.total_liquido == pytest.approx(245.0)

    def test_total_bruto_sem_itens(self):
        o = Orcamento(id=None, paciente_id=1)
        assert o.total_bruto == pytest.approx(0.0)

    def test_expirado_falso_sem_criado_em(self):
        o = Orcamento(id=None, paciente_id=1)
        assert o.expirado is False

    def test_expirado_com_data_antiga(self):
        o = Orcamento(id=None, paciente_id=1, validade_dias=30, criado_em='2020-01-01 10:00:00')
        assert o.expirado is True

    def test_nao_expirado_recente(self):
        from datetime import date, timedelta
        recente = (date.today() - timedelta(days=5)).isoformat() + ' 10:00:00'
        o = Orcamento(id=None, paciente_id=1, validade_dias=30, criado_em=recente)
        assert o.expirado is False


class TestOrcamentoValidacoes:

    def test_paciente_id_invalido(self):
        with pytest.raises(DadosInvalidosError):
            Orcamento(id=None, paciente_id=0)

    def test_validade_dias_minimo(self):
        with pytest.raises(DadosInvalidosError):
            Orcamento(id=None, paciente_id=1, validade_dias=0)

    def test_desconto_global_negativo(self):
        with pytest.raises(DadosInvalidosError):
            Orcamento(id=None, paciente_id=1, desconto_global=-1.0)

    def test_desconto_tipo_invalido(self):
        with pytest.raises(DadosInvalidosError):
            Orcamento(id=None, paciente_id=1, desconto_tipo='invalido')
