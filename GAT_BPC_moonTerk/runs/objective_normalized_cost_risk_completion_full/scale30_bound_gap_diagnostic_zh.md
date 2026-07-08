# 30-scale Bound Gap Diagnostic

## 边界

- 该诊断不求解实例，只汇总已有上界/下界强度。
- compact product bound 是 product-oracle 诊断下界，不是 BPC tree certificate。
- makespan 仍只作为报告指标；下表所有目标值均使用 normalized additive official objective。

## 实例

- instance: `lunar_ice_sp50_030_001_seed929001`
- scale: `30`
- task count: `30`
- reference upper bound: `1.919465`
- reference upper bound source: `instance_reference_solution_best_path_repair`

## 下界对比

| bound | value | ratio to ref UB | gap vs ref UB | note |
|---|---:|---:|---:|---|
| `analytic_relaxation` | 0.470407 | 0.245071934 | 0.754928066 | Conservative non-BPC relaxation lower bound; ignores nonnegative routing, return, recharge, fleet, capacity, shadow, and all makespan/report-only terms. |
| `task_visit_lower_bound` | 0.748208279 | 0.389800428 | 0.610199572 | Safe per-task bound used by direct-DP pruning; it relaxes routing order, return, fleet coupling, capacity interactions, and recharge sequencing. |
| `direct_dp_root_pruning_bound` | 0.841965885 | 0.438646125 | 0.561353875 | Current direct-DP pruning bound at root; it takes the stronger of a safe inbound task-visit formulation and a safe outgoing task-visit formulation. |
| `compact_product_bound:compact_bound_probe_scale030_300s` | 1.25962339 | 0.656236709 | 0.343763291 | Product-oracle diagnostic bound; useful for scale diagnosis but not a BPC tree certificate. |
| `compact_product_bound:compact_tight_m_probe_scale030_300s` | 1.25962339 | 0.656236709 | 0.343763291 | Product-oracle diagnostic bound; useful for scale diagnosis but not a BPC tree certificate. |

## Task-Visit Lower Bound 分解

| term | raw | normalized contribution |
|---|---:|---:|
| operating cost | 1104.98257 | 0.151543851 |
| risk | 51.1253487 | 0.197768631 |
| weighted completion | 10427.9874 | 0.398895797 |
| total |  | 0.748208279 |
| one return path |  | 0.00784008 |
| endpoint path lower bound |  | 0.093757606 |
| inbound tail bound |  | 0.841965885 |
| outgoing task-visit lower bound |  | 0.764262836 |
| start path lower bound |  | 0.057834069 |
| outgoing tail bound |  | 0.822096905 |
| direct-DP root pruning bound |  | 0.841965885 |

## 解释

- direct-DP root pruning bound 对该实例仍偏弱：只达到 repaired reference upper bound 的约 43.86%。
- compact product dual bound 明显强于 task-visit bound，但它仍不是 BPC certificate，且已有 probe 没有闭合 product model。
- 下一步更有价值的 exact-safe 方向是更强的 relaxation/certificate path，而不是继续做局部 dominance 微调。
