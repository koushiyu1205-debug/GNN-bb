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
required_capture_context_field_count = 8
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
    "active_hash_before": "f5e56fbba74784b5",
    "best_true_reduced_cost": -2.550058,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 15,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 13,
    "certificate_effect": false,
    "context_hash": "7e0afd09753effed",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8607129454612732,
    "decision_reason": "high_priority",
    "expected_context_hash": "7e0afd09753effed",
    "forbidden_signature_hash": "4a0466dbb3cb0ca3",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "manifest_row_index": 0,
    "manifest_sample_index": 0,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19",
    "pool_signature_hash": "5b033e33a1d57de2",
    "pool_task_set_hash": "07344d8ff99d9697",
    "source_file": "BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_sequence": [
      19
    ],
    "true_dual_hash": "4fb2dc95e30f31c4",
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "active_hash_before": "d2c0edfced5cf1b3",
    "best_true_reduced_cost": -9.747246,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 18,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 19,
    "certificate_effect": false,
    "context_hash": "a3b5b5263e1cfe17",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8709929585456848,
    "decision_reason": "high_priority",
    "expected_context_hash": "a3b5b5263e1cfe17",
    "forbidden_signature_hash": "d16be31402958c8c",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "manifest_row_index": 1,
    "manifest_sample_index": 1,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12",
    "pool_signature_hash": "5e8d064add26e945",
    "pool_task_set_hash": "6be049fce559e341",
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
    "true_dual_hash": "4e721d29d378a125",
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "active_hash_before": "17dadbafe771952e",
    "best_true_reduced_cost": -6.935715,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 11,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "certificate_effect": false,
    "context_hash": "de2c1d84615d5c71",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9100852012634277,
    "decision_reason": "high_priority",
    "expected_context_hash": "de2c1d84615d5c71",
    "forbidden_signature_hash": "c4a62ea4289cbf19",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "manifest_row_index": 2,
    "manifest_sample_index": 2,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9",
    "pool_signature_hash": "da66c890f9d81836",
    "pool_task_set_hash": "32ed53d0ecd64c89",
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
    "true_dual_hash": "8efb3de0a4ceb57e",
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "active_hash_before": "d2cd6edbbb0e19a5",
    "best_true_reduced_cost": -3.463997,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 12,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 5,
    "certificate_effect": false,
    "context_hash": "157f03afc868de3b",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8218390345573425,
    "decision_reason": "high_priority",
    "expected_context_hash": "157f03afc868de3b",
    "forbidden_signature_hash": "43b8d182947831ab",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "manifest_row_index": 3,
    "manifest_sample_index": 3,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13",
    "pool_signature_hash": "3923d333f2eb61a4",
    "pool_task_set_hash": "241d3df353c8eab4",
    "source_file": "BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_sequence": [
      13
    ],
    "true_dual_hash": "7595051f6357ad9a",
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  }
]
```

## Skipped Counts

```json
{
  "decision_not_selected": 4
}
```

## 边界

- GAT/kNN/OOD 只决定 target-priority 候选，不是 pricing oracle；
- 候选必须来自带完整 context hash / dual / cuts / branch / pool payload 的 capture；
- true-RC negative 不允许永久丢弃；
- 这些候选只能喂给显式 opt-in worker A/B；
- 不能用于 no-negative certificate 或 official lower bound。
