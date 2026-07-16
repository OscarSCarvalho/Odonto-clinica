# OdontoClinica — Sistema de Gestão de Agenda

Sistema web de agendamento para clínicas odontológicas e estéticas. Permite que administradores, recepcionistas e profissionais gerenciem consultas por uma agenda visual, enquanto pacientes realizam o próprio agendamento via link público sem precisar de login.

---

## Funcionalidades

- **Agenda visual** com FullCalendar (visualizações dia / semana / mês), cores por procedimento e destaque do expediente de cada profissional
- **Prevenção automática de conflito de horário** por profissional, com mensagem detalhada em caso de sobreposição
- **CRUD completo** de profissionais, procedimentos e pacientes
- **Autoagendamento público** em 4 passos via link sem login — o paciente escolhe profissional, procedimento, data e horário
- **Lembretes automáticos** por WhatsApp (Evolution API) e e-mail (SMTP), configuráveis em antecedência e canal
- **Controle de acesso por perfil** (admin / recepção / profissional)
- **132 testes automatizados** cobrindo domínio, casos de uso, repositórios e rotas
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
| Calendário | FullCalendar.js 5.11 (MIT) |
| Notificações | Evolution API (WhatsApp) + `smtplib` (e-mail) |
| Agendamento de jobs | APScheduler 3.10 |
| Testes | pytest 8 + pytest-flask |
| Qualidade de código | flake8 |
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

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com seus valores (veja a seção [Variáveis de ambiente](#variáveis-de-ambiente)).

### 5. Inicie o servidor

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

Também são criados: **1 profissional** (Dr. Carlos Silva — Ortodontia) e **3 procedimentos** (Canal, Consulta, Limpeza) para demonstração.

> Altere a senha do admin assim que implantar em produção.

---

## Como usar

### Login

Acesse `http://localhost:5000`, insira e-mail e senha e clique em **Entrar**. O sistema redireciona para a agenda automaticamente.

---

### Agenda

Rota: `/agenda`  
Perfis: admin, recepção, profissional

- **Grid semanal** é a visualização padrão. Use os botões **Mês / Semana / Dia** para alternar.
- **Hoje** volta para a data atual.
- **Setas `<` `>`** navegam entre períodos.
- **Filtro de profissional** filtra eventos sem recarregar a página.
- **Legenda de status** no topo indica as cores: Agendado, Confirmado, Em atendimento, Concluído, Cancelado, Falta.
- Slots fora do expediente do profissional aparecem em cinza.
- Clique em um evento para ver detalhes (editar / alterar status / cancelar).

#### Criar agendamento interno

1. Clique em **+ Novo Agendamento**
2. Selecione profissional e procedimento — o término é calculado automaticamente
3. Escolha a data e hora de início
4. Digite o nome do paciente (autocomplete a partir de 3 caracteres) ou clique em **+ Cadastrar novo paciente**
5. Clique em **Criar agendamento**

Em caso de conflito de horário, o sistema exibe uma mensagem descritiva com o agendamento que causa o conflito.

#### Status dos agendamentos

O fluxo de status permitido é:

```
agendado → confirmado → em_atendimento → concluido
agendado/confirmado → cancelado
agendado/confirmado/em_atendimento → falta
```

Para alterar o status, abra o evento no calendário ou acesse `/agenda/editar/<id>`.

---

### Profissionais

Rota: `/profissionais`  
Perfil: apenas admin

Cada profissional possui:
- **Nome** e **especialidade**
- **Cor** (hex `#RRGGBB`) — usada como cor da coluna no calendário
- **Expediente** — horário de início e fim
- **Dias de trabalho** — seleção dos dias da semana

> Ao desativar um profissional com agendamentos futuros, o sistema exibe um alerta com a contagem de agendamentos que serão afetados.

---

### Procedimentos

Rota: `/procedimentos`  
Perfil: apenas admin

Cada procedimento possui:
- **Nome**
- **Duração em minutos** (mínimo 5 min) — usada para calcular o término do agendamento automaticamente
- **Cor** (hex `#RRGGBB`) — usada como cor do evento no calendário
- **Preço base** (opcional)

---

### Pacientes

Rota: `/pacientes`  
Perfis: admin, recepção

- **Busca por nome** (mínimo 3 caracteres, máximo 10 resultados)
- **Cadastro** com nome, telefone, e-mail, CPF e data de nascimento
- CPF é único — tentativa de cadastrar CPF duplicado exibe link para o cadastro existente

---

### Autoagendamento público

Rota: `/agendar`  
Perfil: público (sem login)

Link para compartilhar com pacientes. O fluxo é dividido em 4 passos:

| Passo | O que acontece |
|---|---|
| 1 — Profissional | Paciente escolhe com quem quer ser atendido |
| 2 — Procedimento | Escolhe o tipo de atendimento (com duração e preço) |
| 3 — Data & Horário | Escolhe a data; o sistema exibe apenas slots livres dentro do expediente |
| 4 — Confirmação | Preenche nome e telefone; sistema identifica ou cria o cadastro automaticamente |

Após a confirmação, o paciente recebe um **protocolo** e pode adicionar o compromisso ao Google Agenda.

> Em caso de race condition (dois pacientes tentando o mesmo slot ao mesmo tempo), o sistema trata o erro e exibe novos horários disponíveis — sem erro 500.

---

### Lembretes automáticos

Rota: `/configuracoes/lembretes`  
Perfil: apenas admin

Configure regras de lembrete indicando:
- **Antecedência em horas** (ex: `24` para lembrar 1 dia antes, `2` para 2h antes)
- **Canal**: WhatsApp ou e-mail

O scheduler roda a cada **15 minutos** verificando agendamentos que precisam de lembrete. Em caso de falha no envio, o sistema tenta novamente até **3 vezes** com intervalo de 15 minutos, registrando o erro em log.

Para configurar os canais, preencha as variáveis de ambiente correspondentes (veja abaixo).

---

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```env
# Obrigatório
FLASK_SECRET_KEY=chave-secreta-longa-e-aleatoria
FLASK_ENV=production           # ou development
DB_PATH=./data/odonto.db

# WhatsApp via Evolution API (opcional — Lembretes)
WHATSAPP_API_URL=https://sua-instancia.evolution-api.com
WHATSAPP_API_KEY=sua-chave-api
WHATSAPP_INSTANCE=nome-da-instancia

# E-mail via SMTP (opcional — Lembretes)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=clinica@gmail.com
SMTP_PASS=senha-de-app
EMAIL_FROM=Clinica <clinica@gmail.com>
```

> Em produção, gere `FLASK_SECRET_KEY` com `python -c "import secrets; print(secrets.token_hex(32))"`.

---

## Banco de dados

O banco SQLite é criado automaticamente em `data/odonto.db`. Abaixo o diagrama simplificado das tabelas:

```
usuarios
  └── perfil: admin | recepcao | profissional

profissionais
  ├── cor_hex, horario_inicio, horario_fim
  └── dias_semana (CSV: 0=dom, 1=seg ... 6=sab)

procedimentos
  └── duracao_minutos, cor_hex, preco_base

pacientes
  └── cpf (único)

agendamentos
  ├── profissional_id → profissionais
  ├── paciente_id    → pacientes
  ├── procedimento_id → procedimentos
  ├── status: agendado | confirmado | em_atendimento | concluido | cancelado | falta
  └── origem: interno | autoagendamento

lembretes_enviados
  └── agendamento_id → agendamentos
      status: pendente | enviado | erro

config_lembretes
  └── antecedencia_h, tipo: whatsapp | email
```

Para inspecionar o banco diretamente:

```bash
sqlite3 data/odonto.db
.tables
SELECT * FROM agendamentos;
.quit
```

---

## Testes

```bash
# Rodar todos os testes
pytest

# Com relatório resumido
pytest --tb=short -q

# Listar todos os testes sem executar
pytest --co -q

# Apenas uma camada
pytest tests/domain/
pytest tests/application/
pytest tests/infrastructure/
pytest tests/interfaces/
```

Os testes de `domain/` e `application/` rodam **sem nenhum banco ativo** — confirmando o isolamento da Clean Architecture. Os testes de `infrastructure/` usam banco em memória (`:memory:`).

**Cobertura atual: 132 testes passando.**

---

## CI/CD (GitHub Actions)

O repositório inclui dois workflows em `.github/workflows/`:

### `ci.yml` — Integração contínua

Disparado em todo `push` e `pull_request` para `main`:

```
lint (flake8) → test (pytest) → build (docker build)
```

Qualquer falha bloqueia o merge.

### `backup.yml` — Backup automático

Executado todo dia às **3h da manhã** (ou manualmente via `workflow_dispatch`):

- Copia `odonto.db` do servidor de produção via SSH
- Salva como artefato do workflow com retenção de **30 dias**

Para ativar o backup, configure os seguintes **secrets** no repositório GitHub:

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
| `/agenda` (visualizar) | ✅ | ✅ | ✅ (próprios) | ❌ |
| `/agenda/novo` e `/editar` | ✅ | ✅ | ❌ | ❌ |
| `/profissionais/*` | ✅ | ❌ | ❌ | ❌ |
| `/procedimentos/*` | ✅ | ❌ | ❌ | ❌ |
| `/pacientes/*` | ✅ | ✅ | ❌ | ❌ |
| `/configuracoes/*` | ✅ | ❌ | ❌ | ❌ |
| `/agendar` | ✅ | ✅ | ✅ | ✅ |

---

## Estrutura de arquivos

```
.
├── app/
│   ├── domain/                    # Entidades, ports, exceções
│   │   ├── entities/
│   │   ├── repositories/          # Interfaces (ABCs)
│   │   └── exceptions.py
│   ├── application/               # Casos de uso
│   │   ├── criar_agendamento.py
│   │   ├── verificar_conflito.py
│   │   ├── listar_slots_disponiveis.py
│   │   ├── autoagendar_paciente.py
│   │   ├── enviar_lembretes.py
│   │   └── ...
│   ├── infrastructure/            # Implementações concretas
│   │   ├── db/
│   │   │   ├── schema.sql
│   │   │   ├── connection.py
│   │   │   └── repositories/      # SqliteXxxRepository
│   │   ├── notifications/         # WhatsApp + e-mail adapters
│   │   ├── scheduler.py
│   │   └── container.py           # Injeção de dependência
│   ├── interfaces/                # Blueprints Flask + templates
│   │   ├── agenda/
│   │   ├── auth/
│   │   ├── pacientes/
│   │   ├── profissionais/
│   │   ├── procedimentos/
│   │   ├── configuracoes/
│   │   └── publico/               # Autoagendamento sem login
│   ├── static/                    # CSS e JS
│   └── templates/                 # HTML Jinja2
├── tests/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interfaces/
├── migrations/                    # Scripts SQL versionados
├── data/                          # Banco SQLite (ignorado no git)
├── .github/workflows/
│   ├── ci.yml
│   └── backup.yml
├── .env.example
├── .gitignore
├── config.py
├── run.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── CONTEXT.md                     # Decisões de arquitetura e stack
├── SPEC.md                        # Especificação BDD completa
└── PLAN.md                        # 33 tarefas em 6 sprints
```

---

## Fora do escopo atual (roadmap)

- Multi-tenant / múltiplas unidades
- Módulo financeiro (lançamentos ao concluir agendamento)
- Prontuário eletrônico completo
- App mobile nativo
- Pagamento online no autoagendamento

---

## Licença

Propriedade de **OdontoClinica**. Desenvolvido por [ATHOS](https://github.com/OscarSCarvalho) — todos os direitos reservados.
