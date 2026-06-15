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
    "expected_context_hash": "3a059da228ba2c81",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -0.006555667,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3a059da228ba2c81_12_2_1_5_7_3_8",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->2:low_risk:1",
      "2->1:low_time:0",
      "1->5:low_time:0",
      "5->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      12,
      2,
      1,
      5,
      7,
      3,
      8
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3a059da228ba2c81_12_2_1_5_7_3_8_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "805e5fc463a05fb8",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -2.360002333,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_805e5fc463a05fb8_2_11_13_3_9_12",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->11:low_time:0",
      "11->13:low_time:0",
      "13->3:low_risk:1",
      "3->9:low_time:0",
      "9->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      2,
      11,
      13,
      3,
      9,
      12
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_805e5fc463a05fb8_2_11_13_3_9_12_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "38ffc02bc19f2143",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -8.483300556,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_38ffc02bc19f2143_13_8_11_9_5",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->8:low_time:0",
      "8->11:low_energy:1",
      "11->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      13,
      8,
      11,
      9,
      5
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_38ffc02bc19f2143_13_8_11_9_5_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "66de5b1da5c5614e",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -3.412270286,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_66de5b1da5c5614e_11_9_5_16_6_19",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->11:low_time:0",
      "11->9:low_time:0",
      "9->5:low_time:0",
      "5->16:low_risk:1",
      "16->6:low_risk:2",
      "6->19:low_time:0",
      "19->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      11,
      9,
      5,
      16,
      6,
      19
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_66de5b1da5c5614e_11_9_5_16_6_19_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
