# Sharded Pulse Phase 10A Profile-DP / Legacy Proof-tail Diagnostics 报告

日期：2026-06-13

## 目标

Phase 9L 后，dual-stabilization production 扩张暂停。Phase 10A 转向 legacy final judge / profile-DP proof-tail，只做只读诊断，不改求解路径。

本轮目标：

1. 给 baseline rows 增加全局 profile-DP tail 摘要；
2. 区分 `profile_dp_negative_tail`、`profile_dp_incomplete_tail`、state-cap、mask-cap；
3. 找出 20-task hard smoke 中 profile-DP tail 的结构热点；
4. 不改变 default config、certificate、lower bound 或 pricing 行为。

## 实现摘要

### 1. 新增 summary 字段

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增只读字段：

- `profile_dp_tail_records`
- `profile_dp_tail_incomplete_count`
- `profile_dp_tail_negative_count`
- `profile_dp_tail_no_negative_count`
- `profile_dp_tail_state_cap_hit_count`
- `profile_dp_tail_mask_cap_incomplete_count`
- `profile_dp_tail_time`
- `profile_dp_tail_state_count_max`
- `profile_dp_tail_processed_labels_max`
- `profile_dp_tail_extension_attempts`
- `profile_dp_tail_nonempty_mask_count_max`
- `profile_dp_tail_max_labels_per_mask_observed_max`
- `profile_dp_tail_top_mask_label_counts`
- `profile_dp_tail_min_best_rc`
- `profile_dp_tail_class`
- `profile_dp_tail_reason`

新增 helper：

- `_official_pricing_records()`
- `_profile_dp_tail_metrics()`
- `_classify_profile_dp_tail()`

这些 helper 只解析 JSONL 中已有 `journey_pricing` 事件，排除 `sharded_pulse_hidden_negative_worker` 和 sharded pulse dummy/final-judge 记录。

### 2. 新增 profile group

新增：

- `phase10a_profile_dp_tail_diagnostics`

展开为：

