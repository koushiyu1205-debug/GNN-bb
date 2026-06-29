# V607/V608 Tree-Policy Wall-Time 标签注入诊断

日期：2026-06-28

## 结论

本轮没有得到可直接进入真实求解的 branch score map。

但完成了一个关键修正：`tree_policy_event_rows` 中已有的 `capped_wall_time_gain` 现在可以显式注入到 branch-priority / wall-time 主训练头，而不是只训练 `tree_policy` 辅助头。

这一步把 V545 证明有效的完整 branch policy path 信号接到了主目标上，但当前数据分布仍不足以训练可泛化模型。

## 实现内容

修改：

- `BPC_future/scripts/build_gat_tree_policy_event_dataset.py`
- `BPC_future/tests/test_gat_tree_policy_event_dataset.py`

新增显式开关：

```text
--include-walltime-labels
```

默认行为保持不变：仍只训练 tree-policy 辅助头。

只有打开该开关时：

- strict positive / controlled replay positive 且 `capped_wall_time_gain >= 30s`：
  - `y_branch_priority = 1`
  - `branch_priority_loss_weight > 0`
  - `y_walltime_gain = capped_wall_time_gain`
  - `walltime_gain_loss_weight > 0`
- strict hard negative / controlled hard negative 且 `capped_wall_time_gain <= -30s`：
  - `y_branch_priority = 0`
  - `branch_priority_loss_weight > 0`
  - `y_counterfactual_regression = 1`
- context competitor / proof-tail right-censored：
  - 继续只作为辅助样本，不误当严格 full-run 正负例。

exact-safe 边界不变：该脚本只生成离线训练样本，不运行 BPC/pricing/RMP，不产生 official bound、certificate 或剪枝依据。

## V607 Dataset

输出：

```text
BPC_future/data/gat_branch_action_sanity/v607_tree_policy_walltime_v534_plus_v562_20260628/
```

报告：

```text
BPC_future/logical_graph/run_reports/20260628_bpc_future_gat_tree_policy_v607_walltime_dataset_zh.md
```

输入：

- `v534_tree_policy_v530_controlled_weighted_events_20260627/tree_policy_event_rows.jsonl`
- `journey_branch_impact_v562_retry_cap_seed61717_20260627/branch_impact_rows.jsonl`

关键分布：

```text
sample_count = 981
branch_priority_label_counts = {
  walltime_gain_positive: 31,
  not_walltime_gain: 4,
  aux_only_tree_policy: 946
}
tree_policy_label_counts = {
  tree_policy_positive: 31,
  tree_policy_hard_negative: 936,
  tree_policy_proof_tail_hard_negative: 14
}
```

判断：

- `31` 个 wall-time positive 来自 strict replay / controlled replay 的完整路径收益。
- 只有 `4` 个严格 wall-time hard negative，主标签负例明显不足。
- `946` 个样本仍只是 auxiliary，不应当作主 branch-priority 负例。

因此 V607 适合诊断和训练链路验证，不是 serious/production-ready 数据集。

## V608 Training

输出：

```text
BPC_future/data/gat_branch_action_sanity/v607_tree_policy_walltime_v534_plus_v562_20260628/gat_branch_action_v608_tree_walltime.pt
BPC_future/results/gat_branch_action_v608_tree_walltime_20260628/summary.json
```

训练完成：

```text
sample_count = 981
train_sample_count = 954
validation_sample_count = 27
train weighted branch rows = 35
validation weighted branch rows = 0
```

训练集 branch-priority 指标：

```text
precision = 0.8857
recall = 1.0
f1 = 0.9394
```

但 validation 的主标签 `weighted_row_count = 0`，所以 validation branch-priority 指标没有意义。

原因不是模型已经很好，而是 wall-time 主标签集中在极少数 instance 上，按 instance 切分后无法同时保证 train/validation 都有正负主标签。

## V608 Score Map 审计

在 V545 full60 logs 上导出两个 score map。

### Hybrid 模式

输出：

```text
BPC_future/results/gat_branch_action_v608_tree_walltime_20260628/score_map_v608_on_v545_full60_hybrid_top200/
```

分布：

