# Sharded Pulse Phase 10E Profile-DP Ordering Attribution 报告

日期：2026-06-13

## 目标

Phase 10D 证明 profile-DP mask label-cap 不是稳定优化方向。本轮只做 Phase 10E：profile-DP ordering attribution / returned task-set trajectory。

目标：

1. 将 ordinary official pricing 返回的 negative task-set 样本写入 ROI summary；
2. 比较 returned negative task-set 与 profile-DP top-mask hotspots 的关系；
3. 判断 Phase 10D 中 improved/worsened 是否来自 top-mask、returned task-set 或 active-pool trajectory；
4. 不改 solver/pricing 语义。

## 实现摘要

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 增加 summary 字段：

- `official_negative_journey_task_set_count`
- `official_negative_journey_task_set_hash`
- `official_negative_journey_task_set_samples`
- `official_negative_journey_sequence_samples`
- `official_negative_journey_signature_samples`
- `official_negative_first_task_set`
- `official_negative_first_task_count`
- `official_negative_profile_dp_top_overlap`
- `official_negative_profile_dp_top_jaccard`
- `official_negative_profile_dp_top_relation`
- `official_negative_profile_dp_top_exact`

这些字段只读 `journey_pricing` 日志，不改变求解路径。

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase10e_profile_dp_ordering_attribution_smoke_20260613 \
--instances phase7o_20_smoke \
--profiles phase10c_profile_dp_mask_hotspot_sensitivity \
--repeat-count 3 \
--time-limit 3.0 \
--pricing-time-limit 0.3 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase10e_profile_dp_ordering_attribution_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase10e_profile_dp_ordering_attribution_smoke_20260613/summary.csv`

矩阵：

- 20-task hard smoke：`tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`
- profiles：baseline, label-cap16, label-cap32
- repeat-count：3
- rows：27

## Aggregate 结果

| profile | rows | pricing | improvement | official changed | critical | returned negative task-sets | top-mask relation |
|---|---:|---|---|---:|---:|---:|---|
| baseline | 9 | 6 INCOMPLETE_LIMIT, 3 FOUND_NEGATIVE | baseline | 0 | 0 | 3 | 2 overlapping, 1 disjoint |
| label-cap16 | 9 | 6 INCOMPLETE_LIMIT, 3 FOUND_NEGATIVE | 7 no_regression, 2 worsened | 2 | 0 | 3 | 3 overlapping |
| label-cap32 | 9 | 6 INCOMPLETE_LIMIT, 3 FOUND_NEGATIVE | 5 no_regression, 4 worsened | 3 | 0 | 3 | 3 overlapping |

没有任何 returned negative task-set 与 profile-DP top-mask exact match。

## 关键 attribution

### `tranq20_01`

- 三个 repeat 全部 `INCOMPLETE_LIMIT`；
- 没有 returned negative task-set；
- label-cap profiles 均 no-regression；
- 当前不是 returned-negative ordering 问题，而是 proof/incomplete tail。

### `mt20_greedy_apollo_01`

- 三个 repeat 全部 `INCOMPLETE_LIMIT`；
- 没有 returned negative task-set；
- incumbent 变化主要表现为 active-pool hash / trajectory 差异；
- label-cap16/32 都出现 worsened；
- 这里不能用 negative returned task-set 解释，下一步若继续查，应看 RMP pool trajectory 和初始列/早期 profile-DP choices。

### `mt20_greedy_tranq_01`

这是本轮最有价值的 attribution。

baseline：

- repeat 0/1 returned `[1,6,15]`；
- top-mask relation：overlapping；
- incumbent：`761.814403`。

baseline repeat 2：

- returned `[13,16]`；
- top-mask relation：disjoint；
- incumbent：`721.502279`，明显更好。

label-cap16/32 repeat 2：

- returned `[1,6,15]`；
- top-mask relation：overlapping；
- incumbent 回到 `761.814403`，相对 baseline repeat 2 worsened。

这说明：

- top-mask overlap 不等于好列；
- 更靠近 hotspot 的 returned column 可能是退化/替换型列；
- 更好的 short CG trajectory 可能来自非 hotspot、disjoint 的 returned task-set；
- label-cap 没有解决 ordering，反而可能把搜索推回高频热点邻域。

## 结论

Phase 10E 进一步否定 label-cap / hotspot 追逐作为主线：

1. returned negative 与 top-mask exact match 次数为 0；
2. 最好的一次 `mt20_greedy_tranq_01` baseline 返回的是 disjoint task-set `[13,16]`；
3. label-cap profiles 返回 overlapping task-set `[1,6,15]` 时反而 worsened；
4. `mt20_greedy_apollo_01` 的变化不是 returned negative，而是 active-pool / early trajectory 差异；
5. 下一步应转向 column trajectory / active-pool attribution，而不是继续调 profile-DP cap 或 label-cap。

## Exactness 边界

- 本轮新增的是 summary diagnostics；
- 不启用 Sharded Pulse worker；
- 不启用 Pulse audit；
- 不启用 dual stabilization；
- 不改变 pricing/final judge/certificate 语义；
- 不改变 official lower-bound 规则。

## 下一步建议

Phase 10F：active-pool / early trajectory attribution。

建议目标：

- 对 `mt20_greedy_apollo_01` 和 `mt20_greedy_tranq_01` 记录前 N 个 pool active hash / top active task-set；
- 比较 baseline improved 与 label-cap worsened 的 early pool divergence；
- 判断是否是初始列 / profile-DP returned order / RMP degeneracy 导致 short-time incumbent 分化；
- 暂停 label-cap、cap 提高和 Pulse worker 主线。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

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

本轮最终 focused run：

```text
Ran 3 tests in 0.003s
OK
```

全量回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 482 tests in 1.444s
OK (skipped=1)
```

whitespace check：

```bash
git diff --check
```

结果：通过。
