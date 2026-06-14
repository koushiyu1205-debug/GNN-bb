# Root Cause Selector Holdout target002 Drift Audit 报告

日期：2026-06-14

## 目的

本报告只读 target002 原始 pt0.3 capture 与 config-matched selector holdout
 capture 日志，审计剩余 1 个 expected context 为什么仍未命中。它不运行
 BPC / pricing / RMP / Pulse，也不改变 worker、certificate 或 solver 默认行为。

## 机器字段

```text
root_cause_selector_holdout_target002_drift_audit = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_target002_context_drift_audited
target_context_hash = 3f914a0d2b97fd27
target_active_hash = f0b96be45c5015c9
source_target_hit_count = 1
new_target_hit_count = 0
new_same_active_event_count = 6
new_same_active_found_negative_count = 0
new_same_active_incomplete_count = 6
capture_audit_expected_context_hit_count = 9
capture_audit_expected_context_hash_count = 10
capture_audit_ready_for_selector_holdout = false
all_checks_pass = true
```

## 结论

target002 的原始 pt0.3 capture 中存在目标 context，但 config-matched active-basis capture 没有复现该 exact context。新采集仍能到达同一 active-hash 邻域，并且 no-certificate-effect / active-basis snapshot 契约全部满足；剩余缺口是同一 active trajectory 下 returned batch / time-limit 分叉，而不是证书或 capture 字段污染。

## Source target events

```json
[
  {
    "active_hash_before": "f0b96be45c5015c9",
    "captured_journey_count": 5,
    "cg_iter": 3,
    "context_hash": "3f914a0d2b97fd27",
    "log_path": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
    "pricing_best_reduced_cost": -6.110727,
    "pricing_kind": "heuristic",
    "pricing_state": "FOUND_NEGATIVE",
    "repeat": "0",
    "returned_journey_count": 5,
    "returned_sequences_sample": [
      [
        [
          13,
          2,
          20
        ]
      ],
      [
        [
          12,
          18,
          5
        ]
      ],
      [
        [
          10,
          2,
          20
        ]
      ],
      [
        [
          3,
          2,
          20
        ]
      ],
      [
        [
          20,
          2
        ]
      ]
    ],
    "returned_task_sets_sample": [
      [
        2,
        13,
        20
      ],
      [
        5,
        12,
        18
      ],
      [
        2,
        10,
        20
      ],
      [
        2,
        3,
        20
      ],
      [
        2,
        20
      ]
    ],
    "rmp_objective_before": 766.81749575
  }
]
```

## New same-active events

```json
[
  {
    "active_hash_before": "f0b96be45c5015c9",
    "captured_journey_count": 0,
    "cg_iter": 3,
    "context_hash": "71cf005b699054ed",
    "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
    "pricing_best_reduced_cost": null,
    "pricing_kind": "heuristic",
    "pricing_state": "INCOMPLETE_LIMIT",
    "repeat": "0",
    "returned_journey_count": 0,
    "returned_sequences_sample": [],
    "returned_task_sets_sample": [],
    "rmp_objective_before": 766.843656
  },
  {
    "active_hash_before": "f0b96be45c5015c9",
    "captured_journey_count": 0,
    "cg_iter": 3,
    "context_hash": "71cf005b699054ed",
    "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
    "pricing_best_reduced_cost": 0.0,
    "pricing_kind": "exact",
    "pricing_state": "INCOMPLETE_LIMIT",
    "repeat": "0",
    "returned_journey_count": 0,
    "returned_sequences_sample": [],
    "returned_task_sets_sample": [],
    "rmp_objective_before": 766.843656
  },
  {
    "active_hash_before": "f0b96be45c5015c9",
    "captured_journey_count": 0,
    "cg_iter": 3,
    "context_hash": "25942edc9eb0f1d8",
    "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
    "pricing_best_reduced_cost": null,
    "pricing_kind": "heuristic",
    "pricing_state": "INCOMPLETE_LIMIT",
    "repeat": "1",
    "returned_journey_count": 0,
    "returned_sequences_sample": [],
    "returned_task_sets_sample": [],
    "rmp_objective_before": 766.81512425
  },
  {
    "active_hash_before": "f0b96be45c5015c9",
    "captured_journey_count": 0,
    "cg_iter": 3,
    "context_hash": "25942edc9eb0f1d8",
    "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
    "pricing_best_reduced_cost": 0.0,
    "pricing_kind": "exact",
    "pricing_state": "INCOMPLETE_LIMIT",
    "repeat": "1",
    "returned_journey_count": 0,
    "returned_sequences_sample": [],
    "returned_task_sets_sample": [],
    "rmp_objective_before": 766.81512425
  },
  {
    "active_hash_before": "f0b96be45c5015c9",
    "captured_journey_count": 0,
    "cg_iter": 3,
    "context_hash": "be5e5e89972d48fe",
    "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
    "pricing_best_reduced_cost": null,
    "pricing_kind": "heuristic",
    "pricing_state": "INCOMPLETE_LIMIT",
    "repeat": "2",
    "returned_journey_count": 0,
    "returned_sequences_sample": [],
    "returned_task_sets_sample": [],
    "rmp_objective_before": 766.780917
  },
  {
    "active_hash_before": "f0b96be45c5015c9",
    "captured_journey_count": 0,
    "cg_iter": 3,
    "context_hash": "be5e5e89972d48fe",
    "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
    "pricing_best_reduced_cost": 0.0,
    "pricing_kind": "exact",
    "pricing_state": "INCOMPLETE_LIMIT",
    "repeat": "2",
    "returned_journey_count": 0,
    "returned_sequences_sample": [],
    "returned_task_sets_sample": [],
    "rmp_objective_before": 766.780917
  }
]
```

## 检查项

```json
{
  "new_capture_has_complete_active_basis": true,
  "new_capture_has_no_certificate_effect_bad_count": true,
  "new_capture_has_same_active_hash_events": true,
  "new_logs_exist": true,
  "new_target_context_missing": true,
  "overall_selector_holdout_not_ready": true,
  "source_logs_exist": true,
  "source_target_context_exists": true
}
```
