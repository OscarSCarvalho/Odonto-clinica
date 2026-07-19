# OdontoClinica — Sistema de Gestão de Agenda

Sistema web de agendamento para clínicas odontológicas e estéticas. Permite que administradores, recepcionistas e profissionais gerenciem consultas por uma agenda visual, enquanto pacientes realizam o próprio agendamento via link público sem precisar de login.

---

## Funcionalidades

### Agenda e Atendimento
- **Dashboard** com KPIs do dia: agendamentos, faturamento previsto/realizado, faltas, retornos pendentes, orçamentos pendentes e valor aprovado no mês
- **Agenda visual** com FullCalendar (visualizações dia / semana / mês), cores por procedimento e destaque do expediente de cada profissional
- **Prevenção automática de conflito de horário** por profissional, com mensagem detalhada em caso de sobreposição
- **Check-in de chegada** — status `aguardando` para marcar o paciente como presente na clínica antes do atendimento
- **Retorno automático sugerido** — ao concluir um atendimento de procedimento com retorno configurado, o sistema sugere a próxima data com um clique para agendar
- **Pacientes recorrentes** — planos de manutenção periódica com painel de acompanhamento e agendamento assistido
- **Fila de retornos pendentes** — painel dedicado para acompanhar pacientes que precisam ser contatados para retorno
- **Anexos do paciente** — upload, download e exclusão de fotos e exames (JPG/PNG/PDF)
- **CRUD completo** de profissionais, procedimentos e pacientes
- **Autoagendamento público** em 4 passos via link sem login

### Orçamentos
- **Criação de orçamentos** antes do agendamento, vinculados a paciente e profissional
- **Seleção de procedimentos por checkboxes** — cards interativos com nome e preço base de cada procedimento
- **Cálculo automático** de total bruto, desconto por item, desconto global e total líquido
- **Envio ao paciente** via WhatsApp (Evolution API) e e-mail com link público de aprovação
- **Aprovação online pelo paciente** via token único sem necessidade de login
- **Conversão direta** de orçamento aprovado em agendamentos com um clique
- **Ciclo de vida completo**: rascunho → enviado → aprovado / recusado / expirado

### Financeiro
- **Contas a receber** — painel unificado de pagamentos pendentes (atendimentos e mensalidades)
- **Registro de pagamento** via modal limpo com seleção visual da forma (Dinheiro / Pix / Débito / Crédito)
- **Mensalidades** — planos de cobrança periódica por paciente com geração automática de cobranças
- **KPIs financeiros**: total a receber, total em atraso e quantidade de cobranças atrasadas com contagem de dias

### Notificações e Automações
- **Lembretes automáticos** por WhatsApp (Evolution API) e e-mail (SMTP), configuráveis em antecedência e canal
- **Envio de orçamentos** por WhatsApp e e-mail com link de aprovação gerado automaticamente

### Relatórios
- **Relatório de faltas e cancelamentos** — por período, profissional e paciente
- **Relatório de pacientes** — perfil de atendimentos, frequência e histórico
- **Relatório de desempenho** — comparativo por profissional e procedimento

### Qualidade e Infraestrutura
- **288 testes automatizados** cobrindo domínio, casos de uso, repositórios e rotas
- **Pre-commit hook** que roda flake8 automaticamente antes de cada commit, impedindo que erros de lint cheguem ao CI
- **Docker** para execução em qualquer ambiente
- **CI/CD** com GitHub Actions (lint → testes → build Docker) e backup diário automático do banco

---

## Stack tecnológica

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11 + Flask 3.1 |
| Banco de dados | SQLite 3 (SQL puro, sem ORM) |
| Autenticação | Sessão Flask (cookie `HttpOnly`) |
| Frontend | Jinja2 + HTML5 + CSS3 + JavaScript vanilla |
| Calendário | FullCalendar.js 6.1 (MIT) |
| Notificações | Evolution API (WhatsApp) + `smtplib` (e-mail) |
| Agendamento de jobs | APScheduler 3.10 |
| Testes | pytest 8 + pytest-flask |
| Qualidade de código | flake8 + pre-commit hook |
| Infra | Docker + docker-compose + GitHub Actions |

---

## Arquitetura

O projeto segue **Clean Architecture** com 4 camadas. As dependências apontam sempre para dentro — a camada de domínio não conhece nenhuma outra.

```
interfaces/   →   application/   →   domain/
                                        ↑
                  infrastructure/  ────┘
```

