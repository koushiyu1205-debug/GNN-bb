# Selector Holdout Gap Matrix 报告

日期：2026-06-14

## 目的

本报告扫描现有 candidate impact CSV，量化 addition-before selector
仍缺哪些 label/schema/context 组合。它不运行 BPC / pricing / RMP / Pulse。

## 机器字段

```text
selector_holdout_gap_matrix = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_gap_matrix_audited
total_candidate_row_count = 630
complete_snapshot_row_count = 62
complete_snapshot_label_counts = {'improved': 59, 'noop': 3}
complete_explicit_forbidden_row_count = 48
complete_explicit_forbidden_label_counts = {'improved': 48}
recommended_next_stage = collect_negative_and_mixed_full_snapshot_contexts
all_checks_pass = true
```

## 结论

当前缺口已经不是字段完全不可得：component payload rows 具备完整 active-basis 和 explicit forbidden payload。但这些 48 行全是 improved，complete explicit forbidden rows 也全是 improved；base 280 行又没有完整 full-snapshot。因此 production selector 的剩余缺口是负例/混合 context 与 full-snapshot schema 的交叉覆盖不足。

## Source summaries

```json
{
  "active_basis_snapshot_smoke": {
    "active_basis_churn_nonempty_count": 14,
    "complete_snapshot_and_explicit_forbidden_label_counts": {},
    "complete_snapshot_and_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {
      "improved": 11,
      "noop": 3
    },
    "complete_snapshot_row_count": 14,
    "context_count": 14,
    "dataset_count": 5,
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "instance_count": 7,
    "label_counts": {
      "improved": 11,
      "noop": 3
    },
    "rmp_degeneracy_pressure_nonempty_count": 14,
    "row_count": 14
  },
  "base_replay_selector": {
    "active_basis_churn_nonempty_count": 0,
    "complete_snapshot_and_explicit_forbidden_label_counts": {},
    "complete_snapshot_and_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_count": 28,
    "dataset_count": 1,
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "instance_count": 4,
    "label_counts": {
      "improved": 209,
      "noop": 71
    },
    "rmp_degeneracy_pressure_nonempty_count": 0,
    "row_count": 280
  },
  "component_payload_addition_before": {
    "active_basis_churn_nonempty_count": 48,
    "complete_snapshot_and_explicit_forbidden_label_counts": {
      "improved": 48
    },
    "complete_snapshot_and_explicit_forbidden_row_count": 48,
    "complete_snapshot_label_counts": {
      "improved": 48
    },
    "complete_snapshot_row_count": 48,
    "context_count": 4,
    "dataset_count": 1,
    "explicit_forbidden_label_counts": {
      "improved": 48
    },
    "explicit_forbidden_row_count": 48,
    "instance_count": 1,
    "label_counts": {
      "improved": 48
    },
    "rmp_degeneracy_pressure_nonempty_count": 48,
    "row_count": 48
  },
  "counterfactual_replay_dataset": {
    "active_basis_churn_nonempty_count": 0,
    "complete_snapshot_and_explicit_forbidden_label_counts": {},
    "complete_snapshot_and_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_count": 22,
    "dataset_count": 6,
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "instance_count": 4,
    "label_counts": {
      "improved": 155,
      "noop": 60
    },
    "rmp_degeneracy_pressure_nonempty_count": 0,
    "row_count": 215
  },
  "other": {
    "active_basis_churn_nonempty_count": 0,
    "complete_snapshot_and_explicit_forbidden_label_counts": {},
    "complete_snapshot_and_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_count": 7,
    "dataset_count": 1,
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "instance_count": 1,
    "label_counts": {
      "improved": 62,
      "noop": 11
    },
    "rmp_degeneracy_pressure_nonempty_count": 0,
    "row_count": 73
  }
}
```

## Gap items

```json
[
  {
    "evidence": {
      "base_complete_snapshot_row_count": 0,
      "base_row_count": 280
    },
    "gap_id": "base_selector_rows_have_no_full_snapshot",
    "required_next_evidence": "重新采集或重放 no-certificate-effect selector rows，必须带完整 active-basis snapshot 和加列前 RMP trajectory 字段。",
    "status": "blocking"
  },
  {
    "evidence": {
      "component_complete_explicit_label_counts": {
        "improved": 48
      },
      "component_label_counts": {
        "improved": 48
      },
      "component_row_count": 48
    },
    "gap_id": "component_payload_rows_are_positive_only",
    "required_next_evidence": "采集同类 component payload 下的 noop / false-positive / low-impact rows；否则只能校准正例，不能训练生产 selector。",
    "status": "blocking"
  },
  {
    "evidence": {
      "complete_snapshot_context_mix": {
        "context_count": 17,
        "mixed_label_context_count": 0,
        "mixed_label_context_samples": [],
        "noop_only_context_count": 3,
        "positive_only_context_count": 14
      },
      "complete_snapshot_label_counts": {
        "improved": 59,
        "noop": 3
      },
      "complete_snapshot_row_count": 62
    },
    "gap_id": "complete_snapshot_rows_label_mix_too_sparse",
    "required_next_evidence": "补充 full-snapshot improved/noop mixed contexts；不能只增加 positive rows 或单类 context。",
    "status": "blocking"
  },
  {
    "evidence": {
      "complete_explicit_context_mix": {
        "context_count": 4,
        "mixed_label_context_count": 0,
        "mixed_label_context_samples": [],
        "noop_only_context_count": 0,
        "positive_only_context_count": 4
      },
      "complete_explicit_label_counts": {
        "improved": 48
      },
      "complete_explicit_row_count": 48
    },
    "gap_id": "complete_explicit_forbidden_rows_have_no_negative_label",
    "required_next_evidence": "需要 explicit forbidden/pool payload 同时覆盖 improved 和 noop；否则 forbidden pressure 只能解释正例，不能学习拒绝条件。",
    "status": "blocking"
  },
  {
    "evidence": {
      "selector_ready_proxy_context_mix": {
        "context_count": 17,
        "mixed_label_context_count": 0,
        "mixed_label_context_samples": [],
        "noop_only_context_count": 3,
        "positive_only_context_count": 14
      },
      "selector_ready_proxy_row_count": 62
    },
    "gap_id": "production_ab_still_requires_selector_and_5_10_20_gates",
    "required_next_evidence": "selector 通过 context/instance/dataset holdout 后，仍必须先跑 5/10 full no-regression，再跑 selected 20 hard-repeat speedup。",
    "status": "blocking"
  }
]
```

## Checks

```json
{
  "active_snapshot_rows_present": true,
  "base_rows_have_no_full_snapshot": true,
  "base_selector_rows_present": true,
  "candidate_rows_exist": true,
  "complete_explicit_rows_positive_only": true,
  "complete_snapshot_rows_have_sparse_noops": true,
  "component_rows_complete_and_explicit": true,
  "component_rows_positive_only": true,
  "component_rows_present": true,
  "diagnostic_not_solver_run": true,
  "has_blocking_gap_items": true
}
```
