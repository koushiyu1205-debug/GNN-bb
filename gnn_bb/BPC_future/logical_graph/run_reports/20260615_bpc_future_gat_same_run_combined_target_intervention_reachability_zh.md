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
record_count = 12
reachable_target_intervention_count = 12
reachability_class_counts = {'target_intervention_reachable': 12}
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
    "first_executed_best_rc": -7.298596667,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->9:low_time:0",
      "9->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      3,
      9,
      11,
      14
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "ea2f1344458c548f",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -62.608718,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      1,
      11
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "09187873900ecefa",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -29.371658,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      6,
      20,
      4,
      16
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "39ec05e43b291642",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -18.801739389,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      20,
      1,
      16,
      9
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "b46cdc0f247ab6e3",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -7.43333825,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->8:low_time:0",
      "8->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      7,
      8,
      2,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "3a9af4966d4b91d5",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -0.246951143,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_18_12",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->18:low_risk:2",
      "18->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      8,
      18,
      12
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_18_12_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "8bd56cf157d96aaa",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -3.334627533,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->20:low_time:0",
      "20->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      18,
      20,
      11,
      1,
      17
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "085044441345625f",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -5.861629387,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      20,
      14,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "5704f305b764baf5",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -6.186580667,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_risk:2",
      "1->14:low_risk:2",
      "14->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      20,
      1,
      14
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "9d086dc2401550f2",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -0.352494,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->9:low_time:0",
      "9->3:low_risk:2",
      "3->10:low_risk:2",
      "10->11:low_risk:1",
      "11->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      9,
      3,
      10,
      11
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "6465dff938f298e1",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -4.853569,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->9:low_time:0",
      "9->1:low_risk:2",
      "1->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      9,
      1,
      12
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "eb76f8c2c929ecb9",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -4.7719555,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      7,
      4,
      5
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