```
app/
├── domain/              # Entidades, interfaces de repositório, exceções de negócio
├── application/         # Casos de uso (sem dependência de framework ou banco)
├── infrastructure/      # Repositórios SQLite, adaptadores WhatsApp/e-mail, scheduler
└── interfaces/          # Blueprints Flask, rotas HTTP, templates Jinja2
```

---

## Pré-requisitos

- Python 3.11+
- pip
- Git
- (Opcional) Docker e docker-compose para execução containerizada

---

## Instalação e execução local

### 1. Clone o repositório

```bash
git clone https://github.com/OscarSCarvalho/Odonto-clinica.git
cd Odonto-clinica
```

### 2. Crie e ative o ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Instale o pre-commit hook (recomendado)

```bash
bash scripts/install_hooks.sh
```

A partir disso, o lint roda automaticamente antes de cada `git commit`.

### 5. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com seus valores (veja a seção [Variáveis de ambiente](#variáveis-de-ambiente)).

### 6. Inicie o servidor

```bash
python run.py
```

Acesse **http://localhost:5000**. O banco SQLite é criado automaticamente em `data/odonto.db` na primeira execução, já com dados seed.

---

## Execução com Docker

```bash
# Subir a aplicação
docker-compose up -d

# Parar
docker-compose down
```

O banco persiste no volume Docker `odonto_data`. Para inspecioná-lo:

```bash
docker-compose exec web sqlite3 data/odonto.db ".tables"
```

---

## Acesso inicial (dados seed)

Na primeira execução, o banco é populado com:

| Campo | Valor |
|---|---|
| E-mail | `admin@clinica.com` |
| Senha | `admin123` |
| Perfil | Administrador |

Também são criados: **1 profissional** (Dr. Carlos Silva — Ortodontia) e **2 procedimentos** (Consulta R$ 150 / Limpeza R$ 200) para demonstração.

> Altere a senha do admin assim que implantar em produção.

---

## Como usar

### Login

Acesse `http://localhost:5000/login`. A tela exibe o painel com o nome do sistema à esquerda e o formulário de acesso à direita. Após autenticar, o sistema redireciona para o **Dashboard**.

---

### Navegação (Sidebar)

O menu lateral esquerdo agrupa todas as funcionalidades por categoria:

| Seção | Itens |
|---|---|
| Principal | Dashboard, Agenda |
| Atendimento | Pacientes, Orçamentos, Recorrentes, Retornos |
| Financeiro | Contas a Receber |
| Relatórios | Relatórios |
| Administração | Profissionais, Procedimentos, Configurações *(apenas admin)* |

---

### Dashboard

Rota: `/dashboard`  
Perfis: admin, recepção, profissional

Painel do dia com:
- **Agendamentos hoje**, **faturamento previsto**, **faturamento realizado** e **faltas hoje**
- **Orçamentos pendentes** (rascunho + enviado) e **valor aprovado no mês**
- **Próximos atendimentos** do dia (até 5, ordenados por horário)
- **Aniversariantes de hoje**
- **Recorrentes vencendo em 7 dias**

---

### Agenda

Rota: `/agenda`  
Perfis: admin, recepção, profissional

- **Grid semanal** é a visualização padrão. Use os botões **Mês / Semana / Dia** para alternar.
- **Filtro de profissional** filtra eventos sem recarregar a página.
- Slots fora do expediente do profissional aparecem em cinza.
- Clique em um evento para ver detalhes (editar / alterar status / cancelar).

#### Status dos agendamentos

```
agendado → confirmado → aguardando → em_atendimento → concluido
agendado/confirmado/aguardando → cancelado
agendado/confirmado/aguardando → falta
```

`aguardando` representa o **check-in de chegada** — marque o paciente como presente assim que ele chegar à recepção.

#### Retorno automático sugerido

Se o procedimento tiver **retorno sugerido** configurado, ao marcar o agendamento como **Concluído** o sistema exibe a data sugerida com botão **Agendar retorno** já pré-preenchido.

---

### Orçamentos

Rota: `/orcamentos`  
Perfis: admin, recepção

#### Criar um orçamento

1. Acesse **Orçamentos → Novo Orçamento**
2. Selecione o paciente, o profissional (opcional), validade e observações
3. Na tela de detalhe, marque os **procedimentos desejados nos cards de seleção** — cada card exibe nome e preço base; ao marcar, aparece o campo de quantidade
4. Clique em **Adicionar Selecionados**
5. Ajuste desconto global se necessário

