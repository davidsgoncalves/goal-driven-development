#!/usr/bin/env python3
"""
parse_spec.py — extrai estrutura da spec (frontmatter, REQs, ACs) sem LLM.

Usado por plan, implement, review --execution, coverage e qualquer skill que
precise de dados estruturados da spec sem ler o arquivo inteiro.

Uso:
    python3 parse_spec.py --task PROJ-123 \\
        [--specs-path docs/specs] \\
        [--god-root .]

Saída JSON:
{
  "ok": true,
  "task": "PROJ-123",
  "spec_path": "docs/specs/tasks/PROJ-123.md",
  "frontmatter": {"spec_version": 2, "profile": "normal", "applicable_rules": [...]},
  "objetivo": "Frase única do problema...",
  "nao_objetivos": ["item 1", "item 2"],
  "reqs": [
    {"id": "REQ-001", "name": "...", "ears": "WHEN ... THEN ...",
     "acs": [{"id": "AC-001.1", "text": "..."}]}
  ],
  "totals": {"reqs": 2, "acs": 5, "nfrs_declared": 3}
}

Python 3.8+ stdlib only.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import fail_json, ok_json, read_text, parse_frontmatter

REQ_RE = re.compile(r"^###\s*(REQ-\d+):\s*(.+?)\s*$", re.MULTILINE)
EARS_RE = re.compile(r"^\*\*WHEN\*\*\s*(.+?)\*\*THEN\*\*\s*(.+?)\*\*SHALL\*\*\s*(.+?)\.\s*$",
                     re.MULTILINE | re.IGNORECASE)
AC_RE = re.compile(r"^-\s*(AC-\d+\.\d+):\s*(.+?)\s*$", re.MULTILINE)
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def split_sections(text):
    """Divide o markdown em {section_name: body}."""
    sections = {}
    matches = list(SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    return sections


def extract_reqs(req_section_text):
    """Extrai lista de REQs com seus ACs."""
    reqs = []
    # Localizar cada REQ-NNN.
    req_blocks = []
    for m in REQ_RE.finditer(req_section_text):
        req_blocks.append((m.start(), m.group(1), m.group(2)))

    for i, (pos, rid, name) in enumerate(req_blocks):
        end = req_blocks[i + 1][0] if i + 1 < len(req_blocks) else len(req_section_text)
        body = req_section_text[pos:end]

        ears_match = EARS_RE.search(body)
        ears_str = None
        if ears_match:
            ears_str = (
                f"WHEN {ears_match.group(1).strip()} "
                f"THEN {ears_match.group(2).strip()} "
                f"SHALL {ears_match.group(3).strip()}."
            )

        acs = [{"id": ac_m.group(1), "text": ac_m.group(2).strip()}
               for ac_m in AC_RE.finditer(body)]

        reqs.append({
            "id": rid,
            "name": name,
            "ears": ears_str,
            "acs": acs,
        })

    return reqs


def main():
    parser = argparse.ArgumentParser(description="Extrai estrutura da spec.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--specs-path", default="docs/specs")
    parser.add_argument("--god-root", default=".")
    args = parser.parse_args()

    god_root = Path(args.god_root).resolve()
    specs_path = Path(args.specs_path)
    if not specs_path.is_absolute():
        specs_path = (god_root / specs_path).resolve()

    spec_path = specs_path / "tasks" / f"{args.task}.md"
    if not spec_path.exists():
        fail_json(f"Spec não encontrada: {spec_path}", task=args.task)

    text = read_text(spec_path)
    fm, body = parse_frontmatter(text)
    sections = split_sections(body)

    objetivo = sections.get("Objetivo", "").strip()
    nao_objetivos_raw = sections.get("Não-objetivos", "")
    nao_objetivos = [
        line.strip("- ").strip()
        for line in nao_objetivos_raw.splitlines()
        if line.strip().startswith("-")
    ]

    reqs_text = sections.get("Requisitos", "")
    reqs = extract_reqs(reqs_text)

    nfrs_text = sections.get("NFRs", "")
    nfrs_declared = sum(
        1 for line in nfrs_text.splitlines()
        if line.strip().startswith("-") and "não aplicável" not in line.lower()
    )

    payload = {
        "ok": True,
        "task": args.task,
        "spec_path": str(spec_path),
        "frontmatter": fm,
        "objetivo": objetivo,
        "nao_objetivos": nao_objetivos,
        "reqs": reqs,
        "totals": {
            "reqs": len(reqs),
            "acs": sum(len(r["acs"]) for r in reqs),
            "nfrs_declared": nfrs_declared,
        },
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fail_json(f"parse_spec failed: {e.__class__.__name__}: {e}")
