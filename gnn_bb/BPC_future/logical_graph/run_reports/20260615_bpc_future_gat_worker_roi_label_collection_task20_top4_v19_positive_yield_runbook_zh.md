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
    "active_hash_before": "f94d076935f27fde",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 6,
    "cell_positive_rate": 0.666667,
    "cell_training_negative_count": 3,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "bec78bfc0baddb44",
    "forbidden_signature_hash": "e89be873ab67ab24",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|4",
    "pool_signature_hash": "06bc54750fc9ac71",
    "pool_task_set_hash": "80b62e66b4be6dc3",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 8.251577,
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->3:low_risk:1",
      "3->0:low_risk:2"
    ],
    "target_priority_sequence": [
      15,
      3
    ],
    "target_sequence": [
      15,
      3,
      8,
      16,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->3:low_risk:1",
          "3->0:low_risk:2"
        ],
        "sequence": [
          15,
          3
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->16:low_time:0",
          "16->2:low_risk:2",
          "2->0:low_time:0"
        ],
        "sequence": [
          8,
          16,
          2
        ],
        "start_time": 185.831264
      }
    ],
    "true_dual_hash": "dc29f619e1498bc2",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "40f42b78b78e3668",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 6,
    "cell_positive_rate": 0.666667,
    "cell_training_negative_count": 3,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "77bc967e4038b08b",
    "forbidden_signature_hash": "1420da74d3d03f9f",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|5",
    "pool_signature_hash": "336001920de5c08d",
    "pool_task_set_hash": "5c3e9193d63d59ad",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 8.241114,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->6:low_risk:2",
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
      18,
      2,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->6:low_risk:2",
          "6->20:low_risk:1",
          "20->0:low_risk:2"
        ],
        "sequence": [
          4,
          6,
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->2:low_time:0",
          "2->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          18,
          2,
          10
        ],
        "start_time": 337.557281
      }
    ],
    "true_dual_hash": "702d11c8080b0386",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "5260be3d13fa9cda",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.5,
    "cell_training_negative_count": 4,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b36178f6655c5f75",
    "forbidden_signature_hash": "b7258704c52ca4cf",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|4",
    "pool_signature_hash": "6dae80d2a19d1b2c",
    "pool_task_set_hash": "b8a49f5ce498f751",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 5.442239,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->12:low_risk:1",
      "12->13:low_risk:2",
      "13->8:low_risk:2",
      "8->15:low_time:0",
      "15->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_priority_sequence": [
      2,
      12,
      13,
      8,
      15,
      3
    ],
    "target_sequence": [
      2,
      12,
      13,
      8,
      15,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->12:low_risk:1",
          "12->13:low_risk:2",
          "13->8:low_risk:2",
          "8->15:low_time:0",
          "15->3:low_risk:2",
          "3->0:low_time:0"
        ],
        "sequence": [
          2,
          12,
          13,
          8,
          15,
          3
        ],
        "start_time": 53.762891
      }
    ],
    "true_dual_hash": "8c208ac829a68b55",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "809582ff03414493",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|apollo15_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.307692,
    "cell_training_negative_count": 8,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "0df8d5cea7864e69",
    "forbidden_signature_hash": "76b64c9004112874",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "pool_signature_hash": "6d15c64a02b6077f",
    "pool_task_set_hash": "3f59bd5d0556eaf7",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 4.932892,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->5:low_risk:2",
      "5->12:low_time:0",
      "12->10:low_risk:2",
      "10->0:low_risk:2"
    ],
    "target_priority_sequence": [
      16,
      5,
      12,
      10
    ],
    "target_sequence": [
      16,
      5,
      12,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->5:low_risk:2",
          "5->12:low_time:0",
          "12->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          16,
          5,
          12,
          10
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "1ce0a0d2ebfba758",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=bec78bfc0baddb44 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=15,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=15,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=15,3,8,16,2 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->15:low_risk:2","15->3:low_risk:1","3->0:low_risk:2"],"sequence":[15,3],"start_time":0.0},{"arc_option_sequence":["0->8:low_time:0","8->16:low_time:0","16->2:low_risk:2","2->0:low_time:0"],"sequence":[8,16,2],"start_time":185.831264}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->15:low_risk:2,15->3:low_risk:1,3->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=77bc967e4038b08b --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,6,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,6,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,6,20,18,2,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->6:low_risk:2","6->20:low_risk:1","20->0:low_risk:2"],"sequence":[4,6,20],"start_time":0.0},{"arc_option_sequence":["0->18:low_risk:2","18->2:low_time:0","2->10:low_risk:2","10->0:low_risk:2"],"sequence":[18,2,10],"start_time":337.557281}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->6:low_risk:2,6->20:low_risk:1,20->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b36178f6655c5f75 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,12,13,8,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,12,13,8,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,12,13,8,15,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_time:0","2->12:low_risk:1","12->13:low_risk:2","13->8:low_risk:2","8->15:low_time:0","15->3:low_risk:2","3->0:low_time:0"],"sequence":[2,12,13,8,15,3],"start_time":53.762891}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_time:0,2->12:low_risk:1,12->13:low_risk:2,13->8:low_risk:2,8->15:low_time:0,15->3:low_risk:2,3->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=0df8d5cea7864e69 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16,5,12,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16,5,12,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,5,12,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_time:0","16->5:low_risk:2","5->12:low_time:0","12->10:low_risk:2","10->0:low_risk:2"],"sequence":[16,5,12,10],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_time:0,16->5:low_risk:2,5->12:low_time:0,12->10:low_risk:2,10->0:low_risk:2'
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