- `baseline`

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase10a_profile_dp_tail_diagnostics_smoke_20260613 \
--instances phase9l_previous_dual_stabilization_gate \
--profiles phase10a_profile_dp_tail_diagnostics \
--repeat-count 1 \
--time-limit 3.0 \
--pricing-time-limit 0.3 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase10a_profile_dp_tail_diagnostics_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase10a_profile_dp_tail_diagnostics_smoke_20260613/summary.csv`

矩阵：

- 20 个 5-task；
- 20 个 10-task；
- 3 个 20-task hard smoke；
- baseline only；
- 共 43 行 summary。

## 结果

### 5-task

聚合：

- rows = 20
- official status: `TIME_LIMIT=20`
- pricing state: `INCOMPLETE_LIMIT=20`
- `profile_dp_tail_class`:
  - `profile_dp_negative_tail=19`
  - `profile_dp_other_tail=1`
- `legacy_final_judge_calls=40`
- `profile_dp_tail_records=133`
- `profile_dp_tail_negative_count=75`
- `profile_dp_tail_incomplete_count=0`
- `profile_dp_tail_state_cap_hit_count=0`
- `profile_dp_tail_time=0.091962`
- max `profile_dp_tail_state_count_max=468`
- max `profile_dp_tail_max_labels_per_mask_observed_max=56`

解释：5-task 短 smoke 的 `TIME_LIMIT` 主要不是 profile-DP incomplete/state-cap；profile-DP 多数能找到 negative。

### 10-task

聚合：

- rows = 20
- official status: `TIME_LIMIT=20`
- pricing state:
  - `FOUND_NEGATIVE=19`
  - `INCOMPLETE_LIMIT=1`
- `profile_dp_tail_class=profile_dp_negative_tail` for all 20 rows
- `legacy_final_judge_calls=2`
- `profile_dp_tail_records=161`
- `profile_dp_tail_negative_count=158`
- `profile_dp_tail_incomplete_count=0`
- `profile_dp_tail_state_cap_hit_count=56`
- `profile_dp_tail_time=1.370609`
- max `profile_dp_tail_state_count_max=1001`
- max `profile_dp_tail_max_labels_per_mask_observed_max=43`

解释：10-task 中 profile-DP 很多记录触达 state cap，但仍多数返回 negative。这里的瓶颈更像 profile-DP search breadth / repeated negative tail，而不是 final no-negative certificate。

### 20-task

聚合：

- rows = 3
- official status: `TIME_LIMIT=3`
- pricing state:
  - `INCOMPLETE_LIMIT=2`
  - `FOUND_NEGATIVE=1`
- `profile_dp_tail_class`:
  - `profile_dp_incomplete_tail=2`
  - `profile_dp_negative_tail=1`
- `legacy_final_judge_calls=4`
- `profile_dp_tail_records=19`
- `profile_dp_tail_incomplete_count=2`
- `profile_dp_tail_negative_count=13`
- `profile_dp_tail_state_cap_hit_count=13`
- `profile_dp_tail_time=0.141483`
- max `profile_dp_tail_state_count_max=1001`
- max `profile_dp_tail_max_labels_per_mask_observed_max=31`

20-task rows：

| instance | pricing | class | records | incomplete | negative | state-cap hits | state max | max labels/mask | min best RC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `tranq20_01` | `INCOMPLETE_LIMIT` | `profile_dp_incomplete_tail` | 6 | 1 | 3 | 3 | 1001 | 16 | `-57.0891735` |
| `mt20_greedy_apollo_01` | `INCOMPLETE_LIMIT` | `profile_dp_incomplete_tail` | 5 | 1 | 2 | 2 | 1001 | 24 | `-139.913748` |
| `mt20_greedy_tranq_01` | `FOUND_NEGATIVE` | `profile_dp_negative_tail` | 8 | 0 | 8 | 8 | 1001 | 31 | `-49.067786` |

20-task top mask hotspots：

- `tranq20_01`:
  - `[5,8]`, `[7,15,20]`, `[7,16]`, `[12,15,20]`
- `mt20_greedy_apollo_01`:
  - `[11,12,17]`, `[4,5,15]`, `[9,10]`, `[4,12]`
- `mt20_greedy_tranq_01`:
  - `[2,7,9,17]`, `[7,9,17]`, `[7,9,10,17]`, `[9,10,17]`

## ROI / Pivot 判断

Phase 10A 给出新的主线判断：

1. 20-task 的 proof-tail 不是单纯 legacy completion retry 问题：
   - 本轮 retry count = 0；
   - 20-task `legacy_final_judge_calls=4`，但 profile-DP records / state-cap hits 更突出。
2. `tranq20_01` 和 `mt20_greedy_apollo_01` 的 hard tail 是 `profile_dp_incomplete_tail`；
3. `mt20_greedy_tranq_01` 是 `profile_dp_negative_tail`，能找到 negative，但仍 `TIME_LIMIT`；
4. 下一步不应回到 Pulse worker 或 dual-stabilization；
5. 下一步应针对 profile-DP proof-tail 做结构化优化。

## 下一步建议

建议 Phase 10B：

- profile-DP state-cap sensitivity with exact-safe diagnostics；
- 不直接提高 global cap；
- 只做 controlled A/B：
  - baseline cap 1000；
  - modest cap 2000/3000；
  - 可选 per-mask cap；
  - 观察 `profile_dp_tail_incomplete_count`、`state_cap_hit_count`、wall、negative/primal；
- 如果提高 cap 只增加 wall 而不减少 incomplete，则转向 profile-DP mask hotspot ordering / selected-mask materialization；
- 不改变 certificate 语义。

## Exactness 边界

- 只新增 summary diagnostics；
- 不改变 solver/pricing path；
- 不改变 default config；
- 不启用 Pulse worker；
- 不启用 certificate gate；
- 不修改 lower-bound 规则；
- 不把 profile-DP incomplete 当 certificate。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_dp_tail_metrics_are_summarized \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 3 tests in 0.002s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

全量 `BPCFutureTests`：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 482 tests in 1.448s
OK (skipped=1)
```

Whitespace 检查：

```bash
git diff --check
```

结果：通过。
