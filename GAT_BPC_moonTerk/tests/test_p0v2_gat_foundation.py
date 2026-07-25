from __future__ import annotations

from dataclasses import replace
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import pickle
import random
import subprocess
import sys

import pytest

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    CanonicalSolveBindingV2,
    PricingOrderingHintsV2,
    canonical_arc_candidate_id,
    canonical_universe_hash,
    reorder_preserving_universe,
)
from lunar_ice_bpc.exact.bpc.guidance.replay import (
    build_pricing_snapshot,
    load_pricing_snapshot,
    replay_pricing_ordering,
    save_pricing_snapshot,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    BACKEND_MODE_NEGATIVE_HARVEST,
    BackendPricingRequest,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    PROOF_QUEUE_EXPERIMENT_ENV,
    resolve_experimental_proof_queue_policy,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
    _attach_development_oracle_task_priorities,
)
from lunar_ice_bpc.exact.core.cuts import (
    raw_ieee_dual_hash,
    true_dual_binding_hash,
)
from lunar_ice_bpc.exact.core.data import FrozenMap, load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.branch_shadow import (
    BranchPairCandidate,
    offline_all_pairs_control,
    rank_p0_shortlist,
)
from lunar_ice_bpc.guidance.deployment import (
    DeploymentEligibilityManifest,
    decide_guidance_entry,
)
from lunar_ice_bpc.guidance.evaluation import (
    SafetyAudit,
    holm_rejections,
    paired_runtime_summary,
    stage_b_gate,
)
from lunar_ice_bpc.guidance.queue_shadow import (
    QueueShadowState,
    cross_policy_alignment_key,
    exhaustive_queue_policy_differential,
    queue_shadow_key,
)
from lunar_ice_bpc.guidance.splits import (
    InstanceSplitRecord,
    build_split_manifest,
    extend_split_manifest,
)
from lunar_ice_bpc.guidance.tensorization import (
    build_static_graph_features,
    encode_queue_policy_id,
)
from lunar_ice_bpc.guidance.training import (
    CensoredBranchObservation,
    branch_cost,
    should_enable_pcgrad,
    strong_pairwise_branch_label,
)


def _data(seed: int = 629001, *, scale: int = 5):
    return load_lunar_ice_data(
        generate_instance(scale, seed=seed, index=1)
    )


def _request(*, negative_harvest: bool = False, scale: int = 5):
    data = _data(scale=scale)
    duals = JourneyDuals(
        cover={task_id: 10.0 for task_id in data.task_ids},
        fleet_limit=0.0,
        cuts={},
    )
    return BackendPricingRequest(
        data=data,
        true_duals=duals,
        mode=(
            BACKEND_MODE_NEGATIVE_HARVEST
            if negative_harvest
            else "exact_proof"
        ),
        instance_hash=data.instance_content_hash,
        config_hash="p0v2-gat-test",
        engine_hash="engine-v2",
        dual_binding_hash=true_dual_binding_hash(
            duals.cover,
            fleet_limit=duals.fleet_limit,
            cuts=duals.cuts,
        ),
        rmp_iteration_id="root-1",
    )


def test_proof_queue_policy_contract_is_exact_only() -> None:
    control = _request()
    assert control.proof_queue_policy_id == "Q0"
    assert (
        replace(control, proof_queue_policy_id="QC0").proof_queue_policy_id
        == "QC0"
    )
    assert replace(control, proof_queue_policy_id="QD1").proof_queue_policy_id == "QD1"
    assert replace(control, proof_queue_policy_id="QB1").proof_queue_policy_id == "QB1"
    with pytest.raises(ValueError, match="unsupported proof_queue_policy_id"):
        replace(control, proof_queue_policy_id="unknown")
    with pytest.raises(ValueError, match="exact-proof diagnostics only"):
        replace(
            _request(negative_harvest=True),
            proof_queue_policy_id="QD1",
        )


def test_development_task_priority_oracle_reuses_canonical_binding(
    tmp_path: Path,
) -> None:
    request = _request(negative_harvest=True)
    artifact = {
        "schema_version": (
            "lunar_ice_bpc.development_trajectory_task_priority_oracle.v1"
        ),
        "source_partition": "development",
        "instance_content_hash": request.data.instance_content_hash,
        "source_artifact_sha256": "a" * 64,
        "task_priorities": {
            task_id: float(index)
            for index, task_id in enumerate(request.data.task_ids)
        },
        "arc_priorities": {},
        "development_only": True,
        "deployable": False,
    }
    path = tmp_path / "oracle.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    guided = _attach_development_oracle_task_priorities(
        request, str(path)
    )
    expected = CanonicalSolveBindingV2.from_backend_request(guided)

    assert guided.guidance_mode == "task_arc"
    assert guided.guidance_hints is not None
    assert guided.guidance_hints.binding_hash == expected.binding_hash
    assert guided.guidance_hints.diagnostic_only is True
    assert set(
        guided.guidance_hints.priorities_for("task")
    ) == set(request.data.task_ids)


def test_proof_queue_scale30_experiment_is_exact_official_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        PROOF_QUEUE_EXPERIMENT_ENV,
        "scale30_qd1_else_q0",
    )
    scale30 = _request(scale=30)
    assert scale30.proof_queue_policy_id == "QD1"
    assert scale30.config_hash != "p0v2-gat-test"

    scale20 = _request(scale=20)
    assert scale20.proof_queue_policy_id == "Q0"
    assert scale20.config_hash != "p0v2-gat-test"

    harvest = _request(negative_harvest=True)
    assert harvest.proof_queue_policy_id == "Q0"
    assert harvest.config_hash == "p0v2-gat-test"

    phase_one = replace(
        _request(),
        objective_mode="phase_one",
        config_hash="phase-one",
        proof_queue_policy_id="Q0",
    )
    assert phase_one.proof_queue_policy_id == "Q0"
    assert phase_one.config_hash == "phase-one"


def test_proof_queue_scale30_branch_or_cut_experiment_is_request_dynamic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mode = "scale30_branch_or_cut_qd1_else_q0"
    monkeypatch.setenv(PROOF_QUEUE_EXPERIMENT_ENV, mode)

    root = _request(scale=30)
    assert root.proof_queue_policy_id == "Q0"
    assert root.config_hash != "p0v2-gat-test"

    branch_policy, branch_selector = (
        resolve_experimental_proof_queue_policy(
            requested_policy_id="Q0",
            mode="exact_proof",
            objective_mode="official",
            scale=30,
            branch_context_active=True,
            cut_context_active=False,
        )
    )
    assert (branch_policy, branch_selector) == ("QD1", mode)

    cut_policy, cut_selector = resolve_experimental_proof_queue_policy(
        requested_policy_id="Q0",
        mode="exact_proof",
        objective_mode="official",
        scale=30,
        branch_context_active=False,
        cut_context_active=True,
    )
    assert (cut_policy, cut_selector) == ("QD1", mode)

    small_policy, small_selector = resolve_experimental_proof_queue_policy(
        requested_policy_id="Q0",
        mode="exact_proof",
        objective_mode="official",
        scale=20,
        branch_context_active=True,
        cut_context_active=True,
    )
    assert (small_policy, small_selector) == ("Q0", mode)

    harvest_policy, harvest_selector = (
        resolve_experimental_proof_queue_policy(
            requested_policy_id="Q0",
            mode=BACKEND_MODE_NEGATIVE_HARVEST,
            objective_mode="official",
            scale=30,
            branch_context_active=True,
            cut_context_active=True,
        )
    )
    assert (harvest_policy, harvest_selector) == ("Q0", "off")


def test_invalid_proof_queue_experiment_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PROOF_QUEUE_EXPERIMENT_ENV, "unknown")
    with pytest.raises(ValueError, match="unsupported proof queue experiment"):
        _request()


