# PLAN.md — OdontoClinica / SistemaGestao
# Módulo: Agenda Clínica

**Versão:** 1.0  
**Data:** 2026-07-15  
**Agentes responsáveis:** Squad Alpha (Arquitetura) + Squad Beta (Engenharia) + Squad Delta (DevOps)  
**Fase 2 (Comercial) aprovada em:** 2026-07-15  
**Referência:** SPEC.md v1.0 | CONTEXT.md v1.0

---

## Convenções deste documento

- **[D]** = camada `/domain`
- **[A]** = camada `/application`
- **[I]** = camada `/infrastructure`
- **[IF]** = camada `/interfaces`
- **[FE]** = frontend (templates + JS)
- **[OPS]** = DevOps / infraestrutura
- **[TEST]** = testes automatizados
- `→ depende de` = tarefa deve estar concluída antes de iniciar esta
- Estimativas em horas incluem testes unitários da própria tarefa

---

## SPRINT 0 — Fundação do Projeto

**Objetivo:** estrutura de diretórios, configuração, banco de dados e autenticação funcionando.  
**Critério de aceite do sprint:** `flask run` sobe, login/logout funciona, banco é criado via script.

---

### T01 — Estrutura de diretórios e dependências
**Camada:** [OPS]  
**Horas:** 1h  
**Dependências:** nenhuma

Criar a estrutura completa de pastas conforme CONTEXT.md seção 3.3.  
Criar `requirements.txt` com dependências mínimas:
```
flask
python-dotenv
```
Criar `.env.example`:
```
FLASK_SECRET_KEY=troque-em-producao
FLASK_ENV=development
DB_PATH=./data/odonto.db
```
Criar `.gitignore` (incluir `*.db`, `.env`, `__pycache__`).

**Aceite:** `tree app/` reflete a estrutura do CONTEXT.md sem erros de importação.

---

### T02 — Configuração central (`config.py`) e ponto de entrada (`run.py`)
**Camada:** [OPS]  
**Horas:** 1h  
**Dependências:** T01

`config.py` lê variáveis do `.env` e expõe:
- `SECRET_KEY`
- `DB_PATH`
- `FLASK_ENV`

`run.py` cria a app Flask, registra todos os blueprints e inicializa o banco na primeira execução.

**Aceite:** `python run.py` inicia sem erro; `flask --app run shell` importa `app` sem exceção.

---

### T03 — Conexão sqlite3 e schema SQL
**Camada:** [I]  
**Horas:** 2h  
**Dependências:** T02

`app/infrastructure/db/connection.py`:
- Função `get_db()` retorna conexão sqlite3 com `row_factory = sqlite3.Row`.
- Função `init_db()` lê e executa `schema.sql`.
- Teardown automático via `app.teardown_appcontext`.

`app/infrastructure/db/schema.sql`:
- DDL completo conforme CONTEXT.md seção 4 (todas as tabelas + índices).
- Inserir dados seed: 1 usuário admin (`admin@clinica.com` / `admin123`), 1 profissional, 2 procedimentos.

**Aceite:** `python -c "from app.infrastructure.db.connection import init_db; init_db()"` cria o arquivo `.db` com todas as tabelas. Seed visível via `sqlite3 data/odonto.db ".tables"`.

---

### T04 — Autenticação por sessão Flask
**Camada:** [IF]  
**Horas:** 3h  
**Dependências:** T03

`app/interfaces/auth/routes.py` (blueprint `auth`, prefix `/`):
- `GET/POST /login` — valida email + senha (hash bcrypt), cria sessão com `user_id`, `perfil`, `nome`.
- `GET /logout` — limpa sessão, redireciona para `/login`.

`app/interfaces/auth/decorators.py`:
- `@requer_login` — redireciona para `/login` se sessão ausente.
- `@requer_perfil(*perfis)` — retorna `403` se perfil não autorizado.

Senha armazenada como `werkzeug.security.generate_password_hash`.

**Aceite:** POST `/login` com credenciais seed cria sessão; acessar `/agenda` sem login redireciona para `/login`; `@requer_perfil('admin')` bloqueia usuário `recepcao` com `403`.

---

