# 30-scale B0/B1 Strict Progress Probe

## 目的

该 probe 验证主全量 runner 在显式放开 30-scale direct-exact-dependent modes 后的真实行级行为，而不是仅写 resource-guard rows。

运行命令：

```bash
timeout 210s python scripts/run_lunar_ice_normalized_objective_full_ablation.py \
  --output-dir runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s \
  --families b0b1 \
  --scales 30 \
  --limit-per-scale 1 \
  --force \
  --run-heavy-direct-modes \
  --max-workers 1 \
  --scale30-row-time-limit 60 \
  --min-mem-available-gb 2 \
  --min-disk-free-gb 20
```

## 实例

- instance: `lunar_ice_sp50_030_001_seed929001`
- requested row time limit: `60s`
- runner output dir: `runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s/`
- total runner wall time: `100.657217s`

## 行级结果

| mode | status | certificate scope | wall time | key evidence |
|---|---|---|---:|---|
| `B0_pure_direct_dp` | `DIRECT_DP_TIME_LIMIT` | `FEASIBLE_INCUMBENT_ONLY` | `50.111255s` | direct-DP timed out during `sortie_candidate_generation`; no B0 objective |
| `B1B_seeded_root_CG` | `BPC_INCOMPLETE_PRICING` | `DIAGNOSTIC_RMP_BOUND` | `50.120424s` | root RMP did not solve to optimality; no official root certificate |
| `B1A_full_universe_root_audit` | `BPC_INCOMPLETE_PRICING` | `FEASIBLE_INCUMBENT_ONLY` | `0.0s` | full-universe mode stayed resource-guarded |

Shared diagnostic values:

- reference feasible upper bound: `1.919465`
- reference source: `instance_reference_solution_best_path_repair`
- direct-DP root pruning bound: `0.841965885`
- direct-DP root pruning active: `false`
- journey label bound-pruned count: `0`

## 结论

该 probe 说明当前全量 runner 已能对 30-scale 做受控真实尝试，但首实例在 60s row setting 下仍没有得到 B0 exact objective，也没有得到 B1 root certificate。

因此 30-scale 缺口不是主 runner 不能执行，而是 exact direct-DP / root closure 仍无法在当前证书链和下界强度下闭合。
