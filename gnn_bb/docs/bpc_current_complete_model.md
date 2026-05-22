# 当前 Clean BPC 完整模型说明

生成时间：2026-05-12 14:29:32 CST +0800

对应代码主线：

```text
bpc/
scripts/run_bpc_clean.py
configs/bpc_clean.yaml
```

本文档描述当前根目录 `bpc/` 下的完整数学模型、pricing、cuts、branching 和求解流程。它记录的是当前实现状态，不描述旧 `src/gnn_bb/bp/` 实验代码，也不描述 `model/scip-version`。

## 0. 2026-05-21 默认主线修正

当前 paper-grade baseline 已恢复为轻主线：默认关闭 `route_enumeration_enabled`、`schedule_pack_diagnostic_enabled`、`schedule_pack_relaxation_enabled`、`schedule_pack_full_pricing_enabled`、`schedule_pack_adaptive_enabled` 和 `route_enumeration_adaptive_enabled`。

2026-05-22 回退校正后，默认也关闭 `ng_dssr_pricing_enabled`、`exact_dssr_pricing_enabled` 和 `pricing_completion_bound_enabled`。原因是 `bench_20_01` 回归显示，ng/DSSR 会减少 root route pool 多样性，使 RIM 从 root 快速找到最优 incumbent 退化为多节点搜索。3PB 候选筛选恢复为原始 fractionality/key 排序，greedy incumbent 不做局部 relocate/重排改进，以贴近 356 秒版本：root route pool 约 `2481`、root RIM 快速 incumbent、`RF(7,10)` 分支。

原因是 20 节点测试显示，重 schedule-pack 在 `bench_20_02` 上能给出较高诊断 LP 值，但 full route-space pricing 没有完整结束，不能把诊断值转成正式 lower bound；在 `bench_20_01` 上还显著增加 route pool、RMP 规模和 exact pricing 次数。

后续默认主线只保留 exact route-vehicle BPC、subset-row、limited-memory rank-1、route-set schedule packing conflict、RIM schedule-aware incumbent 搜索和安全 pricing 加速。schedule-pack 与 near-zero route enumeration 保留为单独消融实验开关。

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
(current_node, sequence, visited_mask, crossing_counts, arc_on_mask,
 time, load, energy, travel_time, cost, service_time, task_dual_sum)
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
- clean 主线默认完整 exact pricing 负责证明；bounded-label heuristic pricing 只用于找列。
- 如果 bounded-label 调用自身 `exhausted=True`，说明 label 上限未触发，该轮已经完成完整枚举，可以作为 certificate。

当前性能实现：

- exact pricing 仍逐车辆完整枚举所有满足资源、时间窗和 branching filter 的 elementary sequence；
- label 扩展时增量维护 route cost、travel time、energy、service time、visited bitmask、任务 dual 贡献、active crossing cut 计数和 active `arc_on` 使用 mask；
- reduced cost 使用这些增量状态直接计算，cut dual 和 branch dual 仍逐 route 计入；
- 只有当 route 的 reduced cost 为负时，才调用 `evaluate_route()` 构造完整 `RouteColumn` 并用公共 `reduced_cost()` 公式复核；
- 因此该优化只减少重复 route 重建和字典查询，不改变 pricing 可行域、不改变节点证书条件。

当前安全 dominance：

- dominance key 是 `(visited_mask, current_node, crossing_counts, arc_on_mask, signature_prefix_mask)`；
- 比较维度是到达时间、载重、能耗和前缀 reduced-cost score；
- active crossing cut 的 prefix crossing 次数进入 key，最终回 depot 的 crossing 由相同 current node 保证一致；
- active `arc_on` row 的使用状态进入 `arc_on_mask`，避免尚未使用该弧的 label 错误支配已经获得 `arc_on` dual reward 的 label；
- schedule capacity cut 只依赖任务集合和车辆，已由 `visited_mask` 覆盖；
- `schedule_pair_conflict`、`schedule_nogood`、`schedule_nogood_core` 和 `schedule_nogood_full` 这类顺序签名 cut 的 active signature prefix mask 进入 key；只有两个 label 对后续可能命中的 active route signatures 完全相同，才允许互相支配。

分支节点增强启发式 pricing：

- 普通 heuristic pricing 使用 `heuristic_pricing_max_labels` 快速找列；
- 若分支节点深度达到 `branch_node_heuristic_boost_min_depth`，普通 heuristic 没有新增列且没有 exhausted，则再运行一次 `heuristic_boost`；
- `heuristic_boost` 使用更大的 `branch_node_heuristic_boost_max_labels` 和 `branch_node_heuristic_boost_routes_per_round`；
- boost 找到列后立即回到 RMP 重解；boost 未 exhausted 时仍必须继续完整 exact pricing；boost exhausted 时可作为 certificate。

## 9. Cut Families

### 9.1 Schedule No-Good Cut

若某个整数 RMP 解中，车辆 `r` 选择的 route 集合 `C` 被 exact schedule checker 证明不可排程，则对每辆同质车辆 `r'` 加：

```text
sum_{p in C} lambda_{p,r'} <= (|C| - 1)y_{r'}
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
sum_{p in C'} lambda_pr <= (|C'| - 1)y_r
```

当前实现不会立即生成 core no-good cut，而是先用 schedule checker 返回的 witness 寻找双向不可排程的 route pair。若存在 `p->q` 和 `q->p` 都不可行的 pair，则加入更小的 `schedule_pair_conflict` cut：

