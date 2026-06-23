# 2026-06-22 BPC_future GAT Stage 3 v121 targeted repair selector 报告

## 结论

本报告只生成 v121 training-only selector，不运行 BPC / pricing / RMP / worker / certificate。

```text
focused_boost_row_count = 10
focused_boost_row_indices = [176, 780, 781, 782, 783, 846, 847, 998, 999, 1001]
train_delayed_safe_positive_candidate_count = 82
validation_delayed_safe_positive_candidate_count = 22
targeted_safe_positive_row_count = 24
targeted_safe_positive_row_indices = [5, 252, 408, 409, 461, 648, 751, 787, 791, 840, 841, 896, 897, 912, 913, 959, 963, 977, 1018, 1019, 1022, 1128, 1132, 1146]
all_checks_pass = true
```

## Selector 边界

- `focused_boost_row_indices.json` 只用于 training-only extra replay；focused gate 仍必须使用 v120/v119-clean 全量 `102` 行 selector。
- `targeted_safe_positive_row_indices.json` 只来自 all-scope audit 的 train split，避免把 validation delayed-safe rows 泄漏进训练。
- validation delayed-safe rows 只作为审计目标，不进入训练 replay。
- 这些 selector 不能生成 official bound 或 certificate。

## Train delayed-safe positive top rows

| row | family | task | ROI | batch score | threshold | context |
|---:|---|---:|---:|---:|---:|---|
| 1018 | greedy-anchor | 20 | 4.236324 | 0.600853 | 0.602469 | `67925c0d2fd4abde` |
| 791 | random-wave | 20 | 4.173969 | 0.599966 | 0.602469 | `e897b76f2888f822` |
| 461 | sector-wave | 20 | 13.568207 | 0.599417 | 0.602469 | `79fde658840fe2b8` |
| 751 | sector-wave | 20 | 13.568207 | 0.599417 | 0.602469 | `79fde658840fe2b8` |
| 1019 | greedy-anchor | 20 | 4.784814 | 0.595786 | 0.602469 | `67925c0d2fd4abde` |
| 787 | random-wave | 20 | 6.135930 | 0.595626 | 0.602469 | `08b8d772e2ab9623` |
| 1146 | sector-wave | 20 | 0.944281 | 0.594862 | 0.602469 | `9a11128d9256c3d8` |
| 912 | sector-wave | 30 | 3.912306 | 0.594829 | 0.602469 | `e4fd62c2907659d8` |
| 841 | random-wave | 30 | 28.973944 | 0.594458 | 0.602469 | `53581aa404f963e3` |
| 977 | random-wave | 20 | 6.242169 | 0.594326 | 0.602469 | `ec59d1f203f1630c` |
| 408 | sector-wave | 20 | 1.000000 | 0.594229 | 0.602469 | `b9550ffc9a42531a` |
| 1128 | sector-wave | 20 | 2.811415 | 0.594155 | 0.602469 | `1f855fbf33f8155e` |

## Validation delayed-safe positive top rows

| row | family | task | ROI | batch score | threshold | context |
|---:|---|---:|---:|---:|---:|---|
| 718 | random-wave | 20 | 0.933005 | 0.601648 | 0.602469 | `96c5f5928a47fe72` |
| 886 | greedy-anchor | 30 | 6.363499 | 0.596990 | 0.602469 | `3e620eccaac5aee0` |
| 1115 | sector-wave | 20 | 3.999467 | 0.595566 | 0.602469 | `09187873900ecefa` |
| 887 | greedy-anchor | 30 | 6.094925 | 0.595031 | 0.602469 | `3e620eccaac5aee0` |
| 580 | sector-wave | 10 | 1.664651 | 0.590281 | 0.602469 | `6c06069a613382f3` |
| 679 | sector-wave | 10 | 1.664651 | 0.590281 | 0.602469 | `6c06069a613382f3` |
| 691 | sector-wave | 10 | 1.664651 | 0.590281 | 0.602469 | `6c06069a613382f3` |
| 705 | sector-wave | 10 | 1.664651 | 0.590281 | 0.602469 | `6c06069a613382f3` |
| 715 | sector-wave | 10 | 1.664651 | 0.590281 | 0.602469 | `6c06069a613382f3` |
| 728 | sector-wave | 10 | 1.664651 | 0.590281 | 0.602469 | `6c06069a613382f3` |
| 621 | greedy-anchor | 10 | 0.694050 | 0.587359 | 0.602469 | `c9ef7d4795e923b6` |
| 1118 | greedy-anchor | 20 | 2.773889 | 0.587194 | 0.602469 | `f567a0928007db23` |

## Artifact

- `BPC_future/results/gat_batch_impact_v121_targeted_repair_selectors_20260622/summary.json`
- `BPC_future/results/gat_batch_impact_v121_targeted_repair_selectors_20260622/focused_boost_row_indices.json`
- `BPC_future/results/gat_batch_impact_v121_targeted_repair_selectors_20260622/targeted_safe_positive_row_indices.json`
- `BPC_future/results/gat_batch_impact_v121_targeted_repair_selectors_20260622/train_delayed_safe_positive_candidates.jsonl`
- `BPC_future/results/gat_batch_impact_v121_targeted_repair_selectors_20260622/validation_delayed_safe_positive_candidates.jsonl`
