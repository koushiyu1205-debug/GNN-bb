# B4.1 V4 Slot-Task Time Pruning Probe

## 当前权威 3600s 对照结论

同一个 30-scale instance001 mature root-tail source probe 上，当前代码仍可接受的最强正式证书路线为：

```text
profile = V4SZ
phase_mode = proof_only
tree_closure_time_limit_sec = 3600
threads = 1
```

落盘结果来自：

```text
runs/b4_1_v4sz_current_code_30_001_3600s_compare550_20260710/
```

结果是正式 `BPC_TREE_OPTIMAL` / `EXHAUSTIVE_NO_NEGATIVE`，但没有比旧 550 秒基准更快：

| run | certificate | row wall_s | final judge wall_s | active columns | vars | rows |
|---|---|---:|---:|---:|---:|---:|
| old 550s baseline | `BPC_TREE_OPTIMAL` | 549.355622 | 549.355622 | 371 | n/a | n/a |
| current-code V4SZ rerun | `BPC_TREE_OPTIMAL` | 581.578981 | 580.558614 | 371 | 6005 | 14725 |

对比旧基准：

```text
delta = +32.223359s
relative_change = +5.866% wall time
```

也就是说，这次 3600 秒正式重跑闭合了 30-scale instance001，但比旧 550 秒基准慢约 32 秒。报告后文的 333s、193s、45s 等是历史探针或后来被 exactness/兼容性边界降级的实验记录；当前性能承诺以本节和 `runs/b4_1_v4sz_current_code_30_001_3600s_compare550_20260710/b4_1_rows.csv` 为准。

## 2026-07-10 追加：Full `(k,m)` Partition Exact Diagnostic

为了避免继续手工调单个 `quad` 或单个 `(k,m)`，本轮对同一个 30-scale instance001 mature root-tail source probe 跑了完整自动分区：

```text
k = 1..30
m = 1..k
variant = V4_current_pair_conflict_capacity_bound
per-region time limit = 30s
threads = 1
```

输出：

```text
runs/b4_1_full_km_partition_30_001_30s_regions_20260710/
```

结果：

| metric | value |
|---|---:|
| partition rows | 465 |
| complete/certified regions | 465 / 465 |
| negative regions | 0 |
| partition gate pass | true |
| full-space partition valid | true |
| best partition LB | -0.000000721 |
| gap to zero | 0.000000721 |
| summed region wall_s | 572.532591 |
| max single region wall_s | 18.263553 |
| mean / median region wall_s | 1.231253 / 0.414167 |

状态分布：

| status | count |
|---|---:|
| `COMPACT_HIGHS_PRICING_OPTIMAL` | 39 |
| `COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE` | 279 |
| `COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE` | 94 |
| `COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE` | 53 |

和旧 `549.355622s` 基准相比：

```text
delta = +23.176969s
relative_change = +4.219%
```

解释：

- 这个完整 `(k,m)` partition 在数学上给出了一个完整 no-negative candidate：所有互斥区域都 `optimal/infeasible`，没有负列，gate issue 为空。
- 但当前 runner/report 仍标记为 `diagnostic-only`，因为还没有把 partition ledger 正式接入 final judge 的 `BPC_TREE_OPTIMAL` 证书路径。
- 即使未来接入 final judge，当前单线程完整分区也没有比旧 550 秒路线更快，约慢 23 秒。
- 这个结果证明“自动完整区域分解”比手工调局部 `(k,m)` 更正确、更可泛化，但还不是性能突破。下一步若继续走这条线，应优先做 region ordering、跳过已由容量 preflight 覆盖的 m-range、以及可证明安全的多 region 并行/ledger merge，而不是继续加特例 cut。

## 2026-07-10 追加：V4SZPC Pair-Conflict Capacity Region Gate

本轮新增一个 opt-in profile：

```text
profile = V4SZPC
base = V4SZ
extra = task_slot_pair_conflict_capacity_bound
env = LUNAR_ICE_COMPACT_TASK_SLOT_PAIR_CONFLICT_CAPACITY_BOUND
```

含义：

```text
在 required_task_count + required_active_sortie_count 的 scoped region proof 中，
先解一个只含 slot-task assignment 和同 slot pair/hyperedge conflict 的小 MILP。
如果该小 MILP 的最大可装任务数 < required_task_count，
则该 scoped region 在构建主 compact pricing MILP 前直接证明 infeasible。
```

证书边界：

- 这只证明 scoped region，不证明 full-space no-negative。
- `V4SZ` 默认行为不变；`V4SZPC` 是显式 opt-in。
- full-space optimization proof 没有固定 `(k,m)`，因此这个 gate 不会直接加速当前 581 秒的 unrestricted final judge。
- restricted/partition rows 仍是 diagnostic candidate，不能单独升级 `BPC_TREE_OPTIMAL`。

### 单元测试

新增并通过：

```text
test_highs_compact_pair_conflict_capacity_bound_can_fail_scoped_region_before_main_milp
test_b4_1_v4szpc_final_judge_enables_pair_conflict_capacity_bound
```

完整 smoke：

```text
PYTHONPATH=src python -m unittest tests.test_lunar_ice_smoke.LunarIceSmokeTests
Ran 228 tests in 42.654s
OK
```

### 30-scale instance001 full-space 60s 探针

同一个 mature root-tail source probe，`V4SZPC / proof_only / 60s`：

| status | certificate | wall_s | final judge_s | dual bound | vars | rows | pair-cap requested | pair-cap enabled |
|---|---|---:|---:|---:|---:|---:|---|---|
| `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | 56.782499 | 55.778695 | -0.259805495 | 6005 | 14725 | true | false |

解释：full-space proof 没有 `required_task_count / required_active_sortie_count`，所以 pair-conflict capacity gate 被请求但不会启用。这个结果确认它不是 unrestricted final judge 的直接加速器。

输出：

- `runs/b4_1_v4szpc_pair_conflict_capacity_bound_60s_probe_30_001_20260710_goal_cont/`

### 30-scale region proof sweep

对同一 source probe 跑 residual `(k,m)` diagnostic：

```text
k = 2..12
m = 1..3
variant = V4_current_pair_conflict_capacity_bound
per-region time limit = 1s
```

汇总：

| metric | value |
|---|---:|
| rows | 32 |
| optimal rows | 7 |
| time-limit rows | 19 |
| pre-MILP infeasible rows | 6 |
| pair-cap enabled rows | 26 |
| pair-cap-caused infeasible rows | 0 |

实测 pair conflict capacity upper bound：

```text
m=1 -> upper_bound=6
m=2 -> upper_bound=12
m=3 -> upper_bound=18
```

这些 upper bound 基本没有比现有 slot/sequence capacity 更紧，因此本实例上没有触发新的 pair-capacity 早退。保留该能力作为 exact-safe region diagnostic 工具，但不推荐作为当前 30-scale 主线加速方向。

对照 `V4_current_dual_task_slot_lb_gate` 同一 sweep：

```text
lb-certified rows = 3
certified: (k=2,m=1), (k=2,m=2), (k=3,m=3)
hard tail remains: k>=6, m=2/3 lower bound still negative or timeout
```

当前结论：

- pair-conflict capacity gate 是正确的 scoped-region preflight 工具，但对 30-001 proof-tail 不是突破点。
- dual-task-slot LB 也只解决少数小 region，拖尾仍集中在较大 `k`、多 sortie 的 residual region。
- 下一步应转向更强的 route/resource-aware lower-bound ledger 或 full-space compact proof 分解，而不是继续调 pair-conflict capacity。

## 结论

- 不建议把 `subset-row cut` 直接加到 B4V4 上作为当前主线 live cut。
- 当前 30-scale instance001 的关键瓶颈是 compact final judge / true-dual no-negative proof，不是分支树规模；已闭合样例的 tree node count 为 1。
- 更直接的优化是削减 B4V4 compact pricing MILP 本身的搜索空间；本轮进一步加入 resource-arc pruning，但还没有形成 30-scale 快速闭合。

## 本次改动

在 B4V4 compact single-journey pricing profile 中启用 `slot_task_time_pruning`：

```text
如果 slot * min_active_sortie_duration + shortest(depot, task)
    > task_latest_service_start
则该 task 不可能在该 slot 被服务。

如果 earliest(slot, source) + service(source) + travel(source, target)
    > target_latest_service_start
则该 task-task arc 不可能在该 slot 被使用。
```

这个判断只用时间下界，不依赖 heuristic 或学习模型；被删除的是可证明不可行的 slot-task placement、slot-specific task-task arc 及其相关变量。

同时新增 B4V4 proof 阶段的 `JourneyColumn` MIP start：

```text
source = current column_pool best JourneyColumn under true RMP dual
usage = HiGHS solver hint only
certificate = unchanged; no lower bound or no-negative proof comes from warm start
```

V2 默认 profile 不启用该 warm start；V4 profile 启用。若 active cut context 非空、payload 不是 `JourneyColumn`、branch context 不允许、slot/arc 变量不存在，或者 restricted no-good 已排除该列，则 fail-safe 不传起点。

## 30-scale instance001 短探针

探针只给极小求解时限，目的是比较建模规模，不是重新做长时间闭合。

| variant | vars | rows | feasible slot-task | pruned slot-task | wall_s |
|---|---:|---:|---:|---:|---:|
| B4V4 before pruning | 24109 | 57086 | 630 | 0 | 0.811576 |
| B4V4 with pruning | 6660 | 15712 | 275 | 355 | 0.200650 |

变量减少 `17449`，约束减少 `41374`，其中 slot-task 剪掉 `355/630`，slot-specific arc option 剪掉 `19`。这比当前 cut 线的 subset-row diagnostic 更贴近 final judge proof-tail 瓶颈。

## 30-scale instance001 warm-start 探针

同一实例、同一 V4 slot-pruned compact model，使用单任务 feasible journey 作为 solver hint：

| variant | vars | rows | mip start | start entries | wall_s | status |
|---|---:|---:|---|---:|---:|---|
| B4V4 with pruning, cold | 6660 | 15712 | DISABLED | 0 | 0.479372 | TIME_LIMIT |
| B4V4 with pruning, warm | 6660 | 15712 | OK | 89 | 0.407867 | TIME_LIMIT |

这个探针只说明：warm start 能被当前 sparse V4 model 接受，并且不会改变模型规模。由于时限极短且目标不是闭合，不把 wall time 差异解释成正式性能收益。

## Resource-Arc Pruning 增量

根据用户对“逐个 quad 手调不能泛化”的反馈，本轮改为加入实例无关、精确安全的 resource-arc pruning：

```text
对于任意 directed arc option (source, target, path_type)，
若 depot-prefix 下界 + 该 arc 的 energy/shadow + service 资源下界 + depot-return 下界
已经必然超过 sortie energy/shadow/demand 限制，
则该 arc 不可能出现在任何可行 sortie 中，可以从 compact pricing MILP 删除。
```

这个剪枝不依赖 30 instance001 的手工参数，也不使用学习模型；被删除的是全局不可行弧，因此不会改变 exact pricing space。

### 单次 compact pricing 对比

使用 30-scale instance001 保存的 true RMP dual，V4 slot-task-time-pruned compact model，3 秒上限：

| variant | vars | rows | resource-pruned arcs | best RC | dual bound | wall_s | status |
|---|---:|---:|---:|---:|---:|---:|---|
| V4 resource pruning off | 6660 | 15712 | 0 | None | None | 3.306060 | TIME_LIMIT |
| V4 resource pruning on | 6009 | 14237 | 653 | 0.101660333 | -0.261058237 | 3.243124 | TIME_LIMIT |

变量减少 `651`，约束减少 `1475`，剪掉的 `653` 条 arc 全部来自 energy 下界不可行。这个结果说明模型规模继续下降，但短时仍没有 no-negative certificate。

### 180 秒 tree-closure 探针

使用同一 30-scale instance001 root-tail probe，V4 profile + resource-arc pruning，tree closure 上限 180 秒：

| status | tree optimal | cert scope | final judge wall_s | vars | rows | best RC | dual bound | resource-pruned arcs |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| BPC_INCOMPLETE_PRICING | 0 | DIAGNOSTIC_PRICING_FRONTIER | 167.503849 | 6009 | 14237 | 0.005868608 | -0.140920227 | 653 |

结论很明确：resource-arc pruning 是正确的泛化型模型缩减，但还不是足够强的 30-scale 闭合突破。它没有在 180 秒内把之前接近 600 秒的 30-scale 证明缩短到闭合；当前仍卡在 compact proof lower bound 为负，不能输出 `BPC_TREE_OPTIMAL`。

因此后续不应继续靠 `(k,m)` 或 quad 手调，而应转向更激进但仍 exact-safe 的 formulation 级方法：

- 更强的 resource-aware dominance / state compression，只删除有证明的 dominated labels。
- 以 complete partition 为目标的 region proof，而不是 prefix/no-good 近似 region。
- 将 exact compact pricing 改成分层 branch-and-bound/branch-and-cut 子问题，保留全局 lower-bound ledger。
- 用 route-template/GAT/worker 只做 column discovery；所有 bound 和 no-negative certificate 仍必须回到 true-dual exact proof。

### 3600 秒正式比较：同 550 秒基准口径

为了和旧的 `549.355622s` 闭合结果公平比较，本次使用同一个 source probe：

```text
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_epsilon_band_merge_official_eps_600s/stage_002/probe.json
```

配置：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4
LUNAR_ICE_COMPACT_RESOURCE_ARC_PRUNING=1
tree_closure_time_limit_sec = 3600
tree_closure_max_rounds = 1
tree_closure_max_nodes = 31
```

