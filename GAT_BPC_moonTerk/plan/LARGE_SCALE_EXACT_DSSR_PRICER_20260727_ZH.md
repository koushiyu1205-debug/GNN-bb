# 大规模 Exact DSSR Pricer 设计契约（2026-07-27）

## 1. 问题与实验语义

当前机器的 Linux 可见内存约为 15.5 GiB。P0 V3 的完整 elementary
labeling 在 scale50/100 上会先达到 Native/host 内存门槛，因此已有
`MEMORY_CENSORED_INCOMPLETE` 只能说明当前状态空间在该机器上无法继续，
不能当作 3600 秒 time-limit 结果、最优性结果或无负 reduced-cost 证明。

文献中常见的 “3600 秒未解”并不等价于“让完整 elementary frontier
不受约束地增长”：

- Nafstad、Desaulniers 和 Stålhane（Transportation Science, 2025）的
  BP&C 实验使用 384 GB RAM；pricing 先用 rank-3/rank-6 reduced network
  heuristic，再调用 exact，并用 bidirectional labeling 缓解完整单向
  labeling 的指数标签增长。
- 近年的 exact VRP 方法普遍结合 ng-route/DSSR、limited-memory cuts、
  reduced-network pricing、双向 labeling 或问题特定 completion bound。
- 论文的 time limit 只有在其内存/算法能够保留完整 proof state 至该时刻时，
  才与本项目需要的 3600 秒语义一致。

所以本候选的目标不是取消内存保护，而是降低 exact proof state 的规模，
使 scale50 的主要终止类型由 memory limit 转为：

1. 找到一个经过完整审计的 elementary negative column；
2. 松弛 pricing 被完整穷尽并给出 exact no-negative 证明；
3. frontier 仍完整保留时达到 3600 秒 time limit。

## 2. 与 P0 的隔离

- P0 V3 继续由
  `FROZEN_P0V3_FULL_RUNTIME_CAPSULE_20260727` 完整保存。
- 新 pricer 使用独立 backend ID、engine hash、build directory 和实验配置。
- 所有支持规模的 exact-proof 调用统一使用同一个 DSSR 算法和 policy；
  scale5/10 不再旁路。规模只用于分层报告和 promotion gate，不能改变
  算法身份。
- 为保持端到端生命周期公平，5/10/20/30 使用与 P0 相同的 in-process
  执行形态，50/100 使用与 P0 相同的 host-isolated 形态；两者只共享
  DSSR policy，不引入额外的规模算法分支。
- negative-harvest 调用继续保持 P0 elementary 路径；这是 pricing phase
  的职责分离，不是规模特判。
- 不修改 production 默认 `no_cut`，不覆盖 P0 V3 baseline registry 条目。
- 所有差分先确认 5/10 确实执行 DSSR 且不退化，再进入 20/30，最后对
  scale50 和 scale100 各一个实例依次做 3600 秒单实例验证；不得用
  scale50 的结果替代 scale100 证据。

## 3. 状态空间松弛

设 `E` 为所有可行 elementary 多-sortie journey，`R(C)` 为 critical task
集合 `C` 下的 DSSR journey 集：

- `C` 中任务禁止重复；
- `C` 外任务可重复；
- 每条 journey 的总 task visit 数不超过实例任务数 `n`；
- 原有时间、单-sortie 容量、能量、shadow、branch 和 cut 资源仍执行；
- `completion_bound` 与原有 subset dominance 在 DSSR 中强制关闭。

于是对任意 `C`：

```text
E ⊆ R(C)
```

因为 elementary journey 每个任务至多访问一次，且总访问数不超过 `n`。
因此若完整穷尽 `R(C)` 后不存在 `rc < -epsilon` 的 journey，则 `E` 中也
不存在这样的 journey。这是合法的 exact no-negative 证明，不要求
`C` 最终等于全部任务。

## 4. 反例驱动细化

每次 DSSR iteration：

1. 在当前 `R(C)` 中搜索第一个 `rc < -epsilon` 的完整 journey；
2. 若该 journey elementary，立即返回真实 negative column；
3. 若它重复任务，把所有重复任务加入 `C`，释放本 iteration 的全部 label
   内存后重跑；
4. 若 `R(C)` 穷尽且无 negative，返回 exact no-negative；
5. 若 timeout、memory limit、crash 或任何 binding/audit 失败，返回 legal
   incomplete，不产生 certificate。

