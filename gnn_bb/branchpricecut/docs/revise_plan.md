你现在是一个资深 Branch-Price-and-Cut / Column Generation / SCIP / PySCIPOpt / Gurobi / 运筹优化工程师。请在当前 `branchpricecut/` 新主线中实现一个更稳健的 Vehicle-Schedule Branch-Price-and-Cut 框架。

目标：
    保留 vehicle-schedule master：
        column = 一辆车的完整多 sortie schedule

    但修改 pricing 数学结构：
        不再把 integrated exact schedule-labeling 作为每轮 pricing 的唯一主力；
        改成：
            Layer 0: schedule column pool scan
            Layer 1: portfolio sortie route generation
            Layer 2: heuristic route-to-schedule composition DP
            Layer 3: DSSR / ng-schedule / integrated exact certificate pricing

核心原则：
    Layer 0/1/2 只能用于快速找 negative reduced-cost schedule columns；
    它们不能用于证明 no negative column；
    节点 lower bound 只能在 Layer 3 exact certificate pricing exhausted 后使用。

============================================================
A. 背景与目标
============================================================

当前新主线：

    branchpricecut/

目标模型是 Vehicle-Schedule BPC：

    x_s = 1 if complete vehicle schedule s is selected

schedule s 是：

    s = (p_1, p_2, ..., p_q)

每条 sortie route：

    p_l = 0 -> i_1 -> ... -> i_m -> 0

旧主线 `bpc/` 是 route-vehicle BPC：

    lambda[p,r] = 1 if vehicle r selects sortie route p

旧主线不是 vehicle-schedule master；旧主线中多 sortie 顺序靠 exact schedule checker、schedule no-good cuts 和 schedule capacity cuts 处理。

本次不要把 `branchpricecut/` 退回旧 route-vehicle master。本次任务是：

    保留 vehicle-schedule set-partitioning master；
    但把 pricing 内部从裸 integrated schedule-labeling 改成分层 pricing；
    重点解决 root pricing 一直卡住的问题。

请先写设计文档：

    docs/vehicle_schedule_two_level_pricing_optimized_design.md

文档需要说明：
    1. 当前 vehicle-schedule master；
    2. integrated schedule pricing 为什么容易爆炸；
    3. 新的 layered pricing 架构；
    4. Layer 1 为什么不能只按 cbar_p 取 top-M；
    5. Layer 2 为什么必须明确是 heuristic；
    6. Layer 3 才能提供 exact certificate；
    7. exactness 边界。

============================================================
B. Master 模型：支持 partitioning / covering 两种模式
============================================================

请在配置中加入：

    master_cover_mode: "partitioning"   # default
    # 可选："covering"

默认使用 set partitioning：

    min sum_{s in Ω} c_s x_s

    s.t. sum_{s in Ω} a_is x_s = 1,    for all i in I
         sum_{s in Ω} x_s <= K
         x_s in {0,1}

其中：
    Ω = 所有真实可行 complete vehicle schedules
    a_is = 1 if schedule s serves task i
    c_s = F + sum of all sortie route costs in schedule s
    K = 可用车辆数量上限

如果 master_cover_mode = "covering"，则改为：

    sum_{s in Ω} a_is x_s >= 1,    for all i in I

注意：
    covering 模式不是无条件等价。
    只有在满足以下条件时，covering integer solution 才能通过 post-processing 转成原始 partitioning 可行解：
        1. travel cost 满足 triangle inequality；
        2. travel time / energy shortcut 不增或可验证不增；
        3. 服务成本非负；
        4. 删除重复服务任务不会破坏 route / schedule feasibility；
        5. 删除重复任务后必须重新做 exact schedule feasibility check；
        6. 若存在 same/separate branching，post-processing 不得破坏 branching 约束。

实现要求：
    1. default 必须是 partitioning；
    2. covering 只作为可配置 experimental mode；
    3. covering 模式下得到 integer solution 后，必须做 duplicate task removal + shortcut + exact schedule feasibility check；
    4. 如果 post-processing 失败，该 solution 不能作为 incumbent；
    5. covering 模式的实验报告要明确标注，不要和 exact partitioning 模式混淆。

============================================================
C. Phase-I RMP 与 Phase-II 切换
============================================================

