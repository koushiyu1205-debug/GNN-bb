# Lunar-GAT-BPC-Exact 算法预构建设计

## 0. 设计结论

本文件预构建 `GAT_BPC_moonTerk` 的正式精确算法主线：`Lunar-GAT-BPC-Exact`。

核心判断：

- `exact fixed-graph direct baseline` 继续保留，但只作为小规模 exact oracle、模型校验器和论文对照基线。
- 正式主算法应是 `journey master + true-dual pricing + branch-and-price-and-cut + GAT exact-safe guidance`。
- 不原样迁移 `BPC_future/solver/journey_driver.py`，只迁移其中证明边界清楚、能服务新场景的组件思想。
- GAT 只影响排序、调度、候选优先级和有限延迟；不提供 official lower bound，不闭节点，不剪枝。
- 所有 optimal claim 必须区分证书范围：direct DP optimal、restricted RMP diagnostic、true-dual BPC optimal。

一句话目标：

```text
用 lunar schema 重建一个证明边界更干净的 GAT+BPC 精确算法，
在 5/10 上对齐 direct baseline，在 20/30 上体现 BPC 扩展性，
后续再支持 50/100 的 gap/scalable benchmark。
```

## 1. 现有代码基础

### 1.1 Lunar 项目已有的好基础

`GAT_BPC_moonTerk` 当前已经有可复用的 lunar-specific exact 基础：

- `src/lunar_ice_bpc/exact/core/data.py`
  - `TaskData` 已包含 `science_weight`、`operation_mode`、`demand`、`service_time`、`service_energy`、`ready_time`、`due_time`、`local_shadow_score`、`local_thermal_risk`。
  - `ArcOptionData` 已包含三路径候选的 `travel_time_min`、`energy_proxy`、`risk_integral`、`distance_km`、`shadow_exposure_min`、`thermal_survival_energy_proxy`、`path_xy`。
  - `LunarIceData` 已包含 `fleet_size`、`max_tasks_per_trip`、`Q_ice`、`B_use`、`horizon`、`dock_overhead_min`、`recharge_power_proxy_per_min`、`max_shadow_exposure_per_sortie` 和 objective weights。

- `src/lunar_ice_bpc/exact/core/columns.py`
  - `TimedSortie` 已经显式检查时间窗、容量、能量、shadow exposure、horizon。
  - `build_timed_sortie()` 已经按“出 depot -> 服务任务 -> 返回 depot -> 充电”构造 sortie。

- `src/lunar_ice_bpc/exact/core/journey.py`
  - `JourneyColumn` 已经把多个 sortie 组合成一台 rover 的 journey。
  - 目标函数已经包含 discovery completion、journey end time、risk、energy。

- `src/lunar_ice_bpc/exact/master/journey_rmp.py`
  - 已有 `JourneyDuals` 和 `manual_journey_reduced_cost()`。
  - 已有 restricted-universe RMP diagnostic。

- `src/lunar_ice_bpc/exact/pricing/journey_pricing.py`
  - 已有 direct-label pricing bridge。
  - 目前仍是小规模 direct/diagnostic pricing，不是正式 BPC pricing oracle。

这些基础应该保留。

### 1.2 BPC_future 中建议迁移的思想

只迁移思想和局部组件，不迁移旧 driver 形状。

建议迁移：

- journey master 的 LP 结构。
- task-cover dual、fleet dual、cut dual 的 reduced-cost 口径。
- pricing 状态语义：
  - `FOUND_NEGATIVE`
  - `LOCAL_NO_COLUMN_UNCERTIFIED`
  - `CERTIFIED_NO_NEGATIVE`
  - `INCOMPLETE_LIMIT`
  - `DUPLICATE_ONLY`
- true-dual final judge 作为唯一 no-negative certificate 路径。
- harvesting：对已经 true-RC 验证过的 negative journeys 做批量、分散、强 reduced-cost 的列选择。
- hidden-negative audit：worker 漏列后由 final judge 暴露，再反哺候选宇宙。
- GAT admission queue 的 exact-safe 语义：GAT 不能 reject true-RC negative column，不能 certificate。

不建议迁移：

- `BPC_future/solver/journey_driver.py` 的整体结构。
- 旧 Moon Trek slope/roughness risk 模型。
- 旧 GAT 权重、旧训练结论、旧 per-instance preset。
- 未在 lunar reduced-cost 口径中重新验证的 cuts / branch heuristics / dual stabilization 参数。

## 2. 算法范围

### 2.1 固定模型宇宙

本算法的 exact claim 只针对如下固定离散模型：

```text
fixed depot
fixed task set
fixed resource-map payload declared by the instance manifest
    current sp50 benchmark: 50 x 50 km, 100 m grid
fixed directed complete logical graph
fixed path-option set per ordered pair:
    low_time
    low_energy
    low_risk
fixed vehicle/resource parameters
fixed time windows
fixed objective function
fixed path-option dominance policy
```

它不是连续月表任意路径最优。物理路径已经在实例预处理阶段固定为三类 path options。

### 2.2 与 direct baseline 的关系

`exact fixed-graph direct baseline`：

- 直接枚举/DP 固定 logical graph 内的 path-option/sortie/journey 组合。
- 适合 5/10，小 20 可作为 sanity oracle。
- optimal 证书范围是 `DIRECT_DP_FIXED_GRAPH_OPTIMAL`。

`Lunar-GAT-BPC-Exact`：

- 用 RMP + pricing 逐步生成 journey columns。
- 通过 true-dual pricing no-negative 和 branch tree closure 证明 optimal。
- root node LP 证书范围是 `BPC_NODE_LP_CERTIFIED`。
- tree optimal 证书范围是 `BPC_TREE_OPTIMAL`。

如果 full BPC tree 关闭，且 direct-DP finite universe 与 BPC column universe 完全一致，则最终 BPC integer incumbent objective 应与 direct-DP integer optimum 一致。Root node 的 BPC LP bound 只要求 `<= direct-DP integer optimum`；root 相等只是 `integral_root=true` 的观察，不是验收要求。BPC 的价值不是求出更低 objective，而是更快、更可扩展、更符合论文主算法。

## 3. 数学模型

### 3.1 集合

```text
T      task set
K      rover set
P      all feasible journey columns
A_ij   path options for directed logical edge i -> j
```

每个 ordered pair `i -> j` 保留三类 path option：

```text
low_time
low_energy
low_risk
```

### 3.2 Sortie

一个 sortie 是：

```text
s = (0, i_1, i_2, ..., i_m, 0)
```

其中：

```text
m <= max_tasks_per_trip
每条 leg 选择一个 path option
```

sortie 必须满足：

```text
time windows
ice load <= Q_ice
energy <= B_use
shadow exposure <= max_shadow_exposure_per_sortie
return and recharge before horizon
```

### 3.3 Journey

一个 journey 是一台 rover 的 multi-sortie schedule：

```text
p = (s_1, s_2, ..., s_q)
```

