# Sharded Pulse Phase 7P-alt Column Impact Filter 报告

日期：2026-06-12

## 目标

Phase 7O 显示 current-context probe 可以在 Apollo10 / tranq10_09 加到 true-RC negative columns，但多数是 replacement，尚未证明 wall-time ROI。

Phase 7P-alt 的目标是引入一个保守、默认关闭的 worker 返回列 impact filter：

- 优先 new task-set；
- 优先 active support-changing replacement；
- 过滤弱 replacement / unchanged candidates；
- 仍然只影响 hidden-negative worker 的 returned columns；
- 不产生 certificate；
- 不产生 official lower bound。

## 实现摘要

### 1. Impact filter

新增 hidden-negative worker 配置：

- `journey_sharded_pulse_hidden_negative_worker_impact_filter_mode`
  - `off`
  - `prefer_new_or_active_support`
  - `require_new_or_active_support`
- `journey_sharded_pulse_hidden_negative_worker_impact_filter_max_columns`

`require_new_or_active_support` 只保留：

- new task-set；
- active support-changing replacement。

如果候选全部被过滤：

- 返回 `INCOMPLETE_LIMIT`；
- reason = `sharded_pulse_hidden_negative_worker_impact_filtered_empty`；
- `global_certificate_capable=False`；
- `final_judge_certificate_capable=False`；
- 不向 RMP 添加列。

filter 运行在 worker sanitize 之后，也就是输入候选已经逐条通过 `manual_journey_reduced_cost()` true-RC negative 过滤。

### 2. 日志字段

新增 worker payload 字段：

- `pulse_worker_impact_filter_enabled`
- `pulse_worker_impact_filter_mode`
- `pulse_worker_impact_filter_candidate_count`
- `pulse_worker_impact_filter_selected_count`
- `pulse_worker_impact_filter_dropped_count`
- `pulse_worker_impact_filter_selected_new_task_set_count`
- `pulse_worker_impact_filter_selected_replacement_task_set_count`
- `pulse_worker_impact_filter_selected_active_support_changing_count`
- `pulse_worker_impact_filter_selected_weak_replacement_count`

### 3. A/B profile

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增显式 opt-in profile：

- `strict_worker_current_probe_impact`

它等价于 current probe worker，但开启：

```text
journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=require_new_or_active_support
```

默认 profile 顺序不包含该 profile。

## Focused tests

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_worker_impact_filter_keeps_new_and_active_support \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_worker_impact_filter_empty_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_negative_runs_without_previous_signal \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_empty_negative_result_not_certificate
```

结果：

```text
Ran 4 tests in 0.044s
OK
```

## A/B smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7p_column_impact_filter_ab_20260612 \
--instances apollo5 tranq5 apollo10 tranq10_09 tranq10_04 tranq10_01 \
--profiles baseline audit_only strict_worker_current_probe strict_worker_current_probe_impact \
--time-limit 6.0 \
--audit-time-limit 0.2 \
--worker-time-limit 0.2 \
--current-probe-time-limit 0.2 \
--pricing-time-limit 0.1 \
--max-cg-iterations 4 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7p_column_impact_filter_ab_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_column_impact_filter_ab_20260612/summary.csv`

## 结果摘要

| instance | unfiltered returned/added | impact selected/dropped | impact added | impact composition | next RMP objective delta |
|---|---:|---:|---:|---|---:|
| Apollo5 | 0 / 0 | 0 / 0 | 0 | gate: `current_probe_instance_too_small` | - |
| Tranquillitatis5 | 0 / 0 | 0 / 0 | 0 | gate: `current_probe_instance_too_small` | - |
| Apollo10 | 2 / 2 | 1 / 2 | 1 | 1 active replacement | -0.220167 |
| tranq10_09 | 4 / 4 | 2 / 3 | 2 | 1 new task-set + 1 active replacement | -8.209058 |
| tranq10_04 | 0 / 0 | 0 / 0 | 0 | gate: `not_certificate_candidate` | - |
| tranq10_01 | 0 / 0 | 0 / 0 | 0 | gate: `not_certificate_candidate` | - |

关键观察：

- Apollo10：impact filter 从 3 个候选中选 1 个 active support-changing replacement，仍保留同样的下一轮 RMP objective movement。
- tranq10_09：impact filter 从 5 个候选中选 2 个，保留 1 个 new task-set 和 1 个 active support-changing replacement，仍保留明显 RMP movement。
- 5-task small-fast guard 仍然有效。
- filter 全程只改变 worker returned columns，不产生 certificate / official lower-bound effect。

## 当前判断

Phase 7P-alt 给出比 Phase 7O 更好的 worker 返回列质量：

- 少返回弱 replacement；
- 保留 new/support-changing signal；
- 没有破坏 exactness 边界；
- 仍未证明 wall-time ROI。

下一步不应默认启用 worker。若继续 worker 主线，应在更长 hard-tail run 上比较：

- unfiltered current probe；
- impact-filtered current probe；
- legacy final judge calls；
- completion-bound retry；
- wall time；
- gap / OPTIMAL count。

暂时不要做：

- official certificate gate；
- 20/100 A/B；
- resume / parallel；
- 提高 worker time limit；
- production default enable。
