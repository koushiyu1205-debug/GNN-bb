# GAT Batch Impact Training 报告

日期：2026-06-15

## 目的

训练 offline batch-impact GAT checkpoint，目标是 high-precision / high-ROI
admission scheduling，而不是普通分类 F1。该训练不运行 BPC / pricing / RMP，
不生成 certificate 或 official lower bound。

## 机器字段

```text
gat_batch_impact_training = current
status = gat_batch_impact_trained
diagnostic_only = true
runs_bpc_or_pricing = false
sample_count = 68
candidate_count = 1410
family_counts = {'sector-wave': 68}
task_count_counts = {'20': 68}
checkpoint_selection = deployment_gate_first_then_utility_roi_loss
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['accepted_batch_roi_below_baseline_margin', 'knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'major_family_coverage_incomplete', 'online_shadow_and_opt_in_ab_not_run', 'safe_precision_below_threshold_or_no_accepted_batches', 'stage2_family_coverage_missing_random_wave_or_greedy_anchor', 'stage3_effective_sample_count_below_200']
production_ready = false
default_enabled = false
all_checks_pass = true
```

## Deployment Metrics

```json
{
  "family_holdout_metrics": {
    "family_count": 1,
    "family_holdout_min_accepted_roi": 0.3550373798934743,
    "family_holdout_min_precision": 0.8125,
    "per_family": {
      "sector-wave": {
        "accepted_batch_count": 16,
        "accepted_batch_roi": 0.3550373798934743,
        "safe_precision": 0.8125,
        "total_batches": 16
      }
    }
  },
  "split": {
    "mode": "instance_path",
    "train_context_count": 52,
    "train_family_counts": {
      "sector-wave": 52
    },
    "train_instances": [
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json"
    ],
    "validation_context_count": 16,
    "validation_family_counts": {
      "sector-wave": 16
    },
    "validation_instances": [
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json"
    ]
  },
  "threshold_search": {
    "best_rejected_reasons": [
      "safe_precision_below_threshold_or_no_accepted_batches",
      "accepted_batch_roi_below_baseline_margin",
      "major_family_coverage_incomplete",
      "stage3_effective_sample_count_below_200",
      "knn_ood_audit_missing"
    ],
    "candidate_count": 1,
    "feasible_threshold_count": 0,
    "selected_metrics": {
      "accepted_batch_count": 16,
      "accepted_batch_precision": 0.8125,
      "accepted_batch_rate": 1.0,
      "accepted_batch_roi": 0.3550373798934743,
      "checkpoint_gate_pass": false,
      "checkpoint_gate_reject_reasons": [
        "safe_precision_below_threshold_or_no_accepted_batches",
        "accepted_batch_roi_below_baseline_margin",
        "major_family_coverage_incomplete",
        "stage3_effective_sample_count_below_200",
        "knn_ood_audit_missing"
      ],
      "coverage_non_ood": 1.0,
      "delay_label_count": 19,
      "delay_rate": 0.0,
      "expected_trajectory_utility": 0.3925373798934743,
      "false_high_priority_on_delay": 0.0,
      "false_high_priority_on_delay_count": 0,
      "false_safe_rate_label_unsafe": 0.0,
      "false_safe_rate_union": 0.0,
      "family_holdout_min_accepted_roi": 0.3550373798934743,
      "family_holdout_min_precision": 0.8125,
      "high_priority_precision": 1.0,
      "high_priority_prediction_count": 261,
      "high_priority_true_positive_count": 261,
      "safe_precision": 0.8125,
      "threshold": 0.47110044956207275,
      "total_batches": 16
    }
  },
  "train_deployment_metrics": {
    "accepted_batch_count": 52,
    "accepted_batch_precision": 0.8269230769230769,
    "accepted_batch_rate": 1.0,
    "accepted_batch_roi": 0.3194995714226164,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "safe_precision_below_threshold_or_no_accepted_batches",
      "accepted_batch_roi_below_baseline_margin",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high",
      "major_family_coverage_incomplete",
      "stage3_effective_sample_count_below_200",
      "knn_ood_audit_missing"
    ],
    "coverage_non_ood": 1.0,
    "delay_label_count": 72,
    "delay_rate": 0.0,
    "expected_trajectory_utility": 0.2877688021918472,
    "false_high_priority_on_delay": 0.2916666666666667,
    "false_high_priority_on_delay_count": 21,
    "false_safe_rate_label_unsafe": 1.0,
    "false_safe_rate_union": 1.0,
    "family_holdout_min_accepted_roi": 0.3194995714226164,
    "family_holdout_min_precision": 0.8269230769230769,
    "high_priority_precision": 0.9778714436248683,
    "high_priority_prediction_count": 949,
    "high_priority_true_positive_count": 928,
    "safe_precision": 0.8269230769230769,
    "threshold": 0.47110044956207275,
    "total_batches": 52
  },
  "validation_deployment_metrics": {
    "accepted_batch_count": 16,
    "accepted_batch_precision": 0.8125,
    "accepted_batch_rate": 1.0,
    "accepted_batch_roi": 0.3550373798934743,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "safe_precision_below_threshold_or_no_accepted_batches",
      "accepted_batch_roi_below_baseline_margin",
      "major_family_coverage_incomplete",
      "stage3_effective_sample_count_below_200",
      "knn_ood_audit_missing"
    ],
    "coverage_non_ood": 1.0,
    "delay_label_count": 19,
    "delay_rate": 0.0,
    "expected_trajectory_utility": 0.3925373798934743,
    "false_high_priority_on_delay": 0.0,
    "false_high_priority_on_delay_count": 0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.0,
    "family_holdout_min_accepted_roi": 0.3550373798934743,
    "family_holdout_min_precision": 0.8125,
    "high_priority_precision": 1.0,
    "high_priority_prediction_count": 261,
    "high_priority_true_positive_count": 261,
    "safe_precision": 0.8125,
    "threshold": 0.47110044956207275,
    "total_batches": 16
  }
}
```

## 边界

- checkpoint selection 先看 deployment gate，再看 utility / ROI / loss；
- HIGH_PRIORITY precision、safe precision、accepted batch ROI、false-safe、accepted count 都是硬门槛；
- 当前 checkpoint 仍 `production_ready=false`；
- kNN/OOD holdout、5/10 no-regression、20-task wall-time ROI、online opt-in A/B 通过前，不能进入 Stage 4；
- DELAY_QUEUE 只能延迟 true-RC negative，不能替代 final exact pricing certificate。
