# BPC_future GAT Target Mode Stage 3 v9 Random-wave Task50 进展报告

日期：2026-06-16

## 结论

本轮围绕 v8/v9 的主要 blocker 做窄口推进：random-wave validation 中存在
high-ROI opportunity，但当前模型 / threshold / kNN-OOD safe source 仍把 random-wave
整体放入 fallback delay。

本轮完成了三件事：

- v8/v9 opportunity mining 明确定位 random-wave missed high-ROI contexts；
- worker runbook 从 20-task-only 修成 candidate-scale，可生成 `task050_...` target-worker 命令；
- 跑通 task50 random-wave same-context target-materialization 数据链路，新增 2 条同 context worker rows，并合并训练 v9。

v9 仍不是 Stage 4 candidate。新增 random-wave 样本后，hard gate 数值仍只来自 sector-wave；
random-wave 在 validation 中继续 `accepted_batch_count=0`，`production_ready=false` 必须保留。

## 重新读计划后的方向确认

计划当前要求：

- GAT/CBF/kNN/OOD 只做 discovery / admission scheduling，不能做 pricing oracle；
- true-RC negative 只能被 finite delay，不能永久 reject；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure；
- Stage 3 训练目标是 `precision-constrained ROI maximization`，loss/F1/recall 不能抵消 precision / ROI / false-safe / coverage gate；
- Stage 4 前必须同时过 5/10 no-regression、20 ROI、certificate safety。

因此本轮没有修改 exact pricing、RMP、branch/cut 或 certificate path，只在 offline data / runbook / training artifact 上推进。

## v8/v9 Opportunity 定位

v8 opportunity mining：

```text
validation_record_count = 98
high_roi_opportunities = 25
missed_high_roi_opportunities = 4
random-wave high_roi_opportunities = 3
random-wave missed_high_roi_opportunities = 2
missed_reason_counts = {'no_candidate_above_threshold': 4}
```

random-wave 主要 missed contexts：

```text
a67f331bdb819d7d  task50  ROI=0.919112  max_candidate_score=0.331097 < threshold
e6b17bbf825984ae  task50  ROI=0.841521  max_candidate_score=0.312073 < threshold
```

v9 opportunity mining 后：

```text
validation_record_count = 100
high_roi_opportunities = 26
missed_high_roi_opportunities = 5
random-wave high_roi_opportunities = 4
random-wave missed_high_roi_opportunities = 3
```

新增的最高 missed random-wave context：

```text
5751b1799b606ad1  task50  ROI=4.385625
max_candidate_score = 0.301699
candidate_threshold = 0.487359
missed_reason = no_candidate_above_threshold
```

这说明新增样本把高 ROI random-wave 信号放进了 validation，但模型还没有学会给它足够高的 candidate score。

## Runbook 修复

问题：

- `build_gat_target_priority_worker_ab_runbook.py` 原本把所有 candidate worker profile 硬编码为 `task020_...`；
- single-run command 使用 `--instance`，但 `run_bpc_future.py` 实际参数是 `--instances`；
- 这会让 task30/50/100 random-wave target-worker runbook 名称和命令都不可靠。

修复：

- candidate command type 改成按候选 task count 命名，例如 `task050_...`；
- 30/50/100 暂无专用 config 时，显式记录 `scale_config_fallback_from_task20=true`，并通过命令行传入目标 logical graph；
- single-run command 改为 `--instances`；
- checks 改为读取 `baseline_command_type` / `worker_command_type`，不再只检查 `task020_...`。

验证：

```text
test_gat_target_priority_worker_ab_runbook: Ran 5 tests OK
```

## v9 Random-wave Task50 Plan / Runbook

v9 intervention plan：

```text
candidate_count = 26
selected_context_count = 8
pairwise_context_target_count = 7
candidate_family_region_counts = {'random-wave|tranquillitatis_balmer_like_20km': 26}
candidate_task_count_counts = {'50': 26}
require_opportunity_context = true
all_checks_pass = true
```

scale-aware worker runbook：

```text
candidate_group_count = 26
candidate task counts = [50]
scale_config_fallback_from_task20 count = 26
first worker command type starts with task050_
--instances present = true
--instance present = false
all_checks_pass = true
production_ready = false
official_bound_effect = false
```

## Worker Probes

### a67f high-ROI context

目标：