```text
lambda[p,r] + lambda[q,r] <= y[r]
```

若没有 pair witness，先尝试 route-set schedule packing conflict cut。此时优先对原始不可排程整数解中的 full route set `C` 调用 exact route-set schedule DP；只有证明同一辆车最多只能排 `U(C)<|C|-1` 条 route，才加入严格强于普通 no-good 的 cut：

```text
sum_{p in C} lambda_pr <= U(C) y_r
```

这是 no-good 的高阶形式；当 `U(C)=|C|-1` 时退化为普通 no-good，当前实现会跳过 route-pack 提升，因为它不会比 fallback no-good 更强。只有当 route-set DP 无法给出更紧上界时，才尝试 9.4 的结构性 schedule-capacity conflict cut。若仍无法证明任务集合 `S` 满足 `U(S)<|S|`，才回退到 core no-good cut。若 core cut 已存在，则最后尝试 full route set no-good；若仍无法新增 cut，则不能把该节点当作 integral feasible fathom。2026-05-21 回归后，LP 层 route-pack separator 默认关闭，因为它在 `bench_20_01` 上新增多条 cut 但 objective 不变；route-pack 代码保留为消融实验项。

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

Schedule capacity cut 有两个来源：

1. LP separation：从当前分数解的任务-车辆负载中生成候选集合 `S`，若当前 LP 违反上式则加入；
2. conflict-induced separation：当某辆车的整数 route 集合不可排程时，从该 route 集合的任务并集、route 组合并集和小规模任务组合中生成候选 `S`，若 exact oracle 证明 `U(S)<|S|`，则对所有同质车辆加入同一类 `schedule_capacity` cut。

第二类 cut 比 route-signature no-good 更结构化。它不是只排除当前几条 route，而是排除“同一车辆服务 `S` 中超过 `U(S)` 个任务”的所有 route 组合；同时它仍只依赖任务集合和车辆，pricing 不需要增加顺序签名状态，安全 dominance 也可以继续启用。

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

当前 pricing 已加入第一版安全 dominance，因此 label state 中会携带 active `arc_on` 使用 mask：

```text
arc_on_mask[h] = 1  如果当前前缀已经使用 branching row h 对应的任务弧
```

dominance 只在相同 `arc_on_mask` 下比较。完整 reduced cost 仍在 route 完成时扣除 `delta_ij q_{ij,p}`，并在负 reduced-cost 候选处用公共 `reduced_cost()` 公式复核。

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
   - 如果某辆车的 route 集合不可排程，先在该临时 MIP 中加入双向不可排程 pair cut；若没有 pair witness，再尝试临时 schedule-capacity cut；最后才退回临时 no-good；
   - RIM 中发现的强 witness cut 会回流成主树正式 cut；弱 no-good 只有在当前 LP 解确实违反时才提升为正式 cut，避免大量不抬升 bound 的全局 no-good 污染 pricing；
   - RIM 使用线性 objective cutoff 过滤不可能改进当前 incumbent 的候选，但不使用 solver objlimit；
   - 只有排程可行且通过 `_set_incumbent_from_assignment` 的解才允许更新 incumbent。

`route_assignment_repair` 和 `restricted_integer_master` 都只改善 primal bound，不影响 dual bound 或节点证明。即使 heuristic 找到 incumbent，若当前节点原 assignment 不可排程，算法仍会加 schedule no-good cut，而不会错误 fathom。

节点 lower bound 只有在当前节点完成 Phase-II RMP、exact pricing certificate 和所有启用 cut separation 后才被标记为已认证。若时间限制在证书完成前触发，不能使用最后一次 RMP LP 作为正式节点 bound，整体求解状态必须是 `TIME_LIMIT`。输出中额外保留 `diagnostic_dual_bound` 和 `diagnostic_gap`，用于实验分析：它们由已知 open node bound 和中断时的 pending node bound 计算，不替代正式 `dual_bound/gap`。

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
- 若不可行，基础返回仍是 `feasible=False, order=(), ready_time=None`。

不可行诊断由单独的：

```text
diagnose_route_set_schedule
```

生成。它会返回：

```text
ScheduleInfeasibilityWitness(
    routes: deletion-minimal core,
    pair_conflicts: tuple[RoutePairScheduleConflict, ...],
    reason: "pair_transition" 或 "set_order",
    deletion_minimal: bool,
)
```

其中 `RoutePairScheduleConflict` 记录两条 route 的签名和最早 ready time，并证明：

```text
p->q 不可行
q->p 不可行
```

因此当前可以安全加入 `schedule_pair_conflict`。若没有 pair witness，仍保留 `schedule_capacity` 与 `schedule_nogood_core` 回退。

当前 minimal infeasible subset 仍由：

```text
shrink_infeasible_route_set
```

做贪心删除得到。它的性质是：

```text
删除到没有单条 route 可以继续去掉且仍保持不可行
```

这是一个 order-dependent 的 deletion-minimal core，不是全局最小 cardinality core，也不是 IIS 证书。

后续如果要进一步做 pairwise clique / interval conflict cuts，还需要继续增强 witness：

```text
1. 完整 route-pair compatibility matrix；
2. DP failure witness:
   对每个 partial subset 的最早 ready time；
   哪些扩展因时间窗、horizon、能量恢复失败；
3. deletion-minimal core with certificate:
   每条 route 被保留的原因；
   任意删除一条后是否可行的检查结果。
```

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

    bounded-label heuristic pricing under true dual
    if negative reduced-cost columns found:
        add columns
        continue

    branch-node heuristic_boost pricing under true dual, if enabled
    if negative reduced-cost columns found:
        add columns
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
schedule_incompatibility_cuts_enabled: true
route_set_schedule_packing_cuts_enabled: true

