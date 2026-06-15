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
candidate_count = 8
decision_split = validation
decision_name = DELAY_QUEUE
positive_label_only = true
excluded_candidate_key_count = 69
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
  "accuracy": 0.6666666666666666,
  "add_precision": 0.5555555555555556,
  "add_recall": 0.38461538461538464,
  "false_high_priority_rate": 0.17391304347826086,
  "false_negative_delay_queue": 8,
  "false_positive_high_priority": 4,
  "predicted_delay_queue": 27,
  "predicted_high_priority": 9,
  "total": 36,
  "true_negative_delay_queue": 19,
  "true_positive_high_priority": 5
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "931e9eb7f04e3978",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json|67925c0d2fd4abde|11,15,6|0->11:low_risk:2,11->15:low_risk:2,15->0:low_risk:2",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "67925c0d2fd4abde",
    "forbidden_signature_hash": "0497e0ba36dd09db",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6",
    "pool_signature_hash": "c1ce4f0c1c5fedec",
    "pool_task_set_hash": "eb7766f8ef463e03",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "validation",
    "source_row_index": 179,
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->15:low_risk:2",
      "15->0:low_risk:2"
    ],
    "target_priority_sequence": [
      11,
      15,
      6
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.7127271890640259
  },
  {
    "active_hash_before": "c3328e9771469ac9",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json|b46cdc0f247ab6e3|7,8,2,13|0->7:low_time:0,7->8:low_time:0,8->0:low_time:0",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b46cdc0f247ab6e3",
    "forbidden_signature_hash": "ec04c32f1201913e",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13",
    "pool_signature_hash": "840a4e1b3e9cc5f0",
    "pool_task_set_hash": "4074dfbaabd20498",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 123,
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->8:low_time:0",
      "8->0:low_time:0"
    ],
    "target_priority_sequence": [
      7,
      8,
      2,
      13
    ],
    "target_sequence": [
      7,
      8,
      2,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_time:0",
          "7->8:low_time:0",
          "8->0:low_time:0"
        ],
        "sequence": [
          7,
          8
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->2:low_risk:1",
          "2->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          2,
          13
        ],
        "start_time": 318.947912
      }
    ],
    "true_dual_hash": "ade0b4a9559f0665",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.6866083741188049
  },
  {
    "active_hash_before": "d9a28376789baaec",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json|4c81d9ecf77097c9|8,4,10|0->8:low_time:0,8->4:low_time:0,4->10:low_time:0,10->0:low_energy:1",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "4c81d9ecf77097c9",
    "forbidden_signature_hash": "72e4076e648b8514",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10",
    "pool_signature_hash": "c387cec8e60241d1",
    "pool_task_set_hash": "ee499f80528aeea9",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 177,
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 1.0,
    "worker_roi_score": 0.6093763709068298
  },
  {
    "active_hash_before": "c17edfb3cd7e8f05",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json|5c5a1e3be100b071|12,20,2|0->12:low_time:0,12->20:low_risk:2,20->2:low_time:0,2->0:low_time:0",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "5c5a1e3be100b071",
    "forbidden_signature_hash": "7f16fa898ec6e3de",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2",
    "pool_signature_hash": "04491760c95bd205",
    "pool_task_set_hash": "077a54edb21e05a0",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 40,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->20:low_risk:2",
      "20->2:low_time:0",
      "2->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      20,
      2
    ],
    "target_sequence": [
      12,
      20,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_time:0",
          "12->20:low_risk:2",
          "20->2:low_time:0",
          "2->0:low_time:0"
        ],
        "sequence": [
          12,
          20,
          2
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "298fa8febac5d588",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 1.0,
    "worker_roi_score": 0.5847551822662354
  },
  {
    "active_hash_before": "778c07cb4ef85021",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json|f9d0b6b18a0a28d3|18,3,13,6,19|0->18:low_risk:2,18->0:low_risk:2",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f9d0b6b18a0a28d3",
    "forbidden_signature_hash": "419f8f65acc3551b",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19",
    "pool_signature_hash": "d26348c8579fe2e4",
    "pool_task_set_hash": "49305ade6883086a",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 10,
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->0:low_risk:2"
    ],
    "target_priority_sequence": [
      18,
      3,
      13,
      6,
      19
    ],
    "target_sequence": [
      18,
      3,
      13,
      6,
      19
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
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->13:low_risk:2",
          "13->6:low_risk:2",
          "6->19:low_risk:2",
          "19->0:low_time:0"
        ],
        "sequence": [
          3,
          13,
          6,
          19
        ],
        "start_time": 206.946847
      }
    ],
    "true_dual_hash": "1f5fbbb40123e95b",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.5845838189125061
  },
  {
    "active_hash_before": "778c07cb4ef85021",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json|f9d0b6b18a0a28d3|20,18,3,4|0->20:low_time:0,20->18:low_energy:1,18->0:low_risk:2",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f9d0b6b18a0a28d3",
    "forbidden_signature_hash": "419f8f65acc3551b",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4",
    "pool_signature_hash": "d26348c8579fe2e4",
    "pool_task_set_hash": "49305ade6883086a",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 137,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->18:low_energy:1",
      "18->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      18,
      3,
      4
    ],
    "target_sequence": [
      20,
      18,
      3,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->18:low_energy:1",
          "18->0:low_risk:2"
        ],
        "sequence": [
          20,
          18
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->4:low_risk:2",
          "4->0:low_time:0"
        ],
        "sequence": [
          3,
          4
        ],
        "start_time": 228.617125
      }
    ],
    "true_dual_hash": "1f5fbbb40123e95b",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.5631064772605896
  },
  {
    "active_hash_before": "13951c54226c029d",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json|e8e35421df342768|5,14,1,20|0->5:low_risk:2,5->14:low_risk:2,14->1:low_risk:2,1->0:low_risk:2",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "e8e35421df342768",
    "forbidden_signature_hash": "8d39350d16921119",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20",
    "pool_signature_hash": "d5e85e9e642773cd",
    "pool_task_set_hash": "3555c1f405e7afcb",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 134,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->14:low_risk:2",
      "14->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      14,
      1,
      20
    ],
    "target_sequence": [
      5,
      14,
      1,
      20
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->14:low_risk:2",
          "14->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          5,
          14,
          1
        ],
        "start_time": 51.181514
      },
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->0:low_risk:2"
        ],
        "sequence": [
          20
        ],
        "start_time": 257.592567
      }
    ],
    "true_dual_hash": "c1d6bf0dee5fe2af",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.5498506426811218
  },
  {
    "active_hash_before": "16e2d0342cb4ce87",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "candidate_unique_key": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json|7db256d4f7224cc6|10,1,16,7,17,4|0->10:low_time:0,10->1:low_risk:2,1->16:low_time:0,16->7:low_risk:2,7->17:low_time:0,17->0:low_time:0",
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7db256d4f7224cc6",
    "forbidden_signature_hash": "5aeacc70a6d978d0",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4",
    "pool_signature_hash": "c5ddd5b68ac1fbd8",
    "pool_task_set_hash": "6f8bb60d3048867b",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 138,
    "target_arc_option_sequence": [
      "0->10:low_time:0",
      "10->1:low_risk:2",
      "1->16:low_time:0",
      "16->7:low_risk:2",
      "7->17:low_time:0",
      "17->0:low_time:0"
    ],
    "target_priority_sequence": [
      10,
      1,
      16,
      7,
      17,
      4
    ],
    "target_sequence": [
      10,
      1,
      16,
      7,
      17,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->10:low_time:0",
          "10->1:low_risk:2",
          "1->16:low_time:0",
          "16->7:low_risk:2",
          "7->17:low_time:0",
          "17->0:low_time:0"
        ],
        "sequence": [
          10,
          1,
          16,
          7,
          17
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->4:low_time:0",
          "4->0:low_time:0"
        ],
        "sequence": [
          4
        ],
        "start_time": 409.464411
      }
    ],
    "true_dual_hash": "2fbba0a0a55dc9ef",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 1.0,
    "worker_roi_score": 0.5410393476486206
  }
]
```

## Commands

### task005_mainline_no_regression_no_new_worker

Run task-5 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task005_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task005_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task005_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task005_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_no_new_worker

Run task-10 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task010_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task010_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task010_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task010_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=67925c0d2fd4abde --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=11,15,6 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=11,15,6 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=11,15,6 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->11:low_risk:2","11->15:low_risk:2","15->0:low_risk:2"],"sequence":[11,15],"start_time":0.0},{"arc_option_sequence":["0->6:low_risk:2","6->0:low_risk:2"],"sequence":[6],"start_time":307.577781}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->11:low_risk:2,11->15:low_risk:2,15->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b46cdc0f247ab6e3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,8,2,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,8,2,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,8,2,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_time:0","7->8:low_time:0","8->0:low_time:0"],"sequence":[7,8],"start_time":0.0},{"arc_option_sequence":["0->2:low_risk:1","2->13:low_risk:2","13->0:low_risk:2"],"sequence":[2,13],"start_time":318.947912}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_time:0,7->8:low_time:0,8->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=4c81d9ecf77097c9 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,4,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,4,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,4,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->4:low_time:0","4->10:low_time:0","10->0:low_energy:1"],"sequence":[8,4,10],"start_time":227.873491}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->4:low_time:0,4->10:low_time:0,10->0:low_energy:1'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=5c5a1e3be100b071 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,20,2 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,20,2 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,20,2 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_time:0","12->20:low_risk:2","20->2:low_time:0","2->0:low_time:0"],"sequence":[12,20,2],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_time:0,12->20:low_risk:2,20->2:low_time:0,2->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f9d0b6b18a0a28d3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18,3,13,6,19 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18,3,13,6,19 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,3,13,6,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_risk:2","18->0:low_risk:2"],"sequence":[18],"start_time":0.0},{"arc_option_sequence":["0->3:low_time:0","3->13:low_risk:2","13->6:low_risk:2","6->19:low_risk:2","19->0:low_time:0"],"sequence":[3,13,6,19],"start_time":206.946847}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_risk:2,18->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f9d0b6b18a0a28d3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,18,3,4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,18,3,4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,18,3,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->18:low_energy:1","18->0:low_risk:2"],"sequence":[20,18],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->4:low_risk:2","4->0:low_time:0"],"sequence":[3,4],"start_time":228.617125}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->18:low_energy:1,18->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=e8e35421df342768 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,14,1,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,14,1,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,14,1,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->14:low_risk:2","14->1:low_risk:2","1->0:low_risk:2"],"sequence":[5,14,1],"start_time":51.181514},{"arc_option_sequence":["0->20:low_risk:2","20->0:low_risk:2"],"sequence":[20],"start_time":257.592567}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->14:low_risk:2,14->1:low_risk:2,1->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7db256d4f7224cc6 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=10,1,16,7,17,4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=10,1,16,7,17,4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=10,1,16,7,17,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->10:low_time:0","10->1:low_risk:2","1->16:low_time:0","16->7:low_risk:2","7->17:low_time:0","17->0:low_time:0"],"sequence":[10,1,16,7,17],"start_time":0.0},{"arc_option_sequence":["0->4:low_time:0","4->0:low_time:0"],"sequence":[4],"start_time":409.464411}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->10:low_time:0,10->1:low_risk:2,1->16:low_time:0,16->7:low_risk:2,7->17:low_time:0,17->0:low_time:0'
```

### audit_worker_roi_solver_ab_results

Read result CSVs after the solver commands finish.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_worker_roi_solver_ab_results.py --runbook-summary BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/summary.json --output-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/ab_audit --report BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_validation_delay_positive_remaining_20260615/ab_audit_zh.md
```

## 边界

- 该 runbook 不是生产开关；
- 5/10 命令不启用新的 hidden-negative worker；
- 20 worker 命令必须显式 opt-in；
- 所有命令都不启用 sharded Pulse certificate 或 official-bound shortcut；
- 未通过安全壳的 true-RC negative 只能延迟，不能永久丢弃。
