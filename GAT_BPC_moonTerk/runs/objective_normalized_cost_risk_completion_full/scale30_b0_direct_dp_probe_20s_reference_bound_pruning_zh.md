# 30-scale B0 Direct-DP 20s Reference-Bound Probe

## 结论

该 probe 只用于验证 reference-solution upper bound 与 direct-DP lower-bound pruning 的诊断效果，不是 full 3600s row，也不是 official 30-scale exact solve。

当前代码可以从 instance `reference_solution` 重构一个 best-path repaired feasible upper bound，并在 direct-DP 中记录：

- `reference_solution_upper_bound`
- `reference_solution_upper_bound_source`
- `direct_bound_pruning_root_bound`
- `direct_bound_pruning_active`
- `journey_label_bound_pruned_count`

当前代码新增了 time-aware task-visit lower bound、endpoint path lower bound，以及 outgoing/start future-tail lower bound。首个 30-task 实例的 root pruning bound 仍只有 `0.841965885`，约为 repaired reference upper bound 的 `43.86%`。因此该实例上 active bound pruning 被安全关闭，避免无效 lower-bound 计算拖慢 sortie candidate generation。

当前 bound-gap diagnostic 显示：

- inbound tail bound = `0.841965885`
- outgoing tail bound = `0.822096905`
- direct-DP root pruning bound = `max(inbound, outgoing) = 0.841965885`

## 实例与结果

- instance: `lunar_ice_sp50_030_001_seed929001`
- wall limit: 20s
- status: `DIRECT_DP_TIME_LIMIT`
- certificate scope: `FEASIBLE_INCUMBENT_ONLY`
- objective: none
- reference upper bound: `1.919465`
- reference upper bound source: `instance_reference_solution_best_path_repair`
- direct-DP root pruning bound: `0.841965885`
- direct-DP root pruning bound / reference UB: `0.438646125`
- active bound pruning: `false`
- journey label bound-pruned count: `0`
- generated journey count: `11,566`
- generated sortie count: `3,649,183`
- route template count: `391,442`
- pareto label count: `44,430`
- set partition state count: `0`
- wall time: `20.009235s`
- max RSS: about `621,392 KB`

## 边界解释

- best-path repaired reference solution 只是 feasible upper bound，不是 optimality certificate。
- task-visit/time-aware/endpoint/outgoing/start lower bound 都是 safe lower bound：inbound formulation 和 outgoing formulation 分别放松真实 route sequence，最后取二者较强者；不会把两套 path bound 相加造成重复计数。
- 该 lower bound 当前仍不足以在 30-scale early candidate generation 中产生有效 pruning；后续需要更强的 exact-safe bound 或不同的 30-scale certificate path。
