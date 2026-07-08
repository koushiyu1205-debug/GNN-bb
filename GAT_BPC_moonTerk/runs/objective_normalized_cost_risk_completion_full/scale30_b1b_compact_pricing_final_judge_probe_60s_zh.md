# 30-scale B1B Compact Pricing Optimization-Mode Final-Judge Probe

> 注：该报告记录的是 no-flow reduced-cost minimization probe。`negative_feasibility_search` 已作为可选诊断另行测试；由于该诊断没有返回可用 best RC 或 dual bound，当前默认 compact final judge 保持 optimization-mode。新诊断结果见 `scale30_b1b_compact_pricing_negative_feasibility_probe_60s_zh.md`。

## 目的

该 probe 验证 30-scale B1B final judge 是否能避开 `2^30` task-subset representative enumeration，改用 compact single-journey reduced-cost pricing MILP 做 exact-safe pricing 诊断。

## 运行设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- output dir: `runs/objective_normalized_cost_risk_completion_full/compact_pricing_probe_scale030_b1b_reference_seed_60s/`
- row time setting: `60s`
- B1B seed mode: `b0_incumbent_plus_singletons`
- B1B `solve_b0_direct_first`: `false`
- reference incumbent seed source: `REFERENCE_FEASIBLE_INCUMBENT:instance_reference_solution_best_path_repair`
- initial columns: `34`
- reference incumbent seed columns: `4`
- reference incumbent used as certificate: `false`

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
| final judge wall time | `49.055805s` |
| compact pricing best reduced cost | `0.001228` |
| compact pricing dual bound | `-2.209305895` |
| compact pricing MIP gap | `1800.713309234` |
| compact pricing variables | `69,331` |
| compact pricing constraints | `72,389` |
| compact pricing complete | `false` |

## 结论

新路径已经把 30-scale B1B final judge 从 complete-universe RC audit 的 `2^30 = 1,073,741,824` 级代表枚举，推进到 compact single-journey pricing MILP。该模型直接优化一条非空 journey 的 reduced cost，因此如果求到 optimal 且最优 reduced cost 非负，可以作为 no-negative pricing proof。

本次 60s probe 仍未闭合：incumbent best reduced cost 为正，但 HiGHS dual bound 仍为负，不能排除存在负 reduced-cost column。因此它是更强的诊断路径，不是 BPC root certificate。
