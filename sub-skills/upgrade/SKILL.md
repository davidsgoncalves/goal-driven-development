---
name: upgrade
description: |
  Detecta a versão instalada do GOD no projeto do usuário e aplica as migrações necessárias até a versão atual. Expansível — cada bump de versão adiciona um novo arquivo em `migrations/`. Use quando o usuário mencionar: "upgrade", "migrar", "atualizar god", "upgrade god", "v1 para v2", ou quando a orquestradora detectar uma instalação de versão antiga.
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Upgrade — Sub-skill de Migração de Versão

> Detecta a versão instalada do GOD no projeto do usuário e aplica as migrações necessárias em cadeia até a versão atual.

## Versão atual

**current_version: v3**

> ⚠️ Ao criar uma nova versão (v3, v4, etc.), atualize este campo e adicione o arquivo de migração correspondente em `migrations/`.

## Migrações disponíveis

| De → Para | Arquivo |
|-----------|---------|
| v1 → v2 | `migrations/v1-to-v2.md` |
| v2 → v3 | `migrations/v2-to-v3.md` |

> Para adicionar uma nova versão no futuro, crie `migrations/vN-to-vN+1.md`, adicione a linha nesta tabela e bump `current_version` acima.

---

## Instruções

Quando o usuário invocar esta skill, execute os seguintes passos **na ordem**:

### 1. Detectar versão instalada

Verificar o arquivo `GOD/VERSION` no projeto do usuário:

- **Se `GOD/` não existe:** informar que não há instalação para migrar e sugerir rodar `install`. Encerrar.
- **Se `GOD/VERSION` não existe:** a instalação é **v1** (versão anterior ao VERSION file). Assumir `current = v1`.
- **Se `GOD/VERSION` existe:** ler o conteúdo (uma linha, ex: `v2`). Usar esse valor como `current`.

### 2. Determinar cadeia de migrações

Comparar `current` (versão instalada) com `target` (versão atual, ver topo deste arquivo).

- Se `current == target`: informar que já está na versão atual e encerrar.
- Se `current < target`: montar a lista ordenada de migrações a aplicar, consultando a tabela "Migrações disponíveis".
  - Exemplo: se `current = v1` e `target = v3`, aplicar em sequência: `v1-to-v2`, depois `v2-to-v3`.
- Se `current > target`: instalação está numa versão posterior à suportada (provavelmente erro de configuração). Alertar o usuário e encerrar sem alterar nada.

### 3. Confirmar com o usuário

Antes de executar qualquer migração, mostrar ao usuário:

```
🔄 Upgrade do GOD detectado!

Versão instalada: {current}
Versão atual:     {target}

Migrações a aplicar:
  1. v1 → v2 — {resumo curto da migração 1}
  2. v2 → v3 — {resumo curto da migração 2}
  ...

As migrações são aplicadas em cadeia e preservam os valores que você já configurou no projeto (patterns, hooks, knowledge, tasks). Arquivos antigos que não existem na versão nova são removidos apenas após confirmação.

Deseja prosseguir? (sim / não)
```

- Se o usuário responder **sim**: prosseguir para o passo 4.
- Se responder **não**: encerrar sem alterar nada.

### 4. Aplicar migrações em ordem

Para cada migração na cadeia (na ordem determinada no passo 2):

1. Ler o arquivo de instruções correspondente (`sub-skills/upgrade/migrations/vX-to-vY.md`)
2. Executar as instruções **passo a passo**, na ordem em que aparecem
3. Ao final da migração, atualizar `GOD/VERSION` com o novo valor (`vY`)
4. Relatar ao usuário o que foi feito nessa migração

**Se uma migração falhar no meio:**
- Parar imediatamente
- Relatar o que já foi aplicado e o que não foi
- Não prosseguir para a próxima migração
- Orientar o usuário a corrigir manualmente ou restaurar o estado anterior via git

### 5. Validação final

Após aplicar todas as migrações:

1. Verificar que `GOD/VERSION` contém o valor `target`
2. Verificar que os arquivos esperados para a versão atual existem (listados no último arquivo de migração aplicado)
3. Executar uma leitura sanity-check em cada arquivo gerado para detectar templates mal renderizados

### 6. Reportar resultado

```
✅ Upgrade concluído!

{current} → {target}

Migrações aplicadas:
  ✓ v1 → v2 — {resumo}
  ✓ v2 → v3 — {resumo}

Arquivos criados/transformados:
  - GOD/VERSION ({target})
  - GOD/patterns.md (migrado de pack-up-instructions.md)
  - GOD/hooks.md (criado com slots default)
  - ...

Arquivos removidos (com sua confirmação):
  - GOD/pack-up-instructions.md

📋 Próximos passos:
- Revise `GOD/patterns.md` e `GOD/hooks.md` — migrações preservam valores mas você pode querer ajustar manualmente.
- {orientações específicas da última migração}
```

---

## Guard-rails

- **Esta skill nunca escreve em `GOD/knowledge.md`.** Migrações podem reorganizar o arquivo estruturalmente se necessário, mas não adicionam nem removem conhecimento (entradas de tasks).
- **Esta skill não sobrescreve valores do usuário silenciosamente.** Sempre preserva o que o usuário configurou (padrões, hooks customizados, descrições de tasks, knowledge) ao transformar de uma versão pra outra. Se um campo não puder ser migrado automaticamente, pergunta ao usuário.
- **Esta skill não deleta arquivos sem confirmação.** Arquivos antigos que foram substituídos (ex: `pack-up-instructions.md` em v2) são removidos apenas após confirmação explícita do usuário — ou mantidos com sufixo `.bak` se o usuário preferir.
- **Migrações são idempotentes quando possível.** Rodar a skill duas vezes na mesma versão é seguro (detecta que está atualizado e encerra).

---

## Como adicionar uma nova migração no futuro (para desenvolvedores do GOD)

1. Criar `migrations/vN-to-vN+1.md` com as instruções passo a passo da transformação
2. Incluir no topo do arquivo:
   - **Objetivo:** o que essa migração resolve
   - **Arquivos afetados:** lista de arquivos criados, transformados, removidos
   - **Riscos:** casos em que a migração pode falhar e como lidar
3. Adicionar a linha correspondente na tabela "Migrações disponíveis" deste SKILL.md
4. Atualizar `current_version` no topo deste SKILL.md
5. Atualizar `install/SKILL.md` para criar a estrutura da nova versão (e checar se já está instalado).
