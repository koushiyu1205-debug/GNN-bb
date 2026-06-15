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
    "active_hash_before": "e1535956c7327c06",
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "8bd56cf157d96aaa",
    "forbidden_signature_hash": "b11ad784e4d9b8ad",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17",
    "pool_signature_hash": "4b1efffc50b093b8",
    "pool_task_set_hash": "78be6d3096f0bebc",
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->20:low_time:0",
      "20->0:low_risk:2"
    ],
    "target_priority_sequence": [
      18,
      20
    ],
    "target_sequence": [
      18,
      20,
      11,
      1,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->20:low_time:0",
          "20->0:low_risk:2"
        ],
        "sequence": [
          18,
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_time:0",
          "11->1:low_risk:2",
          "1->17:low_time:0",
          "17->0:low_risk:2"
        ],
        "sequence": [
          11,
          1,
          17
        ],
        "start_time": 311.371814
      }
    ],
    "true_dual_hash": "a4ab03fce831d8ea",
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d8bc25ab3f9d6059",
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "085044441345625f",
    "forbidden_signature_hash": "ee30d90fc043689a",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13",
    "pool_signature_hash": "45513774a0ae7878",
    "pool_task_set_hash": "20f4ecb4e6bc9940",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      20
    ],
    "target_sequence": [
      20,
      14,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->0:low_time:0"
        ],
        "sequence": [
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->14:low_time:0",
          "14->13:low_energy:1",
          "13->0:low_risk:2"
        ],
        "sequence": [
          14,
          13
        ],
        "start_time": 219.549576
      }
    ],
    "true_dual_hash": "69a06490e6d33f0a",
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "fd7b8679a13a6916",
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "5704f305b764baf5",
    "forbidden_signature_hash": "22f877170957b6e0",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14",
    "pool_signature_hash": "9fd0f95b373f47ee",
    "pool_task_set_hash": "b8c2d8232b3a9b91",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_risk:2",
      "1->14:low_risk:2",
      "14->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      1,
      14
    ],
    "target_sequence": [
      20,
      1,
      14
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->1:low_risk:2",
          "1->14:low_risk:2",
          "14->0:low_risk:2"
        ],
        "sequence": [
          20,
          1,
          14
        ],
        "start_time": 59.772234
      }
    ],
    "true_dual_hash": "04921fa8ad0ea3eb",
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "babec0b5f6278322",
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "9d086dc2401550f2",
    "forbidden_signature_hash": "0bb292e2e0752c83",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11",
    "pool_signature_hash": "83720a2c2717ed75",
    "pool_task_set_hash": "517d8ceba5bd2cdf",
    "target_arc_option_sequence": [
      "0->9:low_time:0",
      "9->3:low_risk:2",
      "3->10:low_risk:2",
      "10->11:low_risk:1",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      9,
      3,
      10,
      11
    ],
    "target_sequence": [
      9,
      3,
      10,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->9:low_time:0",
          "9->3:low_risk:2",
          "3->10:low_risk:2",
          "10->11:low_risk:1",
          "11->0:low_risk:2"
        ],
        "sequence": [
          9,
          3,
          10,
          11
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "ed5910cf8e784664",
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "babec0b5f6278322",
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "6465dff938f298e1",
    "forbidden_signature_hash": "cd24a39bd4bdf643",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12",
    "pool_signature_hash": "ef439d6871f213be",
    "pool_task_set_hash": "e8ac357bc6320fb9",
    "target_arc_option_sequence": [
      "0->9:low_time:0",
      "9->1:low_risk:2",
      "1->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_priority_sequence": [
      9,
      1,
      12
    ],
    "target_sequence": [
      9,
      1,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->9:low_time:0",
          "9->1:low_risk:2",
          "1->12:low_risk:2",
          "12->0:low_time:0"
        ],
        "sequence": [
          9,
          1,
          12
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "8464843cc4f47601",
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "89b3dde8ac4795c8",
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "eb76f8c2c929ecb9",
    "forbidden_signature_hash": "c0312d580e1e5b6f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5",
    "pool_signature_hash": "5d9b5234e5c0a811",
    "pool_task_set_hash": "3e55bac6cc95c651",
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->0:low_risk:2"
    ],
    "target_priority_sequence": [
      7
    ],
    "target_sequence": [
      7,
      4,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_time:0",
          "7->0:low_risk:2"
        ],
        "sequence": [
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          4,
          5
        ],
        "start_time": 221.231704
      }
    ],
    "true_dual_hash": "6ba1197719383628",
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=8bd56cf157d96aaa --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,20,11,1,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_risk:2","18->20:low_time:0","20->0:low_risk:2"],"sequence":[18,20],"start_time":0.0},{"arc_option_sequence":["0->11:low_time:0","11->1:low_risk:2","1->17:low_time:0","17->0:low_risk:2"],"sequence":[11,1,17],"start_time":311.371814}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_risk:2,18->20:low_time:0,20->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=085044441345625f --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,14,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->0:low_time:0"],"sequence":[20],"start_time":0.0},{"arc_option_sequence":["0->14:low_time:0","14->13:low_energy:1","13->0:low_risk:2"],"sequence":[14,13],"start_time":219.549576}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=5704f305b764baf5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,1,14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,1,14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,1,14 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->1:low_risk:2","1->14:low_risk:2","14->0:low_risk:2"],"sequence":[20,1,14],"start_time":59.772234}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->1:low_risk:2,1->14:low_risk:2,14->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=9d086dc2401550f2 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=9,3,10,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=9,3,10,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=9,3,10,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->9:low_time:0","9->3:low_risk:2","3->10:low_risk:2","10->11:low_risk:1","11->0:low_risk:2"],"sequence":[9,3,10,11],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->9:low_time:0,9->3:low_risk:2,3->10:low_risk:2,10->11:low_risk:1,11->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=6465dff938f298e1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=9,1,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=9,1,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=9,1,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->9:low_time:0","9->1:low_risk:2","1->12:low_risk:2","12->0:low_time:0"],"sequence":[9,1,12],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->9:low_time:0,9->1:low_risk:2,1->12:low_risk:2,12->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=eb76f8c2c929ecb9 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,4,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_time:0","7->0:low_risk:2"],"sequence":[7],"start_time":0.0},{"arc_option_sequence":["0->4:low_risk:2","4->5:low_risk:2","5->0:low_risk:2"],"sequence":[4,5],"start_time":221.231704}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_time:0,7->0:low_risk:2'
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
