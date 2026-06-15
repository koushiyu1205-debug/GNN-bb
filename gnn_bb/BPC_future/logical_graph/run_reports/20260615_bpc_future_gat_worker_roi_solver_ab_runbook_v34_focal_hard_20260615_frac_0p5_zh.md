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
candidate_count = 5
decision_split = validation
decision_name = HIGH_PRIORITY
positive_label_only = false
excluded_candidate_key_count = 0
exclude_candidate_jsonl_count = 0
max_workers = 4
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
    "active_hash_before": "96c7c0766604244a",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json|ac15bc4e7e3d6fff|4,19,10,17|0->4:low_risk:2,4->0:low_risk:2",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "forbidden_signature_hash": "16f38b9203fc0908",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17",
    "pool_signature_hash": "a3a808a977a593aa",
    "pool_task_set_hash": "393c147abf261db2",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "validation",
    "source_row_index": 105,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4,
      19,
      10,
      17
    ],
    "target_sequence": [
      4,
      19,
      10,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->0:low_risk:2"
        ],
        "sequence": [
          4
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->10:low_time:0",
          "10->17:low_risk:2",
          "17->0:low_time:0"
        ],
        "sequence": [
          19,
          10,
          17
        ],
        "start_time": 202.264867
      }
    ],
    "true_dual_hash": "b49472077fb42329",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.6378785967826843
  },
  {
    "active_hash_before": "7d81deb6b7371fa5",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json|68f9b4e3d7515691|7,6,1,19,2,8|0->7:low_time:0,7->6:low_energy:1,6->1:low_time:0,1->19:low_energy:1,19->2:low_energy:1,2->8:low_time:0,8->0:low_time:0",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "68f9b4e3d7515691",
    "forbidden_signature_hash": "f9fe31b819c2bd10",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8",
    "pool_signature_hash": "f92473b9e781f066",
    "pool_task_set_hash": "8979a0515dec9dc3",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 165,
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->6:low_energy:1",
      "6->1:low_time:0",
      "1->19:low_energy:1",
      "19->2:low_energy:1",
      "2->8:low_time:0",
      "8->0:low_time:0"
    ],
    "target_priority_sequence": [
      7,
      6,
      1,
      19,
      2,
      8
    ],
    "target_sequence": [
      7,
      6,
      1,
      19,
      2,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_time:0",
          "7->6:low_energy:1",
          "6->1:low_time:0",
          "1->19:low_energy:1",
          "19->2:low_energy:1",
          "2->8:low_time:0",
          "8->0:low_time:0"
        ],
        "sequence": [
          7,
          6,
          1,
          19,
          2,
          8
        ],
        "start_time": 42.02574
      }
    ],
    "true_dual_hash": "b58ef7c1fadb8b40",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.0,
    "worker_roi_score": 0.6370949745178223
  },
  {
    "active_hash_before": "ecf24ed55f829c83",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json|ee378d5c9364745a|7,14,6,19,11|0->7:low_risk:2,7->14:low_time:0,14->6:low_time:0,6->19:low_time:0,19->11:low_time:0,11->0:low_risk:2",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ee378d5c9364745a",
    "forbidden_signature_hash": "113d6a36088892f0",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11",
    "pool_signature_hash": "e5d792a2f67bb738",
    "pool_task_set_hash": "4be88547572266bd",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 167,
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->14:low_time:0",
      "14->6:low_time:0",
      "6->19:low_time:0",
      "19->11:low_time:0",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      7,
      14,
      6,
      19,
      11
    ],
    "target_sequence": [
      7,
      14,
      6,
      19,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->14:low_time:0",
          "14->6:low_time:0",
          "6->19:low_time:0",
          "19->11:low_time:0",
          "11->0:low_risk:2"
        ],
        "sequence": [
          7,
          14,
          6,
          19,
          11
        ],
        "start_time": 37.590443
      }
    ],
    "true_dual_hash": "457accd186602990",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.6352970004081726
  },
  {
    "active_hash_before": "e26a52ba1316b49c",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json|7079ec06a2d9eab3|7,12|0->7:low_risk:2,7->0:low_time:0",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7079ec06a2d9eab3",
    "forbidden_signature_hash": "3359fd60e0ee35a2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12",
    "pool_signature_hash": "25120bd919c33dc8",
    "pool_task_set_hash": "436be223c00e008d",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "validation",
    "source_row_index": 178,
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->0:low_time:0"
    ],
    "target_priority_sequence": [
      7,
      12
    ],
    "target_sequence": [
      7,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->0:low_time:0"
        ],
        "sequence": [
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->12:low_time:0",
          "12->0:low_time:0"
        ],
        "sequence": [
          12
        ],
        "start_time": 240.808163
      }
    ],
    "true_dual_hash": "1fc854fed0a1689d",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.0,
    "worker_roi_score": 0.6099191904067993
  },
  {
    "active_hash_before": "e26a52ba1316b49c",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json|7079ec06a2d9eab3|8,14,11,9,17,5|0->8:low_time:0,8->14:low_risk:2,14->11:low_time:0,11->9:low_time:0,9->0:low_time:0",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7079ec06a2d9eab3",
    "forbidden_signature_hash": "3359fd60e0ee35a2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5",
    "pool_signature_hash": "25120bd919c33dc8",
    "pool_task_set_hash": "436be223c00e008d",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "validation",
    "source_row_index": 157,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->14:low_risk:2",
      "14->11:low_time:0",
      "11->9:low_time:0",
      "9->0:low_time:0"
    ],
    "target_priority_sequence": [
      8,
      14,
      11,
      9,
      17,
      5
    ],
    "target_sequence": [
      8,
      14,
      11,
      9,
      17,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->14:low_risk:2",
          "14->11:low_time:0",
          "11->9:low_time:0",
          "9->0:low_time:0"
        ],
        "sequence": [
          8,
          14,
          11,
          9
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          17,
          5
        ],
        "start_time": 381.433678
      }
    ],
    "true_dual_hash": "1fc854fed0a1689d",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.0,
    "worker_roi_score": 0.6075140237808228
  }
]
```

## Commands

### task005_mainline_no_regression_no_new_worker

Run task-5 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task005_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task005_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task005_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task005_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_no_new_worker

Run task-10 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task010_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task010_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task010_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task010_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac15bc4e7e3d6fff --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,19,10,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,19,10,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,19,10,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->0:low_risk:2"],"sequence":[4],"start_time":0.0},{"arc_option_sequence":["0->19:low_risk:2","19->10:low_time:0","10->17:low_risk:2","17->0:low_time:0"],"sequence":[19,10,17],"start_time":202.264867}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=68f9b4e3d7515691 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,6,1,19,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,6,1,19,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,6,1,19,2,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_time:0","7->6:low_energy:1","6->1:low_time:0","1->19:low_energy:1","19->2:low_energy:1","2->8:low_time:0","8->0:low_time:0"],"sequence":[7,6,1,19,2,8],"start_time":42.02574}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_time:0,7->6:low_energy:1,6->1:low_time:0,1->19:low_energy:1,19->2:low_energy:1,2->8:low_time:0,8->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ee378d5c9364745a --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,14,6,19,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,14,6,19,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,14,6,19,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_risk:2","7->14:low_time:0","14->6:low_time:0","6->19:low_time:0","19->11:low_time:0","11->0:low_risk:2"],"sequence":[7,14,6,19,11],"start_time":37.590443}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_risk:2,7->14:low_time:0,14->6:low_time:0,6->19:low_time:0,19->11:low_time:0,11->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7079ec06a2d9eab3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_risk:2","7->0:low_time:0"],"sequence":[7],"start_time":0.0},{"arc_option_sequence":["0->12:low_time:0","12->0:low_time:0"],"sequence":[12],"start_time":240.808163}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_risk:2,7->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7079ec06a2d9eab3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,14,11,9,17,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,14,11,9,17,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,14,11,9,17,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->14:low_risk:2","14->11:low_time:0","11->9:low_time:0","9->0:low_time:0"],"sequence":[8,14,11,9],"start_time":0.0},{"arc_option_sequence":["0->17:low_time:0","17->5:low_risk:2","5->0:low_risk:2"],"sequence":[17,5],"start_time":381.433678}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->14:low_risk:2,14->11:low_time:0,11->9:low_time:0,9->0:low_time:0'
```

### audit_worker_roi_solver_ab_results

Read result CSVs after the solver commands finish.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_worker_roi_solver_ab_results.py --runbook-summary BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/summary.json --output-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/ab_audit --report BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_focal_hard_20260615_frac_0p5/ab_audit_zh.md
```

## 边界

- 该 runbook 不是生产开关；
- 5/10 命令不启用新的 hidden-negative worker；
- 20 worker 命令必须显式 opt-in；
- 所有命令都不启用 sharded Pulse certificate 或 official-bound shortcut；
- 未通过安全壳的 true-RC negative 只能延迟，不能永久丢弃。
