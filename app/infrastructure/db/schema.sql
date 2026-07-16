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
    cor_hex        TEXT    NOT NULL DEFAULT '#3498db',
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

CREATE TABLE IF NOT EXISTS agendamentos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id  INTEGER NOT NULL REFERENCES profissionais(id),
    paciente_id      INTEGER NOT NULL REFERENCES pacientes(id),
    procedimento_id  INTEGER NOT NULL REFERENCES procedimentos(id),
    data_hora_inicio TEXT    NOT NULL,
    data_hora_fim    TEXT    NOT NULL,
    status           TEXT    NOT NULL DEFAULT 'agendado'
                     CHECK(status IN ('agendado','confirmado','em_atendimento',
                                      'concluido','cancelado','falta')),
    observacoes      TEXT,
    origem           TEXT    NOT NULL DEFAULT 'interno'
                     CHECK(origem IN ('interno','autoagendamento')),
    criado_em        TEXT    NOT NULL DEFAULT (datetime('now')),
    atualizado_em    TEXT    NOT NULL DEFAULT (datetime('now'))
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
