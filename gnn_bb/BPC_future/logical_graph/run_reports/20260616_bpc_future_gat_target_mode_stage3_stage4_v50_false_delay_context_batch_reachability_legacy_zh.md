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
record_count = 5
reachable_target_intervention_count = 4
reachability_class_counts = {'target_intervention_reachable': 4, 'worker_context_not_reached': 1}
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
    "expected_context_hash": "ac056820151e9ad7",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -25.4432665,
    "first_executed_returned_journeys": 3,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_batch3",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      20,
      16,
      15,
      5,
      16,
      7,
      3,
      15,
      20
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_batch3_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "b6d808ebac2a6dd8",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -41.3185275,
    "first_executed_returned_journeys": 3,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "learning_policy_kept": true,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_batch3",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "target_intervention_reachable",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->19:low_risk:2",
      "19->0:low_time:0"
    ],
    "target_causal_match_count": 1,
    "target_sequence": [
      16,
      19,
      1,
      2,
      8,
      5,
      19
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_batch3_target_priority_worker/results.csv",
    "worker_event_count": 5,
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
    "first_executed_returned_journeys": 3,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_batch3",
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
      17,
      12,
      4,
      13,
      5,
      12,
      4,
      19,
      13
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_batch3_target_priority_worker/results.csv",
    "worker_event_count": 4,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "expected_context_worker_event_count": 1,
    "first_executed_best_rc": -31.9356514,
    "first_executed_returned_journeys": 3,
    "first_executed_status": "FOUND_NEGATIVE",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_batch3",
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
      15,
      4,
      19,
      10,
      17,
      4,
      10,
      17,
      7
    ],
    "training_label_allowed": true,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_batch3_target_priority_worker/results.csv",
    "worker_event_count": 6,
    "worker_log_count": 1
  },
  {
    "capture_pricing_kind": "exact",
    "certificate_effect": false,
    "diagnostic_only": true,
    "expected_context_executed_event_count": 0,
    "expected_context_hash": "7b430465c7ae76b3",
    "expected_context_worker_event_count": 0,
    "first_executed_best_rc": null,
    "first_executed_returned_journeys": 0,
    "first_executed_status": "",
    "first_expected_context_skip_reason": "",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "learning_policy_kept": true,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_batch3",
    "no_certificate_effect": true,
    "official_bound_effect": false,
    "reachability_class": "worker_context_not_reached",
    "runs_bpc_or_pricing": false,
    "schema_version": "gat_target_intervention_reachability_record_v1",
    "stage_compatible": true,
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->1:low_risk:2",
      "1->0:low_energy:1"
    ],
    "target_causal_match_count": 0,
    "target_sequence": [
      5,
      1,
      15,
      17,
      19,
      9,
      1,
      9
    ],
    "training_label_allowed": false,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_batch3_target_priority_worker/results.csv",
    "worker_event_count": 3,
    "worker_log_count": 1
  }
]
```

## 下一步

collect_reachable_target_roi_labels
