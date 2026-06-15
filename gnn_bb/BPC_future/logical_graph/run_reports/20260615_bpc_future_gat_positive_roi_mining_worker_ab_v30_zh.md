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
    "active_hash_before": "94ef3d055907ecdb",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.457143,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "33c54245da27321e",
    "forbidden_signature_hash": "43fcee1081686c15",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19",
    "pool_signature_hash": "99d0349bf9ade3d7",
    "pool_task_set_hash": "c82b5246779db63d",
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->17:low_risk:2",
      "17->19:low_time:0",
      "19->0:low_time:0"
    ],
    "target_priority_sequence": [
      16,
      17,
      19
    ],
    "target_sequence": [
      16,
      17,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->17:low_risk:2",
          "17->19:low_time:0",
          "19->0:low_time:0"
        ],
        "sequence": [
          16,
          17,
          19
        ],
        "start_time": 245.489951
      }
    ],
    "true_dual_hash": "8a49fa33ecd1ed88",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3a997f8b9a0db491",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.457143,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7390856b04698300",
    "forbidden_signature_hash": "e2de72736530a6a9",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20",
    "pool_signature_hash": "399ef0ae303938ad",
    "pool_task_set_hash": "49b7daef1a9fc2c3",
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_priority_sequence": [
      12
    ],
    "target_sequence": [
      12,
      8,
      16,
      9,
      20
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->0:low_risk:2"
        ],
        "sequence": [
          12
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->16:low_time:0",
          "16->9:low_risk:2",
          "9->20:low_time:0",
          "20->0:low_time:0"
        ],
        "sequence": [
          8,
          16,
          9,
          20
        ],
        "start_time": 183.956416
      }
    ],
    "true_dual_hash": "d2eeeea3185f6efb",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d000a8a879dc40ae",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.457143,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "33788d6b7bdf8387",
    "forbidden_signature_hash": "0f2d01e925626b31",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20",
    "pool_signature_hash": "06862cd8a43242fd",
    "pool_task_set_hash": "507656db00a5cc1c",
    "target_arc_option_sequence": [
      "0->13:low_energy:1",
      "13->12:low_time:0",
      "12->0:low_time:0"
    ],
    "target_priority_sequence": [
      13,
      12
    ],
    "target_sequence": [
      13,
      12,
      8,
      16,
      9,
      20
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_energy:1",
          "13->12:low_time:0",
          "12->0:low_time:0"
        ],
        "sequence": [
          13,
          12
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->16:low_time:0",
          "16->9:low_risk:2",
          "9->20:low_time:0",
          "20->0:low_time:0"
        ],
        "sequence": [
          8,
          16,
          9,
          20
        ],
        "start_time": 183.956416
      }
    ],
    "true_dual_hash": "93838678a3afe721",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "eb7ddfb3029ed64d",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.457143,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b1fb77954b949bf0",
    "forbidden_signature_hash": "81497f2e29d39933",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14",
    "pool_signature_hash": "e2151485b49e03db",
    "pool_task_set_hash": "74fb358c2ad9aae8",
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->12:low_time:0",
      "12->13:low_time:0",
      "13->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_priority_sequence": [
      6,
      12,
      13,
      7
    ],
    "target_sequence": [
      6,
      12,
      13,
      7,
      17,
      14
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_time:0",
          "6->12:low_time:0",
          "12->13:low_time:0",
          "13->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          6,
          12,
          13,
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->14:low_time:0",
          "14->0:low_time:0"
        ],
        "sequence": [
          17,
          14
        ],
        "start_time": 467.077394
      }
    ],
    "true_dual_hash": "ba52399ea678f004",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "7e1550730bce4588",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.457143,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "84ae11479ed592d4",
    "forbidden_signature_hash": "cfbda5e70fc052f2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5",
    "pool_signature_hash": "6321282f868e0007",
    "pool_task_set_hash": "f699ccb296afaee5",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->17:low_risk:2",
      "17->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_priority_sequence": [
      13,
      17,
      11
    ],
    "target_sequence": [
      13,
      17,
      11,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->17:low_risk:2",
          "17->11:low_risk:2",
          "11->0:low_time:0"
        ],
        "sequence": [
          13,
          17,
          11
        ],
        "start_time": 19.222023
      },
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          5
        ],
        "start_time": 275.78131
      }
    ],
    "true_dual_hash": "a5dfa0099f5679ed",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d9a28376789baaec",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.457143,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "4c81d9ecf77097c9",
    "forbidden_signature_hash": "72e4076e648b8514",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10",
    "pool_signature_hash": "c387cec8e60241d1",
    "pool_task_set_hash": "ee499f80528aeea9",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->4:low_time:0",
      "4->10:low_time:0",
      "10->0:low_energy:1"
    ],
    "target_priority_sequence": [
      8,
      4,
      10
    ],
    "target_sequence": [
      8,
      4,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->4:low_time:0",
          "4->10:low_time:0",
          "10->0:low_energy:1"
        ],
        "sequence": [
          8,
          4,
          10
        ],
        "start_time": 227.873491
      }
    ],
    "true_dual_hash": "7e4b750a4d705954",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "e26a52ba1316b49c",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.3125,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7079ec06a2d9eab3",
    "forbidden_signature_hash": "3359fd60e0ee35a2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12",
    "pool_signature_hash": "25120bd919c33dc8",
    "pool_task_set_hash": "436be223c00e008d",
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->0:low_time:0"
    ],
    "target_priority_sequence": [
      7
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
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "931e9eb7f04e3978",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.3125,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "67925c0d2fd4abde",
    "forbidden_signature_hash": "0497e0ba36dd09db",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6",
    "pool_signature_hash": "c1ce4f0c1c5fedec",
    "pool_task_set_hash": "eb7766f8ef463e03",
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->15:low_risk:2",
      "15->0:low_risk:2"
    ],
    "target_priority_sequence": [
      11,
      15
    ],
    "target_sequence": [
      11,
      15,
      6
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->11:low_risk:2",
          "11->15:low_risk:2",
          "15->0:low_risk:2"
        ],
        "sequence": [
          11,
          15
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->6:low_risk:2",
          "6->0:low_risk:2"
        ],
        "sequence": [
          6
        ],
        "start_time": 307.577781
      }
    ],
    "true_dual_hash": "8be9fa1cee656941",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=33c54245da27321e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16,17,19 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16,17,19 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,17,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_time:0","16->17:low_risk:2","17->19:low_time:0","19->0:low_time:0"],"sequence":[16,17,19],"start_time":245.489951}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_time:0,16->17:low_risk:2,17->19:low_time:0,19->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7390856b04698300 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,8,16,9,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->0:low_risk:2"],"sequence":[12],"start_time":0.0},{"arc_option_sequence":["0->8:low_risk:2","8->16:low_time:0","16->9:low_risk:2","9->20:low_time:0","20->0:low_time:0"],"sequence":[8,16,9,20],"start_time":183.956416}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=33788d6b7bdf8387 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,12,8,16,9,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_energy:1","13->12:low_time:0","12->0:low_time:0"],"sequence":[13,12],"start_time":0.0},{"arc_option_sequence":["0->8:low_risk:2","8->16:low_time:0","16->9:low_risk:2","9->20:low_time:0","20->0:low_time:0"],"sequence":[8,16,9,20],"start_time":183.956416}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_energy:1,13->12:low_time:0,12->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b1fb77954b949bf0 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,12,13,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,12,13,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,12,13,7,17,14 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_time:0","6->12:low_time:0","12->13:low_time:0","13->7:low_time:0","7->0:low_time:0"],"sequence":[6,12,13,7],"start_time":0.0},{"arc_option_sequence":["0->17:low_time:0","17->14:low_time:0","14->0:low_time:0"],"sequence":[17,14],"start_time":467.077394}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_time:0,6->12:low_time:0,12->13:low_time:0,13->7:low_time:0,7->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=84ae11479ed592d4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,17,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,17,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,17,11,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->17:low_risk:2","17->11:low_risk:2","11->0:low_time:0"],"sequence":[13,17,11],"start_time":19.222023},{"arc_option_sequence":["0->5:low_risk:2","5->0:low_risk:2"],"sequence":[5],"start_time":275.78131}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->17:low_risk:2,17->11:low_risk:2,11->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=4c81d9ecf77097c9 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,4,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,4,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,4,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->4:low_time:0","4->10:low_time:0","10->0:low_energy:1"],"sequence":[8,4,10],"start_time":227.873491}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->4:low_time:0,4->10:low_time:0,10->0:low_energy:1'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7079ec06a2d9eab3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_risk:2","7->0:low_time:0"],"sequence":[7],"start_time":0.0},{"arc_option_sequence":["0->12:low_time:0","12->0:low_time:0"],"sequence":[12],"start_time":240.808163}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_risk:2,7->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=67925c0d2fd4abde --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=11,15 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=11,15 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=11,15,6 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->11:low_risk:2","11->15:low_risk:2","15->0:low_risk:2"],"sequence":[11,15],"start_time":0.0},{"arc_option_sequence":["0->6:low_risk:2","6->0:low_risk:2"],"sequence":[6],"start_time":307.577781}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->11:low_risk:2,11->15:low_risk:2,15->0:low_risk:2'
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
