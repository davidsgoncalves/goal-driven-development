"""
_common.py — utilitários compartilhados pelos scripts em sub-skills/_lib/.

Não tem CLI. Importado pelos demais scripts. Sem dependências externas
(stdlib only). Funciona em macOS, Linux e WSL com Python 3.8+.
"""

import json
import os
import re
import sys
from pathlib import Path

# Regex pra capturar bloco YAML frontmatter no topo de markdown.
FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<body>.*?)\n---\s*\n?(?P<rest>.*)\Z",
    re.DOTALL,
)


def read_text(path):
    """Lê texto retornando string vazia se erro/inexistente."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return ""


def write_text(path, content):
    """Escreve texto, criando diretórios pai se necessário."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def parse_frontmatter(text):
    """Parser leve de frontmatter YAML (subset suportado pelo GOD).

    Suporta:
      key: value
      key: "value with spaces"
      key:
        - item1
        - item2
      key: [item1, item2]
      key: null   (vira None)
      key: true   (vira True)
      key: 42     (vira int)

    NÃO suporta YAML aninhado complexo, anchors, multi-line strings, etc.
    O GOD usa frontmatter simples — funciona pro nosso caso.

    Retorna (data: dict, rest: str). Se não houver frontmatter, data={} e
    rest=text completo.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    body = m.group("body")
    rest = m.group("rest")
    data = {}
    lines = body.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue

        # Match "key: value" ou "key:" (lista vem depois).
        kv_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not kv_match:
            i += 1
            continue

        key = kv_match.group(1)
        raw_value = kv_match.group(2).strip()

        # Lista em formato block (- item por linha).
        if raw_value == "":
            items = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                item_match = re.match(r"^\s*-\s*(.+?)\s*$", next_line)
                if item_match:
                    items.append(_coerce(item_match.group(1)))
                    j += 1
                else:
                    break
            if items:
                data[key] = items
                i = j
                continue
            # key vazia mesmo (sem lista nem valor)
            data[key] = None
            i += 1
            continue

        # Lista inline [a, b, c].
        if raw_value.startswith("[") and raw_value.endswith("]"):
            inner = raw_value[1:-1].strip()
            if inner:
                data[key] = [_coerce(x.strip()) for x in inner.split(",")]
            else:
                data[key] = []
            i += 1
            continue

        # Valor escalar.
        data[key] = _coerce(raw_value)
        i += 1

    return data, rest


def _coerce(value):
    """Converte string YAML-ish pra tipo Python."""
    s = value.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1]
    if s.lower() in ("null", "~", ""):
        return None
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def serialize_frontmatter(data):
    """Serializa dict pra bloco YAML simples compat com parse_frontmatter.

    Mantém ordem do dict (Python 3.7+ preserva insertion order).
    """
    lines = ["---"]
    for key, value in data.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {_format_scalar(item)}")
        else:
            lines.append(f"{key}: {_format_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def _format_scalar(value):
    """Formata escalar pra YAML — quote se contém caracteres especiais."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if any(ch in s for ch in ":#[]{}|>!&*\""):
        # Quote conservador.
        return f'"{s}"'
    return s


def update_frontmatter(text, updates):
    """Lê frontmatter, aplica updates (dict), retorna texto reescrito.

    Preserva ordem das chaves existentes; chaves novas vão ao final.
    Se a chave em updates é None, **remove** a chave do frontmatter.
    """
    data, rest = parse_frontmatter(text)
    for key, value in updates.items():
        if value is None and key in data:
            del data[key]
        elif value is None:
            continue  # não adicionar chave nova como null
        else:
            data[key] = value
    new_fm = serialize_frontmatter(data)
    if rest.startswith("\n"):
        return f"{new_fm}\n{rest.lstrip(chr(10))}"
    return f"{new_fm}\n\n{rest}" if rest else f"{new_fm}\n"


def fail_json(message, **kwargs):
    """Imprime JSON de erro em stdout e exit 1.

    Skills consumidoras parseiam stdout — JSON é contrato de erro.
    Mensagem detalhada vai pra stderr também (visível em logs).
    """
    payload = {"ok": False, "error": message, **kwargs}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"[error] {message}", file=sys.stderr)
    sys.exit(1)


def ok_json(payload):
    """Imprime JSON de sucesso em stdout e exit 0."""
    payload = {"ok": True, **payload}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    sys.exit(0)


def resolve_path(path_str, base):
    """Resolve path relativo a `base` se não-absoluto."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (Path(base) / p).resolve()


def find_god_root(start=None):
    """Sobe na árvore de diretórios procurando GOD/. Retorna Path ou None."""
    cur = Path(start or os.getcwd()).resolve()
    while True:
        if (cur / "GOD").is_dir():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


def read_config_value(god_root, key, default=None):
    """Lê uma chave do GOD/config.md (formato `## chave\\n\\nvalor`).

    Retorna `default` se ausente ou vazia.
    """
    config_path = Path(god_root) / "GOD" / "config.md"
    if not config_path.exists():
        return default

    text = read_text(config_path)
    pattern = re.compile(
        rf"^##\s*{re.escape(key)}\s*$(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        return default

    body = m.group(1).strip()
    # Pegar primeira linha não-vazia que não seja comentário/citação.
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith(">") or line.startswith("<!--"):
            continue
        if line.startswith("(deixe vazio") or line.startswith("(") or line.startswith("```"):
            continue
        return line
    return default
