# Route-Vehicle BPC with Schedule Cuts 与原问题等价性证明

本文档只证明模型等价性，不讨论搜索策略、ML、branching 选择速度或实现性能。

当前 `bpc/` 主线的模型是：

```text
route-vehicle master + schedule no-good cuts
```

它不是 vehicle-schedule master。route-vehicle master 的列是一条单独 sortie route；vehicle-schedule master 的列是一辆车完整的一天 schedule。

本文要证明的是：


```text
原问题
= 完整 route-vehicle master + 完整 schedule no-good cuts 的整数模型
```

其中“完整”有两个含义：

```text
1. route 集合包含所有资源可行的单条 sortie route；
2. schedule cuts 包含所有需要排除的不可排程 route 集合，或至少包含每个不可排程集合的一个不可排程子集 cut。
```

如果只使用部分 route columns 或部分 schedule cuts，则当前模型只是原问题的松弛或受限近似，不是显式等价模型。

## 1. 原问题定义

设：

```text
I    任务集合
R    车辆集合
0    depot
H    每辆车 horizon / 总工作时间上界
Q    每条 sortie 载重上界
B    每条 sortie 可用电量上界
F    车辆固定成本
```

每个任务 `i in I` 有：

```text
r_i      最早服务时间
D_i      最晚完成时间
sigma_i  服务时长
d_i      需求/载重
g_i      服务能耗
c_i      服务成本
```

任意两个节点 `i,j in I union {0}` 之间有：

```text
tau_ij     行驶时间
e_ij       行驶能耗
c_ij       行驶成本
```

原问题的一个可行解由每辆车的 sortie 序列组成：

```text
S_r = (p_1, p_2, ..., p_m)
```

每条 sortie `p_k` 是：

```text
0 -> i_1 -> i_2 -> ... -> i_q -> 0
```

原问题约束为：

```text
1. 每个任务被恰好一个 sortie 服务一次；
2. 每条 sortie 内任务不重复；
3. 每条 sortie 满足任务时间窗；
4. 每条 sortie 总载重不超过 Q；
5. 每条 sortie 总能耗不超过 B；
6. 同一辆车的 sortie 序列存在真实执行时间；
7. 每辆车最终 ready time 不超过 H；
8. 目标最小化所有 sortie 成本 + 使用车辆固定成本。
```

这里“真实执行时间”包含：

```text
depot 出发时间；
任务间行驶时间；
任务等待时间；
任务服务时间；
返回 depot 时间；
sortie 完成后恢复/充电/准备下一 sortie 的时间；
```

只要某辆车的多条 sortie 无法以任何顺序满足这些时间条件，该车辆的 route 集合在原问题中不可行。

## 2. 单条 route 集合

定义完整 route 集合 `P`：

```text
P = 所有资源可行的单条 sortie route
```

对每条 route `p in P`：

```text
a_ip = 1 if route p 服务任务 i, else 0
c_p  = route p 的行驶成本 + 服务成本
w_p  = route p 的车辆工作时间下界
```

其中：

```text
w_p = travel_time_p + service_time_p + energy_p / rho
```

注意：`w_p` 是下界，不一定等于该 route 在某个完整车辆 schedule 中实际占用的时间，因为实际排程可能包含等待时间。

## 3. Route-vehicle integer master

变量：

```text
lambda_pr in {0,1}   车辆 r 是否执行 route p
y_r       in {0,1}   车辆 r 是否启用
```

基础 route-vehicle master：

```text
min sum_r F y_r + sum_r sum_p c_p lambda_pr

sum_r sum_p a_ip lambda_pr = 1              for all i in I

sum_p lambda_pr <= S_bar y_r                for all r in R

sum_p w_p lambda_pr <= H y_r                for all r in R

y_{r+1} <= y_r                              vehicle symmetry breaking
```

基础 route-vehicle master 不包含同一车辆多条 sortie 的真实排序变量。因此它通常是原问题松弛。

## 4. Schedule 可排程性

对任意 route 集合 `C subset P`，定义谓词：

```text
Sched(C) = true
```

当且仅当存在 `C` 中所有 routes 的一个排列：

```text
(p_1, p_2, ..., p_|C|)
```

使得一辆车可以从时间 0 开始依次执行这些 routes，并满足：

```text
1. 每条 route 内任务时间窗；
2. route 与 route 之间的 ready time 衔接；
3. 每条 route 的载重、电量；
4. 车辆最终 ready time <= H。
```

如果不存在这样的排列，则：

```text
Sched(C) = false
```

## 5. 完整 schedule no-good cuts

对任意不可排程 route 集合 `C`，即：

```text
Sched(C) = false
```

加入 schedule no-good cut：

```text
sum_{p in C} lambda_pr <= |C| - 1           for all r in R
```

