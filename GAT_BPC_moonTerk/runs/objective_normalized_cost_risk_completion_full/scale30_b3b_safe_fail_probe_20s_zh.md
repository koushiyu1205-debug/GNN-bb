# 30-scale B3B Safe-Fail Probe

## 结论

该 probe 验证 B3B 在 30-scale 放开 `max_direct_tasks=30` 且 B0 direct-DP 没有给出 fixed-graph incumbent 时，会先 fail-closed，不再继续枚举 task-subset representative universe。当前代码会额外记录 instance `reference_solution` 修复得到的 feasible upper bound，但该 upper bound 不作为 BPC certificate。

运行条件：

- instance: `lunar_ice_sp50_030_001_seed929001`
- mode: `B3B_seeded_branch_price_tree`
- `max_direct_tasks=30`
- outer `row_time_limit_sec=20`
- internal direct wall limit: 10s
- `b3_max_rounds_per_node=1`
- `max_tree_nodes=1`
- `max_branch_depth=0`

结果：

| field | value |
|---|---|
| algorithm_status | `BPC_INCOMPLETE_PRICING` |
| certificate_scope | `FEASIBLE_INCUMBENT_ONLY` |
| pricing_state | `INCOMPLETE_LIMIT` |
| B0_direct_objective | `None` |
| B3_global_ub | `1.919465` |
| feasible_incumbent_source | `REFERENCE_FEASIBLE_INCUMBENT:instance_reference_solution_best_path_repair` |
| feasible_incumbent_used_as_bpc_certificate | `false` |
| B3_tree_closed | `False` |
| node_count | 0 |
| wall_time | about 10.48s |
| max RSS | about 0.59 GB |

fail-closed reason:

```text
B3 fails closed before representative-universe enumeration because direct DP did not produce a fixed-graph incumbent: Fixed-graph direct DP exceeded wall_time_limit_sec=10.0 during journey_label_dp; partial counts are diagnostic only.
```

## 解释

这修复的是资源安全边界和诊断边界，不是 30-scale optimality。之前如果 B3B 被显式放开到 30-scale，B0 direct-DP 超时后仍有风险继续进入 representative-universe enumeration。现在 B3B 会在 direct-DP 缺少 exact incumbent 时直接降级为 `FEASIBLE_INCUMBENT_ONLY`，同时记录 reference feasible upper bound，避免再次触发 complete-universe 枚举失控，也避免把可行上界误写成 tree certificate。
