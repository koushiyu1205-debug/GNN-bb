#!/usr/bin/env python3
"""Apply proof-risk evidence to opt-in Journey branch score rows.

The overlay is intentionally conservative and diagnostic-only.  It reads
completed branch-score smoke/full-run analysis summaries and adjusts score rows
for already-observed root branch decisions:

* boost full-run positive branch choices;
* suppress branch choices that changed the root pair but still failed to close;
* suppress timeout hard-negative rows harvested from score-gated root probes.
* suppress paired child-probe hard-negative proxies harvested from fixed-budget
  branch replay probes.

It does not run BPC, pricing, RMP, or produce official bounds/certificates.  The
output can only be used as an opt-in branch ordering score map.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_branch_action_proofrisk_overlay")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260626_bpc_future_gat_branch_action_proofrisk_overlay_zh.md"
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _score_key(pair: list[int] | tuple[int, int], *, node_id: int = 0, depth: int = 0) -> str:
    left, right = sorted((int(pair[0]), int(pair[1])))
    return f"node:{int(node_id)}:depth:{int(depth)}:{left},{right}"


def _wall(item: dict[str, Any], key: str, default: float = 600.0) -> float:
    try:
        value = float(item.get(key))
    except (TypeError, ValueError):
        return float(default)
    if value != value:
        return float(default)
    return float(value)


def _normal_instance(value: Any) -> str:
    return str(value or "").replace("\\", "/")


def _scope_candidates(instance: Any, key: str, *, log_file: Any = None) -> set[tuple[str, str]]:
    normalized_key = str(key or "")
    if not normalized_key:
        return set()
    candidates: set[str] = set()
    instance_text = _normal_instance(instance)
    if instance_text:
        candidates.add(instance_text)
        candidates.add(Path(instance_text).name)
    log_text = _normal_instance(log_file)
    if log_text:
        marker = "BPC_future/logical_graph/"
        idx = log_text.find(marker)
        if idx >= 0:
            canonical = log_text[idx:]
            if canonical.endswith(".jsonl"):
                canonical = canonical[: -len(".jsonl")]
            candidates.add(canonical)
            candidates.add(Path(canonical).name)
    return {(candidate, normalized_key) for candidate in candidates if candidate}


def _row_scope_candidates(row: dict[str, Any]) -> set[tuple[str, str]]:
    scope = _row_scope(row)
    candidates: set[tuple[str, str]] = set()
    if scope is not None:
        instance, key = scope
        candidates.update(_scope_candidates(instance, key))
    return candidates


def _evidence_from_analysis(
    analysis_path: Path,
    *,
    min_wall_improvement: float,
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    payload = _read_json(analysis_path)
    positives: dict[tuple[str, str], dict[str, Any]] = {}
    negatives: dict[tuple[str, str], dict[str, Any]] = {}
    for item in payload.get("items") or []:
        if not isinstance(item, dict) or not bool(item.get("root_changed")):
            continue
        pair = item.get("root_selected_pair")
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        instance = _normal_instance(item.get("instance"))
        if not instance:
            continue
        node_id = int(item.get("root_node_id") or 0)
        depth = int(item.get("root_depth") or 0)
        key = _score_key(pair, node_id=node_id, depth=depth)
        baseline_status = str(item.get("baseline_status") or "")
        status = str(item.get("status") or "")
        baseline_wall = _wall(item, "baseline_wall")
        alternative_wall = _wall(item, "wall")
        gain = baseline_wall - alternative_wall
        evidence = {
            "analysis": str(analysis_path),
            "instance": instance,
            "key": key,
            "pair": pair,
            "baseline_status": baseline_status,
            "alternative_status": status,
            "baseline_wall": baseline_wall,
            "alternative_wall": alternative_wall,
            "gain": gain,
        }
        if status == "OPTIMAL" and (
            baseline_status != "OPTIMAL" or gain >= float(min_wall_improvement)
        ):
            positives[(instance, key)] = evidence
        elif status != "OPTIMAL":
            negatives[(instance, key)] = evidence
    return positives, negatives


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise SystemExit(f"missing timeout evidence: {path}")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _evidence_from_timeout_rows(
    evidence_path: Path,
) -> dict[tuple[str, str], dict[str, Any]]:
    negatives: dict[tuple[str, str], dict[str, Any]] = {}
    for item in _iter_jsonl(evidence_path):
        try:
            hard_negative = float(item.get("y_branch_score_hard_negative") or 0.0) > 0.5
        except (TypeError, ValueError):
            hard_negative = False
        if not hard_negative:
            continue
        pair = item.get("selected_pair")
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        key = _score_key(
            pair,
            node_id=int(item.get("node_id") or 0),
            depth=int(item.get("depth") or 0),
        )
        baseline_wall = _wall(item, "baseline_wall_time")
        alternative_wall = _wall(item, "alternative_wall_time")
        evidence = {
            "analysis": str(evidence_path),
            "instance": _normal_instance(item.get("instance")),
            "log_file": _normal_instance(item.get("log_file")),
            "key": key,
            "pair": pair,
            "baseline_status": str(item.get("baseline_status") or ""),
            "alternative_status": str(item.get("alternative_status") or ""),
            "baseline_wall": baseline_wall,
            "alternative_wall": alternative_wall,
            "gain": baseline_wall - alternative_wall,
            "selected_score": item.get("selected_score"),
            "selected_score_source": item.get("selected_score_source"),
            "label_type": item.get("label_type"),
            "proofrisk_overlay_evidence_kind": "timeout_hard_negative",
        }
        for scope in _scope_candidates(
            item.get("instance"),
            key,
            log_file=item.get("log_file"),
        ):
            negatives[scope] = evidence
    return negatives


def _evidence_from_paired_probe_rows(
    evidence_path: Path,
    *,
    min_wall_improvement: float,
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    positives: dict[tuple[str, str], dict[str, Any]] = {}
    negatives: dict[tuple[str, str], dict[str, Any]] = {}
    for item in _iter_jsonl(evidence_path):
        if str(item.get("pair_role") or "") != "alternative":
            continue
        pair = item.get("forced_pair")
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        key = _score_key(
            pair,
            node_id=int(item.get("source_node_id") or 0),
            depth=int(item.get("source_depth") or 0),
        )
        label_type = str(item.get("paired_label_type") or "")
        wall_gain = _wall(item, "paired_wall_time_gain", 0.0)
        alternative_wall = _wall(item, "wall_time", 600.0)
        baseline_wall = alternative_wall + wall_gain
        evidence = {
            "analysis": str(evidence_path),
            "instance": _normal_instance(item.get("instance")),
            "key": key,
            "pair": pair,
            "baseline_status": "BASELINE_CHILD_PROBE",
            "alternative_status": str(item.get("status") or "CHILD_PROBE"),
            "baseline_wall": baseline_wall,
            "alternative_wall": alternative_wall,
            "gain": wall_gain,
            "paired_label_type": label_type,
            "child_completion_bound_retry_gain": item.get("paired_child_cb_retry_gain"),
            "child_fathomed_count": item.get("child_fathomed_count"),
            "child_proof_cpu": item.get("child_proof_cpu"),
            "proofrisk_overlay_evidence_kind": (
                "paired_probe_positive_proxy"
                if label_type == "positive_proxy"
                else "paired_probe_hard_negative"
            ),
        }
        scopes = _scope_candidates(item.get("instance"), key)
        if label_type == "positive_proxy" and wall_gain >= float(min_wall_improvement):
            for scope in scopes:
                positives[scope] = evidence
        elif label_type == "hard_negative_proxy":
            for scope in scopes:
                negatives[scope] = evidence
    return positives, negatives


def _load_rows(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if isinstance(payload, list):
        return [dict(row) for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        rows = payload.get("rows")
        if isinstance(rows, list):
            return [dict(row) for row in rows if isinstance(row, dict)]
    raise SystemExit(f"unsupported score row payload: {path}")


def _row_scope(row: dict[str, Any]) -> tuple[str, str] | None:
    instance = _normal_instance(row.get("instance_key") or row.get("instance"))
    key = str(row.get("key") or "")
    if instance and key:
        return instance, key
    scoped = str(row.get("scoped_key") or "")
    if "|" in scoped:
        instance, key = scoped.split("|", 1)
        return _normal_instance(instance), key
    return None


def _row_score(row: dict[str, Any]) -> float:
    for field in ("score", "branch_score", "gat_score", "predicted_score"):
        if row.get(field) is not None:
            try:
                return float(row[field])
            except (TypeError, ValueError):
                continue
    return 0.0


def _set_row_score(row: dict[str, Any], value: float) -> None:
    for field in ("score", "gat_score", "predicted_score", "branch_score"):
        row[field] = float(value)


def apply_overlay(
    *,
    base_score_rows: Path,
    analyses: list[Path],
    timeout_evidence: list[Path] | None = None,
    paired_probe_evidence: list[Path] | None = None,
    output_dir: Path,
    report: Path,
    boost_score: float = 0.68,
    suppress_score: float = 0.05,
    min_wall_improvement: float = 30.0,
) -> dict[str, Any]:
    positives: dict[tuple[str, str], dict[str, Any]] = {}
    negatives: dict[tuple[str, str], dict[str, Any]] = {}
    for analysis in analyses:
        pos, neg = _evidence_from_analysis(
            analysis,
            min_wall_improvement=min_wall_improvement,
        )
        positives.update(pos)
        negatives.update({key: value for key, value in neg.items() if key not in positives})
    timeout_negatives: dict[tuple[str, str], dict[str, Any]] = {}
    for evidence_path in timeout_evidence or []:
        timeout_negatives.update(_evidence_from_timeout_rows(evidence_path))
    negatives.update(
        {
            key: value
            for key, value in timeout_negatives.items()
            if key not in positives
        }
    )
    paired_probe_positives: dict[tuple[str, str], dict[str, Any]] = {}
    paired_probe_negatives: dict[tuple[str, str], dict[str, Any]] = {}
    for evidence_path in paired_probe_evidence or []:
        pos, neg = _evidence_from_paired_probe_rows(
            evidence_path,
            min_wall_improvement=min_wall_improvement,
        )
        paired_probe_positives.update(pos)
        paired_probe_negatives.update(neg)
    positives.update(
        {
            key: value
            for key, value in paired_probe_positives.items()
            if key not in negatives
        }
    )
    negatives.update(
        {
            key: value
            for key, value in paired_probe_negatives.items()
            if key not in positives
        }
    )

    rows = _load_rows(base_score_rows)
    counts: Counter[str] = Counter()
    touched: list[dict[str, Any]] = []
    for row in rows:
        scope = _row_scope(row)
        if scope is None:
            continue
        scope_candidates = _row_scope_candidates(row)
        old = _row_score(row)
        positive_scope = next((candidate for candidate in scope_candidates if candidate in positives), None)
        negative_scope = next((candidate for candidate in scope_candidates if candidate in negatives), None)
        if positive_scope is not None:
            evidence = positives[positive_scope]
            new = max(old, float(boost_score))
            _set_row_score(row, new)
            row["proofrisk_overlay"] = "boost_positive"
            row["proofrisk_overlay_gain"] = evidence["gain"]
            row["proofrisk_overlay_status_pair"] = (
                f"{evidence['baseline_status']}->{evidence['alternative_status']}"
            )
            counts["boost_positive"] += 1
            touched.append({"kind": "boost_positive", "old": old, "new": new, **evidence})
        elif negative_scope is not None:
            evidence = negatives[negative_scope]
            evidence_kind = str(evidence.get("proofrisk_overlay_evidence_kind") or "changed_nonoptimal")
            new = min(old, float(suppress_score))
            _set_row_score(row, new)
            if evidence_kind == "timeout_hard_negative":
                overlay_kind = "suppress_timeout_hard_negative"
            elif evidence_kind == "paired_probe_hard_negative":
                overlay_kind = "suppress_paired_probe_hard_negative"
            else:
                overlay_kind = "suppress_changed_nonoptimal"
            row["proofrisk_overlay"] = overlay_kind
            row["proofrisk_overlay_evidence_kind"] = evidence_kind
            row["proofrisk_overlay_gain"] = evidence["gain"]
            row["proofrisk_overlay_status_pair"] = (
                f"{evidence['baseline_status']}->{evidence['alternative_status']}"
            )
            if evidence_kind == "timeout_hard_negative":
                count_key = "suppress_timeout_hard_negative"
            elif evidence_kind == "paired_probe_hard_negative":
                count_key = "suppress_paired_probe_hard_negative"
            else:
                count_key = "suppress_negative"
            counts[count_key] += 1
            touched.append({"kind": overlay_kind, "old": old, "new": new, **evidence})

    output_dir.mkdir(parents=True, exist_ok=True)
    rows_json = output_dir / "journey_branch_score_rows.json"
    rows_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "journey_branch_score_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    score_map = {
        str(row.get("scoped_key") or row.get("key")): _row_score(row)
        for row in rows
        if row.get("scoped_key") or row.get("key")
    }
    (output_dir / "journey_branch_score_map.json").write_text(
        json.dumps(score_map, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema_version": "gat_branch_action_proofrisk_overlay_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "base_score_rows": str(base_score_rows),
        "analysis_paths": [str(path) for path in analyses],
        "timeout_evidence_paths": [str(path) for path in timeout_evidence or []],
        "paired_probe_evidence_paths": [str(path) for path in paired_probe_evidence or []],
        "output_dir": str(output_dir),
        "solver_score_path": str(rows_json),
        "boost_score": float(boost_score),
        "suppress_score": float(suppress_score),
        "min_wall_improvement": float(min_wall_improvement),
        "score_row_count": len(rows),
        "positive_overlay_keys": len(positives),
        "negative_overlay_keys": len(negatives),
        "timeout_negative_overlay_keys": len(timeout_negatives),
        "paired_probe_positive_overlay_keys": len(paired_probe_positives),
        "paired_probe_negative_overlay_keys": len(paired_probe_negatives),
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
        "# GAT Branch Action Proof-Risk Overlay",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把已完成 branch-score 实验中的整实例正负 evidence、timeout hard-negative evidence 和 paired child-probe hard-negative proxy 叠加到 score rows：严格收益分支 boost，changed 后仍非最优或已验证 timeout/paired-probe 高风险的分支 suppress。该脚本只读完成结果，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"base_score_rows = {summary['base_score_rows']}",
        f"analysis_paths = {summary['analysis_paths']}",
        f"timeout_evidence_paths = {summary.get('timeout_evidence_paths', [])}",
        f"paired_probe_evidence_paths = {summary.get('paired_probe_evidence_paths', [])}",
        f"output_dir = {summary['output_dir']}",
        f"score_row_count = {summary['score_row_count']}",
        f"positive_overlay_keys = {summary['positive_overlay_keys']}",
        f"negative_overlay_keys = {summary['negative_overlay_keys']}",
        f"timeout_negative_overlay_keys = {summary.get('timeout_negative_overlay_keys', 0)}",
        f"paired_probe_positive_overlay_keys = {summary.get('paired_probe_positive_overlay_keys', 0)}",
        f"paired_probe_negative_overlay_keys = {summary.get('paired_probe_negative_overlay_keys', 0)}",
        f"overlay_counts = {summary['overlay_counts']}",
        "production_ready = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## Overlay Rows",
        "",
    ]
    for row in summary["touched_rows"]:
        lines.append(
            "- "
            f"{row['kind']}: {Path(row['instance']).name} {row['key']} "
            f"{float(row['old']):.6f}->{float(row['new']):.6f}, "
            f"gain={float(row['gain']):.3f}, "
            f"{row['baseline_status']}->{row['alternative_status']}, "
            f"evidence={row.get('proofrisk_overlay_evidence_kind', 'full_run')}"
        )
    lines.extend(["", "## 边界", ""])
    lines.append(
        "输出只用于 opt-in branch ordering。它不能剪枝，不能替代 exact pricing closure，也不能作为 official lower bound。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-score-rows", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, action="append", default=[])
    parser.add_argument("--timeout-evidence", type=Path, action="append", default=[])
    parser.add_argument("--paired-probe-evidence", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--boost-score", type=float, default=0.68)
    parser.add_argument("--suppress-score", type=float, default=0.05)
    parser.add_argument("--min-wall-improvement", type=float, default=30.0)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = apply_overlay(
        base_score_rows=args.base_score_rows,
        analyses=list(args.analysis),
        timeout_evidence=list(args.timeout_evidence),
        paired_probe_evidence=list(args.paired_probe_evidence),
        output_dir=args.output_dir,
        report=args.report,
        boost_score=float(args.boost_score),
        suppress_score=float(args.suppress_score),
        min_wall_improvement=float(args.min_wall_improvement),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if int(summary["positive_overlay_keys"]) + int(summary["negative_overlay_keys"]) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
