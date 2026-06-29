# Branch Score 主线 v456-v461 阶段报告

日期：2026-06-27

## 结论

本阶段没有达到“20 规模全量 60/60 在 600 秒内 OPTIMAL”的最终目标，但在 12-instance smoke 上取得了一个可复现的 exact-safe 改善：

- v455：4/12 OPTIMAL，capped mean 458.875s，<=200s OPTIMAL 3/12。
- v461 gated：6/12 OPTIMAL，capped mean 424.745s，<=200s OPTIMAL 3/12。
- v455 -> v461：2 个 TIMEOUT -> OPTIMAL，0 个 >5s 退化，capped mean 降低 34.130s。

有效收益来自 branch score 对 root Ryan-Foster pair 的排序改变；early branch 显式关闭，GAT/score map 没有提供 official bound、certificate 或剪枝依据。

## 本阶段做了什么

1. 生成并执行 v456 strict forced-root replay 首批 8 个任务。
   - 输入：v455 失败 context 的 positive-neighbor 候选。
   - 运行：每个 forced pair 600s full replay。
   - 结果：1 个强正例、7 个 hard negative。

2. 新增通用 delta 构建脚本。
   - 脚本：`BPC_future/scripts/build_journey_branch_forced_replay_delta_rows.py`
   - 测试：`BPC_future/tests/test_journey_branch_forced_replay_delta_rows.py`
   - 输出：`BPC_future/results/journey_branch_counterfactual_delta_v456_v455_failed8_positive_neighbor_full600_20260627/`
   - 标签：`EXTERNAL_TIME_LIMIT -> OPTIMAL` 为 strong positive；改变 root pair 后仍非最优为 hard negative。

3. 构建 v457 数据集并重训。
   - 数据集：`BPC_future/data/gat_branch_action_sanity/v457_v453_plus_v456_walltime_20260627/`
   - raw rows：222
   - training samples：140
   - wall-time positive：48
   - not wall-time gain：80
   - aux-only weak positive：12
   - 训练产物：`gat_branch_action_v457_weighted.pt`

4. 诊断 v457 纯模型。
   - v457 score range：0.5256 - 0.5472。
   - 结论：纯模型分数过窄，不能区分新正例 `[2,10]` 和 hard negative，不适合直接上线。

5. 构建 v459 conservative evidence overlay。
   - 基础：v457 score rows。
   - 过滤：只纳入 600 秒级 timeout-resolved 正例、明确 OPTIMAL-to-OPTIMAL 大幅加速正例、600 秒级非最优负例。
   - 输出：`BPC_future/results/gat_branch_action_v457_weighted_walltime_20260627/score_map_v459_conservative_delta_overlay_v455logs/`
   - 触达当前 smoke score rows：7 个 boost，27 个 suppress。

6. 跑 v461 gated smoke12。
   - score gate 真正打开：`journey_branch_candidate_score_selection_gate_enabled=true`
   - gate min score：0.67
   - max total child width：850
   - early branch：关闭

## v456 Replay 结果

首批 8 个 forced-root full replay：

```text
strong_positive = 1
changed_timeout_no_effect_hard_negative = 7
```

新增强正例：

```text
random-wave / seed61411
baseline: EXTERNAL_TIME_LIMIT 600s
forced pair: [2,10]
alternative: OPTIMAL 341.445s
gain: 258.555s
```

这说明正例确实存在，但 positive-neighbor 候选命中率仍低：8 个中只有 1 个能完整闭环。

## v461 Smoke 对比

| 指标 | v455 | v461 gated |
|---|---:|---:|
| OPTIMAL | 4/12 | 6/12 |
| non-OPT | 8/12 | 6/12 |
| capped mean | 458.875s | 424.745s |
| OPT-only mean | 176.625s | 249.489s |
| OPT-only median | 120.629s | 243.478s |
| <=200s OPTIMAL | 3/12 | 3/12 |
| p50 | 600.000s | 525.063s |
| p90 | 600.000s | 600.000s |

逐实例主要变化：

```text
tranq greedy seed61103: EXTERNAL 600.00 -> OPTIMAL 450.13, gain 149.87s
random seed61411:       EXTERNAL 600.00 -> OPTIMAL 340.83, gain 259.17s
```

已有快解基本保持：

```text
seed61001 greedy: OPTIMAL 59.04 -> 57.22
seed61414 greedy: OPTIMAL 96.15 -> 96.88
sector seed61923: OPTIMAL 406.20 -> 405.75
```

没有 >5s 退化实例。

## Gate 审计

v461 root branch candidate 日志显示：

```text
gate ok = 5
score_below_min fallback = 7
```

gate 通过并改变 pair 的 context：

```text
seed61001 greedy: [2,18] -> [3,4], score 0.74
seed61103 greedy: [10,15] -> [6,15], score 0.74
seed61414 greedy: [13,16] -> [6,20], score 0.74
seed61411 random: [1,9] -> [2,10], score 0.74
seed61923 sector: [1,13] -> [13,20], score 0.74
```

低分 context 回退 baseline，没有裸开 v457 窄分数模型。

## 关键问题

1. 纯 GAT 模型仍不可用。
   v457 验证集表现为 recall=1.0、precision=0.429，实际分数集中在 0.53 左右。模型还没有学到能泛化区分 strong positive 和 hard negative 的因果特征。

2. 当前收益主要来自 evidence overlay。
   v461 的收益不是“模型自己泛化发现”，而是 strict replay evidence 被 conservative overlay 编码进 score map 后触发。它是 exact-safe、可复现的调度收益，但还不是成熟的 GAT 泛化能力。

3. 正例命中率低。
   v456 positive-neighbor 首批 8 个候选只有 1 个 strict positive。这说明继续盲目扩展候选 replay 成本高，下一步应提升候选生成质量。

4. full-open 与 gated 必须分清。
   v460 因参数名少了 `candidate`，实际 gate disabled，是 full-open；虽然结果更好一点，但不能作为 gated 结论。v461 才是有效的 score-gated 结论。

## 下一步

1. 继续补 strict replay，但不再盲跑 positive-neighbor。
   优先围绕已验证正例 `[6,20]`、`[2,10]`、`[6,15]`、`[13,20]` 的相邻结构采样，比较同 context hard negative。

2. 改善特征，而不是只加样本。
   需要把 child proof cost、child exact pricing events、completion-bound retry、child width/balance、incumbent relation 的结果字段进入训练行，并确保同一 node 下有正负 pairwise ranking。

3. 保持 conservative score gate。
   在纯模型可分性不足前，生产式 opt-in 只能用 evidence overlay + min score + width/balance gate；低分 context 必须回退 baseline。

4. 扩展到 20-scale 60-instance 前，先跑 20-24 instance smoke。
   目标是确认 v461 的两个新增闭环不是 12-instance 选择偏差，同时检查 5/10 不退化。

5. 暂不把 admission scheduler 作为主线。
   当前收益来自 branch pair；admission 继续作为诊断辅助，避免把列调度和分支排序的因果混在一起。

## 精确性边界

- 本阶段所有学习输出只影响 Ryan-Foster 候选排序。
- early branch 在 v460/v461 smoke 中显式关闭。
- score map / overlay 不提供 lower bound、certificate、pruning decision。
- OPTIMAL 仍由原 exact pricing closure / BPC 逻辑证明。
