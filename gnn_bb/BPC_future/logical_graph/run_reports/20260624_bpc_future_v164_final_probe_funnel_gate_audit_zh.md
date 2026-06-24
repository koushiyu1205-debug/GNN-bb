# BPC_future V164 Final-probe funnel gate audit

日期：2026-06-24

## 背景

第一优先级是修正 Final-probe 触发和停止策略。为了避免继续修低频边角路径，先对 canonical random-TW 20 full600 日志做只读统计：

```text
input = BPC_future/results/logs_20260624_full600_randomtw60_tasks20_parallel4
log_files = 60
```

## 统计结果

`journey_exact_pricing_completion_bound_retry` 的 trigger 分布：

```text
profile_exhausted_no_column = 799
no_retry_budget = 109
empty/unknown = 27
```

`profile_exhausted_no_column` 按 depth 的主要分布：

```text
depth3 = 145
depth4 = 141
depth2 = 120
depth5 = 85
depth1 = 72
depth6 = 69
depth0 = 49
```

这说明 `profile_exhausted_no_column` 是当前 20-scale completion-bound/final-probe funnel 的主路径。旧 full600 日志没有可用的 tail-action 分类行，因此无法直接判断这 799 次里哪些是 D 类、A 类、B 类或 C 类。

## 代码改动

V164 修改 `tail_action_no_column_branch_payload`：

- 当 `before_final_probe=True` 且 `journey_tail_action_no_column_early_branch_before_final_probe_enabled=False` 时，不再静默返回；
- 如果 `journey_tail_action_audit_enabled=True` 且 gate audit 未关闭，记录 `journey_tail_action_no_column_early_branch_gate`；
- 该 audit row 的 `gate_reason=before_final_probe_disabled`；
- 同时写入 `tail_action`、`tail_action_reason`、`rmp_to_incumbent_gap`、`recent_true_rc_productivity`、`recent_active_support_additions`、`recent_rmp_objective_progress` 等字段。

## 精确性边界

V164 不改变求解行为：

- 不触发 early branch；
- 不调用 width guard；
- 不改变 lower bound；
- 不剪枝；
- 不产生 certificate；
- 不产生 official bound。

它只是让默认 canonical 600s 诊断在行为门关闭时也能看到 “这个主 funnel 如果交给 Tail Action Controller 会被怎么分类，以及为什么没有执行”。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. MPLCONFIGDIR=/tmp/mplconfig_bpc_future \
  /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_audits_before_final_probe_when_behavior_disabled \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_branches_before_final_probe_when_opted_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_branches_before_duplicate_retry_when_opted_in \
  BPC_future.tests.test_journey_tail_action_controller_audit

PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py

git diff --check
```

结果：通过。

## 结论

V164 不是加速证据。它把未来 full600 20-scale 诊断的观测面补齐，使主路径 `profile_exhausted_no_column` 能被 Tail Action Controller 分类。下一步应在 canonical 20-scale 小批探针中打开 audit，确认这些 gate rows 的 D/C/A/B 比例，再决定是否扩大 no-column D 类 opt-in 或转向 branch-impact/incumbent/cuts。