```text
context = a67f331bdb819d7d
task50 random-wave
opportunity_score = 0.919112
```

85s run 到 cg44，未到 expected context。

150s run 到 cg48，但 replay context 漂移：

```text
expected_context = a67f331bdb819d7d
actual cg48 context = d358ecd499b79738
worker skip reason = residual_target_context_mismatch
row_count = 0
```

结论：该 high-ROI context 来自 bulk capture profile，当前 target-worker replay profile 不能直接复现。继续盲目加时间不是正确方向，需要 profile-aligned replay 或从实际到达 contexts 重新抽 target。

### 5751 reachable context

实际 replay path 会到达：

```text
context = 5751b1799b606ad1
cg_iter = 44
```

本轮跑了两个 same-context target worker：

```text
mb1 target = [4, 40, 3]
best_true_reduced_cost = -11.539468769
objective_improvement = 4.385625
new_task_set_count = 1

mb2 target = [4, 8, 25, 32, 45, 9]
best_true_reduced_cost = -2.633324538
objective_improvement = 0.024858
new_task_set_count = 1
```

worker rows：

```text
row_count = 2
context_count = 1
largest_context_size = 2
pairwise_context_count = 1
positive_objective_improvement_count = 2
has_same_context_pairs = true
all_checks_pass = true
```

这证明 task50 random-wave target-materialization worker -> same-context rows -> dataset 的链路可用。

## v9 Dataset / Training

v9 dataset 合并 v8 mixed rows 与本轮 v9 task50 rows：

```text
sample_count = 322
candidate_count = 4597
batch_label_counts = {'non_improving': 67, 'roi_positive': 255}
candidate_label_counts = {'delay_queue': 322, 'high_priority': 4275}
family_counts = {'greedy-anchor': 54, 'random-wave': 195, 'sector-wave': 73}
task_count_counts = {'5': 2, '10': 8, '20': 144, '30': 76, '50': 91, '100': 1}
random-wave same_context_pair_count = 9
task50 same_context_pair_count = 3
ranking_ready = true
training_ready = true
all_checks_pass = true
```

v9 training：

```text
training_objective = precision_constrained_roi_maximization
best_epoch = 4
best_loss_epoch = 8
pairwise_ranking_loss_active = true
selected_checkpoint_reason = local_deployment_gate_passed_then_ranked_by_utility_roi_loss
checkpoint_gate_pass = false
stage4_candidate_ready = false
```

v9 selected metrics：

```text
accepted_batch_count = 35
accepted_batch_roi = 8.824355633769716
accepted_batch_roi_ci_low = 4.923453034500176
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.9927495311806395
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
family_delay_fallback_families = ['greedy-anchor', 'random-wave']
```

v9 KNN/OOD (`knn_k=3`, `max_neighbor_delay_fraction=0.34`)：

```text
accepted_batch_count = 35
accepted_batch_roi_ci_low = 4.923453034500176
safe_precision_ci_low = 0.9010957324106112
false_safe_rate_union = 0.0
production_ready = false
production_block_reasons = ['family_holdout_accepted_batch_missing', 'validation_candidate_not_ready']
```

family audit：

```text
random-wave accepted_batch_count = 0
random-wave oracle_high_roi_count = 4
random-wave max_accepted_batch_roi_label = 4.385624885559082
missing_accepted_opportunity_families = ['random-wave']
```

## Exactness Boundary

本轮所有新增 artifact 均保持：

```text
diagnostic_only = true
runs_bpc_or_pricing = false  # dataset/training/audit scripts
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
production_ready = false
```

实际 worker probes 只用于 target-materialization data collection，结果为 `TIME_LIMIT`，
`dual_bound=None`，不构成 proof 或 bound。

## 下一步

1. 不要继续盲跑 `a67f...`：先做 profile-aligned replay，解释 bulk capture context 为什么在 worker profile 下变成 `d358...`。
2. 优先跑 `5751...` 同 context 剩余 targets，形成更多强/弱 ROI pair；当前只有 2 条 positive rows，还不足以让模型解除 random-wave fallback。
3. 增加训练/threshold 对 family-local ranking 的压力：random-wave 现在有 high ROI label，但 candidate score 仍被压在阈值下方。
4. 只有 random-wave 至少有 accepted high-ROI opportunity 且 family holdout ROI / precision 过硬门槛后，才能重新讨论 Stage 4 safe source。
