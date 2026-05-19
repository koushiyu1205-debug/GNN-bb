# 当前 Clean BPC 完整模型说明

生成时间：2026-05-12 14:29:32 CST +0800

对应代码主线：

```text
bpc/
scripts/run_bpc_clean.py
configs/bpc_clean.yaml
```

本文档描述当前根目录 `bpc/` 下的完整数学模型、pricing、cuts、branching 和求解流程。它记录的是当前实现状态，不描述旧 `src/gnn_bb/bp/` 实验代码，也不描述 `model/scip-version`。

## 1. 模型定位

当前实现是：

```text
route-vehicle Branch-Price-and-Cut with schedule cuts
```

它不是：

```text
vehicle-schedule Branch-Price-and-Cut
```

两者区别：

- 当前 master column 是一条单独 sortie route；
- vehicle-schedule master column 是一辆车完整的多 sortie 日程；
- 当前 master 不直接枚举“同一辆车的多条 sortie 先后顺序”；
- 多 sortie 的真实时间顺序由 exact schedule checker、schedule no-good cuts 和 schedule capacity cuts 处理。

因此，当前 route-vehicle master 是原问题的一个 Dantzig-Wolfe 表达框架，但如果不加 schedule cuts，它对“同一车辆多条 sortie 的先后可排程性”是松弛的。当前算法通过 valid schedule cuts 排除不可排程的整数 route 组合，并且只有通过原问题可行性检查的解才能作为 incumbent。

## 2. 原问题

任务集合：

```text
I = {1, ..., n}
```

车辆集合：

```text
R = {1, ..., m}
```

depot 记为 `0`。

任务 `i` 的参数：

```text
r_i        最早开始时间
D_i        最晚完成时间
sigma_i    服务时间
d_i        载重需求
g_i        服务能耗
c_i^srv    服务成本
```

弧 `(i,j)` 的参数：

```text
tau_ij      旅行时间
e_ij        旅行能耗
c_ij        旅行成本
```

车辆和资源参数：

```text
Q       单条 sortie 载重上界
B       单条 sortie 电量上界
H       单车总工作 horizon
S_bar   单车最多 sortie 数
F       固定启用车辆成本
rho     能量恢复/充电速率，用于工作时间下界
```

原问题要求：

- 每个任务恰好服务一次；
- 每条 sortie 从 depot 出发并回到 depot；
- 单条 sortie 内满足时间窗、载重、电量、任务不重复；
- 同一辆车执行的多条 sortie 必须能排成真实时间顺序；
- 每辆车最多执行 `S_bar` 条 sortie；
- 每辆车总工作时间不超过 `H`；
- 最小化固定车辆成本、旅行成本和服务成本。

## 3. Route Column

一个 route column `p` 是一条资源可行 sortie：

```text
p = (0, i_1, i_2, ..., i_q, 0)
```

route 内部必须满足：

```text
start_i >= r_i
finish_i <= D_i
sum_i d_i <= Q
route_energy <= B
return_time <= H
任务不重复
```

route 参数：

```text
a_ip = 1 如果 route p 服务任务 i，否则 0
c_p  = route p 的旅行成本 + 服务成本
w_p  = route p 的车辆工作时间下界
```

当前实现中：

```text
w_p = travel_time_p + service_time_p + energy_p / rho
```

注意：`w_p` 是下界，不包含不同 sortie 之间的等待时间。等待和多 sortie 顺序由 schedule checker 处理。

### 3.1 Route Duplicate Suppression

当前 route duplicate suppression 是强签名查重，不依赖 Python object id。

代码中：

```text
RouteColumn.signature = RouteColumn.tasks
```

即 route signature 是有序任务序列：

```text
signature(p) = (i_1, i_2, ..., i_q)
```

`RoutePool` 使用：

```text
by_signature: dict[tuple[int, ...], RouteColumn]
```

因此，同一个有序任务序列即使被多次生成、对应不同临时对象，也只会保留第一条 canonical route。RMP、pricing duplicate suppression、schedule no-good cuts 都使用该 `signature`。

这意味着当前实现中：

```text
同一路径不同对象 ID 不会绕过 route-signature 类 cuts。
```

