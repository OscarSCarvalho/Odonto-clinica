import pytest
from unittest.mock import MagicMock, patch
from app.application.criar_orcamento import CriarOrcamento
from app.application.adicionar_item_orcamento import AdicionarItemOrcamento
from app.application.enviar_orcamento import EnviarOrcamento
from app.application.aprovar_orcamento import AprovarOrcamento
from app.application.recusar_orcamento import RecusarOrcamento
from app.application.converter_orcamento import ConverterOrcamentoEmAgendamentos
from app.domain.entities.orcamento import Orcamento, OrcamentoItem
from app.domain.entities.paciente import Paciente
from app.domain.entities.procedimento import Procedimento
from app.domain.exceptions import DadosInvalidosError


def _paciente(id=1, nome='Ana', telefone='11999990000', email='ana@test.com'):
    return Paciente(id=id, nome=nome, telefone=telefone, email=email)


def _procedimento(id=1, nome='Limpeza', preco=150.0):
    return Procedimento(id=id, nome=nome, duracao_minutos=30, cor_hex='#e74c3c', preco_base=preco)


def _orcamento(id=1, paciente_id=1, status='rascunho', itens=None):
    o = Orcamento(id=id, paciente_id=paciente_id, status=status)
    if itens:
        o.itens = itens
    return o


class TestCriarOrcamento:

    def test_cria_com_sucesso(self):
        repo = MagicMock()
        pac_repo = MagicMock()
        prof_repo = MagicMock()
        pac_repo.buscar_por_id.return_value = _paciente()
        repo.criar.side_effect = lambda o: setattr(o, 'id', 1) or o

        uc = CriarOrcamento(repo, pac_repo, prof_repo)
        result = uc.executar(paciente_id=1, validade_dias=30)

        repo.criar.assert_called_once()
        assert result.paciente_id == 1
        assert result.status == 'rascunho'

    def test_falha_paciente_nao_encontrado(self):
        repo = MagicMock()
        pac_repo = MagicMock()
        prof_repo = MagicMock()
        pac_repo.buscar_por_id.return_value = None

        uc = CriarOrcamento(repo, pac_repo, prof_repo)
        with pytest.raises(DadosInvalidosError, match="Paciente"):
            uc.executar(paciente_id=999)

    def test_falha_profissional_nao_encontrado(self):
        repo = MagicMock()
        pac_repo = MagicMock()
        prof_repo = MagicMock()
        pac_repo.buscar_por_id.return_value = _paciente()
        prof_repo.buscar_por_id.return_value = None

        uc = CriarOrcamento(repo, pac_repo, prof_repo)
        with pytest.raises(DadosInvalidosError, match="Profissional"):
            uc.executar(paciente_id=1, profissional_id=999)


class TestAdicionarItemOrcamento:

    def test_adiciona_item_com_preco_do_procedimento(self):
        repo = MagicMock()
        proc_repo = MagicMock()
        repo.buscar_por_id.return_value = _orcamento()
        proc_repo.buscar_por_id.return_value = _procedimento(preco=200.0)
        repo.criar_item.side_effect = lambda i: setattr(i, 'id', 10) or i

        uc = AdicionarItemOrcamento(repo, proc_repo)
        item = uc.executar(orcamento_id=1, procedimento_id=1, quantidade=2)

        assert item.valor_unitario == 200.0
        assert item.quantidade == 2
        repo.criar_item.assert_called_once()

    def test_usa_valor_unitario_informado(self):
        repo = MagicMock()
        proc_repo = MagicMock()
        repo.buscar_por_id.return_value = _orcamento()
        proc_repo.buscar_por_id.return_value = _procedimento(preco=200.0)
        repo.criar_item.side_effect = lambda i: setattr(i, 'id', 10) or i

        uc = AdicionarItemOrcamento(repo, proc_repo)
        item = uc.executar(orcamento_id=1, procedimento_id=1, valor_unitario=99.0)

        assert item.valor_unitario == 99.0

    def test_falha_orcamento_nao_rascunho(self):
        repo = MagicMock()
        proc_repo = MagicMock()
        repo.buscar_por_id.return_value = _orcamento(status='enviado')

        uc = AdicionarItemOrcamento(repo, proc_repo)
        with pytest.raises(DadosInvalidosError):
            uc.executar(orcamento_id=1, procedimento_id=1)

    def test_falha_orcamento_nao_encontrado(self):
        repo = MagicMock()
        proc_repo = MagicMock()
        repo.buscar_por_id.return_value = None

        uc = AdicionarItemOrcamento(repo, proc_repo)
        with pytest.raises(DadosInvalidosError):
            uc.executar(orcamento_id=999, procedimento_id=1)

    def test_falha_procedimento_nao_encontrado(self):
        repo = MagicMock()
        proc_repo = MagicMock()
        repo.buscar_por_id.return_value = _orcamento()
        proc_repo.buscar_por_id.return_value = None

        uc = AdicionarItemOrcamento(repo, proc_repo)
        with pytest.raises(DadosInvalidosError):
            uc.executar(orcamento_id=1, procedimento_id=999)


