# V559：两类 retry、retry on/off/gate/cap 对比（seed61717）

## 结论先说

必须把 retry 分成两类：

1. 普通 no-column 补救 retry
   - 典型事件：`journey_exact_pricing_retry`
   - 作用：在普通 exact pricing 不完整或 no-column 后，再尝试找真实负列。
   - 精确性：只能加入真实 reduced-cost 验证过的列；它的 no-column 结果不能当作完整 certificate。

2. completion-bound / final-judge retry
   - 典型事件：`journey_exact_pricing_completion_bound_retry`
   - 作用：用 direct-label / completion-bound 证明没有遗漏负列，形成节点闭合证书。
   - 精确性：它可以帮助 certificate；但如果被 gate/cap 后没有完成，节点只能 fail-closed，不能剪枝。

当前瓶颈主要是第二类，不是第一类。

## 本轮代码改动

新增 opt-in 的 completion-bound / final-judge retry budget cap：

- `journey_certificate_completion_bound_retry_budget_cap_enabled`
- `journey_certificate_completion_bound_retry_budget_cap_time`
- `journey_certificate_completion_bound_retry_budget_cap_min_time`
- `journey_certificate_completion_bound_retry_budget_cap_min_observations`
- `journey_certificate_completion_bound_retry_budget_cap_min_expensive_zero_harvest_retries`
- `journey_certificate_completion_bound_retry_budget_cap_expensive_profile_time`
- `journey_certificate_completion_bound_retry_budget_cap_min_tasks`

它只缩短后续 final-judge retry 的 time limit，不提供 bound，不提供 certificate，不剪枝。

日志新增字段：

- `retry_budget_cap_enabled`
- `retry_budget_cap_applied`
- `retry_budget_cap_reason`
- `retry_budget_cap_original_budget`
- `retry_budget_cap_budget`
- `retry_budget_cap_context_key`
- `retry_budget_cap_context_total_count`
- `retry_budget_cap_context_expensive_zero_harvest_count`

已通过定向测试：

- budget cap 默认关闭不改变行为；
- 同 context 出现昂贵 zero-harvest 历史后才 cap；
- 未见过的 context 不 cap；
- 原 retry gate 单测仍通过。

## 对比结果

实例：

`tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717`

| 组别 | final-judge retry 策略 | status | wall s | gap | ordinary retry | final retry | final profile s | gate events | cap applied | branch nodes | fathom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V555 retry on | 全开 | `EXTERNAL_TIME_LIMIT` | 600.039 | 0.039594 | 0 | 9 | 295.850 | 0 | 0 | 6 | 0 |
| V556 hard gate + branch | 两次昂贵零收获后直接 gate 到 branch | `EXTERNAL_TIME_LIMIT` | 600.033 | 0.039594 | 2 | 2 | 71.127 | 24 | 0 | 22 | 0 |
| V557b retry off | 关闭 final judge，且关闭 required completion-bound | `TIME_LIMIT` | 59.059 | n/a | 1 | 0 | 0.000 | 0 | 0 | 0 | 0 |
| V558 context gate + score branch | depth+trigger gate，score/width/open-node 控制 branch | `EXTERNAL_TIME_LIMIT` | 600.019 | 0.039594 | 0 | 9 | 292.780 | 2 | 0 | 8 | 0 |
| V559 budget cap | 第一次保留 full retry，后续同 trigger cap 到 12s | `TIME_LIMIT` | 170.139 | 0.039594 | 0 | 3 | 57.884 | 0 | 2 | 1 | 0 |

## V559 细节

V559 的三次 final-judge retry：

| node | depth | trigger | cap | budget s | status | reason | profile s | negative | selected |
|---:|---:|---|---|---:|---|---|---:|---:|---:|
| 0 | 0 | `no_retry_budget` | no | 45.0 | `OPTIMAL` | `direct_label_no_negative_journey` | 33.884 | 0 | 0 |
| 1 | 1 | `no_retry_budget` | yes | 12.0 | `INCOMPLETE` | `time_limit` | 12.000 | 0 | 0 |
| 2 | 1 | `no_retry_budget` | yes | 12.0 | `INCOMPLETE` | `time_limit` | 12.000 | 0 | 0 |

