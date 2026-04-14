# Implement — Sub-skill de Implementação

> Executa o plano de implementação da task, criando subagents para tasks complexas ou executando diretamente para tasks simples. Suporta flag `--code-like-me` para implementação cirúrgica.

## Flags

- `--code-like-me` — Ativa a sub-skill `code-like-me` para garantir que o código implementado siga exatamente os padrões e convenções do projeto existente. Quando ativa, cada passo de implementação deve seguir as diretrizes da skill `code-like-me`.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Ler o plano

Ler o arquivo `GDD/tasks/{cod-da-task}/plan.md` para obter o plano de implementação.

- Se o plano estiver vazio, informar o usuário que precisa rodar a skill `plan` antes
- Se o plano existir, analisar sua estrutura e complexidade

### 3. Carregar contexto visual (Figma)

Ler o `GDD/tasks/{cod-da-task}/description.md` e verificar se há links do Figma.

Se houver links do Figma:
- Acessar o Figma via MCP Figma (`get_design_context`) para cada link
- Usar o design como referência visual durante a implementação
- Cada subagent que implementar UI deve receber o contexto do Figma relevante ao seu escopo

### 4. Avaliar complexidade e decidir estratégia

Analisar o plano e decidir a estratégia de execução:

**Task simples (sem divisão de sub-tasks no plano):**
- Executar a implementação diretamente, seguindo os passos do plano na ordem

**Task complexa (com múltiplas sub-tasks no plano):**
- Criar um subagent (via Agent tool) para cada sub-task independente
- Sub-tasks que dependem umas das outras devem ser executadas sequencialmente
- Sub-tasks independentes podem ser executadas em paralelo
- Cada subagent recebe:
  - O contexto completo da task (descrição + plano)
  - Apenas o escopo da sua sub-task específica
  - As convenções do projeto (de `CLAUDE.md`, `ARCHITECTURE.md`, etc.)

### 5. Implementar

**Sem flag `--code-like-me`:**
- Seguir o plano de implementação passo a passo
- Respeitar as convenções do projeto encontradas nos arquivos de configuração

**Com flag `--code-like-me`:**
- Aplicar todas as diretrizes da sub-skill `code-like-me` durante a implementação
- Cada mudança deve ser cirúrgica — mínimo impacto, máxima aderência ao código existente
- Encontrar analogias no código existente antes de criar algo novo
- Verificar a cadeia completa (frontend → API → backend → banco) quando aplicável

### 6. Verificação pós-implementação

Após implementar:
- Ler os arquivos alterados para verificar consistência
- Rodar type-check se o projeto usar TypeScript
- Rodar linter se disponível
- Verificar se todos os passos do plano foram executados

### 7. Reportar resultado

Apresentar ao usuário:
- Resumo do que foi implementado
- Arquivos criados ou modificados
- Se usou subagents, listar o que cada um fez
- Pendências ou pontos de atenção (se houver)
