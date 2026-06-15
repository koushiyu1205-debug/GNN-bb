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
    "expected_context_hash": "8c83e7f0dc9171d5",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -9.820802892,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      3,
      5,
      10,
      8,
      17
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_target_priority_worker/results.csv",
    "worker_event_count": 11,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "12cfa32e4756fd37",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -9.050209,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->9:low_time:0",
      "9->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      3,
      9,
      4,
      2,
      10
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_target_priority_worker/results.csv",
    "worker_event_count": 11,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "c4004463c80918b5",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -11.34037675,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->9:low_energy:1",
      "9->3:low_time:0",
      "3->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      9,
      3,
      20,
      4,
      2,
      10
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_target_priority_worker/results.csv",
    "worker_event_count": 12,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "4d45ffb07ab7073b",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -6.3950645,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_4d45ffb07ab7073b_12_13_4_10_17",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      12,
      13,
      4,
      10,
      17
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_4d45ffb07ab7073b_12_13_4_10_17_target_priority_worker/results.csv",
    "worker_event_count": 11,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
