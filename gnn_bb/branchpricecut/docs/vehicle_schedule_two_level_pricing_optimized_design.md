# Vehicle-Schedule Layered Pricing 优化设计

生成时间：2026-05-13 12:00:00 CST +0800

本文档描述 `branchpricecut/` 新主线的分层 pricing 设计。该设计保留 vehicle-schedule master：

```text
column = 一辆车的完整多 sortie schedule
```

不退回旧 `bpc/` 的 route-vehicle master。

## 1. 当前 Vehicle-Schedule Master

集合：

```text
I      任务集合
Ω      所有真实可行 complete vehicle schedules
K      可用车辆数量
```

变量：

```text
x_s = 1 if schedule s is selected
```

默认 partitioning master：

```text
min  sum_{s in Ω} c_s x_s

s.t. sum_{s in Ω} a_is x_s = 1      for all i in I
     sum_{s in Ω} x_s <= K
     x_s in {0,1}
```

可选 covering master：

```text
sum_{s in Ω} a_is x_s >= 1          for all i in I
```

covering 不是默认 exact 主线。covering 下整数解必须经过 duplicate removal、shortcut 和 exact schedule feasibility check，失败则不能作为 incumbent。

## 2. Integrated Exact Schedule Pricing 为什么容易爆炸

完整 schedule pricing 同时决定：

```text
1. 每条 sortie 内任务顺序；
2. sortie 关闭时间；
3. 下一条 sortie 开始时间；
4. schedule 内任务集合；
5. same/separate branching 状态。
```

裸 integrated labeling 的状态接近：

```text
(covered set, current sortie sequence, used_sorties, ready_time, resources)
```

即使 20 个任务，`covered set` 与 sortie sequence 的组合也会快速膨胀。根节点 Phase-I dual 往往会鼓励覆盖尚未覆盖任务，导致大量负 reduced-cost partial schedules，因此单靠 exact integrated labeling 容易卡在根节点。

## 3. 新 Layered Pricing 架构

每轮 RMP solve 后按顺序执行：

```text
Layer 0: schedule column pool scan
Layer 1: portfolio sortie route generation
Layer 2: heuristic route-to-schedule composition DP
Layer 3: exact certificate pricing
```

安全边界：

- Layer 0/1/2 只用于快速找 negative columns；
- Layer 0/1/2 找不到列，不能证明 no negative column；
- 节点 lower bound 只能在 Layer 3 exact certificate pricing exhausted 后使用；
- Layer 3 若触发 label/time/queue limit，节点不能被认证完成。

## 4. 为什么 Layer 1 不能只按 `cbar_p` 取 top-M

单条 sortie route 的 reduced contribution：

```text
cbar_p = c_p - sum_i a_ip pi_i
```

只取最小 `cbar_p` 的 top-M 是危险策略。原因：

- `cbar_p > 0` 的短 route 可能能填补两个主 route 之间的时间碎片；
- 单任务 micro route 可能是完成 same component 的唯一方式；
- 部分任务如果没有 per-task quota 会从 route pool 中消失；
- route size、time flexibility、branch relevance 会影响 schedule 组合可行性；
- schedule-level 常数 `F - mu - nu` 不应被错误分摊到 route 中。

因此 Layer 1 必须生成 portfolio route pool：

```text
low_cbar_routes
per_task_routes
route_size_buckets
time_flexible_routes
micro_routes
branch_relevant_routes
historical_useful_routes
diverse_routes
```

## 5. Layer 2 为什么必须明确是 Heuristic

Layer 2 只在 Layer 1 的 route pool 上组合 schedule。只要 route pool 不完整，或者使用 beam pruning / width control，就可能漏掉 negative schedule。

因此 Layer 2 输出：

```text
negative schedule candidates
```

但不输出：

```text
no negative schedule certificate
```

若 Layer 2 找不到 negative schedule，必须进入 Layer 3。

## 6. Layer 3 才能提供 Exact Certificate

Layer 3 可以是：

```text
ng-relaxed DSSR exact certificate
integrated exact schedule-labeling debug fallback
```

当前默认使用 `ng_dssr`。该层解的是 elementary schedule pricing 的 relaxed superset：

- 当前 sortie 内仍保持 elementary；
- 跨 sortie 的重复任务由 ng-memory 和 DSSR memory 控制；
- 遇到 negative non-elementary schedule 时扩大 DSSR memory 后重跑；
- 遇到 elementary negative schedule 时返回真实 schedule column；
- 若 relaxed problem exhaustive 且：