Phase-I RMP：

    min sum_i u_i

    s.t. sum_{s in Ω'} a_is x_s + u_i = 1,    for all i in I
         sum_{s in Ω'} x_s <= K
         x_s >= 0
         u_i >= 0

Phase-I 只用于恢复列池覆盖可行性。

重要规则：
    1. Phase-I dual 只能用于 Phase-I pricing；
    2. 当 Phase-I objective 达到 0 后，不能直接用 Phase-I dual 进入 Phase-II pricing；
    3. 必须切换到 Phase-II objective；
    4. 重新 solve Phase-II RMP；
    5. 重新提取 Phase-II true dual；
    6. 再运行 Phase-II pricing。

正确流程：

    solve Phase-I RMP
    if sum_i u_i == 0:
        switch objective to Phase-II
        solve Phase-II RMP
        extract Phase-II duals
        run Phase-II pricing

如果 Phase-I exact pricing exhausted 后仍有：

    sum_i u_i > tolerance

则当前节点不可行。

============================================================
D. Vehicle Lower Bound Cut 与 dual ν
============================================================

可选加入车辆数下界：

    sum_s x_s >= L_veh

其中：

    L_veh = ceil( sum_i d_i / (S_bar * Q) )

如果有更强合法下界，也可以取 max。

配置：

    vehicle_lower_bound_cut_enabled: true/false

重要注意：
    该 cut 是 schedule-level row。
    每个 schedule column 的 coefficient 是 1。
    它的 dual contribution ν 只能作为整个 schedule 的常量进入 reduced cost。
    不能把 ν 分摊到单条 route 的 cbar_p 中。
    否则一个 schedule 有多条 route 时，ν 会被重复计算。

因此：

    rc_s = c_s - sum_i a_is*pi_i - mu - nu

拆成 route contribution 时：

    rc_s = F - mu - nu + sum_{p in s} cbar_p

其中：

    cbar_p = c_p - sum_i a_ip*pi_i

ν 不进入 cbar_p。

dual 符号注意：
    sum_s x_s >= L_veh 是 >= row。
    在 PySCIPOpt / Gurobi 中，dual sign convention 可能不同。
    不要硬编码一定是 -nu 或 +nu。
    必须做 reduced-cost consistency test。

建议实现方式：
    rc_manual = obj_s - sum_over_rows(dual_row * coeff_row_s)

然后与 solver reduced cost 对比。

============================================================
E. Reduced Cost Consistency Test
============================================================

必须实现：

    check_schedule_reduced_cost_consistency(phase, num_samples=20)

对已有 RMP schedule column s：

    rc_manual = obj_s - sum_rows dual[row] * coeff[row,s]
    rc_solver = solver.getReducedCost(x_s)

检查：

    abs(rc_manual - rc_solver) <= tolerance

要求：
    1. Phase-I 通过；
    2. Phase-II 通过；
    3. 启用 vehicle lower-bound cut 时通过；
    4. partitioning / covering 模式均通过；
    5. branching rows 若存在，也必须进入 manual reduced cost；
    6. 任何 cut row 若存在，也必须进入 manual reduced cost。

不要在 reduced cost 一致性测试没通过时继续实现 pricing 优化。

============================================================
F. Route Reduced Contribution
============================================================

对于 Phase-II：

    cbar_p = c_p - sum_i a_ip * pi_i

对于 Phase-I：

    cbar_p_I = - sum_i a_ip * pi_i

schedule reduced cost：

    Phase-II:
        rc_s = F - mu - nu + sum_{p in s} cbar_p

    Phase-I:
        rc_s_I = - mu - nu + sum_{p in s} cbar_p_I

注意：
    mu 和 nu 是 schedule-level constants；
    不进入 route cbar_p；
    cbar_p 只包含 route 自身 cost 和任务 dual contribution。

============================================================
G. Layer 0：Schedule Column Pool Scan
============================================================

每轮 RMP solve 后，先扫描历史 schedule column pool。

For each schedule s in pool:
    recompute true reduced cost under current true dual
    if rc_s < -epsilon and s not in current RMP:
        add s to RMP

规则：
    1. pool scan 只用于找列；
    2. pool scan 找不到列不能证明 no negative column；
    3. 所有 pool columns 必须是完整真实可行 schedule；
    4. 加入前必须用当前 true dual 重新计算 reduced cost；
    5. schedule signature 去重。

配置：
    schedule_column_pool_enabled: true
    max_schedule_pool_size: 100000

============================================================
H. Layer 1：Portfolio Sortie Route Generation
============================================================

不要使用危险策略：

    P_pool = top-M routes by cbar_p

这是过于贪心的。因为一条 cbar_p > 0 的微型 route 可能：
    1. 耗时极短；
    2. 时间窗灵活；
    3. 能补全 same component；
    4. 能塞进两个主 sortie 之间的碎片时间；
    5. 有助于构造整体 negative schedule。

Layer 1 应该生成 portfolio route pool：

    P_pool =
        low_cbar_routes
      ∪ per_task_routes
      ∪ route_size_buckets
      ∪ time_flexible_routes
      ∪ micro_routes
      ∪ branch_relevant_routes
      ∪ historical_useful_routes
      ∪ diverse_routes

具体要求：

1. low_cbar_routes:
    保留 cbar_p 最小的 top-M_neg routes。

2. per_task_routes:
    对每个任务 i，保留覆盖 i 的 top-L routes。
    防止某些任务在 route pool 中完全缺失。

3. route_size_buckets:
    分别保留：
        single-task routes
        two-task routes
        three-task routes
        multi-task routes

4. time_flexible_routes:
    保留 duration 短、time slack 大、可插入性强的 routes。

5. micro_routes:
    保留耗时很短的 routes，即使 cbar_p 轻微为正。

6. branch_relevant_routes:
    如果当前节点存在 same / separate constraints，
    必须保留与 same components 补全相关的 routes。

7. historical_useful_routes:
    保留过去几轮出现在 negative schedules 或 near-negative schedules 中的 routes。

8. diverse_routes:
    按 covered task set、route length、time window cluster 做多样性筛选。

配置建议：

    route_pool_pricing_enabled: true
    max_routes_in_pricing_pool: 2000
    max_new_routes_per_pricing_round: 1000
    low_cbar_route_quota: 500
    per_task_route_quota: 20
    micro_route_quota: 200
    branch_relevant_route_quota: 300
    historical_route_quota: 300
    diverse_route_quota: 300

注意：
    Layer 1 是 heuristic route pool generator。
    如果 P_pool 不完整，则后续 Layer 2 找不到 negative schedule 不能证明 no negative column。

============================================================
I. Layer 1 必须处理 branching constraints
============================================================

必须把 branching constraints 传入 Layer 1 route generation。

1. separate(i,j):

    如果当前节点有 separate(i,j)，则任何 route p 若同时包含 i 和 j，必须在 Layer 1 被 reject。

    if route_contains(i) and route_contains(j):
        reject route p

2. separate between same components:

    如果 component A 和 component B 被 separate，
    则任何 route p 若同时包含 A 中任务和 B 中任务，必须 reject。

3. same(i,j):

    same(i,j) 不代表单条 route 必须同时包含 i,j。
    它只要求同一个 complete schedule 要么同时包含 i,j，要么都不包含。
    因此 Layer 1 不应简单 reject “只含 i 不含 j” 的 route。
    这类 partial route 应保留给 Layer 2 组合；
    但是要在 route metadata 中标记它覆盖了哪些 same component 的哪些任务。

4. arc / route-level branch constraints:
    如果已有 arc-off / arc-on 等约束，必须继续在 Layer 1 route generation 中执行。

============================================================
J. Layer 2：Heuristic Route-to-Schedule Composition DP
============================================================

Layer 2 是 heuristic，不是 exact proof layer。

输入：
    P_pool
    cbar_p
    schedule-level constant F - mu - nu
    branching constraints
    S_bar
    H
    rho
    final_recovery_required

输出：
    top-K negative complete feasible schedules

Label:

    L = (
        covered_task_bitset,
        used_sorties,
        ready_time,
        contribution,
        route_sequence,
        branch_state
    )

其中：
    covered_task_bitset = 已覆盖任务集合
    used_sorties = 已使用 sortie 数
    ready_time = 当前车辆 ready time
    contribution = sum cbar_p
    route_sequence = 已选 route 序列
    branch_state = same components 的 partial coverage / pending obligations

扩展 route p 条件：
    A(p) ∩ covered_task_bitset = empty
    used_sorties + 1 <= S_bar
    Phi_p(ready_time) < infinity
    horizon check satisfied
    branching constraints satisfied:
        separate components cannot co-exist
        same components must be either completed eventually or remain absent

完整 schedule reduced cost：
    rc_s = F - mu - nu + contribution

如果 rc_s < -epsilon：
    add as candidate negative schedule

============================================================
K. Layer 2 Dominance：使用 subset dominance + branch state
============================================================

不要只使用：

    covered_1 == covered_2

这太弱，任务多时几乎没有 dominance。

可使用更强但仍需谨慎的 subset dominance。

Label L1 dominates L2 if:

    covered_1 ⊆ covered_2
    used_sorties_1 <= used_sorties_2
    ready_time_1 <= ready_time_2
    contribution_1 <= contribution_2
    branch_state_1 is no more restrictive than branch_state_2

为了实现简单，第一版可以保守地要求：

    branch_state_1 == branch_state_2

再使用 subset dominance。

重要安全规则：
    1. empty/root label 不允许通过 subset dominance 支配非空 label；
    2. same component pending 状态必须纳入 branch_state；
    3. 若无法判断 branch_state no-more-restrictive，则要求 branch_state exactly equal；
    4. 如果实现复杂，Layer 2 可以使用 heuristic beam pruning，但不得作为 exact proof。

============================================================
L. Layer 2 Beam / Width Control
============================================================

即使在 route pool 上，covered_task_bitset 仍可能造成 2^n 爆炸。

Layer 2 必须显式支持 heuristic search width control：

配置：
    schedule_dp_max_labels: 200000
    schedule_dp_beam_width: 5000
    schedule_dp_max_labels_per_bucket: 5
    schedule_dp_time_bucket_size: 10
    schedule_dp_enable_subset_dominance: true
    schedule_dp_enable_beam_pruning: true

推荐 bucket：

    bucket = (
        used_sorties,
        floor(ready_time / time_bucket_size),
        covered_count,
        branch_state_hash
    )

每个 bucket 只保留 contribution 最小的 top-B labels。

注意：
    beam pruning 会丢失潜在 columns；
    因此 Layer 2 一旦使用 beam pruning，必须标记：
        route_pool_dp_exhausted = false
    找不到列时必须进入 Layer 3 exact certificate。

============================================================
M. Layer 2 Top-K Negative Schedule Return
============================================================

Layer 2 不要只返回一个 schedule。

配置：
    max_negative_schedules_per_pricing: 20

返回 top-K negative schedules。

Diversity filtering：
    1. 相同 covered_task_bitset 只保留 reduced cost 最小的 schedule；
    2. 相同 route_sequence signature 只保留一次；
    3. Jaccard 相似度过高的 schedules 限制数量；
    4. 每轮最多添加 max_negative_schedules_per_pricing 条。

所有 schedule 加入 RMP 前：
    1. 必须是完整 feasible schedule；
    2. 必须满足 all branching constraints；
    3. 必须用 true dual 重新计算 reduced cost；
    4. rc_s < -epsilon 才能加入。

============================================================
N. Layer 3：Exact Certificate Pricing
============================================================

Layer 0/1/2 都不能证明 no negative column。

当 Layer 0/1/2 找不到 negative schedule 时，必须调用 Layer 3。

Layer 3 可以是：
    1. DSSR / ng-schedule exact certificate；
    2. integrated exact schedule-labeling fallback。

当前如果 DSSR 暂时未实现，必须调用 integrated exact schedule pricing fallback。

规则：
    if Layer 3 finds negative schedule:
        add columns and re-solve RMP
    elif Layer 3 exhausted and best_rc >= -epsilon:
        pricing_complete = true
    else:
        pricing_complete = false
        node lower bound cannot be used for proof

配置：
    exact_pricing_fallback_enabled: true
    max_labels_per_exact_pricing: 0   # 0 means unlimited
    exact_pricing_required_for_certificate: true

如果 max_labels_per_exact_pricing > 0 且未 exhausted：
    不能证明该节点完成。

============================================================
O. DSSR / ng-Schedule 预留接口
============================================================

设计接口：

    class DSSRSchedulePricing:
        def run(node, duals, branch_constraints):
            ...
            return PricingResult(
                columns=[],
                exhausted=True/False,
                certificate=True/False,
                best_rc=...
            )

DSSR 思路：
    1. relaxed schedule set Ω_tilde(M) 满足 Ω ⊆ Ω_tilde(M)；
    2. relaxed pricing 若证明 min rc >= -epsilon，则 exact certificate 成立；
    3. 若找到 negative elementary schedule，则加入；
    4. 若找到 negative non-elementary schedule，则识别重复任务并扩大 memory；
    5. 最坏情况下 memory 变成 full visited set。

第一版可以只实现 placeholder，fallback 到 integrated exact pricing。

============================================================
P. Branching: schedule-level Ryan-Foster
============================================================

保留 schedule-level Ryan-Foster branching。

定义：

    z_ij = sum_{s: i and j both covered by s} x_s

若 0 < z_ij < 1，则生成：

    same(i,j)
    separate(i,j)

same(i,j):
    schedule s 必须满足：
        a_is = a_js

separate(i,j):
    schedule s 必须满足：
        a_is + a_js <= 1

实现 same components：
    使用 union-find 维护 same components。

对每个 same component C：
    schedule 必须：
        cover none of C
    or
        cover all of C

separate 应提升到 component 层：
    如果 component A 与 component B separate，
    则 schedule 不能同时覆盖 A 和 B。

Layer 1:
    separate constraints 必须过滤 route。
    same constraints 不应错误过滤 partial route。

Layer 2:
    必须跟踪 same component partial coverage / pending obligations。

Layer 3:
    必须再次完整 enforce all branching constraints。

不要 branch on schedule variable x_s。
不要使用 schedule-variable branching 作为 fallback。

============================================================
Q. Pricing Flow
============================================================

每个 BPC 节点 pricing 流程：

    solve Phase-I or Phase-II RMP
    extract true duals

    run reduced-cost consistency check in debug mode

    Layer 0: schedule column pool scan
    if negative columns found:
        add columns
        continue

    Layer 1: portfolio sortie route generation
    Layer 2: heuristic route-to-schedule DP
    if negative schedules found:
        add top-K columns
        continue

    Layer 3: exact certificate pricing
    if negative schedules found:
        add columns
        continue
    elif exhausted:
        pricing_complete = true
    else:
        pricing_complete = false

    if pricing_complete:
        node lower bound may be used
    else:
        node cannot be certified complete

============================================================
R. Tests
============================================================

请新增以下测试：

1. Reduced cost consistency test:
    existing schedule columns:
        manual rc == solver rc

2. Phase-I to Phase-II test:
    Phase-I reaches objective 0；
    switch to Phase-II；
    re-solve RMP；
    ensure Phase-II duals are extracted；
    ensure Phase-I duals are not reused。

3. Vehicle lower-bound dual sign test:
    enable vehicle LB cut；
    compare manual and solver rc；
    verify correct sign.

4. Layer 1 separate filtering test:
    separate(i,j) active；
    route containing both i and j must be rejected in route generation。

5. Layer 1 portfolio test:
    route pool must include:
        low-cbar routes
        per-task routes
        micro routes
        branch-relevant routes
        historical routes if available

6. Layer 2 subset dominance test:
    L1 covered subset of L2；
    resources no worse；
    contribution no worse；
    branch_state equal；
    L1 dominates L2。
    Empty label must not dominate non-empty label.

7. Layer 2 beam pruning test:
    if beam pruning is used:
        route_pool_dp_exhausted must be false；
        failure to find column must trigger Layer 3.

8. Partitioning / covering mode test:
    partitioning default；
    covering mode requires duplicate-removal post-processing；
    post-processing result must pass exact schedule feasibility check。

9. Tiny full enumeration test:
    n <= 7；
    enumerate all feasible schedules；
    solve full master LP；
    run CG；
    compare LP objective.

10. Branching coverage test:
    parent schedules = same schedules ∪ separate schedules；
    intersection empty.

============================================================
S. Logging
============================================================

新增日志字段：

    master_cover_mode
    phase
    phase_switch_count

    manual_rc_check_max_error

    vehicle_lb_cut_enabled
    vehicle_lb_dual_effective_value

    pool_scan_columns_found
    pool_scan_time

    route_pool_size
    low_cbar_routes_kept
    per_task_routes_kept
    micro_routes_kept
    branch_relevant_routes_kept
    historical_routes_kept
    diverse_routes_kept

    schedule_dp_labels_created
    schedule_dp_labels_pruned_by_subset_dominance
    schedule_dp_labels_pruned_by_beam
    schedule_dp_exhausted
    schedule_dp_negative_schedules_found
    schedule_dp_best_rc
    schedule_dp_time

    exact_pricing_called
    exact_pricing_exhausted
    exact_pricing_best_rc
    exact_pricing_time

    pricing_certificate_layer

============================================================
T. 不要做的事情
============================================================

本次不要做：
    - 2LBB；
    - ML branching；
    - new cut families；
    - route-vehicle master conversion；
    - schedule no-good cuts；
    - pairwise route incompatibility cuts；
    - clique cuts；
    - compact MILP reformulation。

本次只做：
    1. vehicle-schedule master consistency；
    2. partitioning / covering configurable mode；
    3. Phase-I to Phase-II correct dual transition；
    4. reduced-cost consistency tests；
    5. vehicle lower-bound dual handling；
    6. Layer 0 pool scan；
    7. Layer 1 portfolio route generation；
    8. Layer 1 branching filtering；
    9. Layer 2 heuristic route-to-schedule DP；
    10. subset dominance + beam pruning；
    11. Layer 3 exact certificate fallback；
    12. schedule-level Ryan-Foster component propagation；
    13. tiny enumeration tests。

============================================================
U. Exactness Requirements
============================================================

必须严格遵守：

1. Master column must be a complete feasible vehicle schedule.
2. Layer 0 pool scan is heuristic for finding columns only.
3. Layer 1 route pool is heuristic unless proven complete.
4. Layer 2 route-to-schedule DP is heuristic if beam pruning or incomplete route pool is used.
5. Only Layer 3 can certify no negative reduced-cost schedule.
6. Node lower bound can be used only after Layer 3 exact pricing exhausted.
7. If exact pricing hits max_labels and is not exhausted, node cannot be certified complete.
8. All generated schedules must satisfy all branching constraints.
9. separate(i,j) must be enforced in Layer 1 route generation.
10. same(i,j) must be enforced at schedule level via component completion.
11. ν from vehicle lower-bound cut is schedule-level constant and must not be distributed into route cbar_p.
12. Phase-I duals must not be reused for Phase-II pricing.
13. Reduced cost must match solver reduced cost on existing columns.
14. Covering mode incumbents require duplicate-removal post-processing and exact feasibility recheck.

============================================================
V. 最终交付
============================================================

请交付：

1. 修改后的 `branchpricecut/` 代码；
2. 设计文档：
       docs/vehicle_schedule_two_level_pricing_optimized_design.md
3. 测试文档：
       docs/vehicle_schedule_pricing_tests.md
4. reduced-cost consistency tests；
5. Phase-I / Phase-II dual transition tests；
6. Layer 1 portfolio route pool implementation；
7. Layer 2 heuristic schedule DP implementation；
8. Layer 3 exact fallback integration；
9. 日志字段和 CSV 输出；
10. tiny instance enumeration validation。

最终目标：
    形成一个论文级 vehicle-schedule BPC 框架：

        vehicle-schedule set-partitioning master
        + portfolio route-pool heuristic pricing
        + heuristic route-to-schedule composition
        + DSSR / integrated exact pricing certificate
        + schedule-level Ryan-Foster branching

核心原则：
    快速找列靠 Layer 0/1/2；
    数学证明靠 Layer 3；
    不允许 heuristic 层证明 lower bound。

    bench_20_01

============================================================
W. 2026-05-19 当前 bpc_clean 主线补充备注
============================================================

本轮没有切换到 vehicle-schedule master，也没有做 learning to cut。当前只在根目录 `bpc/` 的 route-vehicle BPC with schedule cuts 主线上加入一个受控的 LP schedule incompatibility separator。

新增内容：

1. 对同一车辆 LP 支撑 route 做 exact transition check；
2. 若两条 route `p->q` 与 `q->p` 都不可行，且当前 LP 违反，则加入：

       lambda[p,r] + lambda[q,r] <= y[r]

3. 若一组 route 两两双向不可排程，且当前 LP 违反，则加入：

       sum_{p in K} lambda[p,r] <= y[r]

4. `|K|>=3` 的 cut 记录为 `schedule_clique_conflict`；
5. 新增统计字段 `schedule_clique_conflict_cuts_added` 和 benchmark log metric。

有效性依据：

同一车辆的 sortie 必须存在先后顺序。若两条 route 从时间 0 开始任一先后顺序都不可行，则更晚开始不会使其可行，因此它们不能同时属于同一辆车。pairwise clique 中任意两条都不能共存，所以整组最多选择一条。

该 separator 只在完成 exact pricing certificate 后运行；候选 clique 的构造是启发式，但 cut 的加入由 exact transition check 和 LP violation 决定，不影响最优性证明。

============================================================
X. 2026-05-19 route-set schedule packing cut 补充
============================================================

继续保留当前 `bpc_clean` route-vehicle master，不切回现有 vehicle-schedule master。原因是现有 vehicle-schedule master 的 pricing certificate 在 20 规模上过慢；当前优化目标是在 route-vehicle master 中补强 schedule lower bound。

新增高阶 route-set schedule packing cut：

给定同一车辆的一组 route：

    C = {p_1, ..., p_m}

用 exact schedule DP 计算：

    U(C) = 同一辆真实车辆最多能从 C 中排程多少条 route

若当前 LP 违反：

    sum_{p in C} lambda[p,r] <= U(C)y[r]

则加入正式 cut：

    schedule_route_set_packing

精确性边界：

1. 候选 C 的生成是启发式，只决定尝试哪些 route 集合；
2. RHS 中的 U(C) 必须由 exact_route_set_schedule_capacity 给出；
3. exact DP 同时考虑 ready time 串接、horizon 和 S_bar；
4. 若 oracle 超过状态上限，则返回 None，不加 cut；
5. 因此不会用启发式上界删除任何原问题可行解。

该 cut 是 pair / clique / no-good 的统一加强版：

    pair conflict:        |C|=2, U(C)=1
    clique conflict:      |C|>=3, U(C)=1
    integer no-good:      U(C)<=|C|-1
route-set packing:    1<=U(C)<|C|

============================================================
Y. 2026-05-19 route-pack skip 诊断补充
============================================================

补充 `route_set_schedule_packing_diagnostics` 日志事件，用于解释 route-pack separator 为什么没有加 cut 或只加了很少 cut。该事件只记录诊断信息，不改变模型、约束、定价或证明逻辑。

主要字段：

    candidate_sets
        本轮生成的 route 集合候选数量。

    oracle_queries
        查询 exact route-set schedule bound 的次数，可能命中缓存。

    skipped_oracle_incomplete
        exact oracle 超过状态上限或未能证明，直接跳过，不加 cut。

    skipped_not_tight
        oracle 得到 U(C)>=|C|，该候选没有形成更紧的 schedule packing 约束。

    skipped_not_violated
        cut 有效但当前 LP 没有超过 violation 阈值。

    skipped_duplicate
        候选与已有 cut 或本轮已收集候选重复。

    violated_candidates / added
        exact oracle 证明且 LP 违反的候选数量，以及本轮实际加入 cut 数。

    max_violation / oracle_states_max
        最大 LP 违反量和单个候选最大 exact DP 状态数。

使用方式：

    如果 not_tight 很高，优先改候选集合生成；
    如果 not_violated 很高，说明该 family 对当前 LP bound 帮助有限；
    如果 oracle_incomplete 很高，再考虑缩小候选或优化 exact route-set DP。

============================================================
Z. 2026-05-20 no-good purge 与 schedule-cap/RIM 诊断
============================================================

背景：

    最新 bench_20_02 / bench_20_03 输出显示：
    cut 总数明显增加，但 diagnostic dual 只小幅提升。
    膨胀主因不是 route-pack，而是 schedule_nogood_core。

本轮修改：

1. 增加弱 no-good purge。

   只清理：

       schedule_nogood
       schedule_nogood_core
       schedule_nogood_full

   不清理：

       schedule_pair_conflict
       schedule_clique_conflict
       schedule_route_set_packing

   默认参数：

       schedule_nogood_purge_enabled: true
       schedule_nogood_purge_age: 8
       schedule_nogood_purge_slack: 1.0e-4
       schedule_nogood_purge_dual: 1.0e-8

   精确性边界：

       删除已加入的有效 cut 只会放松 LP；
       RMP 和 pricing 使用同一套 active cut；
       因此不会错误剪掉原问题可行解。

2. 增加 schedule-capacity skip 诊断。

   新日志事件：

       schedule_capacity_diagnostics

   重点字段：

       candidate_subsets
       oracle_queries
       skipped_oracle_incomplete
       skipped_not_tight
       skipped_not_violated
       violated_candidates
       added
       max_violation
       oracle_states_max

3. 增加 RIM 冲突回流诊断。

   新日志事件：

       rim_conflict_diagnostics

   重点字段：

       conflicts_checked
       pair_cuts_added
       schedule_capacity_cuts_added
       nogood_cuts_added
       weak_nogood_not_violated

下一步判断规则：

    如果 no-good 被大量加入又大量 purge，说明局部 no-good 不应继续加强；
    如果 schedule-cap not_tight 高，优先改候选集合；
    如果 schedule-cap oracle_incomplete 高，优先改 oracle；
    如果 RIM 仍主要回流 no-good，下一步应做更强 schedule-capacity certificate、route pool 上界构造或可证明的一车目标下界。

============================================================
AA. 2026-05-20 fixed-cost-aware 初始 incumbent
============================================================

背景：

    重新检查 bench_20_02 / bench_20_03 后发现，当前结果里
    primal_bound 约 329~333，并不是因为一辆车不可行。
    相反，同一实例存在一辆车多 sortie 的真实可行解。
    因此不能安全加入 sum_r y_r >= 2。

问题：

    初始贪心在选择候选插入时主要看 route cost，
    没有把开启新车辆带来的 F y_r 固定成本计入增量目标。
    这会让构造启发式偏向“两辆车、短路线”，即使“一辆车、多 sortie”
    的总目标更低。

本轮修改：

1. _best_greedy_insertion 的候选 score 改为 fixed-cost-aware delta objective。

       插入已有车辆：
           delta = route cost 增量

       给空车辆开新 route：
           delta = route cost + F

2. initialize 阶段新增 serial_schedule incumbent。

       按时间窗顺序把任务串成同一车辆的多条 sortie；
       每条 route 和整车 route set 都必须通过 exact schedule check；
       通过后加入 route pool 并更新 incumbent。

3. 较慢的 greedy improvement 只有在原始构造目标有机会优于当前 incumbent 时才运行。

精确性：

    这些改动只影响 primal heuristic 和初始 route pool。
    lower bound 仍只来自 RMP + true-dual exact pricing + valid cuts。
    因此不会破坏 exactness。

============================================================
AB. 2026-05-21 conflict-induced route-set packing 回流
============================================================

背景：

    bench_20_02 / bench_20_03 的完整输出显示：
    fixed-cost-aware incumbent 已经把 primal gap 从约 30% 降到 3%~5%，
    但 dual bound 几乎没有同步提升。
    运行后半段大量时间花在 restricted-MIP 找到排程不可行整数候选、
    加 schedule_nogood_core、再被 purge 的循环上。

问题：

    当前代码已经有 schedule_route_set_packing cut：

        sum_{p in C} lambda[p,r] <= U(C) y[r]

    其中 U(C) 由 exact_route_set_schedule_capacity 证明。
    但 RIM 回流和整数解校验遇到不可排程 core 时，
    没有先尝试这类高阶 route-set 上界，
    而是从 task-level schedule-capacity 失败后直接退到 schedule_nogood_core。

本轮修改：

1. 新增 _add_schedule_route_set_packing_conflict_cuts()。

       输入原始不可排程整数解中的 full route set C；
       调用 exact_route_set_schedule_capacity(C)；
       若 U(C)<|C|-1，对所有同质车辆加入严格强于 no-good 的 schedule_route_set_packing cut；
       若 oracle 超限、U(C)>=|C|，或 U(C)=|C|-1 只等价于普通 no-good，则不提升为 route-pack conflict。

2. RIM 回流顺序改为：

       pair conflict
       route-set schedule packing conflict
       task-level schedule-capacity conflict
       LP-violated schedule_nogood_core

3. integral validation 顺序同样改为：

       pair conflict
       route-set schedule packing conflict
       schedule-capacity conflict
       schedule_nogood_core
       schedule_nogood_full

4. restricted-MIP 内部临时 cut 顺序也同步加入 route-set packing。

       这样 RIM 在排除同一个不可排程整数候选时，
       优先用严格强于 no-good 的 U(C) 上界；若 U(C)=|C|-1，则直接回退到 schedule-capacity / no-good。

5. 增加冲突缓存与日志字段。

       schedule_conflict_witness_cache:
           缓存不可排程 route set 的 witness；

       route_set_schedule_packing_cache:
           缓存 exact_route_set_schedule_capacity 的 U(C) 结果；

       schedule_route_set_packing_conflict_diagnostics:
           记录 route_count、upper_bound、oracle_complete、oracle_states、
           cache_hit 和 added。

补充修正：

    bench_20_02 的实际输出显示，大量 minimal-core conflict route-pack 都是
    routes=3,U=2 或 routes=4,U=3，即 U(C)=|C|-1。
    这类 cut 与普通 no-good 同强度，但之前会对所有车辆加入，
    导致 root cut 数迅速膨胀而 bound 仍停在 228.39887。

    因此当前实现把 conflict route-pack 的提升条件收紧为
    U(C)<|C|-1，并在 RIM 中用 full route set 计算 route-pack，
    pair / schedule-capacity / no-good fallback 仍使用 deletion-minimal core。
    同时增加 restricted_master_route_pack_conflict_max_events 作为每次
    RIM 回流的安全预算。该修正不改变 exactness，只改变 valid cut 的选择策略。

精确性：

    route-set packing 的有效性完全来自 exact DP 证明的 U(C)。
    候选 C 来自启发式或整数不可行 witness，只决定试哪个集合；
    状态超限时不加 cut。
    因此该修改不会删除任何原问题可行解，也不会改变 node bound 证书条件。

============================================================
AC. 2026-05-21 成本型 schedule 下界与 subset-row cut
============================================================

背景：

    route-pack conflict 的实际输出显示，大量 cut 是 routes=3,U=2
    或 routes=4,U=3，本质接近普通 no-good，cut 数增加但 root bound
    基本不动。schedule-capacity 诊断也显示大量候选 not_tight。

判断：

    继续增加局部 no-good、route-pack conflict 或 purge 规则，
    不能真正推进 lower bound。当前 route-vehicle master 缺的是
    “同一车辆服务某个任务集合时，真实排程成本至少是多少”的成本信息。

本轮修改：

1. 新增 subset-row cut。

       sum_{p,r} floor(|p∩S|/k) lambda[p,r] <= floor(|S|/k)

   这是标准 VRP set-partitioning 强化 cut，候选 S 来自当前 LP
   支撑 route 的任务集合和小规模 route union，默认 k=2,3。

2. 新增 schedule subset cost lower-bound cut。

       z[i,r] = sum_p a[i,p] lambda[p,r]

       sum_p c[p] lambda[p,r]
         - L(S) sum_{i in S} z[i,r]
         + L(S)(|S|-1)y[r] >= 0

   其中 L(S) 是一辆车真实多 sortie schedule 完整服务 S 的变量成本下界。
   当前用 exact_schedule_subset_cost() 小规模 DP 精确求 L(S)。
   oracle 超限、未完成或证明 S 单车不可行时不加 cut。

3. pricing reduced cost 同步支持新 cut。

       subset-row route coefficient:
           floor(|p∩S|/k)

       schedule cost route coefficient:
           c[p] - L(S)|p∩S|

   因为成本型 cut 的系数包含 c[p]，当这类 cut 的 dual 非零时，
   第一版 exact pricing 暂停 dominance，避免旧 label score 漏掉负 reduced-cost route。

4. 新增诊断和统计字段。

       subset_row_diagnostics
       schedule_subset_cost_diagnostics
       subset_row_cuts_added
       schedule_subset_cost_cuts_added

精确性：

    subset-row 是整数 set-partitioning 的 valid inequality。
    schedule subset cost cut 的 L(S) 必须由 exact oracle 证明；
    候选 S 只决定尝试哪个 cut，不参与证明。
    若 oracle 不完整则跳过，因此不会把启发式估计写成证书。

2026-05-21 实测更新：

    bench_20_02 中 subset-row 加入 17 条 cut，root bound 从 228.398870
    抬到约 228.655122，有小幅正收益，应保留默认启用。

    schedule subset cost cut 做了 1620 次 exact oracle 查询，但 violated=0、
    added=0，没有产生任何有效 cut，且消耗明显时间。因此当前默认关闭
    schedule_subset_cost_cuts_enabled，只把代码保留为实验项。

后续方向：

    若要重新启用成本型 schedule 下界，必须先重写候选生成，让候选 S
    来自当前 LP 的真实成本低估结构，而不是盲目枚举高活动任务集合。
    在此之前，论文级 baseline 不应承担这部分 oracle 开销。

============================================================
AD. 2026-05-21 关闭 LP schedule-capacity，加入 lm-rank-1 第一版
============================================================

背景：

    subsetrow_only 运行显示，bench_20_02 的 gap 改善主要来自 primal upper
    bound，不是 lower bound 质变；bench_20_03 的 dual 基本不动。
    同时 LP 层 schedule-capacity separator 在 bench_20_02/03 中做了大量
    oracle 查询但 added=0。

修改：

1. 默认关闭 LP 层 schedule-capacity separator。

       schedule_capacity_separation_enabled: false

   注意：schedule_capacity_cuts_enabled 仍为 true。RIM 回流和整数解校验中的
   schedule-capacity conflict fallback 继续保留，只是不再每个 LP 节点主动枚举
   大量 schedule-capacity 候选。

2. 新增 limited-memory rank-1 cut 第一版。

       sum_{p,r} floor((sum_{i in S} m_i a_ip) / d) lambda[p,r]
           <= floor((sum_{i in S} m_i) / d)

   其中 d 默认取 3 和 4，m_i 是 1 到 d-1 的整数 multiplier。
   普通 subset-row 是所有 m_i=1 的特例；lm-rank1 允许小 memory 内部分任务
   使用更高 multiplier，尝试捕捉普通 subset-row 抓不到的 fractional pattern。

3. pricing reduced cost 同步支持 lm-rank1。

       route coefficient = floor((sum_{i in route∩S} m_i) / d)

精确性：

    lm-rank1 是 set-partitioning cover 等式的 rank-1 CG rounding。
    memory 只限制候选 multiplier pattern，不参与有效性证明。
    pricing 对 route 系数精确计算，不使用估计。

风险：

    第一版 multiplier pattern 仍是启发式候选生成，可能加到的 cut 数有限。
    若 bench_20_02/03 lower bound 仍不明显提升，下一步应增强 rank-1 cut
    separation 或转向更强的 full schedule column / extended master，而不是恢复
    LP schedule-capacity oracle。

============================================================
AE. 2026-05-21 全 route-space exact schedule pricing 第一版
============================================================

背景：

    candidate-pool schedule-pack CG 在 bench_20_02 root 上给出比 route-vehicle
    master 明显更高的 schedule-pack 诊断值，但它只在有限候选 route 集合内收敛，
    不能作为全局 lower bound 证书。

修改：

1. `solve_schedule_pack_node_relaxation()` 新增全 route-space pricing 开关：

       schedule_pack_full_pricing_enabled
       schedule_pack_full_pricing_max_depth
       schedule_pack_full_pricing_max_states

2. 当候选 route 集合内无负 reduced-cost schedule column 后，若 full pricing
   开启，则对每辆车运行 integrated full route-space schedule pricing。

3. full pricing 不再先枚举当前分支节点下全部 elementary sortie route，而是在
   schedule label 扩展时生成下一条可行 sortie route。schedule label 状态包含：

       已覆盖任务集合
       已用 route 数
       车辆 ready time
       当前 reduced component

   若发现负 reduced-cost schedule，则把新 route 和 schedule column 加回
   vehicle-indexed schedule-pack LP，并重新求解。

4. 日志与 CSV 增加：

       exact_over_full_route_space
       full_pricing_route_count
       full_pricing_generated_states
       full_pricing_time
       schedule_pack_relaxation_full_exact
       schedule_pack_relaxation_full_pricing_states
       schedule_pack_relaxation_full_pricing_time

精确性：

    只有 full route-space pricing 没有超时、没有触发状态上限，并且所有车辆均无
    负 reduced-cost schedule column 时，才记录 `exact_over_full_route_space=true`。
    若状态为 `FULL_PRICING_TIME_LIMIT` 或 `exact_over_full_route_space=false`，
    该 schedule-pack 值仍不能用于剪枝、不能写入正式 dual bound，也不能作为
    最优性证明。若非完整 full pricing 已经找到负 reduced-cost 的可行 schedule
    column，可以先把该列回流 RMP；这只是安全加列，不是无遗漏证书。

2026-05-21 集成式 full pricing 诊断：

    bench_20_02 root-only 300s full-pricing 长测中，full-pricing 状态数从约
    69009402 降到 32819435，route 生成数从约 1945331 降到 1195168；
    但 schedule_pack_obj 仍为 232.66585，official lower bound 仍为
    229.306913，说明该改动改善了搜索规模，但尚未得到可剪枝的 exact
    schedule-pack bound。

当前策略：

    paper 配置默认只在 root 尝试 full pricing：

       schedule_pack_full_pricing_enabled: true
       schedule_pack_full_pricing_max_depth: 0
       schedule_pack_full_pricing_max_states: 0

    这保证不把浅层节点时间大量花在全空间枚举上。若 20 节点 root 上 full pricing
    频繁超时，下一步应实现更强的双向 / ng-route schedule pricing，而不是把不完整
    schedule-pack 值当作下界。

2026-05-21 补充：batch schedule-column pricing 与系数缓存
-----------------------------------------------------------

背景：

    bench_20_02 的 schedule-pack 输出显示候选池内仍存在明显负 reduced-cost
    schedule column，但旧实现每轮只加入 1 列，导致大量时间消耗在反复重解
    vehicle-indexed schedule-pack LP 和重复计算 cut / branch 系数上。

修改：

1. `solve_schedule_pack_node_relaxation()` 新增：

       schedule_pack_pricing_batch_size

2. candidate-pool pricing 每轮对所有车辆收集负 reduced-cost schedule columns，
   按 reduced cost 排序后批量回流前 `schedule_pack_pricing_batch_size` 条。

3. 新增 schedule-pack 系数缓存，复用 route task mask、route-cut 系数和
   route-branch 系数；LP 重建和 pricing 均使用同一个缓存对象。

4. vehicle-indexed schedule-pack LP 改为持久化 RMP。初始化时建一次 `y`、cover、
   schedule-use、cut、branch row；后续每批新 schedule column 只调用 PySCIPOpt
   增量接口加入 `z[column,vehicle]` 变量和对应 row 系数，不再每轮重建完整 LP。

5. schedule-pack pricing 只读取 `OPTIMAL` LP 的 dual，并过滤非有限或极大 dual。
   若持久化 RMP 增量加列后出现 dual 不可用，会先用当前全部 schedule columns
   重建一次等价 RMP；若 LP 仍因时间限制或数值问题不能提供可靠 dual，则记录
   `TIME_LIMIT` / `DUAL_UNAVAILABLE`，不再把 SCIP 内部 `1e100` 量级哨兵值写成
   真实 reduced cost。

6. 当且仅当节点 schedule-pack relaxation 记录 `exact_over_full_route_space=true`
   时，将该 LP 值作为正式节点下界：

       node.lower_bound = max(route_vehicle_bound, schedule_pack_bound)

   随后可按普通 bound 规则剪枝。若 full pricing 未完整结束，则该值仍只作为诊断
   和节点排序信号，不进入正式 dual bound。

精确性：

    该修改只改变负 reduced-cost column 的回流批量和系数计算方式，不改变列的数学
    定义、valid cuts、分支约束或 exact 标志语义。持久化 RMP 保留所有 cut row，
    即使当前没有非零 route 系数，也会在未来新增 column 时补入系数；当前为空且满足
    的 cut row dual 按 0 处理。`exact_over_candidate_routes=true` 仍只表示候选 route
    集合内完整定价没有负 reduced-cost column；完整证明仍依赖 full route-space
    pricing 的 `exact_over_full_route_space=true`。
