# Update Plan — Sub-skill de Atualização de Plano

> Permite alterar o plano de implementação durante ou antes da implementação, quando surgem mudanças de escopo, descobertas técnicas ou decisões do usuário.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Ler estado atual

Ler os seguintes arquivos:
- `GDD/tasks/{cod-da-task}/description.md` — descrição original da task
- `GDD/tasks/{cod-da-task}/plan.md` — plano atual

Se o plano estiver vazio, informar que não há plano para atualizar e sugerir rodar `plan`.

### 3. Entender a mudança

Perguntar ao usuário **o que mudou**. Possíveis cenários:

- **Mudança de escopo** — o Jira foi atualizado, entraram ou saíram requisitos
- **Descoberta técnica** — durante a implementação, descobriu-se algo que muda a abordagem
- **Decisão do usuário** — o usuário decidiu fazer diferente
- **Feedback da review** — a review identificou problemas que exigem replanejar

### 4. Atualizar o plano

Modificar o `GDD/tasks/{cod-da-task}/plan.md`:
- Manter os passos que não mudaram
- Marcar passos já executados como concluídos (se a implementação já começou)
- Adicionar, remover ou alterar passos conforme a mudança
- Adicionar uma seção `## Histórico de alterações` no final do plano com:

```markdown
## Histórico de alterações

### Atualização {data}
- **Motivo:** {motivo da mudança}
- **O que mudou:** {resumo das alterações no plano}
```

### 5. Revisar plano atualizado

Chamar a sub-skill `review --plan` para validar o plano atualizado contra a descrição.

- Se a descrição também mudou (ex: escopo novo do Jira), atualizar o `description.md` primeiro
- Avaliar o relatório da review e aplicar correções se necessário

### 6. Apresentar plano atualizado

Mostrar ao usuário o plano atualizado com as diferenças destacadas e pedir validação antes de prosseguir.