### T05 — Layout base e arquivos estáticos
**Camada:** [FE]  
**Horas:** 2h  
**Dependências:** T04

`app/templates/base.html`:
- Navbar com: logo, menu (Agenda / Profissionais / Procedimentos / Pacientes), nome do usuário logado, botão logout.
- Bloco `{% block content %}`.
- Inclusão de FullCalendar.js via CDN (`5.11.x`).
- CSS utilitário mínimo em `app/static/css/main.css`.

`app/templates/auth/login.html`: formulário de login standalone (sem navbar).

**Aceite:** `/login` renderiza página de login; após login, navbar exibe nome do usuário; links de menu não quebram (podem retornar 404 temporariamente).

---

## SPRINT 1 — Domínio e Casos de Uso Core

**Objetivo:** camadas `/domain` e `/application` completas e testadas sem banco ativo.  
**Critério de aceite do sprint:** `pytest tests/domain/ tests/application/` passa 100% sem arquivo `.db`.

---

### T06 — Entidades de domínio
**Camada:** [D]  
**Horas:** 2h  
**Dependências:** T01

Criar dataclasses (ou classes simples) para cada entidade com validações puras:

`app/domain/entities/profissional.py` — `Profissional(id, nome, cor_hex, horario_inicio, horario_fim, dias_semana, ativo)`.  
`app/domain/entities/procedimento.py` — `Procedimento(id, nome, duracao_minutos, cor_hex, ativo)`.  
Validação: `duracao_minutos >= 5` (CB-05 da SPEC).  
`app/domain/entities/paciente.py` — `Paciente(id, nome, telefone, email, cpf, ativo)`.  
`app/domain/entities/agendamento.py` — `Agendamento(id, profissional_id, paciente_id, procedimento_id, data_hora_inicio, data_hora_fim, status, origem)`.  
Método `sobreposicao_com(outro: Agendamento) -> bool` — retorna `True` se os intervalos se sobrepõem (excluindo `cancelado`/`falta`).

**Aceite:** `pytest tests/domain/test_entidades.py` — 10+ casos incluindo CB-03 (fim = início seguinte = sem conflito) e CB-04 (cancelado não bloqueia).

---

### T07 — Exceções de domínio
**Camada:** [D]  
**Horas:** 0.5h  
**Dependências:** T06

`app/domain/exceptions.py`:
```python
class ConflitodeHorarioError(Exception): ...
class HorarioForaDoExpedienteError(Exception): ...
class AgendamentoNaoEditavelError(Exception): ...
class PacienteDuplicadoError(Exception): ...
class DadosInvalidosError(Exception): ...
```

**Aceite:** exceções importáveis sem dependências de framework.

---

### T08 — Interfaces de repositório (ports)
**Camada:** [D]  
**Horas:** 1h  
**Dependências:** T06, T07

`app/domain/repositories/agendamento_repo.py` — ABC com métodos:
- `buscar_por_id(id) -> Agendamento | None`
- `listar_por_periodo(profissional_id, inicio, fim) -> list[Agendamento]`
- `criar(agendamento) -> Agendamento`
- `atualizar(agendamento) -> Agendamento`
- `buscar_conflitos(profissional_id, inicio, fim, excluir_id=None) -> list[Agendamento]`

`app/domain/repositories/profissional_repo.py`, `paciente_repo.py`, `procedimento_repo.py` — ABCs análogos com operações CRUD + `listar_ativos()`.

**Aceite:** ABCs importáveis; instanciar diretamente lança `TypeError` (não é concreto).

---

### T09 — Use Case: VerificarConflito
**Camada:** [A]  
**Horas:** 2h  
**Dependências:** T07, T08

`app/application/verificar_conflito.py`:

```python
class VerificarConflito:
    def __init__(self, agendamento_repo: AgendamentoRepository): ...
    def executar(self, profissional_id, inicio, fim, excluir_id=None) -> None:
        # lança ConflitodeHorarioError se houver sobreposição
        # lança HorarioForaDoExpedienteError se fora do expediente do profissional
```

Usa `agendamento_repo.buscar_conflitos()` e verifica expediente via `Profissional.dias_semana` + horários.