> Procedimentos sem preço cadastrado aparecem desativados com badge "⚠ Sem preço". Configure o preço em **Procedimentos** antes de usar no orçamento.

#### Ciclo de vida

| Status | Descrição |
|---|---|
| Rascunho | Em edição — itens podem ser adicionados/removidos |
| Enviado | Enviado ao paciente via WhatsApp/e-mail com link de aprovação |
| Aprovado | Paciente aceitou — pode ser convertido em agendamentos |
| Recusado | Paciente recusou |
| Expirado | Prazo de validade ultrapassado |

#### Enviar ao paciente

Clique em **Enviar ao Paciente**. O sistema gera um link único com token e envia:
- **WhatsApp** (se o paciente tiver telefone cadastrado)
- **E-mail** (se o paciente tiver e-mail cadastrado)

O paciente acessa o link, vê o resumo do orçamento e clica em **Aprovar** ou **Recusar** — sem precisar de login.

#### Converter em agendamentos

Com o orçamento **Aprovado**, clique em **Converter em Agendamentos**. Para cada procedimento do orçamento, selecione profissional, data e horário. O sistema cria os agendamentos e um pagamento vinculado com o valor total líquido.

---

### Financeiro — Contas a Receber

Rota: `/financeiro`  
Perfis: admin, recepção

Painel unificado de cobranças pendentes (atendimentos concluídos e mensalidades).

- **KPIs**: total a receber, valor em atraso e quantidade de cobranças atrasadas
- **Badge de atraso** com contagem de dias
- **Data formatada** em DD/MM/AAAA

#### Registrar recebimento

Clique em **💳 Receber** na linha do pagamento. Um modal centralizado exibe:
- Resumo do paciente, origem e valor
- **Forma de pagamento** em cards visuais: Dinheiro / Pix / Débito / Crédito
- **Data do recebimento** (padrão: hoje)
- Campo de **observação** opcional

Confirme com **✔ Confirmar Recebimento**. O modal fecha com `Esc` ou clique fora.

---

### Profissionais

Rota: `/profissionais`  
Perfil: apenas admin

Cada profissional possui nome, especialidade, cor (calendário), expediente e dias de trabalho.

---

### Procedimentos

Rota: `/procedimentos`  
Perfil: apenas admin

Cada procedimento possui nome, duração em minutos, cor (calendário), **preço base** e retorno sugerido em dias.

> O preço base é utilizado automaticamente ao adicionar o procedimento a um orçamento. Procedimentos sem preço não podem ser adicionados a orçamentos.

---

### Pacientes

Rota: `/pacientes`  
Perfis: admin, recepção

- Busca por nome (mínimo 3 caracteres)
- Cadastro com nome, telefone, e-mail, CPF e data de nascimento
- CPF único com link para o cadastro existente em caso de duplicata
- **Anexos**: fotos e exames (JPG/PNG/PDF até 8MB)
- **Planos recorrentes**: manutenção periódica (ex: aparelho a cada 30 dias)
- **Mensalidades**: planos de cobrança fixa com geração automática de cobranças
- **Histórico de pagamentos** na ficha do paciente

---

### Autoagendamento público

Rota: `/agendar`  
Perfil: público (sem login)

| Passo | O que acontece |
|---|---|
| 1 — Profissional | Paciente escolhe com quem quer ser atendido |
| 2 — Procedimento | Escolhe o tipo de atendimento |
| 3 — Data & Horário | Escolhe a data; o sistema exibe apenas slots livres dentro do expediente |
| 4 — Confirmação | Preenche nome e telefone; sistema identifica ou cria o cadastro automaticamente |

Após a confirmação, o paciente recebe um protocolo e pode adicionar ao Google Agenda.

> Race condition tratada: se o slot for ocupado entre a seleção e a confirmação, novos horários são exibidos automaticamente.

---

### Lembretes automáticos

Rota: `/configuracoes/lembretes`  
Perfil: apenas admin

Configure antecedência em horas (ex: `24` para 1 dia antes) e canal (WhatsApp ou e-mail). O scheduler roda a cada **15 minutos**, com até **3 tentativas** em caso de falha.

---

### Relatórios

Rota: `/relatorios`  
Perfis: admin, recepção