这表示：任何一辆车都不能同时选择 `C` 中所有 routes。

如果车辆同质，则对所有车辆 `r in R` 加同一类 cut 是有效的。如果车辆异质，则 cut 应按车辆类型或车辆资源参数分别定义。

### 5.1 route-set schedule packing cut

no-good cut 是 route-set schedule packing cut 的一个特例。对任意 route 集合 `C`，定义：

```text
U(C) = 一辆真实车辆最多能从 C 中排程的 route 数
```

若 `U(C)<|C|`，则可加入：

```text
sum_{p in C} lambda_pr <= U(C) y_r          for all r in R
```

当 `U(C)=|C|-1` 时，它退化为普通 schedule no-good cut；当 `U(C)` 更小时，它更强。当前代码的 LP separator 仍可在当前 LP 违反且 `U(C)<|C|` 时加入该 cut；但 RIM 回流和整数解校验中的不可排程 conflict 只在 `U(C)<|C|-1` 时提升为 route-set packing conflict，避免把与 no-good 同强度的 cut 大量加入主问题。若 oracle 超过状态上限或无法证明，则不加 cut。

## 6. 完整扩展模型

定义完整 route-vehicle schedule-cut master：

```text
min sum_r F y_r + sum_r sum_p c_p lambda_pr

sum_r sum_p a_ip lambda_pr = 1              for all i in I

sum_p lambda_pr <= S_bar y_r                for all r in R

sum_p w_p lambda_pr <= H y_r                for all r in R

y_{r+1} <= y_r

sum_{p in C} lambda_pr <= |C| - 1
    for all r in R,
    for all C subset P with Sched(C)=false

lambda_pr in {0,1}
y_r in {0,1}
```

下面证明该完整扩展模型与原问题等价。

## 7. 原问题可行解映射到完整扩展模型

### 命题 1

任意原问题可行解都可以映射为完整扩展模型的可行整数解。

### 证明

给定一个原问题可行解。对每辆车 `r`，它执行若干条 sortie：

```text
S_r = (p_1, p_2, ..., p_m)
```

每条 sortie 都是单条资源可行 route，因此：

```text
p_k in P
```

令：

```text
lambda_{p_k,r} = 1
y_r = 1 if vehicle r is used
```

其他 `lambda` 取 0。

逐项检查：

### 任务覆盖

原问题中每个任务被恰好服务一次，所以：

```text
sum_r sum_p a_ip lambda_pr = 1
```

### Sortie 数

如果原问题限制每辆车最多 `S_bar` 条 sortie，则：

```text
sum_p lambda_pr <= S_bar y_r
```

### 车辆工作时间下界

原问题中车辆 `r` 的真实执行时间不超过 `H`。因为 `w_p` 是 route `p` 的工作时间下界：

```text
sum_p w_p lambda_pr <= actual_work_time_r <= H
```

所以：

```text
sum_p w_p lambda_pr <= H y_r
```

### Schedule cuts

原问题中每辆车选中的 route 集合本身已经按真实时间顺序执行，因此对每辆车 `r`，其 route 集合 `C_r` 满足：

```text
Sched(C_r) = true
```

任意 schedule no-good cut 都对应某个不可排程集合 `C`，即 `Sched(C)=false`。如果某辆车在原问题可行解中同时选择了 `C` 中所有 routes，则 `C` 会是可排程的，因为它是可排程集合 `C_r` 的子集。矛盾。

因此所有 schedule no-good cuts 都满足。

目标值方面，route 成本和车辆固定成本与原问题一致。

所以原问题可行解映射为完整扩展模型可行整数解，且目标值相同。

证毕。

## 8. 完整扩展模型映射到原问题

### 命题 2

任意完整扩展模型的可行整数解都可以映射为原问题可行解。

### 证明

给定完整扩展模型的一个可行整数解。对每辆车 `r`，定义其选择的 route 集合：

```text
C_r = {p in P : lambda_pr = 1}
```

### 每条 route 单独可行

因为 `P` 只包含资源可行的单条 sortie route，所以 `C_r` 中每条 route 都满足：

```text
任务时间窗
载重
电量
depot 出发和返回
route 内任务不重复
```

### 每个任务恰好服务一次

由覆盖约束：

```text
sum_r sum_p a_ip lambda_pr = 1
```

所以每个任务被恰好一个选中 route 服务。

### 每辆车 route 集合可排程

现在证明每个 `C_r` 都满足：

```text
Sched(C_r) = true
```

反证。假设存在某辆车 `r`，使得：

```text
Sched(C_r) = false
```

由于完整扩展模型包含所有不可排程 route 集合的 no-good cut，所以对集合 `C_r` 有 cut：

```text
sum_{p in C_r} lambda_pr <= |C_r| - 1
```