def test_lunar_data_is_deeply_immutable_and_pickle_stable() -> None:
    raw = generate_instance(5, seed=629001, index=1)
    raw["reference_solution"] = {
        "routes": [{"tasks": ["ice_site_001", "ice_site_002"]}]
    }
    data = load_lunar_ice_data(raw)
    assert isinstance(data.tasks, FrozenMap)
    assert isinstance(data.arcs, FrozenMap)
    assert isinstance(data.reference_solution, FrozenMap)
    with pytest.raises(TypeError):
        data.tasks["new"] = data.tasks[data.task_ids[0]]  # type: ignore[index]
    with pytest.raises(TypeError):
        data.arcs[next(iter(data.arcs))]["low_time"] = next(  # type: ignore[index]
            iter(data.arcs[next(iter(data.arcs))].values())
        )
    with pytest.raises(AttributeError):
        data.reference_solution["routes"].append({})  # type: ignore[union-attr]
    restored = pickle.loads(pickle.dumps(data))
    assert restored.instance_content_hash == data.instance_content_hash
    assert isinstance(restored.tasks, FrozenMap)
    assert isinstance(restored.reference_solution, FrozenMap)


def test_content_hash_drives_static_cache_and_rejects_same_id_stale_data() -> None:
    first_raw = generate_instance(5, seed=629001, index=1)
    first = load_lunar_ice_data(first_raw)
    same = load_lunar_ice_data(first_raw)
    second_raw = generate_instance(5, seed=629777, index=1)
    second_raw["instance_id"] = first_raw["instance_id"]
    second = load_lunar_ice_data(second_raw)
    assert same.instance_content_hash == first.instance_content_hash
    assert second.instance_id == first.instance_id
    assert second.instance_content_hash != first.instance_content_hash
    assert build_static_graph_features(first) is build_static_graph_features(same)
    assert build_static_graph_features(second) is not build_static_graph_features(first)


def test_signed_zero_math_hash_is_canonical_but_raw_hash_is_diagnostic() -> None:
    positive = {"a": 0.0, "b": 1.0}
    negative = {"b": 1.0, "a": -0.0}
    assert true_dual_binding_hash(positive) == true_dual_binding_hash(negative)
    assert raw_ieee_dual_hash(positive) != raw_ieee_dual_hash(negative)


def test_canonical_binding_uses_exact_objects_not_redundant_wrong_hashes() -> None:
    request = _request()
    binding = CanonicalSolveBindingV2.from_backend_request(request)
    wrong = replace(
        request,
        branch_context_hash="wrong",
        cut_context_hash="wrong",
    )
    wrong_binding = CanonicalSolveBindingV2.from_backend_request(wrong)
    assert wrong_binding.branch_context_hash == binding.branch_context_hash
    assert wrong_binding.full_cut_context_hash == binding.full_cut_context_hash
    assert set(CanonicalSolveBindingV2.request_consistency_issues(wrong)) == {
        "request_branch_context_hash_mismatch",
        "request_cut_context_hash_mismatch",
    }
    assert binding.phase == "phase_two"


def test_reorder_and_snapshot_replay_preserve_the_legal_universe(
    tmp_path,
) -> None:
    rows = (
        {"candidate_id": "a", "value": 1},
        {"candidate_id": "b", "value": 2},
        {"candidate_id": "c", "value": 3},
    )
    ordered, audit = reorder_preserving_universe(
        rows,
        priorities={"c": 9.0, "a": 1.0},
        enabled=True,
        universe_kind="test",
    )
    assert [row["candidate_id"] for row in ordered] == ["c", "a", "b"]
    assert audit["guidance_filter_count"] == 0
    assert (
        audit["legal_action_universe_hash_before_sort"]
        == audit["legal_action_universe_hash_after_sort"]
    )
    snapshot = build_pricing_snapshot(_request(), candidates=rows)
    snapshot_path = tmp_path / "snapshot.json"
    save_pricing_snapshot(snapshot, snapshot_path)
    restored = load_pricing_snapshot(snapshot_path)
    assert restored.snapshot_hash == snapshot.snapshot_hash
    replay = replay_pricing_ordering(snapshot, priorities={"c": 2.0})
    assert replay["ordering_changed"] is True
    assert replay["result_semantics_changed"] is False
    assert replay["can_certify"] is False
    assert replay_pricing_ordering(
        snapshot,
        priorities={},
        expected_binding_hash="wrong",
    )["status"] == "BINDING_MISMATCH"


def test_zero_filter_universe_property_over_random_priorities() -> None:
    rows = tuple(
        {"candidate_id": f"candidate-{index}"}
        for index in range(40)
    )
    expected = canonical_universe_hash(
        (row["candidate_id"] for row in rows),
        universe_kind="property",
    )
    for seed in range(32):
        rng = random.Random(seed)
        priorities = {
            row["candidate_id"]: rng.uniform(-100.0, 100.0)
            for row in rows
            if rng.random() > 0.2
        }
        ordered, audit = reorder_preserving_universe(
            rows,
            priorities=priorities,
            enabled=True,
            universe_kind="property",
        )
        assert len(ordered) == len(rows)
        assert {
            row["candidate_id"] for row in ordered
        } == {row["candidate_id"] for row in rows}
        assert audit["legal_action_universe_hash_before_sort"] == expected
        assert audit["legal_action_universe_hash_after_sort"] == expected
        assert audit["guidance_filter_count"] == 0


def test_deployment_gate_can_bypass_before_torch_import() -> None:
    code = """
import sys
from lunar_ice_bpc.guidance.deployment import DeploymentEligibilityManifest, decide_guidance_entry
m = DeploymentEligibilityManifest(
 checkpoint_id='c', checkpoint_path='/does/not/matter',
 source_baseline_id='p0v2', engine_hash='engine-v2', model_kind='linear',
 feature_schema_version='f', normalization_version='n',
 ood_policy_version='o', eligible_online_scales=(20, 30),
 preimport_bypass_scales=(5, 10))
d = decide_guidance_entry(m, scale=5, requested_mode='task_arc')
assert d.bypassed_before_import
assert 'torch' not in sys.modules
print(d.status)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED" in result.stdout


def test_environment_gate_rejects_stale_engine_before_torch_import(
    tmp_path,
) -> None:
    manifest = DeploymentEligibilityManifest(
        checkpoint_id="stale",
        checkpoint_path=str(tmp_path / "must-not-be-read.pt"),
        source_baseline_id="p0v2",
        engine_hash="different-engine",
        model_kind="linear",
        feature_schema_version="f",
        normalization_version="n",
        ood_policy_version="o",
        eligible_online_scales=(5,),
    )
    manifest_path = tmp_path / "deployment.json"
    manifest_path.write_text(
        __import__("json").dumps(manifest.to_payload()),
        encoding="utf-8",
    )
    code = f"""
import os, sys
os.environ['LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST'] = {str(manifest_path)!r}
os.environ['LUNAR_ICE_GAT_GUIDANCE_MODE'] = 'harvest'
from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.bpc.pricing.backends import BackendPricingRequest
from lunar_ice_bpc.guidance.runtime import prepare_guidance_request_from_environment
data = load_lunar_ice_data(generate_instance(5, seed=629001, index=1))
request = BackendPricingRequest(
    data=data,
    true_duals=JourneyDuals(
        cover={{task_id: 10.0 for task_id in data.task_ids}},
        fleet_limit=0.0,
        cuts={{}},
    ),
    mode='negative_harvest',
    instance_hash=data.instance_content_hash,
    config_hash='p0v2-gat-test',
    engine_hash='engine-v2',
    rmp_iteration_id='root-1',
)
p = prepare_guidance_request_from_environment(request, stage='harvest')
assert p is not None
assert p.request.guidance_mode == 'off'
assert p.telemetry['bypassed_before_import']
assert p.telemetry['bypass_reason'] == 'exact_engine_hash_mismatch'
assert 'torch' not in sys.modules
print(p.decision.status)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        text=True,
        capture_output=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert "CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED" in result.stdout