这说明 budget cap 生效了：

- final profile：`295.850s -> 57.884s`
- wall：`600.039s -> 170.139s`
- branch nodes：`6 -> 1`

但它没有求到最优：

- status 仍是 `TIME_LIMIT`
- gap 仍是 `0.039594`
- 两个 child 都是 `exact_completion_bound_retry INCOMPLETE/time_limit`
- 没有 fathom

所以 V559 不是可上线优化，只是证明了“final-judge retry 预算可控”。

## 是否能优化

能优化的是局部 proof-tail 成本。

V556 和 V559 都证明：昂贵 zero-harvest final-judge retry 可以被识别并减少耗时。V559 还证明：不需要裸 branch，也能把这部分 profile time 压下来，避免 V556 的 branch tree 爆炸。

但当前还不能优化完整求解。

原因是 final-judge retry 被压短后，child 没有 certificate，只能 fail-closed 成 incomplete node。它省掉了时间，但也提前放弃了可能闭合节点的证明路径。因此 wall time 变短不等于 OPTIMAL 加速。

## 现在的问题

1. retry off 不可用

关闭 final judge 会很快返回内部 `TIME_LIMIT`，但 dual bound / gap 可能缺失或不完整。这只是停止证明，不是求解优化。

2. hard gate + branch 太粗

V556 把 final profile 降到 `71.127s`，但 branch nodes 从 `6` 涨到 `22`。它把 proof cost 转成 branch-tree cost。

3. context gate 太保守

V558 避免了树爆炸，但 profile time 几乎回到 V555。深层 score map 覆盖不足时，branch fallback 被 `missing_score_source` 拦住。

4. budget cap 太硬

V559 不树爆，也大幅降 profile time，但 12s cap 让 child proof 全部 incomplete。它缺少“什么时候必须放宽 cap、什么时候可以直接转 score-gated branch”的策略。

## 下一步优化方向

主线不是关 retry，而是做 adaptive final-judge retry controller：

1. completion-bound retry 分层预算
   - 第一次同 trigger full retry 保留；
   - 第二次 cap 到较短预算；
   - 如果 cap 后仍 `INCOMPLETE/time_limit`，不要无限重复 cap；
   - 根据 child gap / branch depth / incumbent 接近程度放宽预算或转 branch。

2. cap 后的动作不能只是 incomplete
   - 若 branch score 覆盖当前 context，且 score/width/balance/open-node gate 通过，转 exact-safe branch；
   - 若 score 缺失，记录 hard negative / missing context，不裸 branch。

3. 训练标签要加入 retry 后果
   - child final-judge retry count；
   - child final profile time；
   - child `INCOMPLETE/time_limit`；
   - child time-to-certificate；
   - cap 后是否仍能闭合。

4. score map 要补深层 context
   - 当前浅层/root score 有价值；
   - proof tail 发生在 child/depth context；
   - 没有深层 score 时，gate 只能 fail-closed。

5. 全量实验不要把 170s TIME_LIMIT 当 win
   - 它可以作为“节省无效 proof time”的正信号；
   - 但训练主标签仍应区分 `OPTIMAL wall-time gain` 和 `unsolved early stop`；
   - 未最优实例必须保留 gap、dual bound、primal bound 和 timeout 分型。

## 当前判断

这条线有优化价值，但不是单独靠 retry gate 就能把 20 规模打穿。

目前最可信的方向是：

`branch score 主线 + final-judge retry adaptive budget + score-gated branch fallback + 深层 proof-tail 标签`

其中 retry controller 的角色是减少明显无收益的 proof-tail 重复消耗；真正让节点闭环变快，仍要靠更好的 branch pair、child ordering，以及能提高 child certificate 成功率的数据。