要求：

```text
sorties task-disjoint
sorties time-compatible
each sortie starts after previous return + recharge
all sortie resources feasible
```

### 3.4 Column cost

沿用 lunar objective：

```text
c_p =
    alpha_discovery_completion * completion_term_p
  + beta_journey_end_time      * end_time_p
  + gamma_lunar_ice_risk       * risk_p
  + delta_energy               * energy_p
```

其中：

```text
completion_term_p = sum_i science_weight_i * service_completion_time_i
risk_p            = route risk + thermal/service risk
energy_p          = route energy + service energy
end_time_p        = journey final end time
```

第一版 `end_time_p` 是 column-additive penalty：RMP 选择多个 journey 时，目标函数累加各 journey 的 end-time penalty。它不是 global makespan。若 reference solution 使用 `max(end_time)`，只能作为 constructive / diagnostic objective，不能作为 exact BPC objective oracle。未来若需要 global makespan，必须显式引入 master linking variable，而不是把 makespan 混入 column cost。

### 3.5 Journey master

变量：

```text
lambda_p >= 0
```

RMP：

```text
min sum_{p in P'} c_p lambda_p

s.t.
    sum_{p: i in S_p} lambda_p = 1        for all i in T
    sum_{p in P'} lambda_p <= fleet_size
    optional pricing-compatible cuts
```

整数解要求：

```text
lambda_p in {0,1}
```

BPC 中先解 LP relaxation，再通过 branch-and-price 处理整数性。

### 3.6 Reduced cost

RMP duals：

```text
pi_i      task cover dual
mu        fleet limit dual
gamma_h   cut dual
```

Journey reduced cost：

```text
rc(p) = c_p - sum_{i in S_p} pi_i - mu - sum_h gamma_h a_hp
```

所有 pricing、harvesting、audit、certificate 必须使用同一个 reduced-cost 函数。

## 4. 总体架构

建议模块结构：

```text
src/lunar_ice_bpc/exact/bpc/
  master/
    journey_master.py
    reduced_cost.py
    dual_audit.py

  pricing/
    status.py
    sortie_label.py
    journey_label.py
    completion_bounds.py
    final_judge.py
    harvest.py
    hidden_negative_audit.py

  branching/
    ryan_foster.py
    branch_selector.py
    node_queue.py

  cuts/
    subset_row.py
    cut_audit.py

  solver/
    node_solver.py
    tree_solver.py
    incumbent.py
    certificate_ledger.py
    run_bpc.py

src/lunar_ice_bpc/guidance/
  graph_builder.py
  gat_policy.py
  admission_queue.py
  shadow_logger.py
  typed_hints.py
```

已有 `src/lunar_ice_bpc/exact/` 是 proof boundary；正式 BPC 应放在 `src/lunar_ice_bpc/exact/bpc/` 下，避免顶层 `bpc/` 和 `exact/` 形成两个证书边界。Direct baseline 与 BPC 可以共用 instance/schema/objective helper，但不能共用模糊的“最优证书字段”；所有 certificate scope 必须由 ledger 显式命名。

`guidance/` 可以读取 exact 层导出的 typed state / shadow logs，但不能反向持有 proof-mutating code。`exact/bpc/` 只接收 typed hints，例如 candidate ordering、branch-pair ordering、finite-delay advice；hint 不能成为 certificate、lower bound 或 permanent rejection 的来源。

Import boundary：

```text
exact/bpc/ must not import torch, checkpoint loaders, GAT model, OOD model, or guidance policy implementation.
exact/bpc/ may only consume immutable typed guidance hints:
    candidate_id
    priority
    source
    finite_delay_budget
    uncertainty
    diagnostic_only

guidance/ may read exported state snapshots.
guidance/ must not mutate ColumnPool, RMP, certificate ledger, proof debt, or node bound objects directly.
```

实现时加测试：

```text
test_exact_bpc_has_no_torch_import
test_guidance_cannot_construct_certificate
test_guidance_cannot_mutate_exact_state
```

## 5. Node Solver 主循环

单个 branch node 的流程：

```text
Input:
    node branch context
    active cut context
    inherited column pool
    incumbent upper bound

Loop:
    1. Solve journey RMP.
    2. Audit RMP duals and current-pool reduced costs.
    3. Run fast pricing workers.
    4. If workers find true-RC negative columns:
           harvest columns
           add to pool
           continue
    5. If workers return local no-column or incomplete:
           run true-dual final judge
    6. If final judge finds negative columns:
           harvest columns
           hidden-negative audit
           seed worker catalog
           add to pool
           continue
    7. If final judge certifies no negative:
           node LP lower bound is official
           return NODE_LP_CERTIFIED
    8. If final judge hits limit:
           return NODE_INCOMPLETE
```

### 5.1 Node closure condition

一个 node 可以被 official 关闭，仅当：

```text
RMP LP optimal
AND all active column reduced costs are consistent
AND true-dual final judge returns CERTIFIED_NO_NEGATIVE
AND no delayed GAT negative candidate remains unreleased
AND cut/branch reduced-cost audit passes
```

任何 worker-local no-column 都不能关闭 node。

## 6. Pricing 层设计

### 6.1 Pricing 状态

统一状态：

```text
FOUND_NEGATIVE
LOCAL_NO_COLUMN_UNCERTIFIED
CERTIFIED_NO_NEGATIVE
INCOMPLETE_LIMIT
DUPLICATE_ONLY
```

含义：

- `FOUND_NEGATIVE`: 找到至少一个 true-RC negative journey。
- `LOCAL_NO_COLUMN_UNCERTIFIED`: 某个 worker 的本地候选宇宙没找到列，但不能证明全局无负列。
- `CERTIFIED_NO_NEGATIVE`: true-dual final judge 完整证明无负列。
- `INCOMPLETE_LIMIT`: 时间、序列数、label 数、内存或 frontier coverage 未完成。
- `DUPLICATE_ONLY`: 只发现已在 pool 中的 negative 或 replacement candidate，不能闭证书。

`DUPLICATE_ONLY` 不能静默当作 harmless。若 candidate 与当前 master column 重复且 `true_rc < -eps`，必须触发审计：

```text
existing master column manual RC also < -eps:
    RMP optimality / dual binding inconsistent

duplicate signature maps to different coefficients:
    signature or branch/cut coefficient mapping bug

column exists in pool but not current RMP:
    ColumnPool/RMP membership mismatch
```

因此 `DUPLICATE_ONLY` 必须记录 addability、RMP membership 和 RC-consistency audit；它不能关闭 node，也不能被当作无害尾部状态。

### 6.2 Fast worker

Fast worker 可以使用：

```text
GAT task priority
GAT task-set priority
dual-based task order
science/risk heuristic
active support task sets
hidden-negative seed task sets
limited path-option profiles
```

但 fast worker 的 no-column 永远是：

```text
LOCAL_NO_COLUMN_UNCERTIFIED
```

