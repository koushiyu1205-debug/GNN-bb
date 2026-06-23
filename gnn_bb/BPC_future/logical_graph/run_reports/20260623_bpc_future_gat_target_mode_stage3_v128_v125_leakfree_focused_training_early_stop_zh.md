# BPC_future GAT target-mode Stage 3 v128 leak-free focused training 早停报告

日期：2026-06-23

## 结论

v128 是负结果，已在 epoch `3` 后早停。

本轮只做一个隔离实验：保持 v125 的训练配置基本不变，但把 focused training
selector 改成 seed13 train-only；full focused rows 仍只用于 gate。目的不是寻找
更宽阈值，而是验证“v125 的 focused 表现是否依赖把 validation focused rows 也放进
训练 loss”。

结果显示，train-only focused selector 不足以修复当前 blocker：

- epoch `2` 本地 gate 仍可行，但 focused strict 只有 `71/78=0.9103`；
- epoch `3` accepted 覆盖扩大到 `94`，但 false-delay 变成 `1.083%`，超过 `1%` 硬线；
- 前 3 个 epoch 的最好 focused strict 仍低于 v125 selected epoch2 的 `74/78`，也低于 v126 早停实验的 `73/78`；
- 因此继续跑 epoch 4-8 不值得消耗。

本轮不运行 BPC、pricing、RMP、worker 或 certificate。

## 输入与配置

```text
dataset = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
output = BPC_future/results/gat_batch_impact_training_v128_v125_leakfree_focused_training_seed13_20260623
epoch checkpoints = .../epoch_checkpoints/epoch_001.pt ... epoch_003.pt
```

关键差异：

```text
base_config = v125_v121_like
focused_pair_row_indices_file = BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_row_indices.json
focused_pair_training_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_training_row_indices.json
focused_pair_boost_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_boost_train_row_indices.json
targeted_safe_positive_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/optional_v121_train_targeted_safe_positive_row_indices.json
```

## 前 3 个 epoch

| epoch | local gate | accepted | ROI | ROI CI low | safe CI low | false-delay | false-safe | focused strict | 结论 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | true | 35 | 17.179 | 8.130 | 0.9011 | 0.00000 | 0.00000 | 57/78 = 0.7308 | focused 明显退化 |
| 2 | true | 35 | 17.829 | 8.877 | 0.9011 | 0.00722 | 0.00722 | 71/78 = 0.9103 | local 可行，但低于 v125/v126 |
| 3 | false | 94 | 7.687 | 3.856 | 0.9607 | 0.01083 | 0.01083 | 71/78 = 0.9103 | false-delay 越过 1% 硬线 |

对比参考：

| run | 最好 focused strict | 说明 |
|---|---:|---|
| v125 selected epoch2 | 74/78 = 0.9487 | local + global/scale kNN pass，但 focused 未过 |
| v125 epoch3 diagnostic | 76/78 = 0.9744 | focused 最好，但 false-delay 1.083% |
| v126 leak-free safety-balanced | 73/78 = 0.9359 | 多惩罚同时改变，负结果 |
| v128 leak-free focused-training isolated | 71/78 = 0.9103 | 单独替换 train-only selector 仍退化 |

## 与 v127 诊断的合并判断

v127 top-context feature contrast 已确认：v125 epoch2/3 的失败 pair 没有 input collision，
没有 same-context feature drift，并且当前 v119 tensor 已包含 path token、trace/slack scalar
以及 per-candidate active-basis / branch / cut interaction。

因此当前 blocker 不是“模型完全看不到正负差异”，也不是“继续把 validation failure row
回灌进训练就能合法解决”。v128 进一步说明，只做 train-only focused selector 替换也不够。

下一步应转向模型结构和训练口径：

1. 设计 context-local pairwise ranking head 或 pair-context comparator，让同 context 正负
   batch 的差异直接进入 ranking 表示，而不是只靠两个独立 sample score 的 margin loss；
2. 保持 train/validation focused rows 分离，不能用 validation failure rows 做 boost；
3. 继续用 full focused rows 做 gate，目标仍是 `78/78`；
4. 新候选必须同时重跑 full focused gate 与 v124 one-unsafe-neighbor global/scale kNN/OOD。

## Stage 状态

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
```

当前 blocker 不变：

- focused same-context pair gate 未达到 `78/78`；
- Stage 4 shadow / opt-in 未运行；
- 5/10 no-regression 与 20-task ROI 未绑定当前 checkpoint；
- GAT/kNN/OOD 不能提供 official lower bound 或 exact certificate。

## Exactness Boundary

本轮只运行离线训练前 3 个 epoch，并保存 per-epoch diagnostic checkpoints：

- 不运行 BPC/pricing/RMP；
- 不改变 pricing universe；
- 不改变 lower bound、certificate 或 exact closure；
- 不启用 production/default config；
- true-RC negative columns 必须保持 eventually reachable；
- final optimality proof 仍只能来自 exact pricing full closure。
