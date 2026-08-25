#!/usr/bin/env python3
"""Verify Python/C++ Temporal-GAT parity and Native inference p99."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import exp, log
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    ensure_not_terminal, mark_terminal_negative,
)

from lunar_ice_bpc.guidance.temporal_frontier_gat_v1 import (  # noqa: E402
    build_temporal_gat_model, portable_temporal_forward,
)


def _models(bundle):
    import torch

    output = []
    for row in bundle["models"]:
        model = build_temporal_gat_model().double().eval()
        state = {}
        for name, tensor in row["tensors"].items():
            state[name] = torch.tensor(
                tensor["values"], dtype=torch.float64
            ).reshape(tensor["shape"])
        model.load_state_dict(state, strict=True)
        output.append(model)
    return output


def _draw(rng, group):
    values = []
    for lower, upper in zip(group["minimum"], group["maximum"]):
        if upper <= lower:
            values.append(float(lower))
        else:
            values.append(rng.uniform(float(lower), float(upper)))
    return values


def _graph(
    rng, nodes, node_group, edge_group, *, context=False,
    label_nodes: int | None = None,
):
    node_features = [_draw(rng, node_group) for _ in range(nodes)]
    if label_nodes is not None:
        if not 0 < int(label_nodes) < nodes:
            raise ValueError("synthetic type-wise graph requires both node types")
        for index, row in enumerate(node_features):
            row[24] = 1.0 if index < int(label_nodes) else 0.0
            row[25] = 0.0 if index < int(label_nodes) else 1.0
    value = {
        "node_features": node_features,
        "edges": [{
            "source": index, "target": index,
            "features": _draw(rng, edge_group),
        } for index in range(nodes)],
    }
    if context:
        value["context_features"] = [0.0] * 28
    return value


def _synthetic(bundle, count):
    normalization = bundle["normalization"]
    output = []
    for index in range(count):
        rng = random.Random(260819000 + index)
        scale = 30 if index % 2 == 0 else 50
        output.append({
            "cell_t0": _graph(
                rng, 64, normalization["cell_node"],
                normalization["cell_edge"], context=True,
            ),
            "cell_tk": _graph(
                rng, 64, normalization["cell_node"],
                normalization["cell_edge"], context=True,
            ),
            "graph_t0": _graph(
                rng, scale + 32, normalization["node"], normalization["edge"],
                label_nodes=32,
            ),
            "graph_tk": _graph(
                rng, scale + 36, normalization["node"], normalization["edge"],
                label_nodes=36,
            ),
            "counter_features": _draw(rng, normalization["counter"]),
            "context_features": _draw(rng, normalization["context"]),
            "scale": scale,
        })
    return output


def _calibrate(value, calibration):
    if calibration["kind"] == "constant":
        return float(calibration["probability"])
    value = max(1e-7, min(1 - 1e-7, value))
    transformed = float(calibration["a"]) * log(value / (1 - value)) + float(
        calibration["b"]
    )
    return 1.0 / (1.0 + exp(-transformed))


def _action(outputs, bundle, scale):
    calibration = bundle["calibration_by_scale"][str(scale)]
    threshold = bundle["thresholds_by_scale"][str(scale)]
    benefit = _calibrate(
        sum(row[0] for row in outputs) / len(outputs), calibration["benefit"]
    )
    adverse = _calibrate(max(row[2] for row in outputs), calibration["adverse"])
    gain = max(0.0, min(
        1.0,
        min(row[1] for row in outputs) * float(calibration["gain_scale"]),
    ))
    expected = benefit * gain
    disagreement = max(
        max(row[index] for row in outputs) - min(row[index] for row in outputs)
        for index in range(3)
    )
    selected = (
        benefit >= float(threshold["minimum_benefit_probability"]) and
        adverse <= float(threshold["maximum_adverse_probability"]) and
        expected >= float(threshold["minimum_expected_gain"]) and
        expected - float(threshold["adverse_penalty"]) * adverse > 0 and
        disagreement <= float(threshold["maximum_disagreement"])
    )
    return "CONTINUE_QD1" if selected else "MIGRATE_BACK_TO_Q0"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--native-build", type=Path, required=True)
    parser.add_argument("--synthetic-count", type=int, default=500)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        ensure_not_terminal(args.run_root)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if int(args.synthetic_count) != 500:
        raise SystemExit("production portable audit requires exactly 500 synthetic graphs")
    source_path = args.run_root.resolve() / "source.freeze.json"
    if not source_path.is_file():
        raise SystemExit("Temporal-GAT source freeze is missing")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    native_binaries = sorted(args.native_build.resolve().glob(
        "lunar_spprc_native*.so"
    ))
    if (
        Path(str(source.get("native_build_dir") or "")).resolve()
            != args.native_build.resolve()
        or len(native_binaries) != 1
        or hashlib.sha256(native_binaries[0].read_bytes()).hexdigest()
            != str(source.get("native_binary_sha256") or "")
    ):
        raise SystemExit("portable audit Native/source binding drift")
    sys.path.insert(0, str(args.native_build.resolve()))
    import lunar_spprc_native as native

    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    if (
        dict(bundle.get("bindings") or {}).get("dataset_sha256")
            != hashlib.sha256(args.dataset.read_bytes()).hexdigest()
        or dataset.get("source_freeze_sha256")
            != hashlib.sha256(source_path.read_bytes()).hexdigest()
    ):
        raise SystemExit("portable audit bundle/dataset/source binding drift")
    calibration_selected_rows = [
        row for row in dataset["rows"]
        if row.get("partition") == "calibration"
        and int(row["k"]) == int(bundle["trial_pop_budget_by_scale"][
            str(row["scale"])
        ])
    ]
    calibration_rows = [
        row for row in calibration_selected_rows
        if bool(row.get("model_eligible_after_trial"))
    ]
    if not calibration_selected_rows or not calibration_rows or any(
        row.get("temporal_graph") is None for row in calibration_rows
    ):
        mark_terminal_negative(
            args.run_root, stage="PORTABLE_PARITY",
            reason="PORTABLE_CALIBRATION_GRAPH_COVERAGE_DRIFT",
            detail={
                "calibration_selected_context_count": len(
                    calibration_selected_rows
                ),
                "calibration_graph_count": len(calibration_rows),
            },
        )
        raise SystemExit("portable audit calibration graph coverage drift")
    graphs = [row["temporal_graph"] for row in calibration_rows]
    graphs.extend(_synthetic(bundle, int(args.synthetic_count)))
    models = _models(bundle)
    maximum_error = 0.0
    action_mismatch = 0
    inference_ms = []
    for offset in range(0, len(graphs), 50):
        batch = graphs[offset:offset + 50]
        selected_by_scale = {}
        for scale in (30, 50):
            selected = dict(bundle)
            selected["selected_scale"] = scale
            selected["calibration"] = bundle["calibration_by_scale"][str(scale)]
            selected["thresholds"] = bundle["thresholds_by_scale"][str(scale)]
            selected_by_scale[scale] = selected
        # A batch cannot mix selected_scale because Native validates the
        # scale-bound head.  Preserve input order through per-scale batches.
        for scale in (30, 50):
            indexes = [i for i, graph in enumerate(batch) if int(graph["scale"]) == scale]
            if not indexes:
                continue
            selected_graphs = [batch[i] for i in indexes]
            native_rows = native.temporal_gat_forward_batch_ensemble(
                selected_by_scale[scale], selected_graphs
            )
            for graph, native_row in zip(selected_graphs, native_rows):
                cpp = [tuple(map(float, value)) for value in native_row["outputs"]]
                py = []
                for model in models:
                    value = portable_temporal_forward(
                        model, payload=graph, bundle=bundle, scale=scale
                    )
                    py.append(tuple(value[name] for name in (
                        "p_benefit", "positive_gain", "p_adverse"
                    )))
                maximum_error = max(maximum_error, *(
                    abs(left - right)
                    for left_row, right_row in zip(py, cpp)
                    for left, right in zip(left_row, right_row)
                ))
                python_action = _action(py, bundle, scale)
                cpp_recomputed_action = _action(cpp, bundle, scale)
                native_action = str(native_row.get("action") or "")
                action_mismatch += int(
                    python_action != cpp_recomputed_action
                    or python_action != native_action
                )
                inference_ms.append(float(native_row["inference_ms"]))
    ordered = sorted(inference_ms)
    p99 = ordered[min(len(ordered) - 1, int(0.99 * len(ordered)))]
    issues = []
    if maximum_error > 1.0e-9:
        issues.append("numeric_parity_error")
    if action_mismatch:
        issues.append("action_parity_error")
    if p99 > 10.0:
        issues.append("native_inference_p99_over_10ms")
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_portable_parity.v1",
        "decision": "FAIL" if issues else "PASS", "issues": issues,
        "calibration_graph_count": len(calibration_rows),
        "calibration_selected_context_count": len(calibration_selected_rows),
        "calibration_natural_end_no_model_count": (
            len(calibration_selected_rows) - len(calibration_rows)
        ),
        "synthetic_graph_count": int(args.synthetic_count),
        "maximum_absolute_error": maximum_error,
        "action_mismatch_count": action_mismatch,
        "native_inference_p99_ms": p99,
        "bundle_file_sha256": hashlib.sha256(args.bundle.read_bytes()).hexdigest(),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "native_module_path": str(Path(native.__file__).resolve()),
        "native_binary_sha256": hashlib.sha256(
            Path(native.__file__).read_bytes()
        ).hexdigest(),
        "source_freeze_sha256": hashlib.sha256(
            source_path.read_bytes()
        ).hexdigest(),
        "deployment_authorized": False,
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output.exists() and args.output.read_text(encoding="utf-8") != encoded:
        raise SystemExit("immutable portable parity audit drift")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.output.exists():
        args.output.write_text(encoded, encoding="utf-8")
    if issues:
        mark_terminal_negative(
            args.run_root, stage="PORTABLE_PARITY",
            reason="TEMPORAL_PORTABLE_PARITY_FAILED", detail=payload,
        )
        raise SystemExit("TEMPORAL_PORTABLE_PARITY_FAILED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
