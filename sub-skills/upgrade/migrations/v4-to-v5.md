# Migração v4 → v5

## Objetivo

A v5 introduz **`GOD/learned-patterns.md`** — um registro de **regras** generalizáveis (escopadas por `geral`, `linguagem: <lang>` ou `projeto: <nome>`) que são:

- **Escritas pela skill `learn`** após a revisão do PR, numa segunda ação (a primeira continua sendo a entrada em `knowledge.md`).
- **Lidas pela skill `implement`** num novo passo 6.5 (após a escrita de código), filtradas pelo escopo aplicável ao diff, com ajuste automático de desvios mecânicos (formatação, nomenclatura simples) e pergunta ao usuário para casos ambíguos.

A separação entre `knowledge.md` (entrada por task) e `learned-patterns.md` (regras generalizáveis) existe porque elas atendem a fluxos diferentes: `knowledge` é consultado pelo `init`/`plan` para reaproveitar decisões de tasks parecidas; `learned-patterns` é aplicado no loop de escrita de código, pegando desvios pequenos antes do PR.

## Arquivos afetados

**Atualizado:**
- `GOD/VERSION` — conteúdo muda de `v4` para `v5`

**Criado (novo):**
- `GOD/learned-patterns.md` — arquivo vazio com template canônico. A skill `learn` preenche ao longo do tempo. Se um arquivo com nome similar já existir (`learned-patters.md` — typo sem o "n"), é renomeado preservando conteúdo.

**Inalterados (nenhuma reescrita automática):**
- `GOD/knowledge.md`
- `GOD/patterns.md`
- `GOD/hooks.md`
- `GOD/tasks/` (todas as tasks, `status.md`, `description.md`, `plan.md`, `changelog.md`)
- `GOD/tasks/.archived/` (se existir)

**Mudanças de contrato (não de arquivos):**
- `learn` ganha Ação 2 (escrita em `learned-patterns.md`) — executada na mesma invocação, após a Ação 1 (knowledge.md).
- `implement` ganha passo 6.5 (verificação contra `learned-patterns.md`) — roda por padrão; flag `--skip-patterns-check` desativa.
- Guard-rail estendido: `learn` passa a ser o único escritor também de `learned-patterns.md`. `install` e `upgrade` só criam o arquivo vazio; `implement` só lê (e cria defensivamente o arquivo vazio se faltar, sem escrever regras).

## Riscos conhecidos

- **Nenhum risco de perda de dados.** A migração não toca em tasks, knowledge, patterns nem hooks.
- **Rename do arquivo com typo (`learned-patters.md` → `learned-patterns.md`) preserva conteúdo.** Se por algum motivo os dois arquivos existirem simultaneamente (correto + typo), a migração **não mescla**: aborta e pede intervenção manual do usuário, para não perder regras.
- **Tasks antigas não disparam verificação automática retroativa.** O passo 6.5 do `implement` roda apenas em execuções futuras — implementações já finalizadas (em `phase: implemented` ou `packed-up`) não são re-verificadas.

---

## Passos da migração

### 1. Verificar pré-condições

- Confirmar que `GOD/VERSION` existe e contém `v4`.
- Se não existir ou estiver em versão anterior, abortar — o usuário deve rodar as migrações anteriores primeiro.

### 2. Resolver nome do arquivo `learned-patterns.md`

Verificar no diretório `GOD/`:

1. **Nenhum arquivo existe** (`learned-patterns.md` ausente, `learned-patters.md` ausente):
   - Criar `GOD/learned-patterns.md` com o template canônico (ver passo 3 abaixo).

2. **Apenas `learned-patterns.md` existe** (nome canônico, já correto):
   - Manter como está. Não sobrescrever nem alterar conteúdo.

3. **Apenas `learned-patters.md` existe** (typo — falta o "n"):
   - Renomear para `learned-patterns.md` preservando conteúdo exato. Usar `git mv` se o repo rastreia o arquivo, ou `mv` caso contrário.
   - Informar ao usuário no relatório final que o rename aconteceu.

4. **Ambos existem** (cenário patológico):
   - **Abortar a migração inteira.** Relatar ao usuário e pedir intervenção manual: "Detectei `learned-patterns.md` e `learned-patters.md` simultaneamente. Mescle os arquivos manualmente antes de rodar o upgrade novamente."

### 3. Template canônico do `learned-patterns.md`

Quando for criar o arquivo (caso 1 do passo 2), usar exatamente:

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

### 4. Atualizar VERSION

Sobrescrever o conteúdo de `GOD/VERSION` com:

```
v5
```

### 5. Relatório final

```
✅ Migração v4 → v5 concluída!

VERSION atualizado: v5

Arquivo criado/ajustado:
  - GOD/learned-patterns.md ({criado vazio | renomeado de learned-patters.md | já existia})

Novidades disponíveis:
  📐 learned-patterns.md   — regras generalizáveis escopadas (geral/linguagem/projeto)
  📝 learn (Ação 2)        — após registrar knowledge, pergunta quais regras viraram padrão
  🔍 implement (passo 6.5) — após escrever código, checa o diff contra regras aplicáveis e ajusta automaticamente (flag --skip-patterns-check desativa)

Fluxo típico:
  1. implement escreve código
  2. passo 6.5 carrega learned-patterns.md, filtra por linguagem+projeto, ajusta pequenos desvios
  3. pack-up entrega PR
  4. após revisão do PR (próprio + equipe), user roda learn
  5. Ação 1 escreve knowledge.md
  6. Ação 2 pergunta: "que regra virou padrão pra tasks futuras?" e anexa em learned-patterns.md
  7. próxima task aproveita a nova regra no passo 6.5

Tasks existentes não foram alteradas. A próxima execução de `implement` (em qualquer task) passa a rodar o passo 6.5 automaticamente.
```
