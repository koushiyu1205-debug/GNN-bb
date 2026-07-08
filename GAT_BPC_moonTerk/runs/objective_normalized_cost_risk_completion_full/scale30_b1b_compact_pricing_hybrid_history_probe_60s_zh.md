# 30-scale B1B Compact Pricing Hybrid History Probe 60s

## 目的

该 probe 验证 B1/B0B1 row 是否能导出逐轮 pricing history，避免只看到累计统计而无法判断每一轮 final judge 的状态。

## 运行设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- output dir: `runs/objective_normalized_cost_risk_completion_full/compact_pricing_hybrid_history_probe_scale030_b1b_reference_seed_60s/`
- row time setting: `60s`
- B1B `solve_b0_direct_first`: `false`
- compact pricing path: negative-first hybrid

## 结果

| round | pricing_state | best_reduced_cost | final_judge_wall_time | added columns |
|---:|---|---:|---:|---:|
| 1 | `FOUND_NEGATIVE` | `-0.6281595` | `46.732922s` | 1 |
| 2 | `INCOMPLETE_LIMIT` |  | `5.016359s` | 0 |

## 结论

`pricing_history_json` 已写入 B1 rows。后续 300s/3600s probe 可以直接检查每一轮 final judge 是否还在持续发现负列，还是已经进入最后 no-negative proof 但被 bound 卡住。

该 probe 仍不是 BPC certificate；它只补齐诊断可观测性。
