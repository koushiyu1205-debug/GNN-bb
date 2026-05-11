import json
import math
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_path(*parts):
    return PROJECT_ROOT.joinpath(*parts)


def ensure_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def log(message):
    print(message, flush=True)


def to_jsonable(value):
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    return value


def write_json(path, data):
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(to_jsonable(data), handle, indent=2, ensure_ascii=False)


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def round_float(value, digits=6):
    if value is None:
        return None
    return round(float(value), digits)

