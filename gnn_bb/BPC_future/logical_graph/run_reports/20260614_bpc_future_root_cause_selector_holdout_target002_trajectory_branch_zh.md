# Root Cause Selector Holdout target002 Trajectory Branch 报告

日期：2026-06-14

## 目的

本报告只读 target002 source/probe 日志，比较同一 active hash 附近的
 exact context 分叉。它不运行 BPC / pricing / RMP / Pulse，也不改变
 worker、certificate 或 solver 默认行为。

## 机器字段

```text
root_cause_selector_holdout_target002_trajectory_branch = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_target002_trajectory_branch_audited
target_context_hash = 3f914a0d2b97fd27
target_active_hash = f0b96be45c5015c9
same_active_event_count = 10
non_source_same_active_event_count = 9
all_checks_pass = true
```

## 结论

target002 的目标 active hash 可以在多个 probe 中再次到达，但 exact context hash 没有复现。same-active 对比显示 pool/forbidden signature、RMP objective 或 returned batch composition 会分叉；因此 active-task-set 相同并不足以确定后续 pricing universe，production selector 需要更完整的 pool/forbidden/RMP trajectory 前置上下文。

## Same-active Contexts

```json
[
  "25942edc9eb0f1d8",
  "3f914a0d2b97fd27",
  "46e7a2883459d4fb",
  "71cf005b699054ed",
  "91f2210b1b8888cb",
  "be5e5e89972d48fe",
  "f3fd1968f01e3ad6"
]
```

## Comparisons To Source