### 6.3 True-dual final judge

Final judge 必须：

```text
use true RMP duals
respect branch constraints
respect cut duals
search complete feasible journey space for the fixed logical graph
return either FOUND_NEGATIVE, CERTIFIED_NO_NEGATIVE, or INCOMPLETE_LIMIT
```

它是唯一 no-negative certificate 路径。

## 7. Lunar Labeling Kernel

### 7.1 Sortie label

Sortie label state：

```text
visited_task_mask
last_node
current_time
energy_used
shadow_exposure
ice_load
risk_integral
completion_term
path_signature
reduced_base
```

扩展一个 task：

```text
choose next task j
choose path option a in {low_time, low_energy, low_risk}
arrival = current_time + travel_time(last, j, a)
service_start = max(arrival, ready_j)
service_end = service_start + service_time_j
update energy / shadow / load / risk / completion
check due_j / B_use / Q_ice / shadow limit
```

返回 depot：

```text
choose path option a in {low_time, low_energy, low_risk}
return_time = current_time + travel_time(last, depot, a)
recharge_time = dock_overhead + energy_used / recharge_power
sortie_end = return_time + recharge_time
check horizon
```

### 7.2 Journey label

Journey label state：

```text
covered_task_mask
sorties
journey_end_time
journey_reduced_cost_base
```

扩展：

```text
append a feasible sortie whose tasks are disjoint
start next sortie no earlier than previous sortie end
```

### 7.3 Earliest-service dominance

第一版 pricing 只枚举 earliest feasible schedule，不枚举故意晚出发或额外等待。其成立条件必须写入 proof note：

```text
path resource coefficients are time-independent
energy / risk / shadow do not improve by absolute-time delay
objective time weights are nonnegative
waiting has no reward
```

在这些条件下，对同一 task sequence 和同一 path-option choices，earliest feasible schedule 弱支配任何 intentional delay。若未来加入 time-dependent illumination / thermal risk / recharge power，则该 lemma 失效，必须改成 start-time candidate labels。

### 7.4 Dominance

Dominance 必须 exact-safe。

可以支配的最低条件：

```text
same covered_task_mask
same last_node or same sortie boundary state
time <=
energy <=
shadow <=
load <=
risk/base_cost <=
reduced_base <=
```

如果使用 buckets：

- bucket 只能用于排序/缓存，默认不用于剪枝。
- 若用于剪枝，必须证明 bucket bound 是 optimistic lower bound。
- 第一版 final judge 建议少剪，先保证 correctness。

## 8. Completion Bound

建议三层：

### Level 1: Positive Cover Dual Bound

只使用未访问任务的正 cover dual：

```text
LB_tail = - sum max(0, pi_i)
```

它很弱，但安全。第一版默认只用于 ordering / audit；pruning 必须 opt-in。只有通过 Direct-DP/BPC alignment、bound-on/off consistency audit 和 profiling counter 检查后，才能升级为默认 pruning。

### Level 2: Resource Feasibility Bound

使用 lunar-specific 下界：

```text
min service time
min service energy
min route-to-task and route-back time/energy
min shadow exposure
earliest possible completion
```

用途：

- 第一版只做 audit-only / ordering-only。
- 要进入 pruning，必须先通过 consistency audit。

### Level 3: Final-Judge Frontier Bound

只有当 frontier coverage complete 且 lower bound valid 时，才能作为 no-negative proof 的一部分。

用途：

- 辅助 `CERTIFIED_NO_NEGATIVE`。
- 不能在 coverage 不完整时生成 official certificate。

任何 branch context 或 cut context 非空时，completion-bound pruning 默认关闭；除非该 bound 已证明支持对应 context。

## 9. Harvesting

Final judge 或 fast worker 找到 negative candidates 后，不直接只加 best one。

流程：

```text
candidate journeys
  -> true reduced cost filter
  -> remove exact duplicate signatures
  -> classify:
       new task set
       strong replacement
       weak replacement
  -> select by:
       would_enter_master == true
       prefer new task set
       then reduced cost strength
       cap per batch
       log task-set diversity
       log active support difference
       GAT priority as tie-breaker only
  -> add selected batch to RMP
```

MVP 中 `active_support_difference` 是 log-only 字段，不是必需选择规则。等 RMP primal support、ColumnPool addability 和 replacement semantics 稳定后，才能把 support-aware selector 升级为 opt-in 策略。

必须记录：

```text
harvest_candidate_negative_count
harvest_selected_count
harvest_selected_new_task_set_count
harvest_selected_replacement_task_set_count
harvest_rejected_overlap_count
harvest_best_true_rc
harvest_worst_selected_true_rc
harvest_avg_pairwise_jaccard
```

为什么必须第一版就做：

`BPC_future` 的 slow tail 主要不是完全找不到列，而是 final judge 反复返回少量弱/重复列。lunar 图更大、资源更多，若不 harvesting，会更容易重复这个问题。

## 10. Hidden-Negative Audit

触发条件：

```text
fast worker returned LOCAL_NO_COLUMN_UNCERTIFIED
final judge later returned FOUND_NEGATIVE
```

记录字段：

```text
node_id
cg_iter
worker_kind
hidden_task_set
hidden_sequence
hidden_path_signature
hidden_true_rc
miss_reason_guess
```

可能原因：

```text
task set not generated
path profile not generated
resource precheck too aggressive
dominance too aggressive
duplicate filter conflict
branch filter mismatch
cut reduced-cost mismatch
GAT ranking too low
```

使用方式：

- 将 hidden negative 的 task set / path signature / sortie profile 加入后续 worker seed。
- 不改变 worker no-column 语义。
- 不贡献 official certificate。

## 11. Branching

第一版使用 Ryan-Foster-style same/different journey branching。

Branch decision：

```text
same_journey(i, j)
different_journey(i, j)
```

这里的 `journey` 是一台 rover 的 multi-sortie schedule，不是单次 sortie。`same_sortie / different_sortie` 和 route-order / precedence branch 第一版不实现，只保留 diagnostic 或后续 opt-in。

选 pair：

```text
fractional_same_probability(i,j)
distance to 0.5
task mode diversity
spatial sector diversity
child pricing pressure estimate
GAT branch score
```

GAT 只排序候选 pair。

不建议第一版迁移 route-order branch，原因：

- lunar pricing 已经有三路径、shadow、充电、任务模式。
- route-order branch 会增加 pricing feasibility filter 和 dominance 复杂度。
- 先把 same/different journey exact closure 做稳。

### 11.1 Branching completeness fallback

`NO_FRACTIONAL_RF_PAIR` 不是 integrality proof。Journey master 允许同一 task set 下保留多个 route/path/timing/resource representative；如果这些列的 task-pair same/different 关系完全相同，LP 仍可能在代表列之间 fractional，而 Ryan-Foster task-pair branch 分不动。

Fallback order：

