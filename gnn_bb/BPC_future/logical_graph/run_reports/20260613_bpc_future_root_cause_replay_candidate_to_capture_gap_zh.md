# BPC_future 根因审计补充：replay candidates 与 clean capture 的缺口

日期：2026-06-13

## 目的

本轮不运行 solver，不修改 pricing / RMP / Pulse 主线。

目的只回答一个问题：

> 当前已经筛出的 counterfactual replay 候选，是否已经有足够的 exact-context clean capture 样本支撑 selector / worker 优化方向？

答案是否定的。

## 已有 replay candidate 证据

`counterfactual replay candidates` manifest 已经从现有 observational logs 中筛出：

```text
candidate_count = 40
low_context_noise_candidate_count = 3
mixed_descriptor_context_candidate_count = 37
recommended_candidate_ids = [
  replay_candidate_001,
  replay_candidate_003,
  replay_candidate_004
]
```

这说明现有日志里确实有一些值得做 counterfactual replay 的 exact-context pairs。

推荐首批候选分别覆盖：

| candidate | instance | context | 风险 | 为什么重要 |
|---|---|---|---|---|
| `replay_candidate_001` | `mt20_greedy_tranq_01` | `cg_iter=2`，active hash `5c6420f757a39d2d` | low-context-noise | improved descriptor 的 RC 反而没有 worsened descriptor 更负，可检验“更负 RC 不等于更好” |
| `replay_candidate_003` | `mt20_greedy_apollo_01` | `cg_iter=3`，active hash `16862add48072518` | low-context-noise | 同一 exact context 下 returned batch 截断差异明显 |
| `replay_candidate_004` | `tranq20_01` | `cg_iter=1`，active hash `aa2b834c9d43f2a6` | mixed-descriptor stress | return12 与 single-return descriptor 对照，适合压力测试 batch effect |

这些候选的价值是给出下一步 replay target，而不是直接证明优化方向。

## 当前 clean capture 证据

全局扫描当前 `BPC_future/results` 后，clean capture 样本仍严重不足：

```text
files_scanned = 8659
global_capture_event_count = 4
global_ready_20_case_count = 1
global_ready_20_context_count = 1
global_nonready_missing_vehicle_count = 3
```

唯一 ready 的 20-task clean replay context 仍是 Apollo20 v2：

```text
capture_case_0004
task_count = 20
context_hash = 080a188d2484ee3e
candidate_count = 4
best_objective_delta = -137.116184
```

这证明 high-impact returned batch 真实存在，但它仍是单一 ready 20-task context。

## 缺口定义

当前缺口可以直接量化为：

```text
recommended_candidate_count = 3
global_ready_20_context_count = 1
recommended_candidate_minus_ready_20_context_count = 2
```

更重要的是，推荐候选中的 `mt20_greedy_tranq_01`、`mt20_greedy_apollo_01`、`tranq20_01` 都仍主要是 observational candidate 或 descriptor-level target，不是已经可用于 RMP treatment replay 的完整 payload。

完整 payload 至少要包括：

- RMP pool；
- returned batch；
- true dual；
- cuts；
- effective fleet context；
- vehicle count；
- signature；
- arc option ids；
- start times；
- enough metadata to make control RMP `OPTIMAL` and single-candidate deltas finite。

## 对“为什么还不行”的含义

这一步把当前结论进一步收紧：

1. **不是没有 replay target。** 现在已有 40 个候选、3 个首批推荐候选。
2. **不是 high-impact batch 不存在。** Apollo20 clean replay 已经有 `-137.116184` local RMP objective delta。
3. **问题是 clean replay calibration 样本不足。** 当前只有 1 个 ready 20-task context，不能支撑 production selector 或 worker gate。
4. **所以不能把 root-cause explanation 误报成 optimization solution。** 根因解释已经强，但可上线优化方向仍未证明。

## 下一步门槛

下一步应该优先把推荐候选转成 no-certificate-effect exact-context capture，而不是继续叠 Pulse worker budget、target ordering 或 certificate gate。

最小门槛：

```text
ready_20_context_count >= 3
all controls OPTIMAL
all single candidate deltas finite
has high-impact and no-op / low-impact contrast
selector only uses addition-before visible features
selector passes cross-context / cross-instance gate
```

在这些条件满足前，不能说已经找到：

> 保证 exactness、5/10 不退化，同时大幅加速 20-task 最优求解的 production 优化方向。

## Verifier 对应项

新增 evidence ledger section：

```text
counterfactual_replay_candidate_to_capture_gap
```

关键检查：

```text
check_replay_candidate_targets_not_yet_exact_capture_ready = true
```

该检查要求同时满足：

- replay candidate manifest 有 40 个候选；
- low-context-noise candidate 为 3 个；
- 推荐候选为 `replay_candidate_001 / 003 / 004`；
- global capture scan 只有 1 个 ready 20-task context；
- 3 个 non-ready case 都因为缺少 vehicle count 等 payload 问题不能 replay；
- 本报告存在。

## 结论

当前最准确的判断是：

> 我们已经知道该去哪里做 counterfactual replay，但还没有足够 clean exact-context replay 样本来证明一个 production selector。

因此当前目标仍未完成，后续应先补 replay capture calibration，而不是继续推进主线求解器修改。
