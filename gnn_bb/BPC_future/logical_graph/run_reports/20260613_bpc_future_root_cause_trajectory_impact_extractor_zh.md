# BPC_future 根因审计补充：trajectory impact extractor

日期：2026-06-13

## 目标

上一轮已经排除了几个单一 scalar：

- priority task-set 命中；
- returned 数量；
- immediate `active_support_changing`；
- final fractional pressure。

本轮继续做只读归因，尝试抽取更接近真实机制的 trajectory 特征：

1. addition 中的 task-set sample 是否在后续 active basis sample 中出现；
2. 后续 active basis 是否出现 `fractional_sum=0`；
3. 是否出现 integral RMP incumbent update；
4. active hash churn 与 RMP objective delta。

本轮不改 solver、pricing、RMP、Pulse worker、certificate 或 lower-bound。

## 数据

只读输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/*.jsonl`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/summary.csv`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/logs/*.jsonl`

抽取事件：

- `journey_column_addition`
- `journey_pool_structure_diagnostics`
- `journey_rmp`
- `journey_certificate_candidate_updated`

注意：当前 active hit 只基于 JSONL 中记录的 `pool_active_top_task_set_value_samples`，这些是 capped samples，不是完整 active set。因此本轮结论只作为保守 evidence，不作为完整证明。

## 汇总结果

### Phase 10H hard set

| instance/profile/outcome | avg primal | future active hit sets | zero-fractional diagnostics | active hash churn | incumbent updates |
|---|---:|---:|---:|---:|---:|
| `tranq20_01` return8 improved | 595.780 | 12.667 | 3.667 | 6.667 | 3.667 |
| `tranq20_01` return12 improved | 601.393 | 9.333 | 3.333 | 7.000 | 3.333 |
| `mt20_greedy_tranq_01` return8 worsened | 829.395 | 8.000 | 0.000 | 4.000 | 0.000 |
| `mt20_greedy_tranq_01` return12 improved | 704.228 | 7.000 | 1.000 | 4.000 | 1.000 |
| `mt20_greedy_apollo_01` return8 worsened | 1061.554 | 3.500 | 1.000 | 2.500 | 0.000 |
| `mt20_greedy_apollo_01` return8 improved | 770.211 | 6.000 | 2.000 | 4.000 | 1.000 |
| `mt20_greedy_apollo_01` return12 worsened | 1061.554 | 1.333 | 1.000 | 2.000 | 0.000 |

### RC-C / return12 ablation

| instance/profile/outcome | avg primal | future active hit sets | zero-fractional diagnostics | active hash churn | incumbent updates |
|---|---:|---:|---:|---:|---:|
| `tranq20_01` return12 improved | 587.058 | 9.000 | 3.000 | 6.000 | 2.000 |
| `tranq20_01` RC-C improved | 589.388 | 11.000 | 2.000 | 6.667 | 2.000 |

## 关键发现 1：future active hit 比 immediate active_changed 更接近机制，但仍不充分

Immediate `active_changed` 在 Phase 10H 中全是 0，无法解释 improved/worsened。

future active hit 能看到“先 inactive，后进入 active basis”的路径。例如 `tranq20_01` return8 improved：

- cg1 addition 中的 `[5,15,20]` 后续进入 active basis；
- cg3 addition 中的 `[1,3,6]` / `[6,10,12]` 后续进入 active basis；
- cg4 addition 中的 `[1,3,10]` 后续进入 active basis；
- cg7 addition 中的 `[1,9,15]` family 继续推动 active path。

这说明上一轮的 `inactive_addition_enters_active_basis` 不是标签噪声，而是真实机制。

但是 future active hit 仍不充分：

- `mt20_greedy_tranq_01` return8 worsened 的 future active hit sets 平均为 `8.0`；
- `mt20_greedy_tranq_01` return12 improved 的 future active hit sets 平均为 `7.0`。

也就是说，“进入 active basis”本身还不够；进入后把 active path 推向哪里才关键。

## 关键发现 2：zero-fractional episodes 与 incumbent update 更能解释 outcome，但它们是事后信号

在 Phase 10H 中：

- `tranq20_01` improved rows 都有多次 `fractional_sum=0`，并多次更新 integral incumbent；
- `mt20_greedy_tranq_01` return12 improved 有 1 次 zero-fractional diagnostic 与 1 次 incumbent update；
- `mt20_greedy_tranq_01` return8 worsened 没有 zero-fractional diagnostic，也没有 incumbent update；
- `mt20_greedy_apollo_01` return8 r2 improved 有 2 次 zero-fractional diagnostic 与 1 次 incumbent update；
- Apollo worsened rows虽然也可能有一次 zero-fractional diagnostic，但没有 incumbent update。

这比 final fractional pressure 更合理，因为它看的是路径中是否曾进入可产生 incumbent 的 integral active basis。

但这仍然不是可直接用于 pricing selection 的规则：

- zero-fractional 和 incumbent update 要等 RMP solve 后才知道；
- 它是 outcome 解释，不是事前可用的 safe pruning 或 selection signal；
- 直接把它当 production rule 会形成 hindsight bias。

## 关键发现 3：相同 family / 相近 active hit，具体 JourneyColumn signature 仍决定分叉

`mt20_greedy_apollo_01` return8 r0 与 r2 前两轮 additions 几乎一致，但 cg3 后分叉：

- r0 worsened：
  - cg3 signature `a0cff104367cbbc7`；
  - samples 包含 `[4,14,18]`；
  - 后续 `fractional_sum=5.75`；
  - 没有 incumbent update。
- r2 improved：
  - cg3 signature `ce10940e649c88ce`；
  - samples 包含 `[5,10,18]`；
  - cg4 `fractional_sum=0`；
  - 有 incumbent update。

这进一步说明：

- task-set family 不够；
- future active hit 不够；
- 需要具体 JourneyColumn signature / timing / replacement effect 进入 trajectory model。

## 根因更新

当前最准确的解释是：

> 20-task hard set 的收益来自 early additions 触发的 active-basis path 改写；但现有机制只能后验观察这条 path，不能在定价阶段稳定预测哪些 columns 会把 RMP 推到好 path。

这解释了为什么做了很多仍然不行：

1. Pulse / profile-DP 能找 negative columns，但 negative 不等于有益 active trajectory；
2. return12 能增加触发好 path 的机会，但也可能触发坏 path；
3. priority whitelist 能复现单个 `tranq20_01` 的一部分路径，但不是普适规则；
4. active_changed / future_active_hit / fractional pressure 都只是 path 的局部投影；
5. 5/10 小实例太快，不能承担“多试一些 path”的默认开销；
6. 因此没有一个可泛化、exact-safe、低开销的事前选择器时，就无法同时满足 5/10 no-regression 和 20-task 大幅优化。

## 对下一步的约束

下一步如果继续 root-cause 方向，应该做：

- calibration-only trajectory model；
- 输入是 addition 前可见或低成本可见的特征：
  - candidate task-set；
  - candidate signature / timing；
  - relation to current active top samples；
  - relation to recent active families；
  - rough reduced cost；
  - replacement/new/support-changing class；
  - current fractional pressure state；
  - dual movement state。
- 输出只用于离线解释 improved/worsened，不能直接改变 production path。

不应该做：

- 默认 return12；
- 继续扩大 Pulse worker budget；
- 继续手写 priority whitelist；
- 打开 official certificate gate；
- 用 future active hit 或 incumbent update 这种事后信号直接做在线选择。

## 目标状态

目标仍未完成。

本轮增强了根因解释的证据：

- 不是 “找不到 negative columns”；
- 不是 “某个 scalar 没调好”；
- 而是 “没有可事前预测有益 active-basis trajectory 的 exact-safe selector”。

但这还不是最终优化方向的证明，因为尚未证明任何 selector 能在 5/10 不退化下稳定大幅优化 selected 20-task hard set。

## 验证

本轮为只读 JSONL/CSV 归因和文档更新。

抽取脚本只读取既有结果文件，未修改求解语义。