**Aceite:** `pytest tests/application/test_verificar_conflito.py` — casos: sem conflito (passa), com conflito (lança), CB-02 (ultrapassa fim do expediente, lança), CB-03 (fim = início do próximo, passa), CB-04 (conflito com cancelado, passa).

---

### T10 — Use Case: CriarAgendamento
**Camada:** [A]  
**Horas:** 2h  
**Dependências:** T09

`app/application/criar_agendamento.py`:

```python
class CriarAgendamento:
    def __init__(self, agendamento_repo, procedimento_repo, verificar_conflito: VerificarConflito): ...
    def executar(self, profissional_id, paciente_id, procedimento_id, data_hora_inicio, origem='interno') -> Agendamento:
        # 1. Busca procedimento para calcular data_hora_fim
        # 2. Chama VerificarConflito.executar() — pode lançar exceções
        # 3. Persiste e retorna Agendamento
```

**Aceite:** `pytest tests/application/test_criar_agendamento.py` — criação com sucesso, conflito bloqueado, fora do expediente bloqueado.

---

### T11 — Use Case: EditarAgendamento
**Camada:** [A]  
**Horas:** 1.5h  
**Dependências:** T10

`app/application/editar_agendamento.py`:
- Bloqueia edição de `data_hora_inicio` quando `status` é `concluido` ou `em_atendimento` → lança `AgendamentoNaoEditavelError`.
- Re-executa `VerificarConflito` com `excluir_id=agendamento.id`.

**Aceite:** `pytest tests/application/test_editar_agendamento.py` — edição normal, bloqueio de concluído, re-verificação de conflito excluindo o próprio.

---

### T12 — Use Case: CancelarAgendamento
**Camada:** [A]  
**Horas:** 1h  
**Dependências:** T11

`app/application/cancelar_agendamento.py`:
- Lança `AgendamentoNaoEditavelError` se `status == 'concluido'`.
- Muda status para `cancelado`.

**Aceite:** `pytest tests/application/test_cancelar_agendamento.py`.

---

### T13 — Use Case: ListarAgenda
**Camada:** [A]  
**Horas:** 1h  
**Dependências:** T08

`app/application/listar_agenda.py`:
- `executar(profissional_id=None, inicio=None, fim=None) -> list[Agendamento]`
- Filtra por profissional se fornecido; aplica filtro de período.

**Aceite:** `pytest tests/application/test_listar_agenda.py`.

---

## SPRINT 2 — Infraestrutura (Repositórios sqlite3)

**Objetivo:** implementar todos os repositórios concretos em sqlite3.  
**Critério de aceite do sprint:** testes de integração com banco temporário passando.

---

### T14 — SqliteProfissionalRepository
**Camada:** [I]  
**Horas:** 2h  
**Dependências:** T03, T08

`app/infrastructure/db/repositories/sqlite_profissional_repo.py`:
- Implementa `ProfissionalRepository` (port do domínio).
- Métodos: `criar`, `buscar_por_id`, `listar_ativos`, `atualizar`, `desativar`.
- Query `desativar` verifica agendamentos futuros e retorna contagem antes de desativar.

**Aceite:** `pytest tests/infrastructure/test_sqlite_profissional_repo.py` com banco temporário em memória (`:memory:`).

---

### T15 — SqliteProcedimentoRepository
**Camada:** [I]  
**Horas:** 1.5h  
**Dependências:** T03, T08

Análogo a T14 para `Procedimento`.  
Validação: rejeita `duracao_minutos < 5` antes de persistir.

**Aceite:** `pytest tests/infrastructure/test_sqlite_procedimento_repo.py`.

---

### T16 — SqlitePacienteRepository
**Camada:** [I]  
**Horas:** 2h  
**Dependências:** T03, T08

`app/infrastructure/db/repositories/sqlite_paciente_repo.py`:
- Métodos: `criar`, `buscar_por_id`, `buscar_por_cpf`, `buscar_por_telefone`, `buscar_por_nome(termo)` (LIKE, mínimo 3 chars, máximo 10 resultados), `atualizar`, `desativar`.
- `criar` verifica duplicidade de CPF → lança `PacienteDuplicadoError`.

**Aceite:** `pytest tests/infrastructure/test_sqlite_paciente_repo.py` — incluindo busca por nome e duplicidade de CPF.

