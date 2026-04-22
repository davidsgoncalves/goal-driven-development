---
name: learn
description: |
  Transforma uma task executada em conhecimento reutilizável. Analisa a descrição, o plano, os commits e o que realmente aconteceu para extrair aprendizados e registrar no knowledge. Use quando o usuário mencionar: "learn", "aprender", "extrair conhecimento", "registrar aprendizado", ou quando a fase de aprendizado for ativada pelo GOD.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Learn — Sub-skill de Transformação em Conhecimento

> Transforma uma task executada em conhecimento reutilizável. Analisa a descrição, o plano, os commits e o que realmente aconteceu para extrair aprendizados e registrar no knowledge.
>
> Esta skill executa **duas ações em sequência** numa única invocação:
> - **Ação 1** — registra a task em `GOD/knowledge.md` (entrada por task: commits, arquivos, aprendizados).
> - **Ação 2** — registra **regras** generalizáveis em `GOD/learned-patterns.md` (regras escopadas por `geral` / `linguagem` / `projeto`, lidas pelo `implement` após a escrita de código para ajustar pequenos desvios).
>
> A Ação 2 é executada normalmente depois da revisão do PR — o usuário tem feedback próprio e da equipe em mãos. Se o usuário não tem nada a registrar, pula (não força).

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Identificar a task

- Se o contexto da conversa já contém o código da task, usar esse código
- Caso contrário, perguntar ao usuário o código da task (ex: `PROJ-123`)

### 2. Coletar artefatos da task

Ler todos os artefatos disponíveis:

- `GOD/tasks/{cod-da-task}/description.md` — descrição original, links, Q&A
- `GOD/tasks/{cod-da-task}/plan.md` — plano de implementação (incluindo histórico de alterações se houver)

### 3. Analisar commits da task

Identificar todos os commits relacionados à task:

- Buscar commits no git que mencionem o código da task (`git log --all --grep="{cod-da-task}"`)
- Buscar no `GOD/knowledge.md` commits já registrados para esta task (se houver entrada de execução anterior do learn)
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

Atualizar a entrada da task no `GOD/knowledge.md` com o formato completo:

```markdown
### {cod-da-task} — {breve descrição}
- **commits:** {hash1}, {hash2}, ...
- **arquivos principais:** {lista dos arquivos mais relevantes}
- **aprendizados:** {aprendizados extraídos + input do usuário}
```

- Se a entrada já existe (de uma execução anterior do learn), mesclar os novos aprendizados com os existentes
- Se não existe, criar a entrada completa

### 6.1. Garantir existência do `learned-patterns.md`

Verificar se `GOD/learned-patterns.md` existe.

- **Se não existe**, criar com o template canônico:

  ```markdown
  # Learned Patterns — Regras aprendidas nas tasks

  > Regras de estilo, convenções e armadilhas registradas após a revisão de PR de tasks anteriores. Lido pelo `implement` logo após a escrita de código (passo de verificação contra padrões) e escrito pelo `learn` após a revisão do PR.
  >
  > **Escrito apenas pela skill `learn`** — nenhuma outra skill modifica o conteúdo.
  >
  > **Escopos** (cada regra tem um):
  > - `geral` — aplica-se a todos os projetos.
  > - `linguagem: <lang>` — aplica-se a todos os projetos naquela linguagem.
  > - `projeto: <nome>` — aplica-se somente àquele projeto.
  >
  > **Convenção:** adicionar novas regras ao final da lista, numeradas. Não remover, apenas marcar como revogada se necessário (`~~riscado~~` + motivo).

  ---
  ```

- **Se existe**, manter e anexar novas regras no final (próximo passo).

Criação defensiva aqui garante que a skill funcione em instalações legadas que ainda não rodaram o upgrade para v5.

### 6.2. Sessão de Q&A sobre regras (Ação 2)

Esta ação é **separada** da Ação 1 (knowledge.md). A Ação 1 registra o que aconteceu nesta task específica; a Ação 2 extrai **regras generalizáveis** — padrões de estilo, convenções, armadilhas que devem se aplicar a tasks futuras.

