# GAT Target-Priority Worker A/B Runbook

日期：2026-06-14

## 目的

生成下一轮 5/10 no-regression 与 20-task ROI A/B 命令。GAT 仍只负责 embedding / trajectory impact 表达，kNN/OOD 只做安全壳；通过安全壳的 true-RC negative 可优先进入 worker target，不通过的负列进入 DELAY_QUEUE，不能永久丢弃，也不能参与 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_runbook = current
status = ready
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
required_candidate_context_field_count = 8
all_checks_pass = true
```

## Candidate Policy

```json
{
  "certificate_effect": false,
  "context_miss_policy": "capture_actual_reached_contexts_for_next_iteration",
  "gat_role": "embedding_and_trajectory_impact_expression",
  "knn_ood_role": "safety_shell",
  "negative_discard_allowed": false,
  "safe_negative_action": "HIGH_PRIORITY",
  "unsafe_negative_action": "DELAY_QUEUE",
  "worker_stage_policy": "match_capture_pricing_kind"
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "f5e56fbba74784b5",
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7e0afd09753effed",
    "forbidden_signature_hash": "4a0466dbb3cb0ca3",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19",
    "pool_signature_hash": "5b033e33a1d57de2",
    "pool_task_set_hash": "07344d8ff99d9697",
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_sequence": [
      19
    ],
    "true_dual_hash": "4fb2dc95e30f31c4",
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d2c0edfced5cf1b3",
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "a3b5b5263e1cfe17",
    "forbidden_signature_hash": "d16be31402958c8c",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12",
    "pool_signature_hash": "5e8d064add26e945",
    "pool_task_set_hash": "6be049fce559e341",
    "target_arc_option_sequence": [
      "0->14:low_time:0",
      "14->5:low_risk:2",
      "5->8:low_time:0",
      "8->18:low_risk:2",
      "18->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      14,
      5,
      8,
      18,
      12
    ],
    "true_dual_hash": "4e721d29d378a125",
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "17dadbafe771952e",
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "de2c1d84615d5c71",
    "forbidden_signature_hash": "c4a62ea4289cbf19",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9",
    "pool_signature_hash": "da66c890f9d81836",
    "pool_task_set_hash": "32ed53d0ecd64c89",
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->6:low_risk:2",
      "6->1:low_risk:2",
      "1->20:low_time:0",
      "20->9:low_risk:2",
      "9->0:low_risk:2"
    ],
    "target_sequence": [
      14,
      6,
      1,
      20,
      9
    ],
    "true_dual_hash": "8efb3de0a4ceb57e",
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d2cd6edbbb0e19a5",
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "157f03afc868de3b",
    "forbidden_signature_hash": "43b8d182947831ab",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13",
    "pool_signature_hash": "3923d333f2eb61a4",
    "pool_task_set_hash": "241d3df353c8eab4",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_sequence": [
      13
    ],
    "true_dual_hash": "7595051f6357ad9a",
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7e0afd09753effed --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=19 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=19 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=19 --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->19:low_risk:2,19->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=a3b5b5263e1cfe17 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=14,5,8,18,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=14,5,8,18,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=14,5,8,18,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->14:low_time:0,14->5:low_risk:2,5->8:low_time:0,8->18:low_risk:2,18->12:low_risk:2,12->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=de2c1d84615d5c71 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=14,6,1,20,9 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=14,6,1,20,9 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=14,6,1,20,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->14:low_risk:2,14->6:low_risk:2,6->1:low_risk:2,1->20:low_time:0,20->9:low_risk:2,9->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=157f03afc868de3b --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13 --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->0:low_risk:2'
```

## 边界

- 5/10 命令不关闭主线 GAT/learning，也不启用新 worker；
- 20 baseline/worker 命令也不关闭主线 GAT/learning，避免候选捕获上下文无法复现；
- 20 baseline/worker 命令开启 counterfactual replay capture；如果旧 target context 没到，仍保留实际到达的 context 供下一轮候选抽取；
- 20 worker 命令是显式 opt-in，只验证 target-priority ROI；
- 20 worker 候选必须带完整 context / dual / cuts / branch / pool hash；
- 所有命令都不启用 sharded Pulse certificate 或 official lower-bound effect；
- 含 `->` 的 arc-option 配置通过 `shlex.join` 自动引用，不能手工去掉引号；
- 该 runbook 不是生产开关，跑完后仍需看 5/10 no-regression 和 20-task ROI。
