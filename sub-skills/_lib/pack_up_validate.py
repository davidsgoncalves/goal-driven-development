#!/usr/bin/env python3
"""
pack_up_validate.py — orquestrador batch que consolida validações do pack-up.

Substitui múltiplas invocações sequenciais (coverage skill + parse_rules.py +
freshness_check.py + validate_spec.py) por **uma única chamada** que importa
os parsers e retorna JSON consolidado. Skill `pack-up` chama 1x e despacha pros
passos seguintes (review --execution, gerar PR description, update status) sem
precisar re-rodar nada.

Uso:
    python3 pack_up_validate.py --task PROJ-123 \\
        --branch-base main \\
        [--specs-path docs/specs] \\
        [--god-root .] \\
        [--source-root .]

Saída JSON consolidada:
{
  "ok": true,
  "task": "PROJ-123",
  "spec": {
    "path": "docs/specs/tasks/PROJ-123.md",
    "version": 3,
    "applicable_rules": ["BR-PAYMENTS-001", ...],
    "reqs": [...]              # do parse_spec
  },
  "coverage": {                # do parse_coverage
    "acs_declared": [...],
    "covered_by_test": {...},
    "covered_manually": {...},
    "orphaned": [...],
    "summary": {...},
    "markdown": "..."          # tabela markdown pronta pro PR
  },
  "rules": {                    # do parse_rules
    "applicable_rules": [...],
    "annotated": {...},
    "orphaned": [...],
    "summary": {...},
    "markdown": "..."
  },
  "freshness": {                # do freshness_check
    "drift": false,
    "spec_version_current": 3,
    "spec_version_consumed": 3
  },
  "lint": {                     # do validate_spec (subset)
    "blocking": [],
    "warnings": [...]
  },
  "pr_description_data": {      # pronto pra gen_pr_description.py
    "task": "...",
    "spec_path": "...",
    "spec_version_delivered": 3,
    "reqs_covered": [...],
    "coverage_markdown": "...",
    "rules_markdown": "..."
  }
}

Python 3.8+ stdlib only. Cross-platform.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _common import (
    fail_json, read_text, parse_frontmatter, find_god_root
)
import parse_coverage
import parse_rules
import parse_spec as parse_spec_module
import validate_spec
import freshness_check


def safe_run(fn, *args, **kwargs):
    """Roda função capturando exception. Retorna (result, error_str)."""
    try:
        return fn(*args, **kwargs), None
    except SystemExit:
        # Sub-script chamou sys.exit (fail_json/ok_json). Capturar e seguir.
        return None, "sub-script chamou sys.exit"
    except Exception as e:
        return None, f"{e.__class__.__name__}: {e}"


def main():
    parser = argparse.ArgumentParser(description="Validação batch do pack-up.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--branch-base", required=True)
    parser.add_argument("--specs-path", default="docs/specs")
    parser.add_argument("--god-root", default=".")
    parser.add_argument("--source-root", default=".")
    args = parser.parse_args()

    god_root = Path(args.god_root).resolve()
    specs_path = Path(args.specs_path)
    if not specs_path.is_absolute():
        specs_path = (god_root / specs_path).resolve()
    source_root = Path(args.source_root).resolve()

    spec_path = specs_path / "tasks" / f"{args.task}.md"
    if not spec_path.exists():
        # Task pode não ter spec (perfil trivial). Retornar JSON parcial — não é erro.
        payload = {
            "ok": True,
            "task": args.task,
            "spec": None,
            "coverage": None,
            "rules": None,
            "freshness": None,
            "lint": None,
            "pr_description_data": {
                "task": args.task,
                "spec_path": None,
                "spec_version_delivered": None,
                "reqs_covered": [],
                "coverage_markdown": "",
                "rules_markdown": "",
            },
            "warning": f"Spec não encontrada em {spec_path} — task sem spec ou perfil trivial",
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(0)

    # === Spec parse ===
    spec_text = read_text(spec_path)
    fm, body = parse_frontmatter(spec_text)
    spec_version = fm.get("spec_version", 1)
    if isinstance(spec_version, str):
        try:
            spec_version = int(spec_version)
        except ValueError:
            spec_version = 1
    applicable_rules = fm.get("applicable_rules") or []
    if not isinstance(applicable_rules, list):
        applicable_rules = []

    # Reusar a extração de REQs/ACs do parse_spec.
    sections = parse_spec_module.split_sections(body)
    reqs = parse_spec_module.extract_reqs(sections.get("Requisitos", ""))

    spec_data = {
        "path": str(spec_path),
        "version": spec_version,
        "applicable_rules": list(applicable_rules),
        "reqs": [{"id": r["id"], "name": r["name"], "ac_count": len(r["acs"])} for r in reqs],
    }

    # === Coverage ===
    coverage_dir = god_root / "GOD" / "tasks" / args.task
    coverage_matrix, cov_err = safe_run(
        parse_coverage.build_matrix,
        task=args.task,
        spec_path=spec_path,
        spec_text=spec_text,
        coverage_dir=coverage_dir,
        source_root=source_root,
        diff_against=args.branch_base,
    )
    if cov_err:
        coverage_data = {"error": cov_err, "summary": {"total": 0, "tested": 0, "manual": 0, "orphaned": 0}}
        coverage_md = ""
    else:
        coverage_data = coverage_matrix
        coverage_md = parse_coverage.render_markdown(coverage_matrix)
        coverage_data["markdown"] = coverage_md

    # === Rules ===
    rules_data = {
        "applicable_rules": [],
        "annotated": {},
        "orphaned": [],
        "summary": {"total": 0, "annotated": 0, "orphaned": 0},
        "markdown": "",
    }
    if applicable_rules:
        diff_files, _ = safe_run(parse_rules.get_diff_files, args.branch_base, source_root)
        if diff_files is None:
            diff_files = []
        annotated, _ = safe_run(parse_rules.scan_for_rules, diff_files)
        if annotated is None:
            annotated = {}
        declared_set = set(applicable_rules)
        annotated_set = set(annotated.keys()) & declared_set
        orphaned = sorted(declared_set - annotated_set)
        rules_payload = {
            "task": args.task,
            "applicable_rules": list(applicable_rules),
            "annotated": {k: v for k, v in annotated.items() if k in declared_set},
            "orphaned": orphaned,
            "summary": {
                "total": len(declared_set),
                "annotated": len(annotated_set),
                "orphaned": len(orphaned),
            },
        }
        rules_data = rules_payload
        rules_data["markdown"] = parse_rules.render_markdown(rules_payload)

    # === Freshness ===
    status_path = god_root / "GOD" / "tasks" / args.task / "status.md"
    freshness_data = {"drift": False, "spec_version_current": spec_version, "spec_version_consumed": None}
    if status_path.exists():
        status_fm, _ = parse_frontmatter(read_text(status_path))
        consumed = status_fm.get("spec_version_consumed")
        if isinstance(consumed, str):
            try:
                consumed = int(consumed)
            except ValueError:
                consumed = None
        freshness_data["spec_version_consumed"] = consumed
        if consumed is not None and spec_version > consumed:
            freshness_data["drift"] = True
            freshness_data["delta"] = spec_version - consumed

    # === Lint estrutural ===
    lint_data = {"blocking": [], "warnings": []}
    # Conservador: não bloqueia pack-up — apenas reporta warnings de indícios óbvios.
    for r in reqs:
        if len(r["acs"]) == 0:
            lint_data["blocking"].append({
                "check": "req_without_ac",
                "detail": f"{r['id']} não tem AC",
            })

    # === PR description data ===
    reqs_covered = [r["id"] for r in reqs]
    pr_data = {
        "task": args.task,
        "spec_path": str(spec_path),
        "spec_version_delivered": spec_version,
        "reqs_covered": reqs_covered,
        "coverage_markdown": coverage_md,
        "rules_markdown": rules_data.get("markdown", ""),
    }

    # Changelog path (se existe — informa pra pack-up incluir no PR description).
    changelog_path = specs_path / "tasks" / f"{args.task}-changelog.md"
    if changelog_path.exists():
        pr_data["changelog_path"] = str(changelog_path)

    payload = {
        "ok": True,
        "task": args.task,
        "spec": spec_data,
        "coverage": coverage_data,
        "rules": rules_data,
        "freshness": freshness_data,
        "lint": lint_data,
        "pr_description_data": pr_data,
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fail_json(f"pack_up_validate failed: {e.__class__.__name__}: {e}")