```text
1. same_journey / different_journey Ryan-Foster branch
2. if no fractional RF pair:
       branch on journey signature family / column representative / route signature
3. if still unresolved:
       branch on lambda_p variable disjunction or task-set representative choice
4. if claiming no branch is needed:
       require explicit aggregation certificate proving representative-level fractionality is harmless
```

硬规则：

```text
NO_FRACTIONAL_RF_PAIR != NODE_INTEGRAL
NO_FRACTIONAL_RF_PAIR must trigger fallback branch or aggregation certificate.
```

## 12. Cuts

第一阶段只保留 cut interface，不默认开启复杂 cuts。

MVP live cut candidate：

```text
subset row cut
```

`fleet lower-bound cut` 证明完成前只能 diagnostic-only。Journey master 中一个 selected column 是“一台 rover 的 multi-sortie schedule”，fleet 数、journey 数、sortie 数不是普通 VRP route count，不能默认套用 route-count cut。

上线前必须通过：

```text
integer validity proof
journey coefficient function
CutContextVersion
CutCoefficientVector
CutDominanceCompatibilityReport
RMP cut coefficient audit
pricing cut coefficient audit
manual reduced cost == solver reduced cost
cut dual sign audit
certificate with active cuts still exact-safe
dominance safety audit under active cut
```

启用时机：

- 5/10 BPC 与 direct baseline 对齐后。
- 20/30 出现 `lp_bound_below_incumbent` 或 wide plateau。
- pricing 已经能 close 但 node bound 不够强。

## 13. GAT 设计

### 13.1 输入图

GAT 图必须保留 directed logical graph 和 path options：

```text
node features:
    depot/task flag
    xy
    operation_mode
    science_weight
    demand
    service_time
    service_energy
    time window
    shadow/thermal indicators

directed pair features:
    source, target
    relative geometry
    pair distance
    sector relation

path option features:
    path_type
    travel_time
    energy
    risk
    shadow_exposure
    distance
```

`i -> j` 和 `j -> i` 必须分开。

### 13.2 输出头

建议三个 head：

```text
pricing_priority_head:
    task / task-set / path-option priority

branch_priority_head:
    candidate pair priority

harvest_priority_head:
    already true-RC negative candidates ordering
```

### 13.3 Admission 规则

```text
if candidate true_rc >= 0:
    reject allowed

if candidate true_rc < 0:
    GAT may mark high priority
    GAT may delay finite rounds
    GAT may not reject

before certificate:
    release or recheck all delayed negative candidates
    exact final judge must still run for no-negative proof
```

## 14. Certificate Ledger

统一输出字段：

```text
algorithm_status:
    DIRECT_DP_BASELINE_OPTIMAL
    BPC_OPTIMAL
    BPC_TIME_LIMIT
    BPC_INCOMPLETE_PRICING
    BPC_GAP_AVAILABLE
    BPC_INFEASIBLE

certificate_scope:
    DIRECT_DP_FIXED_GRAPH_OPTIMAL
    DIRECT_DP_NO_COVER
    BPC_NODE_LP_CERTIFIED
    BPC_TREE_OPTIMAL
    BPC_INFEASIBLE_CERTIFIED
    DIAGNOSTIC_RMP_BOUND
    DIAGNOSTIC_PRICING_FRONTIER
    FEASIBLE_INCUMBENT_ONLY

pricing_state:
    FOUND_NEGATIVE
    LOCAL_NO_COLUMN_UNCERTIFIED
    CERTIFIED_NO_NEGATIVE
    INCOMPLETE_LIMIT
    DUPLICATE_ONLY

uses_true_dual_bpc_certificate:
    true / false
```

实现时这些状态必须做成 enum + schema validator，而不是在脚本里手写字符串：

```text
AlgorithmStatus
CertificateScope
PricingState
BpcCertificateStatus
```

这样可以从数据结构层面防止把 `DIRECT_DP_FIXED_GRAPH_OPTIMAL`、`BPC_NODE_LP_CERTIFIED`、`BPC_TREE_OPTIMAL` 和 diagnostic evidence 混报为同一种 `optimal`。

Infeasibility 也必须有 scope：

```text
BPC_INFEASIBLE_CERTIFIED:
    only if complete pricing/column-universe coverage proves no feasible journey cover exists

DIRECT_DP_NO_COVER:
    finite fixed-graph direct-DP universe complete and no cover exists

NO_COLUMN_COVER_IN_POOL:
    restricted-pool diagnostic only; not an infeasibility certificate
```

Worker/local no-cover、restricted RMP no-cover、seeded pool no-cover 都不能推出 instance infeasible。

Node official lower bound 来源：

```text
RMP objective at node
only after true-dual final judge certifies no negative
```

Global optimal 条件：

```text
integer incumbent exists
all nodes fathomed or pruned by valid lower bound
global lower bound == incumbent within tolerance
all certificate ledgers valid
```

## 15. 实现阶段

### Phase 1: BPC Skeleton

目标：

- 新建正式 BPC module skeleton。
- 接入 journey master LP。
- 建立 column pool、reduced-cost audit、certificate ledger。
- 不启用 GAT，不启用 cuts。

验收：

```text
5-scale root RMP can solve
manual reduced cost audit passes
certificate fields distinguish baseline vs BPC
```

### Phase 2A: Minimal True-Dual Pricing Kernel

目标：

- 实现 root-only sortie/journey label kernel。
- 不启用 branch，不启用 cuts，不启用 GAT。
- 使用统一 reduced-cost 函数和 true RMP dual。

验收：

```text
one-column journey objective == direct DP journey objective
single-sortie and multi-sortie cost components match direct DP
manual reduced cost == pricing reduced cost
```

### Phase 2B: Fixed-Graph Root Closure

目标：

- 支持完整三路径、energy / shadow / ice load / recharge。
- 在固定 logical graph 上完成 root no-negative closure。
- 对齐 direct-DP 的 fixed-graph integer universe，但不要求 root LP bound 等于 integer optimum。

验收：

```text
A. Complete-column integer oracle alignment:
   full fixed-graph column-universe integer set-partition objective == direct DP objective

B. Root LP pricing closure:
   root RMP + true-dual pricing closure returns BPC_NODE_LP_CERTIFIED

C. LP-vs-IP gap audit:
   root LP bound <= direct DP integer objective
   if equal: record integral_root=true
   if not equal: branch-and-price is required for BPC_TREE_OPTIMAL
```

### Phase 2C: Branch Context Support

目标：

- same_journey / different_journey branch 进入 pricing feasibility filter。
- branch context 下 completion-bound pruning fail-closed，除非已有独立证明。

验收：

```text
branch-filtered generated columns all satisfy node constraints
manual branch-feasibility audit passes
```

### Phase 2D: Cut Context Support

目标：

- active cut dual 进入 reduced-cost function。
- cut coefficient function 同时服务 RMP、pricing、audit。
- cut context 下 completion-bound pruning 默认关闭。

验收：

```text
manual RC with active cuts == pricing RC
cut dual sign audit passes
```