结果：

| run | status | tree optimal | cert scope | wall_s | final judge wall_s | active columns | vars | rows | resource-pruned arcs |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| old baseline | BPC_OPTIMAL | 1 | BPC_TREE_OPTIMAL | 549.355622 | 549.355622 | 371 | n/a | n/a | 0 |
| current V4 + resource pruning | BPC_OPTIMAL | 1 | BPC_TREE_OPTIMAL | 333.310751 | 332.274797 | 371 | 6009 | 14237 | 653 |

当前模型仍给出正式 `BPC_TREE_OPTIMAL`，不是 diagnostic closure。相比旧基准：

```text
time_saved = 216.044871s
relative_speedup = 39.326961% less wall time
speedup_factor = 1.648179x
```

final judge 内部的 compact optimization proof 为 `OPTIMAL`，`pricing_proof_kind=EXHAUSTIVE_NO_NEGATIVE`，best reduced cost 为 `-0.0`，dual bound 为 `-4.03e-07`，在当前 eps 下通过 no-negative proof。

注意边界：这个比较是同一个 root-tail source probe 上的 tree-closure 证明耗时，不包含从零生成 371 个 active columns 的历史累计时间。

## Region Proof Ledger 进展

`restricted-region bound ledger` 现在额外记录：

```text
supported_bound_region_count
unsupported_bound_region_count
nonnegative_bound_region_count
negative_bound_region_count
region_bound_gap_to_zero
region_bound_gap_source_region_id
region_bound_gap_source
```

这些字段用于判断 targeted restricted/no-good region 还差多少才能接近 no-negative proof。边界保持不变：restricted region 不是完整 pricing space partition，因此即使已列出的 region bound 全部非负，也只能标记为 diagnostic，不允许升级 `BPC_TREE_OPTIMAL` 或 `CERTIFIED_NO_NEGATIVE`。

同时 compact pricing 新增 `required_task_set` exact subregion pricing 原语：

```text
required_task_set = S
search space = all feasible journey route variants whose task set is exactly S
certificate role = can certify this exact task-set region only
full-space role = cannot certify full pricing space by itself
```

这使后续可以把 prefix no-good proof 拆成：

```text
1. 每个被 no-good 排除的 exact task-set region 各自证明 nonnegative；
2. 最深 prefix residual region 证明 nonnegative；
3. 只有在这些 regions 构成完整且不重叠的 partition 时，才有资格讨论 official no-negative certificate。
```

当前实现只完成第 1 类 region 的 solver 原语和 partition audit 字段，还没有自动跑全套 partition proof。

随后新增了 `required-task-set partition proof probe` runner：

```text
for each harvested unique task set H_i:
    solve required_task_set = H_i

solve residual:
    forbid all H_i exact task sets
```

如果每个 exact task-set region 和 residual region 都证明 nonnegative，runner 会给出 `partition_candidate_can_certify_no_negative=True`。但该结果仍然是 diagnostic candidate：`official_certificate_allowed=False`，`can_claim_certificate=False`。后续需要把这个 partition proof 接入 final judge / certificate ledger 后，才可以讨论 official no-negative certificate。

### Required-Region Pre-MILP Infeasibility Guard

为了减少 region proof 中无意义的 compact MILP 构建，当前 solver 对 exact required-task-set、required-task-count、required-active-sortie-count region 增加了 pre-MILP 早退：

```text
如果 required_task_count > feasible task count
或 required_task_count > sum(slot capacity)
或 required_task_count > safe slot-sequence capacity upper bound
或 required_task_count > safe slot-task matching capacity upper bound
或 required_task_count 需要的最少 active sortie 数超过可用 slot
或固定 required_active_sortie_count 小于该 task-count / task-set 的安全 slot-prefix capacity minimum
或 required_active_sortie_count 超出该 region 的可行 active-sortie 范围，
则该 region 在构建 slot-specific arc variables 之前直接证明 infeasible。
```

这个 guard 只在 region proof 路径使用，不改变 unrestricted final judge 的 full-space pricing。输出仍是 region-scoped：

```text
pricing_complete_for_required_task_count = true
required_task_count_region_can_certify_no_negative = true
can_certify_no_negative = false
variable_count = 0
constraint_count = 0
```

含义是“这个 required region 无负列”，不是 full-space no-negative certificate。这样 exact task-set partition rows 以及 residual task-count partition 中明显不可能的 `S`、`k` 或 `(k,m)` region 不再浪费时间建完整 compact arc 模型。

本轮把已有的 slot-sequence / slot-task matching upper bound 前移到 compact arc construction 之前执行；当这些安全上界已经小于 required task count 时，直接返回 `variable_count=0`、`constraint_count=0` 的 region infeasible proof。若 `slot_arc_support_pruning` 打开，后续仍会在 support pruning 后重新计算最终 capacity telemetry；accepted V4 默认仍关闭 support pruning。

此外新增 `required_active_sortie_count_capacity_min`：在尚未把 slot 截断到固定 active-sortie 数之前，先按有序 slot prefix 累加安全 sequence capacity，得到覆盖该 required task-count / task-set 至少需要的 active sortie 数。如果当前 region 强制的 `required_active_sortie_count` 小于该值，则记录：

```text
required_active_sortie_count_infeasible_by_capacity_min = true
required_active_sortie_count_capacity_min = <safe lower bound>
variable_count = 0
constraint_count = 0
```

这个判断仍然只证明该 `(k,m)` 或 `(task_set,m)` region infeasible，不是 full-space no-negative certificate。

新增 task-set telemetry：

```text
required_task_set_infeasible_by_feasible_task_count
required_task_set_infeasible_by_slot_capacity
required_task_set_infeasible_by_slot_sequence_capacity
required_task_set_infeasible_by_slot_matching
```

新增 active-sortie telemetry：

```text
required_active_sortie_count_capacity_min
required_active_sortie_count_infeasible_by_capacity_min
```

### Single-Task-Per-Active-Sortie Arc Pruning

对 residual `(k,m)` region 还有一个安全的模型缩减：

```text
如果 required task count / required task set size == required_active_sortie_count，
则每个 active sortie 必须且只能服务 1 个 task。
```

原因是 compact pricing 已经要求：

```text
sum(task visits) = k
sum(active sorties) = m
每个 active sortie 至少服务 1 个 task
```

当 `k=m` 时，任何 active sortie 都不可能服务第二个 task，因此 task-to-task arc variables 在该 region 中全是死变量。当前 solver 会在 candidate arc construction 阶段直接跳过这些 task→task path options，只保留 depot→task 和 task→depot。

同理，既然每个 sortie 只有一个 task，MTZ visit-order variables、endpoint-order cuts 和 pair time-window precedence order cuts 也不会再约束任何真实的多 task route。当前 solver 在该 region 中会局部关闭 MTZ 顺序层；原始 `mtz_connectivity` 配置仍保留在输入语义里，但实际建模使用：

```text
mtz_connectivity_effective = false
single_task_per_active_sortie_mtz_disabled = true
```

新增 telemetry：

```text
single_task_per_active_sortie_arc_pruning_enabled
single_task_per_active_sortie_arc_pruned_option_count
single_task_per_active_sortie_mtz_disabled
mtz_connectivity_effective
partition_region_single_task_per_active_sortie_arc_pruned_option_count_sum
```

单元测试用同一 compact formulation 做 A/B：关闭该剪枝与开启该剪枝的 best reduced cost 必须一致，同时开启后 `variable_count` 和 `constraint_count` 更小。当前 5-task `(k=2,m=2)` A/B：

| variant | best RC | variables | constraints | task→task options pruned | MTZ effective |
| --- | ---: | ---: | ---: | ---: | --- |
| pruning off | `0.322422` | 131 | 290 | 0 | true |
| pruning on | `0.322422` | 81 | 138 | 40 | false |

## Slot-Arc Support Pruning A/B

本轮尝试了更激进的 `slot_arc_support_pruning`：先在经过 time/resource pruning 的 slot arc graph 上做 depot reachability / return reachability，只保留从 depot 可达且能回 depot 的 task-slot，再建 compact pricing 变量。

小规模单元测试中该剪枝没有改变 compact pricing optimum，但 30-scale 同源 root-tail probe 暴露了证书风险：

| variant | status | cert | wall | final judge | added columns | best negative RC | support-pruned task-slots |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| V4 resource/time pruning, support off | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | `332.986s` | `331.958s` | 0 | none | 0 |
| V4 resource/time pruning, support on | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | `116.775s` | `115.718s` | 2 | `-0.001665` | 73 |

结论：`support on` 的 116 秒不是加速闭合，而是提前找到负列并降级；它不能和 333 秒的正式 `BPC_TREE_OPTIMAL` 比较为“更快”。由于 support pruning 理论上是删列，不应在同一源上产生旧 unrestricted proof 未发现的负列，所以当前按潜在 formulation bug / compatibility risk 处理。

因此 accepted V4 默认保持：

```text
resource_arc_pruning = true
slot_task_time_pruning = true
slot_arc_support_pruning = false
```

`slot_arc_support_pruning` 只保留为 low-level diagnostic/experimental switch，不能进入 official B4V4 certificate path。后续若继续推进，必须先证明它和 unrestricted compact pricing 的 feasible-column space 完全一致，或者把它降级为 candidate-search-only 且禁止 no-negative certificate。

## Dual Task-Slot Full-Space LB 门控

本轮还测试了 `dual_task_slot_full_space_lower_bound`：先用安全的 task-count / active-sortie-count region assignment relaxation lower bound 扫描完整 pricing space。如果所有 region 的 lower bound 都非负，就可以在不建完整 compact MILP 的情况下给出 no-negative certificate。

这个机制在 5-scale 小实例上可以直接证明 no-negative，但在当前 30-scale instance001 上不构成加速：

| run | status | cert | wall_s | final judge wall_s | full-space LB status | LB value | scanned regions | negative LB regions |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| accepted V4 | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | `332.986234` | `331.958380` | off | n/a | 0 | 0 |
| V4 + full-space LB | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | `337.727327` | `336.709393` | `BOUND_SCAN_INCOMPLETE_OR_NEGATIVE` | `-1.328629449` | 360 | 349 |

结论：full-space LB 是 exact-safe 的证明捷径候选，但当前 30-scale root dual 下 region lower bound 大量为负，不能提前闭合，反而增加约 `4.74s` wall time。因此它不能升为 accepted V4 默认开关。

为避免以后 opt-in 时再次白扫完整 region 矩阵，当前实现已改成证明门控模式：

```text
dual_task_slot_full_space_lb_early_stop_on_negative = true
```

一旦某个 region lower bound < -eps，full-space LB 已经不可能证明 no-negative，扫描立即停止并回退完整 compact proof。新增 telemetry：

```text
dual_task_slot_full_space_lower_bound_early_stop_on_negative
dual_task_slot_full_space_lower_bound_early_stopped_on_negative
dual_task_slot_full_space_lower_bound_status
dual_task_slot_full_space_lower_bound_region_count
dual_task_slot_full_space_lower_bound_negative_region_count
```

安全边界不变：早停只说明“这个 lower-bound 捷径不能证明”，不能 claim certificate；正式 `BPC_TREE_OPTIMAL` 仍必须来自 unrestricted exact compact pricing / final judge。

## Certificate Boundary

