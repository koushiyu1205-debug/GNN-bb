# 30-scale B1B Compact Pricing Hybrid Final-Judge Probe 3600s

## 目的

该 probe 使用原计划 30-scale row budget 级别的 `3600s`，验证 negative-first hybrid compact final judge 是否能在单实例上持续消除负 reduced-cost column，并最终证明 no-negative。

## 运行设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- output dir: `runs/objective_normalized_cost_risk_completion_full/compact_pricing_hybrid_probe_scale030_b1b_reference_seed_3600s/`
- row time setting: `3600s`
- B1B seed mode: `b0_incumbent_plus_singletons`
- B1B `solve_b0_direct_first`: `false`
- B1 max rounds: `64`
- reference incumbent seed source: `REFERENCE_FEASIBLE_INCUMBENT:instance_reference_solution_best_path_repair`
- compact pricing path: negative-first hybrid
- flow-connectivity: `false`

## B1B 结果

| field | value |
|---|---:|
| algorithm_status | `BPC_INCOMPLETE_PRICING` |
| certificate_scope | `DIAGNOSTIC_PRICING_FRONTIER` |
| pricing_state | `INCOMPLETE_LIMIT` |
| B1 root LP bound | `1.919465` |
| root LP bound official | `false` |
| wall time | `3464.238856s` |
| pricing rounds | `36` |
| added columns | `35` |
| final judge call count | `36` |
| final judge total wall time | `3464.002810s` |
| final judge found-negative count | `35` |
| best negative reduced cost | `-1.532155091` |
| final judge incomplete count | `1` |
| certified no-negative count | `0` |
| last final judge status | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` |
| last compact pricing phase | `optimization_proof` |
| last final judge wall time | `1020.116874s` |
| last best reduced cost | `0.019060306` |
| last dual bound | `-1.480759697` |
| last MIP gap | `78.68742821` |

## 逐轮摘要

- rounds 1-35: 每轮均 `FOUND_NEGATIVE`，每轮加入 1 个 column。
- round 36: `INCOMPLETE_LIMIT`；negative-feasibility phase 未返回新负列，optimization-proof phase 找到正 reduced-cost incumbent `0.019060306`，但 dual bound 仍为 `-1.480759697`，不能证明 no-negative。

## 结论

3600s 单实例 probe 没有闭合 30-scale B1 root certificate，但显著推进了归因：

- 30-scale compact hybrid pricing 能持续产生有效负列，不是 column generation 完全失效。
- 在 35 个负列被加入后，最后一轮已经转向 no-negative proof 形态：incumbent best reduced cost 为正。
- 当前未闭合的直接原因是 compact pricing proof bound 仍为负，不能排除隐藏负 reduced-cost column。

因此，下一步不应只继续优化 seed 或 reference feasible incumbent；重点应放在最后一轮 compact pricing 的 proof bound 强化，或把 30-scale final judge 迁移到更强的 exact-safe pricing/certificate formulation。

该结果不是 `BPC_NODE_LP_CERTIFIED`，也不是 30-scale exact solve；它只是单实例 3600s 诊断。
