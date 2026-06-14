# BPC_future 根因审计补充：low-overlap false positive audit

日期：2026-06-13

## 目标

上一轮 batch feature separability 发现：

```text
pair_overlap <= 0.26992753623188404
accuracy = 17 / 18
tp = 10
fp = 1
tn = 7
fn = 0
```

唯一 false positive 是：

```text
mt20_greedy_apollo_01
experimental_early_new_task_set_quota_3_return12_20_only
repeat = 2
outcome = worsened
delta = +139.913748
```

本轮只读审计这个反例，回答：

**为什么它具有低 overlap / 低 Jaccard 的“好 batch”形态，但最终仍 worsened？**

本轮不改 solver、不改 pricing、不改 RMP、不改 Pulse、不跑新 benchmark。

## 对照对象

同一 instance / repeat：

- improved：`mt20_greedy_apollo_01 / experimental_early_new_task_set_quota_3_20_only / r2`
- worsened：`mt20_greedy_apollo_01 / experimental_early_new_task_set_quota_3_return12_20_only / r2`

输入日志：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_return12_20_only__r2.jsonl`

## 重要数据质量修正

`journey_column_addition.changed_task_set_samples` 在 return12 cg1/cg2 中被 capped：

```text
return12 cg1:
  added = 12
  changed_task_set_count = 12
  changed_task_set_samples_len = 8
  changed_task_set_samples_truncated = True

return12 cg2:
  added = 12
  changed_task_set_count = 12
  changed_task_set_samples_len = 8
  changed_task_set_samples_truncated = True
```

因此，后续做 selector 特征时不能只依赖 capped `journey_column_addition` samples。

本轮改用 `journey_pricing.diagnostic_selected_returned_task_set_samples`，它在本对照中包含完整 returned task-set list：

- return8：cg1/cg2/cg3 各 8 个；
- return12：cg1 12 个、cg2 12 个、cg3 4 个。

这会影响数值，但不会推翻 false positive。相反，使用完整 pricing returned list 后，return12 r2 的 first3 aggregate overlap 更低。

## 完整 returned batch overlap

用前三个 heuristic `journey_pricing` 的 `diagnostic_selected_returned_task_set_samples` 计算：

| profile | first3 returned unique | union | pair_jacc | pair_overlap |
|---|---:|---:|---:|---:|
| return8 r2 improved | 24 | 12 | 0.181220 | 0.269928 |
| return12 r2 worsened | 28 | 14 | 0.161420 | 0.237654 |

结论：

- return12 r2 确实是更低 overlap / 更低 Jaccard；
- 它仍 worsened；
- 所以 false positive 不是 capped sample 造成的假象。

## 轨迹对照

### return8 r2 improved

关键轨迹：

```text
cg1 RMP objective = 1061.554044
cg2 RMP objective = 859.357131
cg3 RMP objective = 780.586496
cg4 RMP objective = 770.211317
cg5 RMP objective = 766.868627
```

active hash / fractional：

```text
cg1 active_hash = c6ea96127d7c5d7b, frac_sum = 0
cg2 active_hash = 427b1308ea279e0c, frac_sum = 2.0
cg3 active_hash = 16862add48072518, frac_sum = 7.0
cg4 active_hash = 22631672c7543445, frac_sum = 0
cg5 active_hash = 8f346beb623b7737, frac_sum = 5.75
```

cg3 returned batch：

```text
best_rc = -20.1912655
returned = 8
task sets =
  [5,14,18]
  [3,14,18]
  [10,14,18]
  [14,18]
  [14,15,18]
  [5,12,18]
  [4,8,14]
  [5,10,18]
```

cg3 后直接效果：

- RMP objective 从 `780.586496` 变为 `770.211317`；
- active hash 从 `16862add48072518` 变为 `22631672c7543445`；
- fractional sum 从 `7.0` 变为 `0`；
- active top samples 出现 `[5,14,18]`、`[4,8,15]`、`[12,16,17]` 等。

说明 cg3 batch 虽然 best RC 不算极强，但它实际改写了 active basis。

### return12 r2 worsened

关键轨迹：

```text
cg1 RMP objective = 1061.554044
cg2 RMP objective = 823.547077
cg3 RMP objective = 765.309360
cg4 RMP objective = 765.309360
```

active hash / fractional：

```text
cg1 active_hash = c6ea96127d7c5d7b, frac_sum = 0
cg2 active_hash = 338663e565646052, frac_sum = 3.5
cg3 active_hash = f5925b65ac3293cf, frac_sum = 1.666667
cg4 active_hash = f5925b65ac3293cf, frac_sum = 1.666667
```

cg3 returned batch：

```text
best_rc = -6.110727
returned = 4
task sets =
  [2,13,20]
  [2,10,20]
  [2,3,20]
  [2,20]
