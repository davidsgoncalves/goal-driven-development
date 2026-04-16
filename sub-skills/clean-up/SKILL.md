---
name: clean-up
description: |
  Arquiva tasks finalizadas que já tiveram todos os seus PRs mergiados. Antes de arquivar, oferece rodar `learn` em tasks ainda não aprendidas. Move pastas de `GOD/tasks/{cod}/` para `GOD/tasks/.archived/{cod}/` (não apaga — o usuário decide quando remover manualmente). Use quando o usuário mencionar: "clean-up", "limpar tasks", "remover tasks concluídas", "arrumar a casa", "arquivar tasks".
tools: Read, Glob, Grep, Bash, Edit, Write, Agent
---

# Clean-up — Sub-skill de Arquivamento de Tasks

> Percorre as tasks em `phase: packed-up`, verifica se todos os PRs foram mergiados e arquiva as que estão prontas. Oferece rodar `learn` antes de arquivar para tasks ainda não aprendidas. **Arquiva (move para `.archived/`), não apaga** — remoção definitiva é decisão do usuário.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Verificar pré-requisitos

- Verificar se `GOD/tasks/` existe. Se não, informar que o projeto não foi configurado e encerrar.
- Verificar se o `gh` CLI está disponível (`gh --version`). Se não estiver instalado/autenticado, avisar o usuário:

  > ⚠️ A skill `clean-up` precisa do GitHub CLI (`gh`) instalado e autenticado para verificar o status dos PRs.
  >
  > Instale em: https://cli.github.com — depois rode `gh auth login`.
  >
  > Encerrando sem alterações.

### 2. Listar candidatas em `packed-up`

Percorrer cada pasta em `GOD/tasks/`, **ignorando pastas que começam com `.`** (ex: `.archived/`).

Para cada pasta de task, ler `status.md` e filtrar:
- Incluir apenas as com `phase == packed-up`
- Ignorar as outras (em andamento ou já arquivadas)

Se nenhuma task estiver em `packed-up`, informar ao usuário e encerrar:
> ✅ Nenhuma task em `packed-up` para arquivar. Nada a fazer.

### 3. Verificar status dos PRs

Para cada task candidata, ler o array `prs` do `status.md`.

- Se `prs` está vazio ou ausente: pular a task e marcá-la como `sem-pr-registrado` no relatório.
- Para cada URL em `prs`, executar:
  ```
  gh pr view {url} --json state,mergedAt,number
  ```
  E coletar `state` (`OPEN` / `MERGED` / `CLOSED`) e `mergedAt`.

Classificar a task:
- **`pronta-para-arquivar`** — todos os PRs têm `state == MERGED`
- **`pendente`** — pelo menos um PR não foi mergiado (ainda aberto, fechado sem merge, ou erro na consulta)

### 4. Apresentar lista ao usuário

Mostrar as tasks prontas para arquivar, separadas das pendentes:

```
🧹 **Clean-up — Candidatas a arquivamento**

✅ Prontas para arquivar (todos os PRs mergiados):
  - `PROJ-123` — 2 PRs mergiados (vakinha-api#123 em 2026-04-10, vakinha-web#456 em 2026-04-11)
    learned: false ← ainda não aprendida
  - `PROJ-456` — 1 PR mergiado (vakinha-api#789 em 2026-04-12)
    learned: true

⏸️ Pendentes (PRs ainda abertos ou sem merge):
  - `PROJ-789` — vakinha-web#999 ainda em `OPEN`

⚠️ Sem PR registrado em status.md:
  - `LEGACY-1` — rode `pack-up` novamente ou edite `status.md` manualmente se aplicável

---

Confirma arquivamento das {N} tasks prontas? (sim / não / seleção)

Se quiser arquivar apenas algumas, responda com os códigos (ex: "sim, apenas PROJ-123").
```

Aguardar resposta. Se for "não" ou equivalente, encerrar sem alterações. Se for "sim" parcial, arquivar apenas as selecionadas.

### 5. Oferecer `learn` antes de arquivar

Para cada task confirmada para arquivamento:

- Ler `learned` do `status.md`
- **Se `learned: false`**, perguntar:
  > A task `PROJ-123` ainda não foi aprendida. Rodar `learn` antes de arquivar? (sim / não)
- Se o usuário responder **sim**: invocar a skill `learn` passando o código da task. A skill `learn` vai flipar `learned: true` ao concluir.
- Se responder **não**: seguir direto para o arquivamento sem rodar `learn`.
- **Se `learned: true`**: pular esta pergunta e seguir direto para o arquivamento.

Processar as tasks uma por uma nessa ordem (pergunta de learn → arquivamento) para que o usuário acompanhe o progresso.

### 6. Arquivar

Para cada task a arquivar:

1. Garantir que `GOD/tasks/.archived/` existe (criar se não existir)
2. Mover a pasta:
   ```
   mv GOD/tasks/{cod-da-task}/ GOD/tasks/.archived/{cod-da-task}/
   ```
3. Se o move falhar (ex: conflito de nome na pasta `.archived/`), renomear com sufixo:
   ```
   GOD/tasks/.archived/{cod-da-task}-{timestamp}/
   ```

**Não apagar o branch local nem remoto.** Clean-up mexe apenas em `GOD/tasks/`.

### 7. Reportar resultado

```
✅ **Clean-up concluído**

Arquivadas ({N}):
  - `PROJ-123` → `GOD/tasks/.archived/PROJ-123/` (learn executado antes)
  - `PROJ-456` → `GOD/tasks/.archived/PROJ-456/` (já aprendida)

Pendentes (continuam em `GOD/tasks/`):
  - `PROJ-789` — PR ainda aberto

Sem PR registrado:
  - `LEGACY-1` — verifique manualmente

---

📂 Pasta `.archived/` contém as tasks arquivadas. Remoção definitiva é sua decisão — rode `rm -rf GOD/tasks/.archived/` (ou mova para outro local) quando não precisar mais desse histórico.

🌿 Os branches locais/remotos das tasks arquivadas **não foram tocados**. Se quiser removê-los:
  - Local: `git branch -d {branch}`
  - Remoto: `git push origin --delete {branch}` (geralmente o GitHub já apaga automaticamente após merge se essa configuração estiver ativa no repo)
```

---

## Guard-rails

- **Esta skill não escreve em `GOD/knowledge.md`.** Quando o usuário escolhe rodar `learn` antes de arquivar, é a skill `learn` que escreve — esta skill apenas delega.
- **Esta skill não apaga pastas.** Sempre arquiva (move para `.archived/`). Remoção definitiva é ação manual do usuário.
- **Esta skill nunca age em tasks fora de `phase: packed-up`.** Tasks em andamento (`initialized`, `planned`, `implementing`, `implemented`) são ignoradas.
- **Esta skill ignora `GOD/tasks/.archived/`** ao listar tasks.
- **Esta skill não mexe em branches git** (nem locais, nem remotos). Só instrui o usuário no relatório final.
- **Nunca arquiva sem confirmação explícita do usuário.**
