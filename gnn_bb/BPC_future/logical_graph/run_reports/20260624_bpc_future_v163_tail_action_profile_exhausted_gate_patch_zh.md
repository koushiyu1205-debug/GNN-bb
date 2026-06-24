# BPC_future V163 Tail Action profile-exhausted final-probe gate 补丁

日期：2026-06-24

## 目的

补齐 Final-probe funnel 中一条漏掉的入口：`profile_exhausted_no_column` 路径在 profile repair 未加入列后，会直接准备进入 completion-bound final probe。V163 在该入口前增加同口径的 `tail_action_no_column_branch_payload(..., before_final_probe=True)`。

## 精确性边界

该补丁默认关闭。只有同时打开：

```text
journey_tail_action_no_column_early_branch_enabled=True
journey_tail_action_no_column_early_branch_before_final_probe_enabled=True
```

并且通过 min-tasks、context、depth、CG iter、productivity、width guard 等条件时，才可能把 D 类 no-column 节点转成 exact-safe early branch。

通过时仍然只继承已有合法 node lower bound：

- 不把当前 RMP objective 当 exact bound；
- 不用该 bound 剪枝；
- 不产生 official bound；
- 不产生 certificate；
- child 仍靠后续 exact pricing closure。

## 当前结论

V163 不是加速证据，也不改变 canonical random-TW 60-instance benchmark 默认行为。它只是把第一优先级“Final-probe 触发/停止策略”中漏掉的一条重型 CB 入口纳入 Tail Action Controller 口径，方便后续 opt-in A/B 看到该节点是被 gate 放行、拦下，还是继续进入 final probe。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_branches_before_final_probe_when_opted_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_branches_before_duplicate_retry_when_opted_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_respects_min_tasks_gate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_tail_action_no_column_respects_context_require_gate \
  BPC_future.tests.test_journey_tail_action_controller_audit

PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile BPC_future/solver/journey_driver.py
git diff --check
```

结果：通过。
