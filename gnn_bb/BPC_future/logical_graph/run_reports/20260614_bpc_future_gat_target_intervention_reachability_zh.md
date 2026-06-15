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
record_count = 11
reachable_target_intervention_count = 0
reachability_class_counts = {'missing_worker_log': 3, 'worker_context_not_reached': 1, 'worker_stage_mismatch': 7}
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
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "7e0afd09753effed",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_context_not_reached",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      19
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_target_priority_worker/results.csv",
    "worker_event_count": 12,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "a3b5b5263e1cfe17",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "missing_worker_log",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->14:low_time:0",
      "14->5:low_risk:2",
      "5->8:low_time:0",
      "8->18:low_risk:2",
      "18->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      14,
      5,
      8,
      18,
      12
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 0
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "de2c1d84615d5c71",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "missing_worker_log",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->6:low_risk:2",
      "6->1:low_risk:2",
      "1->20:low_time:0",
      "20->9:low_risk:2",
      "9->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      14,
      6,
      1,
      20,
      9
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 0
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "157f03afc868de3b",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "missing_worker_log",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      13
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 0
  },
  {
    "capture_pricing_kind": "",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "3d1bd8618099b573",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "learning_policy_kept": false,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_stage_mismatch",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": false,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      8
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "d44af494d156d43e",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "learning_policy_kept": false,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_d44af494d156d43e_6",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_stage_mismatch",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": false,
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->0:low_time:0"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      6
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_d44af494d156d43e_6_target_priority_worker/results.csv",
    "worker_event_count": 10,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "",
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
    "learning_policy_kept": false,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_stage_mismatch",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": false,
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
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "",
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
    "learning_policy_kept": false,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_stage_mismatch",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": false,
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
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "727eba0fe29647bc",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "learning_policy_kept": false,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_727eba0fe29647bc_2",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_stage_mismatch",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": false,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      2
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_727eba0fe29647bc_2_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "e6a026e516dfd2f4",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "learning_policy_kept": false,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_e6a026e516dfd2f4_12_4",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_stage_mismatch",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": false,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      12,
      4
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_e6a026e516dfd2f4_12_4_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "9f2ee06df420d2ac",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "learning_policy_kept": false,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_9f2ee06df420d2ac_4_12",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_stage_mismatch",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": false,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      4,
      12
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_family_20260614/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_9f2ee06df420d2ac_4_12_target_priority_worker/results.csv",
    "worker_event_count": 0,
    "worker_log_count": 1
  }
]
```

## 下一步

build_same_stage_target_worker_hook
