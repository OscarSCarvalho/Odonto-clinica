-- Schema: OdontoClinica / SistemaGestao
-- Versão: 1.0

CREATE TABLE IF NOT EXISTS usuarios (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    senha_hash TEXT    NOT NULL,
    perfil     TEXT    NOT NULL CHECK(perfil IN ('admin','recepcao','profissional')),
    ativo      INTEGER NOT NULL DEFAULT 1,
    criado_em  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS profissionais (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL,
    especialidade  TEXT,
    cor_hex        TEXT    NOT NULL DEFAULT '#2563eb',
    horario_inicio TEXT    NOT NULL DEFAULT '08:00',
    horario_fim    TEXT    NOT NULL DEFAULT '18:00',
    dias_semana    TEXT    NOT NULL DEFAULT '1,2,3,4,5',
    usuario_id     INTEGER REFERENCES usuarios(id),
    ativo          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS procedimentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT    NOT NULL,
    duracao_minutos INTEGER NOT NULL DEFAULT 30,
    cor_hex         TEXT    NOT NULL DEFAULT '#e74c3c',
    preco_base      REAL,
    retorno_dias    INTEGER,
    ativo           INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS pacientes (
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

CREATE TABLE IF NOT EXISTS planos_recorrentes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id       INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id   INTEGER NOT NULL REFERENCES profissionais(id),
    procedimento_id   INTEGER NOT NULL REFERENCES procedimentos(id),
    intervalo_dias    INTEGER NOT NULL,
    proxima_data      TEXT    NOT NULL,
    horario_preferido TEXT,
    observacoes       TEXT,
    ativo             INTEGER NOT NULL DEFAULT 1,
    criado_em         TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_planos_recorrentes_proxima_data
    ON planos_recorrentes(proxima_data);

CREATE TABLE IF NOT EXISTS agendamentos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id     INTEGER NOT NULL REFERENCES profissionais(id),
    paciente_id         INTEGER NOT NULL REFERENCES pacientes(id),
    procedimento_id     INTEGER NOT NULL REFERENCES procedimentos(id),
    data_hora_inicio    TEXT    NOT NULL,
    data_hora_fim       TEXT    NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'agendado'
                        CHECK(status IN ('agendado','confirmado','aguardando','em_atendimento',
                                         'concluido','cancelado','falta')),
    observacoes         TEXT,
    origem              TEXT    NOT NULL DEFAULT 'interno'
                        CHECK(origem IN ('interno','autoagendamento')),
    plano_recorrente_id INTEGER REFERENCES planos_recorrentes(id),
    criado_em           TEXT    NOT NULL DEFAULT (datetime('now')),
    atualizado_em       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_agendamentos_profissional_data
    ON agendamentos(profissional_id, data_hora_inicio);

CREATE INDEX IF NOT EXISTS idx_agendamentos_status
    ON agendamentos(status);

CREATE TABLE IF NOT EXISTS lembretes_enviados (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    agendamento_id INTEGER NOT NULL REFERENCES agendamentos(id),
    tipo           TEXT    NOT NULL CHECK(tipo IN ('whatsapp','email','sms')),
    antecedencia_h INTEGER NOT NULL,
    tentativas     INTEGER NOT NULL DEFAULT 0,
    enviado_em     TEXT,
    status         TEXT    NOT NULL DEFAULT 'pendente'
                   CHECK(status IN ('pendente','enviado','erro')),
    erro_msg       TEXT
);

CREATE TABLE IF NOT EXISTS config_lembretes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    antecedencia_h INTEGER NOT NULL,
    tipo           TEXT    NOT NULL CHECK(tipo IN ('whatsapp','email')),
    ativo          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS paciente_anexos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    nome_original   TEXT    NOT NULL,
    caminho_arquivo TEXT    NOT NULL,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_anexos_paciente ON paciente_anexos(paciente_id);

CREATE TABLE IF NOT EXISTS tarefas_retorno (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    agendamento_id INTEGER NOT NULL REFERENCES agendamentos(id),
    paciente_id    INTEGER NOT NULL REFERENCES pacientes(id),
    data_sugerida  TEXT    NOT NULL,
    observacoes    TEXT,
    status         TEXT    NOT NULL DEFAULT 'pendente' CHECK(status IN ('pendente','contatado')),
    contato_em     TEXT,
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tarefas_retorno_status ON tarefas_retorno(status);

CREATE TABLE IF NOT EXISTS mensalidades (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id    INTEGER NOT NULL REFERENCES pacientes(id),
    valor          REAL    NOT NULL,
    dia_vencimento INTEGER NOT NULL,
    observacoes    TEXT,
    ativo          INTEGER NOT NULL DEFAULT 1,
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pagamentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    agendamento_id  INTEGER REFERENCES agendamentos(id),
    mensalidade_id  INTEGER REFERENCES mensalidades(id),
    valor           REAL    NOT NULL,
    data_vencimento TEXT    NOT NULL,
    forma_pagamento TEXT    CHECK(forma_pagamento IN ('dinheiro','pix','cartao_debito','cartao_credito')
                                   OR forma_pagamento IS NULL),
    status          TEXT    NOT NULL DEFAULT 'pendente' CHECK(status IN ('pendente','pago')),
    data_pagamento  TEXT,
    observacoes     TEXT,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pagamentos_status ON pagamentos(status);
CREATE INDEX IF NOT EXISTS idx_pagamentos_paciente ON pagamentos(paciente_id);

CREATE TABLE IF NOT EXISTS orcamentos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id      INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id  INTEGER REFERENCES profissionais(id),
    status           TEXT NOT NULL DEFAULT 'rascunho'
                     CHECK(status IN ('rascunho','enviado','aprovado','recusado','expirado')),
    validade_dias    INTEGER NOT NULL DEFAULT 30,
    desconto_global  REAL NOT NULL DEFAULT 0,
    desconto_tipo    TEXT NOT NULL DEFAULT 'percentual'
                     CHECK(desconto_tipo IN ('percentual','valor')),
    observacoes      TEXT,
    token_aprovacao  TEXT UNIQUE,
    criado_em        TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_orcamentos_status   ON orcamentos(status);
CREATE INDEX IF NOT EXISTS idx_orcamentos_paciente ON orcamentos(paciente_id);

CREATE TABLE IF NOT EXISTS orcamento_itens (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    orcamento_id    INTEGER NOT NULL REFERENCES orcamentos(id) ON DELETE CASCADE,
    procedimento_id INTEGER NOT NULL REFERENCES procedimentos(id),
    quantidade      INTEGER NOT NULL DEFAULT 1,
    valor_unitario  REAL NOT NULL,
    desconto_item   REAL NOT NULL DEFAULT 0,
    desconto_tipo   TEXT NOT NULL DEFAULT 'percentual'
                    CHECK(desconto_tipo IN ('percentual','valor'))
);
