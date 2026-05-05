#!/usr/bin/env python3
"""
debug_log.py — append de evento em GOD/tasks/{cod}/debug.log (JSON Lines).

Helper opt-in pra rastrear o que cada skill faz numa execução. Útil pra
diagnosticar custo de tokens e onde o fluxo está caindo (caminho otimizado
vs fallback). NÃO mede tokens diretamente — registra ações + sinais
correlacionados (tamanho de diff, número de ACs, etc.).

Ativação: skills só chamam este helper quando flag --debug é passada na
invocação. Sem flag, nenhum log é escrito (zero overhead).

Uso:
    python3 debug_log.py \\
        --task PROJ-123 \\
        --skill pack-up \\
        --step "4.5 coverage" \\
        --action "batch_consumed" \\
        --details '{"context_blob_used": true, "acs": 4, "diff_files": 12}' \\
        --god-root .

Saída: cria/append em GOD/tasks/PROJ-123/debug.log:
    {"ts": "2026-05-05T15:30:00Z", "skill": "pack-up", "step": "4.5 coverage",
     "action": "batch_consumed", "details": {...}}

Stdout: confirmação curta (1 linha JSON `{"ok": true, "appended": true}`).
Skills consumidoras tipicamente ignoram a saída.

Cross-platform, Python 3.8+ stdlib only.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


def now_utc_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    parser = argparse.ArgumentParser(description="Append evento em debug.log da task.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--skill", required=True,
                        help="Nome da skill (ex: pack-up, spec, plan)")
    parser.add_argument("--step", required=True,
                        help="Passo lógico (ex: '4.5 coverage', '0 hook before')")
    parser.add_argument("--action", required=True,
                        help="Verbo curto (ex: batch_consumed, fallback_llm, delegated)")
    parser.add_argument("--details", default="{}",
                        help="JSON com metadados adicionais")
    parser.add_argument("--god-root", default=".")
    parser.add_argument("--duration-ms", type=int, default=None,
                        help="Duração em ms (opcional; skill calcula entre passos)")
    args = parser.parse_args()

    # Parse details JSON.
    try:
        details = json.loads(args.details)
        if not isinstance(details, dict):
            raise ValueError("details deve ser objeto JSON")
    except (json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"ok": False, "error": f"details inválido: {e}"}))
        sys.exit(1)

    god_root = Path(args.god_root).resolve()
    task_dir = god_root / "GOD" / "tasks" / args.task
    if not task_dir.exists():
        # Pasta da task pode não existir ainda (ex: spec antes de init).
        # Criar defensivamente em vez de falhar.
        task_dir.mkdir(parents=True, exist_ok=True)

    log_path = task_dir / "debug.log"

    event = {
        "ts": now_utc_iso(),
        "skill": args.skill,
        "step": args.step,
        "action": args.action,
        "details": details,
    }
    if args.duration_ms is not None:
        event["duration_ms"] = args.duration_ms

    line = json.dumps(event, ensure_ascii=False) + "\n"

    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        print(json.dumps({"ok": False, "error": f"falha ao escrever {log_path}: {e}"}))
        sys.exit(1)

    print(json.dumps({"ok": True, "appended": True, "log": str(log_path)},
                     ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{e.__class__.__name__}: {e}"}))
        sys.exit(1)