但这里的“同一路径”严格指同一个有序任务序列。在当前数据结构中，任务对之间的物理弧由 `data.arc(i,j)` 唯一给定，所以同一任务序列唯一决定 route 的资源消耗和成本。

当前不会合并不同任务顺序：

```text
(1,2,3) 和 (1,3,2)
```

它们是两条不同 route，因为时间窗、能耗、成本和 schedule 行为都可能不同。

需要注意的边界：如果未来引入同一任务序列的多条物理路径、不同速度档、不同充电策略或其他 route 变体，那么当前 `tasks` signature 就不够强，必须扩展为：

```text
signature = (task sequence, physical path ids, resource mode ids, charging policy ids, ...)
```

否则会把本应不同的 columns 错误合并。

## 4. Master Variables

主问题变量：

```text
lambda_pr >= 0
```

表示车辆 `r` 选择 route `p` 的 LP 松弛变量。整数可行解中应为 0/1。

```text
0 <= y_r <= 1
```

表示车辆 `r` 是否启用的 LP 松弛变量。整数可行解中应为 0/1。

Phase-I 人工变量：

```text
u_i >= 0
```

用于任务覆盖。

对 cut 约束，Phase-I 还会加入 cut artificial variables，保证加 cut 后 RMP 仍能进入 Phase-I 可行性恢复。

## 5. Phase-I RMP

Phase-I 目标：

```text
min  sum_i u_i + sum_g s_g
```

其中 `s_g` 是 cut artificial variable。

约束：

```text
sum_r sum_p a_ip lambda_pr + u_i = 1
    for all i in I
```

如果开启 task-vehicle linking，加入：

```text
sum_p a_ip lambda_pr <= y_r
    for all i in I, r in R
```

车辆 sortie 数：

```text
sum_p lambda_pr <= S_bar y_r
    for all r in R
```

车辆工作时间下界：

```text
sum_p w_p lambda_pr <= H y_r
    for all r in R
```

车辆顺序对称破除：

```text
y_{r+1} <= y_r
```

通用 cut 行：

```text
sum_{p,r} b_gpr lambda_pr + sum_r h_gr y_r <= rhs_g
```

或：

```text
sum_{p,r} b_gpr lambda_pr + sum_r h_gr y_r >= rhs_g
```

Phase-I 对 `<=` cut 使用：

```text
lhs - s_g <= rhs_g
```

对 `>=` cut 使用：

```text
lhs + s_g >= rhs_g
```

只有当 Phase-I 完整 exact pricing 后仍有人工变量为正，该节点才能被判定不可行。

## 6. Phase-II RMP

Phase-II 目标：

```text
min  sum_r F y_r + sum_r sum_p c_p lambda_pr
```

任务覆盖：

```text
sum_r sum_p a_ip lambda_pr = 1
    for all i in I
```

task-vehicle linking，默认开启：

```text
sum_p a_ip lambda_pr <= y_r
    for all i in I, r in R
```

车辆 sortie 数：

```text
sum_p lambda_pr <= S_bar y_r
    for all r in R
```

车辆工作时间下界：

```text
sum_p w_p lambda_pr <= H y_r
    for all r in R
```

车辆顺序：

```text
y_{r+1} <= y_r
```

cuts：

```text
sum_{p,r} b_gpr lambda_pr + sum_r h_gr y_r <= rhs_g
```

或：

```text
sum_{p,r} b_gpr lambda_pr + sum_r h_gr y_r >= rhs_g
```

branching constraints：

- 大部分结构分支直接传给 pricing 过滤 route；
- `arc_on` 会在 RMP 中生成一条显式约束；
- `vehicle_on/off` 通过 `y_r` bounds 固定。

## 7. Reduced Cost

对偶变量：

```text
pi_i       任务覆盖约束 dual
xi_ir      task-vehicle linking dual
eta_r      sortie count dual
beta_r     vehicle time dual
gamma_g    cut dual
delta_h    branching row dual
```

cut 系数：

```text
b_gpr      route p on vehicle r 在 cut g 中的 lambda 系数
h_gr       cut g 中 y_r 的系数
```