### Phase 3: Harvesting and Hidden-Negative Audit

目标：

- 批量添加 true-RC negative columns。
- 记录 hidden-negative miss reason。
- seed 回 worker catalog。

验收：

```text
tail CG rounds decrease
replacement-only rounds decrease
no certificate semantics changed
```

### Phase 4: Branch-and-Price

目标：

- Ryan-Foster same/different journey branch。
- Node queue。
- Global LB/UB ledger。

验收：

```text
5/10 full exact closure
20 selected exact closure
node certificate ledger valid
```

### Phase 5: GAT Shadow and Ordering

目标：

- 构造 lunar GAT graph。
- shadow 记录 pricing/branch/harvest decisions。
- 训练后只做 ordering/admission。

验收：

```text
GAT on/off objective identical
certificate semantics identical
runtime or pricing-call count improves
```

### Phase 6: Cuts / Formulation

目标：

- 只在 LP bound 平台明显时启用。
- 添加 pricing-compatible subset row / route-aware cuts。

验收：

```text
manual reduced-cost consistency tests pass
5/10 no regression
20/30 hard cases lower bound improves
```

## 16. 风险与控制

### 风险 1: 新资源导致 dominance 错剪

控制：

- 第一版 final judge 少剪。
- 所有剪枝必须有 optimistic bound 证明。
- 与 direct baseline 对齐 5/10。

### 风险 2: GAT 污染证书

控制：

- GAT output 不进入 official lower bound。
- GAT 不 reject true-RC negative。
- certificate 前释放所有 delayed negatives。

### 风险 3: Cuts reduced-cost 口径不一致

控制：

- cut 默认关闭。
- 上线前做 RMP/pricing/manual 三方 reduced-cost audit。

### 风险 4: 20/30 tail 仍然很慢

控制：

- final judge harvesting 第一版就做。
- hidden-negative audit 第一版就记录。
- tail dual stabilization 后置，不作为第一阶段主药。

### 风险 5: 迁移 BPC_future 复杂度

控制：

- 不迁移旧巨大 driver。
- 每个组件单独有 status、audit、证书边界。
- 先做最小 BPC kernel，再逐层增加功能。

## 17. 推荐的第一步

正式实现前，先完成五件事：

1. 写 `exact/bpc/pricing/status.py` 和 `exact/bpc/certificates/certificate_ledger.py`，把状态语义和 certificate scope 固定下来。
2. 写 `exact/bpc/master/reduced_cost.py`，让 pricing、harvest、audit、manual check 共用同一个 reduced-cost 函数。
3. 写 `TaskIndexMap` 和 `ColumnPool` addability filter，禁止模块私自 `int(task_id)` 或把不可加入列当成 useful negative。
4. 写 Direct-DP / BPC objective alignment tests，先证明 5-scale root-only BPC 和 direct baseline 的 fixed-graph objective 对齐。
5. root closure 能跑后立刻接 hidden-negative + harvesting audit，不等到 full tree 才补 tail 诊断。

但本文件只是设计预构建；按当前要求，暂不开始落代码。

## 18. 自审补充：从 BPC_future 已踩过的坑反推硬约束

本节记录重新审阅 `BPC_future` 代码、报告和本设计后的补充判断。后续开始实现前必须先读本节，避免把旧项目已经暴露的问题迁移到 lunar 项目。

### 18.1 Harvesting 必须先做 addability filter

意料之外的点：

`BPC_future` 并不是没有 harvesting。它已经有 diverse harvest、support-aware harvest、mask closure 等机制，但 hard tail 里仍出现了一个核心浪费：final judge 选出很多 negative candidates，真正能进入 master 的很少。旧报告中出现过 CB 选了 `52` 个 negative candidates，但只有 `17` 个被 master 接受，其余 `35` 个在 duplicate/signature filter 后被丢弃。

因此 lunar 版 harvesting 不能只写：

```text
candidate negative -> diversity selector -> add to RMP
```

必须改成：

```text
candidate negative
  -> true reduced-cost filter
  -> branch/cut feasibility filter
  -> forbidden signature filter
  -> master addability filter
  -> diversity / min-fill / new-task-set quota
  -> add to RMP
```

硬规则：

- `harvest_selected_count` 必须表示 master-addable selected count。
- duplicate signature、forbidden signature、branch-infeasible、cut-inconsistent、会被 current dominance policy 丢掉的 column，不能计入 `min_fill`。
- replacement columns 只能作为 bounded fallback，不能占满 final judge batch。
- 必须优先选择 genuinely addable new signatures、new task sets、active-support-changing columns。

需要记录：

```text
harvest_candidate_negative_count
harvest_addable_candidate_count
harvest_duplicate_signature_count
harvest_forbidden_signature_count
harvest_branch_filtered_count
harvest_dominance_filtered_count
harvest_selected_new_signature_count
harvest_selected_new_task_set_count
harvest_selected_support_changing_count
harvest_selected_replacement_count
```

### 18.2 Task-set dominance 默认不能打开

`BPC_future` 的 `JourneyPool` 可以对同一 task set 只保留低成本 journey。这个在非常窄的条件下可以是安全的：

```text
master 只看 task cover
cuts 只依赖 task set
branch 只依赖 same/different task set
certificate path 不区分 route/order/resource representative
```

但 lunar 版更危险，因为同一个 task set 可能有不同：

- path option signature；
- route/order；
- service timing；
- energy / shadow / risk profile；
- future cut coefficient；
- GAT/harvest active-support effect。

硬规则：

```text
默认关闭 task-set dominance。
```

只有在以下条件同时成立时才允许 opt-in：

```text
no route-order branch
no resource-sensitive cuts
no time/shadow/risk/profile-sensitive cuts
dominance key covers all active cut coefficients
dominance key covers active branch signature
manual reduced-cost audit passes
direct baseline alignment passes on 5/10
```

如果 cuts 或 branch context active，column pool 的 dominance key 至少应包含：

```text
task_set
branch_signature
cut_coefficient_vector
route_order_signature if route/order-sensitive constraints exist
resource_profile_bucket only if proven safe
```

certificate path 不允许只用 task mask 证明 route/order/resource-sensitive universe。

### 18.3 Route-order branch 只能 diagnostic/opt-in，不能第一版 live

`BPC_future` 报告显示 route-order partition/formulation 有信号，finite-pool child RMP gain 可能很大。但旧报告也显示 child pricing 会继续发现强负列，且 direct certificate / completion-bound certificate 对 route-order branch fail-closed。

硬提醒：

```text
child RMP gain 大 != child 可以被 official fathom
```

lunar 第一版不启用 route-order branch。只允许：

- 写 diagnostic audit；
- 写 opt-in experiment；
- 不用于 no-negative certificate；
- 不用于 official prune；
- 不和 task-set dominance 同时默认打开。

如果未来要 live，需要先满足：

