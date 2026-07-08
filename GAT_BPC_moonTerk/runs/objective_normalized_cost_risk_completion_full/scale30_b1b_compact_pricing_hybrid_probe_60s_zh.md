# 30-scale B1B Compact Pricing Hybrid Final-Judge Probe

## 目的

该 probe 验证新的 compact final judge hybrid 策略：

1. 先运行 negative-feasibility search，目标是尽快找到任意 `reduced_cost <= -eps` 的真实负列。
2. 若未找到负列且仍有预算，再运行 reduced-cost minimization mode 做 no-negative proof / bound 诊断。
3. 只有 exact no-negative 才能认证；找到的负列只用于加入 RMP，不能直接形成证书。

## 运行设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- output dir: `runs/objective_normalized_cost_risk_completion_full/compact_pricing_hybrid_probe_scale030_b1b_reference_seed_60s/`
- row time setting: `60s`
- B1B seed mode: `b0_incumbent_plus_singletons`
- B1B `solve_b0_direct_first`: `false`
- reference incumbent seed source: `REFERENCE_FEASIBLE_INCUMBENT:instance_reference_solution_best_path_repair`
- compact pricing default path: negative-first hybrid
- flow-connectivity: `false`

## B1B 结果

| field | value |
|---|---:|
| algorithm_status | `BPC_INCOMPLETE_PRICING` |
| certificate_scope | `DIAGNOSTIC_PRICING_FRONTIER` |
| pricing_state | `INCOMPLETE_LIMIT` |
| B1 root LP bound | `1.919465` |
| root LP bound official | `false` |
| pricing rounds | `2` |
| added columns | `1` |
| final judge call count | `2` |
| final judge total wall time | `51.823028s` |
| final judge found-negative count | `1` |
| best negative reduced cost | `-0.6281595` |
| final judge incomplete count | `1` |
| last final judge status | `COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED` |
| last compact pricing phase | `negative_feasibility_search` |
| last final judge wall time | `2.821627s` |

## 结论

hybrid 策略比单纯 optimization-mode 更适合 30-scale root CG 的前半段：default optimization-mode 在 49s 内只找到正 reduced-cost incumbent，而 negative-feasibility search 在同一 root dual 下找到了经过 manual RC audit 的真实负列，并让 B1B 实际 add 了 1 个 column。

但该 probe 仍未闭合 30-scale：加入 1 个负列后，第二轮 final judge 只剩约 2.8s，无法证明 no-negative。因此它是一个 exact-safe 进展，不是 BPC root certificate。

下一步如果要推进 30-scale，应在更长 row budget 下观察 hybrid 是否能持续消除负列并进入最后的 no-negative proof；同时需要继续增强 compact pricing 的 bound proof，否则最终轮仍会卡在 exact closure。