max_labels_per_pricing: 0
max_routes_per_pricing: 500
root_max_routes_per_pricing: 1200
heuristic_pricing_enabled: true
heuristic_pricing_max_labels: 120000
branch_node_heuristic_boost_enabled: true
branch_node_heuristic_boost_max_labels: 900000
exact_pricing_dominance_enabled: true
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

1. route-vehicle master 的 root relaxation 仍弱于理论上的 vehicle-schedule master。
2. 当前 vehicle-schedule master 实现的 pricing certificate 在 20 规模上过慢，不能直接作为主线替代。
3. schedule no-good cuts 可能很多，且通常只在整数候选解处触发。
4. robust capacity cut 和 k-path/resource cut 在当前 20 规模实例上经常不触发。
5. schedule capacity cut 能找到少量 violated cuts，但不一定显著提升 root bound。
6. 3PB 的 branching testing 时间很大，是当前主要性能瓶颈。
7. 当前还没有 2LBB；ML 还没有参与候选排序或测试预算控制。

## 18. 2026-05-19：LP 违背的 schedule incompatibility pair/clique cut

本轮新增一个受控的 fractional schedule cut separator。它不等待 restricted-MIP 或整数 RMP 解给出不可排程 witness，而是在完成 exact pricing certificate 后检查当前 LP 解中同一车辆的高活动 route 支撑。

分离逻辑：

```text
1. 对每辆车取 LP 活动量最高的 route 支撑，默认最多 80 条；
2. 对 route pair (p,q) 做 exact transition check；
3. 若 p->q 与 q->p 都不可行，则这两条 route 不能同时属于同一辆车；
4. 若活动量 lambda[p,r]+lambda[q,r] > y[r]，则加入 schedule_pair_conflict；
5. 若一组 route 两两双向不可排程，且 sum lambda[p,r] > y[r]，则加入 schedule_clique_conflict：
   sum_{p in K} lambda[p,r] <= y[r]。
```

有效性来自 exact transition check：同一辆车上的两条 sortie 必须存在一个先后顺序；如果从时间 0 开始两个方向都不可行，则更晚开始也不会使其可行。因此 pairwise clique 中任意两条 route 不能共存，整组最多选一条。

默认配置：

```yaml
schedule_incompatibility_cuts_enabled: true
schedule_incompatibility_cut_max_depth: 2
schedule_incompatibility_cut_max_rounds_per_node: 2
schedule_incompatibility_cut_max_support_routes: 80
schedule_incompatibility_cut_max_per_round: 10
schedule_incompatibility_cut_min_violation: 5.0e-2
schedule_incompatibility_clique_min_size: 3
schedule_incompatibility_clique_seed_count: 24
```

新增统计字段：

```text
schedule_clique_conflict_cuts_added
metric_schedule_clique_conflict_cut_events
```

注意：该 separator 只决定尝试哪些 pair/clique；是否加 cut 完全由 exact route transition check 和当前 LP violation 决定。它保持 exactness，但会增加 active signature cut 数量，因此 pricing dominance 继续依赖 `signature_prefix_mask` 来避免错误剪枝。

## 19. 2026-05-19：高阶 route-set schedule packing cut

本轮新增更强的 schedule packing separator。它不再只看 route pair 或 pairwise clique，而是对一组 route `C` 直接计算：

```text
U(C) = 同一辆真实车辆最多能从 C 中排程多少条 route
```

若当前 LP 解满足：

```text
sum_{p in C} lambda[p,r] > U(C)y[r]
```

则加入：

```text
sum_{p in C} lambda[p,r] <= U(C)y[r]
```

实现边界：

```text
1. 候选 C 来自当前 LP 高活动 route 支撑；
2. 候选生成是启发式，只影响尝试哪些集合；
3. RHS 的 U(C) 必须由 exact route-set schedule DP 计算；
4. exact DP 同时考虑 route ready time、horizon 和 S_bar；
5. 若 DP 状态数超过上限，返回 None，不加 cut；
6. cut 只在当前 LP 违反阈值时加入。
```

该 cut 是 pair/clique/no-good 的高阶统一形式：

```text
pair conflict:        |C|=2, U(C)=1
clique conflict:      |C|>=3, U(C)=1
integer no-good:      U(C)<=|C|-1
route-set packing:    1<=U(C)<|C|
```

默认配置：

```yaml
route_set_schedule_packing_cuts_enabled: true
route_set_schedule_packing_cut_max_depth: 2
route_set_schedule_packing_cut_max_rounds_per_node: 2
route_set_schedule_packing_cut_max_support_routes: 40
route_set_schedule_packing_cut_max_routes: 16
route_set_schedule_packing_cut_max_per_round: 5
route_set_schedule_packing_cut_min_violation: 5.0e-2
route_set_schedule_packing_oracle_max_states: 200000
```

新增统计字段：

```text
schedule_route_set_packing_cuts_added
metric_schedule_route_set_packing_cut_events
metric_route_set_schedule_packing_diag_events
metric_route_set_schedule_packing_candidate_sets
metric_route_set_schedule_packing_oracle_queries
metric_route_set_schedule_packing_oracle_incomplete
metric_route_set_schedule_packing_not_tight
metric_route_set_schedule_packing_not_violated
metric_route_set_schedule_packing_duplicates
metric_route_set_schedule_packing_violated_candidates
metric_route_set_schedule_packing_max_violation
metric_route_set_schedule_packing_oracle_states_max
```