- official objective 仍是 `normalized_cost + normalized_risk + 0.4 * normalized_weighted_completion`。
- `makespan` 仍只作为 metric。
- V2 默认 profile 不启用该剪枝，保持 accepted baseline 边界。
- V4 accepted profile 启用 resource arc pruning、slot-task time pruning 和 column-pool MIP start；`slot_arc_support_pruning` 默认关闭。
- certificate 仍必须来自 unrestricted exact compact pricing / negative-feasibility proof。
- restricted/no-good harvesting 仍不能升级为 `CERTIFIED_NO_NEGATIVE`。
- MIP start 只是 primal solver hint，不能提供 official lower bound、frontier bound 或 no-negative certificate。
- Restricted-region bound ledger 是 proof-tail diagnostic；当前没有完整 partition/coverage 证明时必须保持 `FRONTIER_BOUND_INCOMPLETE`。
- `required_task_set` 可以证明单个 exact task-set region，但不能单独证明 full-space no-negative。
- `required-task-set partition proof probe` 可以形成 full-space partition candidate，但当前仍不自动 claim official certificate。
- required-region pre-MILP infeasibility guard 只证明局部 region infeasible，不能 claim full-space certificate。
- `dual_task_slot_full_space_lower_bound` 默认关闭；即使 opt-in，也只有 coverage complete 且全 region LB >= -eps 时才可 certificate，遇到 negative LB 早停时必须回退完整 proof。

## 2026-07-10 追加：Proof-Only Exact Tail

本轮比较了两个更激进但 exact-safe 的 tail 策略：

1. `negative search` 也传入 column-pool MIP start。
2. 直接跳过 `negative search`，进入 unrestricted compact optimization proof。

### Negative-Search MIP Start 结论

新增 opt-in 环境变量：

```text
LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_MIP_START=1
```

它只把 V4 profile 已经选出的 column-pool warm start 传给 negative-feasibility search。该 warm start 仍然只是 HiGHS primal hint，不参与 reduced-cost 计算、lower bound 或 certificate。

30-scale instance001 的 90 秒短探针结果：

| variant | cert scope | wall_s | final judge wall_s | negative-search wall_s | negative-search MIP start | optimization wall_s | result |
|---|---|---:|---:|---:|---|---:|---|
| accepted V4 harvest_then_proof | `BPC_TREE_OPTIMAL` | 330.132429 | 329.101299 | 54.496332 | DISABLED | 274.603393 | closed |
| V4 + negative-search MIP start, 90s cap | `DIAGNOSTIC_PRICING_FRONTIER` | 86.595027 | 85.598581 | 56.684677 | OK | 28.912539 | time-limited |

结论：negative-search MIP start 能正确传入，但没有显示加速信号；在该实例上 negative-search 反而从约 `54.5s` 增至约 `56.7s`。因此该开关保留为 diagnostic/opt-in，不升为 accepted V4 默认。

### V4 Proof-Only 结论

更有效的 aggressive exact 路线是：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4
LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE=proof_only
```

含义：

```text
跳过前置 negative-feasibility search；
直接求 unrestricted compact single-journey optimization proof；
若存在负 reduced-cost column，optimization proof 仍会返回负列；
若 optimum >= -eps，则仍可给 EXHAUSTIVE_NO_NEGATIVE。
```

因此这不是 heuristic shortcut，也不是 diagnostic closure；证书仍来自 unrestricted exact compact pricing。

同一个 30-scale instance001、同一个 source probe、3600 秒上限：

| run | profile | phase mode | status | cert scope | wall_s | final judge wall_s | phases | vars | rows |
|---|---|---|---|---|---:|---:|---|---:|---:|
| B4V2 default | B4V2 | harvest_then_proof | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 670.237780 | 669.214326 | negative + proof | 49162 | 96251 |
| V4 accepted | V4 | harvest_then_proof | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 330.132429 | 329.101299 | negative + proof | 6009 | 14237 |
| V4 proof-only | V4 | proof_only | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 274.217189 | 273.207773 | proof only | 6009 | 14237 |

相对速度：

```text
vs 550s reference:
    time_saved = 275.782811s
    speedup_factor = 2.0057x
    wall reduction = 50.14%

vs accepted V4 harvest_then_proof:
    time_saved = 55.915240s
    speedup_factor = 1.2039x
    wall reduction = 16.94%

vs B4V2 default:
    time_saved = 396.020591s
    speedup_factor = 2.4442x
    wall reduction = 59.09%
```

Proof-only 的风险边界：

- 它适合“active column pool 已成熟，主要任务是 no-negative proof”的 final tail。
- 它不适合早期 column discovery，因为会跳过便宜的 hidden-negative harvesting。
- 如果 optimization proof 找到负列，仍必须回到 RMP 加列，不能 claim no-negative。
- 目前建议把它作为 `30-scale final proof-tail mode` 的 explicit opt-in；要升为默认，还需要在 selected 30-scale 多实例上确认不会因跳过 negative search 造成总轮数增加。

### V4 Lean Proof-Only：关闭非必要 strengthening cuts

在 proof-only 基础上继续测试了两个 exact-safe 的约束缩减开关：

```text
LUNAR_ICE_COMPACT_MTZ_ENDPOINT_ORDER_CUTS=0
LUNAR_ICE_COMPACT_PAIR_ADJACENCY_CUTS=0
```

这两个约束都是 compact MILP 的 strengthening cuts，不定义 pricing space 本身。关闭它们不会增加或删除合法 journey column，只会让 MILP formulation 更松、约束更少。因此它只能靠实测决定是否值得用于 final proof tail。

同一个 30-scale instance001、同一个 source probe、3600 秒上限：

| run | phase mode | endpoint cuts | pair cuts | status | cert scope | wall_s | final judge wall_s | vars | rows |
|---|---|---:|---:|---|---|---:|---:|---:|---:|
| V4 harvest_then_proof | harvest_then_proof | 1030 | 1749 | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 330.132429 | 329.101299 | 6009 | 14237 |
| V4 proof-only | proof_only | 1030 | 1749 | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 274.217189 | 273.207773 | 6009 | 14237 |
| V4 lean proof-only | proof_only | 0 | 0 | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 228.006118 | 226.992552 | 6009 | 11458 |

相对速度：

```text
vs 550s reference:
    time_saved = 321.993882s
    speedup_factor = 2.4122x
    wall reduction = 58.54%

vs V4 proof-only:
    time_saved = 46.211071s
    speedup_factor = 1.2027x
    wall reduction = 16.85%

vs V4 harvest_then_proof:
    time_saved = 102.126311s
    speedup_factor = 1.4479x
    wall reduction = 30.93%
```

结论：

- 对当前 30-scale instance001 的 matured active pool，endpoint-order cuts 和 pair-adjacency cuts 没有帮助，反而增加 `2779` 条约束并拖慢 proof。
- 新的当前最强单实例 tail 是 `V4 + proof_only + endpoint/pair cuts off`，正式闭合时间 `228.006118s`。
- 这仍然不应直接替代所有阶段的 V4 默认：early discovery 阶段可能仍需要 strengthening cuts 或 negative search。更合理的策略是把它作为 “matured active pool final proof-tail” 模式，在 selected 30-scale 多实例上验证。

## Verification

- `PYTHONPATH=src python -m compileall -q src scripts tests`
- `git diff --check`
- `PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_resource_arc_pruning_preserves_pricing_optimum tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_v4_profile_is_explicit_opt_in tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_v2_default_and_v4_diagnostic_configs_are_explicit`
- `PYTHONPATH=src python -m unittest tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_slot_arc_support_pruning_preserves_pricing_optimum tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_v2_default_and_v4_diagnostic_configs_are_explicit tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_v4_profile_is_explicit_opt_in tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_proof_only_skips_negative_discovery tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_feasibility_proof_can_certify_full_space`
- `PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_full_space_dual_task_slot_lb_early_stop_is_not_certificate tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_v4_profile_is_explicit_opt_in tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_default_uses_v2_formulation tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_runner_report_keeps_full_experiment_gate_closed tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_stage_d_tree_closure_row_satisfies_r7_without_stage_b_leak`
- `PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_single_journey_pricing_required_task_set_region tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_single_journey_pricing_required_task_count_region`
- `PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_single_journey_pricing_required_task_count_region tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_residual_task_count_partition_probe_is_fail_closed_until_complete`
- `PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests`

结果：完整 smoke `199 tests OK`；新增/相关 targeted tests `5 tests OK`。

2026-07-10 追加验证：

- `PYTHONPATH=src python -m compileall -q src/lunar_ice_bpc/exact/bpc/pricing/final_judge.py tests/test_lunar_ice_smoke.py`
- `PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_v4_final_judge_passes_column_pool_mip_start_to_proof tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_v4_final_judge_can_pass_mip_start_to_negative_search tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_v4_profile_is_explicit_opt_in tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_default_uses_v2_formulation`
- `PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_proof_only_skips_negative_discovery tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_v4_final_judge_can_pass_mip_start_to_negative_search tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_v4_final_judge_passes_column_pool_mip_start_to_proof`
- `PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_v4_profile_is_explicit_opt_in tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_v4_final_judge_cut_strengthening_can_be_opted_out tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_proof_only_skips_negative_discovery`
- `git diff --check -- src/lunar_ice_bpc/exact/bpc/pricing/final_judge.py tests/test_lunar_ice_smoke.py`
- `PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests`

结果：完整 smoke `200 tests OK`。

2026-07-10 lean proof-tail 追加后，完整 smoke 更新为 `201 tests OK`。

2026-07-10 追加运行 artifacts：

- `runs/b4_1_v4_negative_search_mip_start_90s_probe_20260710/`
- `runs/b4_1_v4_proof_only_30_001_3600s_probe_20260710/`
- `runs/b4_1_v4_proof_only_no_endpoint_pair_30_001_3600s_probe_20260710/`

## 2026-07-10 追加：Fixed Journey-Active Redundant Row Pruning

本轮继续做一个很小但 exact-safe 的 compact MILP 缩减：

```text
single-journey pricing 中 journey_active 的上下界固定为 [1, 1]；
z_slot 自身已有 ub = 1；
因此 z_slot <= journey_active 等价于 z_slot <= 1，是冗余行。
```

修改后这类行在所有 single-journey pricing region 中都跳过，不再只在 fixed active-sortie region 里跳过。

30-scale instance001，同一个 saved true-dual root-tail probe，V4 lean proof-only 配置下直接调用 compact pricing 原语，0.5 秒建模/求解探针：

| variant | vars | rows | skipped fixed-active rows | resource-pruned arcs | slot-task feasible | slot-task pruned |
|---|---:|---:|---:|---:|---:|---:|
| V4 lean proof-only before this pruning | 6009 | 11458 | 0 | 653 | 275 | 355 |
| V4 lean proof-only after this pruning | 6009 | 11437 | 21 | 653 | 275 | 355 |

收益很小：只减少 `21` 条约束，对应当前 30-scale proof model 的 `21` 个 sortie slots。但这个缩减不依赖实例调参，也不改变可行 journey space、reduced cost、dual bound 或 certificate 语义。

45 秒 tree-closure 轻量 probe：

| status | cert scope | pricing state | wall_s | final judge wall_s | skipped rows | certificate leak | manual RC fail | pricing RC fail |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | `INCOMPLETE_LIMIT` | 38.107372 | 37.081467 | 21 | 0 | 0 | 0 |

这个 45 秒 probe 只验证 fail-closed 和模型缩减 telemetry；没有声称闭合。正式闭合口径仍以前面的 3600 秒 V4 lean proof-only run 为准。

新增 artifacts：

- `runs/b4_1_v4_lean_fixed_active_skip_45s_probe_20260710/`

## 2026-07-10 追加：No-MTZ Proof Diagnostic

进一步测试了一个更激进的 formulation 缩减：在 V4 lean proof-only 中关闭 proof 阶段的 MTZ connectivity：

```text
LUNAR_ICE_COMPACT_PROOF_MTZ_CONNECTIVITY=0
```

结构依据是：compact pricing 已对每条 task-task arc 加入 service-start 时间传播约束。由于 travel/service 为正，任何 disconnected task cycle 都会导致一圈时间严格递增而不可行。因此 MTZ 在可行域上可能是冗余的；但它仍可能显著强化 MIP proof bound。

5-scale 多 seed exhaustive 对照：

| seed | expected RC | MTZ RC | no-MTZ RC | MTZ vars/rows | no-MTZ vars/rows |
|---:|---:|---:|---:|---:|---:|
| 629001 | 0.067630 | 0.067630 | 0.067630 | 326 / 714 | 301 / 434 |
| 679123 | 0.138429 | 0.138429 | 0.138429 | 346 / 754 | 321 / 454 |
| 701337 | 0.035364 | 0.035364 | 0.035364 | 351 / 764 | 326 / 459 |
| 809911 | 0.072372 | 0.072372 | 0.072372 | 351 / 764 | 326 / 459 |
| 929001 | 0.070524 | 0.070524 | 0.070524 | 356 / 774 | 331 / 464 |

30-scale instance001，同一个 saved true-dual root-tail probe，V4 lean proof-only compact 原语 0.5 秒建模/求解探针：

| variant | vars | rows | mtz effective | dual bound at 0.5s |
|---|---:|---:|---:|---:|
| V4 lean proof-only with MTZ | 6009 | 11437 | true | -1.483772294 |
| V4 lean proof-only no-MTZ | 5734 | 6818 | false | -0.322708881 |

no-MTZ 的模型规模明显更小：

```text
variables saved = 275
rows saved = 4619
```

但正式 tree-closure 对照显示它不是当前最强路线。同一 source probe、600 秒上限：

| variant | status | cert scope | wall_s | final judge wall_s | proof kind | compact dual bound | certificate leak |
|---|---|---|---:|---:|---|---:|---:|
| V4 lean proof-only with MTZ | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 228.006118 | 226.992552 | `EXHAUSTIVE_NO_NEGATIVE` | -4.03e-07 | 0 |
| V4 lean proof-only no-MTZ | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | 346.516118 | 345.496135 | `FRONTIER_BOUND_INCOMPLETE` | -0.001664642 | 0 |

结论：

- no-MTZ 在小规模上和 exhaustive reduced cost 一致，说明它有潜力作为 exact-safe diagnostic formulation。
- 但在 30-scale final no-negative proof 上，MTZ 对 bound tightening 有实际价值；关闭 MTZ 虽减少约束，却没有更快闭合。
- 因此 no-MTZ 不进入当前 accepted final-tail candidate。当前最强仍是 `V4 + proof_only + endpoint/pair cuts off + MTZ on + resource/slot pruning on`。
- `LUNAR_ICE_COMPACT_PROOF_MTZ_CONNECTIVITY=0` 保留为显式 diagnostic 开关，不能默认启用。

新增 artifacts：

- `runs/b4_1_v4_no_mtz_lean_proof_only_30_001_600s_probe_20260710/`

## 2026-07-10 追加：Pair-Weighted Strengthened Final Tail

no-MTZ 证明“少约束但 bound 变松”不是主线后，本轮转向 exact-safe strengthening：用少量/中量合法下界和 infeasible-pair rows 换更强 no-negative proof bound。

测试的核心组合：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4
LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE=proof_only
LUNAR_ICE_COMPACT_MTZ_ENDPOINT_ORDER_CUTS=0
LUNAR_ICE_COMPACT_PAIR_ADJACENCY_CUTS=0
LUNAR_ICE_COMPACT_PROOF_MTZ_CONNECTIVITY=1
LUNAR_ICE_COMPACT_SORTIE_SLOT_POSITION_BOUNDS=1
LUNAR_ICE_COMPACT_PAIR_WEIGHTED_COMPLETION_LB=1
LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT=1
LUNAR_ICE_COMPACT_PAIR_TIME_WINDOW_INFEASIBLE_CUT=1
LUNAR_ICE_COMPACT_PAIR_SHADOW_INFEASIBLE_CUT=1
```

