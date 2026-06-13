# Sharded Pulse Phase 7P Same-Iteration RC Gate 报告

日期：2026-06-13

## 目标

本轮继续 Phase 7P，但不推进 official certificate gate，也不默认启用 worker。

目标是给已存在的 same-iteration hidden-negative worker 增加一个更保守的 true-RC 强度门槛：

- worker 找到的列仍必须走正常 `manual_journey_reduced_cost()` true-RC 校验；
- 只有 true RC 足够负的候选才允许作为 optional worker 列加入；
- 被筛掉或筛空的 worker 结果不得产生 certificate / official lower bound；
- 只用于 ROI 对照 profile，不改变默认 benchmark 行为。

## 实现摘要

### 1. 新增 opt-in RC 门槛

新增配置：

```text
journey_sharded_pulse_hidden_negative_worker_impact_filter_min_true_rc
```

规则：

- 默认 `0.0`，等价于关闭；
- 必须非正，正数配置会被拒绝；
- 仅在 worker impact filter 内生效；
- 若启用，则只保留 `true_rc <= threshold` 的候选；
- 筛空后返回 `INCOMPLETE_LIMIT`，reason 为 `sharded_pulse_hidden_negative_worker_impact_filtered_empty`，不可能成为证书。

### 2. ROI profile

新增 calibration profile：

```text
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate
```

该 profile 继承：

- 20-task gate；
- pre-heuristic worker；
- same-iteration continue；
- active-support continuation gate；
- inactive-success cooldown；
- impact filter mode `require_new_or_active_support`；
- true-RC threshold `-30.0`。

### 3. 日志/summary 字段

新增或接入 summary 字段：

- `pulse_worker_impact_filter_min_true_rc`
- `pulse_worker_impact_filter_selected_best_true_rc`
- `pulse_worker_impact_filter_rc_threshold_dropped_count`

## Focused Tests

新增/更新覆盖：

- ROI profile 注册和 summary 字段注册；
- RC gate profile 确认 10-task 不启用、20-task 启用 pre-heuristic + same-iteration + `min_true_rc=-30.0`；
- impact filter 默认不启用 RC 门槛时保留 new / active-support 候选；
- `min_true_rc=-50.0` 保留 strong new 列并丢掉 weak new 列；
- `min_true_rc=-200.0` 筛空后返回 `INCOMPLETE_LIMIT`，不证书。

验证：

```text
Ran 5 focused tests in 0.009s
OK
```

全量：

```text
Ran 460 tests in 1.417s
OK (skipped=1)
```

语法与 diff 检查：

```text
py_compile: passed
git diff --check: passed
```

## 20-only 1s Smoke

命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7p_same_iter_rc_gate_20_smoke_1s_20260613_rerun \
--instances mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate \
--time-limit 1.0 --pricing-time-limit 0.2 --pricing-max-dp-states 5000
```

结果摘要：

| profile | avg wall | worker added | RC-threshold dropped | changed vs baseline |
|---|---:|---:|---:|---:|
| baseline | 0.806338 | 0 | 0 | 0 |
| same-iter active gate | 0.825686 | 4 | 0 | 1 |
| same-iter RC gate | 0.824093 | 2 | 2 | 2 |

逐实例观察：

- `mt20_greedy_apollo_01`：RC gate 保留 `true_rc=-39.453983` 的 worker 列，primal 从 `921.640296` 改善到 `890.088613`，但 wall 高于 baseline。
- `mt20_greedy_tranq_01`：RC gate 筛掉 2 个弱列，未加列，primal 不变。
- `tranq20_01`：RC gate 保留 1 个 `true_rc=-41.0531155` worker 列，但 primal 变为 `783.715884`，较 baseline `782.95654` 更差；这是 ROI 不稳定信号，不是 exactness 问题。

## Small Matrix Smoke

命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7p_same_iter_rc_gate_small_matrix_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate \
--time-limit 0.3 --pricing-time-limit 0.12 --pricing-max-dp-states 1000
```

结果摘要：

| scale | profile | avg wall | worker triggered | worker added | changed |
|---:|---|---:|---:|---:|---:|
| 5 | baseline | 0.038061 | 0 | 0 | 0 |
| 5 | RC gate | 0.037829 | 0 | 0 | 0 |
| 10 | baseline | 0.298659 | 0 | 0 | 0 |
| 10 | RC gate | 0.297955 | 0 | 0 | 0 |
| 20 | baseline | 0.315284 | 0 | 0 | 0 |
| 20 | RC gate | 0.310612 | 2 | 1 | 1 |

5/10 规模由 20-task gate 挡住，没有 worker 开销。20 规模中 RC gate 能筛掉弱列，但仍只有局部正向信号。

## Exactness 边界

- 本轮没有打开 production 默认 worker；
- 没有启用 official certificate gate；
- worker 加列仍走普通 add-column path；
- no-column / impact-filter-empty / incomplete 不会产生 official lower bound；
- `min_true_rc` 只过滤 optional worker 列，不改变 pricing universe，也不参与证明。

## 结论

RC gate 机制是安全的，并且能把明显弱的 worker 列挡掉；但本轮 smoke 仍不能证明稳定 ROI。

当前判断：

1. same-iteration gate 解决了短预算下 “worker 后立刻 re-solve 导致 follow-up incomplete” 的一类回归；
2. RC gate 能减少 weak replacement worker 加列；
3. 但 20-only 1s 仍未跑赢 baseline，且 `tranq20_01` 出现加列后 primal 变差的样本；
4. 因此 worker 主线仍不适合默认启用，也不应进入 official certificate gate。

下一步更合理的方向不是继续加大 worker budget，而是把 worker trigger 进一步绑定到后续收益：

- 若保留 worker 路线，应继续做 column impact / active-support / objective-delta gate；
- 若关注 proof，则应回到 shard refinement / resume；
- 暂时不要做 20/100 大规模默认 A/B 或 official lower-bound effect。
