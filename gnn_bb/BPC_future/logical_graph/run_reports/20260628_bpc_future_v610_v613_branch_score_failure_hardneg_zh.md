# 20260628 V610-V613 Branch Score 高分失败回灌总结

## 背景

V608 hybrid score map 在 V545 full60 失败实例上仍存在高分误报。V609 对 4 个 V608 高分 opt-in 候选做了真实 600s score-horizon 复跑，结果全部为 `EXTERNAL_TIME_LIMIT`，gap 可用但未闭环。

这说明当前问题不是缺少一个更高分的 pair，而是 score 仍会把搜索带进 completion-bound proof tail。

## V610：失败运行转 hard negative evidence

新增脚本：

```text
BPC_future/scripts/build_journey_branch_score_failure_evidence.py
```

输入：

```text
BPC_future/results/journey_branch_score_ab_runbook_v609_v608_highscore_external_20260628/runs
```

输出：

```text
BPC_future/results/journey_branch_score_failure_evidence_v610_v609_v608_highscore_external_20260628/
```

关键数字：

```text
result_rows = 4
nonoptimal_result_rows = 4
branch_events = 168
scored_branch_events = 166
hard_negative_rows = 166
tree_policy_rows = 166
completion_bound_retry_count = 179
ordinary_retry_count = 4
status_counts = {"EXTERNAL_TIME_LIMIT": 4}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

这些 label 是 diagnostic hard negative / right-censored proof-tail risk，不是 strict wall-time regression label。

## V611/V612：数据集回灌

V611 先验证 V610 行能被 tree-policy 数据链路消费：

```text
BPC_future/data/gat_branch_action_sanity/v611_v610_failure_hardneg_20260628/
sample_count = 166
tree_policy_label_counts = {"tree_policy_proof_tail_hard_negative": 166}
```

随后合并 V607 原数据和 V611：

```text
BPC_future/data/gat_branch_action_sanity/v612_v607_plus_v610_failure_hardneg_20260628/
sample_count = 1147
tree_policy_positive = 31
tree_policy_hard_negative = 936
tree_policy_proof_tail_hard_negative = 180
walltime_gain_positive = 31
```

这样保留原正例，同时加入 V609 失败路径 hard negative，避免模型只学习“全部否定”。

## V612：重新训练

checkpoint：

```text
BPC_future/data/gat_branch_action_sanity/v612_v607_plus_v610_failure_hardneg_20260628/gat_branch_action_v612.pt
```

metrics：

```text
BPC_future/results/gat_branch_action_v612_v607_plus_v610_failure_hardneg_20260628/summary.json
```

训练 8 epoch，按 `validation_total` 选 checkpoint；最优是 epoch 2：

```text
best_validation_total_loss = 3.9433
validation weighted rows = 23
validation precision = 0.8261
validation recall = 1.0
```

后续 epoch train loss 继续下降但 validation 波动上升，说明新增 hard negative 对分布有冲击，不能把 V612 直接视为 production-ready。

## V612 score map 审计

导出位置：

```text
BPC_future/results/gat_branch_action_v612_v607_plus_v610_failure_hardneg_20260628/score_map_v612_on_v545_full60_hybrid_top200/
```

和 V608 相同口径：

```text
score_row_count = 18823
score_min = 0.865602
score_mean = 0.889534
score_max = 0.927656
production_ready = false
```

对 V609 的 166 条 hard negative 精确匹配：

```text
V608: min=0.633496, mean=0.858090, max=0.961735, >=0.90:57, >=0.95:10
V612: min=0.866050, mean=0.884404, max=0.904580, >=0.90:6,  >=0.95:0
```

结论：

- V612 确实消除了 V609 hard negative 的 `>=0.95` 极端高分。
- 但整体分数仍偏高，hard negative mean 反而上升到 `0.8844`。
- 只靠训练校准还不够，仍需要 evidence overlay 或更强的 pairwise/context negative 构造。

## V613：训练校准 + evidence overlay

输出：

```text
BPC_future/results/gat_branch_action_v612_v607_plus_v610_failure_hardneg_20260628/score_map_v613_v610_failure_overlay_on_v612_hybrid/
```

叠加结果：

```text
score_row_count = 18823
overlay_counts = {"suppress_timeout_hard_negative": 166}
suppress_score = 0.03
production_ready = false
```

V613 把 V609 已验证失败的 166 条 selected branch rows 全部压到 `0.03`。这是当前更安全的 opt-in 候选，但仍不是 production-ready，因为它只覆盖已观测失败 context。

## 精确性边界

本轮所有产物都是 offline / diagnostic：

- 不运行 BPC / pricing / RMP；
- 不产生 official lower bound；
- 不产生 certificate；
- 不参与剪枝；
- 只能用于 opt-in branch ordering 或训练数据构建。

求解精确性仍必须由 exact pricing closure / final judge / BPC certificate 保证。

## 当前判断

V610-V613 解决了一个具体问题：V608 对已失败 proof-tail 路径的极端高分误报可以被识别、回灌并压制。

但这还没有证明 20-scale full60 能更快 OPTIMAL。原因是：

- V609 失败路径只是 4 个实例；
- V612 训练后整体分数仍偏高；
- V613 overlay 只对已观测 context 生效；
- 新 score map 还没有跑真实 opt-in smoke。

## 下一步

建议先跑 4-instance 或 12-instance smoke，不直接 full60：

1. 使用 V613 score map。
2. early branch 仍保持 off，先隔离 branch score 本身。
3. admission off，避免混入列调度变量。
4. retry on，保留 exact certificate 路径。
5. 对比 V545/V608/V613：
   - OPTIMAL 数；
   - capped mean；
   - gap；
   - completion-bound retry count；
   - selected pair 是否避开 V609 hard-negative rows；
   - 是否出现新的 high-score timeout context。

如果 V613 smoke 仍然没有改善，下一步应继续从失败 run 中采样新的 hard negative，而不是提高 score threshold。

## V614：V613 4-instance 真实 smoke

配置：

```text
instances = V609 四个高分失败实例
time_limit = 600s
max_workers = 4
score_map = V613
early_branch = off
admission = off
retry = on
```

结果目录：

```text
BPC_future/results/20260628_v614_v613_failure_overlay_smoke4_tasks20/
```

求解结果：

| instance | status | wall | gap | gap source |
|---|---:|---:|---:|---|
| seed61311 greedy-anchor 04 | EXTERNAL_TIME_LIMIT | 600.021s | 0.045087 | root_corrected_node_bound |
| seed61635 greedy-anchor 07 | EXTERNAL_TIME_LIMIT | 600.023s | 0.060588 | root_corrected_node_bound |
| seed61410 sector-wave 05 | EXTERNAL_TIME_LIMIT | 600.022s | 0.034203 | root_corrected_node_bound |
| seed61718 sector-wave 08 | EXTERNAL_TIME_LIMIT | 600.020s | 0.043777 | root_corrected_node_bound |

日志审计：

| instance | branch | changed | selected score min/mean/max | selected overlay rows | ordinary retry | completion-bound retry | pricing |
|---|---:|---:|---:|---:|---:|---:|---:|
| seed61311 | 31 | 11 | 0.876657 / 0.885463 / 0.895090 | 0 | 1 | 35 | 218 |
| seed61635 | 31 | 10 | 0.879477 / 0.888091 / 0.894144 | 0 | 1 | 38 | 255 |
| seed61410 | 37 | 20 | 0.872543 / 0.881073 / 0.887872 | 0 | 1 | 42 | 219 |
| seed61718 | 38 | 17 | 0.868528 / 0.874933 / 0.878989 | 0 | 1 | 63 | 319 |

结论：

- V613 没有再选中已被 overlay 压低的 V609 hard-negative rows，说明 evidence overlay 生效。
- 但 4/4 仍为 `EXTERNAL_TIME_LIMIT`，说明模型转向了新的高分 proof-tail 路径。
- 当前失败已经不是“同一个坑重复踩”，而是 score 函数整体仍不能区分会导致 expensive certificate tail 的分支。
- 单纯把已知失败 pair 压低不够；下一步需要把 V614 新失败路径继续转成 evidence，并引入更强的结构性惩罚，例如 completion-bound retry count、branch depth、child width、right-censored proof-tail density。
