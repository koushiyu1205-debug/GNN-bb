# 论文级 `bpc_clean` Baseline

`bpc_clean_full` 是当前实验应固定使用的论文级 baseline。它是 exact route-vehicle Branch-Price-and-Cut，SCIP 只求每个节点的 RMP LP；它不是还在探索中的 vehicle-schedule master。

## Baseline 契约

- 求解入口：`bpc.solver.solve_bpc_clean`。
- benchmark variant：`bpc_clean_full`。
- 默认 benchmark 配置：`branchpricecut/config/paper_bpc_clean_baseline.json`。
- 主问题列：一条可行 sortie route 绑定一个 vehicle。
- 排班可行性：整数 incumbent 只有通过 exact multi-sortie schedule check 后才被接受；受限整数主问题内部也会排除排程不可行的整数列组合。
- 最优性边界：节点 bound 只能在 Phase-I/Phase-II RMP、true-dual exact pricing、branching filter 和已启用 cut separation 全部完成后使用。
- 时间限制边界：如果时间在节点证书完成前耗尽，该节点不能使用最后一次 RMP LP 作为已认证 bound，整体状态必须返回 `TIME_LIMIT`。
- 定价加速：bounded-label heuristic pricing 只用于快速找负 reduced-cost 列；若 label 上限触发且没有新列，必须继续运行完整 exact pricing。只有完整枚举的 `exhausted=True` 才能证明该节点没有负 reduced-cost 列；如果 bounded-label 调用本身已经 `exhausted=True`，说明上限未触发，也可以直接作为证明。
- 分支节点增强定价：普通 bounded-label heuristic 在分支节点找不到列时，会先运行一次更高 label 上限的 `heuristic_boost`。它仍只负责找列；只有 boost 自身 `exhausted=True` 时，才可作为完整 pricing certificate。
- 安全 dominance：exact pricing 在 label 状态中携带 `visited_mask`、当前任务、active crossing cut 计数、active `arc_on` 使用 mask 和 active signature prefix mask 后做 dominance；即使存在 schedule pair/no-good 这类顺序签名 cut，也只有两个 label 对后续可能命中的 active route signatures 完全一致时才比较，避免漏列。
- 分支 baseline：不使用 ML；采用 3PB，包含 pseudocost/fractionality 预筛、受限 child LP testing 和 heuristic-CG child testing。
- 强化项：task-vehicle linking、统一 crossing/resource cuts、schedule capacity cuts、LP 违背的 route-set schedule packing cuts、schedule incompatibility pair/clique cuts、inactive robust cuts 清洗、节点整数解排班不可行时优先加入双向不可排程 route-pair cut，其次尝试 conflict-induced schedule-capacity cut，无法证明任务上界时再回退 schedule no-good cuts；restricted master 内部同样按 pair cut、schedule-capacity cut、no-good 的顺序加入临时约束。
- 初始上界：先做 fixed-cost-aware serial/greedy schedule 构造，把通过 exact multi-sortie schedule check 的可行路线放入初始 route pool。该步骤只改善 primal upper bound，不参与 lower bound 证明。

## 当前固化参数

