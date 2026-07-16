# SPEC.md — OdontoClinica / SistemaGestao
# Módulo: Agenda Clínica

**Versão:** 1.0  
**Data:** 2026-07-15  
**Agente responsável:** Agent Product Manager Staff (Squad Alpha)  
**Metodologia:** BDD — Dado / Quando / Então

---

## 1. Objetivo

Construir um módulo de agenda visual para clínicas odontológicas e estéticas que permita:
- Visualização e gestão de agendamentos por administradores e recepcionistas.
- Prevenção automática de conflitos de horário por profissional.
- Autoagendamento público por pacientes via link compartilhável (Fase 2).
- Notificações automáticas de lembrete (Fase 3).

---

## 2. Entidades de Domínio

| Entidade | Atributos-chave |
|---|---|
| `Profissional` | id, nome, cor_hex, horario_inicio, horario_fim, dias_semana |
| `Procedimento` | id, nome, duracao_minutos, cor_hex |
| `Paciente` | id, nome, telefone, email, cpf |
| `Agendamento` | id, profissional_id, paciente_id, procedimento_id, data_hora_inicio, data_hora_fim, status, origem |
| `LembreteEnviado` | id, agendamento_id, tipo, antecedencia_h, status |

---

## 3. Regras de Negócio Globais

- **RN-01:** Um profissional não pode ter dois agendamentos com sobreposição de horário (status ≠ `cancelado` e ≠ `falta`).
- **RN-02:** `data_hora_fim` é calculada automaticamente como `data_hora_inicio + procedimento.duracao_minutos`.
- **RN-03:** Agendamentos só podem ser criados dentro do expediente do profissional (dias e horários configurados).
- **RN-04:** Apenas usuários autenticados (`admin` ou `recepcao`) podem criar/editar/cancelar agendamentos internos.
- **RN-05:** O link de autoagendamento é público (sem autenticação), mas os slots exibidos devem respeitar RN-01 e RN-03.
- **RN-06:** Status permitidos: `agendado → confirmado → em_atendimento → concluido` ou `agendado/confirmado → cancelado/falta`.
- **RN-07:** Agendamentos com status `cancelado` ou `falta` não bloqueiam o horário para novas marcações.

---

## 4. FASE 1 — CRUD de Agenda + Grid Visual + Verificação de Conflito

### UC-01: Visualizar grid de agenda (dia/semana/mês)

**Dado** que o usuário está autenticado e acessa `/agenda`  
**Quando** seleciona a visualização "Diária", "Semanal" ou "Mensal"  
**Então** o grid exibe todos os agendamentos do período com as cores corretas:
- Cor do evento = `procedimento.cor_hex`
- Cor de fundo da coluna do profissional = `profissional.cor_hex` (suavizado)
- Slot fora do expediente do profissional = cinza (`#CCCCCC`)
- Slot livre dentro do expediente = branco (`#FFFFFF`)
- Slot ocupado = cor do procedimento (`procedimento.cor_hex`)

**Dado** que o grid está carregado  
**Quando** o usuário filtra por profissional  
**Então** apenas os eventos do profissional selecionado são exibidos

**Caso de borda CB-01:** Profissional com expediente 08:00–12:00 e 14:00–18:00 (pausa almoço) — o slot 12:00–14:00 deve aparecer cinza mesmo sendo dia útil.

---

### UC-02: Criar agendamento (interno)

**Dado** que o usuário autenticado acessa o formulário de agendamento  
**Quando** seleciona profissional, paciente, procedimento e data/hora de início  
**Então** o sistema calcula `data_hora_fim = inicio + procedimento.duracao_minutos`

**E quando** submete o formulário  
**E** não há conflito (RN-01) e o horário está dentro do expediente (RN-03)  
**Então** o agendamento é salvo com status `agendado` e aparece no grid

**Quando** o horário solicitado conflita com agendamento existente (RN-01)  
**Então** o sistema retorna erro `409 Conflict` com mensagem:  
`"Conflito: [Nome do Profissional] já tem [Procedimento] com [Paciente] das [HH:MM] às [HH:MM]"`

