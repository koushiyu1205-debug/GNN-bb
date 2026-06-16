# 2026-06-16 BPC_future GAT Target Mode Stage 4 Active-replacement Sequential Probe 报告

## 结论

本轮把上一份报告的结论继续推进：从 exact capture batch 中抽取 active-replacement
候选，并运行首个 active-only target-materialization worker。

核心结论：

- 可物化的 first-stage active-replacement 候选只有 `[15,20]`；
- `[15,20]` 单点物化确实触发 `active_replacement_task_set`；
- 但它没有通过 ROI gate，反而增加 RMP / pricing / exact 轮次和 timed-trip workload；
- 运行后新的 exact batch 在后续 context 中发现第二阶段 active-replacement `[1,9]`；
- 当前 worker 只支持单个 expected context，不能在同一 run 中表达 “context A 物化 `[15,20]`，context B 再物化 `[1,9]`” 的 sequential policy。

因此下一步不是把 active-replacement 单列直接上线，而是实现或离线评估 sequential
active-replacement policy：按当前 RMP context 选择下一批 target，而不是一次性固定一个静态白名单。

```text
first_stage_active_candidate = [15,20]
first_stage_active_roi_gate = failed
second_stage_active_candidate = [1,9]
multi_context_worker_needed = true
mutating_admission_ready = false
stage5_ready = false
```

## First-stage Candidate Extraction

输入 baseline log：

```text
BPC_future/results/gat_target_priority_worker_ab_v10_online_shadow_candidates_20260616/
task020_tranq20_ctxac056820_cg07_r02_tasks1_5_mainline_baseline/logs
```

抽取 artifact：

```text
BPC_future/results/gat_active_replacement_target_candidates_active_only_tranq20_01_20260616/candidates.json
```

结果：

```text
selected_candidate_count = 1
selected_category_counts = {'active_replacement': 1}
selected_task_sets = [[15, 20]]
```

说明：baseline `cg_iter=7` 的 `active_changed_task_set_samples` 是：

```text
[4,6]
[4,8]
[15,20]
```

但 captured returned_journeys 中只能反查到 `[15,20]`。`[4,6]` / `[4,8]`
是 active basis 变化样本，但不在当前 capture payload 的 returned journeys 中，不能直接作为 target-materialization 输入。

## First-stage A/B

shared baseline：

```text
status = TIME_LIMIT
primal = 632.987632
dual_bound = None
time = 53.477662
rmp/pricing/exact = 9/14/5
generated/evaluated = 30378/48696
columns = 236
```

active `[15,20]` worker：

```text
status = TIME_LIMIT
primal = 632.987632
dual_bound = None
time = 53.314711
rmp/pricing/exact = 11/17/6
generated/evaluated = 34828/58047
columns = 271
```

worker event：

```text
cg_iter = 7
worker_true_rc = -3.41733
returned_journeys = 1
active_changed_task_set_count = 1
addition_productivity_class = active_replacement_task_set
next_rmp_objective = 653.567981
```

后续 exact 仍需要：

```text
cg_iter = 9
exact_best_rc = -18.05904625
returned_journey_count = 45
active_changed_task_set_samples = [[1,9], [4,6], [4,8]]
addition_productivity_class = active_replacement_task_set
```

判定：

```text
single_active_replacement_roi_gate = failed
```

原因：虽然 `[15,20]` 是 active replacement，但它只产生小幅 immediate objective 下降，
并把后续 exact active batch 推迟到新的 context，导致总 RMP / pricing / exact 工作量增加。

## Second-stage Candidate

对 active `[15,20]` run 的后续 exact capture 再抽取：

```text
BPC_future/results/gat_active_replacement_target_candidates_stage2_after_15_20_tranq20_01_20260616/candidates.json
```

结果：

```text
selected_candidate_count = 1
selected_category_counts = {'active_replacement': 1}
selected_task_sets = [[1, 9]]
expected_context_hash = 7b430465c7ae76b3
true_rc = -1.397984
```

该候选不是 production safe-source；它说明 active-replacement trajectory 是 context-dependent sequential control。

## Exactness Boundary

本轮保持：

```text
diagnostic_only = true
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
default_enabled = false
```

所有运行仍为 `TIME_LIMIT` 且 `dual_bound=None`。最终 certificate 仍必须由 exact pricing
在当前 branch/cut/dual 下对完整配置宇宙执行 no-negative closure。

## 下一步

1. 增加 default-off 多 context target-materialization 实验能力，或先构建离线 sequential replay runbook；
2. 每个 context 的 target batch 必须独立 true-RC verified，且不能参与 certificate；
3. Stage 3 训练标签改成 sequential trajectory utility：单点 active replacement 不能自动标 positive；
4. 若多 context target 在 20-task 上稳定降低 exact tail，再进入 guarded opt-in A/B。
