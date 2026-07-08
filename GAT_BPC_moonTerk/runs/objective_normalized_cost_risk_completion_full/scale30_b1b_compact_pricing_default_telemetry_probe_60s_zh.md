# 30-scale B1B Compact Pricing Optimization-Only Telemetry Probe

## 目的

该 probe 记录只使用 reduced-cost minimization mode 时的 B1B root CG 累计 final-judge telemetry，用于区分：

- root RMP / CG 是否反复加列；
- final judge 是否发现负 reduced-cost column；
- 未闭合是否主要来自 compact pricing bound 证明不足。

## 运行设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- output dir: `runs/objective_normalized_cost_risk_completion_full/compact_pricing_default_telemetry_probe_scale030_b1b_reference_seed_60s/`
- row time setting: `60s`
- B1B seed mode: `b0_incumbent_plus_singletons`
- B1B `solve_b0_direct_first`: `false`
- reference incumbent seed source: `REFERENCE_FEASIBLE_INCUMBENT:instance_reference_solution_best_path_repair`
- compact pricing mode: reduced-cost minimization only
- negative-feasibility search: `false`
- flow-connectivity: `false`

## B1B 结果

| field | value |
|---|---:|
| algorithm_status | `BPC_INCOMPLETE_PRICING` |
| certificate_scope | `DIAGNOSTIC_PRICING_FRONTIER` |
| pricing_state | `INCOMPLETE_LIMIT` |
| B1 root LP bound | `1.919465` |
| root LP bound official | `false` |
| pricing rounds | `1` |
| added columns | `0` |
| final judge call count | `1` |
| final judge total wall time | `49.011398s` |
| final judge found-negative count | `0` |
| final judge incomplete count | `1` |
| final judge status | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` |
| final judge exact status | `NOT_SOLVED` |
| compact pricing best reduced cost | `0.001228` |
| compact pricing dual bound | `-2.209305895` |
| compact pricing MIP gap | `1800.713309234` |
| compact pricing variables | `69,331` |
| compact pricing constraints | `72,389` |
| compact pricing complete | `false` |

## 结论

该 probe 表明 reduced-cost minimization mode 更偏向 bound 诊断而不是找负列：B1B 只进行 1 轮 pricing，未添加新列，incumbent best reduced cost 已为正。

未闭合的直接原因是 compact pricing minimization MILP 在 60s 内不能证明 lower bound 非负：best RC 为 `0.001228`，但 dual bound 仍为 `-2.209305895`。后续 hybrid probe 证明，同一 root dual 下 negative-feasibility phase 能找到真实负列，因此当前默认 compact final judge 已改为 negative-first hybrid。

该结果不是 BPC root certificate。只有 compact pricing exact optimal 且最优 reduced cost 非负，或其他 exact-safe final judge 证明 no-negative 时，才能升级为 `BPC_NODE_LP_CERTIFIED`。
