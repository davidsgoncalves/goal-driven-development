#!/usr/bin/env python3
"""parse_jira_deps.py — Topo-sort de dependências Jira pra stack mode (v12).

Recebe um JSON via stdin descrevendo tasks e suas dependências `is blocked by`,
detecta ciclos, faz topological sort, e atribui um `stack_parent` por task.

Input (stdin, JSON):
{
  "tasks": {
    "PROJ-101": {"blocked_by": []},
    "PROJ-102": {"blocked_by": ["PROJ-101"]},
    "PROJ-103": {"blocked_by": ["PROJ-101"]},
    "PROJ-104": {"blocked_by": ["PROJ-102", "PROJ-103"]}
  }
}

Tasks em `blocked_by` que não estão em `tasks` são ignoradas silenciosamente
(podem ser blockers fora do escopo da árvore inicializada).

Output (stdout, JSON):
{
  "ok": true,
  "order": ["PROJ-101", "PROJ-102", "PROJ-103", "PROJ-104"],
  "stack": {
    "PROJ-101": {"stack_parent": null, "stack_order": 0, "depth": 0},
    "PROJ-102": {"stack_parent": "PROJ-101", "stack_order": 1, "depth": 1},
    "PROJ-103": {"stack_parent": "PROJ-101", "stack_order": 2, "depth": 1},
    "PROJ-104": {"stack_parent": "PROJ-103", "stack_order": 3, "depth": 2}
  },
  "warnings": []
}

Regras de `stack_parent`:
- Sem `blocked_by` (ou todos blockers fora do escopo) → `stack_parent: null` (sai de main).
- 1 blocker no escopo → `stack_parent` = esse blocker.
- N blockers no escopo → `stack_parent` = o último a aparecer em `order` (o mais
  profundo já materializado). Justificativa: branch precisa de UMA base; pegar
  o último garante que todo o conteúdo dos outros blockers também está presente,
  desde que estejam todos no mesmo lineage. Se NÃO estiverem (DAG bifurcado),
  emite warning — o usuário pode precisar mergear manualmente antes do PR.

Erros:
- Ciclo detectado → exit 2, output JSON com `ok: false` e lista do ciclo.
- Input malformado → exit 1.
"""
from __future__ import annotations

import json
import sys
from typing import Any


def topo_sort(graph: dict[str, list[str]]) -> tuple[list[str], list[str] | None]:
    """Kahn's algorithm. Retorna (ordem, None) ou ([], ciclo) se houver ciclo."""
    in_degree = {node: 0 for node in graph}
    for node, deps in graph.items():
        for dep in deps:
            if dep in in_degree:
                in_degree[node] += 1

    queue = [n for n, deg in in_degree.items() if deg == 0]
    queue.sort()  # ordem estável
    order: list[str] = []

    while queue:
        node = queue.pop(0)
        order.append(node)
        # Pra cada nó que depende de `node`, decrementa in-degree
        for other, deps in graph.items():
            if node in deps:
                in_degree[other] -= 1
                if in_degree[other] == 0:
                    queue.append(other)
                    queue.sort()

    if len(order) != len(graph):
        # ciclo: extrair os nós com in-degree > 0
        remaining = [n for n, deg in in_degree.items() if deg > 0]
        return [], remaining

    return order, None


def find_lineage(node: str, graph: dict[str, list[str]]) -> set[str]:
    """Conjunto de todos os ancestrais de node (transitive closure de blocked_by)."""
    visited: set[str] = set()
    stack = list(graph.get(node, []))
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        stack.extend(graph.get(cur, []))
    return visited


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"invalid JSON: {e}"}))
        return 1

    tasks = payload.get("tasks")
    if not isinstance(tasks, dict):
        print(json.dumps({"ok": False, "error": "missing 'tasks' object"}))
        return 1

    # Normaliza graph: só blockers que estão no escopo das tasks recebidas
    in_scope = set(tasks.keys())
    graph: dict[str, list[str]] = {}
    warnings: list[str] = []

    for cod, meta in tasks.items():
        blocked_by = meta.get("blocked_by", []) if isinstance(meta, dict) else []
        if not isinstance(blocked_by, list):
            warnings.append(f"{cod}: blocked_by não é lista, tratado como vazio")
            blocked_by = []
        in_scope_blockers = [b for b in blocked_by if b in in_scope]
        out_of_scope = [b for b in blocked_by if b not in in_scope]
        if out_of_scope:
            warnings.append(
                f"{cod}: blockers fora do escopo ignorados: {', '.join(out_of_scope)}"
            )
        graph[cod] = in_scope_blockers

    order, cycle = topo_sort(graph)
    if cycle is not None:
        print(json.dumps({
            "ok": False,
            "error": "cycle detected in dependency graph",
            "cycle_nodes": cycle,
        }))
        return 2

    # Atribui stack_parent, stack_order, depth
    depth: dict[str, int] = {}
    stack: dict[str, dict[str, Any]] = {}
    for idx, node in enumerate(order):
        blockers = graph[node]
        if not blockers:
            parent = None
            d = 0
        elif len(blockers) == 1:
            parent = blockers[0]
            d = depth.get(parent, 0) + 1
        else:
            # múltiplos blockers: escolhe o mais tardio no `order` (mais profundo)
            parent = max(blockers, key=lambda b: order.index(b))
            d = depth.get(parent, 0) + 1
            # checar se os outros blockers estão todos no lineage de `parent`
            parent_lineage = find_lineage(parent, graph) | {parent}
            other_blockers = [b for b in blockers if b != parent]
            disjoint = [b for b in other_blockers if b not in parent_lineage]
            if disjoint:
                warnings.append(
                    f"{node}: múltiplos blockers em lineages diferentes ({', '.join(disjoint)} "
                    f"fora de {parent}); branch vai sair de {parent}, mas é provável "
                    "que precise merge manual dos outros antes do PR ficar correto"
                )

        depth[node] = d
        stack[node] = {
            "stack_parent": parent,
            "stack_order": idx,
            "depth": d,
        }

    print(json.dumps({
        "ok": True,
        "order": order,
        "stack": stack,
        "warnings": warnings,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
