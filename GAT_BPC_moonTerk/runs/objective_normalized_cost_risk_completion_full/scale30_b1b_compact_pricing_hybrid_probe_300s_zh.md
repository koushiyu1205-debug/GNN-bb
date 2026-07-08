# 30-scale B1B Compact Pricing Hybrid Final-Judge Probe 300s

## 目的

该 probe 验证 negative-first hybrid compact final judge 在更长预算下是否能持续消除负 reduced-cost column，并推进到最终 no-negative proof。

## 运行设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- output dir: `runs/objective_normalized_cost_risk_completion_full/compact_pricing_hybrid_probe_scale030_b1b_reference_seed_300s/`
- row time setting: `300s`
- B1B seed mode: `b0_incumbent_plus_singletons`
- B1B `solve_b0_direct_first`: `false`
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
| pricing rounds | `6` |
| added columns | `5` |
| final judge call count | `6` |
| final judge total wall time | `291.838090s` |
| final judge found-negative count | `5` |
| best negative reduced cost | `-0.685843335` |
| final judge incomplete count | `1` |
| certified no-negative count | `0` |
| last final judge status | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` |
| last compact pricing phase | `negative_feasibility_search` |
| last final judge wall time | `5.215400s` |

## 结论

300s probe 证明 hybrid path 不只是 60s 下偶然找到一个负列：它在同一 30-scale 首实例上连续 5 次找到真实负 reduced-cost column，并把 5 个 column 加入 root RMP。

但该 probe 仍未闭合：第 6 次 final judge 在剩余预算内未找到新的负列，也未证明 no-negative。因此当前 30-scale 缺口从“无法产生有效 pricing 列”推进为“能够消除一批负列，但最终 no-negative proof / exact compact pricing closure 仍未完成”。

这不是 `BPC_NODE_LP_CERTIFIED`，也不是 30-scale exact solve。下一步应优先判断：

- 更长 3600s row budget 是否能让 hybrid 持续消负列直到最后一轮 no-negative proof；
- 或者最终轮仍卡在 compact pricing bound proof，此时需要增强 proof bound，而不是只增加找负列时间。
