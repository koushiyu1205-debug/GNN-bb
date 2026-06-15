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
record_count = 3
reachable_target_intervention_count = 3
reachability_class_counts = {'target_intervention_reachable': 3}
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
    "expected_context_hash": "96c5f5928a47fe72",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -21.353882,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_96c5f5928a47fe72_16_4_19_12_20",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->4:low_time:0",
      "4->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      16,
      4,
      19,
      12,
      20
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord7_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_96c5f5928a47fe72_16_4_19_12_20_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "fc8f27326a163867",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -1.891257,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_fc8f27326a163867_16_15_19_6_12_11_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->16:low_risk:1",
      "16->15:low_risk:2",
      "15->19:low_time:0",
      "19->6:low_energy:1",
      "6->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      16,
      15,
      19,
      6,
      12,
      11,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord7_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_fc8f27326a163867_16_15_19_6_12_11_13_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "55a386bc49af1dda",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -21.258185,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->16:low_risk:1",
      "16->4:low_risk:2",
      "4->14:low_risk:2",
      "14->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      16,
      4,
      14,
      11,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord7_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
