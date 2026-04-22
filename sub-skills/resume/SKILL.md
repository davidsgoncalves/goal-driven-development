---
name: resume
description: |
  Retoma uma task pausada. Lê o changelog, confirma com o usuário se o blocker foi resolvido, registra o bloco RESUME no changelog, remove `paused: true` do status e delega de volta para a skill da fase ativa (implement, plan, etc.). Use quando o usuário mencionar: "resume", "retomar", "continuar task", "voltar na task", "destravei", ou qualquer variação de retomada de task pausada.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Resume — Sub-skill de Retomada de Task

> Retoma uma task pausada. Carrega o contexto registrado no `changelog.md`, confirma com o usuário que a barreira foi resolvida, registra o evento de retomada, limpa o flag `paused` do status e delega de volta à skill responsável pela fase atual da task.

## Instruções

Quando esta skill for invocada, execute os passos **na ordem**:

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Verificar que a task está pausada

Ler `GOD/tasks/{cod-da-task}/status.md`:

- Se o arquivo não existe, informar que a task não foi encontrada e encerrar
- Se `paused: true` **não** estiver marcado (ausente ou `false`), informar que a task não está pausada e sugerir que o usuário rode diretamente a skill da fase atual. Encerrar

### 3. Carregar contexto da pausa

Ler `GOD/tasks/{cod-da-task}/changelog.md` e localizar o **último bloco `⏸ PAUSE`**.

- Extrair: timestamp da pausa, fase congelada, observação do usuário
- Se o changelog não existir ou não tiver bloco PAUSE (situação anômala — task marcada `paused: true` sem registro), avisar o usuário mas prosseguir assumindo que ele sabe o que está fazendo

### 4. Confirmar destravamento com o usuário

Apresentar o contexto da pausa:

> ▶ Retomando task `{cod-da-task}`.
>
> Você pausou em `{timestamp-da-pausa}` na fase `{phase}` com a observação:
>
> > {observação do usuário}
>
> Isso foi resolvido? Quer adicionar uma observação sobre a retomada? (responda com o texto, `sim` para retomar sem observação, ou `não` para manter pausada)

- **Se o usuário responder `não`**: manter a task pausada, encerrar a skill
- **Se responder `sim`** (ou fornecer observação de retomada): prosseguir

### 5. Escrever bloco de retomada no `changelog.md`

Anexar ao final do `GOD/tasks/{cod-da-task}/changelog.md`:

```markdown

## {timestamp-iso-8601-utc} — ▶ RESUME
**Fase:** {phase}
**Observação:** {observação do usuário, ou "sem observação"}
```

### 6. Atualizar `status.md`

Atualizar `GOD/tasks/{cod-da-task}/status.md`:

- `phase`: **preservar o valor atual**
- `paused`: **remover o campo** (não deixar `paused: false` — ausência do campo é a forma canônica de "não pausada")
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `resume`
- `branch`, `learned`, `prs`: preservar valores atuais

### 7. Delegar de volta à skill da fase ativa

Com base no campo `phase` restaurado, sugerir ou delegar para a skill apropriada:

| `phase` | Ação sugerida |
|---------|---------------|
| `initialized` | Delegar para `plan` |
| `planned` | Delegar para `implement` |
| `implementing` | Delegar para `implement` (continuar de onde parou, usando o changelog como referência) |
| `implemented` | Delegar para `pack-up` |
| `packed-up` | Estado anômalo (task finalizada não deveria estar pausada). Informar e encerrar |

**Contexto que deve ser passado à skill delegada:**

- Código da task
- Ponteiro pro `changelog.md` — a skill delegada deve lê-lo para entender o que já foi feito antes da pausa e o que destravou
- Observações de PAUSE e RESUME mais recentes

### 8. Reportar retomada

> ▶ Task `{cod-da-task}` retomada.
>
> 📍 Fase ativa: `{phase}`
> 📝 `GOD/tasks/{cod-da-task}/changelog.md` — bloco de retomada registrado
> 📋 `GOD/tasks/{cod-da-task}/status.md` — `paused` removido
>
> 💡 Próximo passo: continuando com `{skill-delegada}`...

Em seguida, iniciar a skill delegada.

---

## Guard-rails

- **Esta skill não altera `phase`.** Apenas remove o flag `paused` e delega.
- **Esta skill não escreve em `GOD/knowledge.md`.** Apenas `learn`.
- **Esta skill não executa comandos git.** O usuário é responsável por garantir que o ambiente esteja no estado correto antes de retomar.
- **Se o usuário declarar que o blocker não foi resolvido**, a task permanece pausada — a skill não força retomada.
