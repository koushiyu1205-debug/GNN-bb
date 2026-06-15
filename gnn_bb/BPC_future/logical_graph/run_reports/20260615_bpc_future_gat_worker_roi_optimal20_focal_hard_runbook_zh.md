# GAT Worker ROI Solver A/B Runbook 报告

日期：2026-06-15

## 目的

生成下一轮 solver A/B 命令：5/10 只做 no-regression sentinel，20 只对
worker-ROI GAT + kNN/OOD 筛出的候选做显式 opt-in
worker A/B。该脚本不运行求解器。

## 机器字段

```text
gat_worker_roi_solver_ab_runbook = current
status = ready
runs_bpc_or_pricing = false
candidate_count = 1
decision_split = validation
decision_name = HIGH_PRIORITY
positive_label_only = false
excluded_candidate_key_count = 0
exclude_candidate_jsonl_count = 0
max_workers = 2
production_ready = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## Candidate Policy

```json
{
  "certificate_effect": false,
  "context_policy": "expected_context_hash_plus_recovered_capture_context",
  "gat_role": "trajectory_roi_embedding_and_impact_expression",
  "knn_ood_role": "safety_shell",
  "negative_discard_allowed": false,
  "safe_negative_action": "HIGH_PRIORITY",
  "unsafe_negative_action": "DELAY_QUEUE"
}
```

## Source OOD Metrics

```json
{
  "accuracy": 0.6226415094339622,
  "add_precision": 0.38461538461538464,
  "add_recall": 0.29411764705882354,
  "false_high_priority_rate": 0.2222222222222222,
  "false_negative_delay_queue": 12,
  "false_positive_high_priority": 8,
  "predicted_delay_queue": 40,
  "predicted_high_priority": 13,
  "total": 53,
  "true_negative_delay_queue": 28,
  "true_positive_high_priority": 5
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "1133f10e1dec4a72",
    "baseline_csv": "BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json|55a386bc49af1dda|16,4,14,11,13|0->16:low_risk:1,16->4:low_risk:2,4->14:low_risk:2,14->0:low_time:0",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "55a386bc49af1dda",
    "forbidden_signature_hash": "830e5e0aafedc418",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13",
    "pool_signature_hash": "32a3eaef6f86a137",
    "pool_task_set_hash": "f89e87b38c566d31",
    "roi_class": "no_observed_roi",
    "source_decision_split": "validation",
    "source_row_index": 69,
    "target_arc_option_sequence": [
      "0->16:low_risk:1",
      "16->4:low_risk:2",
      "4->14:low_risk:2",
      "14->0:low_time:0"
    ],
    "target_priority_sequence": [
      16,
      4,
      14,
      11,
      13
    ],
    "target_sequence": [
      16,
      4,
      14,
      11,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_risk:1",
          "16->4:low_risk:2",
          "4->14:low_risk:2",
          "14->0:low_time:0"
        ],
        "sequence": [
          16,
          4,
          14
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_time:0",
          "11->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          11,
          13
        ],
        "start_time": 334.703426
      }
    ],
    "true_dual_hash": "9613ffbee36ea5a6",
    "worker_csv": "BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.6094081401824951
  }
]
```

## Commands

### task005_mainline_no_regression_no_new_worker

Run task-5 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 2 --results-csv BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task005_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task005_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task005_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task005_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_no_new_worker

Run task-10 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 2 --results-csv BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task010_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task010_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task010_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task010_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json --time-limit 1800.000000 --results-csv BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json --time-limit 1800.000000 --results-csv BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=55a386bc49af1dda --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16,4,14,11,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16,4,14,11,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,4,14,11,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_risk:1","16->4:low_risk:2","4->14:low_risk:2","14->0:low_time:0"],"sequence":[16,4,14],"start_time":0.0},{"arc_option_sequence":["0->11:low_time:0","11->13:low_risk:2","13->0:low_risk:2"],"sequence":[11,13],"start_time":334.703426}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_risk:1,16->4:low_risk:2,4->14:low_risk:2,14->0:low_time:0'
```

### audit_worker_roi_solver_ab_results

Read result CSVs after the solver commands finish.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_worker_roi_solver_ab_results.py --runbook-summary BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/summary.json --output-dir BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/ab_audit --report BPC_future/results/gat_worker_roi_optimal20_focal_hard_frac0p5_20260615/ab_audit_zh.md
```

## 边界

- 该 runbook 不是生产开关；
- 5/10 命令不启用新的 hidden-negative worker；
- 20 worker 命令必须显式 opt-in；
- 所有命令都不启用 sharded Pulse certificate 或 official-bound shortcut；
- 未通过安全壳的 true-RC negative 只能延迟，不能永久丢弃。
