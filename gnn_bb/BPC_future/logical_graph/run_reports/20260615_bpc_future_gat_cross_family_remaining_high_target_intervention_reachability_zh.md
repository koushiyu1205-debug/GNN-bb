# GAT Target Intervention Reachability Audit 报告

日期：2026-06-14

## 目的

本报告只读 target-priority runbook 和已有 JSONL 日志，判断候选是否真的
进入了同上下文 worker target intervention。它不运行 BPC / pricing / RMP / worker，
不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_target_intervention_reachability = current
status = audited
record_count = 4
reachable_target_intervention_count = 4
reachability_class_counts = {'target_intervention_reachable': 4}
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## 解释

- `target_intervention_reachable` 才允许进入 ROI label 构建；
- `worker_context_not_reached` 表示 dual/cuts/branch/forbidden context 没复现；
- `worker_hook_not_triggered` 表示日志里没有 worker 事件；
- `worker_stage_mismatch` / `capture_learning_policy_mismatch` 是 runbook 配置错误；
- 其他状态必须进 invalid bucket，不能当 GAT 正负标签。

## Records

```json
[
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "301df9ab59b370e5",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -5.940284613,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->8:low_risk:2",
      "8->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      3,
      8,
      9,
      14
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "10d0ac41456ac922",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -4.188133,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_10d0ac41456ac922_13_19_10_18_1_11_12_5",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->13:low_risk:1",
      "13->19:low_time:0",
      "19->10:low_risk:2",
      "10->18:low_time:0",
      "18->1:low_time:0",
      "1->11:low_time:0",
      "11->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      13,
      19,
      10,
      18,
      1,
      11,
      12,
      5
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_10d0ac41456ac922_13_19_10_18_1_11_12_5_target_priority_worker/results.csv",
    "worker_event_count": 8,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "1bb852f9988a595e",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -4.855814143,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      6,
      8,
      12
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "4716509a0e100011",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -18.610697,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_09_seed61817_4716509a0e100011_15_2_14_20",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->2:low_risk:1",
      "2->14:low_time:0",
      "14->20:low_risk:2",
      "20->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      15,
      2,
      14,
      20
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_09_seed61817_4716509a0e100011_15_2_14_20_target_priority_worker/results.csv",
    "worker_event_count": 8,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
