# Root Cause Selector Next Feature Gate 报告

日期：2026-06-14

## 目的

本报告只读现有 selector / active-basis / context sufficiency summary，
把下一步 production selector 前的特征门槛写成机器可复查字段。
它不运行 BPC / pricing / RMP / Pulse，也不改变 worker、certificate 或 solver 默认行为。

## 机器字段

```text
root_cause_selector_next_feature_gate = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_next_feature_gate_audited
selector_next_feature_gate_status = blocked_until_extended_context_features_and_holdout
false_positive_count = 2
strongest_noop_true_reduced_cost = -128.547499
robust_single_feature_selector_count = 0
robust_multifeature_model_count = 0
collection_ready_for_selector_holdout = false
collection_missing_expected_context_count = 1
all_checks_pass = true
```

## 结论

当前证据支持继续做 calibration-only selector holdout 和上下文字段补强，但不支持把 true-RC 阈值、new-task-set、active-basis scalar 或现有 enriched multifeature model 作为 production gate。下一步必须补充 pool/forbidden signature composition 与 returned-batch-vs-pool overlap 等 addition-before 上下文特征，再重新做 context/instance/dataset holdout。

## Blocked Feature Families

```json
[
  {
    "evidence": {
      "strongest_noop_true_reduced_cost": -128.547499,
      "task20_true_rc_threshold_fp": 2
    },
    "family": "true_rc_threshold",
    "reason": "true-RC 阈值在 active-basis snapshot rows 中仍有 false positive，不能作为 production selector。",
    "status": "blocked"
  },
  {
    "evidence": {
      "task20_label_counts": {
        "improved": 10,
        "noop": 2
      },
      "task20_new_task_set_row_count": 12
    },
    "family": "new_task_set_only",
    "reason": "20-task snapshot rows 全部是 new task-set，但仍同时存在 improved 和 noop，new-task-set 本身不能判定 downstream impact。",
    "status": "blocked"
  },
  {
    "evidence": {
      "degeneracy_one_label_counts": {
        "improved": 3,
        "noop": 2
      },
      "positive_churn_label_counts": {
        "improved": 4,
        "noop": 2
      }
    },
    "family": "active_basis_scalar_only",
    "reason": "active-basis churn / degeneracy scalar 有信号但标签混合，不能单独跨 context/instance/dataset 泛化。",
    "status": "blocked"
  },
  {
    "evidence": {
      "robust_enriched_feature_count": 0,
      "robust_multifeature_count": 0,
      "robust_multifeature_model_count": 0,
      "robust_numeric_feature_count": 0,
      "robust_single_feature_selector_count": 0
    },
    "family": "current_enriched_single_or_multifeature_selector",
    "reason": "当前 enriched single-feature 与 shallow multifeature holdout 没有任何 robust all-holdout selector/model。",
    "status": "blocked"
  }
]
```

## Missing Or Required Feature Families

```json
[
  {
    "family": "pool_signature_composition_features",
    "reason": "当前证据显示 active_hash 和 aggregate/proxy 字段不足以区分 pool/forbidden/returned-batch 分叉，需要更细的可泛化上下文表示。",
    "status": "required_before_production_selector"
  },
  {
    "family": "forbidden_signature_pressure_features",
    "reason": "当前证据显示 active_hash 和 aggregate/proxy 字段不足以区分 pool/forbidden/returned-batch 分叉，需要更细的可泛化上下文表示。",
    "status": "required_before_production_selector"
  },
  {
    "family": "returned_batch_vs_pool_overlap_features",
    "reason": "当前证据显示 active_hash 和 aggregate/proxy 字段不足以区分 pool/forbidden/returned-batch 分叉，需要更细的可泛化上下文表示。",
    "status": "required_before_production_selector"
  },
  {
    "family": "active_basis_full_snapshot_features",
    "reason": "当前证据显示 active_hash 和 aggregate/proxy 字段不足以区分 pool/forbidden/returned-batch 分叉，需要更细的可泛化上下文表示。",
    "status": "required_before_production_selector"
  },
  {
    "family": "recent_rmp_trajectory_features",
    "reason": "当前证据显示 active_hash 和 aggregate/proxy 字段不足以区分 pool/forbidden/returned-batch 分叉，需要更细的可泛化上下文表示。",
    "status": "required_before_production_selector"
  }
]
```

## Allowed Next Actions

```json
[
  "collect_no_certificate_effect_selector_holdout_contexts",
  "add_pool_signature_composition_features",
  "add_forbidden_signature_pressure_features",
  "add_returned_batch_vs_pool_overlap_features",
  "rerun_context_instance_dataset_holdout"
]
```

## Forbidden Next Actions

```json
[
  "default_worker",
  "official_certificate_gate",
  "production_bpc_ab_before_selector_holdout",
  "selector_using_post_addition_or_hindsight_features",
  "simple_true_rc_or_new_task_set_rule_as_production_gate"
]
```

## Checks

```json
{
  "active_basis_snapshot_has_false_positive_rows": true,
  "collection_not_ready_for_selector_holdout": true,
  "context_gap_current": true,
  "enriched_multifeature_has_no_robust_model": true,
  "enriched_single_feature_has_no_robust_selector": true,
  "forbidden_actions_block_production_shortcuts": true,
  "missing_expected_context_remains": true,
  "snapshot_signal_has_no_perfect_single_feature_rule": true
}
```