---

### T17 — SqliteAgendamentoRepository
**Camada:** [I]  
**Horas:** 3h  
**Dependências:** T03, T08

`app/infrastructure/db/repositories/sqlite_agendamento_repo.py`:
- `buscar_conflitos`: query com `WHERE profissional_id = ? AND status NOT IN ('cancelado','falta') AND data_hora_fim > ? AND data_hora_inicio < ?` (detecta sobreposição por intervalo).
- `listar_por_periodo`: retorna agendamentos com JOIN em profissional, paciente e procedimento (para o FullCalendar).
- `atualizar`: atualiza `atualizado_em = datetime('now')` automaticamente.

**Aceite:** `pytest tests/infrastructure/test_sqlite_agendamento_repo.py` — CB-03 (sem sobreposição em bordas), CB-04 (cancelado não retorna em `buscar_conflitos`).

---

## SPRINT 3 — Interfaces, Rotas e Templates (CRUD)

**Objetivo:** todas as telas de CRUD funcionais no browser.  
**Critério de aceite do sprint:** fluxo completo de criar/editar/deletar profissional, procedimento, paciente e agendamento sem erros 500.

---

### T18 — Blueprint: Profissionais (CRUD)
**Camada:** [IF] + [FE]  
**Horas:** 3h  
**Dependências:** T04, T14

`app/interfaces/profissionais/routes.py` (blueprint `profissionais`, prefix `/profissionais`):
- `GET /` — lista todos os profissionais.
- `GET/POST /novo` — formulário de criação.
- `GET/POST /editar/<id>` — formulário de edição (pré-preenchido).
- `POST /desativar/<id>` — desativa (com alerta de agendamentos futuros, UC-05).

Templates: `templates/profissionais/lista.html`, `form.html`.  
Todos os endpoints: `@requer_perfil('admin')`.

**Aceite:** CRUD completo funcionando; tentativa de cor inválida retorna mensagem de erro no formulário.

---

### T19 — Blueprint: Procedimentos (CRUD)
**Camada:** [IF] + [FE]  
**Horas:** 2h  
**Dependências:** T04, T15

Análogo a T18 para `Procedimento`.  
`@requer_perfil('admin')`.

**Aceite:** CRUD completo; duração < 5 min retorna erro de validação no formulário.

---

### T20 — Blueprint: Pacientes (CRUD + autocomplete)
**Camada:** [IF] + [FE]  
**Horas:** 3h  
**Dependências:** T04, T16

`app/interfaces/pacientes/routes.py` (blueprint `pacientes`, prefix `/pacientes`):
- CRUD completo (lista, novo, editar, desativar).
- `GET /api/buscar?q=<termo>` — retorna JSON `[{id, nome, telefone}]` para autocomplete (mínimo 3 chars, máximo 10 resultados).

Template do formulário de novo agendamento usa este endpoint com `fetch()` para autocomplete em tempo real.  
`@requer_perfil('admin', 'recepcao')` para CRUD; endpoint de busca: `@requer_login`.

**Aceite:** autocomplete retorna resultados ao digitar 3+ caracteres; CPF duplicado exibe link para cadastro existente.

---

### T21 — Blueprint: Agenda (CRUD + endpoint JSON)
**Camada:** [IF] + [FE]  
**Horas:** 5h  
**Dependências:** T10, T11, T12, T13, T17, T20

`app/interfaces/agenda/routes.py` (blueprint `agenda`, prefix `/agenda`):

- `GET /` — página principal com FullCalendar.
- `GET /api/eventos?start=&end=&profissional_id=` — retorna JSON de eventos no formato FullCalendar (UC-08). Profissional com `perfil='profissional'` vê apenas os próprios (CB-08).
- `GET/POST /novo` — formulário de criação de agendamento. POST chama `CriarAgendamento.executar()`. Em caso de `ConflitodeHorarioError`, retorna `409` com mensagem detalhada.
- `GET/POST /editar/<id>` — chama `EditarAgendamento.executar()`.
- `POST /cancelar/<id>` — chama `CancelarAgendamento.executar()`.
- `POST /status/<id>` — altera status (`confirmado`, `em_atendimento`, `concluido`, `falta`).

