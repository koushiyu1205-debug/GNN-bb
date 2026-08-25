from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

import scripts.collect_p0v5_temporal_gat_root_contexts_v1 as context_collection
import scripts.generate_p0v5_temporal_gat_production_corpus_v1 as corpus_generator
import scripts.initialize_p0v5_temporal_gat_production_v1 as initializer
from scripts.generate_p0v5_temporal_gat_production_corpus_v1 import (
    _assign_splits,
    _canonical_payload_sha256,
)
from scripts.select_p0v5_temporal_gat_trial_k_v1 import _metrics
from scripts.freeze_p0v5_temporal_gat_trial_schedule_v1 import (
    build_schedule, determined_instance_capacity,
)
from scripts.audit_p0v5_temporal_gat_e2e_v1 import audit as audit_e2e
from scripts.finalize_p0v5_temporal_gat_production_v1 import (
    _fixed_canary_instances,
)
from scripts.run_p0v5_temporal_gat_canary_v1 import _audit as audit_canary
from scripts.run_p0v5_temporal_gat_trial_schedule_v1 import (
    _deterministic_probe_hash, _redlines, _run as run_temporal_trial,
)
from scripts.run_p0v5_temporal_gat_full_bpc_v1 import (
    _run_process_with_rss,
    _temporal_telemetry,
)
from lunar_ice_bpc.guidance.temporal_frontier_gat_v1 import (
    SEEDS,
    build_temporal_gat_model,
    export_temporal_bundle,
    portable_temporal_forward,
)
from lunar_ice_bpc.guidance.temporal_frontier_gat_runtime_v1 import (
    _validate_temporal_bundle,
    _temporal_context_features,
    temporal_frontier_runtime_requested,
)


def test_fresh_corpus_split_is_exact_and_order_independent() -> None:
    config = {
        "scales": [30, 50],
        "split_counts_by_scale": {
            "train": 40, "calibration": 12,
            "development_e2e": 12, "sealed_final": 16,
        },
    }
    rows = [
        {"scale": scale, "index": index,
         "instance_content_hash": f"scale{scale}-hash-{index:03d}"}
        for scale in (30, 50) for index in range(80)
    ]
    left = copy.deepcopy(rows)
    right = list(reversed(copy.deepcopy(rows)))
    _assign_splits(left, config)
    _assign_splits(right, config)
    assignment_left = {
        row["instance_content_hash"]: row["partition"] for row in left
    }
    assignment_right = {
        row["instance_content_hash"]: row["partition"] for row in right
    }
    assert assignment_left == assignment_right
    for scale in (30, 50):
        counts = {
            partition: sum(
                row["scale"] == scale and row["partition"] == partition
                for row in left
            )
            for partition in config["split_counts_by_scale"]
        }
        assert counts == config["split_counts_by_scale"]


def test_corpus_round_trip_accepts_stable_raster_nan_metadata() -> None:
    payload = {
        "resource_map": {
            "native_layer_status": {"lola_dem": {"nodata": float("nan")}},
        },
        "validation": {"accepted": True},
    }
    restored = json.loads(json.dumps(payload, sort_keys=True, allow_nan=True))
    assert payload != restored
    assert _canonical_payload_sha256(payload) == (
        _canonical_payload_sha256(restored)
    )


def test_initializer_zero_overlap_binding_does_not_use_falsey_fallback() -> None:
    source = Path(initializer.__file__).read_text(encoding="utf-8")
    assert (
        'corpus_payload.get("official_or_historical_overlap_count") or -1'
        not in source
    )
    assert (
        'corpus_payload.get(\n'
        '            "official_or_historical_overlap_count", -1\n'
        '        )'
        in source
    )


def test_python_contract_count_parser_binds_exact_collected_count() -> None:
    assert initializer._pytest_collected_count(
        "17 tests collected in 0.08s\n"
    ) == 17
    assert initializer._pytest_collected_count(
        "1 test collected in 0.01s\n"
    ) == 1
    assert initializer._pytest_collected_count("collection failed\n") == 0


