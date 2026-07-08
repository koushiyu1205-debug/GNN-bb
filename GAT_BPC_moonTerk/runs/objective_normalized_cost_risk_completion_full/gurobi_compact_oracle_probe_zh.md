# Compact Fixed-Graph Oracle Probe

## 结论

本机存在 `gurobipy 13.0.2`，但 license 是 size-limited non-production license；Gurobi backend 从 10-scale 起被 license 拒绝。

新增 HiGHS backend 后，compact MILP 已在 5-scale 与 10-scale 首实例上和 B0 direct-DP 完全对齐。它可以作为 fixed-graph product exact oracle 候选，但仍不是 BPC root/tree certificate，不能替代 `BPC_TREE_OPTIMAL` 的 true-dual / branch audit 证明链。

## 5-scale 对照

实例：`lunar_ice_sp50_005_001_seed424201`

| solver | status | objective |
|---|---|---:|
| B0 direct-DP | `DIRECT_DP_BASELINE_OPTIMAL` | 2.191915 |
| Gurobi compact MILP | `GUROBI_COMPACT_OPTIMAL` | 2.191915 |
| HiGHS compact MILP | `HIGHS_COMPACT_OPTIMAL` | 2.191915 |

差异：0.0。

HiGHS 运行信息：`model_objective=2.191915033`，`bound=2.191915033`，`gap=0.0`，`wall_time=1.059497s`，`variables=355`，`constraints=473`，`binary_arc_vars=285`。

## 10-scale 对照

实例：`lunar_ice_sp50_010_001_seed424201`

| solver | status | objective |
|---|---|---:|
| B0 direct-DP | `DIRECT_DP_BASELINE_OPTIMAL` | 2.014478 |
| HiGHS compact MILP | `HIGHS_COMPACT_OPTIMAL` | 2.014478 |

差异：0.0。

HiGHS 运行信息：`model_objective=2.014477987`，`bound=2.014477987`，`gap=0.0`，`wall_time=37.514029s`，`variables=6060`，`constraints=6826`，`binary_arc_vars=5580`。

## License / Size Boundary

10-scale 首实例被 Gurobi license 拒绝：

```text
GurobiError: Model too large for size-limited license
```

模型规模估计：

| scale | binary arc vars | task assignment vars | total vars | constraints |
|---:|---:|---:|---:|---:|
| 5 | 285 | 25 | 355 | 473 |
| 10 | 5,580 | 200 | 6,060 | 6,826 |
| 30 | 269,640 | 3,600 | 277,320 | 289,102 |

因此，当前机器上的 Gurobi 不能作为 30-scale exact fallback。HiGHS 已绕开 Gurobi license 限制并通过 10-scale 首实例验证；30-scale 首实例 300s 探针已经运行，无 warm-start 时未找到 feasible incumbent，加入 reference warm-start 后找到并改进了 feasible incumbent，但未证明最优。

## 30-scale 300s 探针

实例：`lunar_ice_sp50_030_001_seed929001`

| field | value |
|---|---:|
| status | `HIGHS_COMPACT_TIME_LIMIT_REACHED` |
| has_feasible_incumbent | false |
| objective |  |
| lower_bound | 1.259623395 |
| journey_count | 0 |
| solver_wall_time_sec | 289.74074 |
| max_rss | 2,446,912 KB |

详细记录见 `scale30_highs_compact_probe_300s_zh.md`。

reference warm-start 后的 300s 结果：

| field | value |
|---|---:|
| status | `HIGHS_COMPACT_TIME_LIMIT_REACHED` |
| has_feasible_incumbent | true |
| objective | 1.9146 |
| lower_bound | 1.259623395 |
| gap | 0.342096147 |
| journey_count | 4 |
| solver_wall_time_sec | 290.903413 |
| max_rss | 2,482,356 KB |
| mip_start_objective | 1.919465 |

## 当前边界

compact MILP 只是 fixed-graph product oracle，不是 BPC 证书路径。它可以给 B0/B2_PRODUCT 风格的 exact product solution 或 upper-bound cross-check，但不能直接证明 B1/B2/B3 true-dual root closure，也不能替代 branch RC audit。

这条路径还没有完成 30-scale exact solve。30-scale 仍需要新的 exact-safe pricing/certificate path，或者先为 HiGHS/SCIP/CP-SAT compact oracle 增加安全 MIP start / incumbent construction，再通过 BPC certificate gate 严格区分 product optimal 与 `BPC_TREE_OPTIMAL`。