注意：`h_gr y_r` 影响 RMP 中 `y_r` 的 reduced cost，但 pricing 只生成 `lambda_pr`，因此 route pricing 只使用 `b_gpr`。

branching row 系数：

```text
q_hpr      route p on vehicle r 在 branching row h 中的系数
```

Phase-II route reduced cost：

```text
rc_pr =
    c_p
  - sum_i a_ip pi_i
  - sum_i a_ip xi_ir
  - eta_r
  - beta_r w_p
  - sum_g gamma_g b_gpr
  - sum_h delta_h q_hpr
```

Phase-I route reduced cost：

```text
rc_pr^I =
    0
  - sum_i a_ip pi_i
  - sum_i a_ip xi_ir
  - eta_r
  - beta_r w_p
  - sum_g gamma_g b_gpr
  - sum_h delta_h q_hpr
```

如果 `task_vehicle_linking_enabled=false`，则没有 `xi_ir` dual，该项为空。

当且仅当 exact pricing 在 true dual 下完整证明不存在：

```text
rc_pr < -epsilon
```

当前 RMP LP 才是该节点的完整 master LP relaxation。

## 8. Exact RCSP Pricing

当前 pricing 在 `bpc/pricing.py` 中实现。它是按车辆 `r` 运行的 exact elementary RCSP labeling。

label 状态：

```text
(current_node, sequence, visited_mask, time, load, energy, travel_time, cost, service_time, task_dual_sum)
```

扩展任务 `j` 时检查：

```text
j not in sequence
time window feasible
load + d_j <= Q
energy + e_ij + g_j <= B
return to depot feasible
return_time <= H
branching partial sequence feasible
```

每个可行前缀都可以形成一个完整 route：

```text
0 -> sequence -> 0
```

若该 route 的 reduced cost 为负，则加入候选列。

当前 exactness 规则：

- `max_labels_per_pricing = 0` 表示不设 label 上限；
- 若设置正数且 pricing 未 exhausted，则不能用该节点 bound 做证明；
- clean 主线默认 exact pricing，不使用 heuristic pricing 证明无负 reduced-cost 列。

当前性能实现：

- exact pricing 仍逐车辆完整枚举所有满足资源、时间窗和 branching filter 的 elementary sequence；
- label 扩展时增量维护 route cost、travel time、energy、service time、visited bitmask 和任务 dual 贡献；
- reduced cost 使用这些增量状态直接计算，cut dual 和 branch dual 仍逐 route 计入；
- 只有当 route 的 reduced cost 为负时，才调用 `evaluate_route()` 构造完整 `RouteColumn` 并用公共 `reduced_cost()` 公式复核；
- 因此该优化只减少重复 route 重建和字典查询，不改变 pricing 可行域、不改变节点证书条件。

## 9. Cut Families

### 9.1 Schedule No-Good Cut

若某个整数 RMP 解中，车辆 `r` 选择的 route 集合 `C` 被 exact schedule checker 证明不可排程，则对每辆同质车辆 `r'` 加：

```text
sum_{p in C} lambda_{p,r'} <= |C| - 1
```

系数：

```text
b_gpr = 1 如果 route p 的 signature 属于 C 且 vehicle=r'
b_gpr = 0 否则
```

有效性：该 route 集合在任意同质车辆上都无法形成真实 schedule，因此不能同时被同一辆车选择。

### 9.2 统一 Crossing Cut

当前实现把 Robust Rounded Capacity Inequality 和 k-path/resource lower bound cut 合并为同一个 cut family。对任务子集 `S`，定义：

```text
Kcap(S)      = ceil(d(S)/Q)
Kresource(S) = chi(G_S)
K(S)         = max(Kcap(S), Kresource(S))
```

其中 `G_S` 是资源不兼容图。若两个任务不可能出现在同一条资源可行 sortie route 中，则在图中连边。`chi(G_S)` 是该图的色数下界。

cut：

```text
sum_{p,r} crossing(p,S) lambda_pr >= 2 K(S)
```

其中 `crossing(p,S)` 是 route `p` 从 `S` 到 `I\S` 或反向穿越的次数，包括 depot 边。

有效性：

