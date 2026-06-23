# BPC_future GAT target-mode Stage 3 v123 leak-free focused selector

日期：2026-06-22

## 结论

v123 的目的不是放宽 gate，而是修正 v120/v121/v122 训练中的 focused row split 混用问题。

使用训练脚本 seed13 / validation_fraction=0.25 复算 split 后：

- v120 focused hard set 总数：102 行；
- 其中 train：81 行；
- 其中 validation：21 行；
- v121 focused boost 总数：10 行，其中 3 行是 validation：`998, 999, 1001`；
- v121 targeted safe-positive 总数：24 行，全部是 train。

因此 v123 的 selector 固定为：

- focused gate 仍使用完整 102 行 hard set；
- focused training loss 只使用 81 行 train focused rows；
- focused boost 只使用 v121 的 7 行 train boost rows；
- targeted safe-positive replay 保留 v121 的 24 行 train rows；
- 不使用 v122 的 35 行大范围 targeted positive replay，因为 v122 已经证明会破坏 focused same-context ranking。

## 输出

- selector summary: `BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/summary.json`
- focused gate rows: `BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_gate_row_indices.json`
- focused training rows: `BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_training_row_indices.json`
- optional v121 train focused boost: `BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_boost_train_row_indices.json`
- optional v121 train positives: `BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/optional_v121_train_targeted_safe_positive_row_indices.json`
- focused row audit: `BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_rows.jsonl`

## 验证要点

v123 retrain 必须同时检查：

1. focused gate 是否在完整 102 行上接近或超过 v121 的 75/78=0.9615；
2. validation local gate 是否仍满足 accepted>=35、safe CI low>=0.9、false-delay<=0.01；
3. kNN/OOD global strict 是否能从 v121 的 34 accepted 提升到 35 accepted；
4. 不得把 validation focused rows 放入 loss replay。

## exactness boundary

本 selector 只影响 offline training/audit：

- 不运行 BPC/pricing/RMP；
- 不改变 pricing universe；
- 不产生 official lower bound；
- 不产生 certificate；
- 不允许永久丢弃 true-RC negative columns；
- `diagnostic_only=true`。
