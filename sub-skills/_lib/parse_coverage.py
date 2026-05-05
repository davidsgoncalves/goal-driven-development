#!/usr/bin/env python3
"""
parse_coverage.py — gera matriz AC × validação pra uma task GOD.

Substitui parsing manual feito pela skill `coverage`. Delegação via Bash
economiza tokens de LLM em pack-up / review --execution / coverage standalone.

Uso:
    python3 parse_coverage.py --task PROJ-123 [--format json|markdown|terminal]
                              [--specs-path docs/specs]
                              [--god-root .]
                              [--diff-against main]

Saída JSON (default):
{
  "task": "PROJ-123",
  "spec_path": "docs/specs/tasks/PROJ-123.md",
  "spec_version": 2,
  "acs_declared": ["AC-001.1", "AC-001.2", ...],
  "covered_by_test": {"AC-001.1": ["tests/foo.spec.ts:42"], ...},
  "covered_manually": {"AC-001.3": "validação visual em staging por PM"},
  "orphaned": ["AC-002.1"],
  "summary": {"total": 4, "tested": 2, "manual": 1, "orphaned": 1}
}

Compatível com Python 3.8+ stdlib only. Sem dependências externas.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Regex unificada pra `// covers: AC-X[, AC-Y]` em comentários de várias linguagens.
# Captura: prefixo de comentário (//, #, --, /*, ...) + "covers:" + lista de IDs.
COVERS_REGEX = re.compile(
    r"""
    (?://|\#|--|/\*|\*)\s*       # prefixo de comentário (// # -- /* *)
    covers:\s*                    # marker literal
    (?P<ids>                      # captura grupo "ids"
        AC-\d+\.\d+               # primeiro ID
        (?:\s*,\s*AC-\d+\.\d+)*   # IDs adicionais separados por vírgula
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Regex pra extrair AC IDs declarados na spec.
AC_DECLARATION_REGEX = re.compile(r"^-\s*(AC-\d+\.\d+):", re.MULTILINE)

# Regex pra spec_version no frontmatter da spec.
SPEC_VERSION_REGEX = re.compile(r"^spec_version:\s*(\d+)", re.MULTILINE)

# Extensões de arquivo onde procurar // covers: (otimização — evita binários).
SOURCE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".rb", ".py", ".go", ".java", ".kt", ".kts",
    ".cs", ".scala", ".rs", ".swift", ".php",
    ".sh", ".bash", ".zsh",
}

# Diretórios a ignorar.
IGNORE_DIRS = {".git", "node_modules", "vendor", "dist", "build", "target", ".next", "__pycache__"}


def read_text(path: Path) -> str:
    """Lê arquivo retornando string vazia se não existe ou erro."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return ""


def find_spec(specs_path: Path, task: str) -> Path:
    """Localiza spec da task em <specs_path>/tasks/<task>.md."""
    candidate = specs_path / "tasks" / f"{task}.md"
    if candidate.exists():
        return candidate
    return None


def parse_acs_declared(spec_text: str) -> list:
    """Extrai lista de AC-IDs declarados na spec (em ordem de aparição)."""
    matches = AC_DECLARATION_REGEX.findall(spec_text)
    # Preserva ordem mas remove duplicatas mantendo primeira ocorrência.
    seen = set()
    out = []
    for ac in matches:
        if ac not in seen:
            seen.add(ac)
            out.append(ac)
    return out


def parse_spec_version(spec_text: str) -> int:
    """Extrai spec_version do frontmatter. Retorna 1 se não encontrado."""
    m = SPEC_VERSION_REGEX.search(spec_text)
    return int(m.group(1)) if m else 1


def find_files_to_scan(root: Path, diff_against: str = None) -> list:
    """Retorna lista de arquivos source pra varrer.

    Se diff_against é informado, limita aos arquivos do diff vs essa base.
    Caso contrário, varre repo inteiro respeitando IGNORE_DIRS.
    """
    if diff_against:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{diff_against}...HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            )
            files = [root / line.strip() for line in result.stdout.splitlines() if line.strip()]
            return [f for f in files if f.exists() and f.suffix in SOURCE_EXTENSIONS]
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Se git falhou, cai pra varredura completa.
            pass

    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Mutar dirnames in-place pra os.walk pular IGNORE_DIRS.
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix in SOURCE_EXTENSIONS:
                files.append(p)
    return files


def scan_files_for_covers(files: list, root: Path) -> dict:
    """Varre arquivos por `// covers: AC-X` e retorna {ac_id: [path:linha, ...]}."""
    coverage = {}
    for path in files:
        text = read_text(path)
        if "covers:" not in text.lower():  # short-circuit barato
            continue
        for line_num, line in enumerate(text.splitlines(), start=1):
            for match in COVERS_REGEX.finditer(line):
                ids_raw = match.group("ids")
                ids = [s.strip() for s in ids_raw.split(",")]
                for ac_id in ids:
                    rel = path.relative_to(root) if path.is_relative_to(root) else path
                    coverage.setdefault(ac_id, []).append(f"{rel}:{line_num}")
    return coverage


def parse_manual_coverage(coverage_md_path: Path) -> dict:
    """Lê GOD/tasks/{cod}/coverage.md e extrai validações manuais.

    Espera formato (seção '## Validações manuais'):
        - AC-002.1: validação manual em staging por PM
        - AC-002.2: visual em staging por UX
    """
    if not coverage_md_path.exists():
        return {}

    text = read_text(coverage_md_path)
    manual = {}

    # Captura bloco entre '## Validações manuais' e próximo cabeçalho ## ou EOF.
    section_re = re.compile(
        r"##\s*Validações manuais\s*\n(.*?)(?=\n##\s|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    section_match = section_re.search(text)
    if not section_match:
        return manual

    section_body = section_match.group(1)
    line_re = re.compile(r"^-\s*(AC-\d+\.\d+):\s*(.+?)$", re.MULTILINE)
    for ac_id, description in line_re.findall(section_body):
        manual[ac_id] = description.strip()

    return manual


def build_matrix(task: str, spec_path: Path, spec_text: str, coverage_dir: Path,
                 source_root: Path, diff_against: str = None) -> dict:
    """Monta o JSON final cruzando declarados × cobertura × manuais."""
    acs_declared = parse_acs_declared(spec_text)
    spec_version = parse_spec_version(spec_text)

    files = find_files_to_scan(source_root, diff_against=diff_against)
    covered_by_test = scan_files_for_covers(files, source_root)

    coverage_md = coverage_dir / "coverage.md" if coverage_dir else None
    covered_manually = parse_manual_coverage(coverage_md) if coverage_md else {}

    declared_set = set(acs_declared)
    tested_set = set(covered_by_test.keys()) & declared_set
    manual_set = set(covered_manually.keys()) & declared_set
    orphaned = sorted(declared_set - tested_set - manual_set)

    return {
        "task": task,
        "spec_path": str(spec_path),
        "spec_version": spec_version,
        "acs_declared": acs_declared,
        "covered_by_test": {k: v for k, v in covered_by_test.items() if k in declared_set},
        "covered_manually": {k: v for k, v in covered_manually.items() if k in declared_set},
        "orphaned": orphaned,
        "summary": {
            "total": len(acs_declared),
            "tested": len(tested_set),
            "manual": len(manual_set),
            "orphaned": len(orphaned),
        },
    }


def render_markdown(matrix: dict) -> str:
    """Gera tabela markdown pra injetar no PR description."""
    lines = ["| AC | Status | Validação |", "|----|--------|-----------|"]
    for ac in matrix["acs_declared"]:
        if ac in matrix["covered_by_test"]:
            paths = matrix["covered_by_test"][ac]
            lines.append(f"| {ac} | ✅ | {', '.join(paths)} |")
        elif ac in matrix["covered_manually"]:
            desc = matrix["covered_manually"][ac]
            lines.append(f"| {ac} | 👁 | manual: {desc} |")
        else:
            lines.append(f"| {ac} | ⚠️ | (sem cobertura) |")

    s = matrix["summary"]
    lines.append("")
    lines.append(
        f"**Resumo:** {s['total']} ACs · {s['tested']} testes · "
        f"{s['manual']} manuais · {s['orphaned']} órfãos"
    )
    return "\n".join(lines)


def render_terminal(matrix: dict) -> str:
    """Saída legível em terminal (sem cores complexas — emoji só)."""
    lines = [f"📊 Cobertura — {matrix['task']} (spec_version: {matrix['spec_version']})", ""]
    for ac in matrix["acs_declared"]:
        if ac in matrix["covered_by_test"]:
            paths = ", ".join(matrix["covered_by_test"][ac])
            lines.append(f"  ✅ {ac}  →  {paths}")
        elif ac in matrix["covered_manually"]:
            lines.append(f"  👁  {ac}  →  manual: {matrix['covered_manually'][ac]}")
        else:
            lines.append(f"  ⚠️  {ac}  →  sem cobertura")
    s = matrix["summary"]
    lines.extend([
        "",
        f"  Total: {s['total']} · Testes: {s['tested']} · Manuais: {s['manual']} · Órfãos: {s['orphaned']}",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Gera matriz AC × validação pra uma task GOD.")
    parser.add_argument("--task", required=True, help="Código da task (ex: PROJ-123)")
    parser.add_argument("--specs-path", default="docs/specs",
                        help="Root do repo de specs (default: docs/specs)")
    parser.add_argument("--god-root", default=".",
                        help="Diretório onde GOD/ está (default: cwd)")
    parser.add_argument("--source-root", default=".",
                        help="Diretório do código a varrer (default: cwd)")
    parser.add_argument("--diff-against", default=None,
                        help="Branch base — limita varredura aos arquivos do diff (ex: main)")
    parser.add_argument("--format", choices=["json", "markdown", "terminal"], default="json")
    args = parser.parse_args()

    god_root = Path(args.god_root).resolve()
    specs_path = Path(args.specs_path)
    if not specs_path.is_absolute():
        specs_path = (god_root / specs_path).resolve()
    source_root = Path(args.source_root).resolve()

    spec_path = find_spec(specs_path, args.task)
    if spec_path is None:
        # Spec ausente → matriz vazia, não bloqueia.
        empty = {
            "task": args.task,
            "spec_path": None,
            "spec_version": None,
            "acs_declared": [],
            "covered_by_test": {},
            "covered_manually": {},
            "orphaned": [],
            "summary": {"total": 0, "tested": 0, "manual": 0, "orphaned": 0},
            "warning": f"Spec não encontrada em {specs_path}/tasks/{args.task}.md",
        }
        if args.format == "json":
            print(json.dumps(empty, indent=2, ensure_ascii=False))
        else:
            print(f"⚠️  Spec não encontrada: {specs_path}/tasks/{args.task}.md")
        return 0

    spec_text = read_text(spec_path)
    coverage_dir = god_root / "GOD" / "tasks" / args.task

    matrix = build_matrix(
        task=args.task,
        spec_path=spec_path,
        spec_text=spec_text,
        coverage_dir=coverage_dir,
        source_root=source_root,
        diff_against=args.diff_against,
    )

    if args.format == "json":
        print(json.dumps(matrix, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(matrix))
    else:
        print(render_terminal(matrix))

    return 0


if __name__ == "__main__":
    sys.exit(main())
