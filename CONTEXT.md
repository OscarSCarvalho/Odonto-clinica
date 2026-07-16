# CONTEXT.md — OdontoClinica / SistemaGestao

**Versão:** 1.0  
**Data:** 2026-07-15  
**Agente responsável:** Agent Software Architect (Squad Alpha)  
**Status:** Fase 0 concluída

---

## 1. Análise de Demanda

### Problema de Negócio
Clínicas odontológicas e estéticas dependem de agendas físicas ou planilhas para organizar consultas, gerando conflitos de horário, faltas não notificadas e falta de visibilidade da capacidade produtiva. A solução referência de mercado (Clinicorp) é robusta demais para clínicas menores — o produto a ser construído entrega o essencial com foco em usabilidade real.

### Público-Alvo
- **Administrador da clínica:** gerencia profissionais, procedimentos e agenda.
- **Recepcionista:** cria e altera agendamentos no dia a dia.
- **Paciente:** acessa link público para autoagendamento sem login.
- **Profissional (dentista/esteticista):** consulta própria agenda.

### Natureza Técnica da Demanda
- Aplicação web multi-usuário com interface de calendário visual.
- Escala: clínica pequena/média (1–20 profissionais, centenas a poucos milhares de agendamentos/mês).
- Requisito de link público de agendamento (face pública, sem autenticação).
- Notificações assíncronas (fase 3).
- Possibilidade futura de multi-tenant (plano Avançado), mas sem implementar agora.

---

## 2. Decisão de Stack

### Stack Definida
| Camada | Tecnologia |
|---|---|
| Backend / Framework | Python 3.11 + Flask |
| Banco de Dados | sqlite3 (módulo nativo do Python) |
| ORM / Query Builder | Nenhum — SQL puro via `sqlite3` |
| Autenticação | Flask session (cookie server-side) |
| Frontend | Jinja2 + HTML5 + CSS3 + JavaScript (vanilla) |
| Calendário Visual | FullCalendar.js (OSS, licença MIT) |
| Notificações (Fase 3) | Evolution API (WhatsApp) + SMTP nativo |
| CI/CD | GitHub Actions (build + deploy simples) |

### Justificativa da Stack

**Flask (e não NestJS/FastAPI):**  
O cliente já possui o projeto "Console de Chamados" em Flask com o mesmo padrão de autenticação por sessão. Reutilizar o mesmo framework elimina curva de aprendizado, permite compartilhamento de padrões de rota, middleware de auth e templates. FastAPI seria superior para API-first pura, mas o sistema tem interface web Jinja2 — Flask é mais natural nesse modelo.

**sqlite3 puro (e não PostgreSQL + Prisma ou SQLAlchemy):**  
A escala de uma clínica pequena/média não justifica a sobrecarga de um servidor de banco de dados separado nem de um ORM. sqlite3 tem zero configuração de infra, backups triviais (copiar arquivo), e SQL puro mantém controle total sobre queries de conflito de horário — crítico neste domínio. A restrição foi explicitamente solicitada pelo cliente e é técnica e arquiteturalmente sólida para o escopo.

**Sem JWT (sessão Flask):**  
JWT é adequado para APIs stateless consumidas por múltiplos clientes. Este sistema tem um único cliente web com Jinja2 — sessões server-side são mais simples, mais seguras contra XSS (cookie HttpOnly) e consistentes com o projeto de referência do cliente.

**FullCalendar.js (e não grid CSS manual):**  
Construir um grid de calendário visual com cores, drag-and-drop e suporte a visualizações dia/semana/mês do zero levaria semanas. FullCalendar entrega isso em horas, é mantido ativamente, tem suporte a eventos coloridos por recurso e integra via JSON — perfeito para o backend Flask retornar eventos via endpoint.

**Vanilla JS (e não React/Vue):**  
Consistente com a filosofia "sem complexidade enterprise". Sem etapa de build, sem node_modules, sem bundler. Jinja2 + pequenos scripts JS específicos por página mantêm o projeto navegável por qualquer dev Python.

---

## 3. Arquitetura — Clean Architecture Adaptada para Flask

### Princípio de Dependência
```
domain ← application ← infrastructure
                 ↑
            interfaces (rotas Flask)
```
Nenhuma camada interna importa camada externa. O domínio é agnóstico a Flask, sqlite3 e HTTP.