这些 rows 都是 compact pricing 内部的 strengthening，不改变 pricing space：

- `sortie_slot_position_bounds`：按 sortie slot 位置给 start/end 变量加安全下界/上界。
- `pair_weighted_completion_lb`：若两个任务同时在同一 sortie 中，给两者 weighted service-start 组合加安全下界。
- `pair_*_infeasible_cut`：若任务对因 energy/time-window/shadow 下界必然不可同 sortie，则加 `y_i + y_j <= 1`。

### 30-scale saved-dual 短时矩阵

同一个 30-scale instance001 saved true-dual root-tail probe，V4 lean proof-only 基础配置，20 秒 compact proof：

| variant | vars | rows | dual_bound | status | wall_s |
|---|---:|---:|---:|---|---:|
| baseline | 6009 | 11437 | -0.229283120 | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` | 20.262443 |
| sortie_position | 6009 | 11499 | -0.223042328 | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` | 16.619013 |
| pair_infeasible_cuts | 6009 | 12259 | -0.232690823 | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` | 17.657487 |
| pair_weighted_completion_lb | 6009 | 13859 | -0.219995417 | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` | 20.197290 |
| sortie + pair_weighted | 6009 | 13921 | -0.227465477 | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` | 17.465444 |
| sortie + pair_weighted + pair infeasible | 6009 | 14743 | -0.215175684 | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` | 20.233389 |

20 秒矩阵说明：组合 row 数更多，但 dual bound 抬得最高，值得做正式 tree-closure probe。

### 300 秒 tree-closure 对照

同一个 source probe、同一个 30-scale instance001：

| variant | status | cert scope | wall_s | final judge wall_s | proof kind | compact dual bound | cert leak |
|---|---|---|---:|---:|---|---:|---:|
| previous strongest V4 lean proof-only | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 228.006118 | 226.992552 | `EXHAUSTIVE_NO_NEGATIVE` | -4.03e-07 | 0 |
| pair-weighted strengthened final tail | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 193.760231 | 192.729891 | `EXHAUSTIVE_NO_NEGATIVE` | -7.21e-07 | 0 |

相对上一版最强配置：

```text
time_saved = 34.245887s
speedup_factor = 1.1767x
wall reduction = 15.02%
```

相对最早约 550 秒口径：

```text
time_saved = 356.239769s
speedup_factor = 2.8386x
wall reduction = 64.77%
```

结论：

- 这是目前 30-scale instance001 上新的最强 final proof-tail：`193.760231s` 正式 `BPC_TREE_OPTIMAL`。
- 它不是 heuristic，也不是 diagnostic certificate；closure 仍来自 unrestricted compact proof 的 `EXHAUSTIVE_NO_NEGATIVE`。
- 但它目前只在 instance001 上验证，不能直接升为全 30-scale accepted default。下一步需要 selected 30-scale 多实例对照，确认额外 rows 不会在其他实例上拖慢 proof。

新增 artifacts：

- `runs/b4_1_v4_strengthening_matrix_30_001_2s_20260710/`
- `runs/b4_1_v4_strengthening_matrix_30_001_20s_20260710/`
- `runs/b4_1_v4_strengthening_combo_30_001_20s_20260710/`
- `runs/b4_1_v4_pair_weighted_infeasible_strengthened_30_001_300s_probe_20260710/`

## 2026-07-10 追加：V4S Profile 固化与 selected30 early-pool 诊断

为了避免靠一串手工环境变量复现实验，当前代码新增显式 profile：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4S
LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE=proof_only
```

`V4S` 等价于上一节 193 秒配置：

```text
name = V4S
formulation_profile = B4V4_strengthened_pair_weighted_final_tail
MTZ proof = on
endpoint-order cuts = off
pair-adjacency cuts = off
resource_arc_pruning = on
slot_task_time_pruning = on
sortie_slot_position_bounds = on
pair_weighted_completion_lb = on
pair_energy_infeasible_cut = on
pair_time_window_infeasible_cut = on
pair_shadow_infeasible_cut = on
```

边界：

- `B4V2` 仍是 official default。
- `V4` 仍是原 combined diagnostic profile。
- `V4S` 是 explicit opt-in final-tail candidate，不自动成为全局默认。

### selected30 early-pool 诊断

随后对 `runs/b4_1_true_dual_proof_tail_stage_c_selected30_input_probes/instance_001..005` 做了 5 个 30-scale selected probes 的 `V4S + proof_only` tree-gate 诊断，每 row 60 秒上限。

结果：

| selected instance | active columns | columns added by tree gate | status | cert scope | wall_s | fail reason |
|---|---:|---:|---|---|---:|---|
| 030_001 | 37 | 26 | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | 0.270499 | tree not closed |
| 030_002 | 39 | 25 | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | 0.277278 | tree not closed |
| 030_003 | 36 | 11 | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | 0.258845 | tree not closed |
| 030_004 | 40 | 20 | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | 0.268938 | tree not closed |
| 030_005 | 39 | 18 | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | 0.261225 | tree not closed |

这些 rows 的意义不是“V4S 慢/快”，而是说明 selected30 input probes 仍是 early-pool 状态：

```text
active columns only 36-40
tree gate immediately finds/needs additional root columns
compact final no-negative proof tail is not reached
```

因此这 5 个 probes 不能证明 `V4S` 的 mature-pool 泛化性。要做真正的多实例泛化验证，需要先把 selected 30-scale instances 推进到 mature active pool，再比较：

```text
V4 lean proof-only
vs
V4S strengthened proof-only
```

安全性结果：

- selected30 early-pool 5 rows 都 fail-closed。
- certificate leak = 0。
- manual RC fail = 0。
- pricing RC fail = 0。
- diagnostic claimed certificate = 0。

新增 artifacts：

- `runs/b4_1_v4s_selected30_early_pool_60s_probe_20260710/`

## 2026-07-10 追加：V4S Profile-Level 成熟池验证

为确认 `V4S` profile 本身已经正确固化，而不是依赖上一节临时手写环境变量，本轮重新用 profile 入口跑同一个 mature 30-scale instance001 root-tail probe：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4S
LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE=proof_only
```

输入仍为：

```text
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_epsilon_band_merge_official_eps_600s/stage_002/probe.json
```

结果：

| run | status | cert scope | wall_s | final judge wall_s | profile | formulation | proof kind | compact dual bound |
|---|---|---|---:|---:|---|---|---|---:|
| V4S profile mature probe | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 194.773356 | 193.759239 | `V4S` | `B4V4_strengthened_pair_weighted_final_tail` | `EXHAUSTIVE_NO_NEGATIVE` | -7.21e-07 |

profile telemetry：

```text
sortie_slot_position_bound_count = 62
pair_weighted_completion_lb_count = 2422
pair_energy_infeasible_cut_count = 333
pair_time_window_infeasible_cut_count = 489
pair_shadow_infeasible_cut_count = 0
certificate_leak = 0
manual_rc_fail = 0
pricing_rc_fail = 0
diagnostic_claimed_certificate = 0
```

与上一节手写 env strengthened run 对比：

```text
manual-env V4S-equivalent wall_s = 193.760231
profile V4S wall_s = 194.773356
difference = 1.013125s
```

结论：

- `V4S` profile 已能独立复现 30-scale instance001 mature-pool 正式闭合。
- 当前 30-001 mature-pool 最强配置可以用 `V4S + proof_only` 直接调用。
- 泛化边界仍不变：需要更多 mature 30-scale active pools 才能把 `V4S` 升为全局 accepted default。

新增 artifacts：

- `runs/b4_1_v4s_profile_mature_30_001_300s_probe_20260710/`

## 2026-07-10 追加：V4S 3600s 限额正式重跑

按“当前最强模型”重跑 30-scale instance001，限额设为 3600s：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4S
LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE=proof_only
tree_closure_time_limit_sec = 3600
threads = 1
```

输入仍为 mature root-tail probe：

```text
runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_epsilon_band_merge_official_eps_600s/stage_002/probe.json
```

结果：

| run | status | cert scope | wall_s | final judge wall_s | profile | formulation | proof kind | variable/constraint |
|---|---|---|---:|---:|---|---|---|---|
| V4S 3600s rerun | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | 193.814224 | 192.806687 | `V4S` | `B4V4_strengthened_pair_weighted_final_tail` | `EXHAUSTIVE_NO_NEGATIVE` | 6009 / 14743 |

相对 550s 参考：

```text
saved = 356.185776s
speedup = 2.837769x
time reduction = 64.761050%
```

证书安全字段：

```text
certificate_leak = 0
manual_rc_fail = 0
pricing_rc_fail = 0
diagnostic_claimed_certificate = 0
compact_pricing_dual_bound = -7.21e-07
```

新增 artifacts：

- `runs/b4_1_v4s_current_strongest_30_001_3600s_rerun_20260710/`

## 2026-07-10 追加：Recharge-Aware Slot Bound 候选

实现了一个 exact-safe 的 active-sortie slot 上界收紧候选：

```text
min_duration_lower_bound =
    min_outbound_travel
  + min_return_travel
  + min_service_time
  + dock_overhead
  + min_sortie_energy / recharge_power
```

这个下界是安全的，因为任何非空 sortie 至少包含一次 depot->task、一次 task->depot、一个 task service，并且 compact 模型本身约束：

```text
sortie_end >= sortie_return + dock + energy_expr / recharge_power
```

30-scale instance001 的 slot bound 变化：

| config | slots | vars | constraints | wall_s | final judge wall_s | cert |
|---|---:|---:|---:|---:|---:|---|
| `V4S` default | 21 | 6009 | 14743 | 194.870807 | 193.848504 | `BPC_TREE_OPTIMAL` |
| recharge-aware slot bound | 18 | 5027 | 12328 | 236.795751 | 235.790846 | `BPC_TREE_OPTIMAL` |

模型规模收益：

```text
variables:   6009 -> 5027  (-982, -16.34%)
constraints: 14743 -> 12328 (-2415, -16.38%)
```

但 wall time 在该实例上变慢：

```text
194.870807s -> 236.795751s
```

结论：

- 该 bound 是证书安全的，适合保留为大实例/内存压力场景的 opt-in compact profile。
- 该 bound 不应替换当前最快 `V4S` 默认线。
- 当前代码中默认 `V4S` 保持 recharge-aware slot bound 关闭；新增 opt-in profile `V4SR` / `V4S_RECHARGE_SLOT` 用于显式开启。

新增 artifacts：

- `runs/b4_1_v4s_default_after_recharge_optin_30_001_3600s_probe_20260710/`
- `runs/b4_1_v4s_recharge_slot_bound_30_001_3600s_probe_20260710/`

## 2026-07-10 追加：V4SH Seed-Harvest Profile

将之前散落在 env probe 里的 route-template pre-harvest 固化为显式 opt-in profile：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4SH
```

