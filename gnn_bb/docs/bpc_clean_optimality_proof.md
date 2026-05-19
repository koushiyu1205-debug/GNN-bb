# Clean BPC 最优性证明

本文档证明根目录 `bpc/` 当前 clean Branch-Price-and-Cut 主线的最优性逻辑。当前模型是：

```text
route-vehicle BPC with schedule cuts
```

它不是 vehicle-schedule BPC。也就是说，master column 是一条单独 sortie route，而不是一辆车完整日程。真实的同车多 sortie 时间顺序由 schedule feasibility checker 和 schedule no-good cuts 处理。

本文证明的是：在若干明确条件成立时，当前算法可以作为原问题的 exact algorithm；如果这些条件被破坏，则只能作为启发式或不完整算法。

## 1. 原问题

设任务集合为 `I`，车辆集合为 `R`。原问题要求：

```text
1. 每个任务 i in I 被服务恰好一次；
2. 每条 sortie 从 depot 出发并回到 depot；
3. 每条 sortie 满足任务时间窗、载重、电量限制；
4. 同一辆车可以执行多条 sortie；
5. 同一辆车的多条 sortie 必须存在一个真实执行顺序；
6. 每辆车总工作时间不超过 H；
7. 目标最小化 route 成本与车辆固定成本。
```

这里“真实执行顺序”指：如果车辆先执行 route `p`，完成后必须等待返回 depot、恢复/充电等时间，之后才能执行下一条 route；所有任务时间窗和总 horizon 都必须满足。

## 2. Route-vehicle master 是原问题松弛

当前 master 的 route column `p` 是单条资源可行 sortie：

```text
p = 0 -> i1 -> i2 -> ... -> iq -> 0
```

每条 route 内部满足：

```text
time-window feasibility
capacity feasibility
energy feasibility
single-route horizon feasibility
elementarity inside route
```

master 变量为：

```text
lambda[p,r] ∈ {0,1}   vehicle r 是否执行 route p
y[r]        ∈ {0,1}   vehicle r 是否启用
```

整数 master 的基本约束为：

```text
sum_r sum_p a[i,p] lambda[p,r] = 1          for all i in I
sum_p lambda[p,r] <= S_bar y[r]             for all r in R
sum_p w[p] lambda[p,r] <= H y[r]            for all r in R
y[r+1] <= y[r]
```

其中 `w[p]` 是 route `p` 的车辆工作时间下界：

```text
w[p] = travel_time[p] + service_time[p] + energy[p] / rho
```

### 引理 1：任意原问题可行解都对应一个 route-vehicle master 可行解

证明：

给定任意原问题可行解。对每辆车 `r` 的每条实际 sortie，取其任务访问序列作为 route column `p`，令：

```text
lambda[p,r] = 1
y[r] = 1 if vehicle r is used else 0
```

因为原问题每条 sortie 本身资源可行，所以所有被选 route 都在完整 route 集合中。因为原问题每个任务恰好服务一次，所以覆盖约束成立。因为原问题每辆车 sortie 数不超过 `S_bar`，所以 sortie 数约束成立。因为 `w[p]` 是该 sortie 实际占用车辆时间的下界，所以：

```text
sum_p w[p] lambda[p,r] <= actual vehicle working time <= H
```

因此该原问题可行解映射为 route-vehicle master 可行解。

证毕。

### 引理 2：route-vehicle master 可行解不一定是原问题可行解

证明：

route-vehicle master 只知道某辆车选择了哪些单条 route，并使用 `sum_p w[p] <= H` 作为总时间下界约束。它没有显式决定这些 route 的执行顺序，也没有显式检查不同 route 之间由任务时间窗导致的等待、冲突和 horizon 可行性。

因此可能存在 route 集合 `C`，其中每条 route 单独可行，且 `sum_{p in C} w[p] <= H`，但无论如何排列都不能形成真实 schedule。这样的解满足 route-vehicle master，却不满足原问题。

证毕。

结论：

```text
原问题可行域 ⊆ route-vehicle master 整数可行域
```

所以基础 route-vehicle master 是原问题的松弛。

## 3. Schedule no-good cuts 的有效性

当前 clean BPC 使用 exact schedule checker 检查某辆车选择的 route 集合 `C` 是否可排程。如果 `C` 被证明不可排程，则对每辆同质车辆加入：

```text
sum_{p in C} lambda[p,r] <= |C| - 1          for all r in R
```

### 引理 3：schedule no-good cut 对原问题有效

证明：

