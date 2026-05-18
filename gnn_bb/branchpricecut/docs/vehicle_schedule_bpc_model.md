# Vehicle-Schedule Branch-Price-and-Cut 模型说明

生成时间：2026-05-13 10:52:35 CST +0800

本文档描述 `branchpricecut/` 的模型路线。当前默认主力求解器是 `master_type="hybrid_route"`：复用根目录 `bpc/` 的低维 route-vehicle BPC 核心，但统一由 `branchpricecut` 配置、脚本和结果目录调度。完整 vehicle-schedule master 保留为 `master_type="vehicle_schedule"` baseline。

## 1. 模型定位

`branchpricecut` 现在保留两种 master：

```text
hybrid_route      column = 单 sortie route + vehicle assignment
vehicle_schedule  column = 一辆车的完整多 sortie schedule
```

20 规模 proof 默认使用 `hybrid_route`，原因是完整 schedule pricing 的 label state 过高；`vehicle_schedule` 用于小规模 correctness baseline 和 ng-DSSR 对照。

## 2. Hybrid Route-Level Master

```text
lambda[p,r] = 车辆 r 是否选择单 sortie route p
y[r]        = 车辆 r 是否启用
```

RMP 包含：

```text
sum_r sum_p a_ip lambda[p,r] = 1              for all task i
sum_p a_ip lambda[p,r] <= y[r]                for all task i, vehicle r
sum_p lambda[p,r] <= S_bar y[r]               for all vehicle r
sum_p w_p lambda[p,r] <= H y[r]               for all vehicle r
y[r+1] <= y[r]
valid cuts and branch rows
```

其中 `w_p` 是 route work-time lower bound，不包含不同 sortie 之间的等待时间。整数解必须经过 exact schedule checker；不可排程的同车 route 集合通过 schedule no-good cut 排除。

route pricing 是单 sortie RCSP。节点只有在 route pricing exhausted 且没有负 reduced-cost route 时，才能使用该节点 LP lower bound。

## 3. Hybrid Exactness 机制

hybrid 模式不是简单“先解 route master 再检查”。exactness 依赖以下闭环：

- route-level RMP lower bound 只在 exact route pricing exhausted 后使用；
- integer assignment 必须通过 exact multi-sortie schedule checker；
- checker 发现不可行 route set 时，加入 valid schedule no-good cuts；
- crossing cuts、schedule capacity cuts、no-good cuts 的 dual 都进入 route reduced cost；
- branch constraints 同时传入 RMP 和 pricing。

## 4. Vehicle-Schedule Baseline Master

完整 schedule-column baseline 仍是更自然的 set-partitioning 模型：

设：

```text
I        任务集合
K        可用车辆数量
Ω        所有真实可行 vehicle schedules
a_is     schedule s 是否服务任务 i
c_s      schedule s 的固定车辆成本 + 所有 sortie 成本
x_s      是否选择 schedule s
```

整数 master：

```text
min  sum_{s in Ω} c_s x_s

s.t. sum_{s in Ω} a_is x_s = 1      for all i in I
     sum_{s in Ω} x_s <= K
     x_s in {0,1}
```

LP relaxation 用 column generation 求解。

## 5. Vehicle-Schedule Schedule Column

一个 schedule 是有序 sortie 序列：

```text
s = (p_1, p_2, ..., p_q), q <= S_bar
```

每个 sortie：

```text
p_l = (0, i_1, ..., i_m, 0)
```

schedule 必须满足：

- 每个任务在该 schedule 内最多出现一次；
- 每条 sortie 满足载重、电量、任务时间窗；
- sortie 之间按真实 ready time 串接；
- 每次 sortie 结束后考虑能量恢复时间 `energy / rho`；
- 最终 ready time 不超过 horizon `H`；
- sortie 数不超过 `S_bar`。

## 6. Vehicle-Schedule Pricing Problem

RMP dual：

```text
pi_i     task coverage dual
mu       fleet constraint dual
```

Phase-II reduced cost：

```text
rc_s = c_s - sum_i a_is pi_i - mu
```

Phase-I reduced cost：

```text
rc_s^I = - sum_i a_is pi_i - mu
```

pricing 要找：

```text
min_{s in Ω} rc_s
```

vehicle-schedule baseline 使用 layered pricing：

```text
Layer 0: schedule column pool scan
Layer 1: portfolio sortie route generation
Layer 2: heuristic route-to-schedule composition DP
Layer 3: ng-relaxed DSSR certificate pricing
```

Layer 0/1/2 只用于快速找 negative reduced-cost schedule columns。只有 Layer 3 `ng_dssr` exhausted 后，当前节点 lower bound 才能用于证明。`ng_dssr` 的 certificate 来自 relaxed superset exhaustive 且 `best_rc >= -epsilon`；full-memory integrated exact fallback 仅在 `full_memory_fallback_enabled=true` 时作为 debug/correctness baseline。

## 7. Vehicle-Schedule Branching

vehicle-schedule baseline 使用 pricing-compatible Ryan-Foster 分支：

```text
same(i,j):     i 和 j 必须在同一个 vehicle schedule 中
separate(i,j): i 和 j 不能在同一个 vehicle schedule 中
```

在 pricing 中：

- `separate(i,j)` 可以对 partial label 早过滤；
- `same(i,j)` 在完整 schedule 生成时检查。

hybrid route-level 主线已使用 route-compatible Ryan-Foster、task-vehicle、arc on/off 和 vehicle-use branching。

## 8. Vehicle-Schedule Exactness 边界

vehicle-schedule baseline 保持以下规则：

- SCIP 只求 RMP LP；
- lower bound 只在 exact pricing exhausted 后使用；
- 若 pricing 触发 label、queue、候选池或单次 pricing 时间保护而未 exhausted，节点不能被证明完成；
- incumbent 由完整 schedule columns 组成，天然满足真实 schedule feasibility；
- branching 约束传入 pricing，子节点覆盖父节点解空间且互斥。

当前内存/时间保护参数：

```text
max_labels_per_pricing
max_generated_labels_per_pricing
max_queue_size_per_pricing
max_candidate_pool_per_pricing
max_pricing_seconds
max_pricing_memory_mb
pricing_memory_check_interval
exact_pricing_enable_dominance
exact_pricing_algorithm
full_memory_fallback_enabled
ng_neighborhood_size
dssr_certificate_without_full_memory
```

`max_generated_labels_per_pricing=0` 表示不使用 generated-label 硬截断。当前证明配置默认 `exact_pricing_algorithm="ng_dssr"` 且 `full_memory_fallback_enabled=false`。触发 queue、memory、label 或 time guard 时，`PricingResult.exhausted=false`，求解器返回 `PRICING_LIMIT`，不会用该节点 LP bound 证明最优。

## 9. 两条主线的关键区别

| 项目 | hybrid_route / `bpc` core | vehicle_schedule baseline |
|---|---|---|
| column | 单 sortie route | 完整 vehicle schedule |
| schedule 顺序 | 后验 checker/cuts | column 内生保证 |
| 整数解可行性 | 可能 route 整数但 schedule 不可行 | master 整数解直接可行 |
| pricing 难度 | 单 sortie RCSP | 多 sortie schedule labeling |
| 后续 2LBB 目标 | 混合分支类型 | 标准 RF schedule-pair 分支 |