**Aceite:** grid FullCalendar carrega eventos; criar agendamento conflitante exibe mensagem de erro sem 500; CB-02 (ultrapassa expediente) bloqueado com mensagem.

---

### T22 — Grid FullCalendar com lógica de cores
**Camada:** [FE]  
**Horas:** 4h  
**Dependências:** T21

`app/static/js/agenda.js`:
- Inicializa FullCalendar com views `dayGridMonth`, `timeGridWeek`, `timeGridDay`.
- `eventSources` aponta para `/agenda/api/eventos`.
- Callback `eventDidMount`: aplica cor do evento via `procedimento.cor_hex`.
- `businessHours` por profissional (dinâmico, lido de endpoint `GET /api/agenda/expedientes`).
- Slots fora do expediente: FullCalendar `businessHours` + `slotLabelClassNames` para cinza visual.
- Filtro de profissional: `<select>` dispara nova requisição ao endpoint com `profissional_id`.

Adicionar endpoint auxiliar `GET /api/agenda/expedientes` que retorna array de `businessHours` por profissional para o FullCalendar.

**Aceite:** slots fora do expediente aparecem cinza; eventos coloridos por procedimento; filtro de profissional funciona sem reload de página.

---

## SPRINT 4 — Fase 2: Autoagendamento Público

**Objetivo:** link público funcional onde paciente agenda sem login administrativo.  
**Critério de aceite do sprint:** paciente completa agendamento via link público e aparece no grid interno.

---

### T23 — Use Case: ListarSlotsDisponiveis
**Camada:** [A]  
**Horas:** 3h  
**Dependências:** T09, T13

`app/application/listar_slots_disponiveis.py`:
- Dado `profissional_id`, `procedimento_id`, `data`:
  1. Gera slots de `horario_inicio` até `horario_fim` com intervalos de `procedimento.duracao_minutos`.
  2. Para cada slot, chama `VerificarConflito` (sem lançar exceção — apenas boolean).
  3. Retorna apenas slots livres.
- Exclui datas cujo dia da semana não esteja em `profissional.dias_semana`.

**Aceite:** `pytest tests/application/test_listar_slots_disponiveis.py` — dia fora do expediente retorna lista vazia; slots ocupados são excluídos; CB-06 (profissionais diferentes podem ter mesmo slot).

---

### T24 — Use Case: AutoagendarPaciente
**Camada:** [A]  
**Horas:** 2h  
**Dependências:** T10, T16

`app/application/autoagendar_paciente.py`:
- Recebe `profissional_id, procedimento_id, data_hora_inicio, nome, telefone, email`.
- Busca paciente por telefone → se não existe, cria com dados mínimos.
- Chama `CriarAgendamento.executar(origem='autoagendamento')`.
- Em caso de race condition (`ConflitodeHorarioError`), propaga a exceção para a rota tratar.

**Aceite:** `pytest tests/application/test_autoagendar_paciente.py` — paciente novo criado automaticamente; paciente existente vinculado; race condition lança exceção.

---

### T25 — Blueprint público `/agendar`
**Camada:** [IF] + [FE]  
**Horas:** 5h  
**Dependências:** T23, T24

`app/interfaces/publico/routes.py` (blueprint `publico`, prefix `/agendar`, **sem** `@requer_login`):

**Fluxo multi-step (sem JS obrigatório — formulários POST simples):**

- `GET /agendar` — Step 1: escolha de profissional (cards com nome, cor, especialidade).
- `GET /agendar/procedimento?profissional_id=X` — Step 2: escolha de procedimento.
- `GET /agendar/data?profissional_id=X&procedimento_id=Y` — Step 3: escolha de data (picker) + exibe slots disponíveis.
- `GET /agendar/confirmar?...&slot=HH:MM` — Step 4: formulário de dados pessoais (nome, telefone, e-mail).
- `POST /agendar/finalizar` — chama `AutoagendarPaciente.executar()`. Em caso de race condition, redireciona para Step 3 com mensagem `"Horário acabou de ser reservado"`. Em sucesso, redireciona para `/agendar/sucesso/<agendamento_id>`.
- `GET /agendar/sucesso/<id>` — tela de confirmação com data, hora, profissional e botão "Adicionar ao Google Calendar".

