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
    "active_hash_before": "859cbba15c6585c7",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 1,
    "cell_positive_rate": 0.076923,
    "cell_training_negative_count": 9,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "4575716b3939cb89",
    "forbidden_signature_hash": "e844295219f3e8fe",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "pool_signature_hash": "2355b3378249fd7c",
    "pool_task_set_hash": "a232e0dde7906105",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 13.081508,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->19:low_energy:1",
      "19->9:low_risk:2",
      "9->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_priority_sequence": [
      3,
      19,
      9,
      12
    ],
    "target_sequence": [
      3,
      19,
      9,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->19:low_energy:1",
          "19->9:low_risk:2",
          "9->12:low_risk:2",
          "12->0:low_time:0"
        ],
        "sequence": [
          3,
          19,
          9,
          12
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "2723e3b6445060e7",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "7f58f54e29eaf87d",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 1,
    "cell_positive_rate": 0.076923,
    "cell_training_negative_count": 9,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ff6827bb236f4831",
    "forbidden_signature_hash": "3b2a853c944fe40e",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "pool_signature_hash": "e7b1f9704726e1eb",
    "pool_task_set_hash": "4a05d50ee276e2c8",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 13.071736,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->18:low_time:0",
      "18->8:low_risk:2",
      "8->7:low_time:0",
      "7->9:low_energy:1",
      "9->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_priority_sequence": [
      3,
      18,
      8,
      7,
      9,
      12
    ],
    "target_sequence": [
      3,
      18,
      8,
      7,
      9,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->18:low_time:0",
          "18->8:low_risk:2",
          "8->7:low_time:0",
          "7->9:low_energy:1",
          "9->12:low_risk:2",
          "12->0:low_time:0"
        ],
        "sequence": [
          3,
          18,
          8,
          7,
          9,
          12
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "d311567607dbafaa",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "e00e5f54b69345ba",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 1,
    "cell_positive_rate": 0.055556,
    "cell_training_negative_count": 15,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "9eb0dc7839bf91ec",
    "forbidden_signature_hash": "eefa5f433de1f487",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "pool_signature_hash": "8c1c94d7b1c2c4b2",
    "pool_task_set_hash": "3b02449ad82d2dc3",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 12.867804,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->17:low_risk:1",
      "17->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_priority_sequence": [
      2,
      17,
      16
    ],
    "target_sequence": [
      2,
      17,
      16,
      13,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->17:low_risk:1",
          "17->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          2,
          17,
          16
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->18:low_time:0",
          "18->0:low_time:0"
        ],
        "sequence": [
          13,
          18
        ],
        "start_time": 336.687825
      }
    ],
    "true_dual_hash": "4fa661248332899c",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "86d9789a5b8352f0",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 1,
    "cell_positive_rate": 0.055556,
    "cell_training_negative_count": 15,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ec59d1f203f1630c",
    "forbidden_signature_hash": "a9b02ad000676eeb",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "pool_signature_hash": "b22e9d42681f1d67",
    "pool_task_set_hash": "c400b3d02d0fc424",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 12.820374,
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->17:low_risk:2",
      "17->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      17
    ],
    "target_sequence": [
      20,
      17,
      15,
      1,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->17:low_risk:2",
          "17->0:low_risk:2"
        ],
        "sequence": [
          20,
          17
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->1:low_energy:1",
          "1->13:low_time:0",
          "13->0:low_time:0"
        ],
        "sequence": [
          15,
          1,
          13
        ],
        "start_time": 195.108447
      }
    ],
    "true_dual_hash": "e408b632cdf39f5e",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "931e9eb7f04e3978",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "67925c0d2fd4abde",
    "forbidden_signature_hash": "0497e0ba36dd09db",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7",
    "negative_gap": 1,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|6",
    "pool_signature_hash": "c1ce4f0c1c5fedec",
    "pool_task_set_hash": "eb7766f8ef463e03",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 11.27443,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->17:low_time:0",
      "17->16:low_risk:2",
      "16->1:low_time:0",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      17,
      16,
      1
    ],
    "target_sequence": [
      20,
      17,
      16,
      1,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->17:low_time:0",
          "17->16:low_risk:2",
          "16->1:low_time:0",
          "1->0:low_risk:2"
        ],
        "sequence": [
          20,
          17,
          16,
          1
        ],
        "start_time": 25.406293
      },
      {
        "arc_option_sequence": [
          "0->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          7
        ],
        "start_time": 370.348334
      }
    ],
    "true_dual_hash": "8be9fa1cee656941",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "2ea75ed4e70d366e",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f4e732e2cfdeea6e",
    "forbidden_signature_hash": "2bd421a6b14906d2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17",
    "negative_gap": 1,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|7",
    "pool_signature_hash": "18669646faec5846",
    "pool_task_set_hash": "732bd8493c75ee14",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 11.028381,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->12:low_time:0",
      "12->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      12
    ],
    "target_sequence": [
      20,
      12,
      18,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->12:low_time:0",
          "12->0:low_risk:2"
        ],
        "sequence": [
          20,
          12
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_time:0",
          "18->17:low_risk:2",
          "17->0:low_time:0"
        ],
        "sequence": [
          18,
          17
        ],
        "start_time": 282.783247
      }
    ],
    "true_dual_hash": "755dfe2226982436",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=4575716b3939cb89 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,19,9,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,19,9,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,19,9,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:2","3->19:low_energy:1","19->9:low_risk:2","9->12:low_risk:2","12->0:low_time:0"],"sequence":[3,19,9,12],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:2,3->19:low_energy:1,19->9:low_risk:2,9->12:low_risk:2,12->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ff6827bb236f4831 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,18,8,7,9,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,18,8,7,9,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,18,8,7,9,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:2","3->18:low_time:0","18->8:low_risk:2","8->7:low_time:0","7->9:low_energy:1","9->12:low_risk:2","12->0:low_time:0"],"sequence":[3,18,8,7,9,12],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:2,3->18:low_time:0,18->8:low_risk:2,8->7:low_time:0,7->9:low_energy:1,9->12:low_risk:2,12->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=9eb0dc7839bf91ec --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,17,16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,17,16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,17,16,13,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_time:0","2->17:low_risk:1","17->16:low_time:0","16->0:low_time:0"],"sequence":[2,17,16],"start_time":0.0},{"arc_option_sequence":["0->13:low_risk:2","13->18:low_time:0","18->0:low_time:0"],"sequence":[13,18],"start_time":336.687825}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_time:0,2->17:low_risk:1,17->16:low_time:0,16->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ec59d1f203f1630c --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,17,15,1,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_risk:2","20->17:low_risk:2","17->0:low_risk:2"],"sequence":[20,17],"start_time":0.0},{"arc_option_sequence":["0->15:low_risk:2","15->1:low_energy:1","1->13:low_time:0","13->0:low_time:0"],"sequence":[15,1,13],"start_time":195.108447}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_risk:2,20->17:low_risk:2,17->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=67925c0d2fd4abde --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,17,16,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,17,16,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,17,16,1,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->17:low_time:0","17->16:low_risk:2","16->1:low_time:0","1->0:low_risk:2"],"sequence":[20,17,16,1],"start_time":25.406293},{"arc_option_sequence":["0->7:low_time:0","7->0:low_time:0"],"sequence":[7],"start_time":370.348334}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->17:low_time:0,17->16:low_risk:2,16->1:low_time:0,1->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f4e732e2cfdeea6e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,12,18,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->12:low_time:0","12->0:low_risk:2"],"sequence":[20,12],"start_time":0.0},{"arc_option_sequence":["0->18:low_time:0","18->17:low_risk:2","17->0:low_time:0"],"sequence":[18,17],"start_time":282.783247}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->12:low_time:0,12->0:low_risk:2'
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
