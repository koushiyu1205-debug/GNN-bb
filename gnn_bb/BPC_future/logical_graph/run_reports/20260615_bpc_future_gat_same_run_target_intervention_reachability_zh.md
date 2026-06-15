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
reachable_target_intervention_count = 0
reachability_class_counts = {'missing_worker_log': 5, 'worker_executed_without_target_causal_match': 1}
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
    "expected_context_hash": "587e2ac350a8619b",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": 42.965988,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "INCOMPLETE_LIMIT",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_executed_without_target_causal_match",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->9:low_time:0",
      "9->0:low_time:0"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      3,
      9
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_target_priority_worker/results.csv",
    "worker_event_count": 3,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "ea2f1344458c548f",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "missing_worker_log",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      1,
      11
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 0
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "09187873900ecefa",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "missing_worker_log",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      6,
      20
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 0
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "39ec05e43b291642",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "missing_worker_log",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      20,
      1
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 0
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "b46cdc0f247ab6e3",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "missing_worker_log",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->8:low_time:0",
      "8->0:low_time:0"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      7,
      8
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 0
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "3a9af4966d4b91d5",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_18_12",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "missing_worker_log",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->18:low_risk:2",
      "18->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      8,
      18,
      12
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_18_12_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 0
  }
]
```

## 下一步

improve_target_reachability_or_budget_before_labeling
