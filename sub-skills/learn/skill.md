# Learn — Sub-skill de Transformação em Conhecimento

> Transforma uma task executada em conhecimento reutilizável. Analisa a descrição, o plano, os commits e o que realmente aconteceu para extrair aprendizados e registrar no knowledge.

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Coletar artefatos da task

Ler todos os artefatos disponíveis:

- `GDD/tasks/{cod-da-task}/description.md` — descrição original, links, Q&A
- `GDD/tasks/{cod-da-task}/plan.md` — plano de implementação (incluindo histórico de alterações se houver)

### 3. Analisar commits da task

Identificar todos os commits relacionados à task:

- Buscar commits no git que mencionem o código da task (`git log --all --grep="{cod-da-task}"`)
- Buscar no `GDD/knowledge.md` commits já registrados para esta task (se houver entrada de execução anterior do learn)
- Para cada commit encontrado, analisar o diff (`git diff {hash}~1..{hash}`)

### 4. Extrair aprendizados

Analisar o histórico completo da task e extrair:

**Arquivos principais:**
- Quais arquivos foram mais impactados
- Quais arquivos são centrais para entender a mudança

**Aprendizados — o que vale registrar:**
- Decisões técnicas tomadas e o porquê (ex: "usamos X em vez de Y porque Z")
- Armadilhas encontradas durante a implementação (ex: "o campo X precisa de migração antes de usar")
- Padrões descobertos ou confirmados (ex: "formulários neste projeto sempre usam Hook Form + Zod")
- Desvios do plano original e o motivo (comparar plan.md com o que foi implementado)
- Dependências ou pré-requisitos não óbvios

**O que NÃO registrar:**
- Detalhes de implementação que estão no código (o código fala por si)
- Coisas óbvias deriváveis dos arquivos do projeto
- Informações efêmeras que não ajudam tasks futuras

### 5. Sessão de Q&A com o usuário

Perguntar ao usuário se há aprendizados adicionais que não são visíveis no código:

- "Houve algo inesperado durante a implementação?"
- "Alguma decisão foi tomada por motivo externo (performance, prazo, requisito de negócio)?"
- "Algo que você faria diferente na próxima vez?"

Se o usuário não tiver nada a acrescentar, seguir adiante.

### 6. Atualizar knowledge

Atualizar a entrada da task no `GDD/knowledge.md` com o formato completo:

```markdown
### {cod-da-task} — {breve descrição}
- **commits:** {hash1}, {hash2}, ...
- **arquivos principais:** {lista dos arquivos mais relevantes}
- **aprendizados:** {aprendizados extraídos + input do usuário}
```

- Se a entrada já existe (de uma execução anterior do learn), mesclar os novos aprendizados com os existentes
- Se não existe, criar a entrada completa

### 7. Reportar resultado

> ✅ Knowledge registrado para `{cod-da-task}`!
>
> 📚 Commits: {quantidade} commits registrados
> 📁 Arquivos principais: {lista resumida}
> 💡 Aprendizados: {quantidade} aprendizados extraídos
>
> O knowledge está disponível em `GDD/knowledge.md` para consulta em tasks futuras.
