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
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.482759,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "4848230110b93844",
    "forbidden_signature_hash": "b1a214d4d4528dc1",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11",
    "pool_signature_hash": "b877226d4d3a777b",
    "pool_task_set_hash": "f1740c235953be41",
    "target_arc_option_sequence": [
      "0->18:low_time:0",
      "18->3:low_energy:1",
      "3->11:low_time:0",
      "11->0:low_energy:1"
    ],
    "target_priority_sequence": [
      18,
      3,
      11
    ],
    "target_sequence": [
      18,
      3,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_time:0",
          "18->3:low_energy:1",
          "3->11:low_time:0",
          "11->0:low_energy:1"
        ],
        "sequence": [
          18,
          3,
          11
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "68a5fd0bc5ad634a",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3a997f8b9a0db491",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.482759,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "94206d715106bf37",
    "forbidden_signature_hash": "9dfa3be1e38061a1",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11",
    "pool_signature_hash": "3c14b550cf403def",
    "pool_task_set_hash": "9f6b5f0d3c4b52bc",
    "target_arc_option_sequence": [
      "0->15:low_risk:1",
      "15->6:low_risk:2",
      "6->2:low_risk:2",
      "2->4:low_risk:1",
      "4->1:low_time:0",
      "1->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      15,
      6,
      2,
      4,
      1,
      11
    ],
    "target_sequence": [
      15,
      6,
      2,
      4,
      1,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_risk:1",
          "15->6:low_risk:2",
          "6->2:low_risk:2",
          "2->4:low_risk:1",
          "4->1:low_time:0",
          "1->11:low_risk:2",
          "11->0:low_risk:2"
        ],
        "sequence": [
          15,
          6,
          2,
          4,
          1,
          11
        ],
        "start_time": 10.110635
      }
    ],
    "true_dual_hash": "f5f56561331d69be",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3a997f8b9a0db491",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.482759,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "c5025a0583f6ea6c",
    "forbidden_signature_hash": "e6cc5b5db49751b8",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5",
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
      3,
      5
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
          "0->3:low_risk:1",
          "3->5:low_time:0",
          "5->0:low_time:0"
        ],
        "sequence": [
          3,
          5
        ],
        "start_time": 166.969124
      }
    ],
    "true_dual_hash": "5b190b4ef41a731e",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3a997f8b9a0db491",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.482759,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7390856b04698300",
    "forbidden_signature_hash": "e2de72736530a6a9",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20",
    "pool_signature_hash": "399ef0ae303938ad",
    "pool_task_set_hash": "49b7daef1a9fc2c3",
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->16:low_time:0",
      "16->9:low_risk:2",
      "9->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      8,
      16,
      9,
      20
    ],
    "target_sequence": [
      8,
      16,
      9,
      20
    ],
    "target_sortie_traces": [
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
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "2997fbc2110f0655",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.333333,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "27b61a4367a5c961",
    "forbidden_signature_hash": "8f673626592596c9",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3",
    "pool_signature_hash": "3e7af4d3033632d1",
    "pool_task_set_hash": "1f65f261c2892ea7",
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->19:low_time:0",
      "19->3:low_risk:1",
      "3->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4,
      19,
      3
    ],
    "target_sequence": [
      4,
      19,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->19:low_time:0",
          "19->3:low_risk:1",
          "3->0:low_risk:2"
        ],
        "sequence": [
          4,
          19,
          3
        ],
        "start_time": 107.581601
      }
    ],
    "true_dual_hash": "129d7d3c03467e21",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "389e7838f069e6d3",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.333333,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "a05232b2b6c99641",
    "forbidden_signature_hash": "cecc1baa46bdf13a",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5",
    "pool_signature_hash": "ece781e2ac79a2aa",
    "pool_task_set_hash": "1f0b57fc9bdfe72e",
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->0:low_risk:2"
    ],
    "target_priority_sequence": [
      18
    ],
    "target_sequence": [
      18,
      4,
      11,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->0:low_risk:2"
        ],
        "sequence": [
          18
        ],
        "start_time": 13.496645
      },
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->11:low_time:0",
          "11->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          4,
          11,
          5
        ],
        "start_time": 201.167469
      }
    ],
    "true_dual_hash": "af3100671b189387",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "046afcb353c352b7",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.482759,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "07e693c5f161a590",
    "forbidden_signature_hash": "f4445bab7cdc5551",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17",
    "pool_signature_hash": "b89cc38a3e4b3afa",
    "pool_task_set_hash": "1da371912db77d6a",
    "target_arc_option_sequence": [
      "0->18:low_time:0",
      "18->5:low_risk:2",
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
      14,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_time:0",
          "18->5:low_risk:2",
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
          "4->14:low_time:0",
          "14->17:low_time:0",
          "17->0:low_time:0"
        ],
        "sequence": [
          4,
          14,
          17
        ],
        "start_time": 408.169422
      }
    ],
    "true_dual_hash": "e617ca5198fa3898",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "e26a52ba1316b49c",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.333333,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7079ec06a2d9eab3",
    "forbidden_signature_hash": "3359fd60e0ee35a2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5",
    "pool_signature_hash": "25120bd919c33dc8",
    "pool_task_set_hash": "436be223c00e008d",
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
      9
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
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "af6eba0dafca41b5",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.333333,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d067a87292522613",
    "forbidden_signature_hash": "81d1e292d504cf33",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5",
    "pool_signature_hash": "250360255c811678",
    "pool_task_set_hash": "672aa67b89626a7e",
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->12:low_time:0",
      "12->0:low_time:0"
    ],
    "target_priority_sequence": [
      8,
      12
    ],
    "target_sequence": [
      8,
      12,
      18,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->12:low_time:0",
          "12->0:low_time:0"
        ],
        "sequence": [
          8,
          12
        ],
        "start_time": 92.827291
      },
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->5:low_risk:2",
          "5->0:low_time:0"
        ],
        "sequence": [
          18,
          5
        ],
        "start_time": 420.502803
      }
    ],
    "true_dual_hash": "1cba2e7ed4601e0f",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "af6eba0dafca41b5",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.333333,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d067a87292522613",
    "forbidden_signature_hash": "81d1e292d504cf33",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5",
    "pool_signature_hash": "250360255c811678",
    "pool_task_set_hash": "672aa67b89626a7e",
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->3:low_risk:2",
      "3->19:low_risk:1",
      "19->0:low_time:0"
    ],
    "target_priority_sequence": [
      4,
      3,
      19
    ],
    "target_sequence": [
      4,
      3,
      19,
      18,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->3:low_risk:2",
          "3->19:low_risk:1",
          "19->0:low_time:0"
        ],
        "sequence": [
          4,
          3,
          19
        ],
        "start_time": 77.869626
      },
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->5:low_risk:2",
          "5->0:low_time:0"
        ],
        "sequence": [
          18,
          5
        ],
        "start_time": 419.754208
      }
    ],
    "true_dual_hash": "1cba2e7ed4601e0f",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "8790f681cbfebafd",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.482759,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "37e3048dada58785",
    "forbidden_signature_hash": "9fda548924a433bc",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17",
    "pool_signature_hash": "2e2a142a53b54e60",
    "pool_task_set_hash": "8eb7f378539697ea",
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->6:low_risk:1",
      "6->12:low_time:0",
      "12->13:low_risk:2",
      "13->7:low_risk:2",
      "7->0:low_time:0"
    ],
    "target_priority_sequence": [
      2,
      6,
      12,
      13,
      7
    ],
    "target_sequence": [
      2,
      6,
      12,
      13,
      7,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->6:low_risk:1",
          "6->12:low_time:0",
          "12->13:low_risk:2",
          "13->7:low_risk:2",
          "7->0:low_time:0"
        ],
        "sequence": [
          2,
          6,
          12,
          13,
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->17:low_risk:2",
          "17->0:low_risk:2"
        ],
        "sequence": [
          17
        ],
        "start_time": 498.707058
      }
    ],
    "true_dual_hash": "b81f49d3ea61f304",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "6cb4dad22a220111",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.333333,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7714263901aeb2ec",
    "forbidden_signature_hash": "d0adc91cc9df80e5",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19",
    "pool_signature_hash": "10deac344d39477b",
    "pool_task_set_hash": "ceb76ec4ad68b7b9",
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8
    ],
    "target_sequence": [
      8,
      14,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->0:low_risk:2"
        ],
        "sequence": [
          8
        ],
        "start_time": 54.504773
      },
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->19:low_risk:2",
          "19->0:low_risk:2"
        ],
        "sequence": [
          14,
          19
        ],
        "start_time": 252.33288
      }
    ],
    "true_dual_hash": "a99ea13dc01c6919",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "dddce018a60cca35",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.37931,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "39ec05e43b291642",
    "forbidden_signature_hash": "77e68285a0c7aef5",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9",
    "pool_signature_hash": "23a0075d28f31ca9",
    "pool_task_set_hash": "401c7ff0289b7a0c",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->8:low_risk:2",
      "8->0:low_time:0"
    ],
    "target_priority_sequence": [
      5,
      8
    ],
    "target_sequence": [
      5,
      8,
      18,
      16,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->8:low_risk:2",
          "8->0:low_time:0"
        ],
        "sequence": [
          5,
          8
        ],
        "start_time": 67.296809
      },
      {
        "arc_option_sequence": [
          "0->18:low_energy:1",
          "18->16:low_energy:1",
          "16->9:low_time:0",
          "9->0:low_time:0"
        ],
        "sequence": [
          18,
          16,
          9
        ],
        "start_time": 302.829549
      }
    ],
    "true_dual_hash": "061fdac57224cbc4",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "2c2e416db249f720",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.37931,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "3d1bd8618099b573",
    "forbidden_signature_hash": "dd79a2cfb5c63e21",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15",
    "pool_signature_hash": "eddad0807740a5f3",
    "pool_task_set_hash": "e1b494c430dfa84e",
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8
    ],
    "target_sequence": [
      8,
      17,
      15
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->0:low_risk:2"
        ],
        "sequence": [
          8
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->17:low_risk:2",
          "17->15:low_risk:2",
          "15->0:low_time:0"
        ],
        "sequence": [
          17,
          15
        ],
        "start_time": 210.955352
      }
    ],
    "true_dual_hash": "bc2e3db079d173a6",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "e1befacbd2b4f74d",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.266667,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ce3508e12ad69da7",
    "forbidden_signature_hash": "f55090bec72c3948",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14",
    "pool_signature_hash": "181b2a9dea1e645b",
    "pool_task_set_hash": "cd6e4848601a3fcc",
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->5:low_time:0",
      "5->10:low_risk:2",
      "10->14:low_risk:2",
      "14->0:low_risk:2"
    ],
    "target_priority_sequence": [
      16,
      5,
      10,
      14
    ],
    "target_sequence": [
      16,
      5,
      10,
      14
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->5:low_time:0",
          "5->10:low_risk:2",
          "10->14:low_risk:2",
          "14->0:low_risk:2"
        ],
        "sequence": [
          16,
          5,
          10,
          14
        ],
        "start_time": 83.467258
      }
    ],
    "true_dual_hash": "b05a14e29bf7d93d",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "7d81deb6b7371fa5",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.266667,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "68f9b4e3d7515691",
    "forbidden_signature_hash": "f9fe31b819c2bd10",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8",
    "pool_signature_hash": "f92473b9e781f066",
    "pool_task_set_hash": "8979a0515dec9dc3",
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
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "eac382d528c824c6",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.266667,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f29ac739f3cb5226",
    "forbidden_signature_hash": "30dc8483c88be66c",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10",
    "pool_signature_hash": "fa4da2e0af2f4a8d",
    "pool_task_set_hash": "ed8a6e8ddef3d056",
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      3,
      5
    ],
    "target_sequence": [
      3,
      5,
      4,
      2,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->5:low_time:0",
          "5->0:low_time:0"
        ],
        "sequence": [
          3,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->2:low_risk:1",
          "2->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          4,
          2,
          10
        ],
        "start_time": 293.846584
      }
    ],
    "true_dual_hash": "bc4dbdb316129d71",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "ecf24ed55f829c83",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.266667,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ee378d5c9364745a",
    "forbidden_signature_hash": "113d6a36088892f0",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11",
    "pool_signature_hash": "e5d792a2f67bb738",
    "pool_task_set_hash": "4be88547572266bd",
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
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "96c7c0766604244a",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.37931,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "forbidden_signature_hash": "16f38b9203fc0908",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15",
    "pool_signature_hash": "a3a808a977a593aa",
    "pool_task_set_hash": "393c147abf261db2",
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_priority_sequence": [
      16
    ],
    "target_sequence": [
      16,
      17,
      15
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          16
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->15:low_energy:1",
          "15->0:low_risk:2"
        ],
        "sequence": [
          17,
          15
        ],
        "start_time": 264.580456
      }
    ],
    "true_dual_hash": "b49472077fb42329",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "65cd1c048360cf2e",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.266667,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "04c4d16cf38f75d9",
    "forbidden_signature_hash": "1389276e7a39cbc6",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8",
    "pool_signature_hash": "25cfb1011ebff24b",
    "pool_task_set_hash": "a7c7ca1ed83f95b0",
    "target_arc_option_sequence": [
      "0->9:low_energy:1",
      "9->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      9,
      5
    ],
    "target_sequence": [
      9,
      5,
      11,
      4,
      2,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->9:low_energy:1",
          "9->5:low_time:0",
          "5->0:low_time:0"
        ],
        "sequence": [
          9,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_risk:2",
          "11->4:low_risk:1",
          "4->2:low_risk:1",
          "2->8:low_risk:1",
          "8->0:low_risk:2"
        ],
        "sequence": [
          11,
          4,
          2,
          8
        ],
        "start_time": 307.81881
      }
    ],
    "true_dual_hash": "242ef2dd4c8868d8",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "4981a129b0afed8b",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.37931,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "17ccb5dc2e9bbac0",
    "forbidden_signature_hash": "33392c6eb4d6d5e3",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15",
    "pool_signature_hash": "64b6b6e5f8185d85",
    "pool_task_set_hash": "f0ca8f0b97d1e3aa",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      5
    ],
    "target_sequence": [
      5,
      10,
      15
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->0:low_time:0"
        ],
        "sequence": [
          5
        ],
        "start_time": 73.784012
      },
      {
        "arc_option_sequence": [
          "0->10:low_risk:2",
          "10->15:low_risk:2",
          "15->0:low_time:0"
        ],
        "sequence": [
          10,
          15
        ],
        "start_time": 245.103053
      }
    ],
    "true_dual_hash": "f70ed544ccc62915",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "809582ff03414493",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.266667,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "0df8d5cea7864e69",
    "forbidden_signature_hash": "76b64c9004112874",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18",
    "pool_signature_hash": "6d15c64a02b6077f",
    "pool_task_set_hash": "3f59bd5d0556eaf7",
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->18:low_risk:2",
      "18->0:low_time:0"
    ],
    "target_priority_sequence": [
      1,
      18
    ],
    "target_sequence": [
      1,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->18:low_risk:2",
          "18->0:low_time:0"
        ],
        "sequence": [
          1,
          18
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "1ce0a0d2ebfba758",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=4848230110b93844 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18,3,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18,3,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,3,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_time:0","18->3:low_energy:1","3->11:low_time:0","11->0:low_energy:1"],"sequence":[18,3,11],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_time:0,18->3:low_energy:1,3->11:low_time:0,11->0:low_energy:1'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=94206d715106bf37 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=15,6,2,4,1,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=15,6,2,4,1,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=15,6,2,4,1,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->15:low_risk:1","15->6:low_risk:2","6->2:low_risk:2","2->4:low_risk:1","4->1:low_time:0","1->11:low_risk:2","11->0:low_risk:2"],"sequence":[15,6,2,4,1,11],"start_time":10.110635}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->15:low_risk:1,15->6:low_risk:2,6->2:low_risk:2,2->4:low_risk:1,4->1:low_time:0,1->11:low_risk:2,11->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=c5025a0583f6ea6c --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,12,3,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_energy:1","13->12:low_time:0","12->0:low_time:0"],"sequence":[13,12],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:1","3->5:low_time:0","5->0:low_time:0"],"sequence":[3,5],"start_time":166.969124}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_energy:1,13->12:low_time:0,12->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7390856b04698300 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,16,9,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,16,9,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,16,9,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->16:low_time:0","16->9:low_risk:2","9->20:low_time:0","20->0:low_time:0"],"sequence":[8,16,9,20],"start_time":183.956416}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->16:low_time:0,16->9:low_risk:2,9->20:low_time:0,20->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=27b61a4367a5c961 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,19,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,19,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,19,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->19:low_time:0","19->3:low_risk:1","3->0:low_risk:2"],"sequence":[4,19,3],"start_time":107.581601}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->19:low_time:0,19->3:low_risk:1,3->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=a05232b2b6c99641 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,4,11,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_risk:2","18->0:low_risk:2"],"sequence":[18],"start_time":13.496645},{"arc_option_sequence":["0->4:low_risk:2","4->11:low_time:0","11->5:low_risk:2","5->0:low_risk:2"],"sequence":[4,11,5],"start_time":201.167469}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_risk:2,18->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=07e693c5f161a590 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,5,4,14,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_time:0","18->5:low_risk:2","5->0:low_time:0"],"sequence":[18,5],"start_time":0.0},{"arc_option_sequence":["0->4:low_time:0","4->14:low_time:0","14->17:low_time:0","17->0:low_time:0"],"sequence":[4,14,17],"start_time":408.169422}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_time:0,18->5:low_risk:2,5->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7079ec06a2d9eab3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,14,11,9 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,14,11,9 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,14,11,9,17,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->14:low_risk:2","14->11:low_time:0","11->9:low_time:0","9->0:low_time:0"],"sequence":[8,14,11,9],"start_time":0.0},{"arc_option_sequence":["0->17:low_time:0","17->5:low_risk:2","5->0:low_risk:2"],"sequence":[17,5],"start_time":381.433678}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->14:low_risk:2,14->11:low_time:0,11->9:low_time:0,9->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d067a87292522613 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,12,18,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->12:low_time:0","12->0:low_time:0"],"sequence":[8,12],"start_time":92.827291},{"arc_option_sequence":["0->18:low_risk:2","18->5:low_risk:2","5->0:low_time:0"],"sequence":[18,5],"start_time":420.502803}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->12:low_time:0,12->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d067a87292522613 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,3,19 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,3,19 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,3,19,18,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->3:low_risk:2","3->19:low_risk:1","19->0:low_time:0"],"sequence":[4,3,19],"start_time":77.869626},{"arc_option_sequence":["0->18:low_risk:2","18->5:low_risk:2","5->0:low_time:0"],"sequence":[18,5],"start_time":419.754208}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->3:low_risk:2,3->19:low_risk:1,19->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=37e3048dada58785 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,6,12,13,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,6,12,13,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,6,12,13,7,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_time:0","2->6:low_risk:1","6->12:low_time:0","12->13:low_risk:2","13->7:low_risk:2","7->0:low_time:0"],"sequence":[2,6,12,13,7],"start_time":0.0},{"arc_option_sequence":["0->17:low_risk:2","17->0:low_risk:2"],"sequence":[17],"start_time":498.707058}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_time:0,2->6:low_risk:1,6->12:low_time:0,12->13:low_risk:2,13->7:low_risk:2,7->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7714263901aeb2ec --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,14,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->0:low_risk:2"],"sequence":[8],"start_time":54.504773},{"arc_option_sequence":["0->14:low_risk:2","14->19:low_risk:2","19->0:low_risk:2"],"sequence":[14,19],"start_time":252.33288}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=39ec05e43b291642 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,8,18,16,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->8:low_risk:2","8->0:low_time:0"],"sequence":[5,8],"start_time":67.296809},{"arc_option_sequence":["0->18:low_energy:1","18->16:low_energy:1","16->9:low_time:0","9->0:low_time:0"],"sequence":[18,16,9],"start_time":302.829549}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->8:low_risk:2,8->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_17_15_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=3d1bd8618099b573 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,17,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->0:low_risk:2"],"sequence":[8],"start_time":0.0},{"arc_option_sequence":["0->17:low_risk:2","17->15:low_risk:2","15->0:low_time:0"],"sequence":[17,15],"start_time":210.955352}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_ce3508e12ad69da7_16_5_10_14_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ce3508e12ad69da7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16,5,10,14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16,5,10,14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,5,10,14 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_time:0","16->5:low_time:0","5->10:low_risk:2","10->14:low_risk:2","14->0:low_risk:2"],"sequence":[16,5,10,14],"start_time":83.467258}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_time:0,16->5:low_time:0,5->10:low_risk:2,10->14:low_risk:2,14->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=68f9b4e3d7515691 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,6,1,19,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,6,1,19,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,6,1,19,2,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_time:0","7->6:low_energy:1","6->1:low_time:0","1->19:low_energy:1","19->2:low_energy:1","2->8:low_time:0","8->0:low_time:0"],"sequence":[7,6,1,19,2,8],"start_time":42.02574}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_time:0,7->6:low_energy:1,6->1:low_time:0,1->19:low_energy:1,19->2:low_energy:1,2->8:low_time:0,8->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_f29ac739f3cb5226_3_5_4_2_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f29ac739f3cb5226 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,5,4,2,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_time:0","3->5:low_time:0","5->0:low_time:0"],"sequence":[3,5],"start_time":0.0},{"arc_option_sequence":["0->4:low_risk:2","4->2:low_risk:1","2->10:low_risk:2","10->0:low_risk:2"],"sequence":[4,2,10],"start_time":293.846584}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_time:0,3->5:low_time:0,5->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ee378d5c9364745a --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,14,6,19,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,14,6,19,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,14,6,19,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_risk:2","7->14:low_time:0","14->6:low_time:0","6->19:low_time:0","19->11:low_time:0","11->0:low_risk:2"],"sequence":[7,14,6,19,11],"start_time":37.590443}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_risk:2,7->14:low_time:0,14->6:low_time:0,6->19:low_time:0,19->11:low_time:0,11->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_16_17_15_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac15bc4e7e3d6fff --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,17,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_time:0","16->0:low_time:0"],"sequence":[16],"start_time":0.0},{"arc_option_sequence":["0->17:low_time:0","17->15:low_energy:1","15->0:low_risk:2"],"sequence":[17,15],"start_time":264.580456}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_time:0,16->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_04c4d16cf38f75d9_9_5_11_4_2_8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=04c4d16cf38f75d9 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=9,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=9,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=9,5,11,4,2,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->9:low_energy:1","9->5:low_time:0","5->0:low_time:0"],"sequence":[9,5],"start_time":0.0},{"arc_option_sequence":["0->11:low_risk:2","11->4:low_risk:1","4->2:low_risk:1","2->8:low_risk:1","8->0:low_risk:2"],"sequence":[11,4,2,8],"start_time":307.81881}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->9:low_energy:1,9->5:low_time:0,5->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_5_10_15_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=17ccb5dc2e9bbac0 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,10,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->0:low_time:0"],"sequence":[5],"start_time":73.784012},{"arc_option_sequence":["0->10:low_risk:2","10->15:low_risk:2","15->0:low_time:0"],"sequence":[10,15],"start_time":245.103053}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v29_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=0df8d5cea7864e69 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1,18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1,18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_time:0","1->18:low_risk:2","18->0:low_time:0"],"sequence":[1,18],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_time:0,1->18:low_risk:2,18->0:low_time:0'
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
