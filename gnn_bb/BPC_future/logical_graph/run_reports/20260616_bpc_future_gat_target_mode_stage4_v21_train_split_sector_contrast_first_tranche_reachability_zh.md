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
record_count = 9
reachable_target_intervention_count = 9
reachability_class_counts = {'target_intervention_reachable': 9}
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
    "expected_context_hash": "0df8d5cea7864e69",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -67.696691,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb1_1_18",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->18:low_risk:2",
      "18->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      1,
      18
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb1_1_18_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "0df8d5cea7864e69",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -39.677578,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb2_16_5_12_10",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->5:low_risk:2",
      "5->12:low_time:0",
      "12->10:low_risk:2",
      "10->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      16,
      5,
      12,
      10
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb2_16_5_12_10_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "0df8d5cea7864e69",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -29.221277,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb3_16_3_2_10",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->16:low_risk:2",
      "16->3:low_time:0",
      "3->2:low_risk:2",
      "2->10:low_time:0",
      "10->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      16,
      3,
      2,
      10
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb3_16_3_2_10_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "b9550ffc9a42531a",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -24.417731778,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb1_13_20_7",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->13:low_time:0",
      "13->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      13,
      20,
      7
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb1_13_20_7_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "b9550ffc9a42531a",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -15.232663667,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb2_5_4_6_11",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      5,
      4,
      6,
      11
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb2_5_4_6_11_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "b9550ffc9a42531a",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -8.89334,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb3_5_19",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      5,
      19
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb3_5_19_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "4e481a6307fca228",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -25.988531,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb1_11_4_7",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->11:low_time:0",
      "11->4:low_energy:1",
      "4->7:low_energy:1",
      "7->0:low_energy:1"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      11,
      4,
      7
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb1_11_4_7_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "4e481a6307fca228",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -15.800567,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb2_10_11_7_3_14",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->10:low_risk:2",
      "10->11:low_risk:1",
      "11->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      10,
      11,
      7,
      3,
      14
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb2_10_11_7_3_14_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "4e481a6307fca228",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -4.306951,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb3_11_7",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      11,
      7
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb3_11_7_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
