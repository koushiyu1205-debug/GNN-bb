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
  "worker_stage_policy": "match_capture_pricing_kind: heuristic_before_heuristic_exact_before_exact"
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "b1fe302aa48c7199",
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "01430159f79364bf",
    "forbidden_signature_hash": "1e8f50212b934096",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19",
    "pool_signature_hash": "cf68162cf5eef019",
    "pool_task_set_hash": "ae376218ed07f20c",
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->10:low_risk:1",
      "10->13:low_risk:1",
      "13->0:low_risk:1"
    ],
    "target_priority_sequence": [
      3,
      10,
      13
    ],
    "target_sequence": [
      3,
      10,
      13,
      7,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->10:low_risk:1",
          "10->13:low_risk:1",
          "13->0:low_risk:1"
        ],
        "sequence": [
          3,
          10,
          13
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->19:low_risk:2",
          "19->0:low_risk:2"
        ],
        "sequence": [
          7,
          19
        ],
        "start_time": 183.681584
      }
    ],
    "true_dual_hash": "38c994daf858e397",
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "240ab10c01bd8a48",
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f567a0928007db23",
    "forbidden_signature_hash": "77884aa39a1dfb7d",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5",
    "pool_signature_hash": "144ee34f7c1f59b7",
    "pool_task_set_hash": "e27862a3103c1271",
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->0:low_time:0"
    ],
    "target_priority_sequence": [
      14
    ],
    "target_sequence": [
      14,
      19,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->0:low_time:0"
        ],
        "sequence": [
          14
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->19:low_time:0",
          "19->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          19,
          5
        ],
        "start_time": 321.763501
      }
    ],
    "true_dual_hash": "fc035d8cb1f6391c",
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "c17edfb3cd7e8f05",
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "5c5a1e3be100b071",
    "forbidden_signature_hash": "7f16fa898ec6e3de",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2",
    "pool_signature_hash": "04491760c95bd205",
    "pool_task_set_hash": "077a54edb21e05a0",
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->20:low_risk:2",
      "20->2:low_time:0",
      "2->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      20,
      2
    ],
    "target_sequence": [
      12,
      20,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_time:0",
          "12->20:low_risk:2",
          "20->2:low_time:0",
          "2->0:low_time:0"
        ],
        "sequence": [
          12,
          20,
          2
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "298fa8febac5d588",
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "50cbc705fc1c3f51",
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "084e39c1f4a0fc67",
    "forbidden_signature_hash": "1457bbff72e453e7",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4",
    "pool_signature_hash": "06b9feca08f44d3e",
    "pool_task_set_hash": "ba608ad516987f86",
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->20:low_time:0",
      "20->0:low_energy:1"
    ],
    "target_priority_sequence": [
      1,
      20
    ],
    "target_sequence": [
      1,
      20,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->20:low_time:0",
          "20->0:low_energy:1"
        ],
        "sequence": [
          1,
          20
        ],
        "start_time": 5.625629
      },
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->0:low_risk:2"
        ],
        "sequence": [
          4
        ],
        "start_time": 347.780164
      }
    ],
    "true_dual_hash": "9f6795835e8726fd",
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=01430159f79364bf --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,10,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,10,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,10,13,7,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:2","3->10:low_risk:1","10->13:low_risk:1","13->0:low_risk:1"],"sequence":[3,10,13],"start_time":0.0},{"arc_option_sequence":["0->7:low_risk:2","7->19:low_risk:2","19->0:low_risk:2"],"sequence":[7,19],"start_time":183.681584}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:2,3->10:low_risk:1,10->13:low_risk:1,13->0:low_risk:1'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f567a0928007db23 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=14,19,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->14:low_risk:2","14->0:low_time:0"],"sequence":[14],"start_time":0.0},{"arc_option_sequence":["0->19:low_time:0","19->5:low_risk:2","5->0:low_risk:2"],"sequence":[19,5],"start_time":321.763501}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->14:low_risk:2,14->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=5c5a1e3be100b071 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,20,2 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,20,2 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,20,2 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_time:0","12->20:low_risk:2","20->2:low_time:0","2->0:low_time:0"],"sequence":[12,20,2],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_time:0,12->20:low_risk:2,20->2:low_time:0,2->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=084e39c1f4a0fc67 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,20,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_risk:2","1->20:low_time:0","20->0:low_energy:1"],"sequence":[1,20],"start_time":5.625629},{"arc_option_sequence":["0->4:low_risk:2","4->0:low_risk:2"],"sequence":[4],"start_time":347.780164}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_risk:2,1->20:low_time:0,20->0:low_energy:1'
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
