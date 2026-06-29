#!/usr/bin/env python3
"""Apply structural proof-tail risk penalties to Journey branch score rows.

This is an offline, diagnostic-only score-map postprocessor.  It reads an
existing branch score map plus score-selected timeout hard-negative evidence,
then caps scores for:

* exact branch decisions already observed in failed full runs;
* repeated failed Ryan-Foster pairs in non-root contexts;
* high-score deep rows in random-TW families that repeatedly produced
  completion-bound proof-tail timeouts.

It never runs BPC, pricing, RMP, or certificates.  The output may only be used
as an opt-in branch ordering hint.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import json
import math
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_score_structural_risk_overlay")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260628_bpc_future_journey_branch_score_structural_risk_overlay_zh.md"
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if path.is_dir():
        path = path / "score_timeout_hard_negative_rows.jsonl"
    if not path.exists():
        raise SystemExit(f"missing evidence path: {path}")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
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


def _normal_instance(value: Any) -> str:
    return str(value or "").replace("\\", "/")


def _pair(value: Any) -> tuple[int, int] | None:
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
        if len(parts) != 2:
            return None
        try:
            left, right = int(parts[0]), int(parts[1])
        except ValueError:
            return None
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            left, right = int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
    else:
        return None
    if left <= 0 or right <= 0 or left == right:
        return None
    return tuple(sorted((left, right)))


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(parsed):
        return float(default)
    return float(parsed)


def _row_score(row: dict[str, Any]) -> float:
    for field in ("score", "branch_score", "gat_score", "predicted_score"):
        if row.get(field) is None:
            continue
        try:
            parsed = float(row[field])
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed):
            return float(parsed)
    return 0.0


def _set_row_score(row: dict[str, Any], score: float) -> None:
    for field in ("score", "branch_score", "gat_score", "predicted_score"):
        row[field] = float(score)


def _score_key(pair: tuple[int, int], *, node_id: int, depth: int) -> str:
    return f"node:{int(node_id)}:depth:{int(depth)}:{int(pair[0])},{int(pair[1])}"


def _instance_candidates(instance: Any, *, log_file: Any = None) -> set[str]:
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
    return {candidate for candidate in candidates if candidate}


def _scope_candidates(instance: Any, key: str, *, log_file: Any = None) -> set[tuple[str, str]]:
    if not key:
        return set()
    return {(candidate, key) for candidate in _instance_candidates(instance, log_file=log_file)}


def _row_scope_candidates(row: dict[str, Any]) -> set[tuple[str, str]]:
    key = str(row.get("key") or "")
    candidates: set[tuple[str, str]] = set()
    if key:
        for instance in _instance_candidates(row.get("instance_key") or row.get("instance")):
            candidates.add((instance, key))
    scoped = str(row.get("scoped_key") or "")
    if "|" in scoped:
        instance, scoped_key = scoped.split("|", 1)
        for candidate in _instance_candidates(instance):
            candidates.add((candidate, scoped_key))
    return candidates


def _row_pair(row: dict[str, Any]) -> tuple[int, int] | None:
    pair = _pair(row.get("pair"))
    if pair is not None:
        return pair
    candidate = row.get("candidate")
    if isinstance(candidate, dict):
        pair = _pair([candidate.get("task_i"), candidate.get("task_j")])
        if pair is not None:
            return pair
    key = str(row.get("key") or "")
    if ":" in key:
        key = key.rsplit(":", 1)[-1]
    return _pair(key)


def _row_depth(row: dict[str, Any]) -> int:
    if row.get("depth") is not None:
        return _int(row.get("depth"))
    key = str(row.get("key") or "")
    marker = "depth:"
    if marker in key:
        tail = key.split(marker, 1)[1]
        return _int(tail.split(":", 1)[0])
    return 0


def _row_family_site(row: dict[str, Any]) -> tuple[str, str]:
    return _family_site(row.get("instance_key") or row.get("instance"))


def _family_site(instance: Any) -> tuple[str, str]:
    text = _normal_instance(instance)
    pieces = [piece for piece in text.split("/") if piece]
    for index, piece in enumerate(pieces):
        if piece.startswith("tasks_") and index + 1 < len(pieces):
            family = pieces[index + 1]
            site = pieces[index + 2] if index + 2 < len(pieces) else ""
            return family, site
    return "", ""


def _quantile(values: list[float], q: float, default: float) -> float:
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return float(default)
    if len(clean) == 1:
        return float(clean[0])
    pos = max(0.0, min(1.0, q)) * (len(clean) - 1)
    low = int(math.floor(pos))
    high = int(math.ceil(pos))
    if low == high:
        return float(clean[low])
    weight = pos - low
    return float(clean[low] * (1.0 - weight) + clean[high] * weight)


def _load_evidence(paths: list[Path]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    exact: dict[tuple[str, str], dict[str, Any]] = {}
    for path in paths:
        for raw in _iter_jsonl(path):
            if _float(raw.get("y_branch_score_hard_negative")) <= 0.5:
                continue
            pair = _pair(raw.get("selected_pair"))
            if pair is None:
                continue
            depth = _int(raw.get("depth"))
            node_id = _int(raw.get("node_id"))
            key = _score_key(pair, node_id=node_id, depth=depth)
            row = dict(raw)
            row["selected_pair_tuple"] = pair
            row["score_key"] = key
            row["depth_int"] = depth
            row["selected_score_float"] = _float(raw.get("selected_score"))
            row["family_site"] = _family_site(raw.get("instance"))
            row["source_evidence_path"] = str(path)
            rows.append(row)
            for scope in _scope_candidates(raw.get("instance"), key, log_file=raw.get("log_file")):
                exact[scope] = row
    return rows, exact


def _risk_stats(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    pair_counts: Counter[tuple[int, int]] = Counter()
    pair_deep_counts: Counter[tuple[int, int]] = Counter()
    family_counts: Counter[str] = Counter()
    family_pair_counts: Counter[tuple[str, tuple[int, int]]] = Counter()
    site_counts: Counter[tuple[str, str]] = Counter()
    depths: list[float] = []
    scores: list[float] = []
    completion_retries: list[float] = []
    for row in evidence:
        pair = row["selected_pair_tuple"]
        depth = int(row["depth_int"])
        family, site = row["family_site"]
        pair_counts[pair] += 1
        if depth >= 1:
            pair_deep_counts[pair] += 1
        if family:
            family_counts[family] += 1
            family_pair_counts[(family, pair)] += 1
        if family or site:
            site_counts[(family, site)] += 1
        depths.append(float(depth))
        scores.append(float(row["selected_score_float"]))
        completion_retries.append(_float(row.get("run_completion_bound_retry_count")))
    return {
        "pair_counts": pair_counts,
        "pair_deep_counts": pair_deep_counts,
        "family_counts": family_counts,
        "family_pair_counts": family_pair_counts,
        "site_counts": site_counts,
        "depth_p50": _quantile(depths, 0.50, 4.0),
        "depth_p75": _quantile(depths, 0.75, 6.0),
        "score_p50": _quantile(scores, 0.50, 0.85),
        "score_p75": _quantile(scores, 0.75, 0.90),
        "completion_retry_p50": _quantile(completion_retries, 0.50, 0.0),
        "completion_retry_p75": _quantile(completion_retries, 0.75, 0.0),
    }


def _cap(row: dict[str, Any], cap_score: float, reason: str, reasons: list[str]) -> None:
    old = _row_score(row)
    new = min(old, float(cap_score))
    _set_row_score(row, new)
    reasons.append(reason)
    row["structural_proof_tail_overlay"] = "suppress_structural_proof_tail"
    row["structural_proof_tail_old_score"] = float(old)
    row["structural_proof_tail_score"] = float(new)


def apply_structural_overlay(
    *,
    base_score_rows: Path,
    evidence_paths: list[Path],
    output_dir: Path,
    report: Path,
    exact_suppress_score: float = 0.03,
    repeated_pair_cap_score: float = 0.35,
    high_depth_cap_score: float = 0.55,
    family_retry_cap_score: float = 0.65,
    structural_min_depth: int = 4,
    repeated_pair_min_depth: int = 3,
    repeated_pair_min_count: int = 2,
    family_min_count: int = 4,
    high_depth_quantile: float = 0.75,
    high_score_quantile: float = 0.75,
) -> dict[str, Any]:
    rows = _load_rows(base_score_rows)
    evidence, exact_scopes = _load_evidence(evidence_paths)
    stats = _risk_stats(evidence)
    counts: Counter[str] = Counter()
    touched: list[dict[str, Any]] = []
    high_depth_threshold = max(
        int(structural_min_depth),
        int(math.floor(_quantile(
            [float(row["depth_int"]) for row in evidence],
            float(high_depth_quantile),
            float(stats["depth_p75"]),
        ))),
    )
    high_score_threshold = max(
        0.0,
        min(
            0.99,
            _quantile(
                [float(row["selected_score_float"]) for row in evidence],
                float(high_score_quantile),
                float(stats["score_p75"]),
            ),
        ),
    )

    pair_counts: Counter[tuple[int, int]] = stats["pair_counts"]
    pair_deep_counts: Counter[tuple[int, int]] = stats["pair_deep_counts"]
    family_counts: Counter[str] = stats["family_counts"]
    family_pair_counts: Counter[tuple[str, tuple[int, int]]] = stats["family_pair_counts"]

    for row in rows:
        old = _row_score(row)
        depth = _row_depth(row)
        pair = _row_pair(row)
        family, site = _row_family_site(row)
        reasons: list[str] = []
        exact_scope = next((scope for scope in _row_scope_candidates(row) if scope in exact_scopes), None)
        if exact_scope is not None:
            _cap(row, exact_suppress_score, "exact_timeout_hard_negative", reasons)
            row["structural_proof_tail_exact_evidence"] = {
                "instance": exact_scopes[exact_scope].get("instance"),
                "key": exact_scopes[exact_scope].get("score_key"),
                "source_experiment": exact_scopes[exact_scope].get("source_experiment"),
            }
            counts["exact_timeout_hard_negative"] += 1
        elif pair is not None and depth >= int(repeated_pair_min_depth):
            deep_pair_count = int(pair_deep_counts.get(pair, 0))
            family_pair_count = int(family_pair_counts.get((family, pair), 0)) if family else 0
            if deep_pair_count >= int(repeated_pair_min_count) or family_pair_count >= int(repeated_pair_min_count):
                _cap(
                    row,
                    repeated_pair_cap_score,
                    f"repeated_failed_pair:{pair[0]},{pair[1]}",
                    reasons,
                )
                row["structural_failed_pair_count"] = int(pair_counts.get(pair, 0))
                row["structural_failed_deep_pair_count"] = deep_pair_count
                row["structural_failed_family_pair_count"] = family_pair_count
                counts["repeated_failed_pair"] += 1
            score_after_pair = _row_score(row)
            if family and int(family_counts.get(family, 0)) >= int(family_min_count):
                if depth >= high_depth_threshold and old >= high_score_threshold:
                    _cap(
                        row,
                        high_depth_cap_score,
                        f"family_deep_high_score:{family}",
                        reasons,
                    )
                    row["structural_high_depth_threshold"] = int(high_depth_threshold)
                    row["structural_high_score_threshold"] = float(high_score_threshold)
                    counts["family_deep_high_score"] += 1
                elif depth >= int(structural_min_depth) and score_after_pair >= high_score_threshold:
                    _cap(
                        row,
                        family_retry_cap_score,
                        f"family_retry_tail_risk:{family}",
                        reasons,
                    )
                    row["structural_high_score_threshold"] = float(high_score_threshold)
                    counts["family_retry_tail_risk"] += 1
        if reasons:
            row["structural_proof_tail_reasons"] = reasons
            row["structural_proof_tail_diagnostic_only"] = True
            row["official_bound_effect"] = False
            row["certificate_effect"] = False
            touched.append(
                {
                    "instance": row.get("instance_key") or row.get("instance"),
                    "key": row.get("key"),
                    "pair": list(pair) if pair is not None else None,
                    "depth": depth,
                    "family": family,
                    "old": old,
                    "new": _row_score(row),
                    "reasons": reasons,
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
        str(row.get("scoped_key") or row.get("key")): _row_score(row)
        for row in rows
        if row.get("scoped_key") or row.get("key")
    }
    (output_dir / "journey_branch_score_map.json").write_text(
        json.dumps(score_map, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema_version": "journey_branch_score_structural_risk_overlay_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "base_score_rows": str(base_score_rows),
        "evidence_paths": [str(path) for path in evidence_paths],
        "output_dir": str(output_dir),
        "solver_score_path": str(rows_json),
        "score_row_count": len(rows),
        "evidence_row_count": len(evidence),
        "exact_evidence_scope_count": len(exact_scopes),
        "overlay_counts": dict(sorted(counts.items())),
        "touched_row_count": len(touched),
        "exact_suppress_score": float(exact_suppress_score),
        "repeated_pair_cap_score": float(repeated_pair_cap_score),
        "high_depth_cap_score": float(high_depth_cap_score),
        "family_retry_cap_score": float(family_retry_cap_score),
        "structural_min_depth": int(structural_min_depth),
        "repeated_pair_min_depth": int(repeated_pair_min_depth),
        "repeated_pair_min_count": int(repeated_pair_min_count),
        "family_min_count": int(family_min_count),
        "high_depth_quantile": float(high_depth_quantile),
        "high_score_quantile": float(high_score_quantile),
        "high_depth_threshold": int(high_depth_threshold),
        "high_score_threshold": float(high_score_threshold),
        "depth_p50": float(stats["depth_p50"]),
        "depth_p75": float(stats["depth_p75"]),
        "score_p50": float(stats["score_p50"]),
        "score_p75": float(stats["score_p75"]),
        "completion_retry_p50": float(stats["completion_retry_p50"]),
        "completion_retry_p75": float(stats["completion_retry_p75"]),
        "family_counts": dict(sorted(stats["family_counts"].items())),
        "top_failed_pairs": [
            {"pair": list(pair), "count": count}
            for pair, count in stats["pair_counts"].most_common(20)
        ],
        "touched_rows_sample": touched[:200],
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
        "# Journey Branch Score Structural Proof-Tail Overlay",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 full-run timeout hard-negative 从精确 key 扩展到结构性 proof-tail 风险：深层重复失败 pair、同 random-TW family 的深层高分路径会被降分。该脚本只改 opt-in score map，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"base_score_rows = {summary['base_score_rows']}",
        f"evidence_paths = {summary['evidence_paths']}",
        f"output_dir = {summary['output_dir']}",
        f"score_row_count = {summary['score_row_count']}",
        f"evidence_row_count = {summary['evidence_row_count']}",
        f"exact_evidence_scope_count = {summary['exact_evidence_scope_count']}",
        f"overlay_counts = {summary['overlay_counts']}",
        f"touched_row_count = {summary['touched_row_count']}",
        f"depth_p50 = {summary['depth_p50']:.3f}",
        f"depth_p75 = {summary['depth_p75']:.3f}",
        f"score_p50 = {summary['score_p50']:.6f}",
        f"score_p75 = {summary['score_p75']:.6f}",
        f"completion_retry_p50 = {summary['completion_retry_p50']:.3f}",
        f"completion_retry_p75 = {summary['completion_retry_p75']:.3f}",
        f"high_depth_threshold = {summary['high_depth_threshold']}",
        f"high_score_threshold = {summary['high_score_threshold']:.6f}",
        f"repeated_pair_min_depth = {summary['repeated_pair_min_depth']}",
        "production_ready = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## Top Failed Pairs",
        "",
    ]
    for item in summary["top_failed_pairs"][:10]:
        lines.append(f"- {item['pair']}: {item['count']}")
    lines.extend(["", "## Touched Rows Sample", ""])
    for row in summary["touched_rows_sample"][:30]:
        lines.append(
            "- "
            f"{Path(str(row.get('instance') or '')).name} {row.get('key')} "
            f"depth={row.get('depth')} {float(row.get('old', 0.0)):.6f}->{float(row.get('new', 0.0)):.6f} "
            f"reason={','.join(str(reason) for reason in row.get('reasons') or [])}"
        )
    lines.extend(["", "## 边界", ""])
    lines.append(
        "输出只能用于 branch ordering。它不能剪枝，不能替代 exact pricing closure，也不能作为 official lower bound。root 只做精确失败 row suppress，不做结构性泛化 suppress。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-score-rows", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--exact-suppress-score", type=float, default=0.03)
    parser.add_argument("--repeated-pair-cap-score", type=float, default=0.35)
    parser.add_argument("--high-depth-cap-score", type=float, default=0.55)
    parser.add_argument("--family-retry-cap-score", type=float, default=0.65)
    parser.add_argument("--structural-min-depth", type=int, default=4)
    parser.add_argument("--repeated-pair-min-depth", type=int, default=3)
    parser.add_argument("--repeated-pair-min-count", type=int, default=2)
    parser.add_argument("--family-min-count", type=int, default=4)
    parser.add_argument("--high-depth-quantile", type=float, default=0.75)
    parser.add_argument("--high-score-quantile", type=float, default=0.75)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = apply_structural_overlay(
        base_score_rows=args.base_score_rows,
        evidence_paths=list(args.evidence),
        output_dir=args.output_dir,
        report=args.report,
        exact_suppress_score=args.exact_suppress_score,
        repeated_pair_cap_score=args.repeated_pair_cap_score,
        high_depth_cap_score=args.high_depth_cap_score,
        family_retry_cap_score=args.family_retry_cap_score,
        structural_min_depth=args.structural_min_depth,
        repeated_pair_min_depth=args.repeated_pair_min_depth,
        repeated_pair_min_count=args.repeated_pair_min_count,
        family_min_count=args.family_min_count,
        high_depth_quantile=args.high_depth_quantile,
        high_score_quantile=args.high_score_quantile,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if int(summary["touched_row_count"]) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
