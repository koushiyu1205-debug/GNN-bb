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
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -31.9356514,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      16,
      17,
      15
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -26.5430824,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      4,
      19,
      10,
      17
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -21.7182942,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      4,
      10,
      17,
      7
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "79fde658840fe2b8",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -29.939646,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      1,
      15,
      17
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "79fde658840fe2b8",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -20.0283435,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      12,
      4,
      13,
      5
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "79fde658840fe2b8",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -14.7797715,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      12,
      4,
      19,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "45baa40751a0bf77",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -13.436328,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb1_2_19_14",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      2,
      19,
      14
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb1_2_19_14_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "45baa40751a0bf77",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -8.283218,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb2_1_3_19_15_12",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      1,
      3,
      19,
      15,
      12
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb2_1_3_19_15_12_target_priority_worker/results.csv",
    "worker_event_count": 5,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "45baa40751a0bf77",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -3.198547,
    "first_executed_returned_journeys": 1,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb3_2_14",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->0:low_risk:2"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      2,
      14
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb3_2_14_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
