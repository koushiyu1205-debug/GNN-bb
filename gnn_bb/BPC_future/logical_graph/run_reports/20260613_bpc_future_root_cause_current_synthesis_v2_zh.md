# BPC_future 当前根因综合 v2：为什么做了很多仍然没有可上线优化

日期：2026-06-13

## 一句话结论

不是因为某一个模块还没调好，也不是因为 Pulse 没写完。

当前失败的核心是：

> 5/10 的可用时间预算太小，任何真实 audit / worker / probe 固定开销都会回退；20-task 又不是缺少 true-RC negative columns，而是缺少一个能在 addition 前判断“哪一批具体 JourneyColumn signature / timing 会把后续 RMP 轨迹推向好路径”的 selector。

这两个问题互相冲突：

- 20 需要探索、比较、筛选更多 returned batch；
- 5/10 不能支付这种探索成本；
- 目前 selector 只能事后解释，不能事前稳定泛化；
- 所以所有“多搜一点 / 多返回一点 / 多加一点 worker”的方向都会在某处失败。

因此当前不是“优化已经完成但收益小”，而是：

> exactness 边界已经守住，机制诊断已经清楚，但 production 优化方向还没有闭环。

最新 counterfactual replay 把这句话进一步收紧：现在 clean exact-context replay 已经不止 Apollo 单点，`tranq20_01` 和 `mt20_greedy_tranq_01` 相关 contexts 也能产生 local RMP high-impact returned batches。但同一批 replay 数据里仍有 no-op candidates，且 `capture_target_002 / mt20_greedy_apollo_01 cg3` 仍未 exact covered。后续复核显示 target002 不是 cg3 才偏离，而是当前代码在 cg1 returned batch 就从旧 phase10h 轨迹分叉。因此当前缺口从“有没有 high-impact batch”变成了“能不能在加入前稳定识别 high-impact batch，并稳定控制早期 returned-batch 轨迹”。

最新 exact-context replay selector gate 又把这个缺口钉得更死：207 条 exact replay impact rows 中，`true_reduced_cost <= -12.430587` 在全样本达到 precision `0.8513513513513513` / recall `0.8571428571428571`，但 dataset holdout 只有 precision `0.664`，instance holdout recall 只有 `0.46258503401360546`，train-best dataset holdout precision 也只有 `0.6907216494845361`。`passing_features_all_holdouts = []`。所以现在不是“没有 signal”，而是“addition-before signal 还不能跨 context / instance / dataset 泛化”。

继续把规则放宽到二特征 AND/OR gate 后，结论仍不变：全样本最优 pair rule 的 precision/recall 为 `0.9512195121951219 / 0.5306122448979592`，但 context holdout recall 只有 `0.272108843537415`，instance holdout precision `0.6907216494845361`，dataset holdout precision `0.6875`，三个 holdout gate 全部失败。

再放宽到简单多特征模型后，结论变得更具体：`nearest_centroid` 和 `shallow_tree_depth3` 在 context / instance holdout 中能过 strict gate，但 dataset holdout 没有任何模型通过；这说明当前 signal 不是不存在，而是仍然不能跨 replay dataset / target source 稳定迁移。

## 证据 1：Pulse 安全，但没有稳定 ROI

Sharded Pulse 这条线的主要价值是把 certificate / duplicate-only / incomplete / materialization / true-RC 边界修正确了。

已经证明的部分：

- returned journeys 通过 `manual_journey_reduced_cost()`；
- incomplete / duplicate-only / empty harvest 不会更新 official lower bound；
- dummy / audit / worker 不污染默认 benchmark；
- current-context probe 可以在 Apollo10 / tranq10_09 返回并加入 true-RC negative columns；
- critical disagreement 长期为 0。

但 Phase 7O 到 Phase 8Q 的真实信号是负的：

- Phase 7O hard-tail worker ROI A/B：
  - 24 行全部 `TIME_LIMIT`；
  - official pricing state 全部 `INCOMPLETE_LIMIT`；
  - critical disagreement `0`；
  - worker events `14`；
  - legacy final judge calls `48`；
  - completion-bound retry count `0`。
