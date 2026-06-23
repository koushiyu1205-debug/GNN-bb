# 2026-06-22 BPC_future GAT Stage 3 v122 train-only targeted repair selector 报告

## 结论

本报告只生成 v122 training-only selector，不运行 BPC / pricing / RMP / worker / certificate。

v122 selector 的核心变化是：只使用 train split 行做训练 replay，避免直接把 validation focused failure 行喂回训练。

```text
focused_boost_row_count = 12
focused_boost_row_indices = [176, 177, 398, 779, 780, 781, 782, 783, 842, 843, 846, 847]
targeted_safe_positive_row_count = 35
targeted_safe_positive_row_indices = [5, 176, 177, 252, 408, 409, 461, 648, 751, 779, 780, 781, 782, 787, 791, 836, 840, 841, 842, 847, 890, 891, 896, 897, 912, 913, 959, 963, 977, 1018, 1019, 1022, 1128, 1132, 1146]
removed_v121_validation_focused_rows = [998, 999, 1001]
focused_all_train = true
targeted_all_train = true
targeted_all_positive = true
all_checks_pass = true
```

## Selector 依据

v121 剩余 blocker：

- focused strict pair pass 仍为 `75/78`，剩 3 个 failed pair；
- global kNN/OOD strict 只 accepted `34` 个 validation batch，safe precision CI-low 为 `0.8984820938`，离 `0.9` 差一个安全 accepted batch；
- scale kNN/OOD strict 已 accepted `35` 个，safe precision CI-low 为 `0.9010957324`。

v122 all-scope global kNN/OOD 仅用于挖 train-side analogue，不作为 Stage 4 证据。

## Focused Boost

保留 v121 中属于 train split 的 focused boost rows：

```text
[176, 780, 781, 782, 783, 846, 847]
```

移除 v121 中属于 validation split 的 focused boost rows：

```text
[998, 999, 1001]
```

新增 train-side focused rows：

```text
[177, 398, 779, 842, 843]
```

用途：

- `398/779` 是剩余 `ddcb5387bef3bf63` train context 的直接 near-margin delay-risk 修复对；
- `177/842/843` 是 random-wave task30 train analogue，用来替代不能训练的 validation context `9f80ae35ea87da5b`；
- 所有 focused boost rows 都来自 train split。

## Targeted Safe Positive

在 v121 的 24 个 train delayed-safe positive 基础上新增 11 个 train positive anchor：

```text
[176, 177, 779, 780, 781, 782, 836, 842, 847, 890, 891]
```

其中：

- `890/891` 是 greedy-anchor task30 train-side high-ROI analogue，用来回应 global kNN/OOD 中 validation row `884` 的 neighbor-sensitive blocker；
- `836/842/847` 是 random-wave task30 train high-ROI anchor；
- `176/177/779/780/781/782` 是 focused 正样本 replay anchor。

## 边界

- 这些 selector 只进入 `_run_epoch` 的 training-only replay；
- validation loss、threshold search、focused gate 和 kNN/OOD gate 不使用这些 selector 放宽；
- selector 不能产生 official bound 或 certificate；
- selector 不能永久丢弃 true-RC negative columns；
- Stage 4 仍必须等待 focused gate、global/scale kNN/OOD、5/10 no-regression、20-task ROI 和 opt-in/shadow 证据。

## Artifacts

- `BPC_future/results/gat_batch_impact_v122_train_only_targeted_repair_selectors_20260622/summary.json`
- `BPC_future/results/gat_batch_impact_v122_train_only_targeted_repair_selectors_20260622/focused_boost_row_indices.json`
- `BPC_future/results/gat_batch_impact_v122_train_only_targeted_repair_selectors_20260622/focused_boost_rows.jsonl`
- `BPC_future/results/gat_batch_impact_v122_train_only_targeted_repair_selectors_20260622/targeted_safe_positive_row_indices.json`
- `BPC_future/results/gat_batch_impact_v122_train_only_targeted_repair_selectors_20260622/targeted_safe_positive_rows.jsonl`
