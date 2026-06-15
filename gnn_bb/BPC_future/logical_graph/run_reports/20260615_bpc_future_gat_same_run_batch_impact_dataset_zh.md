# GAT Same-Run Batch Impact Dataset 报告

日期：2026-06-15

## 目的

本报告从同一次求解日志中配对 capture、column addition 和下一轮 RMP，
构造不会发生 context replay drift 的 GAT batch-impact 标签。
它不运行 BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_same_run_batch_impact_dataset = current
status = built
source_file_count = 20
row_count = 68
positive_objective_improvement_count = 56
non_improving_objective_count = 12
objective_positive_rate = 0.823529
objective_non_improving_rate = 0.176471
active_support_changing_count = 39
new_task_set_added_count = 68
instance_count = 20
instance_region_count = 2
instance_regions = ['apollo15_20km', 'tranquillitatis_balmer_like_20km']
pricing_kinds = ['exact']
label_distribution_ready = true
training_blockers = []
non_improving_rows_needed_for_training = 0
objective_label_by_region = {'apollo15_20km': {'positive_objective_improvement': 29, 'non_improving_objective': 6, 'row_count': 35}, 'tranquillitatis_balmer_like_20km': {'positive_objective_improvement': 27, 'non_improving_objective': 6, 'row_count': 33}}
addition_productivity_class_counts = {'active_replacement_task_set': 39, 'changed_inactive_only': 29}
skipped_counts = {'missing_matching_column_addition': 18}
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
training_ready = true
all_checks_pass = true
```

## 样例

```json
[
  {
    "active_changed_task_set_count": 1,
    "added_journeys": 48,
    "addition_productivity_class": "active_replacement_task_set",
    "best_true_reduced_cost": -67.696691,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_task_set_samples": [
      [
        1,
        18
      ],
      [
        2,
        18,
        19
      ],
      [
        5,
        10,
        12,
        16
      ],
      [
        5,
        12,
        16
      ],
      [
        10,
        16,
        18
      ],
      [
        16,
        18
      ],
      [
        5,
        16
      ],
      [
        5,
        15,
        16
      ],
      [
        3,
        18
      ],
      [
        1,
        2,
        10
      ],
      [
        2,
        10,
        18
      ],
      [
        1,
        2
      ],
      [
        2,
        3,
        10,
        16
      ],
      [
        2,
        18
      ],
      [
        2,
        3,
        16
      ],
      [
        3,
        10,
        18
      ]
    ],
    "certificate_effect": false,
    "cg_iter": 4,
    "context_hash": "0df8d5cea7864e69",
    "cut_hash": "d653e60106177bb4",
    "depth": 0,
    "diagnostic_only": true,
    "forbidden_signature_hash": "76b64c9004112874",
    "instance": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204",
    "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_region": "apollo15_20km",
    "label_active_support_changing": 1,
    "label_new_task_set_added": 1,
    "label_objective_improved": 1,
    "new_journeys": 37,
    "new_task_set_count": 37,
    "node_id": 0,
    "objective_after": 694.957354,
    "objective_before": 768.569384,
    "objective_delta": -73.61203,
    "objective_improvement": 73.61203,
    "official_bound_effect": false,
    "pricing_kind": "exact",
    "replacement_journeys": 11,
    "replacement_task_set_count": 11,
    "returned_journey_count": 49,
    "runs_bpc_or_pricing": false,
    "same_run_intervention_observed": true,
    "schema_version": "gat_same_run_batch_impact_row_v1",
    "source_file": "BPC_future/results/gat_same_run_capture_matrix2_20260615/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "training_label_allowed": true,
    "training_label_scope": "same_run_returned_batch",
    "true_dual_hash": "1ce0a0d2ebfba758"
  },
  {
    "active_changed_task_set_count": 0,
    "added_journeys": 48,
    "addition_productivity_class": "changed_inactive_only",
    "best_true_reduced_cost": -22.979615,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_task_set_samples": [
      [
        5,
        10,
        12,
        13
      ],
      [
        5,
        12,
        13
      ],
      [
        5,
        6,
        10,
        12
      ],
      [
        5,
        6,
        12
      ],
      [
        3,
        5,
        12
      ],
      [
        3,
        5,
        10,
        12
      ],
      [
        5,
        12,
        13,
        15
      ],
      [
        8,
        10,
        12,
        13,
        20
      ],
      [
        8,
        12,
        13,
        20
      ],
      [
        6,
        8,
        13,
        20
      ],
      [
        3,
        7,
        8,
        12
      ],
      [
        3,
        6,
        7,
        8
      ],
      [
        5,
        6,
        10,
        12,
        15
      ],
      [
        5,
        6,
        12,
        15
      ],
      [
        3,
        5,
        12,
        15
      ],
      [
        6,
        8,
        10,
        12,
        13
      ]
    ],
    "certificate_effect": false,
    "cg_iter": 5,
    "context_hash": "fec7e16a3758171c",
    "cut_hash": "d653e60106177bb4",
    "depth": 0,
    "diagnostic_only": true,
    "forbidden_signature_hash": "fdaffe3cde3b498f",
    "instance": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204",
    "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_region": "apollo15_20km",
    "label_active_support_changing": 0,
    "label_new_task_set_added": 1,
    "label_objective_improved": 1,
    "new_journeys": 46,
    "new_task_set_count": 46,
    "node_id": 0,
    "objective_after": 690.914829,
    "objective_before": 694.957354,
    "objective_delta": -4.042524999999955,
    "objective_improvement": 4.042524999999955,
    "official_bound_effect": false,
    "pricing_kind": "exact",
    "replacement_journeys": 2,
    "replacement_task_set_count": 2,
    "returned_journey_count": 48,
    "runs_bpc_or_pricing": false,
    "same_run_intervention_observed": true,
    "schema_version": "gat_same_run_batch_impact_row_v1",
    "source_file": "BPC_future/results/gat_same_run_capture_matrix2_20260615/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "training_label_allowed": true,
    "training_label_scope": "same_run_returned_batch",
    "true_dual_hash": "b3a964e273809348"
  },
  {
    "active_changed_task_set_count": 1,
    "added_journeys": 47,
    "addition_productivity_class": "active_replacement_task_set",
    "best_true_reduced_cost": -23.2995114,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_task_set_samples": [
      [
        4,
        6,
        11,
        20
      ],
      [
        5,
        6,
        11,
        20
      ],
      [
        4,
        11,
        12,
        20
      ],
      [
        4,
        11,
        20
      ],
      [
        5,
        11,
        12,
        20
      ],
      [
        4,
        11,
        15,
        20
      ],
      [
        4,
        6,
        11,
        12
      ],
      [
        4,
        6,
        11,
        12,
        15
      ],
      [
        2,
        7,
        8,
        19
      ],
      [
        5,
        7
      ],
      [
        5,
        11,
        20
      ],
      [
        5,
        11,
        15,
        20
      ],
      [
        5,
        6,
        11,
        12
      ],
      [
        5,
        6,
        11,
        12,
        15
      ],
      [
        4,
        6,
        11
      ],
      [
        4,
        6,
        11,
        15
      ]
    ],
    "certificate_effect": false,
    "cg_iter": 7,
    "context_hash": "1fa17aea2063098d",
    "cut_hash": "d653e60106177bb4",
    "depth": 0,
    "diagnostic_only": true,
    "forbidden_signature_hash": "5559157b1af629c3",
    "instance": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204",
    "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_region": "apollo15_20km",
    "label_active_support_changing": 1,
    "label_new_task_set_added": 1,
    "label_objective_improved": 1,
    "new_journeys": 46,
    "new_task_set_count": 46,
    "node_id": 0,
    "objective_after": 665.645642,
    "objective_before": 681.4518,
    "objective_delta": -15.806158000000096,
    "objective_improvement": 15.806158000000096,
    "official_bound_effect": false,
    "pricing_kind": "exact",
    "replacement_journeys": 1,
    "replacement_task_set_count": 1,
    "returned_journey_count": 47,
    "runs_bpc_or_pricing": false,
    "same_run_intervention_observed": true,
    "schema_version": "gat_same_run_batch_impact_row_v1",
    "source_file": "BPC_future/results/gat_same_run_capture_matrix2_20260615/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "training_label_allowed": true,
    "training_label_scope": "same_run_returned_batch",
    "true_dual_hash": "09d58d42a46b577b"
  },
  {
    "active_changed_task_set_count": 3,
    "added_journeys": 10,
    "addition_productivity_class": "active_replacement_task_set",
    "best_true_reduced_cost": -2.835253,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_task_set_samples": [
      [
        3,
        7,
        13,
        19
      ],
      [
        5,
        12,
        15,
        16
      ],
      [
        5,
        6,
        11,
        12,
        13
      ],
      [
        5,
        6,
        11,
        16
      ],
      [
        5,
        6,
        11,
        13,
        15
      ],
      [
        5,
        6,
        12,
        13
      ],
      [
        5,
        6,
        16
      ],
      [
        5,
        6,
        13,
        15
      ],
      [
        5,
        10,
        12,
        16
      ],
      [
        4,
        8,
        12,
        15
      ]
    ],
    "certificate_effect": false,
    "cg_iter": 8,
    "context_hash": "19758e70e56ed7e7",
    "cut_hash": "d653e60106177bb4",
    "depth": 0,
    "diagnostic_only": true,
    "forbidden_signature_hash": "90773505d87758ac",
    "instance": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204",
    "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_region": "apollo15_20km",
    "label_active_support_changing": 1,
    "label_new_task_set_added": 1,
    "label_objective_improved": 1,
    "new_journeys": 6,
    "new_task_set_count": 6,
    "node_id": 0,
    "objective_after": 665.022629,
    "objective_before": 665.645642,
    "objective_delta": -0.6230129999999008,
    "objective_improvement": 0.6230129999999008,
    "official_bound_effect": false,
    "pricing_kind": "exact",
    "replacement_journeys": 4,
    "replacement_task_set_count": 4,
    "returned_journey_count": 10,
    "runs_bpc_or_pricing": false,
    "same_run_intervention_observed": true,
    "schema_version": "gat_same_run_batch_impact_row_v1",
    "source_file": "BPC_future/results/gat_same_run_capture_matrix2_20260615/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "training_label_allowed": true,
    "training_label_scope": "same_run_returned_batch",
    "true_dual_hash": "6ac906efca5737d6"
  },
  {
    "active_changed_task_set_count": 5,
    "added_journeys": 48,
    "addition_productivity_class": "active_replacement_task_set",
    "best_true_reduced_cost": -24.417731778,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_task_set_samples": [
      [
        7,
        13,
        20
      ],
      [
        5,
        7,
        15
      ],
      [
        7,
        13,
        15
      ],
      [
        15,
        18,
        19
      ],
      [
        7,
        20
      ],
      [
        5,
        8,
        17
      ],
      [
        8,
        13,
        17
      ],
      [
        4,
        5,
        6,
        11
      ],
      [
        19,
        20
      ],
      [
        4,
        6,
        11,
        13
      ],
      [
        15,
        19
      ],
      [
        3,
        4
      ],
      [
        5,
        8,
        13,
        18
      ],
      [
        7,
        15
      ],
      [
        4,
        5,
        11,
        18
      ],
      [
        4,
        11,
        13,
        18
      ]
    ],
    "certificate_effect": false,
    "cg_iter": 6,
    "context_hash": "b9550ffc9a42531a",
    "cut_hash": "d653e60106177bb4",
    "depth": 0,
    "diagnostic_only": true,
    "forbidden_signature_hash": "8a7f2efca8be1f44",
    "instance": "apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306",
    "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "instance_region": "apollo15_20km",
    "label_active_support_changing": 1,
    "label_new_task_set_added": 1,
    "label_objective_improved": 1,
    "new_journeys": 40,
    "new_task_set_count": 40,
    "node_id": 0,
    "objective_after": 727.62422,
    "objective_before": 782.438224,
    "objective_delta": -54.814003999999954,
    "objective_improvement": 54.814003999999954,
    "official_bound_effect": false,
    "pricing_kind": "exact",
    "replacement_journeys": 8,
    "replacement_task_set_count": 8,
    "returned_journey_count": 48,
    "runs_bpc_or_pricing": false,
    "same_run_intervention_observed": true,
    "schema_version": "gat_same_run_batch_impact_row_v1",
    "source_file": "BPC_future/results/gat_same_run_capture_matrix2_20260615/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json.jsonl",
    "training_label_allowed": true,
    "training_label_scope": "same_run_returned_batch",
    "true_dual_hash": "9973b6cde0956787"
  },
  {
    "active_changed_task_set_count": 4,
    "added_journeys": 42,
    "addition_productivity_class": "active_replacement_task_set",
    "best_true_reduced_cost": -19.1028872,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_task_set_samples": [
      [
        10,
        11,
        12,
        16
      ],
      [
        6,
        11,
        12,
        14
      ],
      [
        6,
        11,
        12,
        16
      ],
      [
        6,
        10,
        11,
        16
      ],
      [
        6,
        10,
        11,
        14
      ],
      [
        10,
        12,
        16
      ],
      [
        11,
        12,
        14
      ],
      [
        11,
        12,
        16
      ],
      [
        10,
        11,
        14
      ],
      [
        10,
        11,
        16
      ],
      [
        6,
        12,
        14
      ],
      [
        6,
        10,
        14
      ],
      [
        6,
        12,
        16
      ],
      [
        6,
        10,
        16
      ],
      [
        6,
        11,
        14
      ],
      [
        6,
        11,
        16
      ]
    ],
    "certificate_effect": false,
    "cg_iter": 7,
    "context_hash": "b6507dfb6db81d64",
    "cut_hash": "d653e60106177bb4",
    "depth": 0,
    "diagnostic_only": true,
    "forbidden_signature_hash": "a9fa6948e89224a2",
    "instance": "apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306",
    "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "instance_region": "apollo15_20km",
    "label_active_support_changing": 1,
    "label_new_task_set_added": 1,
    "label_objective_improved": 1,
    "new_journeys": 28,
    "new_task_set_count": 28,
    "node_id": 0,
    "objective_after": 714.637579,
    "objective_before": 727.62422,
    "objective_delta": -12.986641000000077,
    "objective_improvement": 12.986641000000077,
    "official_bound_effect": false,
    "pricing_kind": "exact",
    "replacement_journeys": 14,
    "replacement_task_set_count": 14,
    "returned_journey_count": 42,
    "runs_bpc_or_pricing": false,
    "same_run_intervention_observed": true,
    "schema_version": "gat_same_run_batch_impact_row_v1",
    "source_file": "BPC_future/results/gat_same_run_capture_matrix2_20260615/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json.jsonl",
    "training_label_allowed": true,
    "training_label_scope": "same_run_returned_batch",
    "true_dual_hash": "3fd56392816e9c8d"
  },
  {
    "active_changed_task_set_count": 0,
    "added_journeys": 3,
    "addition_productivity_class": "changed_inactive_only",
    "best_true_reduced_cost": -0.540998,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_task_set_samples": [
      [
        2,
        6,
        18
      ],
      [
        6,
        9,
        18
      ],
      [
        6,
        14,
        18
      ]
    ],
    "certificate_effect": false,
    "cg_iter": 8,
    "context_hash": "2778facbb7f739f7",
    "cut_hash": "d653e60106177bb4",
    "depth": 0,
    "diagnostic_only": true,
    "forbidden_signature_hash": "1db513c112baae4a",
    "instance": "apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306",
    "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "instance_region": "apollo15_20km",
    "label_active_support_changing": 0,
    "label_new_task_set_added": 1,
    "label_objective_improved": 0,
    "new_journeys": 2,
    "new_task_set_count": 2,
    "node_id": 0,
    "objective_after": 714.637579,
    "objective_before": 714.637579,
    "objective_delta": 0.0,
    "objective_improvement": 0.0,
    "official_bound_effect": false,
    "pricing_kind": "exact",
    "replacement_journeys": 1,
    "replacement_task_set_count": 1,
    "returned_journey_count": 3,
    "runs_bpc_or_pricing": false,
    "same_run_intervention_observed": true,
    "schema_version": "gat_same_run_batch_impact_row_v1",
    "source_file": "BPC_future/results/gat_same_run_capture_matrix2_20260615/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json.jsonl",
    "training_label_allowed": true,
    "training_label_scope": "same_run_returned_batch",
    "true_dual_hash": "fcfcdaa4382d2e0a"
  },
  {
    "active_changed_task_set_count": 0,
    "added_journeys": 3,
    "addition_productivity_class": "changed_inactive_only",
    "best_true_reduced_cost": -1.152589,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_task_set_samples": [
      [
        1,
        4,
        5,
        6
      ],
      [
        1,
        4,
        5
      ],
      [
        1,
        4,
        5,
        6,
        18
      ]
    ],
    "certificate_effect": false,
    "cg_iter": 9,
    "context_hash": "5e2ed80c8802533a",
    "cut_hash": "d653e60106177bb4",
    "depth": 0,
    "diagnostic_only": true,
    "forbidden_signature_hash": "9920c0bb2e86adcb",
    "instance": "apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306",
    "instance_path": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "instance_region": "apollo15_20km",
    "label_active_support_changing": 0,
    "label_new_task_set_added": 1,
    "label_objective_improved": 0,
    "new_journeys": 3,
    "new_task_set_count": 3,
    "node_id": 0,
    "objective_after": 714.637579,
    "objective_before": 714.637579,
    "objective_delta": 0.0,
    "objective_improvement": 0.0,
    "official_bound_effect": false,
    "pricing_kind": "exact",
    "replacement_journeys": 0,
    "replacement_task_set_count": 0,
    "returned_journey_count": 3,
    "runs_bpc_or_pricing": false,
    "same_run_intervention_observed": true,
    "schema_version": "gat_same_run_batch_impact_row_v1",
    "source_file": "BPC_future/results/gat_same_run_capture_matrix2_20260615/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json.jsonl",
    "training_label_allowed": true,
    "training_label_scope": "same_run_returned_batch",
    "true_dual_hash": "cc113aa1972dba7b"
  }
]
```

## 结论

- 这类样本比 offline replay 更干净，因为 target/context/加列/下一轮 RMP 都来自同一次运行；
- 只有 `training_ready=true` 才允许进入 GAT 训练；当前若为 false，说明样本量、正负标签或实例/family 分布不足；
- 如果 `need_more_non_improving_objective_rows` 存在，说明当前 exact add-column 样本天然偏向改善动作，需要继续采 hard-tail 中加列但 RMP 不动或弱动的同一上下文对照；
- 该数据只允许做离线 GAT trajectory-impact 监督，不能参与 pricing certificate。
