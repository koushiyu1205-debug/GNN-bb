"""Configuration loading helpers for thin CLI scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_config(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(text)
        return dict(payload or {})
    except Exception:
        return _load_simple_yaml(text)


def apply_overrides(config: dict[str, Any], overrides: list[str] | None) -> dict[str, Any]:
    result = dict(config)
    for item in overrides or []:
        if "=" not in item:
            raise ValueError(f"override must be key=value, got {item!r}")
        key, raw_value = item.split("=", 1)
        result[key.strip()] = _parse_scalar(raw_value.strip())
    return result


def _load_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by benchmark configs.

    This fallback intentionally supports only top-level scalars and top-level
    lists. Nested benchmark metadata should use PyYAML when needed.
    """

    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[Any] | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key is not None and current_list is not None:
            current_list.append(_parse_scalar(line[4:].strip()))
            continue
        if line.startswith(" "):
            continue
        current_key = None
        current_list = None
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value == "":
            current_key = key
            current_list = []
            result[key] = current_list
        else:
            result[key] = _parse_scalar(raw_value)
    return result


def _parse_scalar(value: str) -> Any:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [_parse_scalar(part.strip()) for part in body.split(",")]
    try:
        if any(char in value for char in (".", "e", "E")):
            return float(value)
        return int(value)
    except ValueError:
        return value