Templates em `app/templates/publico/` com layout próprio (sem navbar administrativa).

**Aceite:** fluxo completo sem login; agendamento aparece no grid interno com `origem=autoagendamento`; race condition não gera 500.

---

## SPRINT 5 — Fase 3: Lembretes Automáticos

**Objetivo:** lembretes de agendamento enviados automaticamente via WhatsApp e e-mail.  
**Critério de aceite do sprint:** lembrete configurado para 24h antes é enviado no horário correto e logado em `lembretes_enviados`.

---

### T26 — CRUD de configuração de lembretes
**Camada:** [IF] + [I]  
**Horas:** 2h  
**Dependências:** T03

`app/interfaces/configuracoes/routes.py` (blueprint `configuracoes`, prefix `/configuracoes`):
- `GET/POST /lembretes` — lista e cria regras de lembrete (antecedência em horas, tipo, ativo/inativo).
- `POST /lembretes/remover/<id>` — remove regra.

`SqliteConfiguracaoLembreteRepository` em `/infrastructure`.  
`@requer_perfil('admin')`.

**Aceite:** admin cria regra "24h, WhatsApp"; regra aparece na lista; desativar/remover funciona.

---

### T27 — Adaptador WhatsApp (Evolution API)
**Camada:** [I]  
**Horas:** 3h  
**Dependências:** T01

`app/infrastructure/notifications/whatsapp_adapter.py`:
- Interface `NotificacaoAdapter` em `/domain/repositories/notificacao_adapter.py` com método `enviar(telefone, mensagem) -> bool`.
- `EvolutionWhatsappAdapter` implementa a interface via `urllib.request` (sem requests lib, manter deps mínimas).
- Configuração via `.env`: `WHATSAPP_API_URL`, `WHATSAPP_API_KEY`, `WHATSAPP_INSTANCE`.

**Aceite:** mock de API retorna `200` → `enviar()` retorna `True`; mock retorna `500` → retorna `False` e não lança exceção.

---

### T28 — Adaptador e-mail (SMTP)
**Camada:** [I]  
**Horas:** 2h  
**Dependências:** T01