精确性说明：`C` 的选择不参与证明；只要 `U(C)` 是 exact oracle 给出的真实上界，`sum_{p in C} lambda[p,r] <= U(C)y[r]` 就不会删除任何原问题整数可行解。`y[r]=0` 时车辆不能选 route，`y[r]=1` 时同一辆车最多只能从 `C` 中排 `U(C)` 条 route。状态超限时不加 cut，因此不会用启发式上界破坏 exactness。

### 19.1 route-pack skip 诊断

本轮补充 `route_set_schedule_packing_diagnostics` 日志事件。它不改变模型、cut 或最优性证明，只记录 separator 每轮为什么没有继续加 route-pack cut。

终端会出现类似：

```text
route-pack diag node 0 round=1 vehicles=2/2 support_max=40 cand=90 oracle=90 incomplete=0 not_tight=75 not_viol=10 dup=0 violated=5 added=5 max_viol=0.42 states_max=1234
```

字段含义：

```text
candidate_sets: 生成的 route 集合候选数
oracle_queries: 调用 exact route-set schedule bound 的次数，可能命中缓存
skipped_oracle_incomplete: exact oracle 超状态上限或未能证明，直接跳过
skipped_not_tight: U(C)>=|C|，该集合没有给出更紧 schedule packing 约束
skipped_not_violated: cut 有效但当前 LP 未违反阈值
skipped_duplicate: 与已有 cut 或本轮候选重复
violated_candidates: 通过 exact oracle 且 LP 违反的候选数
added: 本轮实际加入的 cut 数，受 max_per_round 限制
max_violation: 本轮候选中的最大违反量
oracle_states_max: 单个候选 exact DP 最大状态数
```

这个诊断的用途是判断 route-pack separator 的瓶颈：如果 `not_tight` 很高，说明候选集合排程上界太松；如果 `not_violated` 很高，说明 LP 支撑没有明显违反；如果 `oracle_incomplete` 很高，说明 exact oracle 状态上限或候选规模需要调整。

### 19.2 schedule-capacity skip 诊断

本轮补充 `schedule_capacity_diagnostics` 日志事件。它不改变 cut 形式，只记录 schedule-capacity separator 对候选任务集合 `S` 的处理结果。

终端会出现类似：

```text
schedule-cap diag node 0 round=1 vehicles=2/2 cand=700 oracle=700 incomplete=0 not_tight=690 not_viol=10 dup=0 violated=0 added=0 max_viol=0.0 states_max=12345
```

字段含义：

```text
candidate_subsets: 生成的任务集合候选数量
oracle_queries: 调用 exact schedule task-capacity oracle 的次数
skipped_oracle_incomplete: oracle 超状态上限或未能证明，跳过
skipped_not_tight: U(S)>=|S|，该集合没有更强上界
skipped_not_violated: cut 有效但当前 LP 未违反阈值
skipped_duplicate: 与已有 schedule-capacity cut 重复
violated_candidates: oracle 证明且当前 LP 违反的候选数量
added: 本轮实际加入的 schedule-capacity cut 数量
max_violation: 最大违反量
oracle_states_max: 单个候选最大 oracle 状态数
```

这个诊断用于判断 `schedule_capacity_cuts_added=0` 的原因。如果 `not_tight` 很高，说明当前候选 `S` 对真实单车排程并不紧；如果 `not_violated` 很高，说明 LP 已满足这些上界；如果 `oracle_incomplete` 很高，才优先优化 oracle 或降低候选规模。

### 19.3 弱 schedule no-good cut 清理

`schedule_nogood_core` / `schedule_nogood_full` 是从不可排程整数候选中回流的局部排除 cut。它们保持 exactness，但在 20 规模上可能大量出现、对 bound 提升有限，并增加 RMP 和 pricing 的 active signature cut 负担。

当前新增只针对弱 no-good 的 inactive purge：

```yaml
schedule_nogood_purge_enabled: true
schedule_nogood_purge_age: 8
schedule_nogood_purge_slack: 1.0e-4
schedule_nogood_purge_dual: 1.0e-8
```

清理条件：

```text
1. cut.kind 属于 schedule_nogood / schedule_nogood_core / schedule_nogood_full；
2. 当前 RMP 中 slack > schedule_nogood_purge_slack；
3. 当前 RMP dual 绝对值 <= schedule_nogood_purge_dual；
4. 连续 inactive 次数达到 schedule_nogood_purge_age。
```

不清理的结构性 cut：

```text
schedule_pair_conflict
schedule_clique_conflict
schedule_route_set_packing
```

精确性说明：删除一个已经加入的有效 cut 只会放松当前 LP relaxation，不会删除原问题可行解；之后 RMP 和 pricing 使用同一套 active cut，因此节点证书仍然一致。被清理的 no-good 会从 `cut_keys` 中移除，如果后续 LP 或整数候选再次需要它，可以重新加入。

### 19.4 RIM 冲突回流诊断

restricted integer master 仍只作为 primal heuristic，不参与 lower bound 证明。它找到排程不可行整数候选后，按如下顺序尝试回流正式 cut：