Pergunte ao usuário:

> Depois da revisão do PR, você identificou alguma **regra** que deve valer para tasks futuras? (não é um comentário específico desta task — é uma regra generalizável que você quer que o `implement` respeite daqui pra frente)
>
> Exemplos de regras: "handlers internos devem usar prefixo `on*`, não `handle*`", "sempre deixar linha em branco entre setup imperativo e `try`", "não usar Rollbar neste projeto — usar o modelo `Log`".

Se o usuário responder que não tem nada a adicionar, pular para o passo 7.

Se tiver regras, para **cada regra** coletar:

1. **Título curto** (uma linha, descritivo)
2. **Escopo** — perguntar: é `geral`, `linguagem: <qual>`, ou `projeto: <qual>`?
3. **Descrição da regra** — uma descrição direta do que deve ou não ser feito
4. **Por quê** — motivo que permite julgar casos de borda (ex: "preferência consolidada em review", "incidente anterior", "limitação técnica")
5. **Como aplicar** — quando/onde a regra incide. Se o usuário quiser ilustrar, adicionar blocos `Bom` e `Ruim` com exemplos **curtos** da regra (não são exemplos específicos desta task — são ilustrações genéricas da regra)

**O que é uma regra válida:**
- Generalizável — vale em tasks futuras, não só nesta
- Verificável — o `implement` consegue checar contra um diff
- Escopada — tem pelo menos um escopo claro (geral/linguagem/projeto)

**O que NÃO é regra:**
- "Nesta task eu errei X" → vai pra knowledge.md (Ação 1), não aqui
- "O código ficou complicado" → feedback geral, não regra acionável
- "Deveríamos refatorar Y" → é backlog, não regra de estilo

### 6.3. Atualizar `learned-patterns.md`

Para cada regra coletada:

1. Ler o arquivo atual e identificar o **maior número** usado nas regras existentes. A nova regra recebe o próximo número.
2. Anexar no final do arquivo, seguindo o formato:

   ```markdown

   ## N. {título curto}

   **Escopo:** {geral | linguagem: X | projeto: Y}

   {descrição da regra}

   **Por quê:** {motivo}

   **Como aplicar:**

   {instruções de aplicação; opcional: blocos Bom/Ruim}

   ---
   ```

3. **Nunca** reescrever regras anteriores, nem mudar seus números. Regras antigas que ficaram erradas são marcadas com `~~riscado~~` + motivo em linha adicional — não removidas.

### 7. Marcar task como aprendida

Após gravar a entrada no `knowledge.md`, atualizar `GOD/tasks/{cod-da-task}/status.md`:

- `learned`: `true`
- `updated_at`: timestamp ISO 8601 em UTC
- `updated_by`: `learn`
- **Não alterar `phase`** — continua `packed-up` (ou o que estava). Learn é uma ferramenta ortogonal ao fluxo, não uma fase do ciclo.
- Preservar `branch` e `prs` intactos.

### 8. Reportar resultado

> ✅ Knowledge registrado para `{cod-da-task}`!
>
> 📚 Commits: {quantidade} commits registrados
> 📁 Arquivos principais: {lista resumida}
> 💡 Aprendizados: {quantidade} aprendizados extraídos (knowledge.md)
> 📐 Regras novas: {quantidade} regras adicionadas (learned-patterns.md) — ou "nenhuma regra nova" se o usuário não adicionou
>
> O knowledge está disponível em `GOD/knowledge.md` para consulta em tasks futuras.
> As regras estão em `GOD/learned-patterns.md` e serão aplicadas pelo `implement` após a escrita de código.

---

## Guard-rails

- **Esta skill é a única autorizada a escrever em `GOD/knowledge.md` e em `GOD/learned-patterns.md`.** Qualquer atualização a esses arquivos deve passar por aqui, ativada explicitamente pelo usuário.
- **Regras em `learned-patterns.md` nunca são reescritas nem renumeradas.** Regras antigas que ficam incorretas ganham um marcador `~~riscado~~` + motivo. Esta convenção preserva histórico e evita que o `implement` pule regras por mudança de numeração.
