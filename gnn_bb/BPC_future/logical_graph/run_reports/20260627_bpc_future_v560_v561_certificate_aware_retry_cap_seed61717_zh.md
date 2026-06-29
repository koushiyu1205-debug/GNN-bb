# V560/V561：certificate-aware final-judge retry cap 诊断（seed61717）

## 背景

V559 证明了 budget cap 能把 final-judge retry profile 从约 `295.850s` 降到 `57.884s`，但它犯了一个因果错误：

`zero-harvest + certified no negative` 被当成坏样本。

在 completion-bound / final-judge retry 里，这其实是成功证书。没有 negative、没有 selected trips，正是因为它证明了当前 region 没有遗漏负列。它不应该触发过硬 cap；它应该成为“下一次证书大概需要多少时间”的观测。

## 本轮代码修正

retry gate/cap 统计现在区分：

- `certified_zero_harvest_count`
- `expensive_certified_zero_harvest_count`
- `incomplete_zero_harvest_count`
- `expensive_incomplete_zero_harvest_count`
- `certified_zero_harvest_profile_time_max`

默认含义：

- hard gate 默认只看 `expensive_incomplete_zero_harvest_count`，不再把成功证书当作坏样本；
- budget cap 可以由 certified/incomplete 两类历史触发；
- 但 cap 后预算不得低于 `certified_zero_harvest_profile_time_max + margin`。

新增关键参数：

- `journey_certificate_completion_bound_retry_gate_expensive_zero_harvest_source`
- `journey_certificate_completion_bound_retry_budget_cap_expensive_zero_harvest_source`
- `journey_certificate_completion_bound_retry_budget_cap_certified_profile_margin`

精确性边界不变：

- cap 只改变 final-judge retry time limit；
- 不提供 official bound；
- 不提供 certificate；
- 不剪枝；
- cap 后未完成必须 fail-closed。

## 对比结果

实例：

`tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717`

| 组别 | 策略 | status | wall s | primal | dual | gap | nodes | branch | final retry | final profile s | final retry 结果 | cap applied |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| V555 | retry on，无 cap | `EXTERNAL_TIME_LIMIT` | 600.039 | 616.241205 | 591.841542 | 0.039594 | 9 | 6 | 9 | 295.850 | 6 cert / 2 incomplete | 0 |
| V559 | 非 certificate-aware，12s cap | `TIME_LIMIT` | 170.139 | 616.241205 | 591.841542 | 0.039594 | 3 | 1 | 3 | 57.884 | 1 cert / 2 incomplete | 2 |
| V560 | certificate-aware，margin=5 | `EXTERNAL_TIME_LIMIT` | 600.018 | 614.552290 | 591.841542 | 0.036955 | 10 | 6 | 10 | 296.939 | 6 cert / 3 incomplete | 7 |
| V561 | certificate-aware，margin=8 | `EXTERNAL_TIME_LIMIT` | 600.019 | 614.552290 | 591.841542 | 0.036955 | 10 | 7 | 10 | 303.036 | 7 cert / 2 incomplete | 1 |

## 读数

V560/V561 修正了 V559 的错误。

- V559 在 node 1/2 把预算压到 `12s`，两个 child 都 `INCOMPLETE/time_limit`。
- V560 看到 root 证书耗时 `33.667s` 后，把 node 1 cap 自动抬到 `38.667s`，node 1/2 都重新拿到 certificate。
- V561 margin=8 后，node 7 也避免了 V560 的误 cap，拿到了 certificate。

但 V560/V561 仍未求到最优。

- gap 从 `0.039594` 改善到 `0.036955`；
- primal 从 `616.241205` 改善到 `614.552290`；
- 但 dual bound 仍是 `591.841542`；
- 600s 内仍没有完整 proof closure。

## 说明了什么

1. retry off / hard cap 不是正确优化

V559 的 170s 不是好结果，只是过早放弃 child certificate。它省掉了时间，但没有推进 proof closure。