```text
1. 双向不可排程 route pair -> schedule_pair_conflict；
2. 可证明的 route 集合排程上界 -> schedule_route_set_packing；
3. 可证明的任务集合上界 -> schedule_capacity_conflict；
4. 当前 LP 已违反的弱 no-good -> schedule_nogood_core；
5. 若弱 no-good 当前 LP 不违反，则跳过，不回流。
```

新增 `rim_conflict_diagnostics` 日志事件记录：

```text
conflicts_checked
pair_cuts_added
route_set_packing_cuts_added
route_set_packing_cache_hits
route_set_packing_oracle_states_max
schedule_capacity_cuts_added
nogood_cuts_added
weak_nogood_not_violated
```

这个诊断用于确认 RIM 是否正在大量产生只能靠弱 no-good 排除的局部冲突。如果 `nogood_cuts_added` 很高而 bound 提升小，应优先寻找更强 route-set packing / schedule-capacity 证书、route pool 上界构造或可证明的目标值下界，而不是继续提高 no-good 数量。注意：只有证明一辆车方案不可行，或证明所有一辆车方案目标值都不优于当前 incumbent，才能安全加入 `sum_r y_r >= 2`；仅凭 tight fleet 当前为 2 辆车不能加这个 cut。

### 19.6 conflict-induced route-set packing 与缓存

2026-05-21 起，RIM 回流和整数解校验中的不可排程 core 会先尝试 route-set schedule packing conflict cut。实现新增：

```text
_add_schedule_route_set_packing_conflict_cuts()
```

该函数复用 `exact_route_set_schedule_capacity()` 的证书。对 LP separator，只要当前 LP 违反且 `U(C)<|C|` 即可加入；对 RIM / integral validation 的不可排程 conflict 回流，只有 `U(C)<|C|-1` 时才提升为 `schedule_route_set_packing`，因为 `U(C)=|C|-1` 与普通 no-good 同强度，实际输出中会导致 cut 膨胀但 bound 变化很小。RIM 中 route-pack 使用原始不可排程整数解的 full route set 计算 `U(C)`；pair、schedule-capacity 和 no-good fallback 仍使用 deletion-minimal core。其结果进入 `route_set_schedule_packing_cache`，不可排程 witness 进入 `schedule_conflict_witness_cache`，并额外记录：

```text
schedule_route_set_packing_conflict_diagnostics
```

关键字段包括 `route_count`、`upper_bound`、`oracle_complete`、`oracle_states`、`cache_hit` 和 `added`。这些缓存和日志只减少重复 oracle 调用并解释 cut 来源，不改变 cut 有效性或节点 lower-bound 证书。

### 19.5 固定车成本感知的初始上界

2026-05-20 的 bench_20_02/03 输出暴露了一个上界侧问题：初始贪心在比较“把任务插入已有车辆路线”和“开另一辆车的新路线”时主要比较 route travel cost，没有把 `F y_r` 的固定车辆成本计入候选增量。因此它倾向于用两辆车换取较短行驶路线，导致初始 incumbent 落在约 `329~335`，而同一实例存在一辆车多 sortie 的真实可行解，目标约 `237~246`。

当前修复：

```text
1. 初始贪心插入的 score 改为 fixed-cost-aware delta objective；
2. 开启一个快速 serial schedule incumbent：按时间窗顺序把任务串成同一车辆的多条 sortie，若 exact schedule check 通过，就加入初始 route pool 并更新 incumbent；
3. 较慢的贪心改进只有在原始构造目标已经有机会优于当前 incumbent 时才运行，避免在明显更差的构造上消耗初始化时间。
```

精确性边界：这些变化只增加 route pool 中的可行列并改善 primal upper bound，不改变 RMP 约束、pricing 可行域、cut 有效性或 node lower bound 证书。任何由 serial/greedy 得到的 incumbent 都必须通过 `_assignment_feasible()`，即 cover、sortie 数和每辆车 exact multi-sortie schedule check。

### 19.7 subset-row 与实验性成本型 schedule 下界 cut

2026-05-21 的 route-pack conflict 输出显示，很多新增 cut 是 `routes=3,U=2` 或 `routes=4,U=3`，本质只比 no-good 换了形式，root bound 仍停在 `228.39887` 附近。为真正推进 lower bound，当前新增三类 cut，其中 `subset_row` 和 `limited_memory_rank1` 进入默认主线，成本型 schedule 下界 cut 暂时保留为实验项：

```text
subset_row:
sum_{p,r} floor(|p∩S|/k) lambda[p,r] <= floor(|S|/k)
```

这是标准 VRP subset-row inequality，用于强化 route set-partitioning 松弛。候选 `S` 来自当前 LP 支撑 route 的任务集合与小规模 route union；`k` 默认取 2 和 3。

第一版 limited-memory rank-1 cut：

```text
limited_memory_rank1:
sum_{p,r} floor((sum_{i in S} m_i a_ip) / d) lambda[p,r]
    <= floor((sum_{i in S} m_i) / d)
```

其中 `d>=3`，`m_i in {1,...,d-1}`。普通 subset-row 是 `m_i=1` 的特例；lm-rank1 允许在小 memory 任务上给部分任务更高 multiplier，用 rank-1 CG rounding 抓普通 subset-row 抓不到的 fractional pattern。memory 只限制候选 multiplier pattern，不参与有效性证明。当前默认 `lm_rank1_denominators=[3,4]`、`lm_rank1_memory_size=4`、`lm_rank1_max_patterns_per_set=12`，只在根节点轻量分离。2026-05-21 的重参数长测显示，`[3,4,5]`、`memory_size=5`、`patterns_per_set=30` 会在 `bench_20_01` 上显著增加 root 诊断成本，但 lower bound 只提升约 `0.01`，因此不进入默认主线。无新增 cut 的 subset-row / lm-rank1 / route-pack 分离轮次也会计入本节点预算，避免同一节点重复扫描相同无效候选。

