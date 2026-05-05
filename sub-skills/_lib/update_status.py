#!/usr/bin/env python3
"""
update_status.py — read-modify-write determinístico de status.md de uma task.

Substitui edits manuais que LLM fazia em cada skill (spec, init, plan, implement,
pack-up, learn, pause, resume, update-spec). Preserva campos não tocados.

Uso:
    python3 update_status.py --task PROJ-123 --god-root . \\
        --set phase=implementing \\
        --set updated_by=implement \\
        --set-now updated_at \\
        --append prs=https://github.com/org/repo/pull/123 \\
        --remove paused

Operações:
    --set KEY=VALUE     define KEY como VALUE (escalar)
    --set-now KEY       define KEY como timestamp ISO 8601 UTC atual
    --append KEY=VALUE  acrescenta VALUE à lista KEY (cria lista se não existe)
    --remove KEY        remove a chave KEY do frontmatter

Saída JSON: {"ok": true, "task": "...", "path": "...", "changes": {...}}

Cross-platform, Python 3.8+ stdlib only.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (
    fail_json, ok_json, read_text, write_text, parse_frontmatter,
    serialize_frontmatter, _coerce
)


def now_utc_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    parser = argparse.ArgumentParser(description="Atualiza status.md de uma task GOD.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--god-root", default=".")
    parser.add_argument("--set", action="append", default=[], dest="sets",
                        metavar="KEY=VALUE", help="Define key como value (escalar)")
    parser.add_argument("--set-now", action="append", default=[], dest="set_nows",
                        metavar="KEY", help="Define key como timestamp ISO 8601 UTC atual")
    parser.add_argument("--append", action="append", default=[], dest="appends",
                        metavar="KEY=VALUE", help="Acrescenta value à lista key")
    parser.add_argument("--remove", action="append", default=[], dest="removes",
                        metavar="KEY", help="Remove key do frontmatter")
    args = parser.parse_args()

    god_root = Path(args.god_root).resolve()
    status_path = god_root / "GOD" / "tasks" / args.task / "status.md"

    if not status_path.exists():
        fail_json(f"status.md não encontrado em {status_path}")

    text = read_text(status_path)
    data, rest = parse_frontmatter(text)
    changes = {}

    for assignment in args.sets:
        if "=" not in assignment:
            fail_json(f"--set espera KEY=VALUE, recebido: {assignment}")
        k, v = assignment.split("=", 1)
        data[k] = _coerce(v)
        changes[k] = data[k]

    for key in args.set_nows:
        ts = now_utc_iso()
        data[key] = ts
        changes[key] = ts

    for assignment in args.appends:
        if "=" not in assignment:
            fail_json(f"--append espera KEY=VALUE, recebido: {assignment}")
        k, v = assignment.split("=", 1)
        existing = data.get(k)
        if existing is None or existing == [] or existing == "":
            data[k] = [_coerce(v)]
        elif isinstance(existing, list):
            existing.append(_coerce(v))
            data[k] = existing
        else:
            data[k] = [existing, _coerce(v)]
        changes[k] = data[k]

    for key in args.removes:
        if key in data:
            del data[key]
            changes[key] = "[removed]"

    new_fm = serialize_frontmatter(data)
    if rest:
        new_text = f"{new_fm}\n\n{rest.lstrip(chr(10))}"
    else:
        new_text = f"{new_fm}\n"
    write_text(status_path, new_text)

    ok_json({
        "task": args.task,
        "path": str(status_path),
        "changes": changes,
        "current": data,
    })


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fail_json(f"update_status failed: {e.__class__.__name__}: {e}")
