# 30-scale B1B Compact Pricing Negative-Feasibility Probe

> 注：该报告是 negative-feasibility-only B1B row 的历史诊断。表中 final judge 字段记录的是该 row 的最后一次 final judge；它不完整反映前序轮次是否曾找到负列。当前更准确的默认策略与累计 telemetry 见 `scale30_b1b_compact_pricing_hybrid_probe_60s_zh.md`。

## 目的

该 probe 验证 30-scale B1B final judge 是否能把 reduced-cost pricing 从“最小化 reduced cost”改成更贴近证书需求的 exact feasibility problem：

```text
exists a nonempty journey column with reduced_cost <= -eps ?
```

若该 MILP 可行，则找到负 reduced-cost column；若该 MILP 被证明 infeasible，则可作为 no-negative pricing proof；若超时，则仍 fail-closed。

## 运行设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- output dir: `runs/objective_normalized_cost_risk_completion_full/compact_pricing_neg_feas_probe_scale030_b1b_reference_seed_60s/`
- row time setting: `60s`
- B1B seed mode: `b0_incumbent_plus_singletons`
- B1B `solve_b0_direct_first`: `false`
- reference incumbent seed source: `REFERENCE_FEASIBLE_INCUMBENT:instance_reference_solution_best_path_repair`
- compact pricing mode: `negative_feasibility_search=true`
- flow-connectivity: `false`

## B1B 结果

| field | value |
|---|---:|
| algorithm_status | `BPC_INCOMPLETE_PRICING` |
| certificate_scope | `DIAGNOSTIC_PRICING_FRONTIER` |
| pricing_state | `INCOMPLETE_LIMIT` |
| B1 root LP bound | `1.919465` |
| root LP bound official | `false` |
| final judge status | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` |
| final judge exact status | `NOT_SOLVED` |
| final judge wall time | `4.750260s` |
| compact pricing best reduced cost |  |
| compact pricing dual bound |  |
| compact pricing MIP gap |  |
| compact pricing variables | `69,331` |
| compact pricing constraints | `72,390` |
| negative-feasibility search enabled | `true` |
| compact pricing complete | `false` |

## 结论

negative-feasibility formulation 是 proof-safe 的，并且比普通 minimization 更贴近“找负列”的判定问题。但该 negative-only row 的最后一次 final judge 未闭合：HiGHS 在剩余时限内没有证明 infeasible，也没有返回新的负 reduced-cost column。因此该模式本身不是 BPC root certificate。

后续 hybrid probe 显示，同一 30-scale 首实例中 negative-feasibility phase 能找到经过 manual RC audit 的真实负列，并让 B1B add 1 个 column；但最终 no-negative proof 仍未闭合。结论应以 hybrid probe 为准：negative-feasibility 适合做找负列阶段，最终证书仍需要更强的 exact no-negative proof。
