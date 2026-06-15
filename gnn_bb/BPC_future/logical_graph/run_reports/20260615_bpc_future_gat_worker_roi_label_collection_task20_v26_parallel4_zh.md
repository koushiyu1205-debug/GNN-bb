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
    "active_hash_before": "88710450380fcec7",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "49e19467900df88b",
    "forbidden_signature_hash": "8263bc8e7d9cdb44",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3",
    "pool_signature_hash": "dfd65843623308c7",
    "pool_task_set_hash": "bc45cb9be133d81b",
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->11:low_risk:2",
      "11->5:low_risk:2",
      "5->10:low_risk:2",
      "10->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_priority_sequence": [
      19,
      11,
      5,
      10,
      3
    ],
    "target_sequence": [
      19,
      11,
      5,
      10,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->19:low_time:0",
          "19->11:low_risk:2",
          "11->5:low_risk:2",
          "5->10:low_risk:2",
          "10->3:low_risk:2",
          "3->0:low_risk:2"
        ],
        "sequence": [
          19,
          11,
          5,
          10,
          3
        ],
        "start_time": 41.651373
      }
    ],
    "true_dual_hash": "f483ab39edaf3da6",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d0a64df1d2837625",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "6190d8b37f2491c2",
    "forbidden_signature_hash": "914a244f8ac530e8",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3",
    "pool_signature_hash": "257adc1d45993739",
    "pool_task_set_hash": "4b4047afaabd4300",
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->17:low_risk:2",
      "17->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4,
      17,
      3
    ],
    "target_sequence": [
      4,
      17,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->17:low_risk:2",
          "17->3:low_risk:2",
          "3->0:low_risk:2"
        ],
        "sequence": [
          4,
          17,
          3
        ],
        "start_time": 74.514535
      }
    ],
    "true_dual_hash": "27d9f9f9f2ac4246",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "80911d6fa2d0d8a3",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "9a11128d9256c3d8",
    "forbidden_signature_hash": "990b457f64d5a029",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5",
    "pool_signature_hash": "159a41dc4d28445e",
    "pool_task_set_hash": "805affa8fb6d6023",
    "target_arc_option_sequence": [
      "0->13:low_time:0",
      "13->4:low_risk:1",
      "4->16:low_risk:2",
      "16->5:low_time:0",
      "5->0:low_risk:2"
    ],
    "target_priority_sequence": [
      13,
      4,
      16,
      5
    ],
    "target_sequence": [
      13,
      4,
      16,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_time:0",
          "13->4:low_risk:1",
          "4->16:low_risk:2",
          "16->5:low_time:0",
          "5->0:low_risk:2"
        ],
        "sequence": [
          13,
          4,
          16,
          5
        ],
        "start_time": 33.752437
      }
    ],
    "true_dual_hash": "d4309c64cc074461",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "6d195b76f7f8f9f3",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b6675887fb63db55",
    "forbidden_signature_hash": "992d8826f5336140",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2",
    "pool_signature_hash": "85d235ca5fd12b83",
    "pool_task_set_hash": "726d51139030b3b7",
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      1
    ],
    "target_sequence": [
      1,
      9,
      5,
      14,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          1
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->9:low_risk:2",
          "9->5:low_risk:1",
          "5->14:low_time:0",
          "14->2:low_time:0",
          "2->0:low_risk:2"
        ],
        "sequence": [
          9,
          5,
          14,
          2
        ],
        "start_time": 296.968121
      }
    ],
    "true_dual_hash": "a90b95aea6dfa372",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "0fb3834f18a343f8",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "dbddb0163ebb7fd4",
    "forbidden_signature_hash": "42038b50bd4b1d96",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7",
    "pool_signature_hash": "669f4212cdf48ca6",
    "pool_task_set_hash": "55f8534476b1f9b2",
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->0:low_time:0"
    ],
    "target_priority_sequence": [
      6
    ],
    "target_sequence": [
      6,
      18,
      3,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_time:0",
          "6->0:low_time:0"
        ],
        "sequence": [
          6
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_energy:1",
          "18->3:low_time:0",
          "3->7:low_risk:2",
          "7->0:low_time:0"
        ],
        "sequence": [
          18,
          3,
          7
        ],
        "start_time": 274.532668
      }
    ],
    "true_dual_hash": "b27b0b3498c9bc86",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=49e19467900df88b --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=19,11,5,10,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=19,11,5,10,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=19,11,5,10,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->19:low_time:0","19->11:low_risk:2","11->5:low_risk:2","5->10:low_risk:2","10->3:low_risk:2","3->0:low_risk:2"],"sequence":[19,11,5,10,3],"start_time":41.651373}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->19:low_time:0,19->11:low_risk:2,11->5:low_risk:2,5->10:low_risk:2,10->3:low_risk:2,3->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=6190d8b37f2491c2 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,17,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,17,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,17,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->17:low_risk:2","17->3:low_risk:2","3->0:low_risk:2"],"sequence":[4,17,3],"start_time":74.514535}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->17:low_risk:2,17->3:low_risk:2,3->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=9a11128d9256c3d8 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,4,16,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,4,16,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,4,16,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_time:0","13->4:low_risk:1","4->16:low_risk:2","16->5:low_time:0","5->0:low_risk:2"],"sequence":[13,4,16,5],"start_time":33.752437}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_time:0,13->4:low_risk:1,4->16:low_risk:2,16->5:low_time:0,5->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b6675887fb63db55 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,9,5,14,2 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_risk:2","1->0:low_risk:2"],"sequence":[1],"start_time":0.0},{"arc_option_sequence":["0->9:low_risk:2","9->5:low_risk:1","5->14:low_time:0","14->2:low_time:0","2->0:low_risk:2"],"sequence":[9,5,14,2],"start_time":296.968121}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_risk:2,1->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=dbddb0163ebb7fd4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,18,3,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_time:0","6->0:low_time:0"],"sequence":[6],"start_time":0.0},{"arc_option_sequence":["0->18:low_energy:1","18->3:low_time:0","3->7:low_risk:2","7->0:low_time:0"],"sequence":[18,3,7],"start_time":274.532668}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_time:0,6->0:low_time:0'
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