但根据 `C_r` 定义，对所有 `p in C_r`：

```text
lambda_pr = 1
```

因此：

```text
sum_{p in C_r} lambda_pr = |C_r|
```

这违反 no-good cut。矛盾。

所以：

```text
Sched(C_r) = true
```

即每辆车选择的 routes 都存在真实执行顺序。

### 构造原问题解

对每辆车 `r`，取 `Sched(C_r)=true` 的可行排序作为车辆 sortie 执行顺序。由于每条 route 单独可行、任务覆盖恰好一次、车辆 schedule 可行，得到一个原问题可行解。

目标值方面，完整扩展模型的目标：

```text
sum_r F y_r + sum_r sum_p c_p lambda_pr
```

正好等于该原问题解的车辆固定成本加所有 sortie 成本。

所以完整扩展模型可行整数解映射为原问题可行解，且目标值相同。

证毕。

## 9. 等价性定理

### 定理

若：

```text
1. P 包含所有资源可行单条 sortie routes；
2. schedule cuts 包含所有不可排程 route 集合的 no-good cuts；
3. 车辆同质，或 schedule cuts 按车辆资源类型正确区分；
4. route 成本与原问题 sortie 成本一致；
```

则：

```text
原问题
```

与：

```text
完整 route-vehicle master + 完整 schedule no-good cuts
```

在整数可行域和目标值上等价。

### 证明

由命题 1，任意原问题可行解可以映射到完整扩展模型，且目标值相同。

由命题 2，任意完整扩展模型可行整数解可以映射到原问题，且目标值相同。

因此两者可行解集合在目标值保持意义下一一对应，最优目标值相同。

证毕。

## 10. 为什么动态切割也可以 exact

实际 BPC 不会一开始枚举所有不可排程集合 `C`，而是在搜索过程中动态发现并加入 schedule cuts。

动态切割版可以保持 exactness 的条件是：

```text
每当算法准备接受一个整数 route-vehicle 解作为 incumbent，
必须先对每辆车的 route 集合做 exact schedule feasibility check。
```

如果检查可排程，则该解是原问题可行解。

如果检查不可排程，则必须加入 valid schedule cut 并重新求解当前节点，不能接受该解，也不能用它作为最终最优解。该 cut 可以是 pair conflict、route-set schedule packing、schedule-capacity conflict 或 no-good；关键是 cut 必须由 exact schedule checker / exact oracle 证明有效。

当前还加入两类默认启用的 LP 强化不等式，并保留一类默认关闭的实验性不等式：

```text
subset-row:
sum_{p,r} floor(|p∩S|/k) lambda[p,r] <= floor(|S|/k)

limited-memory rank-1:
sum_{p,r} floor((sum_{i in S}m_i a_ip)/d) lambda[p,r] <= floor((sum_{i in S}m_i)/d)

schedule subset cost lower bound:
sum_p c[p]lambda[p,r] - L(S)sum_{i in S}z[i,r] + L(S)(|S|-1)y[r] >= 0
```

`subset-row` 是 set-partitioning 的标准整数有效不等式，当前默认启用。`limited-memory rank-1` 是 cover 等式的 rank-1 CG rounding；memory 只限制 multiplier pattern 的候选生成，不参与有效性证明。`schedule subset cost lower bound` 默认关闭；若作为实验项打开，其中的 `L(S)` 必须由 exact 单车 schedule cost oracle 证明，oracle 超限或未完成时不加 cut。整数解中，若车辆 `r` 未完整服务 `S`，该不等式在非负 route 成本下自动成立；若完整服务 `S`，车辆真实 schedule 的变量成本至少为 `L(S)`。因此这些 cut 只收紧 LP relaxation，不改变原问题整数可行域。

因此，虽然动态切割版在中间过程中只包含部分 schedule cuts，但只要：

```text
1. 不可排程整数解永远不会被接受为 incumbent；
2. 不可排程整数解会生成 valid cut；
3. 分支定价最终证明时所有 open nodes 都已被正确处理；
```

最终最优性证明仍然有效。

## 11. 如果 cut 只加不可排程子集是否足够

实际实现中，若某辆车选择的完整 route 集合 `C` 不可排程，可以不一定对整个 `C` 加 cut，而是找一个不可排程子集 `C' subset C`，并加：

```text
sum_{p in C'} lambda_pr <= |C'| - 1
```

只要 `Sched(C')=false`，这个 cut 仍然 valid。

并且它会排除当前解，因为当前解选择了 `C` 中所有 routes，自然也选择了 `C'` 中所有 routes。

因此使用不可排程子集 cut 是安全的，而且通常更强。

## 12. LP relaxation 不等价

需要明确：

```text
等价性只针对整数模型。
```

route-vehicle master 的 LP relaxation 通常比 vehicle-schedule master 的 LP relaxation 弱。

