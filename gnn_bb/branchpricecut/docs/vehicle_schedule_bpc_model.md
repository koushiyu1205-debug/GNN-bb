# Vehicle-Schedule Branch-Price-and-Cut 模型说明

生成时间：2026-05-13 10:52:35 CST +0800

本文档描述 `branchpricecut/` 新主线。该目录不复用根目录 `bpc/` 的输出、配置、脚本和文档。

## 1. 模型定位

当前模型转向更接近 You et al. / RouteOpt 使用的 set-partitioning 思路：

```text
column = 一辆车的完整多 sortie schedule
```

这和旧 `bpc/` 的 route-vehicle master 不同。旧模型中 column 是单条 sortie route，同一车辆多条 sortie 的真实时间顺序靠后验 schedule cuts 处理。新模型把完整 schedule 放进 column，因此 master 中的整数解天然是 schedule-feasible。

## 2. Master Problem

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

## 3. Schedule Column

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

## 4. Pricing Problem

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

当前实现使用 integrated schedule-labeling：

```text
扩展当前 sortie
关闭当前 sortie
开启下一条 sortie
```

这不是先生成所有 sortie route 再组合，而是在一个 labeling 队列里同时维护当前 sortie 和已完成 sorties。

## 5. Branching

第一版使用 pricing-compatible Ryan-Foster 分支：

```text
same(i,j):     i 和 j 必须在同一个 vehicle schedule 中
separate(i,j): i 和 j 不能在同一个 vehicle schedule 中
```

在 pricing 中：

- `separate(i,j)` 可以对 partial label 早过滤；
- `same(i,j)` 在完整 schedule 生成时检查。

后续 3PB / 2LBB 应在这个候选类型上实现，不应回退到 schedule variable branching。

## 6. Exactness 边界

当前版本保持以下规则：

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
```

这些参数只保护 Python pricing 不无限膨胀。触发保护时，`PricingResult.exhausted=false`，求解器返回 `PRICING_LIMIT`，不会用该节点 LP bound 证明最优。

## 7. 与旧 bpc/ 的关键区别

| 项目 | 旧 `bpc/` | 新 `branchpricecut/` |
|---|---|---|
| column | 单 sortie route | 完整 vehicle schedule |
| schedule 顺序 | 后验 checker/cuts | column 内生保证 |
| 整数解可行性 | 可能 route 整数但 schedule 不可行 | master 整数解直接可行 |
| pricing 难度 | 单 sortie RCSP | 多 sortie schedule labeling |
| 后续 2LBB 目标 | 混合分支类型 | 标准 RF schedule-pair 分支 |
