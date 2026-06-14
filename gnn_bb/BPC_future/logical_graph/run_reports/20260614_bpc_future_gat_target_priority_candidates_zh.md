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
candidate_count = 4
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
    "best_true_reduced_cost": -2.550058,
    "capture_cg_iter": 15,
    "capture_returned_journey_count": 13,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8607129454612732,
    "decision_reason": "high_priority",
    "expected_context_hash": "7e0afd09753effed",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "manifest_row_index": 0,
    "manifest_sample_index": 0,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19",
    "source_file": "BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_sequence": [
      19
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "best_true_reduced_cost": -9.747246,
    "capture_cg_iter": 18,
    "capture_returned_journey_count": 19,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8709929585456848,
    "decision_reason": "high_priority",
    "expected_context_hash": "a3b5b5263e1cfe17",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "manifest_row_index": 1,
    "manifest_sample_index": 1,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12",
    "source_file": "BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->14:low_time:0",
      "14->5:low_risk:2",
      "5->8:low_time:0",
      "8->18:low_risk:2",
      "18->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      14,
      5,
      8,
      18,
      12
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "best_true_reduced_cost": -6.935715,
    "capture_cg_iter": 11,
    "capture_returned_journey_count": 48,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9100852012634277,
    "decision_reason": "high_priority",
    "expected_context_hash": "de2c1d84615d5c71",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "manifest_row_index": 2,
    "manifest_sample_index": 2,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9",
    "source_file": "BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->6:low_risk:2",
      "6->1:low_risk:2",
      "1->20:low_time:0",
      "20->9:low_risk:2",
      "9->0:low_risk:2"
    ],
    "target_sequence": [
      14,
      6,
      1,
      20,
      9
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "best_true_reduced_cost": -3.463997,
    "capture_cg_iter": 12,
    "capture_returned_journey_count": 5,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8218390345573425,
    "decision_reason": "high_priority",
    "expected_context_hash": "157f03afc868de3b",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "manifest_row_index": 3,
    "manifest_sample_index": 3,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13",
    "source_file": "BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_sequence": [
      13
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  }
]
```

## Skipped Counts

```json
{}
```

## 边界

- GAT/kNN/OOD 只决定 target-priority 候选，不是 pricing oracle；
- true-RC negative 不允许永久丢弃；
- 这些候选只能喂给显式 opt-in worker A/B；
- 不能用于 no-negative certificate 或 official lower bound。
