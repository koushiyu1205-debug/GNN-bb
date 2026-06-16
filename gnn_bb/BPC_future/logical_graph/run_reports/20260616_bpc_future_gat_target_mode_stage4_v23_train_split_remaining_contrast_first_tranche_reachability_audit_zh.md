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
    "expected_context_hash": "d519291840dd7000",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -68.344953,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb1_14_10",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->10:low_time:0",
      "10->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      14,
      10
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb1_14_10_target_priority_worker/results.csv",
    "worker_event_count": 9,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "d519291840dd7000",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -9.973161,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb2_5_1_2_18_3",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->18:low_time:0",
      "18->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      5,
      1,
      2,
      18,
      3
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb2_5_1_2_18_3_target_priority_worker/results.csv",
    "worker_event_count": 8,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "d519291840dd7000",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -1.864621,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb3_8_11",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->11:low_time:0",
      "11->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      8,
      11
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb3_8_11_target_priority_worker/results.csv",
    "worker_event_count": 8,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "ddcb5387bef3bf63",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -83.5112654,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb1_2_17_16",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->17:low_risk:1",
      "17->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      2,
      17,
      16
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb1_2_17_16_target_priority_worker/results.csv",
    "worker_event_count": 8,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "ddcb5387bef3bf63",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -28.8175178,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb2_8_4_5_16",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->8:low_energy:1",
      "8->4:low_time:0",
      "4->5:low_time:0",
      "5->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      8,
      4,
      5,
      16
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb2_8_4_5_16_target_priority_worker/results.csv",
    "worker_event_count": 7,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "ddcb5387bef3bf63",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -11.230681,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb3_10_3",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->10:low_risk:2",
      "10->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      10,
      3
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb3_10_3_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "67c11b5ec80925ec",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -37.8568215,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb1_19_16",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->16:low_risk:2",
      "16->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      19,
      16
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb1_19_16_target_priority_worker/results.csv",
    "worker_event_count": 8,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "67c11b5ec80925ec",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -13.062224625,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb2_5_1_15_3",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->15:low_time:0",
      "15->3:low_time:0",
      "3->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      5,
      1,
      15,
      3
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb2_5_1_15_3_target_priority_worker/results.csv",
    "worker_event_count": 9,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "67c11b5ec80925ec",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -0.183465,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb3_5_1_2_18_3",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->18:low_risk:2",
      "18->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      5,
      1,
      2,
      18,
      3
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb3_5_1_2_18_3_target_priority_worker/results.csv",
    "worker_event_count": 8,
    "worker_log_count": 1
  },
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
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb1_1_18_target_priority_worker/results.csv",
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
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb2_16_5_12_10_target_priority_worker/results.csv",
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
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb3_16_3_2_10_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