- `Kcap(S)` 是容量约束给出的最少 route 数下界；
- `Kresource(S)` 是资源不兼容图 exact coloring 给出的最少 route 数下界；
- 覆盖 `S` 至少需要 `K(S)` 条 route；
- 每条服务 `S` 中任务的 route 从 depot 出发并回 depot，因此至少贡献 2 次 crossing；
- 所以上述 crossing cut 对所有原问题整数可行解有效。

这是 robust cut，因为 pricing 只需要给每条 route 计算一个 crossing coefficient，不需要改变 RCSP 状态空间。

当前 cut manager 使用 key：

```text
("crossing_cut", frozenset(S))
```

如果同一个 `S` 已经有 crossing cut，只保留 RHS 最大的一条。若后续发现更大的 `K(S)` 且当前 LP 违反更强 cut，则替换旧 cut，不保留重叠的 RCI/k-path 两条 cut。

### 9.3 Schedule No-Good Core Cut

若整数 assignment 中某辆车的 route 集合 `C` 不可排程，则对 `shrink_infeasible_route_set` 返回的 deletion-minimal core `C'` 加：

```text
sum_{p in C'} lambda_pr <= |C'| - 1
```

当前实现直接生成 core no-good cut。若 core cut 已存在，则最后尝试 full route set no-good；若仍无法新增 cut，则不能把该节点当作 integral feasible fathom。

### 9.4 Schedule Capacity Upper-Bound Cut

定义：

```text
z_ir = sum_p a_ip lambda_pr
```

对任务子集 `S` 和车辆 `r`：

```text
sum_{i in S} z_ir <= U(S) y_r
```

等价写成 RMP row：

```text
sum_p (sum_{i in S} a_ip) lambda_pr - U(S) y_r <= 0
```

其中 `U(S)` 是一辆真实车辆在完整多 sortie schedule 中最多能服务 `S` 内多少个任务。

当前实现用 exact schedule task-capacity oracle 计算 `U(S)`。如果 oracle 超过状态上限或无法证明，则跳过，不加 cut。

有效性：

- 若 `y_r=0`，车辆 `r` 不能服务任务；
- 若 `y_r=1`，左侧表示车辆 `r` 服务 `S` 中任务数量，按 `U(S)` 定义不能超过该上界；
- 因此该 cut 不删除任何原问题整数可行解。

## 10. Cut Purging

当前实现只清洗 inactive capacity 类 cuts：

```text
CrossingCut
ScheduleCapacityCut
```

不清洗 schedule no-good cuts。

清洗规则：

- cut slack 大于阈值；
- cut dual 绝对值小于阈值；
- 连续 inactive age 达到配置上限。

清洗只删除当前 RMP 中长期休眠的 valid cuts，不影响模型正确性。删除 cut 可能放松 LP，但不会删除可行解，也不会使 incumbent 失效。

## 11. Branching

当前 branching 候选来自 `bpc/branching.py`。

### 11.1 Ryan-Foster Branching

对 fractional pair value：

```text
v_ij = sum_{p,r: i,j both in p} lambda_pr
```

若：

```text
0 < v_ij < 1
```

生成两个子节点：

```text
same(i,j):      i 和 j 必须同 route
separate(i,j):  i 和 j 不能同 route
```

pricing 处理：

- `same(i,j)` 禁止只含 `i` 或只含 `j` 的 route；
- `separate(i,j)` 禁止同时含 `i,j` 的 route。

### 11.2 Task-Vehicle Branching

对 fractional assignment：

```text
z_ir = sum_p a_ip lambda_pr
```

若：

```text
0 < z_ir < 1
```

生成：

```text
task_vehicle(i,r)=on
task_vehicle(i,r)=off
```

pricing 处理：

- `on`：含任务 `i` 的 route 只能由车辆 `r` 生成；
- `off`：车辆 `r` 不能生成含任务 `i` 的 route。

### 11.3 Arc Branching

对 fractional arc usage：

```text
v_ij = sum_{p,r: route p uses arc i->j} lambda_pr
```

生成：

```text
arc(i,j)=off
arc(i,j)=on
```

pricing 处理：

- `off`：禁止生成使用该任务弧的 route；
- `on`：RMP 加 row，pricing reduced cost 中加入该 row dual。

