# BPC_future Root Cause calibrated selector A/B profile smoke 报告

日期：2026-06-13

## 目标

本轮目标不是证明性能优化，而是把 replay-calibrated selector candidate 接成一个严格 opt-in 的 A/B profile，并验证：

1. 默认求解路径不变；
2. 5/10 task 下 profile 不触发 Pulse worker；
3. 20 task 下 profile 会写入 calibrated true-RC threshold；
4. 当前 smoke 是否已经覆盖 worker ROI 场景。

## 新增 profile

新增 profile：

```text
strict_worker_current_probe_calibrated_true_rc_20_only
```

新增 profile group：

```text
root_cause_calibrated_selector_ab =
  baseline
  strict_worker_current_probe_calibrated_true_rc_20_only
```

新增 instance group：

```text
root_cause_calibrated_selector_gate =
  apollo5
  tranq5
  apollo10
  tranq10_09
  mt20_greedy_apollo_01
  tranq20_01
```

profile 只存在于诊断脚本：

```text
BPC_future/scripts/run_sharded_pulse_roi_calibration.py
```

没有修改默认 solver 配置，也没有打开 production worker 或 certificate gate。

## Calibrated selector 设置

20-task 上该 profile 设置：

```text
journey_sharded_pulse_hidden_negative_worker_enabled = true
journey_sharded_pulse_worker_current_probe_enabled = true
journey_sharded_pulse_hidden_negative_worker_min_tasks = 20
journey_sharded_pulse_worker_current_probe_min_tasks = 20
journey_sharded_pulse_hidden_negative_worker_impact_filter_mode = prefer_new_or_active_support
journey_sharded_pulse_hidden_negative_worker_impact_filter_max_columns = 0
journey_sharded_pulse_hidden_negative_worker_impact_filter_min_true_rc = -12.430587
```

5/10-task 上 `_apply_profile()` 直接返回，不启用 worker。

配置审计结果：

```text
task_count = 5:
  worker_enabled = false
  current_probe_enabled = false

task_count = 10:
  worker_enabled = false
  current_probe_enabled = false

task_count = 20:
  worker_enabled = true
  current_probe_enabled = true
  min_tasks = 20
  probe_min_tasks = 20
  impact_mode = prefer_new_or_active_support
  min_true_rc = -12.430587
```

## Small-scale gate smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_calibrated_selector_gate_smoke_20260613 \
--instances very_small apollo5 tranq5 \
--profiles root_cause_calibrated_selector_ab \
--time-limit 4 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1 \
--max-cg-iterations 3 \
--current-probe-min-tasks 20 \
--quiet
```

结果摘要：

```text
profile_rows = 3
profile_worker_events = 0
profile_worker_triggered_count = 0
profile_official_changed_count = 0
profile_objective_mismatch_count = 0
profile_unchanged_count = 3
```

注意：这个 smoke 不能当作 small-scale performance proof。`apollo5` / `tranq5` 的短时限 wall time 存在运行噪声，因此这里只能证明 worker 没触发且 official result 没变。

## 20-task smoke

命令分别运行：

```text
mt20_greedy_apollo_01
tranq20_01
mt20_greedy_tranq_01
```

共同配置：

```bash
--profiles root_cause_calibrated_selector_ab
--time-limit 8
--pricing-time-limit 0.3
--pricing-max-dp-states 1000
--max-cg-iterations 3
--current-probe-min-tasks 20
--current-probe-time-limit 0.5
--worker-time-limit 0.5
```

结果摘要：

```text
mt20_greedy_apollo_01:
  profile_worker_events = 0
  profile_official_changed_count = 0
  official_pricing_state = FOUND_NEGATIVE

tranq20_01:
  profile_worker_events = 0
  profile_official_changed_count = 0
  official_pricing_state = FOUND_NEGATIVE

mt20_greedy_tranq_01:
  profile_worker_events = 0
  profile_official_changed_count = 0
  official_pricing_state = FOUND_NEGATIVE
```

这些 smoke 没有进入 worker ROI 场景，原因是 ordinary pricing 已经返回 `FOUND_NEGATIVE`，没有形成 certificate-candidate / no-column hard-tail trigger。

因此本轮当前状态仍是：

```text
has_production_validated_selector = false
has_20_walltime_speedup_evidence = false
```

## 当前结论

已经完成：

1. calibrated selector A/B profile wiring；
2. 5/10 task gate 配置审计；
3. small smoke official result unchanged；
4. 20 smoke official result unchanged。

仍未完成：

1. 没有覆盖真正触发 worker 的 hard-tail context；
2. 没有观察到 `pulse_worker_impact_filter_min_true_rc = -12.430587` 的真实 worker add-column 事件；
3. 没有证明 retry / tail / wall time 下降；
4. 没有 full BPC A/B 证据。

所以本轮只是把下一步 A/B 入口接好，不是生产优化证明。

## 下一步要求

下一步需要选择能进入 certificate-candidate / no-column hard-tail 的 20-task repeats，重新跑：

```text
baseline
strict_worker_current_probe_calibrated_true_rc_20_only
```

验收必须同时包含：

1. 5/10 no-regression；
2. worker triggered；
3. impact filter threshold visible；
4. returned journeys true-RC <= -12.430587；
5. added columns 有 new/support-changing 信号；
6. followup RMP objective 或 dual 有有效变化；
7. selected 20 hard repeat wall time / gap / status / final-judge tail 改善。

在这些证据出现前，生产优化方向仍未证明。