`V4SH` 的数学边界：

- compact proof 仍继承当前最快的 `V4S` formulation。
- 在 compact MILP 前先做 active-pool seed-first route-template pre-harvest。
- pre-harvest 找到的列必须通过 true-dual manual RC / pricing RC / addability audit。
- pre-harvest no-column 不能 claim no-negative；若 fallback 开启，仍进入 compact proof。

默认 profile 参数：

```text
route_template_pre_harvest_enabled = true
route_template_pre_harvest_target = 1
route_template_pre_harvest_time_cap_sec = 15
route_template_pre_harvest_max_direct_tasks = 8
route_template_pre_harvest_max_active_seeds = 120
route_template_pre_harvest_max_neighborhood_seeds = 120
route_template_pre_harvest_max_candidate_sets = 180
route_template_pre_harvest_fallback_enabled = true
```

30-scale instance001 / plus57 round3 active-pool 60s smoke：

| run | wall_s | final judge wall_s | status | selected | best true RC | proof kind |
|---|---:|---:|---|---:|---:|---|
| `V4SH` profile seed-harvest | 25.435062 | 2.080235 | `ROUTE_TEMPLATE_PRE_HARVEST_FOUND_NEGATIVE` | 1 | -0.001331226 | `FRONTIER_BOUND_INCOMPLETE` |

关键 telemetry：

```text
candidate_round_count = 24
candidate_round_limit = 180
candidate_negative_count = 1
certificate_leak = 0
manual_rc_fail = 0
pricing_rc_fail = 0
```

结论：

- `V4SH` 适合作为未知 30-scale 的 aggressive negative-discovery profile，比手调 `(k,m)`/quad/triple 更自动化。
- 它不能替代 `V4S` 的 final no-negative certificate；当 pre-harvest 找不到 addable negative 后，仍需要 compact proof 或完整 region ledger。
- 当前最快已闭合 30-001 的正式证书线仍是 `V4S + proof_only`，`193.814224s`。

新增 artifacts：

- `runs/b4_1_v4sh_profile_seed_harvest_30_001_60s_probe_20260710/`

## 2026-07-10 追加：Objective-Bound / Feasibility Proof 负结果

实现了一个 opt-in cutoff profile：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4SC
```

`V4SC` 继承 `V4S`，只额外设置：

```text
objective_bound_no_negative_cutoff = true
objective_bound = -negative_eps
```

理论目标是让 HiGHS 只证明“不存在 reduced cost <= -eps 的列”，而不是把最优 reduced cost 证明到完整 gap 0。

30-scale instance001 / mature active-pool 对照：

| config | wall_s | final judge wall_s | status | proof kind | nodes | simplex iters | conclusion |
|---|---:|---:|---|---|---:|---:|---|
| `V4S + proof_only` | 193.814224 | 192.806687 | `COMPACT_HIGHS_PRICING_OPTIMAL` | `EXHAUSTIVE_NO_NEGATIVE` | 7909 | 478302 | 当前最快证书线 |
| `V4SC + proof_only` | 262.537275 | 261.530019 | `COMPACT_HIGHS_PRICING_OPTIMAL` | `EXHAUSTIVE_NO_NEGATIVE` | 12945 | 654169 | 更慢，不默认 |

关键观察：

```text
objective_bound_no_negative_cutoff_enabled = true
objective_bound_no_negative_cutoff_value = -1e-06
objective_bound_no_negative_cutoff_can_certify = false
```

也就是说，HiGHS 在该模型上没有以 objective-bound cutoff infeasible 的方式提前停止，最后仍然跑到 full optimal proof；节点数和 simplex iteration 都更高。

同时测试了已有的：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE=feasibility_proof_only
```

该模式会显式加入 `reduced_cost <= -eps` 并做 zero-objective feasibility proof。30-scale instance001 跑到超过 300s 仍未闭合，已经慢于 `V4S + proof_only` 的 193.8s，因此手动中止，不作为默认路线。

结论：

- `V4SC` 是 exact-safe 的 opt-in 证书候选，但在当前 30-001 上慢于 `V4S`。
- objective-bound cutoff 和 feasibility-proof-only 都不能替代当前 `V4S + proof_only`。
- 当前 proof-side 主线仍应回到 formulation/region ledger，而不是期待 solver cutoff 自动缩短 final proof。

新增 artifacts：

- `runs/b4_1_v4sc_objective_bound_cutoff_30_001_3600s_probe_20260710/`

## 2026-07-10 追加：Zero-Capacity Slot Truncation 小收益

> **历史记录，已被后续 exactness fix 降级。** 本节的 `V4SZ ~= 193.617s`
> 来自修复 `conditional sequence` 之前的 fast row。后续发现 inactive dummy slot
> 在 tightened time bound 下被无条件 sequence row 过紧约束，相关快速闭合不能再作为
> current-code accepted certificate 性能承诺。当前代码的可信对照见后文
> “当前代码 V4SZ 3600s 对 550s 基准重跑”：`581.578981s`。

实现了一个 opt-in profile：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4SZ
```

`V4SZ` 继承 `V4S`，只额外启用：

```text
zero_capacity_slot_truncation = true
```

逻辑边界：

- 单个 journey pricing 的 active sortie slot 是前缀连续的。
- 如果第 `k` 个 slot 的 safe sequence capacity 已经是 `0`，则该 slot 的 `z_k` 会被 visit lower-bound 行强制为 0。
- 因为 `z` 前缀连续，后续所有 slot 也不可能 active。
- 因此可以在建 compact MILP 前截掉这个 zero-capacity suffix；这不改变可行域，也不改变 reduced-cost 证明边界。

30-scale instance001 / mature active-pool 对照：

| config | wall_s | final judge wall_s | slots | variables | constraints | proof kind | conclusion |
|---|---:|---:|---:|---:|---:|---|---|
| `V4S + proof_only` | 193.814224 | 192.806687 | 21 | 6009 | 14743 | `EXHAUSTIVE_NO_NEGATIVE` | historical pre-fix row |
| `V4SZ + proof_only` | 193.617246 | 192.596087 | 20 | 6005 | 14725 | `EXHAUSTIVE_NO_NEGATIVE` | historical pre-fix row; no longer current promise |

关键 telemetry：

```text
zero_capacity_slot_truncation_enabled = true
zero_capacity_slot_truncation_original_slot_count = 21
zero_capacity_slot_truncation_effective_slot_count = 20
zero_capacity_slot_truncation_trimmed_slot_count = 1
zero_capacity_slot_truncation_first_zero_slot = 20
algorithm_status = BPC_OPTIMAL
certificate_scope = BPC_TREE_OPTIMAL
manual_rc_fail = 0
pricing_rc_fail = 0
certificate_leak = 0
```

解释：

- 这是一个真正 exact-safe 的模型缩减，但这次只删掉 1 个空 slot，因此变量只减少 `4`，约束减少 `18`。
- wall time 从 `193.814224s` 到 `193.617246s`，只快约 `0.197s`，约 `0.10%`。
- 它可以保留为默认候选/opt-in 小优化，但不能作为 30-scale proof-tail 的主突破。
- 下一步仍应继续做更大粒度的 formulation/region proof：当前主耗时仍在 middle-size full-space no-negative proof，而不是最后一个空 slot。

新增 artifacts：

- `runs/b4_1_v4sz_zero_capacity_slot_truncation_30_001_3600s_probe_20260710/`

## 2026-07-10 追加：Slot Sequence Capacity Live Bound 负结果

实现了一个 opt-in profile：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4SL
```

`V4SL` 继承 `V4S`，并启用：

```text
zero_capacity_slot_truncation = true
slot_sequence_capacity_live_bound = true
```

预期目标是把已有 safe slot sequence capacity 从诊断/预检值变成 live MILP 上界：

```text
sum_task y[slot, task] <= slot_sequence_capacity[slot] * z[slot]
```

这不改变 pricing 可行域，因为 `slot_sequence_capacity[slot]` 是由 time-window/horizon/service/recharge 下界推出的安全上界。

30-scale instance001 / mature active-pool 对照：

| config | wall_s | final judge wall_s | slots | variables | constraints | tightened slots | proof kind | conclusion |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `V4S + proof_only` | 193.814224 | 192.806687 | 21 | 6009 | 14743 | n/a | `EXHAUSTIVE_NO_NEGATIVE` | accepted strongest baseline |
| `V4SZ + proof_only` | 193.617246 | 192.596087 | 20 | 6005 | 14725 | n/a | `EXHAUSTIVE_NO_NEGATIVE` | small positive |
| `V4SL + proof_only` | 194.656214 | 193.654205 | 20 | 6005 | 14725 | 0 | `EXHAUSTIVE_NO_NEGATIVE` | slower |

关键 telemetry：

```text
slot_sequence_capacity_live_bound_enabled = true
slot_sequence_capacity_live_bound_by_slot =
  [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,5,3,1]
slot_sequence_capacity_live_bound_tightened_slot_count = 0
zero_capacity_slot_truncation_trimmed_slot_count = 1
algorithm_status = BPC_OPTIMAL
certificate_scope = BPC_TREE_OPTIMAL
manual_rc_fail = 0
pricing_rc_fail = 0
certificate_leak = 0
```

解释：

- `V4SL` 是 exact-safe，但在该成熟 30-001 proof 模型中没有实际收紧 slot。
- 原因是 zero-capacity suffix 截掉后，剩余 slot 的 feasible task assignment 数已经不超过 sequence capacity；live 上界没有比现有变量域更强。
- wall time 比 `V4SZ` 慢约 `1.039s`，比 `V4S` 慢约 `0.842s`。
- 结论：保留为 diagnostic/opt-in，不作为默认；当前突破方向应转向更强的 route/time/resource bound 或完整 region ledger，而不是 slot task-count capacity。

新增 artifacts：

- `runs/b4_1_v4sl_slot_sequence_live_bound_30_001_3600s_probe_20260710/`

## 2026-07-10 追加：Tight Service-Start Bounds 负结果

实现了一个 opt-in profile：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4ST
```

`V4ST` 继承 `V4S`，并启用：

```text
zero_capacity_slot_truncation = true
tight_service_start_bounds = true
```

逻辑边界：

- 原模型已经有 `service_start[task] <= (due_time - service_time) * y[task]`。
- `tight_service_start_bounds` 只是把对应 continuous variable 的 upper bound 从全局 `horizon` 收紧到该 task 的 latest service start。
- 这不改变可行域、不改变 reduced-cost 目标、不改变 certificate 语义；它只把已有时间窗限制提前到变量 domain。

30-scale instance001 / mature active-pool 对照：

| config | wall_s | final judge wall_s | slots | variables | constraints | tightened service-start vars | proof kind | conclusion |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `V4S + proof_only` | 193.814224 | 192.806687 | 21 | 6009 | 14743 | n/a | `EXHAUSTIVE_NO_NEGATIVE` | accepted strongest baseline |
| `V4SZ + proof_only` | 193.617246 | 192.596087 | 20 | 6005 | 14725 | n/a | `EXHAUSTIVE_NO_NEGATIVE` | small positive |
| `V4ST + proof_only` | 197.981292 | 196.973858 | 20 | 6005 | 14725 | 275 | `EXHAUSTIVE_NO_NEGATIVE` | slower |

关键 telemetry：

```text
tight_service_start_bounds_enabled = true
tight_service_start_bound_count = 275
tight_service_start_bound_min = 65.876593
tight_service_start_bound_max = 974.526396
zero_capacity_slot_truncation_enabled = true
zero_capacity_slot_truncation_effective_slot_count = 20
zero_capacity_slot_truncation_trimmed_slot_count = 1
algorithm_status = BPC_OPTIMAL
certificate_scope = BPC_TREE_OPTIMAL
manual_rc_fail = 0
pricing_rc_fail = 0
certificate_leak = 0
```

解释：

- `V4ST` 是 exact-safe，也能正式闭合 `BPC_TREE_OPTIMAL`。
- 但在 30-001 上 wall time 比 `V4S` 慢约 `4.167s`，比 `V4SZ` 慢约 `4.364s`。
- 说明单纯收紧 service-start UB 没有改善当前 HiGHS proof-tail；可能增加了 presolve/branch 处理负担，收益不足。
- 结论：保留为 diagnostic/opt-in，不作为默认。当前最强默认仍应是 `V4S`，或保守采用小幅正收益的 `V4SZ`；真正突破仍需要更大粒度的 route/time/resource pruning 或 region proof。

新增 artifacts：

- `runs/b4_1_v4st_tight_service_start_30_001_60s_probe_20260710/`
- `runs/b4_1_v4st_tight_service_start_30_001_3600s_probe_20260710/`

## 2026-07-10 追加：Slot-Arc Support Pruning 激进缩模诊断

测试了一个更激进但仍 exact-safe 的 opt-in 组合：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4SZ
LUNAR_ICE_COMPACT_SLOT_ARC_SUPPORT_PRUNING=true
LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE=proof_only
```