原因是 LP 解可以分数选择多个 route 集合，schedule no-good cuts 主要切整数不可排程组合，对分数解的约束力有限。

因此即使完整 schedule cuts 存在：

```text
整数可行域等价；
LP bound 不一定和 vehicle-schedule master 一样强。
```

这解释了当前 clean BPC 在 20 规模上 lower bound 推进较慢的原因之一。

## 13. 与 vehicle-schedule master 的区别

vehicle-schedule master 的列是完整车辆 schedule：

```text
k = (p_1, p_2, ..., p_m)
```

每个 column 天然满足同车多 sortie 的真实顺序。因此它的 master 可以写成：

```text
sum_k a_ik z_k = 1
sum_k z_k <= |R|
z_k in {0,1}
```

在列集合完整时，它更直接等价于原问题。

当前 route-vehicle master 的列是单条 route：

```text
p = single sortie route
```

它需要 schedule cuts 才能补足同车 route 集合的可排程性。

因此：

```text
vehicle-schedule master:
  列本身包含时间顺序，天然更强；

route-vehicle master with schedule cuts:
  列更简单，pricing 更容易，但需要 cuts 修补 schedule 约束。
```

## 14. 当前实现需要满足的等价性条件

当前 `bpc/` 实现要保持与原问题等价，需要满足：

```text
1. evaluate_route / exact_pricing 生成的 route 必须覆盖所有资源可行单条 sortie route；
2. route 内部时间窗、载重、电量检查必须与原问题一致；
3. schedule checker 必须精确判断 route 集合是否可排程；
4. 不可排程 cut 必须只基于 checker 证明 infeasible 的 route 集合；
5. incumbent 必须只接受 checker 通过的整数解；
6. 如果 pricing 没有完整证明无负 reduced-cost route，不能声明节点 LP 完成；
7. 如果 schedule cut separation 还没处理完，不能声明整数解是原问题最优。
```

只要这些条件满足，动态 route-vehicle BPC with schedule cuts 在最终收敛时与原问题等价。

## 15. Schedule-Pack Candidate-Pool Relaxation 的证明边界

新增的 `schedule-pack` relaxation 会把 incumbent schedule 作为 seed columns，并在候选 route 集合内做 dual pricing，直到候选集合内没有负 reduced-cost schedule column，或触发时间/列数限制。浅层节点版本使用 vehicle-indexed schedule columns，并尊重节点分支约束和已有 valid cuts。

因此：

```text
schedule_pack_diagnostic_objective
schedule_pack_relaxation_root_objective
schedule_pack_relaxation_best_objective
```

在 `exact_over_full_route_space=false` 时，不能作为原问题 lower bound，不能用于剪枝，也不能用于证明最优，且不能混入 `dual_bound` 或 `diagnostic_dual_bound`。full route-space pricing 如果已经发现负 reduced-cost 的可行 schedule column，可以把该列安全加入 RMP；这只是在扩大受限主问题列集，不是完整 pricing 证书。只有完整 exact schedule pricing 已经结束，并证明全 route space 中没有负 reduced-cost schedule column，即日志给出 `exact_over_full_route_space=true` 时，schedule-pack master 的 LP 值才可以作为有效下界证书。

当前 full route-space pricing 使用集成式 label search，而不是先枚举所有单 sortie route。该实现仍保持证明边界：route prefix 只按已经发生的载重、服务时间窗和已消耗能量做安全剪枝；同一已覆盖任务集合和 route 数下，较早 ready time 且较低 reduced component 的 label 支配另一个 label。若搜索因时间或状态上限停止，则无论当前找到的 best reduced cost 是负、零还是正，都不能作为“无负列”证明。

当前代码的接入规则是：

```text
if exact_over_full_route_space:
    node.lower_bound = max(route_vehicle_bound, schedule_pack_bound)
else:
    schedule_pack_bound 只作为诊断和节点排序信号
```

该规则保持精确性，因为完整 schedule column master 是原问题的 LP 松弛：每个 column 是一辆车可真实执行的一串 sorties；cover、vehicle-use、当前 valid cuts 和分支约束均同步进入该 LP；full route-space pricing 完整结束后，没有遗漏负 reduced-cost schedule column。

若日志中只有 `exact_over_candidate_routes=true`，则只表示候选 route 集合内收敛；由于候选集合可能被截断，它仍不能替代全 route space 的 exact schedule pricing。

## 16. 简短结论

当前模型与原问题的关系是：

```text
基础 route-vehicle master
  是原问题松弛；

基础 route-vehicle master + 完整 schedule no-good cuts
  与原问题整数可行域等价；

动态 BPC 逐步添加 schedule cuts
  中间是松弛；
  只要每个不可排程整数解都被切掉，最终证明仍然 exact。
```
