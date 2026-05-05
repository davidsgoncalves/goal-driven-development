#!/usr/bin/env python3
"""
freshness_check.py — compara spec_version atual com spec_version_consumed da task.

Usado por plan e implement no início pra detectar drift sem que o LLM precise
ler dois arquivos e raciocinar sobre eles.

Uso:
    python3 freshness_check.py --task PROJ-123 \\
        [--specs-path docs/specs] [--god-root .]

Saída JSON:
{
  "ok": true,
  "task": "PROJ-123",
  "spec_version_current": 3,
  "spec_version_consumed": 1,
  "drift": true,
  "delta": 2,
  "changelog_entries": [
    {"version": 2, "summary": "...", "affected_acs": [...]},
    {"version": 3, "summary": "...", "affected_acs": [...]}
  ]
}

Exit code: 0 sempre que conseguir computar (mesmo com drift). Falha do script
real (arquivo ausente etc) → exit 1.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import fail_json, read_text, parse_frontmatter

CHANGELOG_ENTRY_RE = re.compile(
    r"^##\s*v(\d+)\s*—\s*(.+?)$(.*?)(?=^##\s*v\d+\s*—|\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_changelog(changelog_text):
    """Parser simples do {cod}-changelog.md."""
    entries = []
    for m in CHANGELOG_ENTRY_RE.finditer(changelog_text):
        version = int(m.group(1))
        timestamp = m.group(2).strip()
        body = m.group(3)

        # Tenta extrair "Resumo:" em uma linha.
        resumo_match = re.search(r"\*\*Resumo:\*\*\s*(.+?)$", body, re.MULTILINE)
        resumo = resumo_match.group(1).strip() if resumo_match else ""

        # ACs afetados (na seção "Impacto na execução" ou "Deltas").
        affected = re.findall(r"AC-\d+\.\d+", body)
        # Dedup mantendo ordem.
        seen = set()
        affected_unique = []
        for a in affected:
            if a not in seen:
                seen.add(a)
                affected_unique.append(a)

        entries.append({
            "version": version,
            "timestamp": timestamp,
            "summary": resumo,
            "affected_acs": affected_unique,
        })
    return sorted(entries, key=lambda e: e["version"])


def main():
    parser = argparse.ArgumentParser(description="Checa drift entre spec e status.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--specs-path", default="docs/specs")
    parser.add_argument("--god-root", default=".")
    args = parser.parse_args()

    god_root = Path(args.god_root).resolve()
    specs_path = Path(args.specs_path)
    if not specs_path.is_absolute():
        specs_path = (god_root / specs_path).resolve()

    status_path = god_root / "GOD" / "tasks" / args.task / "status.md"
    spec_path = specs_path / "tasks" / f"{args.task}.md"
    changelog_path = specs_path / "tasks" / f"{args.task}-changelog.md"

    if not status_path.exists():
        fail_json(f"status.md não encontrado: {status_path}")
    if not spec_path.exists():
        fail_json(f"spec não encontrada: {spec_path}")

    status_fm, _ = parse_frontmatter(read_text(status_path))
    spec_fm, _ = parse_frontmatter(read_text(spec_path))

    consumed = status_fm.get("spec_version_consumed")
    if consumed is None or consumed == "null":
        consumed = None
    elif isinstance(consumed, str):
        try:
            consumed = int(consumed)
        except ValueError:
            consumed = None

    current = spec_fm.get("spec_version", 1)
    if isinstance(current, str):
        try:
            current = int(current)
        except ValueError:
            current = 1

    drift = consumed is not None and current > consumed

    changelog_entries = []
    if drift and changelog_path.exists():
        all_entries = parse_changelog(read_text(changelog_path))
        # Pegar entradas posteriores ao consumed.
        changelog_entries = [e for e in all_entries if e["version"] > consumed]

    payload = {
        "ok": True,
        "task": args.task,
        "spec_version_current": current,
        "spec_version_consumed": consumed,
        "drift": drift,
        "delta": (current - consumed) if (consumed is not None and drift) else 0,
        "changelog_entries": changelog_entries,
        "changelog_present": changelog_path.exists(),
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fail_json(f"freshness_check failed: {e.__class__.__name__}: {e}")