- Phase 8Q：
  - 35 行全部 `TIME_LIMIT`；
  - worker returned / added `10 / 10`；
  - new task sets `8`；
  - support-changing `2`；
  - 仍没有稳定 wall-time / gap / tail 改善。

结论：

> Pulse worker 能安全加负列，但“加了负列”没有稳定转化为“更快收敛”。

所以继续加 worker budget、放开 worker default、或者打开 certificate gate 都没有依据。

## 证据 2：5/10 回退不是偶然，是固定开销结构性问题

5/10 small-scale overhead guard audit 汇总了 21 个小规模结果集：

```text
nonbaseline small rows = 545
task5 rows = 380
task10 rows = 165
```

真实触发 worker / audit / probe 的小规模 rows：

```text
rows = 220
worsened = 208
no_regression = 12
improved = 0
official_changed = 17
median wall delta = +0.3165025
relative median delta = +12.1315695952616
worse_count = 220
better_count = 0
```

未触发 worker / audit / probe 的小规模 rows：

```text
rows = 325
no_regression = 301
improved = 24
worsened = 0
official_changed = 0
median wall delta = -0.000043
```

直接解释：

- 5/10 上机制真实触发时，220/220 wall time 都变差；
- 未触发时看起来“不回退”，本质是 no-op / gate，不是机制产生收益；
- full-profile gate 里即使 worker 最后跳过，audit / trigger plumbing 也已经造成固定成本。

所以 5/10 no-regression 的真实条件不是“Pulse 要更聪明”，而是：

> 小规模必须在极早、极便宜的位置 no-op；late skip 已经太晚。

这也是为什么 20 的探索机制不能默认带到 5/10。

## 证据 3：20-task 不是缺负列，而是 returned cut / batch 轨迹选错

Apollo20 dp1000 returned-boundary calibration 显示 baseline 只返回 rank0，但 rank1-rank7 仍有强负列被截断：

```text
rank0  [5,8,15]   rough=-139.913748
rank1  [4,5,8]    rough=-137.150710
rank2  [5,8,18]   rough=-136.660461
rank3  [4,5,15]   rough=-136.347326
rank4  [4,8,15]   rough=-136.011232
rank5  [4,5,18]   rough=-134.743366
rank6  [8,15,16]  rough=-132.930824
rank7  [8,15,18]  rough=-132.886574
```

在该单点上，return8 把 primal 从：

```text
baseline 921.640296
return8  793.914380
```

这证明 returned cut 是真实边界。

但跨日志结果同时证明“多返回”不是解法：

- return8 / return12 在不同 context 上有时改善、有时恶化；
- `mt20_greedy_tranq_01` return8 worsened，但 return12 improved；
- `mt20_greedy_apollo_01` return12 多次 worsened；
- returned count、best RC、rough RC 都不能单独解释 outcome。

因此根因不是“returned 太少”，而是：

> 当前没有能力选择哪一批 returned columns 会改善后续 RMP / dual / pricing trajectory。

## 证据 4：更负 RC 不等于更有用

candidate-level contrast 找到一个很强的反例。

`mt20_greedy_apollo_01` return8 r0 / r2 在 cg3 前 context 完全一致：

```text
objective = 780.586496
active hash = 16862add48072518
dual hash = 350001260a512742
fractional sum = 7.0
```

r0 worsened：

```text
best_rc = -64.283449
negative_candidate_count = 86
selected_candidate_count = 16
returned_count = 8
```

`[5,10,18]` 出现在 negative / selected samples 中，但没有进入 materialized / returned。

r2 improved：

```text
best_rc = -20.1912655
negative_candidate_count = 78
selected_candidate_count = 14
returned_count = 8
```

`[5,10,18]` 进入 materialized / returned，并触发后续 incumbent path。

这说明：

- 更负 best RC 可以走坏；
- 较弱 RC 可以走好；
- selected 还不够，必须 materialized / returned；
- 关键发生在 concrete journey signature / timing / returned batch composition。

所以“按最负 RC 返回”“提高 best-RC 搜索能力”“多找 true negative”都不是充分解法。

## 证据 5：RMP 当轮动了也不代表最终好

per-batch movement audit 显示：

```text
stage rows = 64
moved = 63 / 64
strong_moved = 63 / 64
integerizing = 26 / 64
```

改进组：

```text
40 / 40 moved
40 / 40 strong_moved
```

