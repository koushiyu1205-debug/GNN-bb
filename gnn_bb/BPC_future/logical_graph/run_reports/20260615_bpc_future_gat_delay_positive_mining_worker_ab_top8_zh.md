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
    "active_hash_before": "c15c849bd934ae0b",
    "baseline_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "4848230110b93844",
    "forbidden_signature_hash": "b1a214d4d4528dc1",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14",
    "pool_signature_hash": "b877226d4d3a777b",
    "pool_task_set_hash": "f1740c235953be41",
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->6:low_risk:2",
      "6->1:low_risk:1",
      "1->4:low_time:0",
      "4->10:low_risk:2",
      "10->14:low_risk:1",
      "14->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8,
      6,
      1,
      4,
      10,
      14
    ],
    "target_sequence": [
      8,
      6,
      1,
      4,
      10,
      14
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->6:low_risk:2",
          "6->1:low_risk:1",
          "1->4:low_time:0",
          "4->10:low_risk:2",
          "10->14:low_risk:1",
          "14->0:low_risk:2"
        ],
        "sequence": [
          8,
          6,
          1,
          4,
          10,
          14
        ],
        "start_time": 95.671785
      }
    ],
    "true_dual_hash": "68a5fd0bc5ad634a",
    "worker_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3a997f8b9a0db491",
    "baseline_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "94206d715106bf37",
    "forbidden_signature_hash": "9dfa3be1e38061a1",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10",
    "pool_signature_hash": "3c14b550cf403def",
    "pool_task_set_hash": "9f6b5f0d3c4b52bc",
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
      15,
      6,
      1,
      4,
      10
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
          "0->15:low_risk:1",
          "15->6:low_risk:2",
          "6->1:low_risk:1",
          "1->4:low_time:0",
          "4->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          15,
          6,
          1,
          4,
          10
        ],
        "start_time": 137.565957
      }
    ],
    "true_dual_hash": "f5f56561331d69be",
    "worker_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d000a8a879dc40ae",
    "baseline_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "33788d6b7bdf8387",
    "forbidden_signature_hash": "0f2d01e925626b31",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19",
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
      15,
      6,
      16,
      9,
      19
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
          "0->15:low_risk:1",
          "15->6:low_time:0",
          "6->16:low_time:0",
          "16->9:low_time:0",
          "9->19:low_energy:1",
          "19->0:low_risk:2"
        ],
        "sequence": [
          15,
          6,
          16,
          9,
          19
        ],
        "start_time": 131.723068
      }
    ],
    "true_dual_hash": "93838678a3afe721",
    "worker_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3a997f8b9a0db491",
    "baseline_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "c5025a0583f6ea6c",
    "forbidden_signature_hash": "e6cc5b5db49751b8",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19",
    "pool_signature_hash": "8fb404c9f371aa98",
    "pool_task_set_hash": "e31b722dd799f20c",
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
      15,
      6,
      1,
      9,
      19
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
          "0->15:low_risk:1",
          "15->6:low_time:0",
          "6->1:low_risk:1",
          "1->9:low_risk:2",
          "9->19:low_risk:2",
          "19->0:low_risk:2"
        ],
        "sequence": [
          15,
          6,
          1,
          9,
          19
        ],
        "start_time": 134.817149
      }
    ],
    "true_dual_hash": "5b190b4ef41a731e",
    "worker_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "8fa22105b7d71a70",
    "baseline_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "0f0c5d214add6400",
    "forbidden_signature_hash": "64cde73bd524b1e5",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15",
    "pool_signature_hash": "5a140851789d466b",
    "pool_task_set_hash": "a3df5269fcbc2319",
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->2:low_risk:2",
      "2->11:low_time:0",
      "11->17:low_risk:2",
      "17->0:low_time:0"
    ],
    "target_priority_sequence": [
      18,
      2,
      11,
      17
    ],
    "target_sequence": [
      18,
      2,
      11,
      17,
      3,
      15
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->2:low_risk:2",
          "2->11:low_time:0",
          "11->17:low_risk:2",
          "17->0:low_time:0"
        ],
        "sequence": [
          18,
          2,
          11,
          17
        ],
        "start_time": 8.056828
      },
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->15:low_time:0",
          "15->0:low_risk:2"
        ],
        "sequence": [
          3,
          15
        ],
        "start_time": 377.58502
      }
    ],
    "true_dual_hash": "5c6902f41c1a1901",
    "worker_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "09a48f148e1b778f",
    "baseline_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1b98b5f990279d7b",
    "forbidden_signature_hash": "25f63db63fe6d91e",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8",
    "pool_signature_hash": "13e3faea86aedecc",
    "pool_task_set_hash": "3bbfa1d0ffb5a306",
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->17:low_time:0",
      "17->18:low_time:0",
      "18->0:low_time:0"
    ],
    "target_priority_sequence": [
      2,
      17,
      18
    ],
    "target_sequence": [
      2,
      17,
      18,
      1,
      16,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->17:low_time:0",
          "17->18:low_time:0",
          "18->0:low_time:0"
        ],
        "sequence": [
          2,
          17,
          18
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->16:low_risk:2",
          "16->8:low_risk:2",
          "8->0:low_risk:2"
        ],
        "sequence": [
          1,
          16,
          8
        ],
        "start_time": 294.271406
      }
    ],
    "true_dual_hash": "710570cbd4775dae",
    "worker_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "2997fbc2110f0655",
    "baseline_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "27b61a4367a5c961",
    "forbidden_signature_hash": "8f673626592596c9",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10",
    "pool_signature_hash": "3e7af4d3033632d1",
    "pool_task_set_hash": "1f65f261c2892ea7",
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->2:low_risk:2",
      "2->0:low_time:0"
    ],
    "target_priority_sequence": [
      14,
      2
    ],
    "target_sequence": [
      14,
      2,
      1,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->2:low_risk:2",
          "2->0:low_time:0"
        ],
        "sequence": [
          14,
          2
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->10:low_time:0",
          "10->0:low_risk:2"
        ],
        "sequence": [
          1,
          10
        ],
        "start_time": 308.552862
      }
    ],
    "true_dual_hash": "129d7d3c03467e21",
    "worker_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "af6eba0dafca41b5",
    "baseline_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d8e422fc4def1c51",
    "forbidden_signature_hash": "22e114972c6ce5d9",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18",
    "pool_signature_hash": "5c29af7b1c9ec28d",
    "pool_task_set_hash": "5c3c07c892d145a0",
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->4:low_risk:2",
      "4->18:low_risk:2",
      "18->0:low_energy:1"
    ],
    "target_priority_sequence": [
      3,
      4,
      18
    ],
    "target_sequence": [
      3,
      4,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->4:low_risk:2",
          "4->18:low_risk:2",
          "18->0:low_energy:1"
        ],
        "sequence": [
          3,
          4,
          18
        ],
        "start_time": 123.003159
      }
    ],
    "true_dual_hash": "25dfd82dcc4235ce",
    "worker_csv": "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_mainline_baseline/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_mainline_baseline/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_target_priority_worker/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_target_priority_worker/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=4848230110b93844 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,6,1,4,10,14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,6,1,4,10,14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,6,1,4,10,14 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->6:low_risk:2","6->1:low_risk:1","1->4:low_time:0","4->10:low_risk:2","10->14:low_risk:1","14->0:low_risk:2"],"sequence":[8,6,1,4,10,14],"start_time":95.671785}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->6:low_risk:2,6->1:low_risk:1,1->4:low_time:0,4->10:low_risk:2,10->14:low_risk:1,14->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=94206d715106bf37 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,12,15,6,1,4,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_energy:1","13->12:low_time:0","12->0:low_time:0"],"sequence":[13,12],"start_time":0.0},{"arc_option_sequence":["0->15:low_risk:1","15->6:low_risk:2","6->1:low_risk:1","1->4:low_time:0","4->10:low_risk:2","10->0:low_risk:2"],"sequence":[15,6,1,4,10],"start_time":137.565957}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_energy:1,13->12:low_time:0,12->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=33788d6b7bdf8387 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,12,15,6,16,9,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_energy:1","13->12:low_time:0","12->0:low_time:0"],"sequence":[13,12],"start_time":0.0},{"arc_option_sequence":["0->15:low_risk:1","15->6:low_time:0","6->16:low_time:0","16->9:low_time:0","9->19:low_energy:1","19->0:low_risk:2"],"sequence":[15,6,16,9,19],"start_time":131.723068}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_energy:1,13->12:low_time:0,12->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=c5025a0583f6ea6c --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,12,15,6,1,9,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_energy:1","13->12:low_time:0","12->0:low_time:0"],"sequence":[13,12],"start_time":0.0},{"arc_option_sequence":["0->15:low_risk:1","15->6:low_time:0","6->1:low_risk:1","1->9:low_risk:2","9->19:low_risk:2","19->0:low_risk:2"],"sequence":[15,6,1,9,19],"start_time":134.817149}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_energy:1,13->12:low_time:0,12->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_target_priority_worker/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_target_priority_worker/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=0f0c5d214add6400 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18,2,11,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18,2,11,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,2,11,17,3,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_risk:2","18->2:low_risk:2","2->11:low_time:0","11->17:low_risk:2","17->0:low_time:0"],"sequence":[18,2,11,17],"start_time":8.056828},{"arc_option_sequence":["0->3:low_time:0","3->15:low_time:0","15->0:low_risk:2"],"sequence":[3,15],"start_time":377.58502}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_risk:2,18->2:low_risk:2,2->11:low_time:0,11->17:low_risk:2,17->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_target_priority_worker/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1b98b5f990279d7b --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,17,18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,17,18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,17,18,1,16,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_time:0","2->17:low_time:0","17->18:low_time:0","18->0:low_time:0"],"sequence":[2,17,18],"start_time":0.0},{"arc_option_sequence":["0->1:low_time:0","1->16:low_risk:2","16->8:low_risk:2","8->0:low_risk:2"],"sequence":[1,16,8],"start_time":294.271406}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_time:0,2->17:low_time:0,17->18:low_time:0,18->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=27b61a4367a5c961 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=14,2 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=14,2 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=14,2,1,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->14:low_risk:2","14->2:low_risk:2","2->0:low_time:0"],"sequence":[14,2],"start_time":0.0},{"arc_option_sequence":["0->1:low_time:0","1->10:low_time:0","10->0:low_risk:2"],"sequence":[1,10],"start_time":308.552862}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->14:low_risk:2,14->2:low_risk:2,2->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d8e422fc4def1c51 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,4,18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,4,18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,4,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_time:0","3->4:low_risk:2","4->18:low_risk:2","18->0:low_energy:1"],"sequence":[3,4,18],"start_time":123.003159}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_time:0,3->4:low_risk:2,4->18:low_risk:2,18->0:low_energy:1'
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