| Relatório | Descrição |
|---|---|
| Faltas e cancelamentos | Por período, profissional e paciente — taxa de ausência |
| Pacientes | Perfil de atendimentos, frequência e histórico |
| Desempenho | Comparativo por profissional e procedimento |

---

### Pacientes Recorrentes

Rota: `/recorrentes`  
Perfis: admin, recepção

Painel de todos os planos de recorrência ativos com filtro por janela de vencimento (7 / 14 / 30 / 90 dias). Botão **Agendar** abre a tela de novo agendamento pré-preenchida.

> O sistema nunca cria agendamentos sozinho — a recepção confirma o horário real. Ao concluir o agendamento, o plano avança automaticamente para a próxima data.

---

### Retornos

Rota: `/retornos`  
Perfis: admin, recepção

Fila de pacientes que precisam ser contatados para agendar o retorno após um atendimento concluído. Marque como **Contatado** após o contato.

---

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```env
# Obrigatório
FLASK_SECRET_KEY=chave-secreta-longa-e-aleatoria
FLASK_ENV=production           # ou development
DB_PATH=./data/odonto.db

# WhatsApp via Evolution API (opcional — Lembretes e Orçamentos)
WHATSAPP_API_URL=https://sua-instancia.evolution-api.com
WHATSAPP_API_KEY=sua-chave-api
WHATSAPP_INSTANCE=nome-da-instancia

# E-mail via SMTP (opcional — Lembretes e Orçamentos)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=clinica@gmail.com
SMTP_PASS=senha-de-app
EMAIL_FROM=Clinica <clinica@gmail.com>
```

> Em produção, gere `FLASK_SECRET_KEY` com `python -c "import secrets; print(secrets.token_hex(32))"`.

---

## Banco de dados

O banco SQLite é criado automaticamente em `data/odonto.db`. Tabelas principais:

```
usuarios
  └── perfil: admin | recepcao | profissional

profissionais
  ├── cor_hex, horario_inicio, horario_fim
  └── dias_semana (CSV: 0=dom … 6=sab)

procedimentos
  └── duracao_minutos, cor_hex, preco_base, retorno_dias

pacientes
  └── cpf (único)

planos_recorrentes
  └── paciente_id, profissional_id, procedimento_id
      intervalo_dias, proxima_data, ativo

agendamentos
  ├── profissional_id, paciente_id, procedimento_id
  ├── plano_recorrente_id (opcional)
  ├── status: agendado | confirmado | aguardando | em_atendimento
  │           | concluido | cancelado | falta
  └── origem: interno | autoagendamento

orcamentos
  ├── paciente_id, profissional_id
  ├── status: rascunho | enviado | aprovado | recusado | expirado
  ├── desconto_global, desconto_tipo: percentual | valor
  ├── validade_dias, token_aprovacao (UUID, para link público)
  └── orcamento_itens → procedimento_id, quantidade,
                        valor_unitario, desconto_item

mensalidades
  └── paciente_id, valor, dia_vencimento

pagamentos
  ├── paciente_id
  ├── agendamento_id (opcional)
  ├── mensalidade_id (opcional)
  ├── forma_pagamento: dinheiro | pix | cartao_debito | cartao_credito
  └── status: pendente | pago

lembretes_enviados, config_lembretes, paciente_anexos, tarefas_retorno
```

Para inspecionar o banco diretamente:

```bash
sqlite3 data/odonto.db
.tables
SELECT * FROM orcamentos;
.quit
```

---

## Testes

```bash
# Rodar todos os testes
pytest

# Com relatório resumido
pytest --tb=short -q

# Apenas uma camada
pytest tests/domain/
pytest tests/application/
pytest tests/infrastructure/
pytest tests/interfaces/
```

Os testes de `domain/` e `application/` rodam **sem nenhum banco ativo**. Os testes de `infrastructure/` usam banco em memória (`:memory:`).

**Cobertura atual: 288 testes passando.**

---

## Pre-commit hook

O repositório inclui um hook que roda **flake8** automaticamente antes de cada `git commit`. Se houver erros de lint, o commit é bloqueado com mensagem clara.

```bash
# Instalar (uma vez por clone)
bash scripts/install_hooks.sh
```

O hook usa as mesmas regras do CI: `--max-line-length=120 --exclude=__pycache__`.

---

## CI/CD (GitHub Actions)

### `ci.yml` — Integração contínua

Disparado em todo `push` e `pull_request` para `main`:

```
lint (flake8) → test (pytest) → build (docker build)
```

### `backup.yml` — Backup automático

Executado todo dia às **3h** ou manualmente via `workflow_dispatch`. Copia `odonto.db` via SSH e salva como artefato com retenção de **30 dias**.

Secrets necessários:

| Secret | Descrição |
|---|---|
| `DEPLOY_HOST` | IP ou hostname do servidor |
| `DEPLOY_USER` | Usuário SSH |
| `DEPLOY_SSH_KEY` | Chave privada SSH (formato PEM) |
| `DEPLOY_DB_PATH` | Caminho do arquivo `.db` no servidor |

---

## Controle de acesso por perfil

| Rota | admin | recepção | profissional | público |
|---|:---:|:---:|:---:|:---:|
| `/dashboard` | ✅ | ✅ | ✅ | ❌ |
| `/agenda` (visualizar) | ✅ | ✅ | ✅ | ❌ |
| `/agenda/novo` e `/editar` | ✅ | ✅ | ❌ | ❌ |
| `/pacientes/*` | ✅ | ✅ | ❌ | ❌ |
| `/orcamentos/*` | ✅ | ✅ | ❌ | ❌ |
| `/orcamento/<token>` (aprovação) | ✅ | ✅ | ✅ | ✅ |
| `/financeiro/*` | ✅ | ✅ | ❌ | ❌ |
| `/recorrentes` | ✅ | ✅ | ❌ | ❌ |
| `/retornos` | ✅ | ✅ | ❌ | ❌ |
| `/relatorios/*` | ✅ | ✅ | ❌ | ❌ |
| `/profissionais/*` | ✅ | ❌ | ❌ | ❌ |
| `/procedimentos/*` | ✅ | ❌ | ❌ | ❌ |
| `/configuracoes/*` | ✅ | ❌ | ❌ | ❌ |
| `/agendar` (autoagendamento) | ✅ | ✅ | ✅ | ✅ |

---

## Estrutura de arquivos

```
.
├── app/
│   ├── domain/
│   │   ├── entities/          # Agendamento, Paciente, Procedimento, Profissional,
│   │   │                      # Orcamento, OrcamentoItem, Pagamento, Lembrete …
│   │   ├── repositories/      # Interfaces (ABCs)
│   │   └── exceptions.py
│   ├── application/           # Casos de uso
│   │   ├── criar_agendamento.py
│   │   ├── criar_orcamento.py
│   │   ├── adicionar_item_orcamento.py
│   │   ├── enviar_orcamento.py
│   │   ├── aprovar_orcamento.py
│   │   ├── converter_orcamento.py
│   │   ├── criar_pagamento_atendimento.py
│   │   ├── gerar_cobrancas_mensalidades.py
│   │   ├── listar_contas_receber.py
│   │   ├── obter_dashboard.py
│   │   └── ...
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── schema.sql
│   │   │   ├── connection.py
│   │   │   └── repositories/  # SqliteXxxRepository para cada entidade
│   │   ├── notifications/     # WhatsAppAdapter, EmailAdapter
│   │   ├── scheduler.py
│   │   └── container.py       # Injeção de dependência
│   ├── interfaces/
│   │   ├── agenda/
│   │   ├── auth/
│   │   ├── configuracoes/
│   │   ├── dashboard/
│   │   ├── financeiro/        # Contas a receber, pagamentos, mensalidades
│   │   ├── orcamentos/        # Orçamentos — ciclo completo
│   │   ├── pacientes/
│   │   ├── procedimentos/
│   │   ├── profissionais/
│   │   ├── publico/           # Autoagendamento + aprovação de orçamento (sem login)
│   │   ├── recorrentes/
│   │   ├── relatorios/
│   │   └── retornos/
│   ├── static/                # CSS (main.css) e JS
│   └── templates/             # HTML Jinja2 por módulo
├── scripts/
│   ├── pre-commit             # Hook de lint (rastreado no git)
│   └── install_hooks.sh       # Instala o hook após clonar
├── tests/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interfaces/
├── .github/workflows/
│   ├── ci.yml
│   └── backup.yml
├── .env.example
├── config.py
├── run.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── CONTEXT.md
├── SPEC.md
└── PLAN.md
```

---

## Licença

Propriedade de **OdontoClinica**. Desenvolvido por [ATHOS](https://github.com/OscarSCarvalho) — todos os direitos reservados.