恶化组：

```text
23 / 24 moved
23 / 24 strong_moved
```

也就是说，坏 batch 也会让 RMP objective / active basis 明显移动。不能把“下一轮 RMP 有变化”当作有益信号。

downstream trajectory label audit 进一步说明：

- improved runs 10/10 后续有 incumbent update；
- worsened runs 0/8 有 incumbent update；
- worsened rows 也可能有更大的 immediate objective drop；
- 真正区分好坏的是后续 1-2 轮是否进入 incumbent-producing path、是否降低 residual incomplete tail。

这些是事后标签，能解释根因，但不能直接在线使用。

## 证据 6：最强前置信号仍然不能跨日志泛化

目前最强的 addition-before 信号类别是：

- active relation；
- batch coherence；
- active redundancy；
- pair overlap / pair Jaccard；
- batch 与当前 active top samples 的关系。

在 Phase10H 内部，它们看起来有用：

- `active_avg_jaccard <= 0.305555...` 预测 `incumbent_within2` accuracy `0.78125`；
- 二特征规则 `active_redundant_frac <= 1/6 and pair_overlap >= 0.25` accuracy `0.84375`。

但跨日志 generalization 失败。

纳入 7 个结果集、334 个 stage rows 后：

```text
runs = 98
improved = 98
worsened = 120
no_regression = 116
```

Phase10H 规则外推：

```text
active_avg_jaccard <= 0.305555...
accuracy = 0.6287425
tp = 84
fp = 65
tn = 126
fn = 59
```

二特征 incumbent 规则：

```text
accuracy = 0.6197604
tp = 19
fp = 3
tn = 188
fn = 124
```

final improved 二特征规则表面 accuracy 高：

```text
accuracy = 0.7964071
tp = 36
fp = 6
tn = 230
fn = 62
```

但它主要靠保守预测 non-improved，漏掉 62 个 improved。

leave-one-dataset 更直接：

```text
final improved accuracy = 0.5642201
tp = 3
fp = 0
tn = 120
fn = 95
```

这意味着当前规则几乎退化成“全预测不会改善”，不能承担 20-task improvement selector。

结论：

> active-relation / batch-coherence 是根因信号，但还不是可上线 selector。

## 为什么“做了这么多都不行”

因为前面多数方向解决的是局部问题，不是最终选择问题。

| 方向 | 已证明 | 为什么仍不行 |
|---|---|---|
| Sharded Pulse certificate ledger | 证书语义更安全 | 没产生稳定 no-negative proof / ROI |
| Pulse materialization / true-RC filter | 列语义一致 | 只能保证列正确，不能保证列有用 |
| Transition Pulse / archive / weak bound | 能剪一些 infeasible / dominated states | 搜索更好不等于 returned batch 更好 |
| Hidden-negative worker | 能加 true-RC negative columns | 加列不稳定减少 tail |
| current-context probe | hard-ish 10 上能加列 | 没证明 wall-time ROI |
| adaptive sharding | exact partition 语义清楚 | 当前未降低 incomplete |
| profile-DP cap / selection | 能改变候选域 | 更多候选不等于选对候选 |
| return8 / return12 | 某些 20 单点改善 | 跨 context 可恶化 |
| low-overlap / active-relation / true-RC selector | 同样本有信号 | 跨 instance / dataset 泛化失败 |
| RMP movement / objective drop | 当轮变化明显 | 好坏 batch 都会移动 RMP |

根本差距是：

> 我们能产生候选，也能解释事后 outcome，但还不能在 addition 前可靠预测这个候选批次会不会让后续 trajectory 变好。

## 当前最可信根因表述

当前根因可以收紧为：

> BPC_future 的 20-task hard-tail 不是负列生成能力单点不足，而是 returned JourneyColumn batch 的 concrete task-set / sequence / signature / start-time / arc-option / active-basis relation 与后续 RMP trajectory 之间存在强非线性耦合。现有 return limit、rough RC、best RC、simple diversity、Pulse worker、profile-DP cap 都只能扰动这个耦合，不能稳定选择好 batch。5/10 又因为固定开销极敏感，不能默认承担这种探索成本，所以必须依赖 early no-op gate。没有一个跨 context 泛化的 addition-before selector，就无法同时保证 exactness、5/10 no-regression 和 20 大幅加速。

