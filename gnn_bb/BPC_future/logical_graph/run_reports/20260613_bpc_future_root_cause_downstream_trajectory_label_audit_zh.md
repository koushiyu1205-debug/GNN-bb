# BPC_future 根因审计补充：downstream trajectory label audit

日期：2026-06-13

## 目标

上一轮 per-batch movement audit 已经证明：

- `immediate objective_delta < 0` 太宽；
- `active_hash_changed` 太宽；
- 绝大多数 worsened batches 也会让下一轮 RMP 移动；
- 因此不能把“加入后 RMP 当轮动了”当作优化目标。

本轮继续只读分析，把每个 heuristic returned batch 关联到后续 1-2 轮 trajectory 标签，检查真正区分 improved / worsened 的是否是后续 active-basis / incumbent path，而不是当轮 RC 或当轮 movement。

本轮不改 solver、pricing、RMP、Pulse worker、certificate 或 lower-bound。

## 数据

输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/*.jsonl`

分析集：

- Phase 10H 非 baseline 20-task rows；
- 18 runs；
- improved 10，worsened 8；
- 逐 run 读取前 4 个 heuristic `journey_pricing` returned batch；
- 形成 64 个 per-stage batch rows。

每个 batch 的前置特征：

- returned task-set pair overlap / Jaccard；
- union size；
- best reduced cost；
- 与当前 active top samples 的 avg max overlap / Jaccard；
- active-redundant fraction；
- active-bridge fraction。

每个 batch 的 downstream 标签：

- `zero_within2`：后续 2 个 pool diagnostics 内是否出现 `pool_active_fractional_value_sum = 0`；
- `incumbent_within2`：后续 2 个 CG 迭代内是否出现 `journey_certificate_candidate_updated`；
- `next_negative_count`：后续 2 个 CG 内 `FOUND_NEGATIVE` pricing 次数；
- `next_incomplete_count`：后续 2 个 CG 内 `INCOMPLETE*` pricing 次数；
- `d1_obj` / `d2_obj`：后续 1 / 2 个 RMP objective 相对当前 RMP objective 的变化。

注意：

- `zero_within2` 与 `incumbent_within2` 是事后标签，只能解释 root cause，不能直接作为线上 selector 输入；
- active top samples 是 capped JSONL diagnostics，不是完整 active basis，因此 active-relation 结论仍是保守证据。

## Run-level downstream 标签

18 个非 baseline 20-task runs：

```text
runs = 18
improved = 10
worsened = 8
```

Run-level 结果：

| outcome | runs | any incumbent update | any zero-fractional | avg incumbent updates | avg zero-fractional diagnostics | avg active hash churn |
|---|---:|---:|---:|---:|---:|---:|
| improved | 10 | 10 | 10 | 2.5 | 2.6 | 5.7 |
| worsened | 8 | 0 | 5 | 0.0 | 0.625 | 2.875 |

这说明：

- Phase 10H 中所有 improved runs 都出现了 incumbent update；
- 所有 worsened runs 都没有 incumbent update；
- zero-fractional episode 在 worsened 中也可能出现，因此“曾经 fractional_sum=0”不是充分条件；
- incumbent update 是更强的事后 outcome marker，但它不能在线使用。

Compact run rows：

| instance/profile/repeat | outcome | primal | incumbent updates | zero-fractional diagnostics | active hash churn | final fractional sum |
|---|---:|---:|---:|---:|---:|---:|
| `tranq20_01 / return8 / r0` | improved | 597.118613 | 3 | 3 | 6 | 0.0 |
| `tranq20_01 / return12 / r0` | improved | 605.126958 | 3 | 3 | 7 | 7.0 |
| `tranq20_01 / return8 / r1` | improved | 596.176491 | 4 | 4 | 7 | 0.0 |
| `tranq20_01 / return12 / r1` | improved | 593.924951 | 4 | 4 | 7 | 0.0 |
| `tranq20_01 / return8 / r2` | improved | 594.045835 | 4 | 4 | 7 | 0.0 |
| `tranq20_01 / return12 / r2` | improved | 605.126958 | 3 | 3 | 7 | 7.0 |
| `mt20_greedy_apollo_01 / return8 / r0` | worsened | 1061.554044 | 0 | 1 | 3 | 5.75 |
| `mt20_greedy_apollo_01 / return12 / r0` | worsened | 1061.554044 | 0 | 1 | 2 | 1.666666667 |
| `mt20_greedy_apollo_01 / return8 / r1` | worsened | 1061.554044 | 0 | 1 | 2 | 5.75 |
| `mt20_greedy_apollo_01 / return12 / r1` | worsened | 1061.554044 | 0 | 1 | 2 | 1.666666667 |
| `mt20_greedy_apollo_01 / return8 / r2` | improved | 770.211317 | 1 | 2 | 4 | 5.75 |
| `mt20_greedy_apollo_01 / return12 / r2` | worsened | 1061.554044 | 0 | 1 | 2 | 1.666666667 |
| `mt20_greedy_tranq_01 / return8 / r0` | worsened | 829.395319 | 0 | 0 | 4 | 7.75 |
| `mt20_greedy_tranq_01 / return12 / r0` | improved | 704.228463 | 1 | 1 | 4 | 7.75 |
| `mt20_greedy_tranq_01 / return8 / r1` | worsened | 829.395319 | 0 | 0 | 4 | 7.75 |
| `mt20_greedy_tranq_01 / return12 / r1` | improved | 704.228463 | 1 | 1 | 4 | 7.75 |
| `mt20_greedy_tranq_01 / return8 / r2` | worsened | 829.395319 | 0 | 0 | 4 | 7.75 |
| `mt20_greedy_tranq_01 / return12 / r2` | improved | 704.228463 | 1 | 1 | 4 | 7.75 |

## Per-stage downstream 标签

64 个 per-stage batch rows：

| outcome | rows | `zero_within2` | rate | `incumbent_within2` | rate |
|---|---:|---:|---:|---:|---:|
| improved | 40 | 26 | 0.65 | 26 | 0.65 |
| worsened | 24 | 0 | 0.00 | 0 | 0.00 |

这比 immediate movement 更有解释力：

- immediate strong movement 是 `63/64`，几乎无法区分 final outcome；
- downstream incumbent / zero-fractional 标签只出现在 improved rows；
- 但仍然是事后标签，不能直接用于在线选择。

## Outcome aggregate

| outcome | next negative count | next incomplete count | d1 objective delta | d2 objective delta | active avg overlap | active redundant frac | pair overlap | pair Jaccard | union size |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| improved | 1.7 | 0.6 | -45.904192 | -79.639566 | 0.532118 | 0.232292 | 0.413203 | 0.286608 | 9.2 |
| worsened | 1.0 | 2.0 | -74.451478 | -123.743164 | 0.684606 | 0.538194 | 0.441533 | 0.305330 | 7.708333 |

关键点：

- worsened rows 的 `d1/d2 objective_delta` 反而更大；
- worsened rows 的 next incomplete count 更高；
- improved rows 的 active overlap / redundancy 更低，union 更大；
- 因此“强 immediate RMP improvement”不是好方向，低 active redundancy 和低后续 incomplete 更接近机制。

## Stage aggregate

| stage | outcome | rows | zero within2 | incumbent within2 | active avg overlap | active redundant frac | next negative count | d2 objective delta |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| cg1 | improved | 10 | 9 | 9 | 0.550000 | 0.125000 | 2.0 | -123.194352 |
| cg1 | worsened | 8 | 0 | 0 | 0.820312 | 0.671875 | 1.625 | -216.446136 |
| cg2 | improved | 10 | 10 | 10 | 0.568750 | 0.337500 | 2.0 | -71.022693 |
| cg2 | worsened | 8 | 0 | 0 | 0.657986 | 0.614583 | 1.0 | -41.334398 |
| cg3 | improved | 10 | 7 | 7 | 0.565972 | 0.316667 | 1.6 | -60.422417 |
| cg3 | worsened | 5 | 0 | 0 | 0.620833 | 0.525000 | 0.6 | -13.883184 |
| cg4 | improved | 10 | 0 | 0 | 0.443750 | 0.150000 | 1.2 | -53.438296 |
| cg4 | worsened | 3 | 0 | 0 | 0.500000 | 0.000000 | 0.0 | 0.0 |

解释：

- cg1 中 worsened rows 的 d2 objective drop 更大，但没有 downstream incumbent；
- cg1/cg2 的 active redundancy 差异很明显；
- cg4 的 downstream window 已接近日志尾部，不能用 `within2` 判断强弱；
- late-stage 有益性仍需要结合当前 active basis 和 residual tail，而不是只看 objective drop。

## Pre-feature separability 复核

用 64 个 stage rows 的 final outcome 做标签，单特征阈值最强仍是 active-relation 类：

```text
active_avg_overlap <= 0.5555555555555556
accuracy = 0.765625
tp = 32
fp = 7
tn = 17
fn = 8
```

```text
active_redundant_frac <= 0.25
accuracy = 0.765625
tp = 32
fp = 7
tn = 17
fn = 8
```

```text
best_rc >= -62.6272465
accuracy = 0.765625
tp = 38
fp = 13
tn = 11
fn = 2
```

注意：

- `best_rc >= -62.6272465` 的形式本身说明“更负不一定更好”；
- 但它 false positive 仍多，不能作为 production rule；
- active relation 仍是目前更可信的 preobservable negative-filter 信号，但还不足以证明优化方向。

## Apollo r2 关键分叉复核

### return8 r2 improved / cg3

```text
returned_count = 8
best_rc = -20.1912655
d1_obj = -10.375179
d2_obj = -13.717869
zero_within2 = True
incumbent_within2 = True
next_pricing_states = FOUND_NEGATIVE, INCOMPLETE_LIMIT, INCOMPLETE_LIMIT, INCOMPLETE_LIMIT
active_avg_overlap = 0.4791666667
active_redundant_frac = 0.125
active_bridge_frac = 0.875
```

### return12 r2 worsened / cg3

```text
returned_count = 4
best_rc = -6.110727
d1_obj = 0.0
zero_within2 = False
incumbent_within2 = False
next_pricing_states = INCOMPLETE_LIMIT, INCOMPLETE_LIMIT, INCOMPLETE_LIMIT
active_avg_overlap = 0.5833333333
active_redundant_frac = 0.5
active_bridge_frac = 0.5
```

这进一步支持：

- good trajectory 不是来自更负 RC，而是来自 late-stage active-family bridge；
- bad trajectory 可能在早期有大 objective drop，但后续进入 incomplete tail；
- returned batch 必须按 stage/context 判断，而不是全局 return-count 或全局 low-overlap。

## 根因更新

本轮把根因表述进一步收紧为：

> 当前系统缺少一个 addition 前可见的 trajectory selector。它不是要预测“当前 batch 是否为负”或“加入后 RMP 是否会动”，而是要预测这个 concrete JourneyColumn batch 是否会在后续 1-2 轮把 active basis 推向 incumbent-producing path，并降低 residual pricing tail。现有 RC、return count、simple diversity、Pulse worker 都不具备这个选择能力。

这解释了为什么之前做了很多仍然不行：

1. Pulse 能加 true-RC negative columns，但不能保证这些 columns 进入好 trajectory；
2. return8/return12 能增加探索机会，但也可能把 trajectory 推向 redundant / incomplete path；
3. immediate objective drop 在 worsened 中也大量存在，不能作为优化目标；
4. 5/10 的固定开销预算太小，不能靠“多试一些 trajectory”默认探索；
5. 20 的有效优化必须是 low-overhead、stage-aware、active-context-aware 的 returned-batch selector。

## 仍未完成的部分

本轮是更强的 root-cause evidence，不是 production 优化证明。

仍未证明：

- 哪个 addition-before selector 能稳定选中 improved rows；
- 该 selector 能保护 5/10 no-regression；
- 该 selector 能在 20-task 上稳定大幅减少 wall time / tail；
- 该 selector 在 exactness/certificate 边界下可安全接入。

因此目标仍未完成，不能宣布优化方向已经百分百确定。

## 下一步建议

继续 calibration-only，不做主线大修改。

下一步应构造一个 returned-batch trajectory dataset：

- row = candidate batch / returned batch / CG stage；
- features 只允许使用 addition 前可见信息：
  - task-set union / pair overlap / Jaccard；
  - relation to current active top samples；
  - active-redundant / active-bridge fraction；
  - best/median/worst RC；
  - sequence/signature/start-time/arc-option diversity；
  - current RMP fractional pressure；
  - recent active family churn；
- labels 使用事后 trajectory：
  - next 1-2 CG incumbent update；
  - next 1-2 CG zero-fractional；
  - next pricing incomplete/negative sequence；
  - final primal/gap vs baseline。

只有当这个 dataset 找到可泛化 selector，并通过 5/10 guard 与 20-task repeat smoke 后，才可以考虑主线优化。

