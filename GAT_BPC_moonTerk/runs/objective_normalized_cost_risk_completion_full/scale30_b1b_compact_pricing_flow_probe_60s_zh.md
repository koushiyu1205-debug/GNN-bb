# 30-scale B1B Compact Pricing Flow-Connectivity Probe

## 目的

该 probe 验证在 compact single-journey reduced-cost pricing MILP 中加入单商品流连通性约束，是否能改善 30-scale B1B final judge 的证明效率。

该约束是 exact-safe 的：它只排除不连通的弧选择解，不改变合法 journey 的 reduced-cost 搜索空间。5-scale 回归中，开启与关闭 flow-connectivity 均能与 exhaustive reduced-cost pricing 的最优 reduced cost 对齐。

## 运行设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- output dir: `runs/objective_normalized_cost_risk_completion_full/compact_pricing_flow_probe_scale030_b1b_reference_seed_60s/`
- row time setting: `60s`
- B1B seed mode: `b0_incumbent_plus_singletons`
- B1B `solve_b0_direct_first`: `false`
- reference incumbent seed source: `REFERENCE_FEASIBLE_INCUMBENT:instance_reference_solution_best_path_repair`
- flow-connectivity: `true`

## B1B 结果

| field | value |
|---|---:|
| algorithm_status | `BPC_INCOMPLETE_PRICING` |
| certificate_scope | `DIAGNOSTIC_PRICING_FRONTIER` |
| pricing_state | `INCOMPLETE_LIMIT` |
| B1 root LP bound | `1.919465` |
| root LP bound official | `false` |
| final judge status | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` |
| final judge backend | `HiGHS compact single-journey pricing MILP` |
| final judge model status | `TIME_LIMIT_REACHED` |
| final judge wall time | `5.630172s` |
| compact pricing variables | `136,741` |
| compact pricing constraints | `140,729` |
| compact pricing complete | `false` |

## 与默认 compact pricing probe 对比

| setting | variables | constraints | best RC | dual bound | final judge wall |
|---|---:|---:|---:|---:|---:|
| default no-flow | 69,331 | 72,389 | 0.001228 | -2.209305895 | 49.055805s |
| flow-connectivity | 136,741 | 140,729 |  |  | 5.630172s |

## 结论

flow-connectivity 是 proof-safe tightening，但本次 30-scale 60s probe 没有带来证书进展：模型规模几乎翻倍，且 HiGHS 在时限内没有返回可用 best reduced cost 或 dual bound。因此当前 final judge 默认仍保持 no-flow compact pricing；flow-connectivity 只保留为可选诊断开关，不作为 30-scale 闭合主路径。

该结果不是 BPC root certificate，也不是 30-scale exact solve。它只说明“加连通流约束”这一单点紧化，在当前求解器和时限下不是主要突破口。
