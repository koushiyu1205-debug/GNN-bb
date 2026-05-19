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
- 分支 baseline：不使用 ML；采用 3PB，包含 pseudocost/fractionality 预筛、受限 child LP testing 和 heuristic-CG child testing。
- 强化项：task-vehicle linking、统一 crossing/resource cuts、schedule capacity cuts、inactive robust cuts 清洗、节点整数解排班不可行时的全局 schedule no-good cuts，以及 restricted master 内部的临时排程 no-good。

## 当前固化参数

- `max_routes_per_pricing = 500`：非根节点 exact pricing 每轮最多注入 500 条负 reduced-cost route。
- `root_max_routes_per_pricing = 1200`：根节点 exact pricing 每轮注入更多列，减少 20 节点规模上重复完整枚举的次数。
- `heuristic_pricing_enabled = true`：每轮先做 bounded-label pricing 找列。
- `heuristic_pricing_max_labels = 120000`：启发式定价的 label pop 上限。
- `heuristic_pricing_routes_per_round = 600`：启发式定价单轮最多注入列数。
- `heuristic_pricing_selection_mode = diverse`，`exact_pricing_selection_mode = diverse`：在负 reduced-cost 列很多时，除最低 reduced cost 外，额外保留按任务覆盖和路线长度分层的列。
- `restricted_master_heuristic_enabled = true`：在完成节点定价证书后，对当前 route pool 解一个小时间限制的 binary restricted master，主动寻找 incumbent；它只作为 primal heuristic，不参与 lower bound 证明。
- `restricted_master_schedule_aware = true`：restricted master 每次得到整数 route-vehicle assignment 后，立即对每辆车做 exact schedule check；若某辆车的 route 集合不可排程，就提取一个不可排程 core，在同一个临时 MIP 中加入 `sum lambda[p,r] <= |C|-1` 后继续求解。
- RIM 中的临时 no-good 对所有同质车辆同时加入；RIM 发现的不可排程 core 也会回流为主树正式 `schedule_nogood_core` cut，并触发当前节点重新求解。
- RIM 使用线性 incumbent cutoff 过滤不可能改进当前 incumbent 的整数候选；不使用 SCIP `Objlimit`，避免排程不可行的低目标候选提前终止 no-good 迭代。
- `restricted_master_max_no_good_rounds = 20`：单次 restricted master 最多排除 20 个排程不可行整数解，避免 primal heuristic 吞掉主 BPC 时间。
- `restricted_master_time_limit = 20.0`，`restricted_master_max_routes = 4000`：限制单次受限整数主问题的时间和 route pool 规模，避免吞掉主 BPC 时间。
- `max_labels_per_pricing = 0` / `hybrid_max_labels_per_pricing = 0`：exact pricing 不设 label 上限，用于保留最优性证明。
- certificate pricing 加速：exact pricing 仍完整枚举 elementary route sequence，但在 label 状态中增量维护访问集合、资源、服务时间和任务 dual 贡献；只有发现负 reduced-cost route 时才构造完整 `RouteColumn`。这减少了每个 label 反复调用 `evaluate_route()` 的开销，不改变列集合、不改变 reduced cost 公式，也不允许启发式定价参与证明。

## 论文表格建议报告字段

- `status`, `primal_bound`, `dual_bound`, `gap`, `solving_time`, `node_count`
- `rmp_solves`, `pricing_calls`, `exact_pricing_calls`, `generated_routes`, `label_pops`, `generated_labels`
- `restricted_master_integer_calls`, `restricted_master_integer_feasible`, `restricted_master_integer_time`, `restricted_master_integer_best_objective`
- `restricted_master_integer_raw_best_objective`, `restricted_master_integer_rejected`, `restricted_master_integer_no_good_cuts`
- `cuts_added`, `crossing_cuts_added`, `resource_lower_bound_cuts_added`, `robust_capacity_cuts_added`
- `schedule_capacity_cuts_added`, `schedule_nogood_cuts_added`, `cuts_purged`
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

20 节点规模当前有两个瓶颈：root pricing 的完整枚举次数，以及 fractional route pool 中没有及时转成好 incumbent。现在已经接入不破坏证明的 heuristic pricing、diverse column injection 和 schedule-aware restricted integer master primal heuristic。下一步应在 `bench_20_01` 到 `bench_20_10` 上跑 900 秒和 3600 秒两档，比较 `exact_pricing_calls`、`label_pops`、root dual bound、restricted master 的 rejected/no-good 数量、accepted incumbent 和最终 gap。如果 root gap 仍集中在车辆固定成本附近，再继续做可证明的全局 vehicle lower-bound cut，而不是直接手写 `sum y >= 2` 这类无证明约束。
