#!/usr/bin/env python3
"""Overlay strict tree-policy replay labels onto Journey branch score rows.

The overlay is offline and diagnostic-only.  It reads existing score rows plus
strict tree-policy event rows, then appends state-aware rows that can be used by
``journey_branch_candidate_priority=branch_score_horizon``.  It never runs BPC,
pricing, RMP, or produces official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_tree_policy_strict_overlay_20260627")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260627_bpc_future_gat_tree_policy_strict_overlay_zh.md"
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if path.is_dir():
        path = path / "tree_policy_event_rows.jsonl"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _load_rows(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if isinstance(payload, list):
        return [dict(row) for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return [dict(row) for row in payload["rows"] if isinstance(row, dict)]
    raise SystemExit(f"unsupported score row payload: {path}")


def _pair(value: Any) -> tuple[int, int] | None:
    if isinstance(value, str):
        pieces = [piece.strip() for piece in value.replace(";", ",").split(",") if piece.strip()]
        if len(pieces) == 2:
            try:
                left, right = int(pieces[0]), int(pieces[1])
            except ValueError:
                return None
            return None if left == right else tuple(sorted((left, right)))
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            left, right = int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
        return None if left == right else tuple(sorted((left, right)))
    return None


def _event_pair(row: dict[str, Any]) -> tuple[int, int] | None:
    for key in ("selected_pair", "alternative_pair", "forced_pair", "pair"):
        pair = _pair(row.get(key))
        if pair is not None:
            return pair
    return None


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normal_instance(value: Any) -> str:
    return str(value or "").replace("\\", "/")


def _score_key(pair: tuple[int, int], *, node_id: int | None, depth: int | None) -> str:
    pair_text = f"{int(pair[0])},{int(pair[1])}"
    if node_id is not None and depth is not None:
        return f"node:{int(node_id)}:depth:{int(depth)}:{pair_text}"
    if depth is not None:
        return f"depth:{int(depth)}:{pair_text}"
    if node_id is not None:
        return f"node:{int(node_id)}:{pair_text}"
    return pair_text


def _branch_state_key_from_ancestor_path(path: Any, *, depth: int | None) -> str | None:
    text = str(path or "").strip()
    if not text:
        return "root" if depth == 0 else None
    pieces: list[tuple[int, str]] = []
    for match in re.finditer(
        r"(?:^|[;|])\s*(?:force_pair_path:)?(\d+):(\d+),(\d+)=(same_vehicle|separate_vehicle)",
        text,
    ):
        ordinal = int(match.group(1))
        left = int(match.group(2))
        right = int(match.group(3))
        kind = str(match.group(4))
        i, j = sorted((left, right))
        pieces.append((ordinal, f"RF({i},{j})={kind}"))
    if not pieces:
        return "root" if depth == 0 else None
    pieces.sort(key=lambda item: item[0])
    return ";".join(piece for _ordinal, piece in pieces)


def _branch_state_key_from_constraints(constraints: Any, *, depth: int | None) -> str | None:
    if constraints in (None, ""):
        return "root" if depth == 0 else None
    if isinstance(constraints, str):
        text = constraints.strip()
        if not text:
            return "root" if depth == 0 else None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return text
        constraints = parsed
    if isinstance(constraints, (list, tuple)):
        pieces = [str(item) for item in constraints if str(item)]
        return ";".join(pieces) if pieces else "root"
    return str(constraints)


def _source_log_state_map(path: Path) -> dict[int, str]:
    state_by_node: dict[int, str] = {}
    if not path.exists():
        return state_by_node
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("event") != "journey_node_start":
            continue
        node_id = _int_or_none(event.get("node_id"))
        depth = _int_or_none(event.get("depth"))
        state_key = _branch_state_key_from_constraints(event.get("branch_constraints"), depth=depth)
        if node_id is not None and state_key:
            state_by_node[int(node_id)] = state_key
    return state_by_node


def _branch_state_key_for_event(
    event: dict[str, Any],
    *,
    depth: int | None,
    node_id: int | None,
    source_state_cache: dict[str, dict[int, str]],
) -> str | None:
    direct = _branch_state_key_from_constraints(event.get("branch_state_key"), depth=depth)
    if direct:
        return direct
    direct = _branch_state_key_from_constraints(event.get("branch_constraints"), depth=depth)
    if direct:
        return direct
    ancestor = _branch_state_key_from_ancestor_path(event.get("ancestor_forced_path"), depth=depth)
    if ancestor:
        return ancestor
    source_log_file = event.get("source_log_file")
    if source_log_file in (None, "") or node_id is None:
        return "root" if depth == 0 else None
    source_key = str(source_log_file)
    if source_key not in source_state_cache:
        source_state_cache[source_key] = _source_log_state_map(Path(source_key))
    return source_state_cache[source_key].get(int(node_id)) or ("root" if depth == 0 else None)


def _row_score(row: dict[str, Any]) -> float:
    for field in ("score", "branch_score", "gat_score", "predicted_score"):
        if row.get(field) is None:
            continue
        try:
            return float(row[field])
        except (TypeError, ValueError):
            continue
    return 0.0


def _set_row_score(row: dict[str, Any], score: float) -> None:
    for field in ("score", "branch_score", "gat_score", "predicted_score"):
        if field in row or field in {"score", "branch_score"}:
            row[field] = float(score)


def _row_identity(row: dict[str, Any]) -> tuple[str, str, str | None] | None:
    pair = _pair(row.get("pair") or [row.get("task_i"), row.get("task_j")])
    if pair is None:
        return None
    node_id = _int_or_none(row.get("node_id"))
    depth = _int_or_none(row.get("depth"))
    instance = _normal_instance(row.get("instance_key") or row.get("instance"))
    if not instance:
        scoped = str(row.get("scoped_key") or "")
        if "|" in scoped:
            instance = _normal_instance(scoped.split("|", 1)[0])
    if not instance:
        return None
    branch_state_key = row.get("branch_state_key")
    if branch_state_key in (None, "") and row.get("state_key"):
        state_text = str(row.get("state_key"))
        if state_text.startswith("state:") and "::" in state_text:
            branch_state_key = state_text.split("::", 1)[0].removeprefix("state:")
    return instance, _score_key(pair, node_id=node_id, depth=depth), (
        None if branch_state_key in (None, "") else str(branch_state_key)
    )


def _overlay_candidate(row: dict[str, Any], *, min_positive_gain: float) -> tuple[str, float] | None:
    label_type = str(row.get("tree_policy_label_type") or row.get("label_type") or "")
    gain = _float(row.get("capped_wall_time_gain"))
    status = str(row.get("full_replay_status") or row.get("status") or "")
    is_positive = _float(row.get("y_tree_policy_positive")) > 0.5 or label_type.endswith("positive")
    is_negative = _float(row.get("y_tree_policy_hard_negative")) > 0.5 or label_type.endswith("negative")
    if is_positive and (gain >= float(min_positive_gain) or "strong_positive" in label_type):
        return "boost_positive", gain
    if is_negative:
        return "suppress_negative", gain
    if status == "OPTIMAL" and gain >= float(min_positive_gain):
        return "boost_positive", gain
    return None


def apply_strict_overlay(
    *,
    base_score_rows: Path,
    event_rows: list[Path],
    output_dir: Path,
    report: Path,
    boost_score: float = 0.91,
    suppress_score: float = 0.01,
    min_positive_gain: float = 30.0,
    require_state_for_depth_gt0: bool = True,
) -> dict[str, Any]:
    rows = _load_rows(base_score_rows)
    row_by_identity: dict[tuple[str, str, str | None], dict[str, Any]] = {}
    for row in rows:
        identity = _row_identity(row)
        if identity is not None:
            row_by_identity[identity] = row

    counts: Counter[str] = Counter()
    touched: list[dict[str, Any]] = []
    events_seen = 0
    source_state_cache: dict[str, dict[int, str]] = {}
    for path in event_rows:
        for event in _iter_jsonl(path):
            events_seen += 1
            pair = _event_pair(event)
            instance = _normal_instance(event.get("instance"))
            depth = _int_or_none(event.get("depth"))
            node_id = _int_or_none(event.get("node_id"))
            if pair is None or not instance:
                counts["skipped_invalid_event"] += 1
                continue
            branch_state_key = _branch_state_key_for_event(
                event,
                depth=depth,
                node_id=node_id,
                source_state_cache=source_state_cache,
            )
            if require_state_for_depth_gt0 and (depth or 0) > 0 and not branch_state_key:
                counts["skipped_missing_state_for_deep_event"] += 1
                continue
            action = _overlay_candidate(event, min_positive_gain=min_positive_gain)
            if action is None:
                counts["skipped_unlabeled_or_below_gain"] += 1
                continue
            kind, gain = action
            key = _score_key(pair, node_id=node_id, depth=depth)
            identity = (instance, key, branch_state_key)
            score = float(boost_score) if kind == "boost_positive" else float(suppress_score)
            row = row_by_identity.get(identity)
            old_score = None if row is None else _row_score(row)
            if row is None:
                row = {
                    "schema_version": "gat_tree_policy_strict_overlay_score_row_v1",
                    "diagnostic_only": True,
                    "runs_bpc_or_pricing": False,
                    "production_ready": False,
                    "official_bound_effect": False,
                    "certificate_effect": False,
                    "instance": instance,
                    "instance_key": instance,
                    "node_id": node_id,
                    "depth": depth,
                    "pair": [int(pair[0]), int(pair[1])],
                    "task_i": int(pair[0]),
                    "task_j": int(pair[1]),
                    "key": key,
                    "scoped_key": f"{instance}|{key}",
                }
                rows.append(row)
                row_by_identity[identity] = row
                counts["appended_overlay_row"] += 1
            if kind == "boost_positive":
                score = max(_row_score(row), score)
            else:
                score = min(_row_score(row), score) if old_score is not None else score
            _set_row_score(row, score)
            if branch_state_key:
                row["branch_state_key"] = branch_state_key
                row["branch_constraints"] = branch_state_key.split(";") if branch_state_key != "root" else []
                row["state_key"] = f"state:{branch_state_key}::{key}"
                row["scoped_state_key"] = f"{instance}|state:{branch_state_key}::{key}"
            row["tree_policy_strict_overlay"] = kind
            row["tree_policy_strict_overlay_gain"] = float(gain)
            row["tree_policy_strict_overlay_label_type"] = (
                event.get("tree_policy_label_type") or event.get("label_type")
            )
            row["tree_policy_strict_overlay_policy_run"] = event.get("policy_run")
            row["tree_policy_strict_overlay_source"] = str(path)
            counts[kind] += 1
            touched.append(
                {
                    "kind": kind,
                    "instance": instance,
                    "key": key,
                    "branch_state_key": branch_state_key,
                    "pair": [int(pair[0]), int(pair[1])],
                    "old_score": old_score,
                    "new_score": score,
                    "gain": float(gain),
                    "label_type": event.get("tree_policy_label_type") or event.get("label_type"),
                    "policy_run": event.get("policy_run"),
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    rows_json = output_dir / "journey_branch_score_rows.json"
    rows_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "journey_branch_score_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    score_map = {
        str(row.get("scoped_state_key") or row.get("scoped_key") or row.get("key")): _row_score(row)
        for row in rows
        if row.get("scoped_state_key") or row.get("scoped_key") or row.get("key")
    }
    (output_dir / "journey_branch_score_map.json").write_text(
        json.dumps(score_map, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema_version": "gat_tree_policy_strict_overlay_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "base_score_rows": str(base_score_rows),
        "event_rows": [str(path) for path in event_rows],
        "output_dir": str(output_dir),
        "solver_score_path": str(rows_json),
        "score_row_count": len(rows),
        "events_seen": int(events_seen),
        "boost_score": float(boost_score),
        "suppress_score": float(suppress_score),
        "min_positive_gain": float(min_positive_gain),
        "require_state_for_depth_gt0": bool(require_state_for_depth_gt0),
        "overlay_counts": dict(sorted(counts.items())),
        "touched_rows": touched,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Tree Policy Strict Overlay",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 strict tree-policy replay / controlled replay 标签叠加到 branch score rows。该步骤只读离线日志和标签，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "base_score_rows",
        "event_rows",
        "output_dir",
        "solver_score_path",
        "score_row_count",
        "events_seen",
        "boost_score",
        "suppress_score",
        "min_positive_gain",
        "require_state_for_depth_gt0",
        "overlay_counts",
        "production_ready",
        "official_bound_effect",
        "certificate_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## Touched Rows", ""])
    for row in summary["touched_rows"][:40]:
        lines.append(
            f"- {row['kind']} instance={Path(row['instance']).name} key={row['key']} "
            f"state={row.get('branch_state_key')} score={row['old_score']}->{row['new_score']} "
            f"gain={row['gain']:.3f} label={row.get('label_type')}"
        )
    if len(summary["touched_rows"]) > 40:
        lines.append(f"- ... {len(summary['touched_rows']) - 40} rows omitted")
    lines.extend(["", "## 使用边界", ""])
    lines.append(
        "`journey_branch_score_rows.json` 只影响 Ryan-Foster pair 排序；必须配合 exact pricing closure，不能提供 bound、certificate 或剪枝依据。"
    )
    lines.append(
        "带 `branch_state_key` 的 deep rows 应配合 `journey_branch_candidate_score_require_state_key=True` 使用，避免把某个子树中的正例泄漏到其他分支状态。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-score-rows", required=True, type=Path)
    parser.add_argument("--event-rows", action="append", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--boost-score", type=float, default=0.91)
    parser.add_argument("--suppress-score", type=float, default=0.01)
    parser.add_argument("--min-positive-gain", type=float, default=30.0)
    parser.add_argument(
        "--allow-deep-rows-without-state",
        action="store_true",
        help="Overlay depth>0 rows even when ancestor branch state is unknown.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = apply_strict_overlay(
        base_score_rows=args.base_score_rows,
        event_rows=[Path(path) for path in args.event_rows],
        output_dir=args.output_dir,
        report=args.report,
        boost_score=float(args.boost_score),
        suppress_score=float(args.suppress_score),
        min_positive_gain=float(args.min_positive_gain),
        require_state_for_depth_gt0=not bool(args.allow_deep_rows_without_state),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
