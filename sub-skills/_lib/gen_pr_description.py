#!/usr/bin/env python3
"""
gen_pr_description.py — monta o markdown do PR description a partir de JSON.

Substitui geração linha-a-linha que pack-up fazia via LLM. Recebe um JSON
estruturado e cospe markdown pronto pra `gh pr create --body`.

Uso:
    python3 gen_pr_description.py --input contexto.json [--output -]

Onde contexto.json é tipo:
{
  "task": "PROJ-123",
  "title": "Adicionar campo phone",
  "summary": "Adiciona...",
  "spec_path": "docs/specs/tasks/PROJ-123.md",
  "spec_version_delivered": 3,
  "changelog_path": "docs/specs/tasks/PROJ-123-changelog.md",   // opcional
  "reqs_covered": ["REQ-001", "REQ-002"],
  "coverage_markdown": "...",      // saída de parse_coverage --format markdown
  "rules_markdown": "...",         // saída de parse_rules --format markdown (opcional)
  "extra_sections": [{"title": "Notas", "body": "..."}]   // opcional
}

Saída: markdown completo no stdout (ou arquivo via --output).
"""

import argparse
import json
import sys
from pathlib import Path


def render(ctx):
    parts = []

    # Header / sumário.
    summary = ctx.get("summary", "").strip()
    if summary:
        parts.append(summary)
        parts.append("")

    # Bloco da spec.
    spec_path = ctx.get("spec_path")
    if spec_path:
        parts.append("---")
        parts.append("")
        version = ctx.get("spec_version_delivered")
        version_str = f" (entregue em v{version})" if version else ""
        parts.append(f"📐 **Spec:** `{spec_path}`{version_str}")
        parts.append("")
        reqs = ctx.get("reqs_covered") or []
        if reqs:
            parts.append(f"REQs cobertos: {', '.join(reqs)}")
            parts.append("")
        changelog = ctx.get("changelog_path")
        if changelog:
            parts.append(f"📜 **Mudanças de escopo durante a task:** `{changelog}`")
            parts.append("")

    # Tabela de cobertura.
    cov = (ctx.get("coverage_markdown") or "").strip()
    if cov:
        parts.append("📊 **Cobertura de ACs**")
        parts.append("")
        parts.append(cov)
        parts.append("")

    # Tabela de BRs.
    rules = (ctx.get("rules_markdown") or "").strip()
    if rules and not rules.startswith("_("):  # ignora placeholder vazio
        parts.append("📜 **BRs aplicáveis × anotadas**")
        parts.append("")
        parts.append(rules)
        parts.append("")

    # Seções extras.
    for extra in ctx.get("extra_sections") or []:
        title = extra.get("title", "").strip()
        body = extra.get("body", "").strip()
        if title and body:
            parts.append(f"## {title}")
            parts.append("")
            parts.append(body)
            parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Gera markdown do PR description.")
    parser.add_argument("--input", required=True,
                        help="JSON de entrada (path ou '-' pra stdin)")
    parser.add_argument("--output", default="-",
                        help="Path de saída ('-' = stdout)")
    args = parser.parse_args()

    if args.input == "-":
        ctx = json.load(sys.stdin)
    else:
        ctx = json.loads(Path(args.input).read_text(encoding="utf-8"))

    md = render(ctx)

    if args.output == "-":
        sys.stdout.write(md)
    else:
        Path(args.output).write_text(md, encoding="utf-8")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[error] gen_pr_description failed: {e.__class__.__name__}: {e}\n")
        sys.exit(1)
