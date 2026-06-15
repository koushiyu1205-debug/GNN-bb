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
    "expected_context_hash": "01430159f79364bf",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -2.442716,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->10:low_risk:1",
      "10->13:low_risk:1",
      "13->0:low_risk:1"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      3,
      10,
      13,
      7,
      19
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "f567a0928007db23",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -9.949784909,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      14,
      19,
      5
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "5c5a1e3be100b071",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -3.68290325,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->20:low_risk:2",
      "20->2:low_time:0",
      "2->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      12,
      20,
      2
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "084e39c1f4a0fc67",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -1.666983,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->20:low_time:0",
      "20->0:low_energy:1"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      1,
      20,
      4
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_target_priority_worker/results.csv",
    "worker_event_count": 8,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
