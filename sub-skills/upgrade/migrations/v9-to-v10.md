# Migração v9 → v10

> **Nota histórica (v11):** esta migration foi escrita retrospectivamente em v11 pra fechar o gap entre v8 e v10 — quando v10 foi entregue, o documento não foi criado. Ela descreve a entrega original da v10 (architecture advisor + domain rules). Tudo aqui continua válido em v11 — a v11 só mexeu na ordem `init`/`spec`, não no advisor nem nas BRs.

## Objetivo

A v10 introduz **Architecture advisor + Domain rules** — artefatos opcionais e configuráveis pra elevar a spec/plan/implement a conversar com princípios duradouros do projeto e regras de negócio por domínio, sem virar constitution rígida.

Três artefatos opcionais, ativados via `GOD/config.md`:

- **`principles_path`** (default vazio = desativado) — bullets curtos de princípios duradouros do projeto. `plan` lê e gera bloco "Considerações arquiteturais" sinalizando desvios sem bloquear.
- **`architecture_path`** (default vazio = desativado) — padrões "preferidos mas negociáveis". Lido junto com principles. `plan` aceita flags `--skip-architecture`, `--refactor`, `--preserve` pra modular tom.
- **`domains_path`** (default vazio = desativado) — pasta com arquivos `<dominio>.md` declarando BRs (regras de negócio). IDs derivados do `domain:` do frontmatter (ex: `domain: payments` → `BR-PAYMENTS-NNN`). Agnóstico ao projeto — GOD nunca prescreve nome de domínio.

Cadeia de uso:

1. **`spec`** sugere `applicable_rules` no frontmatter da spec baseado em description (heurística + confirmação do usuário).
2. **`implement`** sugere comentário `// rule: BR-X — descrição` no código onde a invariante é enforced.
3. **`pack-up`** injeta tabela "BRs aplicáveis × anotadas" no PR description (similar à matriz de cobertura AC × validação da v8).

Mudanças estruturais:

- **`config.md` ganha 3 campos opcionais** — `principles_path`, `architecture_path`, `domains_path`. Sem valores, advisor + BRs ficam desativados (retrocompat total).
- **`install` pergunta se quer ativar os 3 artefatos** — cria templates vazios quando o usuário aceita.
- **`spec` passo 4.5 (BRs aplicáveis)** — lê `domains_path`, aplica heurística de relevância contra input bruto + Jira/Figma, sugere BRs ao usuário. Confirmadas vão pro frontmatter (`applicable_rules: [BR-PAYMENTS-001, ...]`).
- **`plan` lê principles + architecture** — gera bloco "Considerações arquiteturais" no plan.md sinalizando desvios. Flags modulam tom (`--skip-architecture` pula, `--refactor` apresenta como oportunidade, `--preserve` exige justificativa explícita).
- **`implement` passo 5.6 (anotações `// rule:`)** — pra cada BR em `applicable_rules`, sugere anotação no código onde a invariante é enforced.
- **`pack-up` passo 4.6 (tabela BRs)** — chama parser de `// rule:` no diff, gera tabela "BRs aplicáveis × anotadas" no PR. Órfãs viram alerta visual, não bloqueio.

## Arquivos afetados

**Atualizado:**
- `GOD/VERSION` — conteúdo muda de `v9` para `v10`
- `GOD/config.md` — ganha 3 linhas opcionais (paths). Default: vazias.

**Inalterados (nenhuma reescrita automática):**
- `GOD/knowledge.md`
- `GOD/patterns.md`
- `GOD/learned-patterns.md`
- `GOD/hooks.md`
- `GOD/tasks/` (todas as tasks v9 — `status.md`, `plan.md`, `coverage.md`, `changelog.md`)
- `GOD/tasks/.archived/` (se existir)
- `<specs_path>/tasks/*.md` (specs existentes — sem `applicable_rules` no frontmatter)

**Novo (criado sob demanda, não pela migração):**
- `GOD/principles.md` — apenas se usuário aceitar ativar advisor durante a migração ou rodar `install` de novo.
- `GOD/architecture.md` — idem.
- `<specs_path>/domains/` — pasta criada com `<dominio>.md` quando usuário ativar BRs.

**Mudanças de contrato (não de arquivos):**
- 3 paths opcionais em `config.md`.
- `spec` passo 4.5 ativo quando `domains_path` configurado.
- `plan` lê advisor quando `principles_path`/`architecture_path` configurados.
- `implement` sugere `// rule:` quando spec tem `applicable_rules`.
- `pack-up` injeta tabela de BRs quando alguma BR está aplicável.

## Riscos conhecidos

