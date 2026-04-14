# Pack-up — Sub-skill de Finalização

> Executa todo o fluxo de finalização da task: commit, testes, linter, push, criação de PR e ações finais — tudo conforme definido no `pack-up-instructions.md`.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Ler instruções de pack-up

Ler o arquivo `GDD/pack-up-instructions.md` para obter as convenções do projeto:
- Branch inicial
- Padrão de nome de branch
- Padrão de mensagem de commit
- Processos de finalização (testes, linter, etc.)
- Padrão de mensagem de PR (título e corpo)
- Ações finais

### 2. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)
- Ler `GDD/tasks/{cod-da-task}/description.md` para obter título e descrição da task

### 3. Verificar estado do git

Verificar o estado atual do repositório:
- Branch atual (`git branch --show-current`)
- Alterações staged e unstaged (`git status`, `git diff`)
- Confirmar que existe trabalho para commitar

Se não houver alterações, informar o usuário e encerrar.

### 4. Revisão plano vs execução

Antes de commitar, chamar a sub-skill `review --execution` passando o código da task.

- Se o relatório retornar **Aprovado**: prosseguir com o commit
- Se o relatório retornar **Ajustes necessários**: apresentar o relatório ao usuário e perguntar se deseja corrigir antes de continuar ou prosseguir mesmo assim
- Se o relatório retornar **Reprovado**: apresentar o relatório ao usuário e pausar o pack-up até que as correções sejam feitas

### 5. Commit

Criar o commit seguindo o **padrão de mensagem de commit** definido no `pack-up-instructions.md`:
- Fazer stage das alterações relevantes (`git add` dos arquivos modificados)
- Criar o commit com a mensagem no padrão configurado
- Se o padrão não estiver definido, usar: `{cod-da-task}: {descrição breve da mudança}`

### 6. Processos de finalização

Executar os processos definidos no `pack-up-instructions.md`, na ordem em que aparecem. Exemplos:
- Rodar testes (`npm test`, `rspec`, etc.)
- Rodar linter (`eslint`, `rubocop`, etc.)
- Qualquer outro processo listado

**Se algum processo falhar:**
- Informar o usuário sobre a falha
- Tentar corrigir automaticamente se for algo simples (ex: fix de lint)
- Se não conseguir corrigir, pausar e perguntar ao usuário como prosseguir

### 7. Push

Fazer push do branch para o remote:
- `git push -u origin {branch-atual}`
- Se o push falhar, informar o usuário

### 8. Criar PR

Criar o Pull Request seguindo o **padrão de mensagem de PR** definido no `pack-up-instructions.md`:
- Usar `gh pr create` com título e corpo no padrão configurado
- Se o padrão não estiver definido, usar:
  - **Título:** `{cod-da-task}: {título da task}`
  - **Corpo:** descrição da task + resumo das alterações

### 9. Ações finais

Executar as ações finais definidas no `pack-up-instructions.md`. Exemplos:
- Criar PR em draft sem revisores
- Adicionar labels
- Atribuir revisores
- Qualquer outra ação listada

### 10. Reportar resultado

> ✅ Pack-up concluído para `{cod-da-task}`!
>
> 📝 Commit: `{hash}` — {mensagem do commit}
> 🔀 Branch: `{nome-do-branch}`
> 🔗 PR: {url-do-pr}
>
> [Resultado dos processos de finalização (testes, linter, etc.)]
> [Ações finais executadas]
