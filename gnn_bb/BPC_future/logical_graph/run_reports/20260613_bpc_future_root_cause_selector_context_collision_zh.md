# Root Cause Selector Context Collision 报告

日期：2026-06-13

## 目标

本报告只读分析 exact-context replay candidate rows，检查相同列局部形态
是否在不同 context 下同时出现 improved 与 noop 标签。不运行 BPC，
不修改 solver，不产生 certificate 或 lower-bound effect。

## 关键结果

```text
row_count = 280
label_counts = {'noop': 71, 'improved': 209}
task_set_group_count = 88
task_set_mixed_group_count = 6
task_set_mixed_row_count = 41
task_sequence_group_count = 94
task_sequence_mixed_group_count = 5
task_sequence_mixed_row_count = 30
online_flags_group_count = 4
online_flags_mixed_group_count = 2
online_flags_mixed_row_count = 278
task_flags_group_count = 88
task_flags_mixed_group_count = 6
task_flags_mixed_row_count = 41
```

## 混合标签示例

```json
{
  "online_flags": [
    {
      "context_count": 26,
      "dataset_count": 4,
      "datasets": [
        "real_capture_mt20_apollo",
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_counterfactual_target_capture_dp1000_tranq20_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0000",
          "case_id": "capture_case_0001",
          "context_hash": "080a188d2484ee3e",
          "cost": 80.486029,
          "impact_dataset": "real_capture_mt20_apollo",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5-4",
          "single_impact_class": "improved",
          "single_objective_delta": -137.116184,
          "strict_replacement_by_cost": false,
          "task_set": "4,5,8",
          "true_reduced_cost": -137.15071
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0001",
          "context_hash": "080a188d2484ee3e",
          "cost": 86.04001,
          "impact_dataset": "real_capture_mt20_apollo",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-4-18",
          "single_impact_class": "improved",
          "single_objective_delta": -129.128532,
          "strict_replacement_by_cost": false,
          "task_set": "4,8,18",
          "true_reduced_cost": -129.163058
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0002",
          "case_id": "capture_case_0001",
          "context_hash": "080a188d2484ee3e",
          "cost": 76.98419,
          "impact_dataset": "real_capture_mt20_apollo",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5",
          "single_impact_class": "improved",
          "single_objective_delta": -70.080792,
          "strict_replacement_by_cost": false,
          "task_set": "5,8",
          "true_reduced_cost": -70.080792
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0003",
          "case_id": "capture_case_0001",
          "context_hash": "080a188d2484ee3e",
          "cost": 77.104529,
          "impact_dataset": "real_capture_mt20_apollo",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-4",
          "single_impact_class": "improved",
          "single_objective_delta": -66.958244,
          "strict_replacement_by_cost": false,
          "task_set": "4,8",
          "true_reduced_cost": -66.99277
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "tranquillitatis_balmer_like_20km_tasks20_01_seed21000"
      ],
      "key": [
        "true",
        "false",
        "false"
      ],
      "label_counts": {
        "improved": 188,
        "noop": 49
      },
      "row_count": 237
    },
    {
      "context_count": 9,
      "dataset_count": 3,
      "datasets": [
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_counterfactual_target_capture_dp1000_tranq20_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0002",
          "case_id": "capture_case_0003",
          "context_hash": "7f2e531534d18ad2",
          "cost": 70.041527,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": false,
          "sequence": "3-2-20",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": true,
          "task_set": "2,3,20",
          "true_reduced_cost": -4.938736
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0003",
          "case_id": "capture_case_0003",
          "context_hash": "7f2e531534d18ad2",
          "cost": 64.82064,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": false,
          "sequence": "20-2",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": true,
          "task_set": "2,20",
          "true_reduced_cost": -4.467174
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0006",
          "context_hash": "7f2e531534d18ad2",
          "cost": 70.041527,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": false,
          "sequence": "3-2-20",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": true,
          "task_set": "2,3,20",
          "true_reduced_cost": -4.938736
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0002",
          "case_id": "capture_case_0006",
          "context_hash": "7f2e531534d18ad2",
          "cost": 64.82064,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": false,
          "sequence": "20-2",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": true,
          "task_set": "2,20",
          "true_reduced_cost": -4.467174
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "tranquillitatis_balmer_like_20km_tasks20_01_seed21000"
      ],
      "key": [
        "false",
        "true",
        "false"
      ],
      "label_counts": {
        "improved": 20,
        "noop": 21
      },
      "row_count": 41
    }
  ],
  "task_flags": [
    {
      "context_count": 2,
      "dataset_count": 3,
      "datasets": [
        "real_capture_mt20_apollo",
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0000",
          "case_id": "capture_case_0001",
          "context_hash": "080a188d2484ee3e",
          "cost": 80.486029,
          "impact_dataset": "real_capture_mt20_apollo",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5-4",
          "single_impact_class": "improved",
          "single_objective_delta": -137.116184,
          "strict_replacement_by_cost": false,
          "task_set": "4,5,8",
          "true_reduced_cost": -137.15071
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0001",
          "context_hash": "080a188d2484ee3e",
          "cost": 80.486029,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5-4",
          "single_impact_class": "improved",
          "single_objective_delta": -137.116184,
          "strict_replacement_by_cost": false,
          "task_set": "4,5,8",
          "true_reduced_cost": -137.15071
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0004",
          "context_hash": "080a188d2484ee3e",
          "cost": 80.486029,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5-4",
          "single_impact_class": "improved",
          "single_objective_delta": -137.116184,
          "strict_replacement_by_cost": false,
          "task_set": "4,5,8",
          "true_reduced_cost": -137.15071
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0007",
          "context_hash": "080a188d2484ee3e",
          "cost": 80.486029,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5-4",
          "single_impact_class": "improved",
          "single_objective_delta": -137.116184,
          "strict_replacement_by_cost": false,
          "task_set": "4,5,8",
          "true_reduced_cost": -137.15071
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
      ],
      "key": [
        "4,5,8",
        "true",
        "false",
        "false"
      ],
      "label_counts": {
        "improved": 7,
        "noop": 3
      },
      "row_count": 10
    },
    {
      "context_count": 5,
      "dataset_count": 3,
      "datasets": [
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_counterfactual_target_capture_dp1000_tranq20_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0000",
          "case_id": "capture_case_0020",
          "context_hash": "d60fcf4b919b7d22",
          "cost": 83.933862,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-18-5",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,18",
          "true_reduced_cost": -128.547499
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0000",
          "case_id": "capture_case_0024",
          "context_hash": "d60fcf4b919b7d22",
          "cost": 83.933862,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-18-5",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,18",
          "true_reduced_cost": -128.547499
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0000",
          "case_id": "capture_case_0028",
          "context_hash": "d60fcf4b919b7d22",
          "cost": 83.933862,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-18-5",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,18",
          "true_reduced_cost": -128.547499
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0007",
          "case_id": "capture_case_0002",
          "context_hash": "7ca23eb07bf4da54",
          "cost": 94.607382,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_tranq20_20260613",
          "instance": "tranquillitatis_balmer_like_20km_tasks20_01_seed21000",
          "new_task_set": true,
          "sequence": "18-5-12",
          "single_impact_class": "improved",
          "single_objective_delta": -23.4311445,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,18",
          "true_reduced_cost": -34.8665505
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "tranquillitatis_balmer_like_20km_tasks20_01_seed21000"
      ],
      "key": [
        "5,12,18",
        "true",
        "false",
        "false"
      ],
      "label_counts": {
        "improved": 1,
        "noop": 6
      },
      "row_count": 7
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "datasets": [
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0002",
          "context_hash": "3c36c602289637b4",
          "cost": 84.387441,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -73.864202
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0005",
          "context_hash": "3c36c602289637b4",
          "cost": 84.387441,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -73.864202
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0008",
          "context_hash": "3c36c602289637b4",
          "cost": 84.387441,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -73.864202
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0002",
          "context_hash": "827ddca748a70f26",
          "cost": 88.035274,
          "impact_dataset": "root_cause_target002_capture_pt03_r3_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "improved",
          "single_objective_delta": -27.407912,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -72.927452
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
      ],
      "key": [
        "4,12,14",
        "true",
        "false",
        "false"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "row_count": 6
    }
  ],
  "task_sequence": [
    {
      "context_count": 3,
      "dataset_count": 2,
      "datasets": [
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0002",
          "context_hash": "3c36c602289637b4",
          "cost": 84.387441,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -73.864202
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0005",
          "context_hash": "3c36c602289637b4",
          "cost": 84.387441,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -73.864202
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0008",
          "context_hash": "3c36c602289637b4",
          "cost": 84.387441,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -73.864202
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0002",
          "context_hash": "827ddca748a70f26",
          "cost": 88.035274,
          "impact_dataset": "root_cause_target002_capture_pt03_r3_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "improved",
          "single_objective_delta": -27.407912,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -72.927452
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
      ],
      "key": [
        "4,12,14",
        "14-12-4"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "row_count": 6
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "datasets": [
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0002",
          "context_hash": "3c36c602289637b4",
          "cost": 78.938545,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "17-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,17",
          "true_reduced_cost": -121.65471
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0005",
          "context_hash": "3c36c602289637b4",
          "cost": 78.938545,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "17-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,17",
          "true_reduced_cost": -121.65471
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0008",
          "context_hash": "3c36c602289637b4",
          "cost": 78.938545,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "17-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,17",
          "true_reduced_cost": -121.65471
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0002",
          "context_hash": "827ddca748a70f26",
          "cost": 82.586378,
          "impact_dataset": "root_cause_target002_capture_pt03_r3_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "17-12-4",
          "single_impact_class": "improved",
          "single_objective_delta": -44.85545425,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,17",
          "true_reduced_cost": -119.507575
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
      ],
      "key": [
        "4,12,17",
        "17-12-4"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "row_count": 6
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "datasets": [
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0005",
          "case_id": "capture_case_0003",
          "context_hash": "7f2e531534d18ad2",
          "cost": 83.033209,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-5-15",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,15",
          "true_reduced_cost": -0.586
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0006",
          "context_hash": "7f2e531534d18ad2",
          "cost": 83.033209,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-5-15",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,15",
          "true_reduced_cost": -0.586
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0005",
          "case_id": "capture_case_0009",
          "context_hash": "1db815e33b9ea471",
          "cost": 83.033209,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-5-15",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,15",
          "true_reduced_cost": -0.586
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0001",
          "context_hash": "080a188d2484ee3e",
          "cost": 83.033209,
          "impact_dataset": "root_cause_target002_capture_pt03_r3_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-5-15",
          "single_impact_class": "improved",
          "single_objective_delta": -130.692333,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,15",
          "true_reduced_cost": -133.018537
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
      ],
      "key": [
        "5,12,15",
        "12-5-15"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "row_count": 6
    }
  ],
  "task_set": [
    {
      "context_count": 2,
      "dataset_count": 3,
      "datasets": [
        "real_capture_mt20_apollo",
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0000",
          "case_id": "capture_case_0001",
          "context_hash": "080a188d2484ee3e",
          "cost": 80.486029,
          "impact_dataset": "real_capture_mt20_apollo",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5-4",
          "single_impact_class": "improved",
          "single_objective_delta": -137.116184,
          "strict_replacement_by_cost": false,
          "task_set": "4,5,8",
          "true_reduced_cost": -137.15071
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0001",
          "context_hash": "080a188d2484ee3e",
          "cost": 80.486029,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5-4",
          "single_impact_class": "improved",
          "single_objective_delta": -137.116184,
          "strict_replacement_by_cost": false,
          "task_set": "4,5,8",
          "true_reduced_cost": -137.15071
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0004",
          "context_hash": "080a188d2484ee3e",
          "cost": 80.486029,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5-4",
          "single_impact_class": "improved",
          "single_objective_delta": -137.116184,
          "strict_replacement_by_cost": false,
          "task_set": "4,5,8",
          "true_reduced_cost": -137.15071
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0001",
          "case_id": "capture_case_0007",
          "context_hash": "080a188d2484ee3e",
          "cost": 80.486029,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "8-5-4",
          "single_impact_class": "improved",
          "single_objective_delta": -137.116184,
          "strict_replacement_by_cost": false,
          "task_set": "4,5,8",
          "true_reduced_cost": -137.15071
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
      ],
      "key": [
        "4,5,8"
      ],
      "label_counts": {
        "improved": 7,
        "noop": 3
      },
      "row_count": 10
    },
    {
      "context_count": 5,
      "dataset_count": 3,
      "datasets": [
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_counterfactual_target_capture_dp1000_tranq20_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0000",
          "case_id": "capture_case_0020",
          "context_hash": "d60fcf4b919b7d22",
          "cost": 83.933862,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-18-5",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,18",
          "true_reduced_cost": -128.547499
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0000",
          "case_id": "capture_case_0024",
          "context_hash": "d60fcf4b919b7d22",
          "cost": 83.933862,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-18-5",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,18",
          "true_reduced_cost": -128.547499
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0000",
          "case_id": "capture_case_0028",
          "context_hash": "d60fcf4b919b7d22",
          "cost": 83.933862,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "12-18-5",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,18",
          "true_reduced_cost": -128.547499
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0007",
          "case_id": "capture_case_0002",
          "context_hash": "7ca23eb07bf4da54",
          "cost": 94.607382,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_tranq20_20260613",
          "instance": "tranquillitatis_balmer_like_20km_tasks20_01_seed21000",
          "new_task_set": true,
          "sequence": "18-5-12",
          "single_impact_class": "improved",
          "single_objective_delta": -23.4311445,
          "strict_replacement_by_cost": false,
          "task_set": "5,12,18",
          "true_reduced_cost": -34.8665505
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "tranquillitatis_balmer_like_20km_tasks20_01_seed21000"
      ],
      "key": [
        "5,12,18"
      ],
      "label_counts": {
        "improved": 1,
        "noop": 6
      },
      "row_count": 7
    },
    {
      "context_count": 3,
      "dataset_count": 2,
      "datasets": [
        "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "root_cause_target002_capture_pt03_r3_20260613"
      ],
      "example_rows": [
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0002",
          "context_hash": "3c36c602289637b4",
          "cost": 84.387441,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -73.864202
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0005",
          "context_hash": "3c36c602289637b4",
          "cost": 84.387441,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -73.864202
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0008",
          "context_hash": "3c36c602289637b4",
          "cost": 84.387441,
          "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "noop",
          "single_objective_delta": 0.0,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -73.864202
        },
        {
          "active_support_changing": false,
          "candidate_id": "journey_0004",
          "case_id": "capture_case_0002",
          "context_hash": "827ddca748a70f26",
          "cost": 88.035274,
          "impact_dataset": "root_cause_target002_capture_pt03_r3_20260613",
          "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
          "new_task_set": true,
          "sequence": "14-12-4",
          "single_impact_class": "improved",
          "single_objective_delta": -27.407912,
          "strict_replacement_by_cost": false,
          "task_set": "4,12,14",
          "true_reduced_cost": -72.927452
        }
      ],
      "instances": [
        "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
      ],
      "key": [
        "4,12,14"
      ],
      "label_counts": {
        "improved": 3,
        "noop": 3
      },
      "row_count": 6
    }
  ]
}
```

## 解释

相同 task-set / sequence / online flag 形态在不同 context 中同时出现 improved 和 noop label，说明列局部形态不足以决定 addition-before impact。selector 必须显式处理 context / RMP trajectory。

因此，根因不能简化成“某类 task-set 或 sequence 一定有用”。
同一列形态在不同 context / dataset 下会变成不同 impact label，
production selector 必须通过 context / instance / dataset holdout，
且不能只依赖列局部特征。