```text
schedule_subset_cost_lb:
sum_p c[p] lambda[p,r]
  - L(S) sum_{i in S} z[i,r]
  + L(S)(|S|-1)y[r] >= 0
```

其中 `L(S)` 是一辆真实车辆完整服务 `S` 的最小变量成本，由 `exact_schedule_subset_cost()` 小规模 DP 证明。若 oracle 超状态上限、未完成、或证明 `S` 单车不可行，则不加成本 cut。该 cut 的作用不是排除某个局部不可排程整数解，而是直接阻止 LP 用过低成本的 fractional route 组合承担同一车辆上的任务集合。

pricing 已同步支持这些新 cut：

```text
subset_row coefficient:
    floor(|p∩S|/k)

schedule_subset_cost_lb coefficient:
    c[p] - L(S)|p∩S|

limited_memory_rank1 coefficient:
    floor((sum_{i in p∩S} m_i) / d)
```

由于第二类系数包含 `c[p]`，当其 dual 非零时，当前实现先关闭 dominance，避免旧 dominance score 未包含成本 cut 信息而错误剪枝。这样会牺牲部分 pricing 速度，但保留 exact pricing 证书。

新增日志：

```text
subset_row_diagnostics
schedule_subset_cost_diagnostics
```

新增配置：

```yaml
subset_row_cuts_enabled: true
lm_rank1_cuts_enabled: true
schedule_subset_cost_cuts_enabled: false
schedule_capacity_separation_enabled: false
```

新增 CSV 字段：

```text
subset_row_cuts_added
schedule_subset_cost_cuts_added
lm_rank1_cuts_added
```

2026-05-21 `bench_20_02` 实测后，`schedule_subset_cost_lb` 当前候选器 1620 次 exact oracle 查询均未找到 violated cut，`added=0`，但消耗了明显时间。因此默认关闭它，避免把无收益 oracle 放进论文 baseline。`subset_row` 则加入 17 条 cut，并把 root bound 从 `228.398870` 抬到约 `228.655122`，保留默认启用。LP 层 `schedule_capacity` separator 在 `bench_20_02/03` 中也大量 oracle 查询但没有加入 cut，因此默认关闭；RIM 和整数校验中的 schedule-capacity fallback 仍保留。

精确性边界：`subset_row` 是整数 set-partitioning 有效不等式；`limited_memory_rank1` 是 cover 等式的 rank-1 CG cut；`schedule_subset_cost_lb` 的 `L(S)` 必须来自 exact oracle。候选集合只决定“尝试哪个 S 或 multiplier pattern”，不参与证明。任何 oracle 不完整的情形都跳过，不加对应 oracle cut。

## 20. Candidate-Pool Schedule-Pack Relaxation

当前主线新增 `schedule-pack` relaxation。它用当前节点已经生成的 route pool 构造一批完整车辆 schedule columns，每个 column 都是一辆车可真实执行的一串 sorties。root 上同时保留诊断输出；浅层节点使用 vehicle-indexed schedule-pack LP，尊重当前节点分支约束和已有 valid cuts。当前实现先做 candidate-pool CG；若开启 full pricing，则在候选池收敛后继续做全 route-space exact schedule pricing。

root 诊断 LP 为：

```text
min  sum_s (F + c_s) z_s
s.t. sum_s a_{i,s} z_s = 1        对每个任务 i
     sum_s z_s <= R_bar           车辆上限
     0 <= z_s <= 1
```

其中 `z_s` 是完整车辆 schedule column，`a_{i,s}` 表示 schedule `s` 是否服务任务 `i`。节点 relaxation 使用 `z_{s,r}` 和 `y_r`，并加入 `sum_s z_{s,r} <= y_r`、当前分支约束以及已生成 valid cuts。该 LP 的目标是判断完整 schedule 变量是否比当前 route-vehicle master 更能反映多 sortie 排程结构。

需要强调：`exact_over_candidate_routes=true` 只表示候选 route 集合内无负 reduced-cost schedule column；候选集合仍可能被截断，所以这不是全局 lower bound 证书。只有 `exact_over_full_route_space=true` 且没有触发时间或状态上限时，才表示该节点的 schedule-pack pricing 完整。当前代码只在该标志为真时把 schedule-pack LP 值接入正式节点下界：

```text
node.lower_bound = max(route_vehicle_bound, schedule_pack_bound)
```

随后该节点可以按普通 lower bound 逻辑剪枝。若 `exact_over_full_route_space=false`，schedule-pack 值仍不混入正式 `dual_bound` / `diagnostic_dual_bound`，也不能用于剪枝或最优性证明。

新增配置。注意：2026-05-21 的 20 节点测试后，这组 schedule-pack 开关在默认论文级配置中关闭；保留为诊断/消融实验开关。