假设 route 集合 `C` 经过 exact schedule checker 证明不可排程。则不存在任何真实车辆 schedule 可以让同一辆车同时执行 `C` 中所有 routes。

因此，在任何原问题可行解中，对任意车辆 `r`，不可能有：

```text
lambda[p,r] = 1 for all p in C
```

也就是：

```text
sum_{p in C} lambda[p,r] <= |C| - 1
```

该 cut 只排除原问题不可行的同车 route 组合，不排除任何原问题可行解。

证毕。

### 引理 4：如果所有不可排程整数 route 集合都被切掉，则整数 master 与原问题等价

证明：

由引理 1，任意原问题可行解满足 route-vehicle master 和所有 valid schedule cuts。

反向考虑任意满足 route-vehicle master 和所有必要 schedule cuts 的整数解。对每辆车 `r`，设其选择的 route 集合为 `C_r`。若 `C_r` 不可排程，则按假设相应 no-good cut 已存在，会禁止该组合，与当前整数解可行矛盾。因此每个 `C_r` 都可排程。

又因为 master 覆盖约束保证每个任务恰好服务一次，每条 route 自身资源可行，每辆车 sortie 数和工作时间约束成立，因此该整数解可转化为原问题可行解。

证毕。

结论：

```text
route-vehicle master + 完整 schedule cuts
= 原问题整数可行域
```

## 4. RMP 与完整 master

完整 master 包含所有资源可行 route columns。RMP 只包含当前已生成的 route 子集。

对于最小化问题，RMP 是完整 master 的限制问题：

```text
columns(RMP) ⊆ columns(full master)
```

因此：

```text
LP(RMP) objective >= LP(full master) objective
```

也就是说，RMP LP objective 本身是受限问题的值；只有当 pricing 证明不存在负 reduced-cost column 时，RMP LP 才等于当前节点完整 master LP。

## 5. Reduced cost 与 exact pricing

设 RMP dual 为：

```text
pi[i]      task covering dual
eta[r]     sortie-count dual
beta[r]    vehicle-time dual
gamma[g]   schedule-cut dual
delta[h]   branching-constraint dual
```

对 route `p` 和车辆 `r`，Phase-II reduced cost 为：

```text
rc[p,r] = c[p]
        - sum_i a[i,p] pi[i]
        - eta[r]
        - beta[r] w[p]
        - sum_g b[g,p,r] gamma[g]
        - sum_h q[h,p,r] delta[h]
```

Phase-I reduced cost 使用 `c[p]=0`。

### 引理 5：若 exact pricing 找不到负 reduced-cost column，则当前 RMP LP 等于当前节点完整 master LP

证明：

这是线性规划列生成的标准最优性条件。给定 RMP primal optimal solution 和对应 dual solution。如果所有未生成 columns 的 reduced cost 都非负，则该 dual solution 对完整 master dual 可行。

因为 RMP primal value 等于 RMP dual value，而该 dual 对完整 master 可行，所以：

```text
full master LP optimum >= RMP dual value = RMP primal value
```

又因为 RMP 是 full master 的限制问题：

```text
full master LP optimum <= RMP primal value
```

两者合并得到：

```text
full master LP optimum = RMP primal value
```

证毕。

因此，只有 exact pricing 完整结束后，当前节点 LP bound 才被认证。

## 6. Phase-I 可行性证明

Phase-I RMP 加入人工覆盖变量：

```text
u[i] >= 0
min sum_i u[i]
sum_r sum_p a[i,p] lambda[p,r] + u[i] = 1
```

### 引理 6：Phase-I exact pricing 完成后，若最优值大于 0，则当前节点不可行

证明：

Phase-I 的目标是最小化未被真实 route columns 覆盖的任务总人工量。如果 exact pricing 已经证明不存在能够改善 Phase-I objective 的负 reduced-cost route，而 Phase-I 最优值仍大于 0，则完整 Phase-I master 中也无法用真实 route columns 覆盖全部任务。

因此，在当前 branching/cut 条件下，不存在满足所有任务覆盖的 route-vehicle 解，该节点不可行。

证毕。

## 7. Branching 的完整性

当前 clean BPC 使用以下分支：

```text
Ryan-Foster
task-vehicle
arc-usage
vehicle-use
```

### 7.1 Ryan-Foster branching

对任务对 `(i,j)`：

```text
left:  i and j are not in the same route
right: i and j are in the same route
```

任意整数 route solution 中，任务 `i,j` 要么在同一 route，要么不在同一 route。因此左右子节点互斥且覆盖父节点整数解空间。