`arc_on` 的当前代数形式是：

```text
sum_{p,r} q_{ij,p} lambda_pr >= 1
```

其中：

```text
q_{ij,p} = 1  如果 route p 的任务序列中存在连续弧 i -> j
q_{ij,p} = 0  否则
```

当前 `arc_on` 不是纯过滤规则。原因是 `arc_on` 表示整数解中至少选一条使用该弧的 route，而不是要求所有后续 generated routes 都必须使用该弧。因此 pricing 仍然必须生成两类 route：

```text
q_{ij,p}=0 的 route
q_{ij,p}=1 的 route
```

然后由 RMP row 和 dual 调整 reduced cost。

若该 row 的 dual 为 `delta_ij`，则 pricing 中加入：

```text
rc_pr <- rc_pr - delta_ij q_{ij,p}
```

当前 exact pricing 的实现方式是：

```text
1. labeling 枚举完整 route sequence；
2. route 完成后计算 q_{ij,p}；
3. reduced cost 中扣除 arc_on row dual；
4. 若 rc < -epsilon，则加入列。
```

当前 pricing 没有 label dominance，因此不需要在 label state 中额外携带“是否已经使用 arc(i,j)”这一位也能保持 exactness。完整枚举会覆盖 `q=0` 和 `q=1` 的所有 route。

但如果后续加入 dominance 或更强剪枝，则必须重新处理 `arc_on`：

```text
label state 需要携带每个 active arc_on 是否已被使用；
或 dominance 必须只在相同 active-arc usage mask 下比较。
```

否则一个尚未使用 `arc_on` 的 label 可能错误支配已经使用该弧、因 dual reward 更有潜力的 label，从而漏掉负 reduced-cost column。

### 11.4 Vehicle-Use Branching

对 fractional `y_r`：

```text
0 < y_r < 1
```

生成：

```text
vehicle(r)=off
vehicle(r)=on
```

处理：

- `off`：RMP 中 `y_r=0`，pricing 不生成该车辆 route；
- `on`：RMP 中 `y_r=1`。

当前实现已避免 route-signature fallback 作为主线分支。route-signature 分支虽然能切割当前列，但不是结构化 VRP 分支，不利于 pricing 和后续 2LBB。

## 12. 3PB Branching Baseline

当前 no-ML branching strategy 是 3PB：

### 第一阶段：initial screening

将候选分成：

- 有 pseudocost 记录；
- 无 pseudocost 记录。

选择：

```text
有 pseudocost: 按 pseudocost score 取 top theta_p
无 pseudocost: 按 fractionality 取 top theta_f
```

### 第二阶段：LP testing

对候选左右子节点分别解 restricted child RMP LP：

```text
不做 column generation
不做 exact pricing
```

计算左右 bound improvement，并得到 LP score。

### 第三阶段：heuristic CG testing

对 LP score top 候选做有限轮 heuristic CG testing：

```text
固定 heuristic iterations
固定每轮 routes limit
固定 max_labels
```

该 testing 只用于选择 branching candidate，不用于证明节点 bound，也不用于剪枝。

最终选择 heuristic score 最好的候选。所有测试统计写入日志和 CSV：

```text
branch_lp_test_rmp_solves
branch_heuristic_test_rmp_solves
branch_heuristic_test_pricing_calls
branch_lp_candidates_tested
branch_heuristic_candidates_tested
branch_testing_time
```

## 13. Incumbent 与 Feasibility Check

当前 incumbent 来源：

1. `greedy_schedule`
   - 初始化阶段构造 schedule-feasible 解；
   - 只用于 upper bound。

2. `certified_integral`
   - 当前 RMP integer solution 对应的 route-vehicle assignment 本身 schedule feasible；
   - 可直接作为 incumbent。

3. `route_assignment_repair`
   - 当前 RMP integer solution 选出的 route 集合可能按原车辆分配不可排程；
   - 因车辆同质，尝试将这些 route 重新分配到车辆上；
   - 每次候选都用 exact schedule checker；
   - 若找到可排程 assignment，则作为真实原问题 incumbent。