class TestEnviarOrcamento:

    def test_envia_e_muda_status(self):
        repo = MagicMock()
        pac_repo = MagicMock()
        whatsapp = MagicMock()
        email_adp = MagicMock()
        whatsapp.enviar.return_value = True
        email_adp.enviar.return_value = True

        item = OrcamentoItem(id=1, orcamento_id=1, procedimento_id=1,
                             quantidade=1, valor_unitario=100.0)
        item.procedimento_nome = 'Limpeza'
        orcamento = _orcamento(itens=[item])
        repo.buscar_por_id.return_value = orcamento
        pac_repo.buscar_por_id.return_value = _paciente()

        uc = EnviarOrcamento(repo, pac_repo, whatsapp, email_adp)
        result = uc.executar(orcamento_id=1, base_url='http://localhost:5000')

        repo.atualizar_status.assert_called_once()
        call_args = repo.atualizar_status.call_args
        assert call_args[0][1] == 'enviado'
        assert call_args[1]['token'] is not None
        whatsapp.enviar.assert_called_once()
        email_adp.enviar.assert_called_once()

    def test_nao_falha_se_notificacao_falhar(self):
        repo = MagicMock()
        pac_repo = MagicMock()
        whatsapp = MagicMock()
        email_adp = MagicMock()
        whatsapp.enviar.side_effect = Exception("conexão falhou")
        email_adp.enviar.side_effect = Exception("smtp erro")

        item = OrcamentoItem(id=1, orcamento_id=1, procedimento_id=1,
                             quantidade=1, valor_unitario=100.0)
        item.procedimento_nome = 'Consulta'
        orcamento = _orcamento(itens=[item])
        repo.buscar_por_id.return_value = orcamento
        pac_repo.buscar_por_id.return_value = _paciente()

        uc = EnviarOrcamento(repo, pac_repo, whatsapp, email_adp)
        # deve completar sem exceção
        result = uc.executar(orcamento_id=1, base_url='http://localhost')
        repo.atualizar_status.assert_called_once()

    def test_falha_orcamento_nao_encontrado(self):
        repo = MagicMock()
        pac_repo = MagicMock()
        repo.buscar_por_id.return_value = None

        uc = EnviarOrcamento(repo, pac_repo, MagicMock(), MagicMock())
        with pytest.raises(DadosInvalidosError):
            uc.executar(orcamento_id=999, base_url='http://localhost')


class TestAprovarOrcamento:

    def test_aprova_via_token(self):
        repo = MagicMock()
        repo.buscar_por_token.return_value = _orcamento(status='enviado')

        uc = AprovarOrcamento(repo)
        result = uc.executar(token='abc123')

        repo.atualizar_status.assert_called_once_with(1, 'aprovado')
        assert result.status == 'aprovado'

    def test_aprova_via_id(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = _orcamento(status='rascunho')

        uc = AprovarOrcamento(repo)
        result = uc.executar(id=1)

        repo.atualizar_status.assert_called_once_with(1, 'aprovado')

    def test_falha_status_invalido(self):
        repo = MagicMock()
        repo.buscar_por_token.return_value = _orcamento(status='aprovado')

        uc = AprovarOrcamento(repo)
        with pytest.raises(DadosInvalidosError):
            uc.executar(token='abc123')

    def test_falha_orcamento_nao_encontrado(self):
        repo = MagicMock()
        repo.buscar_por_token.return_value = None

        uc = AprovarOrcamento(repo)
        with pytest.raises(DadosInvalidosError):
            uc.executar(token='invalido')


class TestConverterOrcamentoEmAgendamentos:

    def test_converte_com_sucesso(self):
        repo = MagicMock()
        criar_ag = MagicMock()
        pag_repo = MagicMock()

        item = OrcamentoItem(id=1, orcamento_id=1, procedimento_id=1,
                             quantidade=1, valor_unitario=200.0)
        orcamento = _orcamento(status='aprovado', itens=[item])
        repo.buscar_por_id.return_value = orcamento

        ag_mock = MagicMock()
        ag_mock.id = 10
        criar_ag.executar.return_value = ag_mock

        uc = ConverterOrcamentoEmAgendamentos(repo, criar_ag, pag_repo)
        result = uc.executar(
            orcamento_id=1,
            agendamentos_data=[{
                'procedimento_id': 1,
                'profissional_id': 1,
                'data_hora_inicio': '2026-07-20 09:00',
            }],
        )

        assert len(result) == 1
        criar_ag.executar.assert_called_once()
        pag_repo.criar.assert_called_once()

    def test_falha_orcamento_nao_aprovado(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = _orcamento(status='rascunho')

        uc = ConverterOrcamentoEmAgendamentos(repo, MagicMock(), MagicMock())
        with pytest.raises(DadosInvalidosError):
            uc.executar(orcamento_id=1, agendamentos_data=[])

    def test_falha_orcamento_nao_encontrado(self):
        repo = MagicMock()
        repo.buscar_por_id.return_value = None

        uc = ConverterOrcamentoEmAgendamentos(repo, MagicMock(), MagicMock())
        with pytest.raises(DadosInvalidosError):
            uc.executar(orcamento_id=999, agendamentos_data=[])
