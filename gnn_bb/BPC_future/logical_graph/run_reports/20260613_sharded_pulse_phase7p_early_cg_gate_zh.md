# Sharded Pulse Phase 7P Early-CG Worker Gate 报告

日期：2026-06-13

## 目标

前两轮 `same-iteration RC gate` 与 `follow-up reserve gate` 说明：

- Pulse worker 能在 20-task hard-ish 样本上找到 true-RC negative columns；
- 但 late-tail worker 经常没有足够后续 RMP / pricing 空间；
- 只靠 RC 强度和 follow-up reserve 仍不能形成稳定 wall-time ROI。

本轮目标是新增一个更窄的 early-CG gate：

- 只允许 optional Pulse hidden-negative worker 在早期 CG round 触发；
- 默认关闭，通过 profile opt-in；
- gate 只减少 worker 调用，不影响 official certificate / lower bound；
- 用 short smoke 验证它能挡掉 weak/late worker，同时不污染 5/10 默认路径。

## 实现摘要

### 1. 新增 opt-in 配置

新增配置：

```text
journey_sharded_pulse_hidden_negative_worker_max_cg_iter
```

规则：

- 默认 `0`，等价于关闭；
- 必须非负；
- 若 `max_cg_iter > 0` 且当前 `cg_iter > max_cg_iter`，worker 直接跳过；
- skip reason：

```text
max_cg_iter_exceeded
```

该 gate 只阻止 optional Pulse worker 调用，不会产生 certificate，也不会改变 official lower-bound 语义。

### 2. 新增 ROI profile

新增 calibration profile：

```text
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg
```

该 profile 继承：

- 20-task gate；
- pre-heuristic worker；
- same-iteration continue；
- active-support continuation gate；
- `impact_filter_min_true_rc=-30.0`；
- `min_followup_time_after_add=0.4`；
- `max_cg_iter=1`。

## Focused Tests

新增/更新覆盖：

- `max_cg_iter` 为负时配置非法；
- `cg_iter` 超过 gate 时，不调用 `price_journeys()`；
- early-CG profile 只在 20-task profile 下启用；
- early-CG profile 同时保留 RC gate、follow-up reserve 和 same-iteration 配置。

验证：

```text
Ran 4 focused tests in 0.007s
OK
```

全量：

```text
Ran 463 tests in 1.434s
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
--output-dir BPC_future/results/sharded_pulse_phase7p_early_cg_gate_20_smoke_1s_20260613 \
--instances mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg \
--time-limit 1.0 --pricing-time-limit 0.2 --pricing-max-dp-states 5000
```

结果摘要：

| profile | avg wall | worker triggered | worker added | changed |
|---|---:|---:|---:|---:|
| baseline | 0.808086 | 0 | 0 | 0 |
| RC + follow-up reserve | 0.821124 | 2 | 1 | 1 |
| early-CG gate | 0.818963 | 1 | 1 | 2 |

逐实例观察：

- `mt20_greedy_apollo_01`：early-CG 保留早期 worker 列，primal 从 baseline `921.640296` 改善到 `890.088613`，但 wall 从 `0.768548` 增至 `0.797401`。
- `mt20_greedy_tranq_01`：follow-up reserve profile 会触发 worker 但没有加列；early-CG gate 不触发 worker，wall 接近 baseline。
- `tranq20_01`：early-CG 不触发 worker；primal 有短跑轨迹差异改善，但不是 worker 直接导致。

## 5/10/20 Short Matrix

命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7p_early_cg_gate_small_matrix_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_early_cg \
--time-limit 0.3 --pricing-time-limit 0.12 --pricing-max-dp-states 1000
```

结果摘要：

| scale | profile | avg wall | worker triggered | worker added | changed |
|---:|---|---:|---:|---:|---:|
| 5 | baseline | 0.039341 | 0 | 0 | 0 |
| 5 | early-CG gate | 0.037280 | 0 | 0 | 0 |
| 10 | baseline | 0.297973 | 0 | 0 | 0 |
| 10 | early-CG gate | 0.298328 | 0 | 0 | 0 |
| 20 | baseline | 0.303329 | 0 | 0 | 0 |
| 20 | early-CG gate | 0.313880 | 0 | 0 | 0 |

短预算小矩阵中，early-CG profile 没有触发 worker。5/10 没有被 worker 污染；20-task 没有观察到稳定改善。

## Exactness 边界

- early-CG gate 只跳过 optional worker；
- worker 输出仍必须经过 true-RC negative 检查和正常 add-column path；
- skip / no-column / incomplete 不会形成 certificate；
- official lower bound 仍只来自既有 exact certificate path；
- 默认 benchmark 不启用该 profile。

## 结论

early-CG gate 是比上一版更安全的 worker 触发约束：它挡掉了部分 weak/late worker 调用，并保留了 `mt20_greedy_apollo_01` 里真正能改变 primal 轨迹的早期 worker。

但 ROI 仍不稳定：

1. 20-only 1s 中 early-CG 平均 wall 仍高于 baseline；
2. 有改善的样本仍带来额外 wall time；
3. 5/10 路径没有触发 worker，说明 guard 生效，但不能证明收益；
4. 20-task short matrix 没有 worker 触发，也没有稳定性能收益。

因此当前结论仍是：不要默认启用 worker，不进入 official certificate gate。early-CG gate 可以保留为后续 hard-tail worker tuning 的一个 opt-in 条件，但还不足以作为 Phase 7P 成功标准。

下一步更合理的方向不是继续加大 worker 预算，而是继续收紧触发依据，例如使用历史 follow-up objective/gap 改善信号，或转向更强的 column-impact / active-support-aware 选择。