4. `restricted_integer_master`
   - 在当前 route pool 上解 binary restricted master；
   - 该 MIP 只作为 primal heuristic，不参与 lower bound 证明；
   - 每次得到整数 assignment 后立即运行 exact schedule checker；
   - 如果某辆车的 route 集合不可排程，就提取不可排程 core，并在该临时 MIP 中对所有同质车辆加入 no-good 约束后继续求解；
   - RIM 中发现的不可排程 core 是有效 cut，会回流成主树正式 `schedule_nogood_core` cut；一旦新增正式 cut，当前节点必须重新求解；
   - RIM 使用线性 objective cutoff 过滤不可能改进当前 incumbent 的候选，但不使用 solver objlimit；
   - 只有排程可行且通过 `_set_incumbent_from_assignment` 的解才允许更新 incumbent。

`route_assignment_repair` 和 `restricted_integer_master` 都只改善 primal bound，不影响 dual bound 或节点证明。即使 heuristic 找到 incumbent，若当前节点原 assignment 不可排程，算法仍会加 schedule no-good cut，而不会错误 fathom。

节点 lower bound 只有在当前节点完成 Phase-II RMP、exact pricing certificate 和所有启用 cut separation 后才被标记为已认证。若时间限制在证书完成前触发，不能使用最后一次 RMP LP 作为节点 bound，整体求解状态必须是 `TIME_LIMIT`。

### 13.1 Schedule Checker 当前返回的信息

当前 schedule checker 的返回对象是：

```text
ScheduleCheckResult(
    feasible: bool,
    order: tuple[int, ...],
    ready_time: float | None,
)
```

含义：

- 若可行，`order` 是 route 列表索引的一个可行执行顺序；
- 若可行，`ready_time` 是完成该车辆 route 集合后的最早 ready time；
- 若不可行，当前只返回 `feasible=False, order=(), ready_time=None`。

也就是说，当前 checker 不返回以下失败见证：

```text
不可行时间区间
哪两个 route 双向顺序都不可能
DP 失败状态集合
minimal infeasible subset 的证明树
pairwise conflict graph
```

当前 minimal infeasible subset 由：

```text
shrink_infeasible_route_set
```

做贪心删除得到。它的性质是：

```text
删除到没有单条 route 可以继续去掉且仍保持不可行
```

这是一个 order-dependent 的 deletion-minimal core，不是全局最小 cardinality core，也不是 IIS 证书。

因此当前可以安全加入 schedule no-good cut，因为完整 checker 已经证明整个 route 集合不可排程；但当前还不具备高质量 pairwise clique separation 所需的见证信息。

如果后续要做 pairwise clique / interval conflict cuts，应该先增强 schedule checker，使其至少能输出：

```text
1. route-pair compatibility matrix:
   route a before b feasible?
   route b before a feasible?

2. DP failure witness:
   对每个 partial subset 的最早 ready time；
   哪些扩展因时间窗、horizon、能量恢复失败；

3. deletion-minimal core with certificate:
   每条 route 被保留的原因；
   任意删除一条后是否可行的检查结果。
```

在这些 witness 没有实现前，不应添加依赖 pairwise infeasibility 结构的强 cut。当前 no-good cut 是安全但偏弱的保守选择。

## 14. BPC 节点流程

每个节点流程：

```text
load branch constraints

repeat:
    solve Phase-I or Phase-II RMP LP

    if RMP infeasible:
        fathom node

    if Phase-I artificial sum == 0:
        switch to Phase-II
        continue

    exact pricing under true dual

    if negative reduced-cost columns found:
        add columns
        continue

    if pricing not exhausted:
        abort proof for this run

    if Phase-I still has artificial:
        fathom infeasible

    separate unified crossing cuts
    if cuts added: continue

    separate schedule capacity cuts
    if cuts added: continue

    break

set node lower bound

if bound >= incumbent:
    fathom by bound

if LP solution integral:
    validate schedule feasibility
    if feasible:
        update incumbent
        fathom integral
    else:
        add schedule no-good cut
        reprocess node

choose branching candidate by 3PB
create child nodes
```

## 15. Exactness 条件

当前 clean BPC 保持精确性的条件：