pricing 传播：

```text
separate: 禁止同时包含 i,j 的 route
together: 禁止只包含 i 或只包含 j 的 route
```

### 7.2 Task-vehicle branching

对任务 `i` 和车辆 `r`：

```text
left:  vehicle r does not serve task i
right: vehicle r serves task i
```

任意整数解中，任务 `i` 由唯一车辆服务。因此对固定车辆 `r`，该命题非真即假，左右子节点互斥且覆盖父节点整数解空间。

pricing 传播：

```text
off: 禁止车辆 r 生成含 i 的 route
on:  禁止其他车辆生成含 i 的 route
```

### 7.3 Arc-usage branching

对任务弧 `(i,j)`：

```text
left:  no selected route uses direct arc i -> j
right: at least one selected route uses direct arc i -> j
```

任意整数解中，弧 `i -> j` 在被选 route 中出现次数是整数。若分数 LP 解中该弧使用量非整数，则可用：

```text
left:  arc usage = 0
right: arc usage >= 1
```

作为二分。左右子节点互斥，并覆盖父节点整数解空间。

pricing 传播：

```text
arc_off: 禁止生成包含直接弧 i -> j 的 route
arc_on:  RMP 加入 sum q[i,j,p] lambda[p,r] >= 1
```

对 `arc_on`，该分支约束的 dual `delta` 必须进入 reduced cost：

```text
rc[p,r] := rc[p,r] - q[i,j,p] delta
```

当前实现满足这一点。

### 7.4 Vehicle-use branching

对车辆 `r`：

```text
left:  y[r] = 0
right: y[r] = 1
```

任意整数解中 `y[r]` 是 0/1，因此左右子节点互斥且覆盖父节点整数解空间。

pricing 传播：

```text
y[r]=0: 禁止车辆 r 生成 route
y[r]=1: RMP 固定 y[r] 下界为 1
```

### 引理 7：当前 branching 不删除任何父节点整数可行解

证明：

上述每类分支都是某个整数命题的真假二分。任意父节点整数可行解必然满足左支或右支之一，且不能同时满足两者。因此分支集合覆盖父节点整数解空间且互斥。

证毕。

## 8. Incumbent 的正确性

当前算法只有在以下条件同时满足时才更新 incumbent：

```text
1. RMP solution 在 lambda/y 上为整数；
2. 每个任务被覆盖一次；
3. 每辆车选中的 route 集合通过 exact schedule checker；
4. route 内部资源可行；
5. objective 按原问题成本计算。
```

Primal heuristic 也必须经过同样 schedule feasibility 检查后才允许更新 incumbent。当前 `restricted_integer_master` 是受限列池上的 binary MIP heuristic：它可以在临时 MIP 中先加入双向不可排程的 route-pair cut，再尝试 schedule-capacity cut，最后才退回排程 no-good 来继续寻找更好的候选。这些临时约束不提供节点 lower bound，也不替代主树中的 exact pricing 或正式 schedule cut separation。RIM 发现的强 witness cut 若回流到主树，则作为正式 valid schedule cut 使用；弱 no-good 只有在当前 LP 解违反时才提升为正式 cut。新增正式 cut 后，当前节点必须重新求解，不能继续使用旧 LP 解做分支或剪枝。

### 引理 8：任意被接受的 incumbent 都是原问题可行解

证明：

整数 RMP 解保证任务覆盖和 route 选择为 0/1。每条 route 在生成时已经满足单 sortie 的时间窗、载重、电量。schedule checker 又验证每辆车所选 route 集合存在真实执行顺序，并满足车辆 horizon。因此该解满足原问题全部约束。

证毕。

## 9. Node bound 的正确性

在一个 BPC 节点中，只有当以下流程完成后，节点 lower bound 才有效：

```text
1. Phase-I 若需要，则 exact pricing 完整结束；
2. Phase-II RMP LP 求解到最优；
3. exact pricing 使用 true dual、cut dual、branch dual 完整结束；
4. 如果 LP 解整数，则完成 schedule separation：
   - 可排程：更新 incumbent；
   - 不可排程：加 schedule cut 并重新求解，不使用旧 bound 终止；
5. 当前没有新的 violated schedule cut 需要加入。
```

如果时间限制在上述流程完成前触发，该节点没有已认证 lower bound。算法必须返回 `TIME_LIMIT`，不能把最后一次 RMP LP objective 当成节点证明。

