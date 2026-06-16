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
reachable_target_intervention_count = 4
reachability_class_counts = {'target_intervention_reachable': 4, 'worker_context_not_reached': 5}
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
    "expected_context_hash": "9a2ca522ff49991c",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_9a2ca522ff49991c_mb1_35_7_13_32_44",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_context_not_reached",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->35:low_risk:2",
      "35->7:low_time:0",
      "7->13:low_risk:2",
      "13->32:low_risk:2",
      "32->44:low_time:0",
      "44->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      35,
      7,
      13,
      32,
      44
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/task050_apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_9a2ca522ff49991c_mb1_35_7_13_32_44_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "9a2ca522ff49991c",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_9a2ca522ff49991c_mb2_35_7_13_32_44_42",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_context_not_reached",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->35:low_risk:2",
      "35->7:low_time:0",
      "7->13:low_risk:2",
      "13->32:low_risk:2",
      "32->44:low_time:0",
      "44->42:low_time:0",
      "42->0:low_risk:1"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      35,
      7,
      13,
      32,
      44,
      42
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/task050_apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_9a2ca522ff49991c_mb2_35_7_13_32_44_42_target_priority_worker/results.csv",
    "worker_event_count": 7,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "9a2ca522ff49991c",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -114.832405,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_9a2ca522ff49991c_mb3_35_7_13_32_31_42",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->35:low_risk:2",
      "35->7:low_time:0",
      "7->13:low_risk:2",
      "13->32:low_risk:2",
      "32->31:low_risk:2",
      "31->42:low_time:0",
      "42->0:low_risk:1"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      35,
      7,
      13,
      32,
      31,
      42
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/task050_apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_9a2ca522ff49991c_mb3_35_7_13_32_31_42_target_priority_worker/results.csv",
    "worker_event_count": 8,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "39e3a497e73941e5",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_39e3a497e73941e5_mb1_11_1_26_34",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_context_not_reached",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->1:low_risk:2",
      "1->26:low_risk:2",
      "26->34:low_time:0",
      "34->0:low_risk:2"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      11,
      1,
      26,
      34
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/task050_apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_39e3a497e73941e5_mb1_11_1_26_34_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "39e3a497e73941e5",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_39e3a497e73941e5_mb2_11_1_49_15_44_42",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_context_not_reached",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->1:low_energy:1",
      "1->49:low_time:0",
      "49->15:low_time:0",
      "15->44:low_risk:2",
      "44->42:low_time:0",
      "42->0:low_risk:1"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      11,
      1,
      49,
      15,
      44,
      42
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/task050_apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_39e3a497e73941e5_mb2_11_1_49_15_44_42_target_priority_worker/results.csv",
    "worker_event_count": 7,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "39e3a497e73941e5",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_39e3a497e73941e5_mb3_11_1_26_15_44_42",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_context_not_reached",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->1:low_risk:2",
      "1->26:low_risk:2",
      "26->15:low_risk:1",
      "15->44:low_risk:2",
      "44->42:low_time:0",
      "42->0:low_risk:1"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      11,
      1,
      26,
      15,
      44,
      42
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/task050_apollo15_20km_random_wave_randomtw_tasks050_01_seed91000_39e3a497e73941e5_mb3_11_1_26_15_44_42_target_priority_worker/results.csv",
    "worker_event_count": 4,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb1_1_18_target_priority_worker/results.csv",
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
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb2_16_5_12_10_target_priority_worker/results.csv",
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
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb3_16_3_2_10_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
