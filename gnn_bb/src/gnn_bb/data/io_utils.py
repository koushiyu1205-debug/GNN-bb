"""中文摘要：本文件提供 JSON、目录和数值清洗工具，供实例管理和实验结果输出复用。"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, data: Any) -> Path:
    output_path = Path(path)
    ensure_dir(output_path.parent)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return output_path


def finite_or_none(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    # 中文注释：SCIP 常用 1e20 量级表示无界或尚无 primal/dual bound；CSV 中记录为空更清楚。
    if isinstance(value, float) and abs(value) >= 1.0e19:
        return None
    return value


def round_float(value: Any, digits: int = 6) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        if abs(value) >= 1.0e19:
            return None
        return round(value, digits)
    return value
