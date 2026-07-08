# 30-scale B1B Reference-Seed-Without-B0 Probe

## 目的

该 probe 验证一个 exact-safe 30-scale B1B 改动：当 B0 direct-DP 没有 exact incumbent 时，允许 B1B 跳过预先 B0 direct-DP，用 instance `reference_solution` 修复得到的 feasible incumbent 作为 RMP seed。

该 reference incumbent 只作为 primal feasible seed / upper-bound diagnostic，不作为 BPC certificate。

## 关键代码边界

- 新增 opt-in CLI: `--b1-reference-seed-without-b0`
- B1 payload 字段：
  - `solve_b0_direct_first`
  - `feasible_incumbent_seed_source`
  - `feasible_incumbent_seed_column_count`
  - `feasible_incumbent_seed_used_as_certificate`
- 证书门槛不变：只有 true-dual final judge closure、manual RC audit、pricing RC audit、proof debt gate 全通过，才允许 `BPC_NODE_LP_CERTIFIED`。

## 运行命令

```bash
timeout 210s python scripts/run_lunar_ice_normalized_objective_full_ablation.py \
  --output-dir runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed_no_b0 \
  --families b0b1 \
  --scales 30 \
  --limit-per-scale 1 \
  --force \
  --run-heavy-direct-modes \
  --b1-reference-seed-without-b0 \
  --max-workers 1 \
  --scale30-row-time-limit 60 \
  --min-mem-available-gb 2 \
  --min-disk-free-gb 20
```

## 结果

| mode | status | scope | wall | seed evidence |
|---|---|---|---:|---|
| `B0_pure_direct_dp` | `DIRECT_DP_TIME_LIMIT` | `FEASIBLE_INCUMBENT_ONLY` | `50.113947s` | unchanged B0 direct-DP timeout |
| `B1B_seeded_root_CG` | `BPC_INCOMPLETE_PRICING` | `FEASIBLE_INCUMBENT_ONLY` | `60.000051s` | `solve_b0_direct_first=false`; `initial_column_count=34`; `feasible_incumbent_seed_source=REFERENCE_FEASIBLE_INCUMBENT:instance_reference_solution_best_path_repair`; `feasible_incumbent_seed_column_count=4`; `feasible_incumbent_seed_used_as_certificate=false` |
| `B1A_full_universe_root_audit` | `BPC_INCOMPLETE_PRICING` | `FEASIBLE_INCUMBENT_ONLY` | `0.0s` | full-universe mode stayed resource-guarded |

## 对比旧 probe

- 旧 B1B seed：`initial_column_count=30`，只有 singleton seed；B1B 在约 `50.120424s` fail-closed 为 `DIAGNOSTIC_RMP_BOUND`。
- 新 B1B seed：`initial_column_count=34`，包含 4 条 reference incumbent journeys；B1B 不再浪费 row budget 先跑 B0 direct-DP，但 60s 内仍未闭合。

## 结论

该改动把 30-scale B1B 从“缺 B0 incumbent 导致 seed 太弱/诊断不足”推进到“reference incumbent 可作为 seed，但 true-dual pricing/final-judge tail 仍超时”。

这不是 30-scale exact solve，也不是 BPC certificate。下一步应针对 B1/B2 final judge deadline propagation、partial telemetry、以及 true-dual pricing tail lower bound 继续优化。