```text
route-order branch pricing support complete
completion-bound/final-judge support complete or fail-closed
task-set dominance disabled or route-order-aware
child pricing pressure decreases in probe
manual reduced-cost coefficient audit passes
```

### 18.4 不迁移复杂 tail scheduler 作为第一版默认

`BPC_future` 里一些 exact-safe 调度 gate 看起来合理，例如 flat weak column pressure、immediate reserve、tail action controller。但旧报告中已经出现过：这些开关能识别 tail pathology，却不一定缩短证明时间，有时还会推迟最终 certificate 窗口。

硬规则：

- 第一版不默认迁移复杂 tail scheduler。
- 先解决 final judge candidate addability、true-RC batch harvesting、hidden-negative seeding。
- scheduler 类开关必须通过 A/B，而不是因为 exact-safe 就默认打开。

优先级：

```text
1. addability-aware harvest
2. true-RC batch harvesting
3. hidden-negative seed
4. final proof bound strengthening
5. tail scheduler tuning
```

### 18.5 Unique-route exact-first-step bound 是优先候选

`BPC_future` 中比较值得吸收的窄优化是 unique-route exact-first-step completion bound：bucket suffix 仍然保守，但第一步 transition 用真实 time/energy 计算，再和 bucket lower bound 取更强的 valid lower bound。旧报告显示它在某些 hard root 上能把 TIME_LIMIT 推到 true-dual certificate。

lunar 版本可以迁移这个思想，但必须扩展资源：

```text
exact first step uses:
    real travel time
    real energy
    real shadow exposure
    real service time
    real service energy
    real demand increment
    real return/recharge lower-bound effect

bucket suffix remains optimistic:
    time bucket
    energy bucket
    shadow bucket if used
```

硬规则：

- exact-first-step bound 只能增强 valid optimistic lower bound。
- 如果 shadow/resource bucket coverage 不完整，不能用于 certificate，只能用于 pruning diagnostics 或 fail-closed incomplete status。
- 优先实现它，而不是优先上复杂 dual stabilization。

### 18.6 GAT delay queue 是 proof debt ledger

`BPC_future` 的 GAT admission queue 有一个正确边界：selector 永远不能 certificate；delayed true-RC negative candidate 在 certificate 前必须释放或重新检查。

lunar 版应把 GAT delay 明确视为 proof debt：

```text
GAT can delay a true-RC negative candidate.
GAT cannot make it disappear.
Before node certificate, all delayed negatives must be released or repriced.
```

建议命名：

```text
proof_debt_queue
```

必须记录：

```text
delayed_negative_count
released_before_certificate_count
rechecked_before_certificate_count
certificate_blocked_by_delayed_negative
selector_can_certificate = false
requires_exact_pricing_full_scan = true
```

GAT model 训练前就要先实现 proof debt 空壳：

```text
ProofDebtQueue.add(candidate)
ProofDebtQueue.release_all_before_certificate()
ProofDebtQueue.block_certificate_if_unreleased()
ProofDebtQueue.audit()
```

这个模块不需要等 GAT 模型可用。它的作用是先把 certificate 前的 delayed-negative 释放规则固定住，防止后续任何 selector / threshold / OOD gate 静默吞掉 true-RC negative。

### 18.7 ColumnPool 必须成为正式模块

本设计前文已经有 harvesting 和 certificate ledger，但 column pool 策略还不够明确。根据 `BPC_future` 的 duplicate/replacement 坑，lunar 版必须单独实现 `ColumnPool`。

建议接口：

```text
ColumnPool.addability_check(column, node_context) -> AddabilityReport
ColumnPool.add(column, node_context) -> AddResult
ColumnPool.forbidden_signatures(node_context) -> set
ColumnPool.dominance_policy(node_context) -> DominancePolicy
```

`AddabilityReport` 至少包含：

```text
is_new_signature
is_forbidden_signature
is_allowed_by_branch
cut_coefficients
dominance_key
would_replace_existing
would_change_active_support
would_enter_master
reject_reason
```

harvesting 必须基于 `would_enter_master=true` 的候选做 batch selection。

### 18.8 所有 pruning/bound 必须带 profiling counters

`BPC_future` 的经验说明：某个 exact-safe pruning active 了，不代表 wall time 会下降。有时 generated sequences 反而增加，或者 pruning overhead 抵消收益。

因此 lunar pricing 每个 pruning/bound 都必须记录：

```text
labels_generated
labels_extended
labels_pruned_by_resource
labels_pruned_by_time_window
labels_pruned_by_dominance
labels_pruned_by_completion_bound
labels_pruned_by_branch
bound_check_time
dominance_time
queue_time
candidate_addability_time
candidate_duplicate_count
candidate_addable_count
```

没有 profiling 的 optimization 只能作为 diagnostic，不能默认进入主线。

实现时 profiling 不是散落字段，而应是 pruning/filter 接口的一部分：

```text
PruningCounter:
    labels_generated
    labels_extended
    labels_pruned_by_resource
    labels_pruned_by_time_window
    labels_pruned_by_dominance
    labels_pruned_by_completion_bound
    labels_pruned_by_branch
    check_time_by_filter
    dominance_time
    bound_time
```

每个 bound、dominance、branch filter 都必须写入同一个 counter 对象，否则该优化只能作为 diagnostic，不允许默认开启。

### 18.9 Task id 不允许隐式 int 转换

`BPC_future` 大量逻辑使用整数 task id；lunar 当前 task id 是字符串，例如 `"001"`。如果迁移时随手 `int(task_id)`，会把 `"001"` 变成 `1`，导致：

- JSON / solution / figure node id 不一致；
- GAT node mapping 错位；
- manifest 和 solver 输出无法对齐；
- hidden-negative audit 回放失败。

硬规则：

```text
外部 task id 全程保持 string。
内部如需 bit mask，必须通过 TaskIndexMap。
```

建议：

```text
TaskIndexMap:
    external_id -> dense_index
    dense_index -> external_id
    bit_mask helpers
    stable ordering
```

任何模块不允许自行 `int(task_id)`。

### 18.10 更新后的实现优先级

原 Phase 顺序保持，但实现前增加以下硬门：

```text
Gate 0.1: status semantics fixed
Gate 0.2: TaskIndexMap fixed
Gate 0.3: ColumnPool addability fixed
Gate 0.4: reduced-cost function fixed
Gate 0.5: certificate ledger names fixed
Gate 0.6: ProofDebtQueue fixed
Gate 0.7: PathOptionUniverse / dominance audit fixed
```

然后再进入：

```text
Phase 1: BPC skeleton
Phase 2A: minimal true-dual pricing kernel
Phase 2B: fixed-graph root closure
Phase 2C: branch context support
Phase 2D: cut context support
Phase 3: addability-aware harvesting + hidden-negative audit
Phase 4: branch-and-price
Phase 5: GAT shadow/admission
Phase 6: cuts/formulation
```

后续开始落代码前，先把本节的硬规则转成 tests，而不是先写 solver driver。

