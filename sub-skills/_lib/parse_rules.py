#!/usr/bin/env python3
"""
parse_rules.py — parseia comentários `// rule: BR-X` no diff de uma task.

Usado pelo pack-up (gerar tabela "BRs aplicáveis × anotadas" no PR description)
e pelo review --execution (eixo BR).

Uso:
    python3 parse_rules.py --task PROJ-123 \\
        --branch-base main \\
        [--source-root .] \\
        [--specs-path docs/specs] \\
        [--god-root .] \\
        [--format json|markdown|terminal]

Saída JSON:
{
  "ok": true,
  "task": "PROJ-123",
  "applicable_rules": ["BR-PAYMENTS-001", "BR-PAYMENTS-007"],
  "annotated": {"BR-PAYMENTS-001": ["src/foo.ts:42"], ...},
  "orphaned": ["BR-PAYMENTS-007"],
  "summary": {"total": 2, "annotated": 1, "orphaned": 1}
}

Cross-platform (macOS/Linux/WSL), Python 3.8+ stdlib only.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (
    fail_json, ok_json, read_text, parse_frontmatter, find_god_root, read_config_value
)

RULE_REGEX = re.compile(
    r"""
    (?://|\#|--|/\*|\*)\s*
    rule:\s*
    (?P<id>BR-[A-Z][A-Z0-9_]*-\d+)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def get_diff_files(branch_base, source_root):
    """Lista arquivos modificados desde branch_base usando git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{branch_base}...HEAD"],
            cwd=source_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return [Path(source_root) / line.strip()
                for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return []


def scan_for_rules(files):
    """Varre arquivos por `// rule: BR-X`. Retorna {id: [path:linha]}."""
    annotated = {}
    for path in files:
        if not path.exists() or not path.is_file():
            continue
        text = read_text(path)
        if "rule:" not in text.lower():
            continue
        for line_num, line in enumerate(text.splitlines(), start=1):
            for match in RULE_REGEX.finditer(line):
                rid = match.group("id").upper()
                annotated.setdefault(rid, []).append(f"{path}:{line_num}")
    return annotated


def render_markdown(payload):
    if not payload["applicable_rules"]:
        return "_(spec sem `applicable_rules` ou domains_path desativado — sem tabela de BRs)_"
    lines = ["| BR | Status | Anotações no código |", "|----|--------|---------------------|"]
    for rid in payload["applicable_rules"]:
        if rid in payload["annotated"]:
            paths = ", ".join(payload["annotated"][rid])
            lines.append(f"| {rid} | ✅ | {paths} |")
        else:
            lines.append(f"| {rid} | ⚠️ | (declarada aplicável mas sem anotação no diff) |")
    s = payload["summary"]
    lines.append("")
    lines.append(f"**Resumo:** {s['total']} BRs aplicáveis · {s['annotated']} anotadas · {s['orphaned']} órfã(s)")
    return "\n".join(lines)


def render_terminal(payload):
    lines = [f"📜 BRs — {payload['task']}", ""]
    if not payload["applicable_rules"]:
        lines.append("  (sem applicable_rules ou domains_path desativado)")
    else:
        for rid in payload["applicable_rules"]:
            if rid in payload["annotated"]:
                lines.append(f"  ✅ {rid}  →  {', '.join(payload['annotated'][rid])}")
            else:
                lines.append(f"  ⚠️  {rid}  →  sem anotação no diff")
        s = payload["summary"]
        lines.extend(["", f"  Total: {s['total']} · Anotadas: {s['annotated']} · Órfãs: {s['orphaned']}"])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parseia // rule: BR-X no diff.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--branch-base", required=True)
    parser.add_argument("--source-root", default=".")
    parser.add_argument("--specs-path", default="docs/specs")
    parser.add_argument("--god-root", default=".")
    parser.add_argument("--format", choices=["json", "markdown", "terminal"], default="json")
    args = parser.parse_args()

    god_root = Path(args.god_root).resolve()
    specs_path = Path(args.specs_path)
    if not specs_path.is_absolute():
        specs_path = (god_root / specs_path).resolve()
    source_root = Path(args.source_root).resolve()

    spec_path = specs_path / "tasks" / f"{args.task}.md"
    applicable = []
    if spec_path.exists():
        spec_text = read_text(spec_path)
        fm, _ = parse_frontmatter(spec_text)
        applicable = fm.get("applicable_rules") or []
        if not isinstance(applicable, list):
            applicable = []

    files = get_diff_files(args.branch_base, source_root)
    annotated = scan_for_rules(files)

    declared = set(applicable)
    annotated_set = set(annotated.keys()) & declared
    orphaned = sorted(declared - annotated_set)

    payload = {
        "ok": True,
        "task": args.task,
        "applicable_rules": list(applicable),
        "annotated": {k: v for k, v in annotated.items() if k in declared},
        "orphaned": orphaned,
        "summary": {
            "total": len(declared),
            "annotated": len(annotated_set),
            "orphaned": len(orphaned),
        },
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(payload))
    else:
        print(render_terminal(payload))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fail_json(f"parse_rules failed: {e.__class__.__name__}: {e}")
