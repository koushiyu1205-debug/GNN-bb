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
    "active_hash_before": "0ac8cb9a6ab0732f",
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "35a4908dfecb7ff3",
    "forbidden_signature_hash": "48df1e7f52f569ad",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13",
    "pool_signature_hash": "e4bd17f60af80372",
    "pool_task_set_hash": "4a147e30b41d2b25",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->18:low_time:0",
      "18->10:low_risk:1",
      "10->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      18,
      10
    ],
    "target_sequence": [
      5,
      18,
      10,
      8,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->18:low_time:0",
          "18->10:low_risk:1",
          "10->0:low_risk:2"
        ],
        "sequence": [
          5,
          18,
          10
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->13:low_time:0",
          "13->0:low_time:0"
        ],
        "sequence": [
          8,
          13
        ],
        "start_time": 230.776211
      }
    ],
    "true_dual_hash": "3a4993d175b27e81",
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "6da932b87f5dccf6",
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7fc1de982db572be",
    "forbidden_signature_hash": "45633cd412e425ae",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13",
    "pool_signature_hash": "1bd6802adf3e1260",
    "pool_task_set_hash": "98633eab2bb25abc",
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->10:low_risk:1",
      "10->0:low_time:0"
    ],
    "target_priority_sequence": [
      18,
      10
    ],
    "target_sequence": [
      18,
      10,
      12,
      4,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->10:low_risk:1",
          "10->0:low_time:0"
        ],
        "sequence": [
          18,
          10
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->4:low_time:0",
          "4->13:low_time:0",
          "13->0:low_time:0"
        ],
        "sequence": [
          12,
          4,
          13
        ],
        "start_time": 205.925
      }
    ],
    "true_dual_hash": "028c4f12cfc5d246",
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "64565b767ae27294",
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "8f2fd95e2f03ec41",
    "forbidden_signature_hash": "ca614602b523bed0",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13",
    "pool_signature_hash": "7154afaa8d60e43b",
    "pool_task_set_hash": "794efea398562cf5",
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->7:low_energy:1",
      "7->20:low_energy:1",
      "20->1:low_risk:2",
      "1->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      7,
      20,
      1,
      5
    ],
    "target_sequence": [
      12,
      7,
      20,
      1,
      5,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_time:0",
          "12->7:low_energy:1",
          "7->20:low_energy:1",
          "20->1:low_risk:2",
          "1->5:low_time:0",
          "5->0:low_time:0"
        ],
        "sequence": [
          12,
          7,
          20,
          1,
          5
        ],
        "start_time": 5.657341
      },
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          13
        ],
        "start_time": 380.267365
      }
    ],
    "true_dual_hash": "7fcbacf6b50a27c1",
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "b54cdb488e305b84",
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1625c1776efc58ed",
    "forbidden_signature_hash": "4bcc9f644e25d5f6",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4",
    "pool_signature_hash": "e0dbc1428ea1e199",
    "pool_task_set_hash": "8fc2386d5b9953d0",
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->7:low_risk:2",
      "7->2:low_risk:2",
      "2->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      7,
      2,
      1
    ],
    "target_sequence": [
      12,
      7,
      2,
      1,
      10,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->7:low_risk:2",
          "7->2:low_risk:2",
          "2->1:low_time:0",
          "1->0:low_time:0"
        ],
        "sequence": [
          12,
          7,
          2,
          1
        ],
        "start_time": 2.442032
      },
      {
        "arc_option_sequence": [
          "0->10:low_risk:2",
          "10->4:low_risk:2",
          "4->0:low_time:0"
        ],
        "sequence": [
          10,
          4
        ],
        "start_time": 271.464168
      }
    ],
    "true_dual_hash": "557fc046535ce949",
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "0f4ee9690f1be103",
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "355f0684d6e275df",
    "forbidden_signature_hash": "a990efc5c6f5079d",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8",
    "pool_signature_hash": "6fc63885d9fbe83a",
    "pool_task_set_hash": "049dfdeed1ba1c65",
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->17:low_time:0",
      "17->3:low_time:0",
      "3->9:low_time:0",
      "9->4:low_risk:2",
      "4->8:low_time:0",
      "8->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      17,
      3,
      9,
      4,
      8
    ],
    "target_sequence": [
      5,
      17,
      3,
      9,
      4,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_time:0",
          "5->17:low_time:0",
          "17->3:low_time:0",
          "3->9:low_time:0",
          "9->4:low_risk:2",
          "4->8:low_time:0",
          "8->0:low_risk:2"
        ],
        "sequence": [
          5,
          17,
          3,
          9,
          4,
          8
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "7b6d2d271131e625",
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "6fa088e9e57884fa",
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "aa78e15d40fb733a",
    "forbidden_signature_hash": "93c04417d6d57313",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13",
    "pool_signature_hash": "e098d90ada71328e",
    "pool_task_set_hash": "ab27bb28c49107d8",
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->9:low_risk:1",
      "9->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      9
    ],
    "target_sequence": [
      20,
      9,
      1,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->9:low_risk:1",
          "9->0:low_risk:2"
        ],
        "sequence": [
          20,
          9
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          1,
          13
        ],
        "start_time": 240.769033
      }
    ],
    "true_dual_hash": "e26da6b86e78bf95",
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=35a4908dfecb7ff3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,18,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,18,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,18,10,8,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->18:low_time:0","18->10:low_risk:1","10->0:low_risk:2"],"sequence":[5,18,10],"start_time":0.0},{"arc_option_sequence":["0->8:low_time:0","8->13:low_time:0","13->0:low_time:0"],"sequence":[8,13],"start_time":230.776211}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->18:low_time:0,18->10:low_risk:1,10->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7fc1de982db572be --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,10,12,4,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_risk:2","18->10:low_risk:1","10->0:low_time:0"],"sequence":[18,10],"start_time":0.0},{"arc_option_sequence":["0->12:low_risk:2","12->4:low_time:0","4->13:low_time:0","13->0:low_time:0"],"sequence":[12,4,13],"start_time":205.925}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_risk:2,18->10:low_risk:1,10->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=8f2fd95e2f03ec41 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,7,20,1,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,7,20,1,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,7,20,1,5,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_time:0","12->7:low_energy:1","7->20:low_energy:1","20->1:low_risk:2","1->5:low_time:0","5->0:low_time:0"],"sequence":[12,7,20,1,5],"start_time":5.657341},{"arc_option_sequence":["0->13:low_risk:2","13->0:low_risk:2"],"sequence":[13],"start_time":380.267365}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_time:0,12->7:low_energy:1,7->20:low_energy:1,20->1:low_risk:2,1->5:low_time:0,5->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1625c1776efc58ed --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,7,2,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,7,2,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,7,2,1,10,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->7:low_risk:2","7->2:low_risk:2","2->1:low_time:0","1->0:low_time:0"],"sequence":[12,7,2,1],"start_time":2.442032},{"arc_option_sequence":["0->10:low_risk:2","10->4:low_risk:2","4->0:low_time:0"],"sequence":[10,4],"start_time":271.464168}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->7:low_risk:2,7->2:low_risk:2,2->1:low_time:0,1->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=355f0684d6e275df --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,17,3,9,4,8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,17,3,9,4,8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,17,3,9,4,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_time:0","5->17:low_time:0","17->3:low_time:0","3->9:low_time:0","9->4:low_risk:2","4->8:low_time:0","8->0:low_risk:2"],"sequence":[5,17,3,9,4,8],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_time:0,5->17:low_time:0,17->3:low_time:0,3->9:low_time:0,9->4:low_risk:2,4->8:low_time:0,8->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=aa78e15d40fb733a --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,9 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,9 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,9,1,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_risk:2","20->9:low_risk:1","9->0:low_risk:2"],"sequence":[20,9],"start_time":0.0},{"arc_option_sequence":["0->1:low_time:0","1->13:low_risk:2","13->0:low_risk:2"],"sequence":[1,13],"start_time":240.769033}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_risk:2,20->9:low_risk:1,9->0:low_risk:2'
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