### Estrutura de Diretórios
```
SistemaGestao/
├── app/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── agendamento.py       # Entidade Agendamento + regras puras
│   │   │   ├── profissional.py
│   │   │   ├── procedimento.py
│   │   │   └── paciente.py
│   │   ├── repositories/
│   │   │   ├── agendamento_repo.py  # Interface (abstract)
│   │   │   ├── profissional_repo.py
│   │   │   └── paciente_repo.py
│   │   └── exceptions.py            # ConflitodeHorarioError, PacienteNaoEncontradoError, etc.
│   │
│   ├── application/
│   │   ├── criar_agendamento.py     # Use Case
│   │   ├── verificar_conflito.py    # Use Case (regra central)
│   │   ├── listar_agenda.py         # Use Case
│   │   ├── cancelar_agendamento.py  # Use Case
│   │   └── autoagendar_paciente.py  # Use Case (Fase 2)
│   │
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── connection.py        # Singleton de conexão sqlite3
│   │   │   ├── schema.sql           # DDL completo
│   │   │   └── repositories/
│   │   │       ├── sqlite_agendamento_repo.py
│   │   │       ├── sqlite_profissional_repo.py
│   │   │       └── sqlite_paciente_repo.py
│   │   └── notifications/
│   │       ├── whatsapp_adapter.py  # Fase 3
│   │       └── email_adapter.py     # Fase 3
│   │
│   ├── interfaces/
│   │   ├── agenda/
│   │   │   ├── routes.py            # Blueprint Flask
│   │   │   └── dtos.py              # Request/Response schemas
│   │   ├── profissionais/
│   │   │   └── routes.py
│   │   ├── pacientes/
│   │   │   └── routes.py
│   │   └── publico/
│   │       └── routes.py            # Link de autoagendamento (Fase 2)
│   │
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       ├── agenda/
│       ├── profissionais/
│       └── publico/
│
├── tests/
│   ├── domain/
│   └── application/
│
├── migrations/          # Scripts SQL versionados
├── config.py
├── run.py
├── CONTEXT.md
├── SPEC.md
├── PLAN.md
└── AI_ROLES.md
```

---

## 4. Schema do Banco de Dados (sqlite3)

```sql
CREATE TABLE usuarios (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT    NOT NULL,
    email     TEXT    NOT NULL UNIQUE,
    senha_hash TEXT   NOT NULL,
    perfil    TEXT    NOT NULL CHECK(perfil IN ('admin','recepcao','profissional')),
    ativo     INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE profissionais (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    especialidade   TEXT,
    cor_hex         TEXT    NOT NULL DEFAULT '#3498db',
    horario_inicio  TEXT    NOT NULL DEFAULT '08:00',
    horario_fim     TEXT    NOT NULL DEFAULT '18:00',
    dias_semana     TEXT    NOT NULL DEFAULT '1,2,3,4,5',  -- CSV: 0=dom..6=sab
    usuario_id      INTEGER REFERENCES usuarios(id),
    ativo           INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE procedimentos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nome             TEXT    NOT NULL,
    duracao_minutos  INTEGER NOT NULL DEFAULT 30,
    cor_hex          TEXT    NOT NULL DEFAULT '#e74c3c',
    preco_base       REAL,
    ativo            INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE pacientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    telefone        TEXT,
    email           TEXT,
    cpf             TEXT    UNIQUE,
    data_nascimento TEXT,
    observacoes     TEXT,
    ativo           INTEGER NOT NULL DEFAULT 1,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE agendamentos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id     INTEGER NOT NULL REFERENCES profissionais(id),
    paciente_id         INTEGER NOT NULL REFERENCES pacientes(id),
    procedimento_id     INTEGER NOT NULL REFERENCES procedimentos(id),
    data_hora_inicio    TEXT    NOT NULL,  -- ISO 8601: 'YYYY-MM-DD HH:MM'
    data_hora_fim       TEXT    NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'agendado'
                        CHECK(status IN ('agendado','confirmado','em_atendimento',
                                         'concluido','cancelado','falta')),
    observacoes         TEXT,
    origem              TEXT    NOT NULL DEFAULT 'interno'
                        CHECK(origem IN ('interno','autoagendamento')),
    criado_em           TEXT    NOT NULL DEFAULT (datetime('now')),
    atualizado_em       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_agendamentos_profissional_data
    ON agendamentos(profissional_id, data_hora_inicio);

CREATE TABLE lembretes_enviados (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agendamento_id  INTEGER NOT NULL REFERENCES agendamentos(id),
    tipo            TEXT    NOT NULL CHECK(tipo IN ('whatsapp','email','sms')),
    antecedencia_h  INTEGER NOT NULL,  -- horas antes do agendamento
    enviado_em      TEXT,
    status          TEXT    NOT NULL DEFAULT 'pendente'
                    CHECK(status IN ('pendente','enviado','erro')),
    erro_msg        TEXT
);

CREATE TABLE config_lembretes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    antecedencia_h  INTEGER NOT NULL,  -- ex: 24, 2
    tipo            TEXT    NOT NULL CHECK(tipo IN ('whatsapp','email')),
    ativo           INTEGER NOT NULL DEFAULT 1
);
```

---

## 5. Regras Arquiteturais Específicas do Projeto

1. **Verificação de conflito é domínio puro:** a função `verificar_conflito(profissional_id, inicio, fim, excluir_id=None)` vive em `/application/verificar_conflito.py` e recebe dados já hidratados — nunca faz query direta.
2. **Repositórios são interfaces no domínio, implementações na infraestrutura:** `AgendamentoRepository` (abstract) em `/domain`, `SqliteAgendamentoRepository` em `/infrastructure`.
3. **Cores no grid são responsabilidade do frontend:** o backend retorna `status`, `profissional.cor_hex`, `procedimento.cor_hex` e o JavaScript do FullCalendar decide a cor de exibição por regra de negócio visual.
4. **Sem dependência circular:** blueprints Flask não importam nada de `/domain` diretamente — passam por use cases em `/application`.
5. **Testes de domínio e aplicação sem banco:** a Squad Gamma deve conseguir rodar `pytest tests/domain/ tests/application/` sem nenhum arquivo `.db` presente.
