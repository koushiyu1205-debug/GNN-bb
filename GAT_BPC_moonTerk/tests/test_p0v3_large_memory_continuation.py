from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_p0v3_large_memory_continuation.py"
SPEC = importlib.util.spec_from_file_location(
    "prepare_p0v3_large_memory_continuation", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

MONITOR_SCRIPT = ROOT / "scripts" / "run_live_sri_paired_promotion.py"
MONITOR_SPEC = importlib.util.spec_from_file_location(
    "run_live_sri_paired_promotion_for_cleanup_test", MONITOR_SCRIPT
)
assert MONITOR_SPEC is not None and MONITOR_SPEC.loader is not None
MONITOR_MODULE = importlib.util.module_from_spec(MONITOR_SPEC)
MONITOR_SPEC.loader.exec_module(MONITOR_MODULE)

for import_path in (
    ROOT / "scripts",
    ROOT / "src",
    ROOT
    / "runs"
    / "frozen_native_live_sri_p0_no_task_wait_baseline_v3_20260725"
    / "native",
):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))
RUNNER_SCRIPT = ROOT / "scripts" / "run_p0v3_six_scale_full120_baseline.py"
RUNNER_SPEC = importlib.util.spec_from_file_location(
    "run_p0v3_six_scale_full120_for_retry_test", RUNNER_SCRIPT
)
assert RUNNER_SPEC is not None and RUNNER_SPEC.loader is not None
RUNNER_MODULE = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(RUNNER_MODULE)


def test_large_memory_resource_plan_rejects_local_sized_host() -> None:
    plan = MODULE.derive_resource_plan(
        total_memory_gb=31.82,
        minimum_total_memory_gb=360.0,
        recommended_total_memory_gb=380.0,
        system_reserve_gb=48.0,
        native_cap_fraction=0.875,
    )

    assert plan["host_qualified"] is False
    assert plan["native_cooperative_memory_limit_gb"] == 0.0


def test_large_memory_resource_plan_for_384_gib_host() -> None:
    plan = MODULE.derive_resource_plan(
        total_memory_gb=384.0,
        minimum_total_memory_gb=360.0,
        recommended_total_memory_gb=380.0,
        system_reserve_gb=48.0,
        native_cap_fraction=0.875,
    )

    assert plan["host_qualified"] is True
    assert plan["recommendation_met"] is True
    assert plan["native_cooperative_memory_limit_gb"] == 332.0
    assert plan["host_emergency_watchdog_limit_gb"] == 334.0
    assert plan["outer_process_tree_emergency_cap_gb"] == 336.0
    assert plan["minimum_start_available_memory_gb"] == 344.0


def test_runtime_config_changes_only_large_resource_envelope() -> None:
    source = yaml.safe_load(
        (
            ROOT / "configs" / "native_live_sri_p0_full120_v1.yaml"
        ).read_text(encoding="utf-8")
    )
    plan = MODULE.derive_resource_plan(
        total_memory_gb=384.0,
        minimum_total_memory_gb=360.0,
        recommended_total_memory_gb=380.0,
        system_reserve_gb=48.0,
        native_cap_fraction=0.875,
    )
    runtime = MODULE.build_runtime_config(
        source,
        native_memory_limit_gb=332.0,
        resource_plan=plan,
    )

    for scale in (5, 10, 20, 30):
        assert runtime["profiles"][str(scale)] == source["profiles"][str(scale)]
    for scale in (50, 100):
        assert runtime["profiles"][str(scale)]["memory_limit_gb"] == 332.0
        assert runtime["profiles"][str(scale)]["row_time_limit_sec"] == 3600
    assert runtime["live_sri_policy"] == "P0"
    assert runtime["large_scale_execution_class"] == (
        "qualified_time_limit_benchmark_v1"
    )