每次非 elementary witness 至少把一个新任务加入 `C`，所以最多细化 `n`
次。全部任务 critical 时，`R(C) = E`。

## 5. 多-sortie、branch 与 cut 不变量

### 多-sortie

- critical memory 跨 depot/recharge 保留，不能在新 sortie 清空；
- `task_visit_count` 统计总访问次数，用于 `<= n` 的有限性约束；
- `visited_count` 只统计不同任务，用于诊断和 elementary 检查；
- no-task-wait 的 retroactive depot-departure shift 语义保持不变；
- active-sortie dominance 继续禁用。

### Dominance key

depot 状态的 DSSR key 为：

```text
visited & (critical_task_mask | branch_task_mask)
```

并继续要求：

- 相同 packed cut state；
- 不晚的 global time；
- 不多的 total task visits；
- 不差的其他资源与 reduced cost。

branch task 即使尚未 critical，也必须保留 presence bit，避免合并
same/different Ryan–Foster 语义不同的状态。

### Cuts

现有 packed overlap cut state 保持 exact。重复访问 cut member 达到
`max_overlap` 后可判 infeasible；这只可能排除非 elementary journey，
不会排除 `E` 中任何 journey，因此不破坏 `E ⊆ R(C)`。

### 禁用的加速

- DSSR 中禁止现有 positive-dual completion bound。重复任务会重复获得
  dual reward，原 bound 的“每个剩余正 dual 至多一次”前提不再成立。
- 首版 DSSR 禁止 subset dominance，避免两个独立松弛叠加后难以审计。
- 不允许 memory-pressure label trimming。达到硬门槛仍是 incomplete，
  不能伪装成 time limit 或 certificate。

## 6. Certificate 与 telemetry

必须记录：

```text
dssr_enabled
dssr_policy_version
dssr_iteration_count
dssr_refinement_count
dssr_initial_critical_task_count
dssr_final_critical_task_count
dssr_repeated_witness_count
dssr_elementary_witness_returned
dssr_relaxation_no_negative_certificate
dssr_total_processed_labels
dssr_total_extended_labels
dssr_iteration_trace
```

只有下面两条路径可产生有数学含义的结果：

- elementary witness 经 Python 重建、manual true-RC、branch/cut audit 后，
  作为 partial negative column；
- 最后一次 relaxation `search_exhaustive=true`、`frontier_empty=true`、
  `labels_dropped=false` 且所有 binding 一致时，作为
  `DSSR_RELAXATION_LOWER_BOUND` no-negative certificate。

若 native 首个 elementary witness 在 Python manual true-RC 重建后恰落在
`-negative_eps` 边界、因而没有任何公开负列，则必须在同一 exact 请求中
fail-closed 回退 elementary frontier exhaustion。该回退按审计事件触发，
不按规模触发，并记录 `dssr_boundary_audit_fallback_used`；不得放宽 RC
阈值或把被拒 witness 当作负列。

任何 incomplete iteration 的 frontier 都不跨调用恢复，也不产生
certificate。

## 7. 验证门槛

### 单元与性质测试

- 空 critical set 可产生重复 witness；
- 把 witness 中重复任务加入 critical 后，该重复被禁止；
- 全 critical 与原 elementary pricer 的最优 RC/no-negative 一致；
- scale5 小实例枚举验证 `E ⊆ R(C)` 与 relaxed no-negative implication；
- active branch/cut context differential；
- timeout/memory 路径无 certificate；
- completion/subset 在 DSSR 中确实被强制关闭；
- old backend payload 未启用 DSSR，P0 行为不变。

### 逐规模差分

1. scale5 全量 exact differential；
2. scale10 全量 exact differential；
3. scale20/30 固定实例，比较 objective、RC、certificate、time、RSS；
4. 只有前述全部通过后，scale50 单实例、单进程、3600 秒、受监控运行；
5. scale50 安全完成后，再以相同规则运行 scale100 单实例，不并行。

scale50/100 成功标准不是必须闭合 BPC，而是首先满足：

- 不由 host watchdog kill；
- 无 label drop、无 certificate leak；
- 在相同安全内存预算下，比 P0 到达更多 RMP/B&B progress；
- 最终是 exact closure、合法 elementary negative progress，或完整
  frontier 下的 3600 秒 time limit。

如果最松 DSSR iteration 仍先达到内存门槛，则下一阶段必须开发
external-memory frontier 或 project-specific bidirectional join；不得通过
丢 label、扩大 swap 或取消 host 保护宣称解决。
