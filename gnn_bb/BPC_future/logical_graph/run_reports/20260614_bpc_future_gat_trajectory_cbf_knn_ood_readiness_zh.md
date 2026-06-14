# GAT + CBF kNN/OOD Readiness 审计报告

日期：2026-06-14

## 目的

确认现有 GAT 是否可以进入 CBF/kNN/OOD 生产化链路。该审计只读现有
manifest、checkpoint 和 validation summary，不运行 BPC / pricing / RMP，
不生成列，也不产生 certificate 或 official bound。

## 机器字段

```text
gat_cbf_knn_ood_readiness = current
status = gat_cbf_knn_ood_readiness_audited
diagnostic_only = true
runs_bpc_or_pricing = false
official_bound_effect = false
embedding_candidate_ready = true
production_ready = false
all_checks_pass = true
```

## 关系结论

- GAT 的正确角色是 trajectory / residual-family embedding 或 impact predictor。
- kNN+OOD 的正确角色是 conservative safety shell。
- GAT 不能成为 pricing oracle、certificate source 或 official lower-bound source。
- kNN/OOD 判为 unsafe 的 true-RC negative column 只能进入 delay queue，不能永久丢弃。

## 当前审计结论

```json
{
  "checkpoint_contract": {
    "checkpoint_can_certificate": false,
    "checkpoint_load_error": null,
    "checkpoint_missing": false,
    "exactness_contract": "Trajectory CBF impact predictor only; never a pricing oracle, certificate source, official lower-bound source, or permanent filter for true-RC negative columns.",
    "has_embedding_model_config": true,
    "has_exactness_contract": true,
    "has_horizon_cbf_target": true,
    "model_config": {
      "candidate_feature_dim": 10,
      "context_feature_dim": 17,
      "dropout": 0.05,
      "heads": 4,
      "hidden_dim": 32,
      "node_dim": 9,
      "num_gnn_layers": 1,
      "option_dim": 10,
      "option_hidden_dim": 32,
      "pair_edge_dim": 32,
      "selector_hidden_dim": 32,
      "use_layer_norm": true
    },
    "selector_class_names": [
      "skip",
      "add",
      "abstain"
    ],
    "train_instances": [
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
      "apollo15_20km_random-wave_randomtw_tasks020_02_seed61102",
      "apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000",
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821",
      "tranquillitatis_balmer_like_20km_tasks10_01_seed11000"
    ],
    "validation_instances": [
      "apollo15_20km_random-wave_randomtw_tasks020_01_seed61000",
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206",
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410"
    ],
    "version": "context_aware_trajectory_cbf_gat_v1"
  },
  "embedding_candidate_ready": true,
  "gat_embedding_validation_contract": {
    "capture_validation_available": true,
    "checks_pass": true,
    "delay_queue_guard_present": true,
    "evidence_source": "capture_validation",
    "false_positive": 0,
    "no_certificate_effect": true,
    "precision": 1.0,
    "predicted_positive": 4,
    "production_ready": false,
    "recall": 0.8,
    "summary_missing": false,
    "validation_candidate_ready": true,
    "validation_row_count": 8
  },
  "knn_ood_shell_contract": {
    "decision_reason_counts": {
      "delay_neighbor_unsafe_fraction": 3,
      "delay_probability_below_threshold": 5
    },
    "false_positive": 0,
    "has_productivity_signal": false,
    "predicted_positive": 0,
    "production_ready": false,
    "safety_shell_checks_pass": true,
    "summary_missing": false,
    "validation_candidate_ready": false,
    "validation_row_count": 8
  },
  "production_blockers": [
    "no_5_10_no_regression_bpc_ab_yet",
    "no_20_task_wall_time_roi_ab_yet",
    "no_online_opt_in_solver_integration_yet"
  ],
  "production_ready": false,
  "selector_dataset_contract": {
    "column_level_add_skip_dataset": false,
    "has_horizon_cbf_label": true,
    "instance_count": 23,
    "label_counts": {
      "add": 34,
      "skip": 102
    },
    "manifest_missing": false,
    "manifest_schema_version": "gat_trajectory_cbf_dataset_manifest_v1",
    "ready_for_trajectory_gat_training": true,
    "sample_count": 136,
    "summary_missing": false,
    "summary_schema_version": "gat_trajectory_cbf_dataset_summary_v1",
    "trajectory_horizon_cbf_dataset": true
  },
  "trajectory_dataset_contract": {
    "checks_pass": true,
    "diagnostic_only": true,
    "has_horizon_labels": true,
    "horizon_cbf_feasible_count": 36,
    "horizon_cbf_infeasible_count": 103,
    "min_rows": 100,
    "no_certificate_effect": true,
    "production_ready": false,
    "row_count": 139,
    "schema_version": "cbf_trajectory_gate_dataset_v1",
    "summary_missing": false,
    "trajectory_rows_sufficient": true
  }
}
```

## 下一步

- run audit-only 5/10 no-regression and 20-sector-wave ROI smoke before any online effect
- keep certificate and official lower-bound paths on exact final judge only
