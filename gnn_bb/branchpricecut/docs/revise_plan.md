## 2026-05-19 `bpc_clean` tight fleet 优化记录

当前先不做 learning to cut，继续保留 exactness，优先优化 tight fleet 下的 route-vehicle `bpc_clean`。

本轮第一版改动：

- 增强 branch-node heuristic pricing：普通 bounded-label heuristic 在分支节点没有新增列且没有完成枚举时，先运行一次更高 label 上限的 `heuristic_boost`。
- 安全 dominance：exact pricing 的 label 状态加入 active crossing cut 计数、active `arc_on` 使用 mask 和 active signature prefix mask；dominance 只在相同状态 key 下比较到达时间、载重、能耗和前缀 reduced-cost score。
- 安全边界：schedule no-good / pair cut 这类顺序签名 cut 通过 active signature prefix mask 进入 key，因此不再直接关闭 dominance。
- 证明边界不变：heuristic 和 boost 只用于找负 reduced-cost route；只有 `exhausted=True` 的 pricing 调用才能作为节点 certificate。
- 配置开关：`branch_node_heuristic_boost_enabled`、`branch_node_heuristic_boost_max_labels`、`branch_node_heuristic_boost_routes_per_round`、`branch_node_heuristic_boost_min_depth`、`exact_pricing_dominance_enabled`。

评估重点：

- 日志中 `pricing_kind=heuristic_boost` 是否在分支节点找到列；
- `dominance_enabled` 是否经常为 true；
- `dominance_pruned` 是否足够大；
- `bench_20_01` 的完整 exact pricing 次数和 label pops 是否明显下降；
- `bench_20_02/03` 在 3600 秒内 gap 是否下降。

## 2026-05-19 `bench_20_02` schedule feasibility 加强

`bench_20_02` 的新日志显示，主要瓶颈不是纯 pricing，而是 route-vehicle master 反复找到低成本但真实 schedule 不可行的整数组合，导致大量 `schedule_nogood_core` cut，并且这些顺序签名 cut 会让安全 dominance 关闭。

本轮改动：

- 新增 conflict-induced schedule-capacity cut：当某辆车的 route 集合不可排程时，先从该 route 集合中生成任务集合候选 `S`；
- 对每个候选 `S` 调用 exact schedule task-capacity oracle，只有证明 `U(S)<|S|` 时才加 cut；
- 加入的正式 cut 仍是 `schedule_capacity`：

```text
sum_{i in S} z[i,r] <= U(S) y[r]
```

- 该 cut 对所有同质车辆同时加入，能切掉同一车辆服务过多 `S` 内任务的整类组合，而不是只切当前 route signatures；
- 若 exact oracle 无法证明任务上界，则回退到原来的 deletion-minimal `schedule_nogood_core`；
- restricted-MIP 内部也先尝试临时 schedule-capacity cut，失败后才加入临时 no-good。

有效性边界：

- 所有 schedule-capacity conflict cut 都必须由 exact oracle 给出 `U(S)`；
- oracle 超过状态上限或不能证明时不加 cut；
- heuristic 只负责生成候选 `S`，不决定 cut 是否有效；
- 节点 bound 仍只在 exact pricing 和启用的 cut separation 完成后使用。

## 2026-05-19 schedule witness 与 RIM cut 提升收紧

本轮先修三个结构问题：

- schedule checker 新增不可行 witness：对不可排程 route set 先压缩为 deletion-minimal core，再寻找双向不可排程的 route pair；
- 若 route pair `p,q` 满足 `p->q` 和 `q->p` 都不可行，加入更小的 `schedule_pair_conflict`：

```text
lambda[p,r] + lambda[q,r] <= 1
```

- RIM 内部排除不可排程整数候选时，顺序改为临时 pair cut、临时 schedule-capacity cut、临时 no-good；
- RIM 回流主树时，只自动提升 pair / schedule-capacity 这类强 witness cut；弱 no-good 只有在当前 LP 解违反时才提升为正式 cut。

预期效果：

- 减少 `schedule_nogood_core` 的数量；
- 降低顺序签名 cut 对 dominance 的干扰；
- 保留 exactness，因为每条正式 cut 都来自 exact schedule witness 或 exact schedule-capacity oracle。

## 2026-05-19 diagnostic bound 与 signature-cut dominance

根据 `bench_20_02` 最新日志，瓶颈从 root no-good 污染转向分支后 certificate pricing。新增两项改动：

- TIME_LIMIT 输出保留 `diagnostic_dual_bound`、`diagnostic_gap`、`best_open_node_bound`、`pending_node_bound` 和 `last_certified_node_bound`，用于判断算法实际进展；正式 `dual_bound/gap` 仍只在严格证书完整时填写；
- active schedule signature cut 不再直接关闭 dominance；pricing 为每个 label 维护 active signature prefix mask，只有两个 label 对后续可能命中的 active route signatures 完全一致时才允许支配。

验证重点：

- `bench_20_02` 日志中带 no-good/pair cut 的 exact pricing 是否仍出现 `dominance_enabled=true`；
- `dominance_pruned` 是否明显增加；
- `diagnostic_gap` 是否能反映 TIME_LIMIT 时的真实搜索进展。

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