1. RMP 初始可行由 Phase-I 人工变量处理。
2. `0 <= y_r <= 1`，车辆启用变量是二进制变量的 LP 松弛。
3. task-vehicle linking 是原问题整数可行解满足的 valid inequality。
4. reduced cost 与 RMP dual 完全一致。
5. exact pricing 使用 true dual、branching constraints、cut duals。
6. heuristic testing 只影响 branching candidate 选择，不用于剪枝或证明。
7. cuts 只在数学上 valid 且当前 LP 违反时加入。
8. node lower bound 只在 full pricing 和 cut separation 完成后使用。
9. integer incumbent 必须通过 exact schedule feasibility check。
10. pricing 中断或 label budget 未 exhausted 时，不能证明该节点完成。

### 15.1 Reduced-Cost 一致性测试

当前测试集中加入了 reduced-cost consistency audit：

```text
tests/test_bpc_clean.py::test_existing_lambda_reduced_cost_matches_solver
```

测试逻辑：

```text
1. 构造一个 very_small RMP；
2. RMP 中包含已有 lambda[p,r]；
3. 同时包含会影响 lambda 的 row：
   - cover row
   - task-vehicle linking row
   - sortie count row
   - vehicle time row
   - schedule-capacity cut row
   - arc_on branching row
4. 从 SCIP 读取每个已有 lambda[p,r] 的 solver reduced cost；
5. 用 bpc/pricing.py::reduced_cost 手算同一 lambda[p,r] 的 reduced cost；
6. 要求两者误差 <= 1e-6。
```

这条测试直接保护以下原则：

```text
RMP 里每一条会影响 lambda[p,r] 的 row，其 dual 都必须进入 pricing reduced cost。
```

如果后续新增任何含 `lambda[p,r]` 的 row，但没有在 pricing 里加入对应 coefficient 和 dual，该测试应被扩展并失败。

## 16. 当前可配置项

核心配置在：

```text
configs/bpc_clean.yaml
```

重要开关：

```yaml
branching_strategy: 3pb

task_vehicle_linking_enabled: true

robust_capacity_cuts_enabled: true
resource_lower_bound_cuts_enabled: true
schedule_capacity_cuts_enabled: true

max_labels_per_pricing: 0
max_routes_per_pricing: 200
```

消融配置：

```text
configs/bpc_ablation.yaml
scripts/run_bpc_ablation.py
```

默认四组：

```text
no_link_no_schedcap
link_only
schedcap_only
link_schedcap
```

## 17. 当前模型的局限

当前模型仍有以下局限：

1. route-vehicle master 的 root relaxation 仍弱于 vehicle-schedule master。
2. schedule no-good cuts 可能很多，且通常只在整数候选解处触发。
3. robust capacity cut 和 k-path/resource cut 在当前 20 规模实例上经常不触发。
4. schedule capacity cut 能找到少量 violated cuts，但不一定显著提升 root bound。
5. 3PB 的 branching testing 时间很大，是当前主要性能瓶颈。
6. 当前还没有 2LBB；ML 还没有参与候选排序或测试预算控制。

## 18. 运行命令

20 规模当前主线：

```bash
cd /home/kai/work/gnn_bb
RUN_ID="$(date +%Y%m%d_%H%M%S)_medium_clean_bpc_current_3600"
mkdir -p results/logs/bpc_clean_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --config configs/bpc_clean.yaml \
  --instances medium \
  --time-limit 3600 \
  --results-csv "results/${RUN_ID}.csv" \
  --log-dir "results/logs/${RUN_ID}" \
  --solution-dir "results/solutions/${RUN_ID}" \
  2>&1 | tee "results/logs/bpc_clean_terminal/${RUN_ID}_terminal.log"
```

20 规模 linking / schedule-cap 消融：

```bash
cd /home/kai/work/gnn_bb
RUN_ID="$(date +%Y%m%d_%H%M%S)_medium_link_schedcap_ablation_3600"
mkdir -p results/logs/bpc_ablation_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_ablation.py \
  --config configs/bpc_ablation.yaml \
  --instances medium \
  --time-limit 3600 \
  --run-id "$RUN_ID" \
  2>&1 | tee "results/logs/bpc_ablation_terminal/${RUN_ID}_terminal.log"
```