- `max_routes_per_pricing = 500`：非根节点 exact pricing 每轮最多注入 500 条负 reduced-cost route。
- `root_max_routes_per_pricing = 1200`：根节点 exact pricing 每轮注入更多列，减少 20 节点规模上重复完整枚举的次数。
- `heuristic_pricing_enabled = true`：每轮先做 bounded-label pricing 找列。
- `heuristic_pricing_max_labels = 120000`：启发式定价的 label pop 上限。
- `heuristic_pricing_routes_per_round = 600`：启发式定价单轮最多注入列数。
- `heuristic_pricing_selection_mode = diverse`，`exact_pricing_selection_mode = diverse`：在负 reduced-cost 列很多时，除最低 reduced cost 外，额外保留按任务覆盖和路线长度分层的列。
- `branch_node_heuristic_boost_enabled = true`：分支节点普通启发式找不到列时，先做一次增强启发式 pricing。
- `branch_node_heuristic_boost_max_labels = 900000`，`branch_node_heuristic_boost_routes_per_round = 1000`，`branch_node_heuristic_boost_min_depth = 1`：boost 从深度 1 开始，扩大 label 上限和单轮列注入上限，目标是减少 `bench_20_01` 分支节点上“heuristic=0、exact 找到大量负列”的情况。
- `exact_pricing_dominance_enabled = true`：开启安全 dominance；日志字段 `dominance_enabled` 和 `dominance_pruned` 用于确认该轮是否真正启用和剪掉多少 label。
- `restricted_master_heuristic_enabled = true`：在完成节点定价证书后，对当前 route pool 解一个小时间限制的 binary restricted master，主动寻找 incumbent；它只作为 primal heuristic，不参与 lower bound 证明。
- `restricted_master_schedule_aware = true`：restricted master 每次得到整数 route-vehicle assignment 后，立即对每辆车做 exact schedule check；若某辆车的 route 集合不可排程，就提取 witness。
- 若 witness 中存在两条 route `p,q` 满足 `p->q` 和 `q->p` 都不可行，RIM 先加入临时 `lambda[p,r]+lambda[q,r]<=y[r]`；若没有 pair witness，再尝试用 exact schedule-capacity oracle 证明某个任务集合 `S` 满足 `U(S)<|S|`，成功时加入 `sum_{i in S} z[i,r] <= U(S)y[r]`；若仍无法证明，才加入 `sum lambda[p,r] <= (|C|-1)y[r]` 临时 no-good。
- RIM 发现的 pair / schedule-capacity conflict 会回流到主树生成正式 cut；弱 no-good 只有在当前 LP 解确实违反时才提升为正式 cut，避免大量不抬升 bound 的全局 no-good 关闭 dominance。
- RIM 使用线性 incumbent cutoff 过滤不可能改进当前 incumbent 的整数候选；不使用 SCIP `Objlimit`，避免排程不可行的低目标候选提前终止 no-good 迭代。
- `restricted_master_max_no_good_rounds = 20`：单次 restricted master 最多排除 20 个排程不可行整数解，避免 primal heuristic 吞掉主 BPC 时间。
- `restricted_master_time_limit = 20.0`，`restricted_master_max_routes = 4000`：限制单次受限整数主问题的时间和 route pool 规模，避免吞掉主 BPC 时间。
- `max_labels_per_pricing = 0` / `hybrid_max_labels_per_pricing = 0`：exact pricing 不设 label 上限，用于保留最优性证明。
- certificate pricing 加速：exact pricing 仍完整枚举 elementary route sequence，但在 label 状态中增量维护访问集合、资源、服务时间、任务 dual 贡献、active crossing cut 计数、active `arc_on` 使用 mask 和 active signature prefix mask；只有发现负 reduced-cost route 时才构造完整 `RouteColumn`。这减少了每个 label 反复调用 `evaluate_route()` 的开销；安全 dominance 不改变列集合的证明逻辑、不改变 reduced cost 公式，也不允许未完成的启发式定价参与证明。
- route-set schedule packing separator：完成 exact pricing certificate 后，在浅层节点对同一车辆的 LP 高活动 route 集合 `C` 运行 exact schedule DP，证明同一辆车最多可排 `U(C)` 条 route；若当前 LP 违反 `sum_{p in C} lambda[p,r] <= U(C)y[r]`，加入正式 `schedule_route_set_packing` cut。候选集合来自启发式，`U(C)` 必须来自 exact oracle；oracle 状态超限时不加 cut。
- route-pack skip 诊断：separator 每轮额外写出 `route_set_schedule_packing_diagnostics`，记录候选数、oracle 查询数、oracle 未完成、`U(C)>=|C|` 不够紧、LP 未违反、重复候选、违反候选、实际加入数、最大违反量和最大 oracle 状态数。该诊断只用于定位瓶颈，不参与模型或证明。
- schedule-capacity skip 诊断：separator 每轮额外写出 `schedule_capacity_diagnostics`，记录候选任务集合数、oracle 查询数、oracle 未完成、`U(S)>=|S|` 不够紧、LP 未违反、重复候选、违反候选、实际加入数、最大违反量和最大 oracle 状态数。
- 弱 no-good 清理：`schedule_nogood_core/full` 若连续多轮 slack 大且 dual 近 0，会被清理；pair / clique / route-pack 结构性 cut 默认保留。清理 cut 只会放松 LP，不会破坏 exactness。
- RIM 冲突诊断：restricted-MIP 排除排程不可行整数候选后，记录正式回流 cut 的来源，包括 pair、schedule-capacity、no-good 以及“弱 no-good 当前 LP 不违反而跳过”的数量。
- schedule incompatibility separator：完成 exact pricing certificate 后，在浅层节点检查同一车辆 LP 支撑 route。若两条 route 的 `p->q` 和 `q->p` 都不可行，且当前 LP 违反 `lambda[p,r]+lambda[q,r]<=y[r]`，加入正式 pair cut；若一组 route 两两双向不可排程且当前 LP 违反 `sum lambda[p,r]<=y[r]`，加入正式 `schedule_clique_conflict` cut。候选搜索只是启发式，cut 有效性由 exact transition check 证明。
- 固定车成本感知初始构造：比较插入候选时使用包含 `F y_r` 的增量目标，避免为了较短 route cost 过早开启第二辆车；同时新增快速 serial schedule incumbent。2026-05-20 的检查显示，bench_20_02/03 上存在一辆车多 sortie 可行解，因此不能把 `sum_r y_r >= 2` 当作有效 cut。只有证明一辆车不可行，或证明所有一辆车方案目标值不可能优于当前 incumbent，才能安全排除一辆车分支。

