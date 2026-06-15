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
candidate_count = 7
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
    "best_true_reduced_cost": -52.519726,
    "capture_cg_iter": 3,
    "capture_returned_journey_count": 48,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.823053240776062,
    "decision_reason": "high_priority",
    "expected_context_hash": "3d1bd8618099b573",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "manifest_row_index": 16,
    "manifest_sample_index": 16,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8",
    "source_file": "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_sequence": [
      8
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "best_true_reduced_cost": -4.138581667,
    "capture_cg_iter": 16,
    "capture_returned_journey_count": 6,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8623261451721191,
    "decision_reason": "high_priority",
    "expected_context_hash": "d44af494d156d43e",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "manifest_row_index": 21,
    "manifest_sample_index": 21,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_d44af494d156d43e_6",
    "source_file": "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->0:low_time:0"
    ],
    "target_sequence": [
      6
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "best_true_reduced_cost": -29.371658,
    "capture_cg_iter": 6,
    "capture_returned_journey_count": 46,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8148101568222046,
    "decision_reason": "high_priority",
    "expected_context_hash": "09187873900ecefa",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "manifest_row_index": 27,
    "manifest_sample_index": 27,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20",
    "source_file": "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave-extra/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_sequence": [
      6,
      20
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "best_true_reduced_cost": -18.801739389,
    "capture_cg_iter": 7,
    "capture_returned_journey_count": 29,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8177616000175476,
    "decision_reason": "high_priority",
    "expected_context_hash": "39ec05e43b291642",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "manifest_row_index": 28,
    "manifest_sample_index": 28,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1",
    "source_file": "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave-extra/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_sequence": [
      20,
      1
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "best_true_reduced_cost": -16.242464,
    "capture_cg_iter": 8,
    "capture_returned_journey_count": 49,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8786776065826416,
    "decision_reason": "high_priority",
    "expected_context_hash": "727eba0fe29647bc",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "manifest_row_index": 29,
    "manifest_sample_index": 29,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_727eba0fe29647bc_2",
    "source_file": "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave-extra/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->0:low_risk:2"
    ],
    "target_sequence": [
      2
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "best_true_reduced_cost": -25.062302,
    "capture_cg_iter": 8,
    "capture_returned_journey_count": 49,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8543282747268677,
    "decision_reason": "high_priority",
    "expected_context_hash": "e6a026e516dfd2f4",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "manifest_row_index": 31,
    "manifest_sample_index": 31,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_e6a026e516dfd2f4_12_4",
    "source_file": "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave-extra/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_sequence": [
      12,
      4
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  },
  {
    "best_true_reduced_cost": -1.484995,
    "capture_cg_iter": 9,
    "capture_returned_journey_count": 5,
    "certificate_effect": false,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8806465268135071,
    "decision_reason": "high_priority",
    "expected_context_hash": "9f2ee06df420d2ac",
    "gate_role": "gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "manifest_row_index": 32,
    "manifest_sample_index": 32,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_9f2ee06df420d2ac_4_12",
    "source_file": "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave-extra/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      4,
      12
    ],
    "worker_role": "explicit_opt_in_target_priority_roi_probe"
  }
]
```

## Skipped Counts

```json
{
  "decision_not_selected": 27
}
```

## 边界

- GAT/kNN/OOD 只决定 target-priority 候选，不是 pricing oracle；
- true-RC negative 不允许永久丢弃；
- 这些候选只能喂给显式 opt-in worker A/B；
- 不能用于 no-negative certificate 或 official lower bound。