逻辑边界：

- 先按 slot-time pruning 和 resource-arc pruning 得到候选 arc。
- 对每个 slot 构造支持图；若某 task 在该 slot 不可从 depot 到达，或到达后无法返回 depot，则该 task-slot assignment 不可能出现在合法 sortie 中。
- 删除这些 unsupported task-slot assignment 及相关 arc option；这是 reachability/support pruning，不是 heuristic column filtering。

60 秒 sanity probe：

| config | wall_s | final judge wall_s | variables | constraints | supported assignments | pruned assignments | pruned arc options | rc lb / bound | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `V4SZ + proof_only` | 193.617246 | 192.596087 | 6005 | 14725 | 275 | n/a | n/a | `-7.21e-07` | `BPC_TREE_OPTIMAL` |
| `V4SZ + slot_arc_support + proof_only` 60s | 56.692901 | 55.685169 | 4382 | 10178 | 202 | 73 | 1400 | `-0.18662959` | `NOT_SOLVED` |

关键 telemetry：

```text
slot_arc_support_pruning_enabled = true
slot_arc_support_feasible_assignment_count = 202
slot_arc_support_pruned_assignment_count = 73
slot_arc_support_pruned_no_return_count = 73
slot_arc_support_pruned_option_count = 1400
slot_task_time_feasible_assignment_count = 275
slot_task_model_assignment_count = 202
zero_capacity_slot_truncation_trimmed_slot_count = 2
variable_count = 4382
constraint_count = 10178
global_remaining_rc_lb = -0.18662959
certificate_scope = DIAGNOSTIC_PRICING_FRONTIER
```

解释：

- 这个方向确实大幅减少变量/约束：变量比 `V4SZ` 少 `1623`，约束少 `4547`。
- 但 60 秒 proof bound 明显更弱；随后启动过 3600 秒正式对照，在超过当前 `V4SZ` 193.617s 基线后仍未闭合，因此手动终止，避免继续占用资源。
- 结论：`slot_arc_support_pruning` 是强缩模但不是当前 30-001 加速方向。它可能适合负列发现或某些局部 region proof，但不能作为默认 full-space final judge proof profile。
- 下一步更应转向能提升 no-negative proof bound 的 formulation/region certificate，而不是只减少模型大小。

新增 artifacts：

- `runs/b4_1_v4sz_slot_arc_support_30_001_60s_probe_20260710/`
- `runs/b4_1_v4sz_slot_arc_support_30_001_3600s_probe_20260710/`（超过 baseline 后人工终止，无完整 row）

## 2026-07-10 追加：Dual Task-Slot Route-Decomposition Lower Bound

本轮没有继续调单个 quad，而是加强 `dual_task_slot_lower_bound` / `dual_task_slot_full_space_lower_bound` 的通用 proof bound。新增内容全部只作用在 lower-bound/region proof MIP 中，不改变 official objective，不增加正式 compact pricing 主模型变量，也不能在 coverage 不完整时 claim certificate。

新增 exact-safe 下界：

- `route_arc_lb` 连续变量：用 slot 内最小入弧、最小出弧、旧常数弧下界共同约束路线弧成本。
- `pair_completion_lift`：同一 slot 内被选 pair 的加权完成时间 lift，只取最大 lift，避免多 pair 重复累计。
- `single_task_route_arc_bound`：当 `task_count == active_sortie_count` 时，每个 sortie 恰好一个任务，路线弧成本至少为 `depot-task-depot` 单任务下界之和。
- `pair_route_arc_bound`：当 `task_count == 2` 时，同一 sortie 的二任务路线必须是 `depot-task-task-depot`，加入精确 pair route arc 下界。
- `triple_route_arc_bound`：当 `task_count == 3, active_sortie_count == 1` 时，加入三任务单 sortie 的 permutation route arc 下界。
- `one_pair_rest_single_route_arc`：当 `task_count == active_sortie_count + 1` 时，加入“一个双任务 sortie + 其余单任务 sortie”的聚合 route decomposition 下界。
- `cross_slot_completion_lift`：若早 slot 选任务 i、晚 slot 选任务 j，则 j 的开始时间不能早于 i 的最早服务、服务时间、返回 depot、dock 之后再出发的下界。

30-001 的 60 秒 full-space lower-bound progression：

| variant | first negative region | full-space LB | scanned regions | lb wall_s | final status |
|---|---:|---:|---:|---:|---|
| route-arc only | `(2,1)` | `-0.026561812` | 2 | 0.011376 | `DIAGNOSTIC_PRICING_FRONTIER` |
| + pair route arc | `(2,2)` | `-0.067270433` | 3 | 0.205975 | `DIAGNOSTIC_PRICING_FRONTIER` |
| + single route arc | `(3,1)` | `-0.084696714` | 4 | 0.206282 | `DIAGNOSTIC_PRICING_FRONTIER` |
| + triple route arc | `(3,2)` | `-0.134702202` | 5 | 0.555874 | `DIAGNOSTIC_PRICING_FRONTIER` |
| current route-decomposition | `(3,2)` | `-0.023270454` | 5 | 0.581352 | `DIAGNOSTIC_PRICING_FRONTIER` |

Scoped region checks on the same 30-001 true dual:

```text
(2,1):  LB = 0.054593315, exact compact RC = 0.054656
(2,2):  LB = 0.094132860
(3,1):  LB = 0.021999665
(3,2):  LB = -0.023270454, exact compact RC = 0.058952
```

解释：

- 这个方向有效：full-space lower-bound 的首个失败 region 已从 `(2,1)` 推进到 `(3,2)`。
- `(2,1)`、`(2,2)`、`(3,1)` 已能通过 scoped route-decomposition lower bound 闭合。
- 当前仍不能 60 秒内闭合 30-001，因为 `(3,2)` region 的 assignment relaxation 仍比完整 compact pricing 松，虽然已从 `-0.134702202` 抬到 `-0.023270454`。
- 不能把当前 row 升级为 `BPC_TREE_OPTIMAL`：coverage 不完整，`dual_task_slot_full_space_lower_bound_negative_region_count = 1`，仍然必须 fail-closed。

安全验证：

```text
PYTHONPATH=src python -m unittest tests.test_lunar_ice_smoke.LunarIceSmokeTests
Ran 218 tests in 42.631s
OK
```

新增 artifacts：

- `runs/b4_1_v4sz_route_decomposition_lb_fullspace_30_001_60s_probe_20260710/`

## 2026-07-10 追加：Selected-Pair Separation for `(k=m+1)` Region

针对上一节剩余的 `(task_count=3, active_sortie_count=2)` gap，新增了轻量 selected-pair separation：

- 先用 1 条聚合 route decomposition row 求解 lower-bound relaxation。
- 如果 relaxation 选中的结构是“一个双任务 sortie + 其余单任务 sortie”，只给当前被选中的双任务 pair 加 1 条 conditional route row。
- 重新求解，最多 24 轮。
- 若 per-region time limit 小于 1 秒，则不启用 separation，避免默认 full-space scan 从 negative-bound diagnostic 退化成 unsupported timeout。

scoped `(3,2)` region 在 30-001 true dual 下的改善：

| config | LB | separation rows | lb wall_s | status |
|---|---:|---:|---:|---|
| 聚合 route decomposition | `-0.023270454` | 0 | 0.033047 | `Optimal` |
| selected-pair separation x8 | `-0.010661111` | 8 | 0.267211 | `Optimal` |
| selected-pair separation x16 | `-0.005472660` | 16 | 0.797193 | `Optimal` |
| selected-pair separation x24 | `-0.001271382` | 24 | 1.655790 | `Optimal` |

解释：

- 这个 separation 是 exact-safe 的：新增 row 只在对应 pair 被同 slot 选中时收紧 route arc 下界，否则 Big-M 放松。
- 它有效但还不足以闭合 `(3,2)`：24 轮后仍为 `-0.001271382`，距离 0 只差约 `0.00127`。
- 26 轮在当前 HiGHS scoped lower-bound 上触发 time limit，拿不到有效 bound，因此默认固定为 24 轮。
- 默认 full-space 0.25 秒 per-region probe 不启用 separation，所以最新 full-space row 与上一版一致，仍 fail-closed 在 `(3,2)`：

```text
dual_task_slot_full_space_lower_bound_value = -0.023270454
dual_task_slot_full_space_lower_bound_task_count = 3
dual_task_slot_full_space_lower_bound_active_sortie_count = 2
dual_task_slot_full_space_lower_bound_status = BOUND_SCAN_NEGATIVE_REGION_EARLY_STOP
certificate_scope = DIAGNOSTIC_PRICING_FRONTIER
```

安全验证：

```text
PYTHONPATH=src python -m unittest tests.test_lunar_ice_smoke.LunarIceSmokeTests
Ran 218 tests in 41.930s
OK
```

新增 artifact：

- `runs/b4_1_v4sz_selected_pair_separation_lb_fullspace_30_001_60s_probe_20260710/`

## 2026-07-10 追加：V4SZT Tight Time-Arc Big-M Profile

本轮新增 `V4SZT` profile，目标不是继续手调单个 `(k,m)` region，而是强化 full-space compact final judge 的通用 proof formulation。

新增配置：

```text
profile = V4SZT
base = V4SZ
tight_service_start_bounds = true
tight_time_arc_big_m = true
```

`tight_time_arc_big_m` 的安全边界：

- 对所有真实 sortie，`sortie_start` 不可能晚于 `latest_service_start_upper_bound - min_depot_outbound_travel`。
- inactive dummy sortie 的 `sortie_start` 也可安全收紧到这个上界，因为 dummy start 不代表任何真实路径。
- 因此 depot->task 时间弧的 Big-M 可从 `horizon + travel` 收紧为 `sortie_start_upper_bound + travel`，不删除任何 feasible column。

30-001 结果：

| profile | proof kind | exact status | final judge wall_s | row wall_s | shell wall_s | vars | rows | max M reduction |
|---|---|---|---:|---:|---:|---:|---:|---:|
| V4SZ | optimization proof | `BPC_TREE_OPTIMAL` | `248.405697` | `249.425242` | `274.69` | `6005` | `14725` | n/a |
| V4SZT | negative-feasibility proof | `BPC_TREE_OPTIMAL` | `45.008167` | `46.025814` | `49.82` | `6005` | `14726` | `718.659507` |

证书状态：

```text
algorithm_status = BPC_OPTIMAL
exact_status = BPC_TREE_OPTIMAL
certificate_scope = BPC_TREE_OPTIMAL
pricing_state = CERTIFIED_NO_NEGATIVE
pricing_proof_kind = EXHAUSTIVE_NO_NEGATIVE
manual_rc_fail = 0
pricing_rc_fail = 0
certificate_leak = 0
```

关键解释：

- V4SZT 没有靠 diagnostic frontier 升级；它在 compact negative-feasibility model 中证明 `reduced_cost <= -eps` 不可行，因此是 official no-negative proof。
- 变量数没有下降，因为本轮强化主要是 bound/Big-M tightening；约束多 1 条来自 negative-feasibility reduced-cost cutoff。
- 速度提升主要来自 proof formulation 变强：tight Big-M 让 negative-feasibility 反证在约 45 秒闭合，避免走约 250 秒的 optimization proof tail。
- 这个方法是实例无关的，适合作为下一轮 30-scale selected instances 的候选默认 proof-tail profile。

安全验证：

```text
PYTHONPATH=src python -m unittest \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_single_journey_tight_time_arc_big_m_preserves_rc \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_v4szt_profile_enables_tight_big_m \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_proof_only_skips_negative_discovery \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_feasibility_proof_can_certify_full_space

Ran 4 tests in 0.180s
OK
```

新增 artifact：

