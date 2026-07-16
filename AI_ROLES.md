# AI_ROLES.md — OdontoClinica / SistemaGestao

**Projeto:** Sistema de Gestão com Módulo de Agenda  
**Data:** 2026-07-15

---

## Squad Omega — Commercial & Growth

| Agente | Responsabilidade neste projeto |
|---|---|
| SDR Staff | Mapeamento de clínicas-alvo (odonto/estética), qualificação por porte e dor de agenda |
| Tech Estimator & Pricing Specialist | Estimativa de horas por fase (Fase 1–3), precificação por plano (Básico/Intermediário/Avançado) |
| Account Executive Staff | `PROPOSAL.md` com ROI e proposta de planos SaaS |

---

## Squad Alpha — Product & Architecture

| Agente | Responsabilidade neste projeto |
|---|---|
| Product Manager Staff | `SPEC.md` com BDD de todos os casos de uso de agendamento e autoagendamento |
| Software Architect | Decisão de stack (registrada em `CONTEXT.md`), guardião da Clean Architecture, revisão de PRs |

---

## Squad Beta — Core Engineering

| Agente | Responsabilidade neste projeto |
|---|---|
| Senior Backend Engineer | Domínio puro (entidades + use cases), repositórios sqlite3, rotas Flask, API JSON para FullCalendar |
| Senior Frontend Engineer | Templates Jinja2, integração FullCalendar.js, lógica de cores no grid, responsividade do painel |

---

## Squad Gamma — Quality & Assurance

| Agente | Responsabilidade neste projeto |
|---|---|
| Senior SDET (QA) | Testes unitários de `/domain` e `/application` (sem banco), testes de integração de rotas, validação contra `SPEC.md` |

**Regra:** testes de domínio e aplicação devem rodar 100% sem arquivo `.db` ativo.

---

## Squad Delta — Platform & DevOps

| Agente | Responsabilidade neste projeto |
|---|---|
| Senior DevOps/SRE | Dockerfile, GitHub Actions (lint + testes + deploy), estratégia de backup do arquivo `.db` |

---

## Decisões de Arquitetura Fixadas (não negociáveis por agentes individuais)

1. Stack: Flask + sqlite3 puro — sem SQLAlchemy, sem JWT.
2. Autenticação: sessão Flask com cookie HttpOnly.
3. Verificação de conflito: use case puro em `/application`, nunca em rota.
4. Grid visual: FullCalendar.js alimentado por endpoint JSON `/api/agenda/eventos`.
5. Qualquer alteração de stack deve ser aprovada pelo Agent Software Architect e registrada em `CONTEXT.md`.
