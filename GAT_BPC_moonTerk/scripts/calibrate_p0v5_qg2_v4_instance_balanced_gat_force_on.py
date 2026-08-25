#!/usr/bin/env python3
"""Run the frozen QG2 force-on replay with instance-balanced selection.

The replay implementation and safety checks remain frozen.  This wrapper only
changes the deterministic order used by a bounded screen: every instance gets
one context before any instance contributes a second context.  A full run
still evaluates the same eligible context universe.
"""

from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.instance_balanced_learning import (  # noqa: E402
    INSTANCE_BALANCING_POLICY_V1,
)


FROZEN_FORCE_ON = ROOT / "scripts/calibrate_p0v5_qg2_v3_gat_force_on.py"
SELECTION_POLICY = "instance_round_robin_then_frozen_state_order.v1"


def main() -> int:
    module = _load_frozen_force_on()
    module._frozen_context_order = _instance_balanced_context_order
    returncode = int(module.main())
    output = _argument_path("--output")
    if output is not None and output.is_file():
        _annotate_report(output)
    return returncode


def _instance_balanced_context_order(rows, *, maximum_per_scale: int):
    result = []
    for scale in (30, 50):
        candidates = [
            dict(row) for row in rows if int(row["scale"]) == scale
        ]
        by_instance = defaultdict(list)
        for row in candidates:
            by_instance[str(row["instance_hash"])].append(row)
        for values in by_instance.values():
            values.sort(key=_frozen_context_key)
        instance_order = sorted(
            by_instance,
            key=lambda value: hashlib.sha256(value.encode()).hexdigest(),
        )
        queues = {
            instance: deque(by_instance[instance])
            for instance in instance_order
        }
        selected = []
        while any(queues.values()):
            for instance in instance_order:
                if queues[instance]:
                    selected.append(queues[instance].popleft())
                    if maximum_per_scale > 0 and (
                        len(selected) >= maximum_per_scale
                    ):
                        break
            if maximum_per_scale > 0 and len(selected) >= maximum_per_scale:
                break
        result.extend(selected)
    return result


def _frozen_context_key(row):
    return (
        str(row.get("q0_milestone_kind") or ""),
        hashlib.sha256(str(row["state_hash"]).encode()).hexdigest(),
    )


def _annotate_report(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = list(payload.get("records") or ())
    payload.update({
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "selection_experimental_unit": "instance",
        "context_selection_policy": SELECTION_POLICY,
        "selection_by_scale": {
            str(scale): {
                "context_count": sum(
                    int(row.get("scale") or 0) == scale for row in records
                ),
                "instance_count": len({
                    str(row.get("instance_hash") or "")
                    for row in records
                    if int(row.get("scale") or 0) == scale
                }),
            }
            for scale in (30, 50)
        },
    })
    _write(path, payload)


def _argument_path(flag: str) -> Path | None:
    try:
        index = sys.argv.index(flag)
    except ValueError:
        return None
    if index + 1 >= len(sys.argv):
        return None
    value = Path(sys.argv[index + 1]).expanduser()
    return value if value.is_absolute() else (ROOT / value).resolve()


def _load_frozen_force_on():
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_v3_frozen_force_on", FROZEN_FORCE_ON
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen QG2 force-on evaluator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