- **Quem não ativar nada continua intocado.** Paths vazios = advisor e BRs desativados. Retrocompat 100% — fluxo da v9 segue idêntico.
- **Tasks v9 sem `applicable_rules` no frontmatter** — `implement` e `pack-up` tratam como "nenhuma BR aplicável" e pulam tabela silenciosamente.
- **Especs v9 com `applicable_rules` adicionado retroativamente** — usuário pode editar manualmente o frontmatter de uma spec v9 pra adicionar BRs; `implement` da próxima execução vai sugerir anotações.
- **Heurística de sugestão de BRs pode dar falso positivo** — `spec` apresenta lista pra confirmação do usuário, nunca aplica direto. Falso positivo treina dev a ignorar — heurística é deliberadamente conservadora.
- **Manutenção de domains exige dono** — sem dono, fica desatualizado. Issue futura (`audit-rules`) sinaliza divergências.
- **Comentário `// rule:` em todo lugar polui código** — diretriz: anotar só onde a regra é *enforced*, não em cada toque. Documentado no `implement`.
- **Nenhum risco de perda de dados.** Migração só atualiza VERSION e adiciona seções opcionais em `config.md`.

---

## Passos da migração

### 1. Verificar pré-condições

- Confirmar que `GOD/VERSION` existe e contém `v9`.
- Se não existir ou estiver em versão anterior, abortar — o usuário deve rodar as migrações anteriores primeiro.

### 2. Atualizar VERSION

Sobrescrever o conteúdo de `GOD/VERSION` com:

```
v10
```

### 3. Atualizar `config.md` (sem ativar nada por default)

Adicionar 3 seções opcionais ao final de `GOD/config.md` (caso ainda não existam):

```markdown
## principles_path

(vazio = desativado. Caminho relativo ou absoluto pra arquivo de princípios duradouros. Ex: `GOD/principles.md`)

## architecture_path

(vazio = desativado. Caminho relativo ou absoluto pra arquivo de padrões arquiteturais preferidos. Ex: `GOD/architecture.md`)

## domains_path

(vazio = desativado. Caminho relativo ou absoluto pra pasta com arquivos `<dominio>.md` declarando BRs. Ex: `<specs_path>/domains/`)
```

Sem valores preenchidos, advisor + BRs ficam desativados.

### 4. Perguntar ao usuário se quer ativar agora (opcional)

```
🎯 GOD v10 introduz 3 artefatos opcionais:

  1. principles.md      — princípios duradouros do projeto (plan gera "Considerações arquiteturais")
  2. architecture.md    — padrões preferidos mas negociáveis
  3. domains/<X>.md     — regras de negócio (BRs) por domínio, agnóstico

Ativar algum agora? (Pode deixar pra depois — edite config.md ou rode `install` de novo a qualquer momento.)

  [a] principles + architecture (advisor de arquitetura)
  [b] domains/ (BRs)
  [c] todos os 3
  [d] nada (deixa pra depois)
```

Aplicar conforme escolha:
- (a): cria `GOD/principles.md` e `GOD/architecture.md` com template mínimo, popula paths em `config.md`.
- (b): cria `<specs_path>/domains/` com `<dominio>-exemplo.md`, popula `domains_path` em `config.md`.
- (c): combina (a) + (b).
- (d): nada — paths permanecem vazios.

### 5. Não tocar em tasks ativas

A migração **deliberadamente não modifica** nenhum arquivo dentro de `GOD/tasks/{cod}/` ou specs existentes. As mudanças (advisor no plan, BRs no spec/implement/pack-up) só atuam em execuções futuras quando os paths estiverem populados.

### 6. Relatório final

```
✅ Migração v9 → v10 concluída!

VERSION atualizado: v10
config.md: 3 seções opcionais adicionadas ({preenchidas / vazias})

{Se usuário ativou advisor:}
  ✅ GOD/principles.md criado (template mínimo)
  ✅ GOD/architecture.md criado (template mínimo)
  ✅ config.md com principles_path e architecture_path populados

{Se usuário ativou BRs:}
  ✅ <specs_path>/domains/ criado com exemplo
  ✅ config.md com domains_path populado

Novidades disponíveis:
  🎯 plan                 — lê principles/architecture, gera "Considerações arquiteturais"
  📜 spec passo 4.5       — sugere BRs aplicáveis (quando domains/ ativado)
  📝 implement passo 5.6  — sugere `// rule: BR-X` no código
  📊 pack-up passo 4.6    — injeta tabela "BRs aplicáveis × anotadas" no PR

Tasks em andamento continuam compatíveis. Advisor + BRs só atuam em execuções futuras
quando os paths em config.md estiverem populados — sem isso, fluxo segue idêntico ao v9.

Próximos passos sugeridos:
  - Se ativou advisor: preencha `GOD/principles.md` com bullets curtos dos princípios do projeto.
  - Se ativou BRs: crie arquivos `<dominio>.md` em <specs_path>/domains/ pra declarar BRs do seu domínio.
  - Pra ativar depois: edite `GOD/config.md` ou rode `install` de novo.
```