## 论文表格建议报告字段

- `status`, `primal_bound`, `dual_bound`, `gap`, `diagnostic_dual_bound`, `diagnostic_gap`, `solving_time`, `node_count`
- `rmp_solves`, `pricing_calls`, `exact_pricing_calls`, `generated_routes`, `label_pops`, `generated_labels`
- `restricted_master_integer_calls`, `restricted_master_integer_feasible`, `restricted_master_integer_time`, `restricted_master_integer_best_objective`
- `restricted_master_integer_raw_best_objective`, `restricted_master_integer_rejected`, `restricted_master_integer_pair_conflict_cuts`, `restricted_master_integer_no_good_cuts`, `restricted_master_integer_schedule_capacity_cuts`
- `cuts_added`, `crossing_cuts_added`, `resource_lower_bound_cuts_added`, `robust_capacity_cuts_added`
- `schedule_pair_conflict_cuts_added`, `schedule_clique_conflict_cuts_added`, `schedule_route_set_packing_cuts_added`, `schedule_capacity_cuts_added`, `schedule_nogood_cuts_added`, `cuts_purged`
- `metric_route_set_schedule_packing_candidate_sets`, `metric_route_set_schedule_packing_oracle_queries`, `metric_route_set_schedule_packing_oracle_incomplete`, `metric_route_set_schedule_packing_not_tight`, `metric_route_set_schedule_packing_not_violated`, `metric_route_set_schedule_packing_violated_candidates`, `metric_route_set_schedule_packing_max_violation`, `metric_route_set_schedule_packing_oracle_states_max`
- `metric_schedule_capacity_candidate_subsets`, `metric_schedule_capacity_oracle_queries`, `metric_schedule_capacity_oracle_incomplete`, `metric_schedule_capacity_not_tight`, `metric_schedule_capacity_not_violated`, `metric_schedule_capacity_violated_candidates`, `metric_schedule_capacity_max_violation`, `metric_schedule_capacity_oracle_states_max`
- `metric_rim_conflict_checked`, `metric_rim_conflict_nogood_cuts_added`, `metric_rim_conflict_weak_nogood_not_violated`, `metric_cut_purged_schedule_nogood_core`, `metric_cut_purged_schedule_nogood_full`
- `branch_nodes`, `branch_lp_candidates_tested`, `branch_heuristic_candidates_tested`, `branch_testing_time`

## 单实例对比方式

`bpc_clean_full` 和 compact SCIP MILP baseline 必须使用同一个 JSON 实例。当前 benchmark run 中 `bench_10_01` 的实例路径是：

```bash
/home/kai/work/gnn_bb/branchpricecut/results/benchmark/20260513_224021_benchmark_10_20_30/instances/instance_bench_10_01.json
```

compact SCIP MILP 可用下面命令看完整 SCIP 日志：

```bash
/home/kai/miniconda3/envs/ecole/bin/python /home/kai/work/gnn_bb/src/gnn_bb/baseline/scip_milp.py \
  --instance-path /home/kai/work/gnn_bb/branchpricecut/results/benchmark/20260513_224021_benchmark_10_20_30/instances/instance_bench_10_01.json \
  --time-limit 3600 \
  --results-csv /home/kai/work/gnn_bb/branchpricecut/results/benchmark/20260513_224021_benchmark_10_20_30/scip_compact_baseline/scip_compact_bench_10_01.csv \
  --log-path /home/kai/work/gnn_bb/branchpricecut/results/benchmark/20260513_224021_benchmark_10_20_30/scip_compact_baseline/logs/bench_10_01.log
```

## 下一步

20 节点 tight fleet 当前主要瓶颈分成两类：上界侧要先确认 fixed-cost-aware serial/greedy incumbent 是否把 bench_20_01/02/03 降到一辆车多 sortie 的可行目标；下界侧继续看 route-vehicle master 的 schedule lower bound 与分支节点 certificate pricing。下一步先用固定结果路径跑 `bench_20_01`、`bench_20_02`、`bench_20_03`，重点看 `initial_incumbent`、`route-pack diag`、`schedule-cap diag`、`rim-conflict diag`、`cut_purged`、`diagnostic_dual_bound`、`pricing_kind=heuristic_boost`、`dominance_pruned`、`label_pops` 和节点 gap。如果 cut 数继续快速增长但 diagnostic bound 仍只小幅变化，应停止增加局部 no-good，转向更强 schedule-capacity 证书或可证明的一车目标下界，而不是直接加车辆数下界 cut。
