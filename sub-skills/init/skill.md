# Init — Sub-skill de Inicialização de Task

> Recebe uma task (via Jira ou manual), coleta contexto, consulta histórico e cria a estrutura da task no projeto.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Verificar estado do git

Antes de qualquer coisa, verificar:

1. Ler `GDD/pack-up-instructions.md` para identificar o **branch inicial** configurado pelo usuário
2. Verificar se o usuário está no branch inicial (`git branch --show-current`)
3. Verificar se existem alterações não commitadas (`git status`)

**Se o branch está correto e não há alterações pendentes:** atualizar o branch inicial com `git pull` antes de seguir para o próximo passo. Se o pull falhar (ex: conflitos remotos), avisar o usuário e aguardar orientação antes de continuar.

**Se o branch está errado OU existem alterações não commitadas:** apresentar as seguintes opções ao usuário:

> ⚠️ Foram detectadas pendências no git antes de iniciar a task:
> - [Branch atual: `X` — esperado: `Y`] (se aplicável)
> - [Alterações não commitadas detectadas] (se aplicável)
>
> Escolha uma opção:
> 1. **Reverter e continuar** — descarta as alterações, faz checkout no branch inicial e cria o branch da nova task
> 2. **Criar apenas as pastas** — cria a estrutura da task em `GDD/tasks/` mas não mexe no git. Resolva as pendências manualmente e rode o init novamente
> 3. **Abortar** — cancela o init sem fazer nada

Aguardar a escolha do usuário e agir conforme:
- **Opção 1:** `git checkout -- .` + `git checkout {branch-inicial}` + `git pull` (atualizar o branch) + criar branch da task seguindo o padrão definido em `pack-up-instructions.md`
- **Opção 2:** pular para o passo de criação de estrutura (passo 5) e encerrar após criar as pastas
- **Opção 3:** encerrar sem executar nada

### 2. Receber input da task

O usuário deve fornecer **uma** das seguintes opções:

- **Link do Jira** — ex: `https://empresa.atlassian.net/browse/PROJ-123`
- **Código da task** — ex: `PROJ-123` (será buscado no Jira via MCP Atlassian)
- **Nome/descrição manual** — texto livre descrevendo a task

### 3. Obter dados da task

**Se foi fornecido link ou código do Jira:**
- Acessar o Jira via MCP Atlassian e obter:
  - Título da task
  - Descrição completa
  - Links do Figma (se existirem nos campos ou na descrição)
  - Qualquer anexo ou contexto relevante
- Usar o código da task do Jira como identificador (ex: `PROJ-123`)

**Se foi fornecida descrição manual:**
- O usuário deve informar um código ou nome curto para identificar a task (ex: `minha-task`)
- Usar o texto fornecido como descrição

### 4. Consultar knowledge

Ler o arquivo `GDD/knowledge.md`. O knowledge terá registros de tasks anteriores no formato:

```
### {cod-da-task} — {breve descrição}
- **commits:** {hash1}, {hash2}, ...
- **arquivos principais:** {lista dos arquivos mais relevantes}
- **aprendizados:** {o que foi aprendido, decisões tomadas, armadilhas evitadas}
```

Verificar se existem tasks anteriores com contexto semelhante à task atual. Se encontrar tasks semelhantes, guardar os **códigos de commit** (pode haver mais de um por task) e os **aprendizados** para incluir no `description.md` como referência.

### 5. Sessão de perguntas e respostas

Após coletar os dados da task, iniciar uma sessão de Q&A com o usuário para esclarecer a task:

- Fazer perguntas sobre pontos ambíguos ou faltantes na descrição
- Se a task veio do Jira e a descrição é vaga, perguntar mais
- Se há links do Figma, perguntar se o escopo do design é completo ou parcial
- Agrupar perguntas — não fazer uma por uma

**Registrar todas as perguntas e respostas** — elas serão salvas no `description.md`.

Se a descrição já é clara e completa, informar ao usuário e seguir adiante.

### 6. Criar estrutura da task

Criar a seguinte estrutura em `GDD/tasks/`:

```
GDD/tasks/{cod-da-task}/
├── description.md
└── plan.md
```

**`description.md`** — preencher com:
- Título da task
- Descrição completa (do Jira ou fornecida manualmente)
- Link do Jira (se disponível)
- Link(s) do Figma (se encontrados)
- Tasks semelhantes encontradas no knowledge (apenas os códigos de commit como referência)
- Sessão de Q&A — todas as perguntas feitas e respostas do usuário

**`plan.md`** — criar vazio, será preenchido em etapa posterior.

### 7. Reportar resultado

> ✅ Task `{cod-da-task}` inicializada!
>
> 📄 `GDD/tasks/{cod-da-task}/description.md` — descrição preenchida
> 📋 `GDD/tasks/{cod-da-task}/plan.md` — aguardando planejamento
>
> [Se encontrou contexto no knowledge.md, listar aqui]
> [Se encontrou links do Figma, listar aqui]
