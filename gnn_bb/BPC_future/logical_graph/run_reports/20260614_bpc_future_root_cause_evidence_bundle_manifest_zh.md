# Root Cause Evidence Bundle Manifest 报告

日期：2026-06-14

## 目的

本报告是当前根因证据包索引。它只读 evidence ledger，不运行 solver，
不改变 pricing / worker / certificate。

## 机器字段

```text
root_cause_evidence_bundle_manifest = current
goal_complete = false
completion_decision = keep_goal_active
evidence_bundle_entry_count = 6
evidence_bundle_primary_artifact_count = 175
missing_artifact_count = 0
conclusion_ids = small_scale_fixed_overhead_sensitivity,twenty_negative_columns_not_sufficient,true_rc_negative_can_be_high_impact_or_noop,selector_not_production_validated,exact_context_capture_ready_but_calibration_only,objective_completion_blocked
all_checks_pass = true
```

## 复核命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/verify_root_cause_evidence.py --output-dir BPC_future/results/root_cause_evidence_ledger_20260613
```

## 重建命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/rebuild_root_cause_evidence_bundle.py
```

## 结论索引

### small_scale_fixed_overhead_sensitivity

```text
status = supported
primary_artifact_count = 1
```

5/10 scale regression is explained by fixed overhead from triggered worker/audit/probe mechanisms.

### twenty_negative_columns_not_sufficient

```text
status = supported
primary_artifact_count = 3
```

20-task runs can safely add true-RC negative journeys, but that has not produced stable wall-time/status improvement.

### true_rc_negative_can_be_high_impact_or_noop

```text
status = supported
primary_artifact_count = 3
```

Exact-context replay contains both high-impact returned batches and no-op/replacement negative candidates.

### selector_not_production_validated

```text
status = blocking
primary_artifact_count = 134
```

A replay-calibrated selector candidate exists, but it has not passed the required context/instance/dataset holdout and no production BPC A/B has validated it.

### exact_context_capture_ready_but_calibration_only

```text
status = supported_not_production
primary_artifact_count = 6
```

Capture/replay data are ready for selector calibration, not for production selector or certificate effect.

### objective_completion_blocked

```text
status = blocking
primary_artifact_count = 63
```

The user objective remains active because production selector validation and 20-task speedup evidence are missing.

## 总结

这是当前根因证据包的索引。它证明证据链可复查，但不改变完成结论：目标仍未完成，production selector 和 20-task speedup 仍是阻塞项。