- `runs/b4_1_v4szt_tight_time_big_m_30_001_3600s_probe_20260710_051444/`

## 2026-07-10 追加：Pair-to-Later Lift Safety Fix

完整 smoke 发现原先 pair-to-later completion separation 有一个安全问题：

```text
test_highs_compact_dual_task_slot_one_pair_rest_single_route_lb_is_safe
lower_bound = 0.918392087
exact_best_rc = 0.908163
```

原因：

- `pair_completion_lift_col` 已经计入同一 slot 内 pair 的内部 start-time lift。
- pair-to-later separation 又把 pair 内部两个任务的 weighted start lift 和 later task delay 一起放进 `cross_slot_lift_col`。
- 两个 lift 变量同时进目标，导致 pair 内部 lift 被双计，lower bound 可能越过 exact RC。

修复：

- pair-to-later separation 现在只约束 later task 的额外 delay。
- pair 内部 start lift 仍只由 `pair_completion_lift_col` 负责。
- 修复后 `(task_count=3, active_sortie_count=2)` scoped lower bound 在 30-001 true dual 下保持：

```text
dual_task_slot_lower_bound_value = -0.000662188
dual_task_slot_lower_bound_cross_slot_pair_completion_separation_row_count = 3
dual_task_slot_lower_bound_one_pair_rest_single_route_arc_separation_row_count = 24
```

安全验证：

```text
PYTHONPATH=src python -m unittest tests.test_lunar_ice_smoke.LunarIceSmokeTests

Ran 220 tests in 42.747s
OK
```

## 2026-07-10 追加：Selected-30 5-Instance Probe Caveat

尝试用 `V4SZT` 对 `stage_c_selected30_input_probes/instance_001..005` 做 5-instance tree-closure 检查，但这组 source probes 不是成熟 root-tail active pool：

```text
active_column_count ~= 35-40
root_added_column_count = 11..26
root_last_pricing_state = FOUND_NEGATIVE
exact_status = NOT_SOLVED
certificate_scope = DIAGNOSTIC_PRICING_FRONTIER
mean wall ~= 0.27s
```

解释：

- 这不是 V4SZT no-negative proof 的失败；它还没进入 proof-tail。
- 这些 rows 说明 selected 5 的输入池太早期，一轮 tree closure 只是在补负列。
- 要做有效泛化验证，需要先把每个 selected instance 的 active pool 推到 root-tail，再用 V4SZT final judge 证明 no-negative。

新增 artifact：

- `runs/b4_1_v4szt_selected30_5x_600s_probe_20260710_052106/`

## 2026-07-10 追加：V4SZTP Proof-Only Tail Profile

成熟 30-scale root-tail 上，`V4SZT` 默认 `harvest_then_proof` 会先尝试 negative-feasibility no-negative proof；该路线已能把 30-001 从约 550 秒压到约 46 秒。进一步对照发现，同一个 mature active pool 上直接走 optimization proof 更快，因此新增显式 profile：

```text
profile = V4SZTP
base = V4SZT
phase_mode_default = proof_only
compact_pricing_phase = optimization_proof
```

这个 profile 只改变 final judge 的 phase 选择，不改变 official objective、pricing space、branch/cut context 或 reduced-cost 公式。它适合“active column pool 已经成熟、只剩 no-negative proof-tail”的场景；早期还在持续发现负列的 selected probes 仍不应直接跳过 harvesting。

30-001 同一 source probe 对照：

| profile | phase | proof kind | exact status | final judge wall_s | row wall_s | shell wall_s | vars | rows |
|---|---|---|---|---:|---:|---:|---:|---:|
| old baseline | optimization proof | `EXHAUSTIVE_NO_NEGATIVE` | `BPC_TREE_OPTIMAL` | `549.355622` | `549.355622` | n/a | n/a | n/a |
| V4SZ | optimization proof | `EXHAUSTIVE_NO_NEGATIVE` | `BPC_TREE_OPTIMAL` | `248.405697` | `249.425242` | `274.69` | `6005` | `14725` |
| V4SZT | negative-feasibility proof | `EXHAUSTIVE_NO_NEGATIVE` | `BPC_TREE_OPTIMAL` | `45.008167` | `46.025814` | `49.82` | `6005` | `14726` |
| V4SZTP | optimization proof | `EXHAUSTIVE_NO_NEGATIVE` | `BPC_TREE_OPTIMAL` | `32.241618` | `33.259111` | `37.01` | `6005` | `14725` |

`V4SZTP` 证书状态：

```text
algorithm_status = BPC_OPTIMAL
exact_status = BPC_TREE_OPTIMAL
certificate_scope = BPC_TREE_OPTIMAL
pricing_state = CERTIFIED_NO_NEGATIVE
pricing_proof_kind = EXHAUSTIVE_NO_NEGATIVE
best_reduced_cost = 0.013004
dual_bound = 0.013003658
manual_rc_fail = 0
pricing_rc_fail = 0
certificate_leak = 0
```

相对旧 550 秒口径：

```text
time_saved ~= 516.10s
relative_speedup ~= 16.5x by row wall
```

相对 V4SZT：

```text
time_saved ~= 12.77s
relative_speedup ~= 1.38x by row wall
```

同时测试了两个通用强化候选，但暂不接受为默认：

| candidate | exact status | row wall_s | vars | rows | conclusion |
|---|---|---:|---:|---:|---|
| V4SZT + slot-service-start y lower bound | `BPC_TREE_OPTIMAL` | `47.940300` | `6005` | `14726` | safe, opt-in only; slower than V4SZT |
| V4SZT + slot-arc-support pruning | `BPC_TREE_OPTIMAL` | `50.305529` | `4382` | `10179` | model smaller, but proof slower on 30-001 |

边界：

- `slot_service_start_y_lower_bound` 已实现为 opt-in，默认不进入 `V4SZT/V4SZTP`。
- `slot_arc_support_pruning` 仍保留为 opt-in；虽然变量/约束明显减少，但当前 30-001 proof-tail wall time 变慢，不能只凭模型更小就接受。
- 当前 strongest mature-tail profile 是 `V4SZTP`，不是 selected-early-pool 的默认 column-discovery profile。

新增验证：

```text
PYTHONPATH=src python -m unittest \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_slot_service_start_y_lb_preserves_rc \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_v4szt_profile_enables_tight_big_m \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_v4sztp_profile_defaults_to_proof_only

Ran 3 tests in 0.168s
OK

PYTHONPATH=src python -m unittest tests.test_lunar_ice_smoke.LunarIceSmokeTests

Ran 222 tests in 42.119s
OK
```

新增 artifacts：

- `runs/b4_1_v4sztp_profile_30_001_3600s_probe_20260710_goal_cont/`
- `runs/b4_1_v4szt_proof_only_30_001_3600s_probe_20260710_goal_cont/`
- `runs/b4_1_v4szt_slot_service_start_lb_30_001_3600s_probe_20260710_goal_cont/`
- `runs/b4_1_v4szt_slot_arc_support_30_001_3600s_probe_20260710_goal_cont/`

## 2026-07-10 追加：Conditional Sequence Exactness Fix

复查 `V4SZTP` 的 tree JSON 时发现一个重要问题：

```text
single_journey_mip_start_status = ERROR
```

根因不是 warm start 本身，而是 compact model 的时间序列约束：

```text
sortie_start[q] >= sortie_end[q-1]
```

这条约束原来对所有 slot 无条件生效。引入 `tight_time_arc_big_m` 后，`sortie_start` 上界被收紧到：

```text
latest_service_start_upper_bound - min_depot_outbound_travel
```

这对真实 active sortie start 是安全的，但对 inactive dummy slot 不应强制继承前一个 active sortie 的 end time。否则如果某个真实 journey 的最后一个 active sortie 结束较晚，后续 inactive dummy slot 会被迫：

```text
inactive_start >= previous_active_end
```

再叠加 tightened start upper bound，模型可能排除本来可行的真实 journey。也就是说，之前 `V4SZT=46s` 和 `V4SZTP=33s` 的快速闭合来自一个过紧 compact model，不能继续作为 accepted full-space certificate 证据。

修复：

```text
sortie_start[q] >= sortie_end[q-1] - horizon * (1 - z[q])
```

只有当前 slot active 时才强制顺序衔接；inactive dummy slot 不再约束真实路径时间。同时 warm start 对 inactive tail 不再填 previous_end/return/end，避免给 HiGHS 传入违反 inactive rows 的 hint。

修复后 30-001 mature source probe 的 60 秒诊断：

| profile | phase | status | cert scope | row wall_s | vars | rows | dual bound | mip start |
|---|---|---|---|---:|---:|---:|---:|---|
| pre-fix V4SZTP | optimization proof | `BPC_TREE_OPTIMAL` | `BPC_TREE_OPTIMAL` | `33.259111` | `6005` | `14725` | `0.013003658` | `ERROR` |
| corrected V4SZTP | optimization proof | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | `53.791904` | `6005` | `14725` | negative / incomplete | `OK` |
| corrected V4SZT | harvest_then_proof | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | `60.257666` | `6005` | `14725` | negative / incomplete | `OK` |

同时测试了一个 opt-in tightening：

```text
active_time_z_bounds:
    sortie_start <= start_bound * z
    sortie_end   <= horizon * z
```

它是 exact-safe，但 60 秒内没有改善 proof bound，并增加约束：

| candidate | status | row wall_s | vars | rows | active-time rows | conclusion |
|---|---|---:|---:|---:|---:|---|
| corrected V4SZTP default | `BPC_INCOMPLETE_PRICING` | `53.791904` | `6005` | `14725` | `0` | default |
| corrected V4SZTP + active_time_z_bounds | `BPC_INCOMPLETE_PRICING` | `53.195088` | `6005` | `14765` | `40` | opt-in only; not accepted |

当前结论：

- accepted exactness fix：conditional sequence + inactive-tail warm-start fix。
- accepted warm-start improvement：`single_journey_mip_start_status` 从 `ERROR` 变为 `OK`。
- 之前 30-001 `BPC_TREE_OPTIMAL` 快速闭合证据降级；不能再说 corrected B4.1 已闭合 30-001。
- corrected model 下，30-scale 重新卡在 true-dual compact proof bound：60 秒内 `FRONTIER_BOUND_INCOMPLETE`，无证书泄漏。
- 下一步应继续做 region / partition lower-bound ledger 或更强 exact pricing proof，而不是沿用修复前的 33 秒结论。

新增验证：

```text
PYTHONPATH=src python -m unittest \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_tight_time_big_m_accepts_inactive_tail_mip_start \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_single_journey_tight_time_arc_big_m_preserves_rc \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_compact_final_judge_v4sztp_profile_defaults_to_proof_only

Ran 3 tests in 0.165s
OK

PYTHONPATH=src python -m unittest tests.test_lunar_ice_smoke.LunarIceSmokeTests

Ran 223 tests in 41.730s
OK
```

新增 artifacts：

- `runs/b4_1_v4sztp_conditional_sequence_default_60s_diagnostic_30_001_20260710_goal_cont/`
- `runs/b4_1_v4szt_conditional_sequence_60s_diagnostic_30_001_20260710_goal_cont/`
- `runs/b4_1_v4sztp_active_time_z_bounds_60s_diagnostic_30_001_20260710_goal_cont/`

## 2026-07-10 追加：当前代码 V4SZ 3600s 对 550s 基准重跑

按同一个 30-scale instance001 mature root-tail source probe 重跑一次当前代码下仍可接受的最强 mature-tail 路线：

```text
source_probe = runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_epsilon_band_merge_official_eps_600s/stage_002/probe.json
profile = V4SZ
phase_mode = proof_only
tree_closure_time_limit_sec = 3600
threads = 1
```

结果：

| run | status | certificate | row wall_s | final judge wall_s | active columns | vars | rows | proof kind |
|---|---|---|---:|---:|---:|---:|---:|---|
| old 550s baseline | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | `549.355622` | `549.355622` | `371` | n/a | n/a | `EXHAUSTIVE_NO_NEGATIVE` |
| current-code V4SZ rerun | `BPC_OPTIMAL` | `BPC_TREE_OPTIMAL` | `581.578981` | `580.558614` | `371` | `6005` | `14725` | `EXHAUSTIVE_NO_NEGATIVE` |

证书状态：

```text
pricing_state = CERTIFIED_NO_NEGATIVE
pricing_proof_kind = EXHAUSTIVE_NO_NEGATIVE
global_remaining_rc_lb = -7.21e-07
manual_rc_fail = 0
pricing_rc_fail = 0
certificate_leak = 0
single_journey_mip_start_status = OK
```

对比旧 `549.355622s` 基准：

```text
delta = +32.223359s
relative_change = +5.866% wall time
```