## 19. 外部评审吸收与反驳：实现前必须写硬的部分

本节来自对外部评价的再审阅。总体结论：评价认为本设计方向正确，但仍偏总蓝图；这个判断接受。后续实现前，必须把模型宇宙、目标函数、pricing universe、completion bound、cut 上线合同、branch 语义、GAT 验收指标写成硬约束和测试。

### 19.1 我不同意或需要修正的事实判断

评价里提到当前项目仍是：

```text
resource_map_extent_km = 30.0
active footprint = 12 / 20 / 30 km by scale
```

这个判断已经不符合当前仓库状态。当前 lunar sp50 正式 benchmark 已经使用：

```text
resource_map_extent_km = 50.0
synthetic_grid_resolution_m = 100.0
ACTIVE_FOOTPRINT_BY_SCALE = 50 km for all scales
dense depot = [-9.90, -19.10] km
```

所以不应把文档回退到 30 km 口径。但评价背后的提醒是对的：exact claim 不能只绑定口头说法，而要绑定 instance payload / manifest。后续所有 optimal claim 必须写成：

```text
exact over the fixed resource-map payload declared by the instance manifest
exact over the fixed directed complete logical graph declared by the instance
exact over the fixed path-option set after the declared dominance policy
```

如果未来换真实 LOLA/illumination/M3/LEND 底图、换 extent、换 resolution，算法 exact 声明不需要重写，只需要 manifest schema 明确新的 fixed universe。

### 19.2 固定模型宇宙必须进入证书范围

三条路径不是求解器运行时重新寻路得到的自由变量，而是 instance 输入的一部分。BPC pricing 只能在这些已声明 path options 上选列。

硬规则：

```text
PathOptionUniverse:
    directed arc i -> j
    path option id in {low_time, low_energy, low_risk}
    fixed geometry
    fixed travel_time
    fixed energy
    fixed risk
    fixed shadow exposure
    fixed distance
```

如果启用 per-arc path-option dominance filtering，则 certificate scope 必须写清楚：

```text
FIXED_GRAPH_AFTER_MONOTONE_PATH_OPTION_DOMINANCE
```

并保留过滤审计：

```text
filtered option id
dominating option id
travel_time <=
energy <=
risk <=
shadow <=
at least one strict
```

Certificate invariant：

```text
Path-option dominance filtering may be applied only if all objective and feasibility dimensions are monotone nondecreasing in:
    travel_time
    energy
    risk
    shadow
    distance if used
```

如果未来引入 time-dependent illumination / thermal windows / science reward tradeoff，或者某个目标项让更长时间、更高 shadow、更高 risk 在某些情形下变得可取，则 path-option dominance filter 必须关闭或重新证明，不能沿用旧 certificate scope。

否则不能声称“对三路径全宇宙 exact”，只能声称“对过滤后的固定路径宇宙 exact”。

### 19.3 Objective 第一版固定为 additive journey end-time

评价指出一个关键风险：reference solution、direct-DP、journey master 可能混用不同的 completion/end-time 口径。这个提醒接受。

第一版正式 BPC objective 固定为 column-additive：

```text
min sum_p c_p lambda_p

c_p =
    alpha * completion_term_p
  + beta  * journey_end_time_p
  + gamma * risk_p
  + delta * energy_p
```

这意味着 `journey_end_time` 是对被选 journey 的 additive penalty，不是 global makespan。理由：

- column cost 可以直接进入 RMP；
- reduced cost 公式干净；
- pricing 能独立评价单个 journey；
- direct-DP / BPC objective 更容易对齐。

如果 reference solution 使用 `max(end_time)` 或 makespan 风格，它只作为 constructive heuristic / time-window helper / feasible incumbent，不作为 exact objective oracle。若未来要惩罚 global makespan，必须新增 master linking variable：

```text
z >= end_time_p * lambda_p
min ... + beta * z
```

这属于第二版 formulation，不混入第一版。

### 19.4 Pricing universe 需要 Earliest-Service Dominance Lemma

当前 lunar 模型下，路径资源不随绝对时间变化，objective 中 completion/end-time 权重非负。因此对于同一任务序列和同一路径选择，额外等待或故意晚出发不会改善 energy/risk/shadow，只会让时间项不更好。

第一版使用以下 lemma：

```text
Earliest-Service Dominance Lemma:
For a fixed sequence and fixed path-option choices,
under time-independent resource coefficients and nonnegative time penalties,
the earliest feasible schedule weakly dominates any intentionally delayed schedule.
```

因此 pricing 可以只枚举 earliest feasible service schedule：

```text
arrival = current_time + travel_time
service_start = max(arrival, ready_time)
service_end = service_start + service_time
```

但这个 lemma 有明确失效条件：

- illumination / thermal risk 变成 time-dependent；
- 某些 PSR 暴露风险随绝对时刻变化；
- recharge power 随时间变化；
- objective 对等待有负奖励；
- time window 之外存在可等待收益。

一旦引入这些特征，pricing universe 必须显式枚举 start-time candidates 或 time-dependent labels，不能沿用 earliest-only final judge。

### 19.5 Completion bound 先保守上线

三层 completion bound 保留，但上线策略改得更硬：

```text
Level 1: positive cover dual optimistic bound
    默认用于 ordering / audit
    pruning opt-in
    通过 Direct-DP/BPC alignment + bound-on/off consistency 后才能默认开启

Level 2: lunar resource feasibility bound
    第一版 audit-only / ordering-only
    通过 consistency 后才能 opt-in pruning

Level 3: final-judge frontier bound
    只能在 frontier coverage complete 且 lower-bound proof 有效时进入 official certificate
```

任何 branch context 或 cut context 非空时，completion-bound pruning 默认 fail-closed；除非该 bound 已经证明支持对应 branch/cut dual 和 feasibility filter。

### 19.6 Cut 上线合同

第一版 cut 优先级改为：

```text
subset-row cut: first candidate
fleet lower-bound cut: opt-in only with proof
```

fleet lower-bound cut 不能默认开启，因为 journey master 允许单车多 sortie，车辆数、journey 数、sortie 数之间不是普通 CVRP route count 的简单关系。

任何 cut 上线前必须满足：

```text
integer validity proof
journey coefficient function
RMP coefficient audit
pricing coefficient audit
manual reduced cost == solver reduced cost
cut dual sign audit
branch/cut context completion-bound fail-closed
dominance safety audit under active cut
```

如果 cut coefficient 依赖 route order、sortie count、resource profile 或 time profile，不能沿用只看 task set 的 dominance / duplicate / replacement 逻辑。

`fleet lower-bound cut` 在证明完成前只能 diagnostic-only；即使 opt-in，也必须先证明它在“单 rover 多 sortie journey master”下仍是 integer-valid lower-bound cut，不能套用普通 route-count 直觉。

### 19.7 Branch 语义：journey 不是 sortie

第一版 branch 使用：

