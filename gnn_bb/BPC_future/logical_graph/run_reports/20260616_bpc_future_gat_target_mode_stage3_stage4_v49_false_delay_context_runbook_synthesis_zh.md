# GAT Target Mode Stage 3/4 v49 False-delay Context Runbook 综合报告

日期：2026-06-16

## 结论

本报告承接 v48：v48 已把 v41 false HIGH_PRIORITY-on-delay catalog 转成
`sector-wave|20` context-local hard-negative 采样计划；v49 进一步把 15 个
materialized true-RC negative target 转成 guarded target-priority worker A/B
runbook。

本阶段仍不运行 BPC、pricing、RMP、worker 或 certificate。v49 的产物只是下一轮
显式 opt-in worker A/B 的命令集合，用于判断这些 false-delay context 下的 true-RC
negative target 是否会改善或拖累 RMP trajectory。

## 机器字段

```text
stage = stage3_stage4_v49_false_delay_context_runbook
individual_runbook_status = ready
individual_candidate_group_count = 15
individual_command_count = 32
context_batch_runbook_status = ready
context_batch_candidate_group_count = 5
context_batch_command_count = 12
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## 输入与输出

输入候选：

```text
BPC_future/results/gat_batch_impact_false_delay_context_plan_v48_v39_20260616/multibatch_intervention_plan/candidates.json
```

逐候选 attribution runbook：

```text
BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/summary.json
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_stage4_v49_false_delay_context_individual_runbook_zh.md
```

同 context batch pilot runbook：

```text
BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/summary.json
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_stage4_v49_false_delay_context_batch_runbook_zh.md
```

## Context 覆盖

| context | family | region | false-delay FP | candidate groups batch=1 | candidate groups batch=3 | action |
| --- | --- | --- | ---: | ---: | ---: | --- |
| ac056820151e9ad7 | sector-wave | tranquillitatis | 33 | 3 | 1 | collect_same_context_false_delay_hard_negative_contrast |
| b6d808ebac2a6dd8 | sector-wave | apollo15 | 4 | 3 | 1 | collect_same_context_false_delay_hard_negative_contrast |
| 79fde658840fe2b8 | sector-wave | tranquillitatis | 4 | 3 | 1 | collect_same_context_false_delay_hard_negative_contrast |
| ac15bc4e7e3d6fff | sector-wave | tranquillitatis | 2 | 3 | 1 | collect_same_context_false_delay_hard_negative_contrast |
| 7b430465c7ae76b3 | sector-wave | tranquillitatis | 1 | 3 | 1 | collect_same_context_false_delay_hard_negative_contrast |

## Runbook 对比

| runbook | worker_batch_size | candidate groups | command count | 用途 |
| --- | ---: | ---: | ---: | --- |
| individual | 1 | 15 | 32 | 逐 target attribution；能定位哪个 true-RC negative 触发拖尾或弱 ROI |
| context_batch | 3 | 5 | 12 | 低成本 first-tranche pilot；同一 context 的 3 个 target 一次物化，先判断 context-level 方向 |

两套 runbook 的共同检查均为 true：

- candidate instance 存在；
- candidate context fields 完整；
- 5/10 no-regression 命令不启用新 worker；
- candidate baseline / worker 命令保留主线 learning 以复现 capture context；
- worker 命令带 expected context hash；
- candidate baseline / worker 命令开启 counterfactual replay capture；
- worker 命令不启用 certificate 或 official lower-bound shortcut；
- fixed worker 禁用 Pulse search / harvest / archive / bound pruning；
- target materialization payload 存在；
- arc-option 中的 `->` 已由 `shlex.join` 引用，避免 shell 重定向。

## 推荐执行顺序

先跑 `context_batch`，不是直接跑全部 `individual`。

原因：

1. 当前问题是 context-local false-delay ranking，不是单个 target 先验好坏；
2. `context_batch` 只需要 12 条命令，能先给 5 个 context 的方向性信号；
3. 若某个 context batch 明显改善 RMP trajectory，再用 `individual` 拆分 attribution；
4. 若某个 context batch 增加 pricing / exact retry / RMP solves 或无 ROI，则这些 true-RC negative 应作为 hard-negative / DELAY_QUEUE 训练证据；
5. worker 结果在验证 expected context reachability 和 target causal match 前，不能直接并入训练标签。

## 训练含义

v49 的目标不是证明 GAT 可以 online admission，而是补 Stage 3 缺失的监督：

```text
same RMP context:
  true-RC negative that improves trajectory -> HIGH_PRIORITY positive
  true-RC negative that worsens tail / no ROI -> DELAY_QUEUE hard negative
```

只有 worker A/B 返回真实 trajectory ROI 后，才能把这些样本用于下一版
`precision-constrained ROI maximization` 训练。单纯 `rc < 0` 仍不能作为 high-quality
label。

## 边界

- v49 不运行 BPC / pricing / RMP / worker；
- v49 不改变 official benchmark config；
- v49 不启用 production scheduler；
- v49 不产生 official lower bound；
- v49 不参与 no-negative certificate；
- true-RC negative 低 ROI 只能进入 hard-negative / DELAY_QUEUE 语义，不能永久丢弃；
- 最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下 exact pricing exhaustive closure。

## 下一步

下一步若要继续推进，应执行 `context_batch_worker_ab_runbook` 的 5 个 context-level A/B
pilot，并用现有 worker A/B audit 汇总：

```text
expected context reached?
target materialization matched?
primal / objective improved?
RMP solves reduced?
pricing calls reduced?
exact pricing calls reduced?
tail retry reduced?
dual_bound / certificate status unchanged?
```

如果 context miss，则不贴标签，只把实际到达的 capture context 回流到下一轮 v50
candidate extraction。