def test_run_monitor_interrupt_cleans_process_group(tmp_path: Path) -> None:
    class InterruptedProcess:
        pid = 987654

        @staticmethod
        def poll():
            return None

        @staticmethod
        def wait(*, timeout=None):
            raise KeyboardInterrupt

    sample = {
        "process_count": 2,
        "tree_rss_gb": 1.0,
        "tree_swap_gb": 0.0,
        "available_memory_gb": 100.0,
        "system_swap_used_gb": 0.0,
        "disk_free_gb": 100.0,
    }
    with (
        patch.object(
            MONITOR_MODULE.subprocess,
            "Popen",
            return_value=InterruptedProcess(),
        ),
        patch.object(
            MONITOR_MODULE,
            "resource_sample",
            return_value=sample,
        ),
        patch.object(MONITOR_MODULE, "append_heartbeat"),
        patch.object(
            MONITOR_MODULE, "terminate_process_group"
        ) as terminate,
        pytest.raises(KeyboardInterrupt),
    ):
        MONITOR_MODULE.run_monitored(
            ["placeholder"],
            cwd=tmp_path,
            run_dir=tmp_path,
            slot_id="interrupt-cleanup",
            heartbeat_csv=tmp_path / "heartbeat.csv",
            heartbeat_interval_sec=30.0,
            timeout_sec=3600.0,
            effective_memory_limit_gb=300.0,
            min_available_memory_gb=16.0,
            low_memory_consecutive_samples=2,
        )

    terminate.assert_called_once()


def test_large_memory_continuation_retries_only_censored_rows() -> None:
    rows = [
        {"slot_id": "exact", "terminal_class": "EXACT"},
        {"slot_id": "timeout", "terminal_class": "LEGAL_INCOMPLETE"},
        {
            "slot_id": "memory",
            "terminal_class": "MEMORY_CENSORED_INCOMPLETE",
        },
        {
            "slot_id": "resource",
            "terminal_class": "RESOURCE_CENSORED_INCOMPLETE",
        },
        {"slot_id": "unsafe", "terminal_class": "UNSAFE_FAILURE"},
    ]

    retained = RUNNER_MODULE.filter_recovered_rows_for_retry(
        rows,
        retry_unsafe=True,
        retry_resource_censored=True,
        retry_legal_incomplete=False,
        retry_memory_censored=True,
    )

    assert [row["slot_id"] for row in retained] == ["exact", "timeout"]
    assert RUNNER_MODULE.terminal_class(
        {
            "safety_issues": [],
            "exact": False,
            "launcher_termination_reason": "",
            "incomplete_native_engine_status": "MEMORY_LIMIT",
        }
    ) == "MEMORY_CENSORED_INCOMPLETE"


def test_memory_censored_row_cannot_complete_time_limit_benchmark() -> None:
    schedule = [{"slot_id": "s050_instance_001", "scale": 50}]
    common = {
        "schedule": schedule,
        "formal_full120": False,
        "dry_run": False,
        "stopped_reason": "",
        "execution_bundle_hash": "same",
        "execution_bundle_hash_at_end": "same",
        "wall_time_sec": 1.0,
        "preflight": {},
    }
    memory_summary = RUNNER_MODULE.summarize(
        [
            {
                "slot_id": "s050_instance_001",
                "scale": 50,
                "terminal_class": "MEMORY_CENSORED_INCOMPLETE",
                "execution_bundle_hash": "same",
            }
        ],
        **common,
    )
    timeout_summary = RUNNER_MODULE.summarize(
        [
            {
                "slot_id": "s050_instance_001",
                "scale": 50,
                "terminal_class": "LEGAL_INCOMPLETE",
                "execution_bundle_hash": "same",
            }
        ],
        **common,
    )

    assert memory_summary["status"] == "INCOMPLETE"
    assert memory_summary["memory_censored_incomplete_count"] == 1
    assert timeout_summary["status"] == "COMPLETE"
    assert timeout_summary["legal_incomplete_count"] == 1