```

cg3 后直接效果：

- RMP objective 不变：`765.309360 -> 765.309360`；
- active hash 不变：`f5925b65ac3293cf -> f5925b65ac3293cf`；
- fractional sum 不变：`1.666667 -> 1.666667`；
- 下一轮 pricing 进入 `INCOMPLETE_LIMIT`。

说明 return12 r2 的 cg3 columns 虽然属于低-overlap aggregate batch 的一部分，但这批列没有推动 active basis，也没有改善 RMP objective。

## 与当前 active basis 的关系

### return8 cg3

cg3 returned sets 与当前 active top sample 的平均最大关系：

```text
avg max Jaccard to active = 0.279
avg max overlap to active = 0.479
```

代表性 returned set：

```text
[5,14,18]  best active [1,14], overlap 0.5
[5,10,18]  best active [2,10,19], overlap 0.333
[4,8,14]   best active [4,5,8], overlap 0.667
```

这些 columns 不是完全 disjoint，而是把 active basis 中的若干 family 通过 task 14 / 18 / 5 / 10 等重新连接，随后 active basis 进入 integer state。

### return12 cg3

cg3 returned sets 与当前 active top sample 的平均最大关系：

```text
avg max Jaccard to active = 0.375
avg max overlap to active = 0.583
```

代表性 returned set：

```text
[2,13,20]  best active [11,13,20], overlap 0.667
[2,3,20]   best active [2,3,19], overlap 0.667
[2,20]     best active [2,3,19], overlap 0.5
```

这说明 return12 cg3 的 `[2,20]` family 更像当前 active basis 的局部变体 / redundant replacement，而不是会触发新 active trajectory 的 bridge。

## 为什么 low-overlap 误判

low-overlap aggregate rule 的问题是：

1. 它把前三轮 returned sets 混在一起看；
2. 它没有区分 batch 所在 CG stage；
3. 它没有判断当前 active basis 是否已经被前两轮改写到不同 context；
4. 它没有判断某一轮 batch 加入后是否实际改变 RMP objective / active hash；
5. 它没有区分“全局分散”与“当前 active context 下的 marginally useful bridge”。

return12 r2 的 first3 aggregate overlap 很低，是因为：

- cg1/cg2 returned batch 确实更宽；
- 但这两轮也把 active/dual context 推到了不同路径；
- 到 cg3 时，returned batch 只剩 weak RC 的 `[2,20]` family；
- 这批 cg3 columns 与当前 active top samples 有较高 overlap；
- 加入后 active hash 和 RMP objective 完全不动。

因此：

> 低 overlap 是必要性候选信号，但不是充分条件。真正需要的是 stage-aware、context-aware 的 returned-batch selector：既要控制 batch diversity，也要判断它对当前 active basis 是否有 marginal bridge value。

## 对根因的进一步收紧

当前根因可进一步写成：

> 20-task hard-tail 的有益 early batch 不只是“低 overlap / 更分散”，而是“在当前 RMP active basis context 下，低冗余且能桥接 fractional active families、推动 active hash / RMP objective 变化的 concrete JourneyColumn signature batch”。return12 r2 低 overlap 但 worsened，是因为其后期 returned batch 退化为 weak-RC、active-redundant 的 `[2,20]` family，没有形成有效 marginal active-basis movement。

这解释了为什么：

- return12 有时改善、有时恶化；
- 全局 overlap 特征能做到 17/18，但仍会误判关键 Apollo20 case；
- future-hit / active sample hit 也不够，因为要看 stage 和 marginal movement；
- production selector 不能只按 batch diversity 排序。

## 下一步

如果继续，应仍然保持 calibration-only：

1. 增加 candidate-list 层完整 returned/truncated batch diagnostics，避免 capped addition samples；
2. 对每一轮 candidate batch 计算 stage-aware features：
   - pair overlap / pair jacc；
   - max relation to current active top samples；
   - active-family bridge score；
   - weak RC / best RC distribution；
   - signature / start-time / arc-option diversity；
   - whether batch is concentrated on one active-redundant family；
3. 离线模拟 selector 时必须单独处理 Apollo20 return12 r2：
   - 若规则仍选中 cg3 `[2,20]` family，则不合格；
4. 在解释该 false positive 前，不应做 production A/B。

## 目标状态

目标仍未完成。

本轮说明 low-overlap 是更强的根因特征候选，但也证明它不是最终优化方向。当前还需要一个能排除 active-redundant low-overlap false positive 的 stage/context-aware selector。