```text
best_rc >= -epsilon
```

则可直接声明 no negative elementary schedule column，因此节点 pricing complete。若 label、queue、memory 或 time limit 触发，不能认证节点。full-memory exact fallback 保留为 `full_memory_fallback_enabled=true` 时的 debug/correctness baseline，默认不作为 20 规模主力证明器。

## 7. Vehicle Lower Bound Cut 与 Dual

可选车辆数下界：

```text
sum_s x_s >= L_veh
L_veh = ceil(sum_i d_i / (S_bar Q))
```

该 row 是 schedule-level row。每个 schedule 的 coefficient 是 1。

若其 dual 为 `nu`，则：

```text
rc_s = c_s - sum_i a_is pi_i - mu - nu
```

拆 route contribution 时：

```text
rc_s = F - mu - nu + sum_{p in s} cbar_p
```

`nu` 不能进入 `cbar_p`，否则多 sortie schedule 会重复扣减。

实际符号不硬编码，代码使用通用公式：

```text
rc_manual = obj_s - sum_rows dual[row] * coeff(row,s)
```

并用 solver reduced cost 做一致性测试。

## 8. 当前代码映射

已落地代码路径：

- RMP 与 reduced-cost audit：`branchpricecut/rmp.py`
- Layer 0 pool scan 与 CG 主流程：`branchpricecut/tree.py`
- Layer 1 portfolio sortie route pool：`branchpricecut/route_pool.py`
- Layer 2 heuristic route-to-schedule DP：`branchpricecut/schedule_dp.py`
- Layer 3 ng-DSSR engine：`branchpricecut/ng_dssr.py`，由 `branchpricecut/pricing.py` 的 `DSSRSchedulePricing` 调用

当前实现细节：

- `master_cover_mode` 默认是 `partitioning`；`covering` 仅是实验模式。
- Phase-I 只用 Phase-I dual pricing；Phase-I artificial sum 为 0 后直接切 Phase-II，重新求 Phase-II RMP 并提取 Phase-II dual。
- RF branching 当前通过 column filtering / pricing feasibility enforce，不作为额外 RMP dual row。
- Layer 0 pool scan 按当前节点 RMP column signature 判断缺列，并用当前 true dual 重新计算 reduced cost。
- Layer 1 enforce component-level `separate`；`same` 只做 metadata 标记，不错误过滤 partial route；`time_flexible_routes` 使用 ready/duration 与 deadline slack；`branch_relevant_routes` 在存在 same component 时优先保留 same-component routes；`diverse_routes` 使用 covered task set、route length、time cluster。
- Layer 2 对 component-level branch state 做保守 dominance；beam pruning 或 width control 触发时 `exhausted=false`；top-K 输出会做相同 covered task set 去重和 Jaccard 相似度限制。
- `DSSRSchedulePricing` 默认调用 `ng_dssr`；`PricingResult.certificate=true` 可以来自 ng-relaxed superset exhaustive 且 `best_rc >= -epsilon`，并通过 `certificate_from_relaxation=true` 标记。
- full-memory integrated exact fallback 仍保留，但由 `full_memory_fallback_enabled` 控制，默认关闭。
- covering integer incumbent 必须先满足 triangle/shortcut 非增和服务成本非负前置检查，再经过 duplicate removal、shortcut rebuild 和 exact schedule feasibility check；失败不作为 incumbent。

当前明确不覆盖：

- arc-on / arc-off / route-level branching；
- 文档中的 `check_schedule_reduced_cost_consistency(phase, num_samples=20)` 签名，代码使用 `check_schedule_reduced_cost_consistency(solution, tolerance=...)` 并检查全部 active columns；
- `branching coverage` 测试里 column-level `intersection empty` 表述。

## 9. Exactness 边界

必须保持：

1. Master column 是完整真实可行 schedule；
2. Phase-I dual 不得复用到 Phase-II；
3. 所有影响 `x_s` 的 row dual 都进入 schedule reduced cost；
4. Layer 0/1/2 只找列，不认证；
5. Layer 3 `ng_dssr` 或 full-memory fallback exhausted 后才使用节点 lower bound；
6. branching constraints 在 Layer 1、Layer 2、Layer 3 均被执行；
7. covering mode incumbent 必须通过 post-processing 和 exact feasibility recheck。

注意：RF `same(i,j)` 与 `separate(i,j)` 在单个 column 集合上会共享“不覆盖 i/j 任一任务”的 column；互斥性是对完整 partitioning 解空间而言，不是对每条 column 而言。