2. certificate-aware 是必要修正

如果不区分 certified zero-harvest 和 incomplete zero-harvest，controller 会把成功证书当坏样本，直接伤害精确闭环。

3. 只调 cap margin 不够

margin=5：仍有可证节点被压成 incomplete。

margin=8：减少误 cap，但大部分 cap 变成 `cap_not_tighter`，profile 成本回到 V555 量级。

所以单靠 budget cap 只能在“明显无证书希望”的 retry 上省时间，不能解决 proof tail 的主矛盾。

4. 当前主矛盾仍是 branch/proof-tail 闭环

V560/V561 的 branch score 只在 root 有明确 score source；深层 branch 基本没有 score：

- root selected pair `[4, 9]` 有 score；
- depth>=1 的 selected score 多为 missing；
- 这导致 retry controller 识别到 proof-tail 后，没有可靠的 score-gated branch fallback。

## 下一步

继续保留 certificate-aware retry cap，但不要把它当主加速线。

真正下一步应该是：

1. 把 V555/V560/V561 的 child proof-tail 事件转成训练数据
   - child final-judge retry profile time；
   - certified / incomplete；
   - child branch pair；
   - child primal/gap 改善；
   - cap 后是否导致误 incomplete。

2. 补深层 branch-score coverage
   - depth 1/2/3 的 Ryan-Foster candidates；
   - score source 必须包含 state/context；
   - 没有 score source 不允许裸 branch。

3. retry controller 的生产默认
   - certificate-aware 统计开启；
   - 第一次 full final-judge retry 保留；
   - cap floor = observed certified profile max + margin；
   - 只有 `expensive_incomplete_zero_harvest` 才作为坏样本；
   - cap 后若仍 incomplete，不直接判赢，必须进入 branch-score / failure typing。

4. 全量 random-TW 20 规模评估时继续记录 gap
   - `EXTERNAL_TIME_LIMIT` 也必须保留 primal、dual、gap；
   - 不把 `TIME_LIMIT` 早停当加速正例；
   - 训练标签区分 wall-time gain、gap gain、certificate gain、误 cap regression。

## V562 branch-impact 结构化

已将 V555/V560/V561 三组日志跑入 branch-impact audit：

输出目录：

`BPC_future/results/journey_branch_impact_v562_retry_cap_seed61717_20260627/`

报告：

`BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_branch_impact_v562_retry_cap_seed61717_zh.md`

机器摘要：

| 字段 | 值 |
|---|---:|
| log_count | 3 |
| branch_count | 19 |
| branch_training_row_count | 19 |
| child_probe_row_count | 38 |
| completion_bound_tail | 14 |
| unprocessed_children | 5 |
| right_censored_branch_count | 19 |
| usable_branch_impact_training_count | 0 |
| total_child_completion_bound_retries | 79 |
| total_child_exact_pricing_events | 94 |
| total_child_negative_pricing_events | 117 |
| total_child_fathom_events | 0 |

这批数据不能当 strict positive。

原因是三组都没有 finish，所有 branch rows 都是 right-censored；未处理 child 不能被当成该 branch 的真实完整后果。

但它们有训练价值：

- 可以作为 proof-tail risk / hard negative 诊断；
- 可以标注 `completion_bound_tail`、`child_completion_bound_retry_count`、`child_proof_cpu`；
- 可以帮助 GAT 学“哪些深层 branch 会带来大量 child completion-bound retry”；
- 不能直接学“这个 branch 会让完整求解更快最优”。

## 当前判断

V560/V561 是一次重要纠偏：之前的 retry gate/cap 方向里，坏样本定义错了。

纠偏后，retry controller 变得 exact-safe 且不再明显伤害可闭合 child；但它也证明了，final-judge cap 本身不是 20-scale 600s OPTIMAL 的核心答案。下一步必须回到 Branch Score 主线：让 GAT 学深层 branch pair 对 child proof cost / certificate time 的影响，而不是继续只在 root 或浅层做排序。