也就是说，这次当前代码重跑仍然给出正式 `BPC_TREE_OPTIMAL`，但没有比 550 秒更快，反而慢约 32 秒。该结果比早前 `V4SZ ~= 193s` 的历史记录慢很多；结合后续 conditional sequence exactness fix，当前应以这次重跑作为更可信的 current-code 对照，而不能继续用旧 fast row 作为当前性能承诺。

输出目录：

- `runs/b4_1_v4sz_current_code_30_001_3600s_compare550_20260710/`

## 2026-07-10 追加：V4SZW Warm Integer Start Opt-in

为降低 mature-tail proof search 对 incumbent hint 的敏感性，本轮新增一个 opt-in profile：

```text
profile = V4SZW
base = V4SZ
mip_start_zero_fill_integers = true
```

含义：

- 原 `V4SZ` warm start 只给活动 route 的非零变量和少量时间变量。
- `V4SZW` 在不恢复 inactive-tail 错误时间 hint 的前提下，把所有 compact integer 变量显式给 0/1：
  - all route arc `x`
  - all task-slot visit `y`
  - all active-sortie `z`
  - fixed `journey_active`
- 连续时间变量仍只给真实活动 route 上的值。
- 这只是 HiGHS solver hint，不改变 pricing space、objective、dual bound、certificate 逻辑。

新增接口：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4SZW
LUNAR_ICE_COMPACT_MIP_START_ZERO_FILL_INTEGERS=1
```

30-scale instance001 mature root-tail 60 秒 A/B：

| variant | status | cert scope | row wall_s | final judge wall_s | dual bound | mip start entries | zero-fill integer entries |
|---|---|---|---:|---:|---:|---:|---:|
| V4SZ | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | `53.193375` | `52.195321` | `-0.265217558` | `60` | `0` |
| V4SZW | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | `54.702115` | `53.691981` | `-0.264943636` | `5417` | `5395` |

结论：

- zero-fill warm start 被 HiGHS 接受，`single_journey_mip_start_status=OK`。
- 证书边界正常：`manual_rc_fail=0`、`pricing_rc_fail=0`、`certificate_leak=0`。
- 60 秒内 lower bound 只改善约 `0.000274`，wall time 反而多约 `1.5s`。
- 因此 `V4SZW` 保留为 opt-in diagnostic / stability probe，不进入默认 strongest profile。

新增验证：

```text
PYTHONPATH=src python -m unittest \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_single_journey_pricing_accepts_journey_mip_start \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_v4szw_final_judge_enables_warm_integer_start

Ran 2 tests in 0.280s
OK

PYTHONPATH=src python -m unittest tests.test_lunar_ice_smoke.LunarIceSmokeTests

Ran 224 tests in 42.552s
OK
```

Artifacts：

- `runs/b4_1_v4sz_current_code_60s_ab_probe_30_001_20260710/`
- `runs/b4_1_v4szw_warm_integer_start_60s_probe_30_001_20260710/`

## 2026-07-10 追加：V4SZCAP Slot-Sequence Capacity Arc Pruning

本轮继续做一个更直接的 exact-safe 缩模尝试：

```text
profile = V4SZCAP
base = V4SZ
slot_sequence_capacity_arc_pruning = true
```

核心规则：

```text
如果某个 slot 的 safe slot-sequence capacity <= 1，
则该 slot 不可能服务两个及以上 task。
因此该 slot 的 task->task arc 以及 MTZ visit-order 层都是死结构。
```

实现边界：

- 只用已有 safe lower-bound 推导出来的 slot capacity，不用 heuristic。
- 只删除 capacity<=1 slot 的 task→task arc，并局部跳过该 slot 的 MTZ order variables/rows。
- 不改变 official objective、pricing dual、manual RC、final certificate 逻辑。
- 默认不启用；通过 profile/env opt-in：

```text
LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE=V4SZCAP
LUNAR_ICE_COMPACT_SLOT_SEQUENCE_CAPACITY_ARC_PRUNING=1
```

30-scale instance001 mature root-tail 60 秒 A/B：

| variant | status | cert scope | row wall_s | final judge wall_s | dual bound | vars | rows | disabled MTZ slots | arc pruned |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| V4SZ | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | `53.193375` | `52.195321` | `-0.265217558` | `6005` | `14725` | n/a | n/a |
| V4SZCAP | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_PRICING_FRONTIER` | `56.773924` | `55.756751` | `-0.259805495` | `6004` | `14723` | `1` | `0` |

结论：

- 这个 pruning 是 exact-safe，且短探针中无 redline：`manual_rc_fail=0`、`pricing_rc_fail=0`、`certificate_leak=0`。
- 30-001 上只有最后一个 slot 被 capacity<=1 命中；该 slot 的 task→task arc 已经被其它 time/resource pruning 删除，所以本轮实际只少 `1` 个 MTZ variable 和 `2` 条 row。
- 60 秒 dual bound 略有改善，但 wall time 变慢约 `3.58s`。
- 因此 `V4SZCAP` 暂时保留为 opt-in diagnostic，不进入默认 strongest profile。它对更晚 slot 更多、capacity<=1/0 更密集的实例可能更有价值，但当前 30-001 不是突破点。

新增验证：

```text
PYTHONPATH=src python -m unittest \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_slot_sequence_capacity_arc_pruning_preserves_rc \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_v4szcap_final_judge_enables_slot_sequence_capacity_arc_pruning \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_single_journey_pricing_accepts_journey_mip_start

Ran 3 tests in 0.371s
OK
```

Artifact：

- `runs/b4_1_v4szcap_slot_sequence_capacity_arc_pruning_60s_probe_30_001_20260710/`

## 2026-07-10 追加：Adaptive k-to-(k,m) Partition 3600s 对比

本轮按“先粗分 k，失败后只对该 k 拆 active sortie count m”的思路实现并实测：

```text
--partition-residual-task-count-proof
--partition-residual-active-sortie-count-proof
--partition-adaptive-active-sortie-refinement
--partition-region-time-limit-sec 30
--threads 1
```

Artifact：

- `runs/b4_1_adaptive_k_to_km_partition_30_001_30s_regions_20260710/`

安全边界：

- partition gate pass: `True`
- partition_candidate_can_certify_no_negative: `True`
- official_certificate_allowed: `False`
- certificate leak: `0`
- negative region: `0`
- best_partition_region_lb: `-7.21e-07`
- residual task-count expected/observed/proven/missing: `30 / 30 / 30 / 0`
- residual active-sortie missing/duplicate group: `0 / 0`

自适应分区细节：

| metric | value |
|---|---:|
| row_count | `193` |
| adaptive attempts | `30` |
| coarse accepted | `18` |
| refined k groups | `12` |
| discarded coarse wall_s | `325.323622` |
| reported row wall_s | `503.229692` |
| total internal wall_s | `828.553314` |
| process elapsed_s | `918.48` |
| max RSS KB | `456148` |

和已知基线对比：

| method | comparable wall_s | vs old 549.355622s |
|---|---:|---:|
| old formal root-tail baseline | `549.355622` | baseline |
| current V4SZ formal run | `581.578981` | `+32.223359` |
| full `(k,m)` partition internal wall | `572.532591` | `+23.176969` |
| adaptive k-to-(k,m) internal wall | `828.553314` | `+279.197692` |
| adaptive k-to-(k,m) process elapsed | `918.48` | `+369.124378` |

结论：

- 这个 adaptive partition 是 exact-safe diagnostic：它能完整证明 30-scale instance001 的 root-tail no-negative candidate，没有 redline。
- 但它没有加速，反而显著变慢。主要原因是失败 coarse k 的开销太重：12 个 refined k group 之前额外消耗了 `325.323622s` 的 discarded coarse wall。
- 因此不能把“逐个 k 手动/自适应粗试再拆 m”作为当前最强默认路线。它最多保留为诊断工具，用来学习哪些 k 可粗证、哪些 k 必须直接细分。
- 下一步如果还要加速，方向应改成更激进但 exact-safe 的自动 region policy：基于已知 telemetry 直接跳过会失败的 coarse k，或者在 compact pricing 内部加入可证的 global bound / infeasibility precheck，而不是先让 MIP 在粗 region 上耗尽时间。

## 2026-07-10 追加：V4S/V4SZ 190s Baseline 恢复审计

目标是找回 `V4S/V4SZ ~= 190s` 的 30-scale instance001 精确闭合性能，同时不破坏 exactness。

已完成的安全代码收口：

- `tight_conditional_sequence_big_m` 保留：只影响 tight-time profile，测试证明 reduced cost 不变。
- `inactive-tail time warm-start` 改为 opt-in，不再默认污染 V4S/V4SZ baseline。
- 新增 `LUNAR_ICE_COMPACT_MIP_START_INACTIVE_TAIL_TIME(_MODE)`，支持审计 `zero / previous_end / previous_end_all`。
- 新增 `LUNAR_ICE_COMPACT_HIGHS_*` 搜索参数覆盖，写入 `highs_option_overrides`，只影响 HiGHS 搜索，不改变模型/证书。

验证：

```text
PYTHONPATH=src python -m py_compile \
  src/lunar_ice_bpc/exact/solver/gurobi_compact.py \
  src/lunar_ice_bpc/exact/bpc/pricing/final_judge.py \
  src/lunar_ice_bpc/runners/b4_1_true_dual_proof_tail.py \
  tests/test_lunar_ice_smoke.py

PYTHONPATH=src python -m unittest \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_single_journey_pricing_accepts_journey_mip_start \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_tight_time_big_m_accepts_inactive_tail_mip_start \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_tight_conditional_sequence_big_m_preserves_rc

Ran 3 tests in 0.399s
OK
```

关键对比：

| run | profile | status | final judge wall_s | entry | inactive mode | dual bound / LB | nodes |
|---|---|---:|---:|---:|---|---:|---:|
| historical strongest | V4S | certified | `192.805712` | `118` | unknown | `-7.21e-07` | `7909` |
| current default | V4S | timeout | `549.453731` | `61` | off | `-0.062790509` | `32271` at timeout |
| current zero-inactive | V4S | timeout | `546.107347` | `118` | zero | `-0.062790509` | `32271` at timeout |
| symmetry-off probe | V4S | timeout | `215.632046` | `118` | zero | `-0.174379581` | `9646` at timeout |
| legacy-sequence restored | V4S | certified | `193.352819` | `61` | off | `-7.21e-07` | `7909` |
| historical strongest | V4SZ | certified | `192.595031` | `114` | unknown | `-7.21e-07` | `7909` |
| current default | V4SZ | certified | `580.557552` | `60` | off | `-7.21e-07` | `34155` |
| current zero-inactive | V4SZ | timeout | `270.639917` | `114` | zero | `-0.174379581` | `13764` at timeout |
| zero-inactive unsorted MIP start | V4SZ | timeout | `267.025560` | `114` | zero, unsorted | `-0.174379581` | `13229` at timeout |
| legacy-sequence restored | V4SZ | certified | `193.839102` | `60` | off | `-7.21e-07` | `7909` |

已经排除的解释：

- 不是 `tight-time` 修复导致 V4SZ 变慢：`V4SZ` 本身不启用 `tight_time_arc_big_m`。
- 不是单纯 entry count 从 `114/118` 掉到 `60/61`：把 entry count 补回后仍然不闭合。
- 不是 inactive slot 填 `zero` 就能恢复；`previous_end` 版本之前也未恢复。
- 不是 HiGHS symmetry detection 单项导致；关闭 symmetry 后 240s 内 bound 更差。
- 不是 sparse MIP start 索引排序导致；unsorted 构造顺序只带来约 `3.6s` 小幅改善，dual bound 没改善。

当前判断：

- 根因已定位：slot sequence 约束从旧版无条件时间链 `start[s] >= end[s-1]` 被改成了非 tight-time 下也使用 horizon Big-M 的条件链。这个改动不破坏 exactness，但显著削弱 LP/MIP 搜索，导致 HiGHS 节点数从 `7909` 增到 `34155`。
- 修复方式：当 `active_time_z_bounds=False` 且 `sortie_start_upper_bound >= horizon` 时恢复无条件 sequence 链；只有 `active_time_z_bounds=True` 或 tight-time 将 start 上界降到 horizon 以下时才保留必要 Big-M。
- 修复后 V4S/V4SZ 都重新回到 `BPC_TREE_OPTIMAL`，final judge wall 约 `193s`，节点数回到 `7909`。因此可以进入后续全量 30-scale 20-instance 实验。

新增验证：

```text
PYTHONPATH=src python -m unittest \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_legacy_sequence_chain_preserves_rc \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_tight_time_big_m_accepts_inactive_tail_mip_start \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_tight_conditional_sequence_big_m_preserves_rc

Ran 3 tests in 0.233s
OK
```