**Quando** o horário está fora do expediente do profissional (RN-03)  
**Então** o sistema retorna erro `422 Unprocessable` com mensagem:  
`"Horário fora do expediente de [Nome do Profissional] ([HH:MM]–[HH:MM])"`

**Caso de borda CB-02:** Agendamento de 50 minutos a partir das 17:40 com expediente até 18:00 — fim = 18:30, deve ser recusado por ultrapassar o expediente.

**Caso de borda CB-03:** Criar agendamento que começa exatamente quando outro termina (ex: 09:00–09:30 e 09:30–10:00) — deve ser permitido (sem sobreposição).

**Caso de borda CB-04:** Criar agendamento sobreposto a um agendamento com status `cancelado` — deve ser permitido (RN-07).

---

### UC-03: Editar agendamento

**Dado** que existe um agendamento com status `agendado` ou `confirmado`  
**Quando** o usuário altera data/hora, profissional ou procedimento  
**Então** o sistema re-executa a verificação de conflito excluindo o próprio agendamento da checagem

**Quando** o agendamento tem status `concluido` ou `em_atendimento`  
**Então** o sistema bloqueia edição de data/hora e retorna `403`  
(apenas `observacoes` e `status` podem ser editados)

---

### UC-04: Cancelar agendamento

**Dado** que existe um agendamento com status ≠ `concluido`  
**Quando** o usuário cancela  
**Então** o status muda para `cancelado` e o slot fica disponível para novas marcações

**Quando** o status é `concluido`  
**Então** o cancelamento é bloqueado com mensagem `"Não é possível cancelar atendimento já concluído"`

---

### UC-05: CRUD de Profissionais

**Dado** que o usuário tem perfil `admin`  
**Quando** cria um profissional com nome, cor, horário e dias de trabalho  
**Então** o profissional aparece nas opções de agendamento e no grid

**Quando** tenta criar profissional com cor hexadecimal inválida  
**Então** retorna erro de validação `"Cor deve estar no formato #RRGGBB"`

**Quando** desativa um profissional com agendamentos futuros  
**Então** o sistema alerta: `"[N] agendamento(s) futuro(s) serão afetados"` e requer confirmação

---

### UC-06: CRUD de Procedimentos

**Dado** que o usuário tem perfil `admin`  
**Quando** cria um procedimento com nome, duração em minutos e cor  
**Então** o procedimento aparece nas opções de agendamento

**Caso de borda CB-05:** Duração de 0 minutos — deve ser rejeitado com `"Duração mínima é 5 minutos"`.

---

### UC-07: CRUD de Pacientes

**Dado** que o usuário está autenticado  
**Quando** cadastra paciente com CPF já existente  
**Então** retorna erro `"CPF já cadastrado para [Nome do Paciente]"` com link para o cadastro existente

**Quando** busca paciente por nome (campo de autocomplete no formulário de agendamento)  
**Então** retorna lista filtrada em tempo real (mínimo 3 caracteres, máximo 10 resultados)

---

### UC-08: Endpoint JSON para FullCalendar

**Dado** que o frontend faz `GET /api/agenda/eventos?start=YYYY-MM-DD&end=YYYY-MM-DD&profissional_id=X`  
**Quando** o parâmetro `profissional_id` é omitido  
**Então** retorna todos os agendamentos do período

**E** cada evento retorna:
```json
{
  "id": 42,
  "title": "Ana Paula — Limpeza",
  "start": "2026-07-20T09:00:00",
  "end": "2026-07-20T09:30:00",
  "backgroundColor": "#e74c3c",
  "borderColor": "#c0392b",
  "extendedProps": {
    "paciente": "Ana Paula",
    "procedimento": "Limpeza",
    "profissional": "Dr. Carlos",
    "status": "agendado"
  }
}
```

---

## 5. FASE 2 — Link Público de Autoagendamento

### UC-09: Acessar link público de agendamento

