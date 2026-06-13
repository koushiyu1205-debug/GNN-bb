# Sharded Pulse Phase 7O Hard-tail Worker ROI A/B 报告

日期：2026-06-12

## 目标

Phase 7O 不继续改算法，也不放开 official certificate gate。

本轮目标是回答一个窄问题：

current-context probe 能在 10-task hard-tail 中加到 true-RC negative columns，但这些列是否带来可观测 ROI？

这里的 ROI 主要看：

- worker 是否触发；
- worker 是否返回/加入 columns；
- 是否产生 new task-set 或 active support-changing replacement；
- worker 后下一轮 RMP objective / dual 是否移动；
- legacy final judge calls / completion-bound retry 是否下降；
- small-fast 5-task 是否被 gate 拦住；
- official result 是否只通过正常 add-column path 改变，不出现 certificate / lower-bound side effect。

## 实现摘要

扩展 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py`：

- 新增实例 preset：
  - `tranq10_01`
  - `tranq10_04`
- summary 新增 ROI 字段：
  - `solving_time`
  - `rmp_solves`
  - `pricing_calls`
  - `exact_pricing_calls`
  - `columns`
  - `legacy_final_judge_calls`
  - `legacy_final_judge_after_worker_calls`
  - `completion_bound_retry_count`
  - `exact_retry_calls`
  - `hidden_negative_audit_events`
  - `pulse_worker_added_new_journeys`
  - `pulse_worker_added_replacement_journeys`
  - `pulse_worker_added_new_task_set_count`
  - `pulse_worker_added_replacement_task_set_count`
  - `pulse_worker_added_support_changing_count`
  - `pulse_worker_addition_productivity_class`
  - `pulse_worker_next_rmp_objective_delta`
  - `pulse_worker_next_dual_l1_delta`
  - `pulse_worker_followup_legacy_final_judge_called`
  - `pulse_worker_followup_completion_retry_called`
  - `pulse_worker_followup_hidden_negative_found`

这些字段均从 existing solver result / JSONL logs 重建，不改变 solver 行为。

## A/B 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_hard_tail_worker_roi_ab_20260612 \
--instances apollo5 tranq5 apollo10 tranq10_09 tranq10_04 tranq10_01 \
--profiles baseline audit_only strict_worker_previous_signal_only strict_worker_current_probe \
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

- `BPC_future/results/sharded_pulse_phase7o_hard_tail_worker_roi_ab_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_hard_tail_worker_roi_ab_20260612/summary.csv`
- per-run JSONL logs

## 结果摘要

| instance | profile | worker returned/added | worker productivity | next RMP objective delta | next dual L1 delta | gate / signal |
|---|---:|---:|---|---:|---:|---|
| Apollo5 | strict current probe | 0 / 0 | none | - | - | `current_probe_instance_too_small` |
| Tranquillitatis5 | strict current probe | 0 / 0 | none | - | - | `current_probe_instance_too_small` |
| Apollo10 | strict current probe | 2 / 2 | active replacement | -0.220167 | 0.36586 | `current_context_probe` |
| tranq10_09 | strict current probe | 4 / 4 | active replacement + 1 new task-set | -8.209058 | 30.524704 | `current_context_probe` |
| tranq10_04 | strict current probe | 0 / 0 | none | - | - | `not_certificate_candidate` |
| tranq10_01 | strict current probe | 0 / 0 | none | - | - | `not_certificate_candidate` |

Previous-signal-only profile：

- 所有 relevant rows 都没有 previous audit signal；
- Apollo5 / Tranq5 / Apollo10 / tranq10_09 均 skip：`no_previous_audit_negative_signal`；
- tranq10_04 / tranq10_01 skip：`not_certificate_candidate`。

## 关键观察

### 1. Small-fast guard 生效

Apollo5 / Tranquillitatis5：

- audit-only 能看到 `FOUND_NEGATIVE` warning；
- strict current probe 被 min-task gate 拦住；
- worker 没有返回列；
- official result 与 baseline 保持一致。

这符合 Phase 7N/7O 的预期：小快实例不应被额外 worker/probe 拖慢。

### 2. 10-task 有真实加列信号

Apollo10：

- returned 2 / added 2；
- added columns 是 replacement；
- active support-changing count = 1；
- 下一轮 RMP objective delta = -0.220167；
- 下一轮 dual L1 delta = 0.36586。

tranq10_09：

- returned 4 / added 4；
- new task-set count = 1；
- replacement task-set count = 3；
- active support-changing count = 1；
- 下一轮 RMP objective delta = -8.209058；
- 下一轮 dual L1 delta = 30.524704。

这说明 current-context probe 不只是产生 weak duplicate；它至少在 tranq10_09 上产生了 new task-set，并让 RMP objective / dual 明显移动。

### 3. 还没有证明 wall-time ROI

本轮短时限 A/B 中：

- completion-bound retry count 没有下降；
- legacy final judge calls 没有下降；
- strict current probe profile 因多跑 probe / 多一轮 RMP，在 wall time 上比短 baseline 更长；
- Apollo10 / tranq10_09 的 positive signal 是 RMP movement，不是 wall-time speedup。

所以当前不能默认启用 worker，也不能提高 worker budget。

### 4. official certificate 边界保持

本轮没有放开：

- official certificate gate；
- official lower-bound effect；
- production default enable。

current probe 的所有影响都来自正常 add-column path。

## 当前判断

Phase 7O 结论：

- current-context probe 在 10-task hard-ish 样本中有真实加列能力；
- Apollo10 / tranq10_09 有可观测 RMP movement；
- 小实例 gate 有效；
- 但短时限 A/B 尚未证明 worker 会减少 legacy final judge tail 或 wall time；
- 不应默认启用 worker；
- 不应进入 official certificate gate。

## 建议下一步

如果继续 worker 主线，优先做：

Phase 7P-alt：column impact filter / active-support-aware return。

原因：

- Apollo10 的 columns 全是 replacement，只有 1 个 active support-changing；
- tranq10_09 有 1 个 new task-set，是更强信号；
- 下一步应优先返回 new task-set / active support-changing columns，而不是单纯最负 RC 或 replacement columns。

暂时不要做：

- 提高 worker time limit；
- 默认启用 worker；
- official certificate gate；
- 20/100 A/B；
- resume / parallel；
- cut/subset-row prefix bound。

## 验证

脚本语法检查通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py
```

Phase 7N 之后的全量回归仍为：

```text
Ran 443 tests in 47.323s
OK (skipped=1)
```
