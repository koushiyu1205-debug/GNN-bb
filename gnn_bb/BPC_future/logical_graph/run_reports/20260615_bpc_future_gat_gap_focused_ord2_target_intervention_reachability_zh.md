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
record_count = 6
reachable_target_intervention_count = 6
reachability_class_counts = {'target_intervention_reachable': 6}
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
    "expected_context_hash": "35a4908dfecb7ff3",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -2.729889,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->18:low_time:0",
      "18->10:low_risk:1",
      "10->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      5,
      18,
      10,
      8,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_target_priority_worker/results.csv",
    "worker_event_count": 7,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "7fc1de982db572be",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -1.508165091,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->10:low_risk:1",
      "10->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      18,
      10,
      12,
      4,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_target_priority_worker/results.csv",
    "worker_event_count": 7,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "8f2fd95e2f03ec41",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -7.582667,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->7:low_energy:1",
      "7->20:low_energy:1",
      "20->1:low_risk:2",
      "1->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      12,
      7,
      20,
      1,
      5,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "1625c1776efc58ed",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -1.147281923,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->7:low_risk:2",
      "7->2:low_risk:2",
      "2->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      12,
      7,
      2,
      1,
      10,
      4
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "355f0684d6e275df",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -4.817581471,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->17:low_time:0",
      "17->3:low_time:0",
      "3->9:low_time:0",
      "9->4:low_risk:2",
      "4->8:low_time:0",
      "8->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      5,
      17,
      3,
      9,
      4,
      8
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "aa78e15d40fb733a",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -4.958868,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->9:low_risk:1",
      "9->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      20,
      9,
      1,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