```text
same_journey(i, j)
different_journey(i, j)
```

但这里的 `journey` 是一台 rover 的 multi-sortie schedule，不等于单次 sortie。

硬区分：

```text
same_journey:
    i and j appear in the same journey column

different_journey:
    i and j may not appear in the same journey column

same_sortie / different_sortie:
    not implemented in v1

route-order / precedence branch:
    diagnostic or later opt-in only
```

这样可以避免把 Ryan-Foster route branch 误解释为同一 sortie 内的顺序约束。

### 19.8 Certificate scope taxonomy

后续所有结果报告必须使用以下 taxonomy，不能只写一个笼统的 `optimal`：

```text
DIRECT_DP_FIXED_GRAPH_OPTIMAL
    finite fixed-graph direct-DP integer optimum

BPC_NODE_LP_CERTIFIED
    one branch node has RMP LP optimum and true-dual no-negative pricing certificate

BPC_TREE_OPTIMAL
    all branch nodes closed/pruned with valid bounds and incumbent matched

DIAGNOSTIC_RMP_BOUND
    restricted column pool LP bound only

DIAGNOSTIC_PRICING_FRONTIER
    incomplete or local pricing evidence

FEASIBLE_INCUMBENT_ONLY
    feasible solution without proof
```

论文和 manifest 中的 optimal count 必须按 scope 分列统计。Direct-DP optimal 可以作为 exact baseline，但不能冒充 true-dual BPC certificate。

### 19.9 Direct-DP / BPC Alignment Protocol

BPC 初期不先追 20/30 速度，先追 5/10 对齐。

每个对齐测试必须检查：

```text
same instance payload
same depot/task set
same fleet rule
same path-option dominance policy
same objective
same earliest-service assumption
same resource constraints
same journey cost
same time-window interpretation
same max_tasks_per_trip / Q_ice / B_use / shadow limit
```

第一批 tests：

```text
test_objective_same_on_one_column
test_sortie_cost_same_as_direct_dp
test_journey_cost_same_as_direct_dp
test_full_fixed_column_ip_equals_direct_dp
test_root_pricing_closure_has_no_missing_columns_5scale
test_root_lp_bound_le_direct_dp_integer_objective
```

如果 BPC objective 与 direct-DP 不一致，先分类：

```text
missing column
pricing reduced-cost bug
objective mismatch
dominance bug
path-option filtering mismatch
start-time universe mismatch
fleet/journey interpretation mismatch
```

只有 5-scale 和 selected 10-scale 对齐后，才进入 branch/cut/GAT。

### 19.10 Harvesting MVP 降低复杂度

评价建议第一版 harvesting 不要过强，这点接受。

MVP 规则：

```text
true_rc < -eps
unique full signature
would_enter_master == true
prefer new task set
then strongest reduced cost
cap per batch
log diversity metrics
```

`active support difference`、task-set replacement strength、GAT harvest head 可以保留接口，但第一版不作为必需选择规则。原因是这些策略依赖稳定的 RMP primal support、列签名和 addability 语义，过早加入会增加 tail bug 面积。

### 19.11 GAT 训练与验收必须服务 solver ROI

GAT 不只看分类指标。第一版 shadow 数据要覆盖以下 labels：

```text
observed true-RC negative found by final judge
hidden-negative miss
harvest selected / not selected
candidate addability accepted / rejected
delayed negative became proof debt / released / repriced
active support changed
child proof CPU
branch pair win/loss under same context
pricing pressure
certificate time
no-harvest CPU
```

其中两个 label 必须第一批就有：

```text
candidate_addability_label:
    final judge found candidate, ColumnPool accepted/rejected, reject reason

delayed_negative_debt_label:
    GAT delayed a true-RC negative, later released/repriced before certificate
```

原因是 GAT 不能只学习“哪里有 negative”，还要学习“这个 negative 是否能进入 master”以及“延迟后会不会变成 certificate 前的 proof debt”。

主 split 规则：

```text
split by instance / scale / seed family
random-row split cannot be the main claim
```

安全指标：

```text
false-safe rate
delayed true-negative release rate
safe precision
OOD coverage
top-K recall for final-judge negatives
```

solver ROI 指标：

```text
wall time
pricing calls
exact final-judge calls
generated labels
RMP iterations
node count
certificate time
optimal count by certificate scope
```

GAT 只有在 objective/certificate 完全一致的前提下，才讨论 wall time 或 pricing-call 改进。

GAT do-no-harm gate：

```text
with GAT guidance enabled in shadow/opt-in mode:
    objective must match no-GAT baseline
    certificate scope must match no-GAT baseline
    no true-RC negative may be permanently dropped
    proof_debt_queue must be empty before certificate
    no additional BPC_INCOMPLETE may be caused by GAT delay
```

如果 do-no-harm gate 失败，GAT 只能回到 shadow logging，不允许进入 ordering/admission 默认路径。

### 19.12 更新后的实现入口

正式落代码前按这个顺序：

```text
1. exact/bpc/pricing/status.py
2. exact/bpc/certificates/certificate_ledger.py
3. exact/bpc/master/reduced_cost.py
4. exact/bpc/core/task_index.py
5. exact/bpc/core/column_pool.py
6. exact/bpc/certificates/proof_debt_queue.py
7. guidance/typed_hints.py
8. direct-DP / BPC objective alignment tests
9. minimal true-dual root pricing closure, no branch, no cut
10. hidden-negative + addability-aware harvesting audit
```

禁止第一步就写 full tree driver。先把证书名、RC 公式、列池语义和对齐测试固定，再扩大功能面。

更硬的依赖顺序：

```text
没有 TaskIndexMap，不写 pricing label。
没有 ColumnPool addability，不写 harvest。
没有统一 reduced-cost，不写 final judge。
没有 certificate ledger，不写 tree solver。
没有 ProofDebtQueue，不接 GAT admission。
没有 PathOptionUniverse / dominance audit，不启用 path-option filtering。
```

### 19.13 第二轮外部评审吸收：branching completeness 与 do-no-harm

本轮评价基本接受，重点新增以下硬约束：

```text
1. NO_FRACTIONAL_RF_PAIR is not a proof of integrality.
2. Root LP closure is not integer optimality; direct-DP integer optimum only aligns with closed BPC tree.
3. DUPLICATE_ONLY triggers addability / RMP-membership / RC-consistency audit.
4. exact/bpc import boundary must exclude torch/checkpoints/GAT/OOD implementation.
5. MVP live cut candidate is subset-row only; fleet lower-bound remains diagnostic until proof.
6. Path-option dominance requires monotone objective/feasibility dimensions.
7. Infeasibility certificates need explicit scope; restricted-pool no-cover is diagnostic only.
8. GAT must pass do-no-harm gate before leaving shadow/opt-in mode.
```

这些约束的共同目的：防止 solver 在“没有可用 RF pair”“duplicate-only negative”“restricted pool no cover”“GAT delayed negative”这类状态下误闭证书。