`app/infrastructure/notifications/email_adapter.py`:
- Usa `smtplib` e `email.mime` (biblioteca padrão Python).
- Configuração via `.env`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM`.

**Aceite:** mock SMTP aceita conexão → e-mail enviado; SMTP indisponível → retorna `False` sem lançar exceção.

---

### T29 — Use Case: EnviarLembretes
**Camada:** [A]  
**Horas:** 3h  
**Dependências:** T17, T26, T27, T28

`app/application/enviar_lembretes.py`:
- Busca agendamentos cujo `data_hora_inicio` está em N horas a partir de agora (para cada regra ativa).
- Filtra agendamentos cujo lembrete desta antecedência ainda não foi enviado (`lembretes_enviados`).
- Filtra `status NOT IN ('cancelado', 'falta')`.
- Chama adaptador (WhatsApp ou e-mail); em falha, registra com `status='erro'` e agenda retry.
- Lógica de retry: até 3 tentativas com 15 min de intervalo; implementada via `tentativas` no registro de `lembretes_enviados`.

Template de mensagem WhatsApp:  
`"Olá [Nome]! Lembrete: você tem [Procedimento] com [Profissional] amanhã às [HH:MM]. Confirme: [link/resposta]."`

**Aceite:** `pytest tests/application/test_enviar_lembretes.py` — lembrete enviado registrado como `enviado`; falha registrada como `erro`; agendamento cancelado ignorado (CB-07).

---

### T30 — Job Scheduler (APScheduler)
**Camada:** [I]  
**Horas:** 2h  
**Dependências:** T29

Adicionar `APScheduler` ao `requirements.txt`.  
`app/infrastructure/scheduler.py`:
- Job rodando a cada 15 minutos: chama `EnviarLembretes.executar()`.
- Scheduler iniciado em `run.py` junto com a app Flask (modo background thread).

**Aceite:** após iniciar a app, logs mostram job executando a cada 15 min; lembrete de teste é enviado no horário configurado.

---

## SPRINT 6 — DevOps e Qualidade

**Objetivo:** projeto rodável via Docker, CI/CD configurado, testes completos.

---

### T31 — Suite de testes completa
**Camada:** [TEST]  
**Horas:** 4h  
**Dependências:** todos os sprints anteriores

`pytest.ini` com `testpaths = tests`.  
`conftest.py` com fixture de banco em memória (`:memory:`) para testes de infraestrutura.

Cobertura mínima obrigatória:
- `tests/domain/` — entidades e regras puras (sem banco).
- `tests/application/` — todos os use cases com mocks de repositório.
- `tests/infrastructure/` — repositórios sqlite3 com banco `:memory:`.
- `tests/interfaces/` — rotas Flask com `app.test_client()`.

Casos de borda obrigatórios nos testes: CB-01 a CB-08 (conforme SPEC.md seção 4).

**Aceite:** `pytest --tb=short` passa 100%; `pytest --co -q` lista ≥ 40 testes.

---

### T32 — Dockerfile e docker-compose
**Camada:** [OPS]  
**Horas:** 2h  
**Dependências:** T01

`Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py"]
```

`docker-compose.yml`:
- Serviço `web` com volume para persistir `data/odonto.db`.
- Variáveis de ambiente via `.env`.

**Aceite:** `docker-compose up` sobe a aplicação sem erros; banco persiste entre restarts.

---

### T33 — GitHub Actions CI/CD
**Camada:** [OPS]  
**Horas:** 2h  
**Dependências:** T31, T32

`.github/workflows/ci.yml`:
- Trigger: push e pull_request para `main`.
- Jobs: `lint` (flake8) → `test` (pytest) → `build` (docker build).
- Falha em qualquer job bloqueia o merge.

`.github/workflows/backup.yml`:
- Trigger: cron `0 3 * * *` (3h da manhã).
- Copia `data/odonto.db` para artifact do workflow (retido por 30 dias).

**Aceite:** push para main dispara pipeline; falha de teste bloqueia; artefato de backup visível nas Actions.

---

## Ordem de Execução Recomendada (Squad Beta)

```
Sprint 0: T01 → T02 → T03 → T04 → T05
Sprint 1: T06 → T07 → T08 → T09 → T10 → T11 → T12 → T13
Sprint 2: T14 → T15 → T16 → T17  (paralelo entre si após T08)
Sprint 3: T18 → T19 → T20 → T21 → T22  (T18/T19/T20 paralelos após Sprint 2)
Sprint 4: T23 → T24 → T25
Sprint 5: T26 → T27 → T28 → T29 → T30  (T27/T28 paralelos)
Sprint 6: T31 → T32 → T33
```

---

## Resumo de Estimativas

| Sprint | Tarefas | Horas |
|---|---|---|
| Sprint 0 — Fundação | T01–T05 | 9h |
| Sprint 1 — Domínio & Use Cases | T06–T13 | 12.5h |
| Sprint 2 — Repositórios sqlite3 | T14–T17 | 8.5h |
| Sprint 3 — Interfaces & Grid | T18–T22 | 17h |
| Sprint 4 — Autoagendamento Público | T23–T25 | 10h |
| Sprint 5 — Lembretes Automáticos | T26–T30 | 12h |
| Sprint 6 — DevOps & Testes | T31–T33 | 8h |
| **Total** | **33 tarefas** | **~77h** |

---

## Pontos de Atenção (Squad Beta deve revisar antes de implementar)

1. **Race condition no autoagendamento (T25):** a janela entre o paciente ver o slot livre e confirmar pode resultar em conflito. A rota `POST /agendar/finalizar` deve tratar `ConflitodeHorarioError` com redirect, não 500.
2. **sqlite3 e concorrência (T03):** configurar `check_same_thread=False` com cuidado; usar `with conn:` para transações atômicas no autoagendamento.
3. **FullCalendar businessHours dinâmicos (T22):** cada profissional tem seu próprio expediente — o endpoint `GET /api/agenda/expedientes` deve retornar o formato exato esperado pelo FullCalendar para o `resourceTimeGridDay` view.
4. **APScheduler em produção (T30):** usar `BackgroundScheduler` com `daemon=True`; garantir que não inicia duplicado em workers múltiplos (configurar `max_instances=1`).