新增 target replay 证据：

```text
target coverage: 2 / 3 exact covered
target001/002 sweep ready cases = 66
target001/002 high-impact candidates = 117
target001/002 noop candidates = 59
target001/002 best local RMP objective delta = -267.639664
tranq20 target high-impact candidates = 26
tranq20 target best local RMP objective delta = -70.009099
target002 reproduction gap = cg1 returned-batch trajectory drift
exact replay selector gate rows = 207
exact replay full-sample true-RC precision/recall = 0.8513513513513513 / 0.8571428571428571
exact replay dataset-holdout true-RC precision/recall = 0.664 / 0.564625850340136
exact replay passing_features_all_holdouts = []
exact replay pair full-sample precision/recall = 0.9512195121951219 / 0.5306122448979592
exact replay pair context-holdout precision/recall = 0.7547169811320755 / 0.272108843537415
exact replay pair dataset-holdout precision/recall = 0.6875 / 0.8979591836734694
exact replay model context passing count = 2
exact replay model instance passing count = 2
exact replay model dataset passing count = 0
exact replay model all-holdout passing count = 0
production_direction_proven = false
```

## 现在不能继续推的方向

不要继续做这些作为 production 主线：

- 默认启用 Pulse worker；
- 扩大 Pulse worker time limit / recursion limit；
- 打开 official certificate gate；
- 默认 return8 / return12；
- 简单提高 profile-DP cap；
- 只按 rough RC / best RC / rank 重排；
- 只按全样本 `true_reduced_cost` 阈值筛选；
- 只按简单二特征 AND/OR gate 筛选；
- 直接上线当前 nearest-centroid / shallow-tree 简单模型；
- 只按 low-overlap / active_avg_overlap / active_redundant_frac 单规则筛选；
- 把同样本最优二特征规则写进 solver；
- 在 5/10 上做默认 audit / probe / worker；
- 用 “少跑 final judge” 伪装加速。

这些方向要么会破坏 5/10，要么会让 20 走坏 trajectory，要么没有跨日志证据。

## 下一步什么才算有价值

下一步如果继续做，应该是 calibration-only，不应直接改 production path。

最有价值的方向是构造 candidate / batch 级 trajectory dataset：

- addition 前可见特征：
  - task-set；
  - sequence；
  - signature / start time；
  - arc option family；
  - rough RC / true RC；
  - relation to active top samples；
  - active redundancy / bridge；
  - batch union / overlap / coherence；
  - new / replacement / support-changing class；
  - current fractional pressure；
  - recent active hash churn；
  - current pricing state / residual tail context；
- 后验标签只用于训练 / 校准：
  - next RMP objective delta；
  - next dual movement；
  - active persistence；
  - incumbent within 1-2 rounds；
  - zero fractional within 1-2 rounds；
  - next incomplete-heavy path；
  - residual negative family chain。

验收必须是：

1. leave-one-instance / leave-one-dataset 仍能抓到 positive improved batch；
2. false positive 足够低；
3. 5/10 默认 early no-op；
4. 20 hard set 有稳定 wall-time / gap / primal / tail 改善；
5. exactness 仍只来自 true-dual exact certificate；
6. returned columns 仍逐条 true-RC negative。

没有这个证据前，不能宣称找到优化方向。

## 当前状态

根因解释已经比较清楚：

- 5/10 失败来自固定开销；
- 20 失败来自 returned-batch trajectory selector 缺失；
- Pulse / profile-DP / return-count 都只是候选生成或扰动机制；
- 最强前置信号仍然不能跨日志泛化。

但目标仍未完成：

- 还没有 production selector；
- 还没有证明 5/10 不退化且 20 稳定大幅改善；
- 还没有可以默认启用的 profile；
- 还没有可以打开的 Pulse certificate gate。

所以对“为什么做了这么多都不行”的直接回答是：

> 因为我们一直在增强“找负列”和“扰动 returned batch”的能力，但真正缺的是能事前判断哪些负列批次会改善后续 RMP 轨迹的选择器；同时小规模实例没有预算承受这些探索。现在 exactness 已经守住，失败点已经定位，但优化闭环还没完成。