```text
score_row_count = 18823
score_instance_count = 42
score_min = 0.5833
score_mean = 0.8526
score_max = 0.9617
score >= 0.67: 18757 rows / 42 instances
score >= 0.85: 10641 rows / 31 instances
score >= 0.90: 4896 rows / 21 instances
```

问题：

Hybrid 几乎所有候选都高分，无法作为 gate。最高分集中在 V545 仍然 `EXTERNAL_TIME_LIMIT` 的实例，例如 sector/tranquillitatis seed61718 深层 node 88。

这说明 branch-priority / wall-time 主头过度乐观，主要学习到了“深层/宽子树也给高 gain”，没有学会失败上下文抑制。

### Tree-Policy 模式

输出：

```text
BPC_future/results/gat_branch_action_v608_tree_walltime_20260628/score_map_v608_on_v545_full60_treepolicy_top200/
```

分布：

```text
score_row_count = 18823
score_instance_count = 42
score_min = 0.00139
score_mean = 0.01513
score_max = 0.03935
score >= 0.03: 1878 rows / 22 instances
score >= 0.04: 0 rows / 0 instances
```

问题：

Tree-policy 辅助头过于保守，整体分数太低，也不能直接作为 branch gate。

## 当前判断

V608 不能跑 opt-in full60，原因是两个头不一致：

- hybrid / branch-priority 头过度乐观，容易在失败实例上给高分；
- tree-policy 头过度保守，没有形成可用阈值；
- validation 主标签为空，训练指标不能证明泛化；
- 严格 hard negative 太少，不能校准失败上下文。

这不是 exact-safe 问题，而是训练数据和 loss 校准问题。所有输出仍是 diagnostic-only，不影响 solver 默认行为。

## 下一步

1. 不把 V608 作为真实求解配置。
2. 继续收集严格 hard negative，特别是：
   - V545/V608 高分但 `EXTERNAL_TIME_LIMIT` 的 state/pair；
   - deep state 中 branch-priority 高分、tree-policy 低分的冲突样本；
   - full replay 失败但模型预测 gain 很高的样本。
3. 调整训练：
   - 对 branch-priority 主头增加 hard negative / calibration loss；
   - 对 tree-policy 头使用 state-scoped positive path 的 pairwise ranking；
   - 对 right-censored proof-tail 只训练 proof-risk/child proof CPU，不直接作为 0/1 full-run 标签。
4. score gate 应拆成三档：
   - strict overlay：继续可用；
   - tree-policy model：仅做诊断；
   - wall-time generalized model：必须经过 high-score hard-negative 校准后才能 smoke。

## V609 High-Score Hard-Negative Runbook

基于 V608 hybrid score map，额外生成一个只针对高分误报的 A/B runbook：

```text
BPC_future/results/journey_branch_score_ab_runbook_v609_v608_highscore_external_20260628/
BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_branch_score_ab_runbook_v609_v608_highscore_external_zh.md
```

筛选条件：

```text
V545 status = EXTERNAL_TIME_LIMIT
wall_time >= 590s
V608 hybrid top score >= 0.95
limit = 6
```

实际得到：

```text
entry_count = 4
command_count = 8
```

4 个 high-score failure 实例：

| instance | top pair | top score |
|---|---:|---:|
| greedy/tranquillitatis seed61311 | [18, 20] | 0.9580 |
| greedy/tranquillitatis seed61635 | [18, 20] | 0.9504 |
| sector/tranquillitatis seed61410 | [18, 20] | 0.9550 |
| sector/tranquillitatis seed61718 | [13, 20] | 0.9617 |

该 runbook 只是下一轮误报验证清单，不自动运行求解，不产生 official bound 或 certificate。

## 验证

通过：

```text
python -m py_compile BPC_future/scripts/build_gat_tree_policy_event_dataset.py BPC_future/tests/test_gat_tree_policy_event_dataset.py

python -m unittest \
  BPC_future.tests.test_gat_tree_policy_event_dataset \
  BPC_future.tests.test_gat_tree_policy_strict_overlay \
  BPC_future.tests.test_expand_gat_tree_policy_context_competitors
```

结果：

```text
Ran 7 tests ... OK
```