```yaml
schedule_pack_diagnostic_enabled: false
schedule_pack_diagnostic_max_candidate_routes: 180
schedule_pack_diagnostic_max_columns: 8000
schedule_pack_diagnostic_beam_width: 800
schedule_pack_diagnostic_max_sorties: 0
schedule_pack_diagnostic_time_limit: 60.0
schedule_pack_pricing_batch_size: 32
schedule_pack_relaxation_enabled: false
schedule_pack_relaxation_max_depth: 1
schedule_pack_relaxation_time_limit: 30.0
schedule_pack_relaxation_use_for_priority: true
schedule_pack_full_pricing_enabled: false
schedule_pack_full_pricing_max_depth: 0
schedule_pack_full_pricing_max_states: 0
schedule_pack_adaptive_enabled: false
schedule_pack_adaptive_gap_abs: 10.0
schedule_pack_adaptive_gap_ratio: 0.03
schedule_pack_adaptive_skip_if_fathomable: true
route_enumeration_adaptive_enabled: false
route_enumeration_adaptive_gap_abs: 10.0
route_enumeration_adaptive_gap_ratio: 0.03
```

新增日志事件：

```text
schedule_pack_adaptive
schedule_pack_diagnostic
schedule_pack_relaxation
route_enumeration_adaptive
```

新增 CSV 字段：

```text
schedule_pack_diagnostic_status
schedule_pack_diagnostic_objective
schedule_pack_diagnostic_gap_vs_root
schedule_pack_diagnostic_columns
schedule_pack_diagnostic_candidate_routes
schedule_pack_diagnostic_generated_states
schedule_pack_diagnostic_time
schedule_pack_relaxation_calls
schedule_pack_relaxation_root_objective
schedule_pack_relaxation_best_objective
schedule_pack_relaxation_best_gap_vs_node
schedule_pack_relaxation_candidate_exact
schedule_pack_relaxation_full_exact
schedule_pack_relaxation_full_pricing_states
schedule_pack_relaxation_full_pricing_time
schedule_pack_relaxation_columns
schedule_pack_adaptive_decisions
schedule_pack_adaptive_runs
schedule_pack_adaptive_skips
schedule_pack_adaptive_easy_skips
schedule_pack_adaptive_bound_skips
route_enumeration_adaptive_decisions
route_enumeration_adaptive_runs
route_enumeration_adaptive_skips
route_enumeration_adaptive_easy_skips
```

判读方式：

- 若 `schedule_pack_diagnostic_objective` 明显高于当前 `root_relaxation`，且 `exact_over_full_route_space=true`，说明完整 schedule master 的下界确实强于当前 route-vehicle master；
- 若它与 `root_relaxation` 接近，说明仅改变量粒度未必能解决问题，需要优先检查 route pool、固定车辆成本结构和实例本身的 schedule 可分性；
- 若状态为 `NO_COVER`，说明诊断生成的 schedule columns 没覆盖所有任务，应先扩大候选 route 或 beam；
- 若状态为 `TIME_LIMIT`，说明诊断生成/求解成本过高，应降低候选规模或单独离线跑。

2026-05-21 后的版本中，schedule-pack 不再只是一次性 beam LP。它会：

1. 把当前 incumbent 的每辆车 schedule 作为 seed columns 强制加入；
2. 解 candidate-pool schedule-pack LP；
3. 读取 cover、schedule/fleet、cut 和 branch dual；
4. 在候选 route 集合内用 DP pricing 搜索负 reduced-cost 完整 schedule column；
5. 每轮 pricing 不再只回流 1 列，而是按 `schedule_pack_pricing_batch_size` 批量加入最负的一组 schedule columns，并缓存 route-task mask、cut 系数和 branch 系数；
6. vehicle-indexed schedule-pack LP 使用持久化 RMP：初始化建一次 PySCIPOpt 模型，后续新 schedule column 只增量加入 `z[column,vehicle]` 变量及 cover、schedule-use、cut、branch row 的系数，不再每轮重建完整 LP；
7. 只有 LP 状态为 `OPTIMAL` 且 dual 数值有限、未超过安全阈值时才进入 pricing；若持久化 RMP 增量加列后出现 dual 不可用，会先用当前全部 schedule columns 重建一次等价 RMP；若仍触发时间限制或 SCIP 返回内部极大哨兵值，则记为 `TIME_LIMIT` / `DUAL_UNAVAILABLE`，不把该 dual 用于 reduced cost；
8. 若找到则加列并重复，直到候选 route 集合内无负 reduced-cost schedule column，或触发时间/列数限制；
9. 若完整全 route-space pricing 结束并得到 `exact_over_full_route_space=true`，则把 schedule-pack LP 值作为正式节点 lower bound；否则只记录诊断值和节点排序信号。

因此，`exact_over_candidate_routes=true` 只表示“候选 route 集合内”已经收敛；只有后续 full pricing 完整结束并给出 `exact_over_full_route_space=true`，才说明没有被候选 route 截断影响。

2026-05-21 之后，schedule-pack 和 route enumeration 增加自适应门控，用来避免 `bench_20_01` 这类简单实例反复支付重诊断成本。判据只使用当前 incumbent 与 route-vehicle 节点下界的差距：

```text
gap = incumbent - route_vehicle_bound
threshold = max(schedule_pack_adaptive_gap_abs,
                schedule_pack_adaptive_gap_ratio * max(1, |route_vehicle_bound|))
```

若 `gap <= threshold`，则该节点记为 `easy_gap` 并跳过 schedule-pack diagnostic / relaxation；若当前节点已经可由 incumbent 直接 bound fathom，则记为 `already_fathomable` 并跳过。route enumeration 使用同样判据：简单节点不回收 near-zero 非负 reduced-cost route，只保留负 reduced-cost route 的标准回流。日志中 `schedule_pack_adaptive` 和 `route_enumeration_adaptive` 会记录 `action=skip/run`、`reason`、`gap`、`threshold`、`incumbent` 和节点下界，CSV 中也有对应计数。该机制不跳过 exact pricing、不删除任何合法列、不改变 cut 和 lower-bound 证明；它只控制额外的诊断/排序信号和非必要的近零列回收。