### 引理 9：已认证节点 lower bound 是该节点所有原问题可行整数解的下界

证明：

由引理 5，exact pricing 结束后，RMP LP value 等于当前节点完整 route-vehicle master LP value。LP relaxation 的最优值不大于该节点任意整数 route-vehicle solution 的目标值。

由引理 3，已加入的 schedule cuts 不排除原问题可行解。由 branching 完整性，当前节点内的原问题可行整数解都在该节点 master 可行域内。因此该 LP value 是当前节点所有原问题可行整数解的下界。

证毕。

## 10. 全局最优性证明

BPC 树维护：

```text
UB = 当前最佳原问题可行 incumbent
LB = 所有 open nodes 已认证 lower bound 的最小值
```

如果 open nodes 为空，则所有节点都已被以下原因处理：

```text
infeasible
bound >= UB
integral and feasible
branched into children
```

### 定理：若算法有限结束且 open nodes 为空，则 incumbent 是原问题全局最优解

证明：

由引理 8，incumbent 是原问题可行解，因此其目标值 `UB` 是有效上界。

每个被 bound 剪枝的节点都有已认证 lower bound，且该 lower bound 不小于 `UB`，所以该节点不可能包含优于 incumbent 的原问题可行解。

每个 infeasible 节点由 Phase-I exact pricing 证明无可行 route-vehicle 解，因此不包含原问题可行解。

每个 integral feasible 节点的解已经用于更新或比较 incumbent。

branching 由引理 7 保证不遗漏父节点整数可行解。由于 open nodes 为空，整个根节点整数解空间已经被完整处理。因此不存在目标值小于 `UB` 的原问题可行解。

故 incumbent 为原问题全局最优解。

证毕。

## 11. 带时间限制时的证书

如果算法因 time limit、node limit 或 pricing incomplete 停止，则不能声明最优。此时：

```text
UB = 当前 incumbent objective，若存在；
LB = open nodes 中已认证 lower bound 的最小值，若所有 open nodes bound 都有效；
gap = (UB - LB) / |UB|
```

如果 pricing incomplete 或某节点 bound 未认证，则该节点不能用于全局 LB。实现上必须避免输出虚假的 dual bound。

当前 clean BPC 的原则是：

```text
pricing incomplete => 不声明节点完成，不使用该节点 bound 证明最优
```

## 12. 当前实现仍需满足的工程条件

上面的证明依赖以下实现条件：

```text
1. exact_pricing 必须枚举所有满足 branch/cut 逻辑的资源可行 route，或有严格证明的 dominance。
2. reduced_cost 必须包含 cover、sortie_count、vehicle_time、schedule cut、branching dual。
3. schedule checker 必须是 exact checker，不能用启发式近似判断不可排程。
4. no-good cut 只能基于已证明不可排程的 route 集合生成。
5. branching 左右子节点必须同时创建，不能被 ML 或 heuristic 删除。
6. incumbent 必须通过原问题可行性检查。
7. 若使用 heuristic pricing、selective pricing、ML ranking、time budget，必须保留 exact fallback；否则不能证明无负 reduced-cost column。
```

## 13. 当前框架与 vehicle-schedule BPC 的关系

vehicle-schedule BPC 的 column 是一辆车完整 schedule：

```text
K = (route_1, route_2, ..., route_m)
```

每个 column 天生满足同车多 sortie 的真实时间顺序。因此 vehicle-schedule master 更天然地等价于原问题。

当前 route-vehicle BPC 的 column 是单条 route：

```text
p = route
```

它需要 schedule cuts 才能排除不可排程的 route 组合。因此：

```text
route-vehicle master 本身不是原问题等价模型；
route-vehicle master + 完整 schedule cut separation 才能达到等价。
```

这也是当前算法可能慢的根本原因之一：LP relaxation 比 vehicle-schedule master 弱，且需要通过 cuts 逐步修补 schedule 维度。

## 14. 总结

当前 clean BPC 的最优性可以概括为：

```text
1. route-vehicle master 是原问题松弛；
2. schedule no-good cuts valid，不删除原问题可行解；
3. exact pricing 完成后，RMP LP 是当前节点完整 master LP；
4. branching 覆盖且互斥，不遗漏整数解；
5. incumbent 只接受原问题可行解；
6. 所有节点被正确处理后，UB=LB 时得到全局最优证明。
```

因此，当前框架可以是 exact BPC，但前提是：

```text
schedule separation 完整；
exact pricing 完整；
branching 完整；
node bound 只在完整定价和切割后使用。
```
