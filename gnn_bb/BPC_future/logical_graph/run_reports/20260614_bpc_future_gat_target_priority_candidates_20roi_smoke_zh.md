# GAT Target-Priority Candidates 报告

日期：2026-06-14

## 目的

从 GAT embedding + kNN/OOD 的 HIGH_PRIORITY 决策中抽取 target-priority worker
候选。该脚本只读离线记录，不运行 BPC / pricing / RMP，不启用 worker，不产生
certificate 或 official lower bound。

## 机器字段

```text
gat_target_priority_candidates = current
status = ready
candidate_count = 1
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## Candidates

```json
[
  {
    "best_true_reduced_cost": -14.8269665,
    "capture_cg_iter": 7,
    "capture_returned_journey_count": 20,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.7530577778816223,
    "decision_reason": "high_priority",
    "expected_context_hash": "c488c428ee5822de",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "manifest_row_index": 0,
    "manifest_sample_index": 0,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_c488c428ee5822de_20_17_16",
    "source_file": "BPC_future/results/gat_embedding_audit_ab_runbook_20roi_smoke_20260614/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->17:low_risk:2",
      "17->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      17,
      16
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  }
]
```

## Skipped Counts

```json
{
  "decision_not_selected": 1
}
```

## 边界

- GAT/kNN/OOD 只决定 target-priority 候选，不是 pricing oracle；
- true-RC negative 不允许永久丢弃；
- 这些候选只能喂给显式 opt-in worker A/B；
- 不能用于 no-negative certificate 或 official lower bound。
