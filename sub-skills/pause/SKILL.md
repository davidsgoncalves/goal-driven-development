---
name: pause
description: |
  Pausa uma task em andamento, registrando uma observação opcional do usuário no changelog e marcando o status como pausado. Use quando o usuário mencionar: "pause", "pausar", "pausar task", "tô travado", "parar aqui", "retomo depois", ou quando uma skill do fluxo detectar uma barreira que impede prosseguir (código ausente, dependência externa indisponível, decisão pendente do usuário).
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Pause — Sub-skill de Pausa de Task

> Pausa uma task em andamento. Escreve um bloco de pausa no `changelog.md` da task (com observação opcional do usuário) e marca `paused: true` no `status.md`. A task pode ser retomada posteriormente com a skill `resume`.

## Quando é invocada

1. **Explicitamente pelo usuário** — `pause`, `pausar`, `pausar task`, ou com observação inline (ex: `pause "esperando endpoint X"`).
2. **Por outra skill do fluxo** — `implement` ou `plan` delegam para `pause` quando detectam uma barreira que impede prosseguir:
   - Código/endpoint/módulo que deveria existir mas não existe
   - Dependência externa indisponível (serviço fora, credencial faltando, MCP não autenticado)
   - Decisão do usuário pendente que bloqueia progresso
   - Ambiguidade no plano que exige clarificação antes de prosseguir

## Instruções

Quando esta skill for invocada, execute os passos **na ordem**:

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Verificar estado atual

Ler `GOD/tasks/{cod-da-task}/status.md`:

- Se o arquivo não existe, informar que a task não foi encontrada e encerrar
- Se `paused: true` já estiver marcado, informar que a task já está pausada e sugerir `resume`. Encerrar
- Se `phase: packed-up`, informar que a task já foi finalizada e não precisa ser pausada. Encerrar

### 3. Coletar observação do usuário

**Se a skill foi invocada inline com observação** (ex: `pause "esperando endpoint X"`): usar essa observação direto.

**Se a skill foi invocada sem observação, perguntar ao usuário:**

> ⏸ Vou pausar a task `{cod-da-task}` na fase `{phase}`.
>
> Quer adicionar uma observação sobre o motivo da pausa? (responda com o texto, ou `pular` para pausar sem observação)

A observação deve explicar o motivo da pausa — o que está bloqueando, o que precisa acontecer pra destravar, qualquer contexto útil para quando a task for retomada.

**Se a skill foi invocada por outra skill detectando barreira:** a skill chamadora deve passar o motivo da barreira como observação. Ainda assim, mostrar ao usuário o motivo detectado e perguntar se ele quer complementar antes de registrar.

### 4. Escrever bloco de pausa no `changelog.md`

Abrir `GOD/tasks/{cod-da-task}/changelog.md` (criar se não existir).

- **Se o arquivo não existe**, criar com o header:
  ```markdown
  # Changelog — {cod-da-task}
  ```

Anexar ao final:

```markdown

## {timestamp-iso-8601-utc} — ⏸ PAUSE
**Fase:** {phase atual — ex: implementing}
**Observação:** {observação do usuário, ou "sem observação" se ele pulou}
```

- `timestamp-iso-8601-utc` — ex: `2026-04-22T16:00:00Z`
- `phase atual` — ler do `status.md` (não alterar)

### 5. Atualizar `status.md`

Atualizar `GOD/tasks/{cod-da-task}/status.md` adicionando o campo `paused`:

- `phase`: **preservar o valor atual** (pause não muda a fase)
- `paused`: `true`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `pause`
- `branch`, `learned`, `prs`: preservar valores atuais

Exemplo após pause:

```yaml
---
phase: implementing
paused: true
updated_at: 2026-04-22T16:00:00Z
updated_by: pause
branch: task/PROJ-123/add-phone-field
learned: false
prs: []
---
```

### 6. Reportar resultado

> ⏸ Task `{cod-da-task}` pausada.
>
> 📍 Fase congelada em: `{phase}`
> 📝 `GOD/tasks/{cod-da-task}/changelog.md` — bloco de pausa registrado
> 📋 `GOD/tasks/{cod-da-task}/status.md` — `paused: true`
>
> Quando quiser retomar, rode `resume`.

---

## Guard-rails

- **Esta skill não altera `phase`** — a fase reflete o trabalho em si. `paused` é um modificador paralelo.
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas a skill `learn` pode fazê-lo.
- **Esta skill não executa comandos git.** Não commita, não faz stash, não muda branch. O estado do git fica como o usuário deixou — ele pode commitar parciais manualmente se quiser antes de pausar.
- **Esta skill não remove arquivos nem reverte mudanças.** Pausar é congelar, não desfazer.
