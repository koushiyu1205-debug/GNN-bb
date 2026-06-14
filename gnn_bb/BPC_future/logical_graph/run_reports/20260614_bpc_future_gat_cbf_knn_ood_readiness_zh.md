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
embedding_candidate_ready = false
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
    "exactness_contract": "Heuristic RMP-impact predictor only; never a pricing oracle, certificate source, or official lower-bound source.",
    "has_embedding_model_config": true,
    "has_exactness_contract": true,
    "has_horizon_cbf_target": false,
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
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001"
    ],
    "validation_instances": [
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
    ],
    "version": "context_aware_column_selector_v1"
  },
  "embedding_candidate_ready": false,
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
    "gat_checkpoint_is_column_level_add_skip_not_trajectory_cbf",
    "gat_training_contract_missing_label_horizon_cbf_feasible",
    "sector_wave_knn_ood_smoke_has_no_high_priority_productivity_signal",
    "no_gat_embedding_knn_ood_external_validation_yet",
    "no_5_10_no_regression_bpc_ab_yet",
    "no_20_task_wall_time_roi_ab_yet",
    "no_online_opt_in_solver_integration_yet"
  ],
  "production_ready": false,
  "selector_dataset_contract": {
    "column_level_add_skip_dataset": true,
    "has_horizon_cbf_label": false,
    "instance_count": 2,
    "label_counts": {
      "add": 183,
      "skip": 70
    },
    "manifest_missing": false,
    "manifest_schema_version": "gnn_column_selector_dataset_v1",
    "ready_for_trajectory_gat_training": false,
    "sample_count": 253,
    "summary_missing": false,
    "summary_schema_version": "gnn_column_selector_dataset_summary_v1"
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

- build trajectory-labeled GAT dataset with label_horizon_cbf_feasible targets
- train GAT impact/barrier head or export candidate embeddings for kNN/OOD
- validate GAT embeddings with kNN/OOD on independent sector-wave captures
- run audit-only 5/10 no-regression and 20-sector-wave ROI smoke before any online effect