def test_protected_history_reuses_only_frozen_inventory_bound_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(corpus_generator, "ROOT", tmp_path)
    historical = tmp_path / "data/history/instance_001_logical_graph.json"
    historical.parent.mkdir(parents=True)
    historical.write_text('{"stable":true}\n', encoding="utf-8")
    relative = str(historical.relative_to(tmp_path))
    inventory = [{
        "path": relative, "size": historical.stat().st_size,
        "mtime_ns": historical.stat().st_mtime_ns,
    }]
    inventory_sha256 = hashlib.sha256(json.dumps(
        inventory, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    round1 = tmp_path / "data/round1"
    round1.mkdir()
    cache = round1 / "protected_history_hashes.cache.json"
    cache.write_text(json.dumps({
        "schema_version": (
            "lunar_ice_bpc.temporal_gat_protected_history_cache.v1"
        ),
        "inventory_sha256": inventory_sha256,
        "file_count": 1,
        "rows": [{"path": relative, "instance_content_hash": "bound-hash"}],
    }), encoding="utf-8")
    manifest = round1 / "corpus.freeze.json"
    manifest.write_text(json.dumps({
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_corpus.v1",
        "status": "FROZEN_BEFORE_QUEUE_OUTCOMES",
        "protected_history_audit": {
            "cache_path": str(cache.relative_to(tmp_path)),
            "cache_sha256": hashlib.sha256(cache.read_bytes()).hexdigest(),
            "inventory_sha256": inventory_sha256,
        },
    }), encoding="utf-8")
    reused, source_sha256 = corpus_generator._best_reusable_protected_rows(
        tmp_path / "data/round2", [historical]
    )
    assert reused == {relative: "bound-hash"}
    assert source_sha256 == hashlib.sha256(cache.read_bytes()).hexdigest()

    historical.write_text('{"drift":true}\n', encoding="utf-8")
    reused, source_sha256 = corpus_generator._best_reusable_protected_rows(
        tmp_path / "data/round2", [historical]
    )
    assert reused == {}
    assert source_sha256 is None


def test_generation_retry_seed_subranges_are_frozen_and_disjoint() -> None:
    config = {
        "instances_per_scale": 80,
        "seed_base_by_scale": {"30": 9490000, "50": 9690000},
        "generation_retry": {
            "maximum_attempts": 16,
            "seed_stride": 10000000,
            "retry_only_on_instance_validation_or_protected_hash_rejection": (
                True
            ),
        },
    }
    seeds = {
        corpus_generator._generation_seed(config, scale, index, attempt)
        for scale in (30, 50)
        for index in range(1, 81)
        for attempt in range(16)
    }
    assert len(seeds) == 2 * 80 * 16
    for scale in (30, 50):
        for index in (1, 25, 80):
            for attempt in (0, 1, 15):
                seed = corpus_generator._generation_seed(
                    config, scale, index, attempt
                )
                assert corpus_generator._generation_seed_attempt(
                    config, scale, index, seed
                ) == attempt


def test_k_metrics_do_not_hide_resource_censor_in_incomplete_context() -> None:
    rows = []
    for repeat in range(3):
        for arm in ("Q0", "CONTINUE_QD1", "MIGRATE_BACK_TO_Q0"):
            rows.append({
                "context_id": "ctx", "instance_hash": "instance",
                "scale": 30, "k": 128, "arm": arm,
                "status": "TIMEOUT" if arm == "CONTINUE_QD1" else "COMPLETE",
                "wall_seconds": 1.0, "resource_censor": arm == "CONTINUE_QD1",
                "correctness_redlines": [], "repeat": repeat,
                "trial_completed_for_action": arm != "CONTINUE_QD1",
            })
    metric = _metrics(rows, 30, 128)
    assert metric["determined_instances"] == 0
    assert metric["resource_censor_count"] == 1


def test_k_metrics_exclude_trial_that_ended_before_action() -> None:
    rows = []
    for repeat in range(3):
        for arm in ("Q0", "CONTINUE_QD1", "MIGRATE_BACK_TO_Q0"):
            rows.append({
                "context_id": "ctx", "instance_hash": "instance",
                "scale": 50, "k": 512, "arm": arm,
                "status": "COMPLETE", "wall_seconds": 1.0,
                "resource_censor": False, "correctness_redlines": [],
                "repeat": repeat,
                "trial_completed_for_action": arm == "Q0",
            })
    metric = _metrics(rows, 50, 512)
    assert metric["determined_instances"] == 0
    for row in rows:
        row["trial_completed_for_action"] = True
        row["wall_seconds"] = (
            0.99 if row["arm"] == "CONTINUE_QD1" else 1.0
        )
    metric = _metrics(rows, 50, 512)
    assert metric["continue_instances"] == 1
    assert metric["revert_instances"] == 0


def test_frontier_telemetry_hash_excludes_deadline_counters_only_when_censored(
) -> None:
    left = {
        "action": "CONTINUE_QD1", "trial_wall_seconds": 1.0,
        "qd1_post_probe_pops": 100,
        "nested": {"graph_hash": "abc", "inference_wall_seconds": .1},
    }
    right = {
        "action": "CONTINUE_QD1", "trial_wall_seconds": 9.0,
        "qd1_post_probe_pops": 200,
        "nested": {"graph_hash": "abc", "inference_wall_seconds": .7},
    }
    assert _deterministic_probe_hash(left) != _deterministic_probe_hash(right)
    assert _deterministic_probe_hash(
        left, resource_censor=True
    ) == _deterministic_probe_hash(right, resource_censor=True)
    right["qd1_post_probe_pops"] = 100
    assert _deterministic_probe_hash(left) == _deterministic_probe_hash(right)
    right["nested"]["graph_hash"] = "def"
    assert _deterministic_probe_hash(left) != _deterministic_probe_hash(right)
    scope_redlines = _redlines(
        {"arm": "CONTINUE_QD1", "scale": 30, "k": 128},
        {"engine_status": "COMPLETE", "labels_dropped": False},
        {
            "trial_started": True, "trial_completed": False,
            "problem_scale": 30, "pricing_lifecycle": "tree_node",
            "require_root_cg": True,
        },
    )
    assert "temporal_trial_authorization_scope_mismatch" in scope_redlines


def test_train_schedule_is_blocked_three_arm_full_k_grid() -> None:
    config = {
        "maximum_contexts_per_instance": 3,
        "blocked_fresh_process_repeats": 3,
        "trial_k_candidates": [128, 512, 2048],
        "boundary_by_scale": {"30": 4096, "50": 16384},
        "execution": {
            "scale30_task_cap_sec": 300,
            "scale50_task_cap_sec": 600,
            "effective_native_memory_limit_gb": 10.867,
            "memavailable_reserve_gb": 2.0,
        },
    }
    contexts = {"rows": [{
        "context_id": "ctx", "scale": 50, "partition": "train",
        "instance_hash": "instance", "pricing_lifecycle_scope": "root_cg",
        "selection_policy": (
            "earliest_boundary_reaching_p0v4_fallback_request_v1"
        ),
        "selection_rank_within_instance": 0,
    }]}
    schedule = build_schedule(config, contexts, partition="train")
    assert schedule["task_count"] == 27
    assert schedule["single_host_instance"] is True
    assert schedule["memavailable_reserve_gb"] == 2.0
    grouped = {}
    for row in schedule["tasks"]:
        grouped.setdefault(row["block_id"], set()).add(row["arm"])
    assert len(grouped) == 9
    assert all(actions == {
        "Q0", "CONTINUE_QD1", "MIGRATE_BACK_TO_Q0"
    } for actions in grouped.values())


def test_train_schedule_capacity_counts_distinct_instances_not_contexts() -> None:
    contexts = {"rows": [
        {
            "partition": "train", "scale": 30,
            "instance_hash": "scale30-a", "context_id": "30-a-0",
        },
        {
            "partition": "train", "scale": 30,
            "instance_hash": "scale30-a", "context_id": "30-a-1",
        },
        {
            "partition": "train", "scale": 30,
            "instance_hash": "scale30-b", "context_id": "30-b-0",
        },
        {
            "partition": "train", "scale": 50,
            "instance_hash": "scale50-a", "context_id": "50-a-0",
        },
        {
            "partition": "calibration", "scale": 50,
            "instance_hash": "scale50-heldout", "context_id": "50-h-0",
        },
    ]}
    assert determined_instance_capacity(
        contexts, partition="train"
    ) == {"30": 2, "50": 1}


def test_scale50_literal_q0_uses_legacy_probe_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands = []

    def fake_run(command, **kwargs):
        commands.append(list(command))
        Path(command[command.index("--output") + 1]).write_text(
            "{}\n", encoding="utf-8"
        )
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(
        "scripts.run_p0v5_temporal_gat_trial_schedule_v1.subprocess.run",
        fake_run,
    )
    task = {
        "arm": "Q0", "replay_policy": "Q0", "repeat": 0,
        "cap_seconds": 60.0, "memory_limit_gb": 10.867,
        "boundary": 16384, "k": 128, "task_id": "q0",
    }
    context = {"instance_path": "/tmp/i", "snapshot_path": "/tmp/s"}
    run_temporal_trial(task, context, tmp_path / "q0.json", {})
    task.update({
        "arm": "CONTINUE_QD1", "replay_policy": "QT_CONTINUE",
        "task_id": "continue",
    })
    run_temporal_trial(task, context, tmp_path / "continue.json", {})
    boundaries = [
        command[command.index("--frontier-probe-boundary") + 1]
        for command in commands
    ]
    assert boundaries == ["4096", "16384"]


def test_scale50_boundary_eligibility_is_literal_q0_with_canonical_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = list(command)
        output = Path(command[command.index("--output") + 1])
        output.write_text("{}\n", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(context_collection.subprocess, "run", fake_run)
    context_collection._eligibility(
        {
            "boundary_by_scale": {"50": 16384},
            "native_build_dir": "build/native-spprc-temporal-frontier-v10",
            "execution": {
                "scale50_task_cap_sec": 600,
                "effective_native_memory_limit_gb": 10.867,
            },
        },
        {
            "scale": 50, "instance_path": "/tmp/instance.json",
            "snapshot_path": "/tmp/snapshot.json", "state_hash": "state",
        },
        tmp_path / "eligibility.json",
    )
    command = observed["command"]
    assert command[command.index("--policy") + 1] == "QPF0"
    prefix = command.index("--frontier-observation-boundaries")
    assert command[prefix + 1:prefix + 4] == ["4096", "8192", "16384"]


def test_temporal_runtime_discovers_active_production_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "runtime_manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    registry = tmp_path / "production_registry.json"
    registry.write_text(json.dumps({
        "schema_version": "lunar_ice_bpc.production_policy_registry.v2",
        "active_policy": "P0V4+V5_TEMPORAL_GAT_V1",
        "active_runtime_manifest": str(manifest),
        "active_runtime_manifest_sha256": hashlib.sha256(
            manifest.read_bytes()
        ).hexdigest(),
    }), encoding="utf-8")
    monkeypatch.delenv(
        "LUNAR_ICE_P0V5_TEMPORAL_GAT_V1_MANIFEST", raising=False
    )
    monkeypatch.setenv("LUNAR_ICE_PRODUCTION_POLICY_REGISTRY", str(registry))
    assert temporal_frontier_runtime_requested() is True

    registry.write_text(json.dumps({
        "schema_version": "lunar_ice_bpc.production_policy_registry.v2",
        "active_policy": "no_cut",
    }), encoding="utf-8")
    assert temporal_frontier_runtime_requested() is False


def test_temporal_context_carries_dual_branch_cut_and_v5_state() -> None:
    request = SimpleNamespace(
        true_duals=SimpleNamespace(
            cover={"a": 2.0, "b": -1.0}, fleet_limit=3.0,
            cuts={"cut": -4.0},
        ),
        cut_context=SimpleNamespace(cuts=(object(),), empty=False),
        branch_context=SimpleNamespace(pair_decisions=(object(),), empty=False),
        cut_state_enabled=True, cut_dual_projection_enabled=True,
        harvest_target=64, exact_admission_batch_size=16,
        exact_raw_negative_pool_size=64,
        proof_tail_active_column_count=10, proof_tail_round_index=2,
        proof_tail_dual_delta_l1=.25, memory_limit_gb=10.867,
        wall_time_limit_sec=300.0, exact_negative_escape_enabled=True,
        proof_tail_v5_midpoint_wall_sec=.5,
    )
    values = _temporal_context_features(request)
    assert len(values) == 28
    assert values[5] == 3.0 and values[7] == 4.0
    assert values[26:] == (1.0, 1.0)


def _graph(
    torch, generator, nodes: int, width: int, edge_width: int,
    *, label_nodes: int | None = None,
):
    node_features = torch.randn(
            nodes, width, generator=generator, dtype=torch.float64
        ).tolist()
    if label_nodes is not None:
        assert 0 < label_nodes < nodes and width > 25
        for index, row in enumerate(node_features):
            row[24] = 1.0 if index < label_nodes else 0.0
            row[25] = 0.0 if index < label_nodes else 1.0
    return {
        "node_features": node_features,
        "edges": [{
            "source": index, "target": index,
            "features": torch.randn(
                edge_width, generator=generator, dtype=torch.float64
            ).tolist(),
        } for index in range(nodes)],
    }


def test_temporal_v2_python_cpp_portable_parity(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")
    native = pytest.importorskip("lunar_spprc_native")
    models = []
    for seed in SEEDS:
        torch.manual_seed(seed)
        models.append((seed, build_temporal_gat_model().double().eval()))
    controls = {"linear": [], "mlp": [], "no_message": []}
    for seed in SEEDS:
        torch.manual_seed(seed + 1)
        controls["linear"].append((
            seed, torch.nn.Linear(54, 3).double().eval()
        ))
        controls["mlp"].append((seed, torch.nn.Sequential(
            torch.nn.Linear(54, 64), torch.nn.ReLU(),
            torch.nn.Linear(64, 3),
        ).double().eval()))
        controls["no_message"].append((
            seed, build_temporal_gat_model(no_message=True).double().eval()
        ))
    widths = {
        "cell_node": 16, "cell_edge": 10, "node": 40,
        "edge": 11, "counter": 24, "context": 28,
    }
    normalization = {
        name: {
            "mean": [0.0] * width, "scale": [1.0] * width,
            "minimum": [-100.0] * width, "maximum": [100.0] * width,
        }
        for name, width in widths.items()
    }
    calibration = {
        str(scale): {
            "benefit": {"kind": "platt", "a": 1.0, "b": 0.0},
            "adverse": {"kind": "platt", "a": 1.0, "b": 0.0},
            "gain_scale": 1.0,
        }
        for scale in (30, 50)
    }
    thresholds = {
        str(scale): {
            "minimum_benefit_probability": 0.5,
            "maximum_adverse_probability": 0.5,
            "minimum_expected_gain": 0.0,
            "adverse_penalty": 1.0,
            "maximum_disagreement": 1.0,
        }
        for scale in (30, 50)
    }
    bundle = export_temporal_bundle(
        models=models, normalization=normalization,
        calibration_by_scale=calibration,
        thresholds_by_scale=thresholds,
        trial_pop_budget_by_scale={"30": 128, "50": 512},
        boundary_by_scale={"30": 4096, "50": 16384},
        bindings={
            "engine_hashes": ["test-engine"],
            "source_request_config_hashes_observed_diagnostic_only": [
                "training-rmp-round-config"
            ],
            "selected_exact_config_sha256": "0" * 64,
            "native_binary_sha256": "1" * 64,
            "source_freeze_sha256": "2" * 64,
            "experiment_config_sha256": "3" * 64,
        },
        evaluation_controls=controls,
        output_path=tmp_path / "temporal_bundle.v2.json",
    )
    bundle_path = tmp_path / "temporal_bundle.v2.json"
    assert bundle["ood_policy"]["standard_deviation_radius"] == 8.0
    # Live request hashes include RMP/request state and are deliberately not an
    # allowlist.  Static exact-config and engine bindings remain mandatory.
    _validate_temporal_bundle(
        SimpleNamespace(
            engine_hash="test-engine",
            config_hash="previously-unseen-live-rmp-config",
        ),
        bundle,
        hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
        expected_selected_config_sha256="0" * 64,
        expected_native_binary_sha256="1" * 64,
        expected_source_freeze_sha256="2" * 64,
        expected_experiment_config_sha256="3" * 64,
    )
    generator = torch.Generator().manual_seed(260819)
    cell_t0 = _graph(torch, generator, 64, 16, 10)
    cell_tk = _graph(torch, generator, 64, 16, 10)
    cell_t0["context_features"] = [0.0] * 28
    cell_tk["context_features"] = [0.0] * 28
    payload = {
        "cell_t0": cell_t0, "cell_tk": cell_tk,
        "graph_t0": _graph(
            torch, generator, 17, 40, 11, label_nodes=7
        ),
        "graph_tk": _graph(
            torch, generator, 19, 40, 11, label_nodes=9
        ),
        "counter_features": torch.randn(
            24, generator=generator, dtype=torch.float64
        ).tolist(),
        "context_features": torch.randn(
            28, generator=generator, dtype=torch.float64
        ).tolist(),
        "scale": 50,
    }
    selected = dict(bundle)
    selected["selected_scale"] = 50
    selected["calibration"] = calibration["50"]
    selected["thresholds"] = thresholds["50"]
    maximum = 0.0
    for index, (_, model) in enumerate(models):
        expected = portable_temporal_forward(
            model, payload=payload, bundle=bundle, scale=50
        )
        actual = native.temporal_gat_forward(selected, payload, index)
        maximum = max(maximum, *(
            abs(expected[name] - actual[offset])
            for offset, name in enumerate(
                ("p_benefit", "positive_gain", "p_adverse")
            )
        ))
    assert maximum <= 1.0e-9
    batch_row = native.temporal_gat_forward_batch_ensemble(
        selected, [payload]
    )[0]
    batch_outputs = [tuple(map(float, row)) for row in batch_row["outputs"]]
    expected_action = (
        "CONTINUE_QD1"
        if (
            sum(row[0] for row in batch_outputs) / len(batch_outputs) >= 0.5
            and max(row[2] for row in batch_outputs) <= 0.5
            and min(row[1] for row in batch_outputs) > 0.0
            and (
                sum(row[0] for row in batch_outputs) / len(batch_outputs)
                * min(row[1] for row in batch_outputs)
                - max(row[2] for row in batch_outputs)
            ) > 0.0
        ) else "MIGRATE_BACK_TO_Q0"
    )
    assert batch_row["action"] == expected_action

    simple_features = torch.tensor(
        payload["counter_features"] + payload["context_features"] + [0.0, 1.0],
        dtype=torch.float64,
    )
    for kind in ("linear", "mlp", "no_message"):
        control_bundle = dict(selected)
        control_bundle["controller_kind"] = kind
        control_bundle["models"] = bundle["evaluation_controls"][kind]["models"]
        for index, (_, model) in enumerate(controls[kind]):
            if kind == "no_message":
                value = portable_temporal_forward(
                    model, payload=payload, bundle=bundle, scale=50
                )
                expected = tuple(value[name] for name in (
                    "p_benefit", "positive_gain", "p_adverse"
                ))
            else:
                with torch.inference_mode():
                    expected = tuple(map(float, torch.sigmoid(model(simple_features))))
            actual = native.temporal_gat_forward(control_bundle, payload, index)
            assert max(abs(left - right) for left, right in zip(
                expected, actual
            )) <= 1.0e-9


def test_full_bpc_e2e_audit_enforces_complete_four_arm_matrix() -> None:
    rows = []
    wall_by_arm = {
        "Q0": 100.0, "MODEL": 90.0,
        "ALWAYS_CONTINUE": 90.0, "BEST_CONTROL": 100.0,
    }
    for scale in (30, 50):
        for index in range(12):
            instance = f"s{scale}-{index:02d}"
            for arm, wall in wall_by_arm.items():
                for repeat in range(3):
                    rows.append({
                        "scale": scale, "instance_hash": instance,
                        "arm": arm, "repeat": repeat, "status": "COMPLETE",
                        "wall_seconds": wall, "resource_censor": False,
                        "correctness_redlines": [],
                        "exact_semantics_signature": f"exact-s{scale}-{instance}",
                        "objective": float(scale), "peak_rss_gb": 1.0,
                        "inference_ms_values": [1.0] if arm == "MODEL" else [],
                        "probe_overhead_ratio": 1.001,
                        "graph_wall_seconds": 0.1 if arm == "MODEL" else 0.0,
                    })
    gates = {
        "harm_ratio": 1.05, "per_scale_gm_at_most": .95,
        "peak_rss_ratio_at_most": 1.05,
        "scale30_always_continue_regression_at_most": 1.01,
        "scale50_best_control_ratio_at_most": .98,
        "inference_p99_ms_at_most": 10.0,
        "probe_overhead_gm_at_most": 1.01,
        "probe_overhead_worst_at_most": 1.05,
    }
    result = audit_e2e(
        rows, gates, "development_e2e", expected_instances_per_scale=12,
        effective_native_memory_limit_gb=10.867,
    )
    assert result["decision"] == "PASS"
    incomplete = [row for row in rows if row["instance_hash"] != "s50-11"]
    assert audit_e2e(
        incomplete, gates, "development_e2e",
        expected_instances_per_scale=12,
        effective_native_memory_limit_gb=10.867,
    )["decision"] == "FAIL"
    escaped = _temporal_telemetry({
        "proof_queue_frontier_probe": {
            "enabled": True, "model_called": True,
            "problem_scale": 30, "pricing_lifecycle": "tree_node",
            "require_root_cg": True, "mode": "learned_after_trial",
            "action": "CONTINUE_QD1", "boundary": 4096,
            "trial_pops": 128, "seed_outputs": [[0.9, 0.1, 0.01]],
        }
    })
    assert escaped["tree_model_calls"] == 1


def test_process_tree_rss_sampler_covers_inprocess_backend_path(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "process_resource_telemetry.json"
    returncode = _run_process_with_rss(
        [sys.executable, "-c", (
            "import time; value=bytearray(4*1024*1024); "
            "time.sleep(0.15); assert len(value)==4*1024*1024"
        )],
        environment=dict(os.environ),
        telemetry_path=telemetry,
    )
    payload = json.loads(telemetry.read_text(encoding="utf-8"))
    assert returncode == 0
    assert payload["measurement"] == "sampled_sum_vmrss_process_tree_v1"
    assert int(payload["sample_count"]) >= 2
    assert int(payload["process_tree_peak_rss_bytes"]) > 4 * 1024 * 1024


def test_candidate_freezes_boundary_reaching_development_canaries(
    tmp_path: Path,
) -> None:
    corpus_rows = []
    outcomes = []
    for scale in (30, 50):
        path = tmp_path / f"s{scale}.json"
        path.write_text("{}\n", encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        instance_hash = f"hash-{scale}"
        corpus_rows.append({
            "scale": scale, "partition": "development_e2e",
            "instance_content_hash": instance_hash,
            "path": str(path), "file_sha256": digest,
        })
        outcomes.append({
            "scale": scale, "instance_hash": instance_hash, "arm": "MODEL",
            "inference_ms_values": [1.0],
            "selected_action_counts": {"MIGRATE_BACK_TO_Q0": 1},
        })
    selected = _fixed_canary_instances(
        {"rows": corpus_rows}, {"rows": outcomes}
    )
    assert set(selected) == {"30", "50"}
    assert all(row["instance_file_sha256"] for row in selected.values())


def test_canary_audit_requires_normal_force_and_fail_closed_paths(
    tmp_path: Path,
) -> None:
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text("{}\n", encoding="utf-8")
    freeze = {
        "_path": freeze_path,
        "fixed_instances_by_scale": {"30": {}, "50": {}},
    }
    definitions = (
        ("q0_30", 30), ("q0_50", 50),
        ("model_30", 30), ("model_50", 50),
        ("force_continue_30", 30), ("force_revert_50", 50),
        ("bundle_hash_mismatch_30", 30), ("ood_fail_closed_50", 50),
    )
    rows = []
    for task_id, scale in definitions:
        row = {
            "task_id": task_id, "scale": scale, "status": "COMPLETE",
            "resource_censor": False, "correctness_redlines": [],
            "exact_semantics_signature": f"exact-{scale}",
            "objective": float(scale), "runtime_reasons": [],
            "inference_ms_values": [], "selected_action_counts": {},
            "fail_closed_reasons": [],
        }
        if task_id.startswith("model_"):
            row["runtime_reasons"] = ["temporal_bundle_attached"]
            row["inference_ms_values"] = [1.0]
            row.update({
                "runtime_calls": 1, "graph_wall_seconds": 0.01,
                "trial_wall_seconds": 0.1, "peak_rss_gb": 1.0,
            })
        elif task_id == "force_continue_30":
            row["selected_action_counts"] = {"CONTINUE_QD1": 1}
        elif task_id == "force_revert_50":
            row["selected_action_counts"] = {"MIGRATE_BACK_TO_Q0": 1}
        elif task_id == "bundle_hash_mismatch_30":
            row["runtime_reasons"] = ["temporal_fail_closed:ValueError"]
        elif task_id == "ood_fail_closed_50":
            row["fail_closed_reasons"] = ["temporal_frontier_ood"]
            row["selected_action_counts"] = {"MIGRATE_BACK_TO_Q0": 1}
        rows.append(row)
    candidate = {
        "candidate_id": "P0V4+V5_TEMPORAL_GAT_V1",
        "runtime_manifest_sha256": "a" * 64,
    }
    assert audit_canary(candidate, freeze, rows)["decision"] == "PASS"
    rows[-1]["fail_closed_reasons"] = []
    assert audit_canary(candidate, freeze, rows)["decision"] == "FAIL"
