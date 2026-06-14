# Root Cause target002 Component Drift 报告

日期：2026-06-14

## 目的

本报告比较 target002 historical source context 与同 active hash 的非 source
事件，定位 target context 不能复现的具体组成差异。它只读已有 summary，
不运行 BPC / pricing / RMP / Pulse，也不改变 solver 行为。

## 机器字段

```text
selector_holdout_target002_component_drift = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_target002_component_drift_diagnosed
target_context_hash = 3f914a0d2b97fd27
target_active_hash = f0b96be45c5015c9
non_source_same_active_event_count = 9
pool_signature_hash_same_count = 0
forbidden_signature_hash_same_count = 0
config_matched_exact_returned_task_sets_same_count = 0
all_checks_pass = true
```

## 结论

同一个 active hash 下，非 source 事件没有一个同时复现 source 的
`pool_signature_hash` 或 `forbidden_signature_hash`；config-matched
active-basis capture 也没有复现 source 的 returned task-set batch。
因此 target002 缺失不是简单 active-basis snapshot 字段缺失，而是
pool / forbidden / returned-batch composition 分叉。

target002 source context is not recovered because same-active events drift in pool signature, forbidden signature, RMP objective, and/or returned-batch composition.  Active hash alone is therefore not a sufficient selector or replay key.

## Source Components

```json
{
  "active_hash_before": "f0b96be45c5015c9",
  "context_hash": "3f914a0d2b97fd27",
  "forbidden_signature_hash": "58107ff08c6fea87",
  "pool_journey_count": 180,
  "pool_signature_hash": "f76583ce6e01cc35",
  "pool_task_set_hash": "06b59350e5916882",
  "pricing_best_reduced_cost": -6.110727,
  "pricing_state": "FOUND_NEGATIVE",
  "rmp_objective_before": 766.81749575
}
```

## Field Same Counts

```json
{
  "forbidden_signature_hash": 0,
  "pool_journey_count": 8,
  "pool_signature_hash": 0,
  "pool_task_set_hash": 4,
  "pricing_best_reduced_cost": 2,
  "pricing_state": 3,
  "rmp_objective_before": 0
}
```

## Event Comparisons

```json
[
  {
    "cg_iter": 4,
    "context_hash": "46e7a2883459d4fb",
    "extra_task_sets": [],
    "group_id": "historical_source",
    "missing_source_task_sets": [
      [
        5,
        12,
        18
      ]
    ],
    "repeat": "1",
    "returned_journey_count": 4,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_journey_count": false,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_pricing_best_reduced_cost": true,
    "same_pricing_state": true,
    "same_returned_task_sets": false,
    "same_rmp_objective_before": false
  },
  {
    "cg_iter": 3,
    "context_hash": "71cf005b699054ed",
    "extra_task_sets": [],
    "group_id": "config_matched_active_basis_capture",
    "missing_source_task_sets": [
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
    "repeat": "0",
    "returned_journey_count": 0,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_journey_count": true,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": true,
    "same_pricing_best_reduced_cost": false,
    "same_pricing_state": false,
    "same_returned_task_sets": false,
    "same_rmp_objective_before": false
  },
  {
    "cg_iter": 3,
    "context_hash": "71cf005b699054ed",
    "extra_task_sets": [],
    "group_id": "config_matched_active_basis_capture",
    "missing_source_task_sets": [
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
    "repeat": "0",
    "returned_journey_count": 0,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_journey_count": true,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": true,
    "same_pricing_best_reduced_cost": false,
    "same_pricing_state": false,
    "same_returned_task_sets": false,
    "same_rmp_objective_before": false
  },
  {
    "cg_iter": 3,
    "context_hash": "25942edc9eb0f1d8",
    "extra_task_sets": [],
    "group_id": "config_matched_active_basis_capture",
    "missing_source_task_sets": [
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
    "repeat": "1",
    "returned_journey_count": 0,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_journey_count": true,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_pricing_best_reduced_cost": false,
    "same_pricing_state": false,
    "same_returned_task_sets": false,
    "same_rmp_objective_before": false
  },
  {
    "cg_iter": 3,
    "context_hash": "25942edc9eb0f1d8",
    "extra_task_sets": [],
    "group_id": "config_matched_active_basis_capture",
    "missing_source_task_sets": [
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
    "repeat": "1",
    "returned_journey_count": 0,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_journey_count": true,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_pricing_best_reduced_cost": false,
    "same_pricing_state": false,
    "same_returned_task_sets": false,
    "same_rmp_objective_before": false
  },
  {
    "cg_iter": 3,
    "context_hash": "be5e5e89972d48fe",
    "extra_task_sets": [],
    "group_id": "config_matched_active_basis_capture",
    "missing_source_task_sets": [
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
    "repeat": "2",
    "returned_journey_count": 0,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_journey_count": true,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_pricing_best_reduced_cost": false,
    "same_pricing_state": false,
    "same_returned_task_sets": false,
    "same_rmp_objective_before": false
  },
  {
    "cg_iter": 3,
    "context_hash": "be5e5e89972d48fe",
    "extra_task_sets": [],
    "group_id": "config_matched_active_basis_capture",
    "missing_source_task_sets": [
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
    "repeat": "2",
    "returned_journey_count": 0,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_journey_count": true,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": false,
    "same_pricing_best_reduced_cost": false,
    "same_pricing_state": false,
    "same_returned_task_sets": false,
    "same_rmp_objective_before": false
  },
  {
    "cg_iter": 3,
    "context_hash": "f3fd1968f01e3ad6",
    "extra_task_sets": [],
    "group_id": "no_active_basis_capture",
    "missing_source_task_sets": [],
    "repeat": "0",
    "returned_journey_count": 5,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_journey_count": true,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": true,
    "same_pricing_best_reduced_cost": false,
    "same_pricing_state": true,
    "same_returned_task_sets": true,
    "same_rmp_objective_before": false
  },
  {
    "cg_iter": 3,
    "context_hash": "91f2210b1b8888cb",
    "extra_task_sets": [],
    "group_id": "alias_instance_capture",
    "missing_source_task_sets": [],
    "repeat": "0",
    "returned_journey_count": 5,
    "same_context_hash": false,
    "same_forbidden_signature_hash": false,
    "same_pool_journey_count": true,
    "same_pool_signature_hash": false,
    "same_pool_task_set_hash": true,
    "same_pricing_best_reduced_cost": true,
    "same_pricing_state": true,
    "same_returned_task_sets": true,
    "same_rmp_objective_before": false
  }
]
```

## Checks

```json
{
  "config_matched_does_not_recover_returned_task_sets": true,
  "missing_context_diagnosis_passed": true,
  "no_non_source_same_context_hash": true,
  "no_non_source_same_forbidden_signature_hash": true,
  "no_non_source_same_pool_signature_hash": true,
  "non_source_same_active_events_exist": true,
  "source_target_event_exists": true,
  "target_context_hash_matches_missing_context": true,
  "target_context_not_recovered": true,
  "trajectory_branch_passed": true
}
```
