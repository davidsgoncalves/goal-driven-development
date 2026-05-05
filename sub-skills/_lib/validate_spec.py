#!/usr/bin/env python3
"""
validate_spec.py — lint estrutural da spec (sem LLM).

Substitui parte do trabalho do `review --spec` que é puramente determinístico.
Verificações semânticas profundas (ortogonalidade, NFRs adequados, edge cases
óbvios) continuam no review (subagent) — esse script só pega o "burro" barato.

Uso:
    python3 validate_spec.py --task PROJ-123 \\
        [--specs-path docs/specs] [--god-root .]

Saída JSON:
{
  "ok": true,
  "task": "PROJ-123",
  "blocking": [{"check": "...", "detail": "..."}],
  "warnings": [...],
  "summary": {"blocking": 0, "warnings": 2}
}

Exit code: 0 se sem blockers; 2 se há blockers (warnings sozinhos = 0).
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import fail_json, read_text, parse_frontmatter

REQ_RE = re.compile(r"^###\s*(REQ-\d+):", re.MULTILINE)
AC_RE = re.compile(r"^-\s*(AC-\d+\.\d+):\s*(.+?)\s*$", re.MULTILINE)
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

REQUIRED_SECTIONS = ["Objetivo", "Não-objetivos", "Requisitos", "Cenários", "NFRs"]

# Palavras-tabu sem métrica (lista deliberadamente conservadora).
TABU_WORDS = [
    "rápido", "rapida", "fácil", "facil", "intuitivo",
    "escalável", "escalavel", "simples", "limpo", "robusto",
]
METRIC_HINTS = ["<", ">", "ms", "s ", " s.", "%", "qps", "tps", "rps"]

# Palavras-flag de framework leak (subset das mais comuns; alinhar com heuristics.md).
FRAMEWORK_FLAGS = [
    "react", "vue", "angular", "next.js", "nuxt", "remix",
    "rails", "django", "flask", "laravel", "spring", "express", "fastify", "nestjs",
    "postgres", "postgresql", "mysql", "mongodb", "redis", "memcached",
    "kafka", "rabbitmq", "sqs", "kinesis",
    "useState", "useEffect", "useMemo", "ActiveRecord", "sequelize", "prisma",
]


def main():
    parser = argparse.ArgumentParser(description="Lint estrutural da spec.")
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
        fail_json(f"Spec não encontrada: {spec_path}")

    text = read_text(spec_path)
    fm, body = parse_frontmatter(text)
    blocking = []
    warnings = []

    # Frontmatter checks.
    for required in ("spec_version", "task"):
        if required not in fm:
            blocking.append({
                "check": "frontmatter_missing",
                "detail": f"campo obrigatório `{required}` ausente no frontmatter",
            })

    # Sections check.
    sections = {m.group(1).strip() for m in SECTION_RE.finditer(body)}
    for required in REQUIRED_SECTIONS:
        if required not in sections:
            blocking.append({
                "check": "section_missing",
                "detail": f"seção obrigatória `## {required}` ausente",
            })

    # REQ × AC: cada REQ deve ter ao menos 1 AC.
    req_positions = [(m.start(), m.group(1)) for m in REQ_RE.finditer(body)]
    for i, (pos, rid) in enumerate(req_positions):
        end = req_positions[i + 1][0] if i + 1 < len(req_positions) else len(body)
        block = body[pos:end]
        if not AC_RE.search(block):
            blocking.append({
                "check": "req_without_ac",
                "detail": f"{rid} não tem nenhum AC",
            })

    # AC IDs estáveis (formato AC-NNN.N).
    all_acs = [(m.group(1), m.group(2)) for m in AC_RE.finditer(body)]
    seen_acs = set()
    for ac_id, ac_text in all_acs:
        if ac_id in seen_acs:
            warnings.append({
                "check": "duplicate_ac_id",
                "detail": f"AC {ac_id} aparece mais de uma vez",
            })
        seen_acs.add(ac_id)

    # Palavras-tabu sem métrica em ACs.
    for ac_id, ac_text in all_acs:
        ac_lower = ac_text.lower()
        for tabu in TABU_WORDS:
            if tabu in ac_lower and not any(h in ac_lower for h in METRIC_HINTS):
                blocking.append({
                    "check": "tabu_word_without_metric",
                    "detail": f"{ac_id} usa '{tabu}' sem métrica — reescrever com critério mensurável",
                })
                break

    # Framework leak em REQs/ACs/Objetivo (não em Notas técnicas / Input bruto).
    sections_to_lint = ["Objetivo", "Requisitos"]
    section_bodies = {}
    section_positions = list(SECTION_RE.finditer(body))
    for i, m in enumerate(section_positions):
        name = m.group(1).strip()
        start = m.end()
        end = section_positions[i + 1].start() if i + 1 < len(section_positions) else len(body)
        section_bodies[name] = body[start:end]

    for sec_name in sections_to_lint:
        sec_body = section_bodies.get(sec_name, "")
        sec_lower = sec_body.lower()
        for flag in FRAMEWORK_FLAGS:
            if flag.lower() in sec_lower:
                warnings.append({
                    "check": "framework_leak",
                    "detail": f"seção `## {sec_name}` menciona '{flag}' — considere mover pra `## Notas técnicas (input pro plan)`",
                })

    # Non-blocking: input bruto preservado.
    if "## Input bruto" not in body and fm.get("spec_version", 1) >= 1:
        warnings.append({
            "check": "input_bruto_missing",
            "detail": "seção `## Input bruto` ausente — em v9+, ela substituiu description.md",
        })

    payload = {
        "ok": True,
        "task": args.task,
        "blocking": blocking,
        "warnings": warnings,
        "summary": {
            "blocking": len(blocking),
            "warnings": len(warnings),
        },
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    sys.exit(0 if not blocking else 2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fail_json(f"validate_spec failed: {e.__class__.__name__}: {e}")