**Dado** que um paciente recebe o link `https://clinica.com/agendar/[slug-da-clinica]`  
**Quando** acessa o link sem estar autenticado  
**Então** vê uma página pública com:
- Logo/nome da clínica
- Seleção de profissional (com foto e especialidade)
- Seleção de procedimento
- Grid de slots disponíveis (apenas horários livres, RN-01 e RN-03 aplicados)
- Formulário de dados pessoais (nome, telefone, e-mail)

---

### UC-10: Paciente realiza autoagendamento

**Dado** que o paciente selecionou profissional, procedimento e slot disponível  
**Quando** preenche nome e telefone e confirma  
**Então** o sistema:
1. Busca paciente por CPF/telefone — se encontrado, vincula; se não, cria novo cadastro mínimo
2. Cria agendamento com `status=agendado` e `origem=autoagendamento`
3. Exibe tela de confirmação com data, hora e nome do profissional
4. Envia confirmação por WhatsApp/e-mail se configurado

**Quando** o slot é ocupado por outro agendamento entre o paciente selecionar e confirmar (race condition)  
**Então** o sistema informa `"Horário acabou de ser reservado por outra pessoa"` e exibe novos slots disponíveis

**Caso de borda CB-06:** Paciente tenta agendar dois procedimentos no mesmo slot — deve ser permitido (profissionais diferentes) ou bloqueado (mesmo profissional, RN-01).

---

## 6. FASE 3 — Lembretes Automáticos

### UC-11: Configurar lembretes

**Dado** que o admin acessa `/configuracoes/lembretes`  
**Quando** adiciona uma regra: "24h antes, via WhatsApp"  
**Então** todos os novos agendamentos com status ≠ `cancelado` passam a ter um lembrete programado

---

### UC-12: Enviar lembrete automático

**Dado** que existe um agendamento com lembrete programado para N horas antes  
**Quando** o sistema executa o job (cron/scheduler) e o horário de envio chegou  
**E** o status do agendamento não é `cancelado` ou `falta`  
**Então** envia a mensagem via API configurada (WhatsApp/e-mail)  
**E** registra em `lembretes_enviados` com `status=enviado`

**Quando** a API de envio retorna erro  
**Então** registra em `lembretes_enviados` com `status=erro` e `erro_msg` preenchido  
**E** tenta reenvio até 3 vezes com intervalo de 15 minutos

**Caso de borda CB-07:** Agendamento cancelado após o lembrete já ter sido disparado — lembrete enviado não é revertido, mas lembretes futuros são cancelados.

---

## 7. Autenticação e Controle de Acesso

| Rota | Perfis permitidos |
|---|---|
| `/agenda` (visualização) | admin, recepcao, profissional |
| `/agenda/novo` | admin, recepcao |
| `/agenda/editar/:id` | admin, recepcao |
| `/agenda/cancelar/:id` | admin, recepcao |
| `/profissionais/*` | admin |
| `/procedimentos/*` | admin |
| `/pacientes/*` | admin, recepcao |
| `/configuracoes/*` | admin |
| `/agendar/:slug` | público (sem autenticação) |
| `/api/agenda/eventos` | admin, recepcao, profissional |

**Caso de borda CB-08:** Profissional autenticado acessa `/api/agenda/eventos` — deve ver apenas seus próprios agendamentos, não os de outros profissionais.

---

## 8. Requisitos Não-Funcionais

- **RNF-01:** Grid de agenda deve carregar em < 1 segundo para períodos de até 1 mês.
- **RNF-02:** A verificação de conflito deve retornar em < 200ms.
- **RNF-03:** Link público de autoagendamento deve funcionar sem cookies de sessão administrativa.
- **RNF-04:** O sistema deve ser utilizável em dispositivos móveis (responsivo).
- **RNF-05:** Backup do arquivo `.db` deve ser automatizado diariamente.

---

## 9. Fora de Escopo (explícito)

- Multi-tenant / múltiplas unidades (roadmap Plano Avançado — não implementar agora).
- Integração com prontuário eletrônico completo (simplificado via `observacoes` por ora).
- Integração com módulo financeiro (gerar lançamento ao concluir agendamento — roadmap Fase 4).
- App mobile nativo.
- Pagamento online no autoagendamento.