def test_harvest_cheap_gate_bypasses_before_torch_import(tmp_path) -> None:
    manifest = DeploymentEligibilityManifest(
        checkpoint_id="cheap-gate",
        checkpoint_path=str(tmp_path / "must-not-be-read.pt"),
        source_baseline_id="p0v2",
        engine_hash="engine-v2",
        model_kind="linear",
        feature_schema_version="f",
        normalization_version="n",
        ood_policy_version="o",
        eligible_online_scales=(5,),
        minimum_harvest_candidates_by_scale=((5, 3),),
        minimum_harvest_negative_mass_by_scale=((5, 0.1),),
    )
    manifest_path = tmp_path / "deployment-cheap-gate.json"
    manifest_path.write_text(
        __import__("json").dumps(manifest.to_payload()),
        encoding="utf-8",
    )
    code = f"""
import os, sys
os.environ['LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST'] = {str(manifest_path)!r}
os.environ['LUNAR_ICE_GAT_GUIDANCE_MODE'] = 'harvest'
from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.bpc.pricing.backends import BackendPricingRequest
from lunar_ice_bpc.guidance.runtime import prepare_guidance_request_from_environment
data = load_lunar_ice_data(generate_instance(5, seed=629001, index=1))
request = BackendPricingRequest(
    data=data,
    true_duals=JourneyDuals(
        cover={{task_id: 10.0 for task_id in data.task_ids}},
        fleet_limit=0.0,
        cuts={{}},
    ),
    mode='negative_harvest',
    instance_hash=data.instance_content_hash,
    config_hash='p0v2-gat-test',
    engine_hash='engine-v2',
    rmp_iteration_id='root-1',
)
p = prepare_guidance_request_from_environment(
    request,
    stage='harvest',
    harvest_candidates=(
        {{'candidate_id':'a','task_ids':[],'context':[-0.2,1,1,0]}},
        {{'candidate_id':'b','task_ids':[],'context':[-0.1,1,1,0]}},
    ),
)
assert p is not None
assert p.request.guidance_mode == 'off'
assert p.telemetry['bypassed_before_import']
assert p.telemetry['bypass_reason'] == 'cheap_gate_too_few_legal_harvest_candidates'
assert p.telemetry['cheap_gate_candidate_count'] == 2
assert 'torch' not in sys.modules
print(p.decision.status)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        text=True,
        capture_output=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert "CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED" in result.stdout


def test_split_manifest_keeps_protected_full120_out() -> None:
    records = []
    for scale in (5, 10, 20, 30, 50, 100):
        for index in range(8):
            records.append(
                InstanceSplitRecord(
                    instance_content_hash=f"new-{scale}-{index}",
                    instance_id=f"new-{scale}-{index}",
                    scale=scale,
                    source_role="new_development",
                    time_window_mode=f"tw{index % 2}",
                    task_mode=f"mode{index % 3}",
                    hotspot_structure=f"hot{index % 2}",
                    fleet_ratio_bin=f"fleet{index % 2}",
                    p0_difficulty_bin=f"difficulty{index % 3}",
                )
            )
        records.append(
            InstanceSplitRecord(
                instance_content_hash=f"protected-{scale}",
                instance_id=f"protected-{scale}",
                scale=scale,
                source_role=(
                    "full80_exact_test"
                    if scale <= 30
                    else "existing_large_shadow_test"
                ),
                time_window_mode="holdout",
                task_mode="holdout",
                hotspot_structure="holdout",
                fleet_ratio_bin="holdout",
                p0_difficulty_bin="holdout",
            )
        )
    manifest = build_split_manifest(
        records,
        calibration_per_scale={scale: 2 for scale in (5, 10, 20, 30, 50, 100)},
    )
    assert manifest["audit"]["passed"]
    assert manifest["audit"]["protected_full120_not_used"]
    protected = {
        row["instance_content_hash"]
        for row in manifest["protected_final_test"]
    }
    used = {
        row["instance_content_hash"]
        for key in ("development", "calibration")
        for row in manifest[key]
    }
    assert protected.isdisjoint(used)
    fold_counts = Counter(row["fold"] for row in manifest["development"])
    assert max(fold_counts.values()) - min(fold_counts.values()) <= 1
    by_stratum = defaultdict(Counter)
    for row in manifest["development"]:
        stratum = tuple(
            row[field]
            for field in (
                "scale",
                "time_window_mode",
                "task_mode",
                "hotspot_structure",
                "fleet_ratio_bin",
                "p0_difficulty_bin",
            )
        )
        by_stratum[stratum][row["fold"]] += 1
    for counts in by_stratum.values():
        all_fold_counts = [counts.get(fold, 0) for fold in range(5)]
        assert max(all_fold_counts) - min(all_fold_counts) <= 1


def test_large_scale_split_extension_preserves_every_base_assignment() -> None:
    base_records = [
        InstanceSplitRecord(
            instance_content_hash=f"small-{scale}-{index}",
            instance_id=f"small-{scale}-{index}",
            scale=scale,
            source_role="new_development",
            time_window_mode="mixed",
            task_mode="mixed",
            hotspot_structure="mixed",
            fleet_ratio_bin="medium",
            p0_difficulty_bin="medium",
        )
        for scale in (5, 10, 20, 30)
        for index in range(8)
    ]
    base = build_split_manifest(
        base_records,
        calibration_per_scale={scale: 2 for scale in (5, 10, 20, 30)},
    )
    frozen = {
        row["instance_content_hash"]: (
            row["partition"],
            row["fold"],
        )
        for partition in ("development", "calibration")
        for row in base[partition]
    }
    large_records = [
        InstanceSplitRecord(
            instance_content_hash=f"large-{scale}-{index}",
            instance_id=f"large-{scale}-{index}",
            scale=scale,
            source_role="new_development",
            time_window_mode="mixed",
            task_mode="mixed",
            hotspot_structure="mixed",
            fleet_ratio_bin="medium",
            p0_difficulty_bin="tail_censored",
        )
        for scale in (50, 100)
        for index in range(20)
    ]
    extended = extend_split_manifest(
        base,
        large_records,
        calibration_per_scale={50: 8, 100: 8},
    )
    after = {
        row["instance_content_hash"]: (
            row["partition"],
            row["fold"],
        )
        for partition in ("development", "calibration")
        for row in extended[partition]
        if row["instance_content_hash"] in frozen
    }
    assert after == frozen
    assert extended["base_manifest_hash"] == base["manifest_hash"]
    assert extended["audit"]["counts"]["development:scale50"] == 12
    assert extended["audit"]["counts"]["calibration:scale50"] == 8
    assert extended["audit"]["counts"]["development:scale100"] == 12
    assert extended["audit"]["counts"]["calibration:scale100"] == 8


def test_branch_shortlist_is_symmetric_and_never_drops_pairs() -> None:
    rows = (
        BranchPairCandidate("b", "a", 0),
        BranchPairCandidate("c", "a", 1),
        BranchPairCandidate("d", "a", 2),
    )
    scores = {"branch_pair:a|d": 10.0}
    ordered, audit = rank_p0_shortlist(rows, scores=scores, enabled=True)
    assert ordered[0].candidate_id == "branch_pair:a|d"
    assert audit["guidance_branch_pair_drop_count"] == 0
    assert (
        audit["legal_branch_shortlist_hash_before_sort"]
        == audit["legal_branch_shortlist_hash_after_sort"]
    )
    all_pairs = offline_all_pairs_control(rows, scores=scores)
    assert set(all_pairs["U0_deterministic"]) == set(
        all_pairs["U1_learned"]
    )


def test_branch_target_and_censoring_do_not_fabricate_penalties() -> None:
    assert branch_cost(10, 10, 0.0) < branch_cost(10, 100, 0.8)
    exact = CensoredBranchObservation(
        observed_work_lower_bound=5.0,
        censoring_time_sec=1.0,
        censoring_memory_bytes=100,
        left_status="closed",
        right_status="closed",
        exact=True,
        exact_branch_cost=5.0,
    )
    censored = CensoredBranchObservation(
        observed_work_lower_bound=8.0,
        censoring_time_sec=2.0,
        censoring_memory_bytes=200,
        left_status="timeout",
        right_status="open",
        exact=False,
    )
    assert strong_pairwise_branch_label(exact, censored) == -1
    assert strong_pairwise_branch_label(censored, censored) is None
    assert should_enable_pcgrad([-0.3, -0.25, -0.21])


def test_queue_shadow_keys_are_explicit_and_cross_policy_alignment_is_canonical() -> None:
    state = QueueShadowState(
        partial_rc=-2.0,
        guidance_score=3.0,
        creation_sequence_id=7,
        heuristic_completion_priority=1.0,
        heuristic_proof_risk=0.2,
        canonical_state_signature="state",
        canonical_path_signature="path",
    )
    assert queue_shadow_key("Q1", state) == (-2.0, -3.0, 7)
    assert queue_shadow_key("Q2", state) == (1.0, -2.0, -3.0, 7)
    assert cross_policy_alignment_key(state) == ("state", "path")
    assert [encode_queue_policy_id(f"Q{index}") for index in range(5)] == [
        0.0,
        0.25,
        0.5,
        0.75,
        1.0,
    ]


def test_all_shadow_queue_keys_preserve_exhaustive_global_min_and_threshold() -> None:
    states = tuple(
        QueueShadowState(
            partial_rc=float(index - 3),
            guidance_score=float((index * 7) % 5),
            creation_sequence_id=index,
            heuristic_completion_priority=float(5 - index),
            heuristic_proof_risk=float(index) / 10.0,
            canonical_state_signature=f"state-{index}",
            canonical_path_signature=f"path-{index}",
            terminal_reduced_cost=value,
        )
        for index, value in enumerate(
            (1.0, -0.5, -2.0, 0.25, None, -1.25)
        )
    )
    audit = exhaustive_queue_policy_differential(
        states, threshold=-1.0
    )
    assert audit["all_policies_match"]
    assert audit["expected_global_min_rc"] == -2.0
    assert audit["expected_has_rc_below_threshold"]
    assert set(audit["policies"]) == {"Q0", "Q1", "Q2", "Q3", "Q4"}
    assert not audit["can_certify"]


def test_symmetric_pair_model_features_are_exchange_invariant() -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.models import symmetric_pair_features

    left = torch.randn(3, 8)
    right = torch.randn(3, 8)
    global_embedding = torch.randn(3, 8)
    context = torch.randn(3, 4)
    first = symmetric_pair_features(left, right, global_embedding, context)
    second = symmetric_pair_features(right, left, global_embedding, context)
    assert torch.allclose(first, second)


@pytest.mark.skipif(
    importlib.util.find_spec("lunar_spprc_native") is None,
    reason="native extension is not installed",
)
def test_native_task_arc_guidance_is_bound_order_only_and_zero_filter() -> None:
    from lunar_ice_bpc.exact.bpc.pricing.backends import (
        NativeRcsppInprocessBackend,
    )

    request = _request(negative_harvest=True)
    enriched = replace(
        request,
        guidance_mode="task_arc",
        guidance_feature_schema_version="feature-v2",
        guidance_normalization_version="norm-fold-only-v1",
        guidance_checkpoint_id="test-checkpoint",
        guidance_ood_policy_version="ood-calibration-v1",
    )
    binding = CanonicalSolveBindingV2.from_backend_request(enriched)
    hints = PricingOrderingHintsV2(
        binding_hash=binding.binding_hash,
        task_priorities=tuple(
            (task_id, float(index))
            for index, task_id in enumerate(enriched.data.task_ids)
        ),
        arc_priorities=tuple(
            (
                canonical_arc_candidate_id(source, target, path_type),
                float(index % 7),
            )
            for index, ((source, target), by_type) in enumerate(
                sorted(enriched.data.arcs.items())
            )
            for path_type in sorted(by_type)
        ),
        diagnostic_only=False,
    )
    result = NativeRcsppInprocessBackend().solve(
        replace(enriched, guidance_hints=hints)
    )
    assert result.telemetry["guidance_effective_mode"] == "task_arc"
    assert result.telemetry["guidance_filter_count"] == 0
    assert result.telemetry["guidance_arc_drop_count"] == 0
    assert result.telemetry["guidance_label_drop_count"] == 0
    assert result.telemetry["request_bindings_match"]
    assert not result.labels_dropped
    assert result.telemetry[
        "best_reduced_cost_event_trace_valid"
    ]
    assert result.telemetry[
        "best_reduced_cost_event_trace_usable_for_training"
    ]
    assert result.telemetry["best_reduced_cost_events_audited"]
    assert result.telemetry["legal_action_universe_hash_before_sort"] == (
        canonical_universe_hash(enriched.data.task_ids, universe_kind="task")
    )
    exact_control = replace(request, mode="exact_proof", guidance_mode="off")
    exact_enriched = replace(enriched, mode="exact_proof")
    exact_binding = CanonicalSolveBindingV2.from_backend_request(exact_enriched)
    exact_guided = replace(
        exact_enriched,
        guidance_hints=replace(hints, binding_hash=exact_binding.binding_hash),
    )
    control_result = NativeRcsppInprocessBackend().solve(exact_control)
    guided_result = NativeRcsppInprocessBackend().solve(exact_guided)
    assert guided_result.telemetry["guidance_effective_mode"] == "off"
    assert guided_result.telemetry[
        "best_reduced_cost_event_trace_valid"
    ]
    assert not guided_result.telemetry[
        "best_reduced_cost_event_trace_usable_for_training"
    ]
    assert not guided_result.telemetry[
        "best_reduced_cost_events_audited"
    ]
    assert guided_result.search_exhaustive == control_result.search_exhaustive
    assert guided_result.frontier_empty == control_result.frontier_empty
    assert guided_result.proved_no_rc_below == control_result.proved_no_rc_below
    assert guided_result.global_min_rc == pytest.approx(
        control_result.global_min_rc
    )
    assert sorted(
        round(float(value), 8)
        for value in (
            guided_result.telemetry["reconstruction_audit"][index][
                "python_manual_rc"
            ]
            for index in range(
                len(guided_result.telemetry["reconstruction_audit"])
            )
        )
    ) == sorted(
        round(float(value), 8)
        for value in (
            control_result.telemetry["reconstruction_audit"][index][
                "python_manual_rc"
            ]
            for index in range(
                len(control_result.telemetry["reconstruction_audit"])
            )
        )
    )


@pytest.mark.skipif(
    importlib.util.find_spec("lunar_spprc_native") is None,
    reason="native extension is not installed",
)
def test_native_opt_in_snapshot_is_replayable_without_b_and_b(
    tmp_path, monkeypatch
) -> None:
    from lunar_ice_bpc.exact.bpc.pricing.backends import (
        NativeRcsppInprocessBackend,
    )

    monkeypatch.setenv("LUNAR_ICE_GAT_SNAPSHOT_DIR", str(tmp_path))
    monkeypatch.setenv("LUNAR_ICE_GAT_SNAPSHOT_MAX_PER_PROCESS", "8")
    result = NativeRcsppInprocessBackend().solve(
        _request(negative_harvest=True)
    )
    assert result.telemetry["guidance_snapshot_written"] is True
    snapshot = load_pricing_snapshot(
        result.telemetry["guidance_snapshot_path"]
    )
    assert snapshot.instance_content_hash == _request().data.instance_content_hash
    replay = replay_pricing_ordering(
        snapshot,
        priorities={snapshot.p0_ordering[-1]: 100.0},
    )
    assert replay["status"] == "REPLAY_READY"
    assert replay["ordering_changed"] is True
    assert replay["result_semantics_changed"] is False


@pytest.mark.skipif(
    importlib.util.find_spec("lunar_spprc_native") is None,
    reason="native extension is not installed",
)
def test_host_timeout_is_legal_incomplete_without_certificate_leak() -> None:
    from lunar_ice_bpc.exact.bpc.pricing.backends import (
        NativeRcsppHostBackend,
    )

    data = load_lunar_ice_data(
        generate_instance(10, seed=629991, index=1)
    )
    duals = JourneyDuals(
        cover={task_id: 1.0 for task_id in data.task_ids},
        fleet_limit=0.0,
        cuts={},
    )
    request = BackendPricingRequest(
        data=data,
        true_duals=duals,
        mode="exact_proof",
        instance_hash=data.instance_content_hash,
        config_hash="host-timeout-no-leak",
        engine_hash="engine-v2",
        dual_binding_hash=true_dual_binding_hash(
            duals.cover,
            fleet_limit=duals.fleet_limit,
            cuts=duals.cuts,
        ),
        wall_time_limit_sec=0.0,
        memory_limit_gb=1.0,
    )
    NativeRcsppHostBackend.close()
    try:
        result = NativeRcsppHostBackend().solve(request)
    finally:
        NativeRcsppHostBackend.close()
    assert result.engine_status in {"TIMEOUT", "TIME_LIMIT"}
    assert not result.search_exhaustive
    assert not result.can_enter_certificate_audit
    assert result.global_min_rc is None
    assert result.proved_no_rc_below is None
    assert "native_exact_search_incomplete" in result.certificate_blockers


def test_manifest_online_and_shadow_scales_are_head_specific_not_global_weights() -> None:
    manifest = DeploymentEligibilityManifest(
        checkpoint_id="shared-six-scale",
        checkpoint_path="/tmp/checkpoint.pt",
        source_baseline_id="p0v2",
        engine_hash="engine-v2",
        model_kind="mlp2x32",
        feature_schema_version="f2",
        normalization_version="fold-only",
        ood_policy_version="calibration-only",
        engine_hash_by_scale=((100, "engine-host-v2"),),
        eligible_online_scales=(20, 30),
        shadow_only_scales=(5, 10, 20, 30, 50, 100),
        preimport_bypass_scales=(5, 10),
    )
    assert manifest.expected_engine_hash(20) == "engine-v2"
    assert manifest.expected_engine_hash(100) == "engine-host-v2"
    assert (
        decide_guidance_entry(
            manifest, scale=20, requested_mode="task_arc"
        ).import_learning_runtime
        is False
    )
    assert (
        decide_guidance_entry(
            manifest, scale=20, requested_mode="harvest"
        ).import_learning_runtime
        is True
    )
    assert (
        decide_guidance_entry(
            manifest, scale=100, requested_mode="task_arc"
        ).import_learning_runtime
        is False
    )


def test_lazy_runtime_loads_one_bound_checkpoint_and_reports_full_cost(
    tmp_path,
) -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.models import (
        build_model,
        checkpoint_payload,
    )
    from lunar_ice_bpc.guidance.runtime import (
        expected_model_dimensions,
        prepare_guidance_request,
    )
    from lunar_ice_bpc.guidance.tensorization import (
        COMPOSITE_FEATURE_SCHEMA_V3,
        HARVEST_MODEL_CONTEXT_SCHEMA_V2,
    )

    node_dim, edge_dim = expected_model_dimensions()
    model = build_model(
        "linear", node_input_dim=node_dim, edge_input_dim=edge_dim
    )
    for parameter in model.parameters():
        torch.nn.init.zeros_(parameter)
    checkpoint = tmp_path / "linear.pt"
    metadata = {
        "checkpoint_id": "linear-test",
        "source_baseline_id": "p0v2-b0-control",
        "engine_hash": "engine-v2",
        "compatible_engine_hashes": ["engine-v2"],
        "feature_schema_version": COMPOSITE_FEATURE_SCHEMA_V3,
        "harvest_model_context_schema_version": (
            HARVEST_MODEL_CONTEXT_SCHEMA_V2
        ),
        "normalization_version": "fold-train-only",
        "ood_policy_version": "calibration-only",
        "node_feature_mean": [0.0] * node_dim,
        "node_feature_std": [1000.0] * node_dim,
        "edge_feature_mean": [0.0] * edge_dim,
        "edge_feature_std": [1000.0] * edge_dim,
        "ood_max_abs_z": 1000.0,
        "ood_max_abs_z_by_scale": {"5": 1000.0},
        "ood_calibrated": True,
            "training_objective": "counterfactual_trajectory_v2",
            "trajectory_objective_spec_id": (
                "fixed_pool_pricing_pressure_auc."
                "equal_mass_count.current_state.normalized.v1"
            ),
        "counterfactual_main_scope": "harvest_only",
        "p0_noop_trained": True,
        "trained_main_heads": ["harvest"],
    }
    torch.save(checkpoint_payload(model, metadata=metadata), checkpoint)
    checkpoint_sha256 = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    manifest = DeploymentEligibilityManifest(
        checkpoint_id="linear-test",
        checkpoint_path=str(checkpoint),
        source_baseline_id="p0v2-b0-control",
        engine_hash="engine-v2",
        model_kind="linear",
        feature_schema_version=COMPOSITE_FEATURE_SCHEMA_V3,
        normalization_version="fold-train-only",
        ood_policy_version="calibration-only",
        checkpoint_sha256=checkpoint_sha256,
        eligible_online_scales=(5,),
        shadow_only_scales=(5,),
    )
    prepared = prepare_guidance_request(
        _request(negative_harvest=True),
        manifest=manifest,
        requested_mode="harvest",
        harvest_candidates=(
            {
                "candidate_id": "route-a",
                "task_ids": ["ice_site_001"],
                "context": [-1.0, 1.0, 1.0, 0.2],
            },
            {
                "candidate_id": "route-b",
                "task_ids": ["ice_site_002"],
                "context": [-0.5, 1.0, 1.0, 0.2],
            },
        ),
    )
    assert prepared.request.guidance_hints is not None
    assert prepared.request.guidance_hints.binding_hash
    assert prepared.request.guidance_hints.proof_tail_risk is None
    assert prepared.diagnostics["nonfinite_hint_accepted"] is False
    assert prepared.diagnostics["torch_num_threads"] == 1
    assert prepared.diagnostics["deterministic_inference"] is True
    assert prepared.diagnostics["p0_noop_available"] is True
    assert prepared.diagnostics["abstained_to_p0"] is True
    assert prepared.diagnostics["learned_action_selected"] is None
    assert prepared.request.guidance_hints.task_priorities == tuple()
    assert prepared.request.guidance_hints.arc_priorities == tuple()
    assert prepared.request.guidance_hints.harvest_priorities == tuple()
    lifecycle = dict(prepared.request.guidance_lifecycle_telemetry)
    assert lifecycle["guidance_import_sec"] >= 0.0
    assert lifecycle["guidance_checkpoint_load_sec"] >= 0.0
    assert lifecycle["guidance_tensorize_sec"] >= 0.0
    assert lifecycle["guidance_forward_total_sec"] >= 0.0
    assert lifecycle["guidance_call_count"] == 1
    repeated = prepare_guidance_request(
        _request(negative_harvest=True),
        manifest=manifest,
        requested_mode="harvest",
        harvest_candidates=(
            {
                "candidate_id": "route-a",
                "task_ids": ["ice_site_001"],
                "context": [-1.0, 1.0, 1.0, 0.2],
            },
            {
                "candidate_id": "route-b",
                "task_ids": ["ice_site_002"],
                "context": [-0.5, 1.0, 1.0, 0.2],
            },
        ),
    )
    assert repeated.diagnostics["ood_diagnostics"][
        "static_tensor_cache_hit"
    ]


def test_stage_b_statistics_gate_and_holm_are_explicit() -> None:
    medium = paired_runtime_summary([10, 20, 30], [8, 16, 24])
    small = paired_runtime_summary([1, 2, 3], [1.0, 2.0, 3.0])
    gate = stage_b_gate(
        safety=SafetyAudit(),
        first_addable_negative_p50_ratio_20_30=0.8,
        equal_budget_best_rc_improved=True,
        duplicate_negative_rate_delta=0.0,
        rmp_bound_gain_per_pricing_second_improved=True,
        medium_runtime=medium,
        small_runtime=small,
    )
    assert gate["passed"]
    assert holm_rejections({"linear": 0.001, "mlp": 0.02, "gat": 0.2}) == {
        "linear": True,
        "mlp": True,
        "gat": False,
    }


def test_deployment_freezer_requires_bound_calibrated_checkpoint(
    tmp_path,
) -> None:
    torch = pytest.importorskip("torch")
    from lunar_ice_bpc.guidance.models import (
        build_model,
        checkpoint_payload,
    )
    from lunar_ice_bpc.guidance.runtime import expected_model_dimensions
    from lunar_ice_bpc.guidance.tensorization import (
        COMPOSITE_FEATURE_SCHEMA_V3,
        HARVEST_MODEL_CONTEXT_SCHEMA_V2,
    )

    node_dim, edge_dim = expected_model_dimensions()
    model = build_model(
        "linear", node_input_dim=node_dim, edge_input_dim=edge_dim
    )
    checkpoint = tmp_path / "calibrated.pt"
    torch.save(
        checkpoint_payload(
            model,
            metadata={
                "checkpoint_id": "calibrated",
                "source_baseline_id": "p0v2",
                "engine_hash": "engine-v2",
                "compatible_engine_hashes": ["engine-v2"],
                "feature_schema_version": COMPOSITE_FEATURE_SCHEMA_V3,
                "harvest_model_context_schema_version": (
                    HARVEST_MODEL_CONTEXT_SCHEMA_V2
                ),
                "normalization_version": "fold-only",
                "ood_policy_version": "cal-only",
                "node_feature_mean": [0.0] * node_dim,
                "node_feature_std": [1.0] * node_dim,
                "edge_feature_mean": [0.0] * edge_dim,
                "edge_feature_std": [1.0] * edge_dim,
                "ood_max_abs_z": 7.0,
                "ood_calibrated": True,
                "ood_max_abs_z_by_scale": {"5": 7.0},
                "fold": 0,
                "training_objective": "counterfactual_trajectory_v2",
                "trajectory_objective_spec_id": (
                    "fixed_pool_pricing_pressure_auc."
                    "equal_mass_count.current_state.normalized.v1"
                ),
                "counterfactual_main_scope": "harvest_only",
                "p0_noop_trained": True,
                "trained_main_heads": ["harvest"],
            },
        ),
        checkpoint,
    )
    output = tmp_path / "deployment.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/freeze_p0v2_gat_deployment_manifest.py",
            "--checkpoint",
            str(checkpoint),
            "--output",
            str(output),
            "--engine-hash",
            "5=engine-v2",
            "--shadow-scales",
            "5",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    frozen = DeploymentEligibilityManifest.load(output)
    assert frozen.checkpoint_sha256 == hashlib.sha256(
        checkpoint.read_bytes()
    ).hexdigest()
    assert frozen.expected_engine_hash(5) == "engine-v2"
    discovery_output = tmp_path / "discovery-deployment.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/freeze_p0v2_gat_deployment_manifest.py",
            "--checkpoint",
            str(checkpoint),
            "--output",
            str(discovery_output),
            "--engine-hash",
            "5=engine-v2",
            "--online-scales",
            "5",
            "--shadow-scales",
            "5",
            "--experimental-discovery-only",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    discovery = DeploymentEligibilityManifest.load(discovery_output)
    assert discovery.experimental_discovery_only
    assert not discovery.formal_promotion_eligible
    assert not discovery.promotion_gate_report_hash
    assert discovery.discovery_validation_fold == 0


def test_model_rung_selection_keeps_smaller_model_without_significant_gain(
    tmp_path,
) -> None:
    metrics = tmp_path / "metrics.jsonl"
    common = {
        "split_manifest_hash": "split-v1",
        "training_objective": "counterfactual_trajectory_v2",
        "safety_gate_pass": True,
        "scale5_10_non_degradation": True,
        "stage_b_gate_pass": True,
        "inference_overhead_gate_pass": True,
        "counterfactual_context_coverage_gate": True,
        "counterfactual_worst_scale_lcb_gate": True,
        "gold_trajectory_gate": True,
        "p0_noop_calibration_gate": True,
        "route_harvest_first_stage_gate": True,
        "memory_resource_safety_gate": True,
        "net_advantage_after_model_cost_gate": True,
        "instance_snapshot_bootstrap_unit_gate": True,
        "scale50_100_safety_only_gate": True,
        "unbiased_sentinel_opportunity_density_gate": True,
        "perfect_policy_net_benefit_gate": True,
        "cheap_preimport_eligibility_gate": True,
        "opportunity_roi_eligible_scales": [5, 10, 20, 30],
        "worst_scale_bootstrap_lcb": 0.1,
        "scale20_30_end_to_end_gain": 0.2,
        "guidance_total_wall_sec": 0.01,
    }
    rows = [
        {
            **common,
            "model_kind": "linear",
            "parameter_count": 100,
            "p_value_vs_next_smaller": None,
        },
        {
            **common,
            "model_kind": "mlp2x32",
            "parameter_count": 1000,
            "p_value_vs_next_smaller": 0.5,
            "significantly_better_than_next_smaller": False,
        },
    ]
    metrics.write_text(
        "".join(
            __import__("json").dumps(row) + "\n" for row in rows
        ),
        encoding="utf-8",
    )
    output = tmp_path / "selection.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/select_p0v2_gat_model_rung.py",
            "--candidate-metrics-jsonl",
            str(metrics),
            "--output",
            str(output),
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    selected = __import__("json").loads(output.read_text(encoding="utf-8"))
    assert selected["passed"]
    assert selected["selected_model_kind"] == "linear"


def test_candidate_metric_sign_flip_detects_only_paired_improvement() -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_p0v2_gat_candidate_metrics.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_candidate_metrics_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._paired_sign_flip_pvalue(
        [-0.2] * 20, samples=5000, seed=7
    ) < 0.01
    assert module._paired_sign_flip_pvalue(
        [0.2] * 20, samples=5000, seed=7
    ) == 1.0


def test_model_ladder_training_epoch_keeps_scale_aggregation_bounded() -> None:
    torch = pytest.importorskip("torch")
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v2_gat_model_ladder.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_training_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    row = {
        "scale": 5,
        "node_features": [[0.0] * 23, [0.1] * 23, [0.2] * 23],
        "edge_features": [[0.0] * 8, [0.1] * 8, [0.2] * 8],
        "edge_index": [[0, 1, 2], [1, 2, 0]],
        "task_node_indices": [1, 2],
        "task_grades": [4.0, 1.0],
        "arc_grades": [0.0, 3.0, 1.0],
        "resource_context": [1.0, 2.0, 0.0, 1.0],
    }
    normalization = module._fit_normalization([row])
    from lunar_ice_bpc.guidance.models import build_model
    from lunar_ice_bpc.guidance.training import EMALossNormalizer

    model = build_model("mlp2x32", node_input_dim=23, edge_input_dim=8)
    optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3)
    loss, per_scale, cosine, diagnostics = module._run_epoch(
        model,
        [row],
        normalization,
        optimizer=optimizer,
        loss_normalizer=EMALossNormalizer(),
        pcgrad_enabled=False,
    )
    assert loss >= 0.0
    assert set(per_scale) == {"5"}
    assert -1.0 <= cosine <= 1.0
    assert set(diagnostics["per_head_loss"]) == {"exact_pricing"}


def test_b0_result_ledger_merges_scales_atomically(tmp_path) -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v2_gat_b0_development.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_b0_runner", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "ledger.jsonl"
    first = {
        "instance_content_hash": "scale5-a",
        "scale": 5,
        "index": 1,
    }
    second = {
        "instance_content_hash": "scale30-a",
        "scale": 30,
        "index": 1,
    }
    module._write_result_ledger(path, {"scale5-a": first})
    ledger = module._load_result_ledger(path)
    ledger["scale30-a"] = second
    module._write_result_ledger(path, ledger)
    assert [
        row["instance_content_hash"]
        for row in module._load_result_ledger(path).values()
    ] == ["scale5-a", "scale30-a"]


def test_head_specific_training_and_frozen_shadow_heads() -> None:
    torch = pytest.importorskip("torch")
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v2_gat_model_ladder.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_head_training_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    graph = {
        "scale": 20,
        "node_features": [[0.0] * 23, [0.1] * 23, [0.2] * 23],
        "edge_features": [[0.0] * 8, [0.1] * 8, [0.2] * 8],
        "edge_index": [[0, 1, 2], [1, 2, 0]],
        "task_node_indices": [1, 2],
        "resource_context": [1.0, 2.0, 0.0, 0.0],
    }
    exact = {
        **graph,
        "head": "exact_pricing",
        "task_grades": [4.0, 1.0],
        "arc_grades": [0.0, 3.0, 1.0],
    }
    harvest = {
        **graph,
        "head": "harvest",
        "harvest_task_masks": [
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        "harvest_context": [[-2.0, 1.0, 1.0, 0.1]] * 2,
        "harvest_grades": [4.0, 1.0],
    }
    from lunar_ice_bpc.guidance.models import build_model
    from lunar_ice_bpc.guidance.training import EMALossNormalizer

    normalization = module._fit_normalization([exact, harvest])
    model = build_model("mlp2x32", node_input_dim=23, edge_input_dim=8)
    optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3)
    _, _, _, diagnostics = module._run_epoch(
        model,
        [exact, harvest],
        normalization,
        optimizer=optimizer,
        loss_normalizer=EMALossNormalizer(),
        pcgrad_enabled=True,
    )
    assert set(diagnostics["per_head_loss"]) == {
        "exact_pricing",
        "harvest",
    }
    proof = {
        **graph,
        "head": "proof_risk",
        "proof_observed_lower_bound": [2.0],
        "proof_exact_mask": [0.0],
    }
    branch = {
        **graph,
        "head": "branch",
        "branch_pairs": [[1, 2], [2, 1]],
        "branch_context": [[0.2, 1.0, 2.0, 0.0]] * 2,
        "branch_observed_lower_bounds": [2.0, 3.0],
        "branch_exact_mask": [1.0, 0.0],
    }
    module._freeze_for_shadow_heads(model, ["proof_risk", "branch"])
    assert not any(
        parameter.requires_grad
        for parameter in model.node_encoder.parameters()
    )
    shadow_optimizer = torch.optim.Adam(
        [
            parameter
            for parameter in model.parameters()
            if parameter.requires_grad
        ],
        lr=1.0e-3,
    )
    _, _, _, shadow_diagnostics = module._run_epoch(
        model,
        [proof, branch],
        normalization,
        optimizer=shadow_optimizer,
        loss_normalizer=EMALossNormalizer(),
        pcgrad_enabled=False,
    )
    assert set(shadow_diagnostics["per_head_loss"]) == {
        "proof_risk",
        "branch",
    }


def test_materializer_applies_useful_and_hidden_negative_grades() -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "materialize_p0v2_gat_snapshot_rows.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_materializer_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    harvest = module._apply_pricing_grade_contract(
        {
            "head": "harvest",
            "harvest_grades": [3.0, 3.0, 1.0],
            "harvest_context": [
                [-2.0, 1.0, 1.0, 0.2],
                [-1.0, 0.0, 1.0, 0.2],
                [-0.5, 0.0, 0.0, 0.2],
            ],
            "harvest_hidden_negative_mask": [False, True, True],
        }
    )
    assert harvest["harvest_grades"] == [4.0, 4.0, 2.0]
    exact = module._apply_pricing_grade_contract(
        {
            "head": "exact_pricing",
            "task_grades": [3.0, 0.0],
            "task_hidden_negative_mask": [True, False],
            "arc_grades": [1.0, 3.0],
            "arc_hidden_negative_mask": [False, True],
        }
    )
    assert exact["task_grades"] == [4.0, 0.0]
    assert exact["arc_grades"] == [1.0, 4.0]


def test_harvest_large_scale_effective_loss_weight_stays_below_ten_percent() -> None:
    torch = pytest.importorskip("torch")
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v2_gat_model_ladder.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_weighting_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for scale in (5, 20, 50, 100):
        rows.append(
            {
                "scale": scale,
                "head": "harvest",
                "node_features": [
                    [0.0] * 23,
                    [0.1] * 23,
                    [0.2] * 23,
                ],
                "edge_features": [
                    [0.0] * 8,
                    [0.1] * 8,
                    [0.2] * 8,
                ],
                "edge_index": [[0, 1, 2], [1, 2, 0]],
                "task_node_indices": [1, 2],
                "resource_context": [1.0, 2.0, 0.0, 0.0],
                "harvest_task_masks": [
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
                "harvest_context": [[-2.0, 1.0, 1.0, 0.1]] * 2,
                "harvest_grades": [4.0, 1.0],
            }
        )
    normalization = module._fit_normalization(rows)
    from lunar_ice_bpc.guidance.models import build_model

    model = build_model("mlp2x32", node_input_dim=23, edge_input_dim=8)
    _, _, _, diagnostics = module._run_epoch(
        model,
        rows,
        normalization,
        optimizer=None,
        loss_normalizer=None,
        pcgrad_enabled=False,
    )
    weights = diagnostics["effective_head_scale_loss_weight"]
    assert weights["harvest:scale5"] == pytest.approx(
        weights["harvest:scale20"]
    )
    assert (
        weights["harvest:scale50"] + weights["harvest:scale100"]
        < 0.10
    )


def test_training_weights_instances_equally_despite_context_count() -> None:
    torch = pytest.importorskip("torch")
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v2_gat_model_ladder.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_instance_weighting_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = {
        "scale": 30,
        "head": "exact_pricing",
        "node_phase": "phase_two",
        "node_features": [[0.0] * 23, [0.1] * 23, [0.2] * 23],
        "edge_features": [[0.0] * 8, [0.1] * 8, [0.2] * 8],
        "edge_index": [[0, 1, 2], [1, 2, 0]],
        "task_node_indices": [1, 2],
        "resource_context": [1.0, 2.0, 0.0, 0.0],
        "task_grades": [4.0, 1.0],
        "arc_grades": [0.0, 3.0, 1.0],
    }
    rows = [
        {
            **base,
            "instance_content_hash": "many-contexts",
            "rmp_context_hash": f"many-{index}",
        }
        for index in range(3)
    ] + [
        {
            **base,
            "instance_content_hash": "one-context",
            "rmp_context_hash": "one-0",
        }
    ]
    normalization = module._fit_normalization(rows)
    from lunar_ice_bpc.guidance.models import build_model

    model = build_model("mlp2x32", node_input_dim=23, edge_input_dim=8)
    _, _, _, diagnostics = module._run_epoch(
        model,
        rows,
        normalization,
        optimizer=None,
        loss_normalizer=None,
        pcgrad_enabled=False,
    )
    weight_range = diagnostics[
        "effective_instance_loss_weight_range_by_head_scale"
    ]["exact_pricing:scale30"]
    assert weight_range["min"] == pytest.approx(weight_range["max"])


def test_stage_b_discovery_metrics_pair_contexts_before_instances() -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "evaluate_p0v2_gat_stage_b.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_stage_b_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    control = {
        "instance_content_hash": "instance-a",
        "scale": 30,
        "first_addable_negative_by_context": [
            {"context_id": "root", "pricing_sec": 10.0},
            {"context_id": "child", "pricing_sec": 100.0},
        ],
        "equal_budget_best_rc_trajectories": [
            {
                "context_id": "root",
                "points": [
                    {"pricing_budget_sec": 1.0, "best_true_rc": -1.0},
                    {"pricing_budget_sec": 2.0, "best_true_rc": -2.0},
                ],
            }
        ],
    }
    guided = {
        **control,
        "first_addable_negative_by_context": [
            {"context_id": "root", "pricing_sec": 5.0},
            {"context_id": "child", "pricing_sec": 50.0},
        ],
        "equal_budget_best_rc_trajectories": [
            {
                "context_id": "root",
                "points": [
                    {"pricing_budget_sec": 1.0, "best_true_rc": -1.5},
                    {"pricing_budget_sec": 2.0, "best_true_rc": -3.0},
                ],
            }
        ],
    }
    ratio = module._paired_first_addable_ratio(control, guided)
    assert ratio is not None
    assert ratio["paired_context_count"] == 2
    assert ratio["instance_p50_ratio"] == pytest.approx(0.5)
    matched = module._matched_budget_rc(control, guided)
    assert len(matched) == 1
    assert matched[0]["context_id"] == "root"
    assert matched[0]["guided_minus_p0_best_rc"] == pytest.approx(-1.0)


def test_stage_b_guided_ledger_rejects_wrong_fold(tmp_path) -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "evaluate_p0v2_gat_stage_b.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_stage_b_fold_audit_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ledger = tmp_path / "guided.jsonl"
    ledger.write_text(
        __import__("json").dumps(
            {
                "instance_content_hash": "instance-a",
                "experiment_variant": "HA",
                "guidance_mode": "task_arc",
                "split_manifest_hash": "split-v1",
                "partition": "development",
                "fold": 1,
                "guidance_checkpoint_id": "checkpoint-fold1",
                "guidance_model_kind": "linear",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="fold mismatch"):
        module._load(
            str(ledger),
            selected_hashes={"instance-a"},
            expected_variant="HA",
            expected_guidance_mode="task_arc",
            expected_split_manifest_hash="split-v1",
            expected_fold_by_hash={"instance-a": 0},
        )


def test_large_development_generation_is_locked_before_ha_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_p0v2_gat_development_instances.py",
            "--scales",
            "50,100",
            "--per-scale",
            "20",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "locked until --stage-b-report" in (
        result.stdout + result.stderr
    )


def test_semantic_redline_audit_keeps_raw_flags_without_false_certificate_leak(
    tmp_path,
) -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v2_gat_b0_development.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_redline_audit_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    proof_dir = tmp_path / "proof"
    proof_dir.mkdir()
    (proof_dir / "b4_1_summary.json").write_text(
        __import__("json").dumps(
            {
                "redlines": {
                    "certificate_leak_count": 0,
                    "tail_dual_certificate_leak_count": 1,
                }
            }
        ),
        encoding="utf-8",
    )
    (proof_dir / "b4_1_rows.jsonl").write_text(
        __import__("json").dumps(
            {
                "tail_dual_stabilization_enabled": True,
                "worker_pricer_kind": "relaxed_labeling",
                "worker_generated_column_task_set_count": 0,
                "worker_dual_source": "",
                "worker_dual_only": False,
                "true_dual_rc_recomputed": False,
                "tail_dual_no_column_can_certify": False,
                "can_certify_no_negative": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    fields = (
        "certificate_leak",
        "manual_rc_fail",
        "pricing_rc_fail",
        "tail_dual_certificate_leak",
        "true_dual_rc_recompute_missing",
        "worker_certificate_leak",
    )
    diagnostic = {
        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
        "certificate_leak": "1",
        "manual_rc_fail": "1",
        "pricing_rc_fail": "1",
        "tail_dual_certificate_leak": "1",
        "true_dual_rc_recompute_missing": "0",
        "worker_certificate_leak": "0",
        "no_cheat_pass": "True",
    }
    audit = module._semantic_redline_audit(
        tmp_path, diagnostic, raw_fields=fields
    )
    assert audit["passed"]
    assert audit["diagnostic_timeout_rc_flags_ignored"]
    assert audit["configured_but_unobserved_worker_tail_flag_ignored"]
    assert audit["raw_fields"]["certificate_leak"] == 1
    certifying = {
        **diagnostic,
        "certificate_scope": "BPC_TREE_OPTIMAL",
        "certificate_leak": "0",
        "tail_dual_certificate_leak": "0",
    }
    failed = module._semantic_redline_audit(
        tmp_path, certifying, raw_fields=fields
    )
    assert not failed["passed"]
    assert "certifying_manual_rc_audit_failed" in failed["issues"]


def test_compact_static_cache_is_hash_checked_and_epoch_context_rotates(
    tmp_path,
) -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v2_gat_model_ladder.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_compact_cache_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from lunar_ice_bpc.exact.core.cuts import stable_payload_hash

    key = "content-a"
    payload = {
        "schema_version": "lunar_ice_bpc.gat_static_tensor_sidecar.v1",
        "instance_content_hash": key,
        "feature_schema_version": "static-test",
        "node_static_features": [[1.0, 2.0], [3.0, 4.0]],
        "edge_features": [[5.0]],
        "edge_index": [[0], [1]],
        "task_node_indices": [1],
    }
    payload["static_tensor_cache_hash"] = stable_payload_hash(payload)
    (tmp_path / f"{key}.json").write_text(
        __import__("json").dumps(payload), encoding="utf-8"
    )
    base = {
        "head": "exact_pricing",
        "scale": 5,
        "instance_content_hash": key,
        "node_phase": "phase_two",
        "static_tensor_cache_key": key,
        "static_tensor_cache_hash": payload[
            "static_tensor_cache_hash"
        ],
        "dynamic_node_features": [[0.1], [0.2]],
    }
    rows = [
        {**base, "rmp_context_hash": "a"},
        {**base, "rmp_context_hash": "b"},
    ]
    cache = module._load_static_tensor_cache(rows, cache_dir=tmp_path)
    node, edge, edge_index, task_indices = module._resolve_feature_arrays(
        rows[0], static_cache=cache
    )
    assert node == [[1.0, 2.0, 0.1], [3.0, 4.0, 0.2]]
    assert edge == [[5.0]]
    assert edge_index == [[0], [1]]
    assert task_indices == [1]
    assert module._epoch_context_sample(rows, 0)[0][
        "rmp_context_hash"
    ] == "a"
    assert module._epoch_context_sample(rows, 1)[0][
        "rmp_context_hash"
    ] == "b"
    corrupted = [{**rows[0], "static_tensor_cache_hash": "stale"}]
    with pytest.raises(SystemExit, match="payload hash mismatch"):
        module._load_static_tensor_cache(
            corrupted, cache_dir=tmp_path
        )


def test_harvest_model_context_masks_deterministic_selector_facts() -> None:
    from lunar_ice_bpc.guidance.tensorization import (
        HARVEST_MODEL_CONTEXT_SCHEMA_V2,
        learned_harvest_context,
    )

    assert HARVEST_MODEL_CONTEXT_SCHEMA_V2.endswith(
        "v2_without_selector_facts"
    )
    assert learned_harvest_context((-2.0, 1.0, 1.0, 0.4)) == (
        -2.0,
        0.0,
        0.0,
        0.4,
    )
    with pytest.raises(ValueError, match="four values"):
        learned_harvest_context((1.0, 2.0))
    with pytest.raises(ValueError, match="finite"):
        learned_harvest_context((1.0, float("nan"), 0.0, 0.5))


def test_offline_discovery_audit_distinguishes_raw_from_model_leakage(
    tmp_path,
) -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "evaluate_p0v2_gat_offline_discovery.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_offline_discovery_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "rows.jsonl"
    path.write_text(
        __import__("json").dumps(
            {
                "head": "harvest",
                "schema_version": (
                    "lunar_ice_bpc.gat_harvest_training_row.v2"
                ),
                "instance_content_hash": "development-a",
                "harvest_grades": [4.0, 3.0],
                "harvest_context": [
                    [-2.0, 1.0, 1.0, 0.2],
                    [-1.0, 0.0, 0.0, 0.1],
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    audit = module._audit_harvest_target_leakage(
        path,
        development_hashes={"development-a"},
        forbidden_hashes={"protected-a"},
    )
    assert audit["raw_context_direct_target_leakage"]
    assert not audit["learned_input_direct_target_leakage"]
    assert audit["v2_context_count"] == 1


def test_harvest_replay_universe_hash_is_order_invariant() -> None:
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "replay_p0v2_gat_harvest_rows.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v2_harvest_replay_script", script_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    descriptors = [
        {
            "candidate_sequence_id": 0,
            "task_indices": (1, 2),
            "true_reduced_cost": -2.0,
            "would_change_active_support": True,
            "grade": 4.0,
        },
        {
            "candidate_sequence_id": 1,
            "task_indices": (2,),
            "true_reduced_cost": -1.0,
            "would_change_active_support": False,
            "grade": 3.0,
        },
    ]
    assert module._universe_hash(descriptors) == module._universe_hash(
        list(reversed(descriptors))
    )
    metrics = module._ranking_metrics([4.0, 3.0], [1, 0])
    assert metrics["first_useful_candidate_rank"] == 2
