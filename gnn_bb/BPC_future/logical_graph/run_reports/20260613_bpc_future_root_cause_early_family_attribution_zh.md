# BPC_future Root-cause Early-family Attribution 报告

日期：2026-06-13

## 目标

本轮继续根因审计，不做主线大修改。

目标是验证上一份根因报告提出的候选方向：

> context-aware early-column / active-family trajectory control

是否能进一步收敛为可执行的优化方向。

本轮只做离线归因：

- 读取已有 Phase 10H summary；
- 按 instance / profile / repeat 提取 early task-set sequence；
- 比较 improved / worsened / baseline 中出现的 family；
- 判断“early family 本身”是否足以解释 20-task 改善。

不改 solver，不启用 worker，不改 certificate / lower-bound。

## 数据来源

输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.json`

该矩阵包含：

- instances：
  - `tranq20_01`
  - `mt20_greedy_apollo_01`
  - `mt20_greedy_tranq_01`
- profiles：
  - baseline
  - `experimental_early_new_task_set_quota_3_20_only`
  - `experimental_early_new_task_set_quota_3_return12_20_only`
- repeat-count：3
- rows：27

## 方法

对每行读取：

- `instance`
- `profile`
- `repeat_index`
- `improvement_class`
- `official_primal_bound`
- `early_column_primary_task_set_sequence`

然后按 instance 聚合：

- baseline family；
- improved family；
- worsened family；
- improved-only family；
- worsened-only family。

判定规则：

- 如果某个 family 只在 improved rows 中反复出现，且 baseline / worsened 中不出现，则它是 strong positive candidate；
- 如果某个 family 同时出现在 improved 和 worsened rows，则 family 本身不足以解释 outcome；
- 如果 improved row 没有独有 family，则不能把该 instance 的改善归因到单个 early task-set。

## 结果 1：`tranq20_01` 有干净的 positive early-family 信号

Baseline 三次 repeat 的 early families 完全一致：

```text
[5,15,20]
[4,13,18]
[4,6,13]
```

两个 quota profiles 的 6 个 improved rows 中，反复出现 task-1 anchored families：

| family | improved count | baseline count | worsened count |
|---|---:|---:|---:|
| `[1,3,6]` | 6 | 0 | 0 |
| `[1,3,10]` | 6 | 0 | 0 |
| `[1,15,20]` | 6 | 0 | 0 |
| `[1,3,9]` | 5 | 0 | 0 |
| `[2,7,15]` | 5 | 0 | 0 |
| `[1,8,14]` | 4 | 0 | 0 |
| `[1,2,13]` | 3 | 0 | 0 |
| `[1,2,18]` | 3 | 0 | 0 |
| `[1,3,5]` | 3 | 0 | 0 |
| `[1,13,18]` | 3 | 0 | 0 |

对应 primal：

- baseline：三次都是 `781.101309`；
- return8：`597.118613`, `596.176491`, `594.045835`；
- return12：`605.126958`, `593.924951`, `605.126958`。

判断：

`tranq20_01` 上，early-column trajectory 的正向证据很强。这里的改善不是随机噪声，也不是 Pulse worker 结果，而是 20-only early quota 改变了 early family，使后续 RMP trajectory 进入更好的 incumbent path。

## 结果 2：`mt20_greedy_tranq_01` 证明 early family 本身不够

Baseline 三次 repeat 的 early families 完全一致：

```text
[8,10,13]
[2,7,10,17]
[2,7,9,17]
[3,4]
[8,12]
[13,16]
[2,7,9]
[1,6,15]
```

两个 quota profiles 的 early sequence 也完全一致：

```text
[3,4]
[1,2,7]
[4,19]
[1,3]
```

但 outcome 相反：

- return8：三次 `worsened`，primal = `829.395319`；
- return12：三次 `improved`，primal = `704.228463`。

判断：

这直接证伪了“只要识别 early task-set family 就能优化”的简单解释。

对于 `mt20_greedy_tranq_01`，同一组 early families 在不同 return quota 下方向相反。根因必须包含更细的 context：

- returned column count / quota；
- materialized journey set；
- RMP active path；
- 后续 active basis transition；
- 或同 family 下不同具体 journey 的 cost / timing / signature 差异。

因此下一步不能只做“task-set family 白名单”。

## 结果 3：`mt20_greedy_apollo_01` 没有干净 positive family

Baseline repeats：

```text
rep0: [5,8,15], [5,12,18], [12,16,17], [4,5,8] -> primal 847.812231
rep1: [5,8,15], [5,12,18], [2,9] -> primal 921.640296
rep2: [5,8,15], [5,12,18] -> primal 921.640296
```

Quota profiles：

- return8：
  - two worsened rows；
  - one improved row `770.211317`；
  - early sequence overlaps heavily with worsened rows。
- return12：
  - three worsened rows；
  - repeated `[4,5,8]`, `[16,17]`。

Family counts：

| family | improved | worsened | baseline |
|---|---:|---:|---:|
| `[4,5,8]` | 1 | 5 | 1 |
| `[3,12,17]` | 1 | 1 | 0 |
| `[14,18]` | 1 | 1 | 0 |
| `[2,20]` | 1 | 1 | 0 |
| `[16,17]` | 0 | 3 | 0 |

判断：

`mt20_greedy_apollo_01` 没有 improved-only family。唯一清楚的是 `[16,17]` 偏负向，但这只能解释部分 worsened rows，不能解释 improved row。

因此 Apollo20 的根因更像：

- 同一 task-set family 下的具体 journey / timing / signature 差异；
- early active hash path；
- RMP fractional / degeneracy trajectory；
- 或后续 profile-DP / ordinary pricing tail 的交互。

不能把 Apollo20 的优化方向简化为 early task-set family selection。

## 根因判断更新

上一份根因报告的结论需要进一步收紧：

原判断：

> early-column / active-family trajectory sensitivity 是最有证据的根因。

更新后更精确的判断：

> 20-task hard set 的根因是 early-column 到 RMP active trajectory 的上下文敏感性；task-set family 是其中一层可观测信号，但单独不够。必须同时看 instance、return quota、具体 journey materialization、active basis path 和后续 pricing tail。

支持：

- `tranq20_01`：early family 足够解释改善；
- `mt20_greedy_tranq_01`：同 family 在不同 return quota 下方向相反；
- `mt20_greedy_apollo_01`：没有 clean positive family，只有 partial negative family。

## 不能做的结论

当前仍不能说：

- 已经百分百确定优化方向；
- 只要优先某些 early task-set family 就能稳定优化；
- task-set family whitelist 可以默认启用；
- 20-task 已经能大幅加速；
- 5/10 no-regression 已能和 20 improvement 同时满足。

这些都还没有证据。

## 下一步建议

下一步如果继续验证，应该做 Phase RC-B：

**per-context early-trajectory replay / intervention design**

目标不是 production 优化，而是回答：

1. 对 `tranq20_01`，强制/优先 task-1 anchored families 是否可复现改善，同时不增加 incomplete；
2. 对 `mt20_greedy_tranq_01`，同一 early family 下 return8 与 return12 的 materialized journeys / active basis 差异是什么；
3. 对 `mt20_greedy_apollo_01`，改善 row 与 worsened row 在具体 JourneyColumn signature / timing / cost / active hash path 上有什么差异；
4. 能否构造一个 context rule，而不是 global rule。

验收条件：

- 只做 calibration-only；
- 5/10 no-op；
- selected 20-task 每个 hard case 不回退；
- 至少两个 hard case repeat 改善；
- no critical disagreement；
- no certificate / lower-bound effect。

如果 RC-B 仍不能形成稳定正证据，则应停止 early-trajectory tuning，把下一步转向更底层的 RMP formulation / active-family stabilization 或 legacy proof-tail 重构。

## Exactness 边界

本轮只做离线归因和报告：

- 不改变 solver；
- 不改变 pricing；
- 不改变 RMP；
- 不改变 default config；
- 不启用 worker；
- 不启用 certificate gate；
- 不改变 lower-bound 规则。

## 验证

本轮归因使用只读 Python 脚本读取已有 `summary.json`。

报告写入后运行：

```bash
git diff --check
```

结果：

```text
git diff --check: passed
BPCFutureTests: Ran 483 tests in 1.461s OK (skipped=1)
```
