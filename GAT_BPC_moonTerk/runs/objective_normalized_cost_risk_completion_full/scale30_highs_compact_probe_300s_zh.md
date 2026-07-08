# 30-scale HiGHS Compact Fixed-Graph Product Oracle Probe

## 结论

首个 30-scale 实例的 compact HiGHS fixed-graph product MILP 在无 warm-start 的 300 秒内部 time limit 内没有找到可重构的 feasible incumbent，也没有证明最优。

加入 instance reference-solution warm-start 后，HiGHS 在 300 秒内可以保留并略微改进 feasible incumbent，但仍没有证明最优，product gap 约 34.21%。

这说明 HiGHS compact oracle 目前可以作为 30-scale product upper-bound 探针，但不能直接替代 30-scale B0 direct-DP / B2_PRODUCT 全量 exact product solve，更不能替代 BPC root/tree certificate。

## 实例与规模

- instance: `lunar_ice_sp50_030_001_seed929001`
- task count: 30
- vehicle count: 4
- sortie slots per vehicle: 30
- binary arc vars: 269,640
- task assignment vars: 3,600
- total vars: 277,320
- constraints: 289,102
- path option policy: `sp50_three_path_psr_rim_slope_contrast_v2`

## 300s 无 warm-start 探针结果

| field | value |
|---|---:|
| algorithm_status | `HIGHS_COMPACT_TIME_LIMIT_REACHED` |
| certificate_scope | `FEASIBLE_INCUMBENT_ONLY` |
| has_feasible_incumbent | false |
| objective |  |
| model_objective |  |
| lower_bound | 1.259623395 |
| gap |  |
| journey_count | 0 |
| solver_wall_time_sec | 289.74074 |
| process_elapsed | 5m16.47s |
| max_rss | 2,446,912 KB |
| swap | 0 |

原始 note：

```text
Compact HiGHS fixed-graph product model stopped without a reconstructable feasible incumbent.
```

## 300s reference warm-start 探针结果

warm-start 来源：instance `reference_solution.journeys`，按当前 compact nondominated path option 修复 path type 后传入 HiGHS。

| field | value |
|---|---:|
| algorithm_status | `HIGHS_COMPACT_TIME_LIMIT_REACHED` |
| certificate_scope | `FEASIBLE_INCUMBENT_ONLY` |
| has_feasible_incumbent | true |
| objective | 1.9146 |
| model_objective | 1.91460103 |
| lower_bound | 1.259623395 |
| gap | 0.342096147 |
| journey_count | 4 |
| solver_wall_time_sec | 290.903413 |
| process_elapsed | 5m17.54s |
| max_rss | 2,482,356 KB |
| swap | 0 |
| mip_start_status | `OK` |
| mip_start_source | `instance_reference_solution` |
| mip_start_objective | 1.919465 |
| mip_start_sortie_count | 12 |

原始 note：

```text
Compact HiGHS fixed-graph product model found a feasible incumbent but did not prove optimality within the configured limits.
```

## 边界解释

- 该结果不是 30-scale exact solve。
- `certificate_scope=FEASIBLE_INCUMBENT_ONLY` 是现有 fail-closed schema 的保守 scope；`has_feasible_incumbent` 才是 product oracle 是否给出 primal solution 的判断字段。
- 无 warm-start 的 300s 内没有 incumbent；加入 reference warm-start 后有 feasible incumbent，但没有 product optimal proof。
- warm-start product incumbent 可用于 upper-bound 诊断，不是 exact optimality certificate。
- 后续若继续推进 compact product oracle，应测试更强 MIP start、heuristic cuts 或外部 exact solver；这仍然不等同于 BPC certificate。
