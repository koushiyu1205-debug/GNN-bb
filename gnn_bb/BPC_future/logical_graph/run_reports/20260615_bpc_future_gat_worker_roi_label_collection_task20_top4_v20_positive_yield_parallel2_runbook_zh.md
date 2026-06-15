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
    "active_hash_before": "3c1f1334f5a3a2bc",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 7,
    "cell_positive_rate": 0.636364,
    "cell_training_negative_count": 4,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d8b85dff55093cb1",
    "forbidden_signature_hash": "49b6ee68adb7494e",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|5",
    "pool_signature_hash": "68e19f6eafe316a7",
    "pool_task_set_hash": "5d7b3c3440e0a8ae",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 9.5588,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->6:low_time:0",
      "6->20:low_risk:1",
      "20->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4,
      6,
      20
    ],
    "target_sequence": [
      4,
      6,
      20,
      3,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->6:low_time:0",
          "6->20:low_risk:1",
          "20->0:low_risk:2"
        ],
        "sequence": [
          4,
          6,
          20
        ],
        "start_time": 4.4203
      },
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          3,
          7
        ],
        "start_time": 326.708516
      }
    ],
    "true_dual_hash": "d3c94df3fc13c59d",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3e8f3aed71837bf4",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 7,
    "cell_positive_rate": 0.636364,
    "cell_training_negative_count": 4,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ddb0ce64af10976a",
    "forbidden_signature_hash": "3126535ec385e265",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|6",
    "pool_signature_hash": "22402377b4c1e40c",
    "pool_task_set_hash": "3c66a844944479b2",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 7.571723,
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->5:low_risk:2",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      19,
      5
    ],
    "target_sequence": [
      19,
      5,
      13,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->5:low_risk:2",
          "5->0:low_time:0"
        ],
        "sequence": [
          19,
          5
        ],
        "start_time": 18.338654
      },
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->0:low_time:0"
        ],
        "sequence": [
          13
        ],
        "start_time": 260.75182
      },
      {
        "arc_option_sequence": [
          "0->9:low_time:0",
          "9->0:low_time:0"
        ],
        "sequence": [
          9
        ],
        "start_time": 507.881796
      }
    ],
    "true_dual_hash": "3e2c91d2ed0ef1c5",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "8790f681cbfebafd",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 5,
    "cell_positive_rate": 0.555556,
    "cell_training_negative_count": 4,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "37e3048dada58785",
    "forbidden_signature_hash": "9fda548924a433bc",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|4",
    "pool_signature_hash": "2e2a142a53b54e60",
    "pool_task_set_hash": "8eb7f378539697ea",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 6.192574,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->6:low_risk:1",
      "6->12:low_time:0",
      "12->13:low_risk:2",
      "13->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_priority_sequence": [
      2,
      6,
      12,
      13,
      8
    ],
    "target_sequence": [
      2,
      6,
      12,
      13,
      8,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->6:low_risk:1",
          "6->12:low_time:0",
          "12->13:low_risk:2",
          "13->8:low_risk:2",
          "8->0:low_risk:2"
        ],
        "sequence": [
          2,
          6,
          12,
          13,
          8
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->0:low_time:0"
        ],
        "sequence": [
          17
        ],
        "start_time": 530.786948
      }
    ],
    "true_dual_hash": "b81f49d3ea61f304",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "046afcb353c352b7",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 5,
    "cell_positive_rate": 0.555556,
    "cell_training_negative_count": 4,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "07e693c5f161a590",
    "forbidden_signature_hash": "f4445bab7cdc5551",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|4",
    "pool_signature_hash": "b89cc38a3e4b3afa",
    "pool_task_set_hash": "1da371912db77d6a",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 6.190332,
    "target_arc_option_sequence": [
      "0->18:low_time:0",
      "18->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      18,
      5
    ],
    "target_sequence": [
      18,
      5,
      4,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_time:0",
          "18->5:low_time:0",
          "5->0:low_time:0"
        ],
        "sequence": [
          18,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->4:low_time:0",
          "4->11:low_time:0",
          "11->0:low_time:0"
        ],
        "sequence": [
          4,
          11
        ],
        "start_time": 406.924018
      }
    ],
    "true_dual_hash": "e617ca5198fa3898",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 2 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 2 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d8b85dff55093cb1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,6,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,6,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,6,20,3,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->6:low_time:0","6->20:low_risk:1","20->0:low_risk:2"],"sequence":[4,6,20],"start_time":4.4203},{"arc_option_sequence":["0->3:low_time:0","3->7:low_time:0","7->0:low_time:0"],"sequence":[3,7],"start_time":326.708516}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->6:low_time:0,6->20:low_risk:1,20->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ddb0ce64af10976a --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=19,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=19,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=19,5,13,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->19:low_risk:2","19->5:low_risk:2","5->0:low_time:0"],"sequence":[19,5],"start_time":18.338654},{"arc_option_sequence":["0->13:low_risk:2","13->0:low_time:0"],"sequence":[13],"start_time":260.75182},{"arc_option_sequence":["0->9:low_time:0","9->0:low_time:0"],"sequence":[9],"start_time":507.881796}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->19:low_risk:2,19->5:low_risk:2,5->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=37e3048dada58785 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,6,12,13,8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,6,12,13,8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,6,12,13,8,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_time:0","2->6:low_risk:1","6->12:low_time:0","12->13:low_risk:2","13->8:low_risk:2","8->0:low_risk:2"],"sequence":[2,6,12,13,8],"start_time":0.0},{"arc_option_sequence":["0->17:low_time:0","17->0:low_time:0"],"sequence":[17],"start_time":530.786948}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_time:0,2->6:low_risk:1,6->12:low_time:0,12->13:low_risk:2,13->8:low_risk:2,8->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=07e693c5f161a590 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,5,4,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_time:0","18->5:low_time:0","5->0:low_time:0"],"sequence":[18,5],"start_time":0.0},{"arc_option_sequence":["0->4:low_time:0","4->11:low_time:0","11->0:low_time:0"],"sequence":[4,11],"start_time":406.924018}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_time:0,18->5:low_time:0,5->0:low_time:0'
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