```json
[
  {
    "cg_iter": 4,
    "context_hash": "46e7a2883459d4fb",
    "event_only_task_sets": [],
    "event_pricing_best_reduced_cost": -6.110727,
    "event_rmp_objective_before": 766.96965575,
    "group_id": "historical_source",
    "objective_delta_vs_source": 0.15216,
    "repeat": "1",
    "same_active_hash": true,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_returned_count": false,
    "same_returned_sequence_set": false,
    "same_returned_task_set_set": false,
    "source_only_task_sets": [
      [
        5,
        12,
        18
      ]
    ],
    "source_pricing_best_reduced_cost": -6.110727,
    "source_rmp_objective_before": 766.81749575
  },
  {
    "cg_iter": 3,
    "context_hash": "71cf005b699054ed",
    "event_only_task_sets": [],
    "event_pricing_best_reduced_cost": null,
    "event_rmp_objective_before": 766.843656,
    "group_id": "config_matched_active_basis_capture",
    "objective_delta_vs_source": 0.02616025,
    "repeat": "0",
    "same_active_hash": true,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": true,
    "same_returned_count": false,
    "same_returned_sequence_set": false,
    "same_returned_task_set_set": false,
    "source_only_task_sets": [
      [
        2,
        3,
        20
      ],
      [
        2,
        10,
        20
      ],
      [
        2,
        13,
        20
      ],
      [
        2,
        20
      ],
      [
        5,
        12,
        18
      ]
    ],
    "source_pricing_best_reduced_cost": -6.110727,
    "source_rmp_objective_before": 766.81749575
  },
  {
    "cg_iter": 3,
    "context_hash": "71cf005b699054ed",
    "event_only_task_sets": [],
    "event_pricing_best_reduced_cost": 0.0,
    "event_rmp_objective_before": 766.843656,
    "group_id": "config_matched_active_basis_capture",
    "objective_delta_vs_source": 0.02616025,
    "repeat": "0",
    "same_active_hash": true,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": true,
    "same_returned_count": false,
    "same_returned_sequence_set": false,
    "same_returned_task_set_set": false,
    "source_only_task_sets": [
      [
        2,
        3,
        20
      ],
      [
        2,
        10,
        20
      ],
      [
        2,
        13,
        20
      ],
      [
        2,
        20
      ],
      [
        5,
        12,
        18
      ]
    ],
    "source_pricing_best_reduced_cost": -6.110727,
    "source_rmp_objective_before": 766.81749575
  },
  {
    "cg_iter": 3,
    "context_hash": "25942edc9eb0f1d8",
    "event_only_task_sets": [],
    "event_pricing_best_reduced_cost": null,
    "event_rmp_objective_before": 766.81512425,
    "group_id": "config_matched_active_basis_capture",
    "objective_delta_vs_source": -0.0023715,
    "repeat": "1",
    "same_active_hash": true,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_returned_count": false,
    "same_returned_sequence_set": false,
    "same_returned_task_set_set": false,
    "source_only_task_sets": [
      [
        2,
        3,
        20
      ],
      [
        2,
        10,
        20
      ],
      [
        2,
        13,
        20
      ],
      [
        2,
        20
      ],
      [
        5,
        12,
        18
      ]
    ],
    "source_pricing_best_reduced_cost": -6.110727,
    "source_rmp_objective_before": 766.81749575
  },
  {
    "cg_iter": 3,
    "context_hash": "25942edc9eb0f1d8",
    "event_only_task_sets": [],
    "event_pricing_best_reduced_cost": 0.0,
    "event_rmp_objective_before": 766.81512425,
    "group_id": "config_matched_active_basis_capture",
    "objective_delta_vs_source": -0.0023715,
    "repeat": "1",
    "same_active_hash": true,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_returned_count": false,
    "same_returned_sequence_set": false,
    "same_returned_task_set_set": false,
    "source_only_task_sets": [
      [
        2,
        3,
        20
      ],
      [
        2,
        10,
        20
      ],
      [
        2,
        13,
        20
      ],
      [
        2,
        20
      ],
      [
        5,
        12,
        18
      ]
    ],
    "source_pricing_best_reduced_cost": -6.110727,
    "source_rmp_objective_before": 766.81749575
  },
  {
    "cg_iter": 3,
    "context_hash": "be5e5e89972d48fe",
    "event_only_task_sets": [],
    "event_pricing_best_reduced_cost": null,
    "event_rmp_objective_before": 766.780917,
    "group_id": "config_matched_active_basis_capture",
    "objective_delta_vs_source": -0.03657875,
    "repeat": "2",
    "same_active_hash": true,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_returned_count": false,
    "same_returned_sequence_set": false,
    "same_returned_task_set_set": false,
    "source_only_task_sets": [
      [
        2,
        3,
        20
      ],
      [
        2,
        10,
        20
      ],
      [
        2,
        13,
        20
      ],
      [
        2,
        20
      ],
      [
        5,
        12,
        18
      ]
    ],
    "source_pricing_best_reduced_cost": -6.110727,
    "source_rmp_objective_before": 766.81749575
  },
  {
    "cg_iter": 3,
    "context_hash": "be5e5e89972d48fe",
    "event_only_task_sets": [],
    "event_pricing_best_reduced_cost": 0.0,
    "event_rmp_objective_before": 766.780917,
    "group_id": "config_matched_active_basis_capture",
    "objective_delta_vs_source": -0.03657875,
    "repeat": "2",
    "same_active_hash": true,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_returned_count": false,
    "same_returned_sequence_set": false,
    "same_returned_task_set_set": false,
    "source_only_task_sets": [
      [
        2,
        3,
        20
      ],
      [
        2,
        10,
        20
      ],
      [
        2,
        13,
        20
      ],
      [
        2,
        20
      ],
      [
        5,
        12,
        18
      ]
    ],
    "source_pricing_best_reduced_cost": -6.110727,
    "source_rmp_objective_before": 766.81749575
  },
  {
    "cg_iter": 3,
    "context_hash": "f3fd1968f01e3ad6",
    "event_only_task_sets": [],
    "event_pricing_best_reduced_cost": -6.1107805,
    "event_rmp_objective_before": 766.8686265,
    "group_id": "no_active_basis_capture",
    "objective_delta_vs_source": 0.05113075,
    "repeat": "0",
    "same_active_hash": true,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": true,
    "same_returned_count": true,
    "same_returned_sequence_set": true,
    "same_returned_task_set_set": true,
    "source_only_task_sets": [],
    "source_pricing_best_reduced_cost": -6.110727,
    "source_rmp_objective_before": 766.81749575
  },
  {
    "cg_iter": 3,
    "context_hash": "91f2210b1b8888cb",
    "event_only_task_sets": [],
    "event_pricing_best_reduced_cost": -6.110727,
    "event_rmp_objective_before": 766.81512425,
    "group_id": "alias_instance_capture",
    "objective_delta_vs_source": -0.0023715,
    "repeat": "0",
    "same_active_hash": true,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": true,
    "same_returned_count": true,
    "same_returned_sequence_set": true,
    "same_returned_task_set_set": true,
    "source_only_task_sets": [],
    "source_pricing_best_reduced_cost": -6.110727,
    "source_rmp_objective_before": 766.81749575
  }
]
```

## Checks

```json
{
  "no_non_source_event_matches_target_context": true,
  "non_source_same_active_events_exist": true,
  "same_active_events_exist": true,
  "same_active_has_objective_or_batch_drift": true,
  "same_active_has_pool_or_forbidden_signature_drift": true,
  "source_target_event_exists": true
}
```