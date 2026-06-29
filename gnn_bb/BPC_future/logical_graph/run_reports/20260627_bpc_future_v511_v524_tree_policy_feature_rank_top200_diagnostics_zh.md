# V511-V524 Tree-Policy Branch Score 诊断总结

日期：2026-06-27

## 背景

本轮继续推进 branch score 主线：让 GAT 学 Ryan-Foster pair 对完整 proof tail 闭环时间的影响。所有产物仍是 `diagnostic_only / production_ready=false`，只影响离线 score map；没有接入默认求解，也不产生 official bound、certificate 或剪枝依据。

## 已实现修改

1. 修复 tree-policy 数据构造的候选特征缺失：
   - `build_gat_tree_policy_event_dataset.py` 现在会从 `top/priority_top` 中回填 selected pair 的真实候选特征。
   - 之前大量训练样本的 `same_mass/fractionality/child width` 等特征实际为 0，模型主要在学 rank/context shortcut。

2. 新增 top200 context competitor 扩展脚本：
   - `expand_gat_tree_policy_context_competitors.py`
   - 从成功 policy 的同一 branch context 中扩展低权重 hard negative。
   - V514：保留 29 个强正例、52 个严格 hard negative，新增 885 个 top200 低权重 context competitor。

3. 去掉 tree-policy 的 rank shortcut：
   - 训练和导出时，`branch_rank_in_top` / `branch_rank_in_priority_top` 均对模型置 0。
   - 输出 score rows 仍保留原始 rank 字段用于诊断。

4. 修复训练切分：
   - `validation_fraction=0.0` 现在真正表示全量训练，不再强制留 1 个 instance 做 validation。

5. 增加测试：
   - 候选特征回填测试。
   - top200 competitor 扩展测试。
   - validation_fraction=0 的切分测试。

## 关键离线结果

### V513：feature-filled，但仍使用旧 context competitor

seed61001 已知成功路径排名：

```text
node0 target [5,19]  rank 8
node1 target [8,12]  rank 12
node2 target [13,19] rank 2
```

结论：补齐候选特征后，模型不再完全靠空特征，但仍不能复现成功路径。

### V517：top200 competitor，但仍保留 rank 特征

结果明显退化：

```text
node0 target [5,19]  rank 14
node1 target [8,12]  rank 8
node2 target [13,19] rank 22
```

结论：`rank_in_top` 不是可移植因果特征。top200 负例扩展后，模型反而学到 rank shortcut。

### V520：top200 + rank-neutral，pairwise 加权

这是目前离线最好的一版：

```text
node0 target [5,19]  rank 1
node1 target [8,12]  rank 7
node2 target [13,19] rank 3
```

结论：rank-neutral 后 root 成功 pair 能排到第一，说明方向是对的；但 depth1 仍不能稳定选中成功 pair，因此不应进入真实 600s smoke。

### V522/V524：更强 pairwise / 真全量训练

没有继续改善：

```text
V522: node0 rank 7, node1 rank 4, node2 rank 4
V524: node0 rank 3, node1 rank 12, node2 rank 4
```

结论：当前数据和模型已经不是简单“训练久一点”能解决；强 pairwise 会过拟合少数 family/depth 模式，不能稳定重现已知成功路径。

## 当前判断

V490 证明了 score-map policy 确实能把一个 600s 失败实例变成 OPTIMAL，但 V511-V524 说明：当前监督信号还不能让 GAT 泛化出稳定的 branch decision policy。

本轮最重要的发现是：

1. 旧数据里存在候选特征缺失，导致模型学错输入。
2. `priority_rank` 和 `top_rank` 都会造成策略依赖 shortcut，不能作为 tree-policy 因果特征。
3. top200 context competitor 是必要的，但它只是弱负例；不能替代真实反事实 full replay。
4. 只把一次成功 run 中的所有 selected pair 都标成正例仍然太粗，尤其 depth1/depth2 的 pair 可能是路径依赖结果，不是单 pair 因果正例。

补充 V525 controlled replay 后，结论进一步收紧：

- root 强制 `[5,19]` 后，node1 `[12,13]` 和 `[8,12]` 都能 OPTIMAL，且 `[12,13]` 更快。
- V468 baseline log 的 node1 和 root 改成 `[5,19]` 后的 node1 不是同一个上下文。
- 因此，用 baseline log 导出的静态 score map 评价或控制 changed-tree child node 是不可靠的；score key 至少需要 branch-state/context hash，或者改成在线 GAT scoring。

## 为什么不跑真实 smoke

V520 仍在 seed61001 的 node1 把 `[17,18]`、`[13,19]` 等 competitor 排在 `[8,12]` 前面。若直接 opt-in，求解器很可能在 depth1 走错分支，复现 V494 那类回归。

因此当前正确动作是 fail-closed：保留离线产物，不接入默认、不跑大规模 smoke。

## 下一步

1. 做有限 controlled replay，而不是继续扩弱标签：
   - 对 V520 在 seed61001 node1 的 top candidates 做强制 replay：
     `[17,18]`, `[13,19]`, `[12,13]`, `[8,12]`。
   - 目标是给同一 node/context 生成严格 pairwise label。

2. 把 tree-policy 标签从“整条成功路径 selected pair 全部正例”改成：
   - 同 node/context 的 strict winner / loser。
   - 使用完整 replay 或 limited fixed-expansion proof cost，不再只靠成功 run 搭桥。

3. 训练上改成 group-aware：
   - train/validation 以完整 branch context 分组。
   - pairwise ranking loss 只在有严格同 context 正负对时计算。

4. score map 使用 rank-based gate 而不是概率绝对值：
   - 当前 tree-policy 概率校准不可靠。
   - 更合理的是同一 branch event 内选 top1，并要求 top1-top2 margin 达标。

5. 真实求解 smoke 的门槛：
   - 至少已知成功路径三段都能排到 top1/top2。
   - 同 context 的已知 hard negative 被压到成功 pair 之后。
   - score rows 仍保持 `production_ready=false`，只作为 opt-in。

## 验证

已通过：

```text
python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_training \
  BPC_future.tests.test_gat_tree_policy_event_dataset \
  BPC_future.tests.test_expand_gat_tree_policy_context_competitors
```

边界保持：

```text
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
production_ready = false
solver_default_effect = false
```