2026-05-21 之后，节点 schedule-pack relaxation 增加全 route-space exact schedule pricing 的第一版：

1. 先保持 candidate-pool CG，快速在当前 route pool 内补充负 reduced-cost schedule column；
2. 当候选集合内无负 reduced-cost column 后，若 `schedule_pack_full_pricing_enabled=true` 且节点深度不超过 `schedule_pack_full_pricing_max_depth`，则对该节点每辆车运行 integrated full route-space schedule pricing；
3. full pricing 不再先物化全部 elementary sortie route，而是在每个 schedule label 上生成下一条可行 sortie route 并立即尝试扩展完整 schedule column；schedule 状态包含已覆盖任务集合、route 数、车辆 ready time 和当前 reduced component；
4. 若发现全 route-space 负 reduced-cost schedule，则把其中新 route 加入候选池、加入 schedule column、重解 vehicle-indexed schedule-pack LP，并重复；即使本轮 full pricing 因早停、时间或状态上限尚未完整结束，只要该 schedule column 本身可行，也可以安全加列；
5. 若所有车辆的全 route-space pricing 都完整结束且没有负 reduced-cost schedule，日志标记 `exact_over_full_route_space=true` 和 `exact_bound=true`。

精确性边界：全 route-space pricing 只有在没有触发时间限制、没有触发 `schedule_pack_full_pricing_max_states` 状态上限时才给出 exact 证书。若日志状态为 `FULL_PRICING_TIME_LIMIT` 或 `exact_over_full_route_space=false`，该 schedule-pack 值仍然不能用于剪枝或最优性证明。非完整 full pricing 中发现的负 reduced-cost schedule column 只作为合法列回流 RMP，不构成无遗漏证明。当前代码仍保守地把非 exact schedule-pack 值作为独立 schedule-pack 字段和节点排序信号，不混入正式 `dual_bound`。

2026-05-21 集成式 full pricing 的安全剪枝与 dominance：

1. route prefix 只按已经发生的服务时间窗、载重和已消耗能量剪枝，不用“prefix 立即回仓库”作为剪枝条件，避免误删可继续延伸的 route；
2. 完整 route 是否可作为下一条 sortie，需要通过 `evaluate_route()` 和 `evaluate_route_at_start()`；
3. 同一 `(covered_task_mask, route_count)` 下，若一个 label 的 `ready_time` 不晚且 `reduced_component` 不大，则它安全支配另一个 label，因为未来可选任务集合相同、剩余 sortie 数相同，且更早 ready time 和更低 reduced component 对任何后续扩展都不劣。

`bench_20_02` root-only 300s full-pricing 长测：集成式版本把 full-pricing 状态数从约 `69009402` 降到 `32819435`，route 生成数从约 `1945331` 降到 `1195168`；但 `schedule_pack_obj=232.66585`、`official_lb=229.306913` 未变，仍未得到 full exact 证书。

## 21. Route Pricing 四步加速

2026-05-21 的当前版本在 `bpc/pricing.py` 中加入 route pricing 四步加速第一版：

1. `ng-DSSR` 启发式层：在 bounded-label heuristic pricing 中使用 ng-memory dominance。route 扩展仍检查完整 `visited_mask`，所以生成的 route 仍是 elementary；但 ng-memory dominance 不是完整状态证明，因此这类调用永远不能作为节点 certificate。
2. completion bound：当没有 active cut dual、没有 active `arc_on` dual、没有 vehicle-time dual 时，对 label prefix 计算剩余任务的乐观 reduced-cost suffix 下界。若该下界已经不可能低于 `-pricing_eps`，安全剪掉该 prefix；当前实现按剩余任务 bit-mask 动态求和，不再预生成 `2^n` 大表。
3. backward completion bound：当前实现不是完整双向 label merge，而是后向 suffix bound 的安全版本。它只用于证明某个 prefix 不可能补成负 reduced-cost route，不改变 route 可行域。
4. route enumeration phase：完整 exact pricing 若没有负 reduced-cost route，可额外回收 reduced cost 不超过 `route_enumeration_rc_threshold` 的近零非负 route。若该轮仍存在负列，则只回流负列，避免正 reduced-cost route 拖慢主 CG。

对应配置：

```text
pricing_completion_bound_enabled: true
ng_dssr_pricing_enabled: true
ng_dssr_memory_size: 6
route_enumeration_enabled: false
route_enumeration_rc_threshold: 0.25
route_enumeration_max_routes: 1200
route_enumeration_adaptive_enabled: false
route_enumeration_adaptive_gap_abs: 10.0
route_enumeration_adaptive_gap_ratio: 0.03
```

日志新增字段：

```text
ng_relaxation_enabled
ng_memory_size
completion_bound_enabled
completion_pruned
route_enumeration_threshold
enumerated_routes
```

精确性边界：`ng-DSSR` 只影响启发式找列，不允许 `cert=True`；completion bound 只在数学上安全的条件下启用；route enumeration 只添加合法 column，不删除 column。节点 lower bound 的证明条件仍是：Phase-II RMP 使用 true dual，exact pricing 完整结束且没有负 reduced-cost route，并且所有启用的 cut separation 都完成。

## 22. 运行命令

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
