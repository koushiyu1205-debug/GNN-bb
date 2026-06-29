# 20260627 V464 Full-60 Score-Gated Branch Ordering 报告

## 结论

V464 在 random-TW canonical 20-scale 60 个实例上完成全量测试。该版本只启用保守的 branch score selection gate，不启用 early branch，也不启用 admission；因此它只改变 Ryan-Foster 分支候选排序，不影响 official bound、certificate 或剪枝逻辑。

结果相对 baseline 有明确净收益：

- OPTIMAL：`26/60 -> 31/60`
- capped mean：`381.77s -> 353.77s`
- `<=200s OPTIMAL`：`20/60 -> 22/60`
- `>5s` win/loss/tie：`13/0/47`
- `TIME_LIMIT/EXTERNAL_TIME_LIMIT -> OPTIMAL`：`5`
- `OPTIMAL -> TIME_LIMIT/EXTERNAL_TIME_LIMIT`：`0`

相对 20260626 消融报告中的当前 best `early branch on + branch + admission`，V464 的 capped mean 更低：`361.46s -> 353.77s`，OPTIMAL 数更多：`30/60 -> 31/60`。但它仍未达到本轮最终目标：`20-scale 60/60 OPTIMAL within 600s`。

## 配置边界

V464 使用：

- `journey_branch_candidate_priority=branch_score_horizon`
- `journey_branch_candidate_score_path=.../score_map_v463_conservative_overlay_on_branchonly60/journey_branch_score_rows.json`
- `journey_branch_candidate_score_selection_gate_enabled=true`
- `journey_branch_candidate_score_selection_gate_min_score=0.67`
- `journey_branch_candidate_score_selection_gate_max_pool_total_child_width=850`
- `journey_branch_candidate_score_selection_gate_max_pool_child_width=450`
- `journey_branch_candidate_score_selection_gate_max_pool_balance_gap=100`
- early branch 全关
- admission scheduler 未启用

输出目录：

`BPC_future/results/20260627_v464_v463_conservative_overlay_score_selection_gate850_randomtw60_tasks20/`

## 指标对比

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 26 | 4 | 30 | 20 | 381.77 | 123.38 | 53.78 | 577.87 | 600.00 | 600.00 | 600.00 |
| V464 | 60 | 31 | 3 | 26 | 22 | 353.77 | 145.42 | 94.80 | 375.29 | 600.00 | 600.00 | 600.00 |

差异：

| metric | value |
|---|---:|
| `>5s` win/loss/tie | `13/0/47` |
| `>30s` improve/regress | `6/0` |
| `>100s` improve/regress | `6/0` |
| `TIME_LIMIT/EXTERNAL -> OPTIMAL` | `5` |
| `OPTIMAL -> TIME_LIMIT/EXTERNAL` | `0` |

## 关键正收益实例

| instance | baseline | V464 | gain |
|---|---:|---:|---:|
| tranq greedy seed61414 | TIME_LIMIT 555.75 | OPTIMAL 94.80 | +460.94 |
| tranq greedy seed61001 | OPTIMAL 327.75 | OPTIMAL 56.90 | +270.85 |
| tranq random seed61411 | EXTERNAL 600.00 | OPTIMAL 339.28 | +260.72 |
| apollo greedy seed61000 | EXTERNAL 600.00 | OPTIMAL 342.41 | +257.59 |
| tranq sector seed61923 | EXTERNAL 600.00 | OPTIMAL 408.17 | +191.83 |
| tranq greedy seed61103 | EXTERNAL 600.00 | OPTIMAL 447.10 | +152.90 |

## Gate 审计

日志事件：

- `journey_branch_candidates`：624
- `journey_branch`：624
- `journey_tail_action_no_column_early_branch_gate`：917
- `journey_fathom`：166
- `journey_early_branch_trigger`：0

branch score selection gate：

- `ok`：6
- `score_below_min`：31
- `missing_score_source`：587

真正改变 selected pair 的事件只有 6 个，全部发生在 root node，并且全部对应大正收益：

| instance | baseline pair | selected pair | score | result |
|---|---|---|---:|---|
| tranq greedy seed61001 | `[2,18]` | `[3,4]` | 0.74 | +270.85s |
| tranq greedy seed61414 | `[13,16]` | `[6,20]` | 0.74 | +460.94s |
| tranq greedy seed61103 | `[10,15]` | `[6,15]` | 0.74 | +152.90s |
| apollo greedy seed61000 | `[3,7]` | `[12,20]` | 0.74 | +257.59s |
| tranq random seed61411 | `[1,9]` | `[2,10]` | 0.74 | +260.72s |
| tranq sector seed61923 | `[1,13]` | `[13,20]` | 0.74 | +191.83s |

exact-safe 审计：

- early branch 没有触发。
- tail-action early branch gate 全部未通过，原因是 `before_final_probe_disabled`。
- 本轮收益不是来自提前剪枝，也不是来自把 RMP objective 当 exact bound。
- learning 只改变分支排序；节点闭环仍由原 exact pricing/proof 逻辑完成。

## 分组表现

| family/site | V464 status | capped mean | mean gain | wins >5s |
|---|---|---:|---:|---:|
| greedy/apollo | 3 OPT, 2 TL, 5 EXT | 467.06 | +29.97 | 5 |
| greedy/tranq | 5 OPT, 5 EXT | 376.44 | +88.62 | 3 |
| random/apollo | 6 OPT, 1 TL, 3 EXT | 264.60 | +1.22 | 0 |
| random/tranq | 6 OPT, 4 EXT | 293.98 | +26.32 | 1 |
| sector/apollo | 6 OPT, 4 EXT | 296.27 | +1.47 | 2 |
| sector/tranq | 5 OPT, 5 EXT | 424.29 | +20.39 | 2 |

## 解释

V464 证明了当前 branch score 方向是有效的：只要 gate 真的命中高置信 root pair，完整求解闭环时间会大幅下降，而且这 6 个命中没有产生退化。

但 V464 同时暴露了主问题：覆盖率太低。624 个 branch candidate 事件中，只有 6 个通过 gate 并改写 selected pair；大量事件是 `missing_score_source`，另有一部分是 `score_below_min`。因此大多数未最优实例仍然按 baseline 分支路径走，最终继续 600s 超时。

这说明下一步不应先调低 gate 阈值裸放开。正确方向是补充严格 replay 标签，尤其是 v464 仍未 OPTIMAL 的 29 个实例的 root pair 反事实，扩大 score map 对难 context 的覆盖，再逐步放宽 gate。

## 后续动作

已生成 V465 runbook：

`BPC_future/results/journey_branch_candidate_replay_runbook_v465_v464_nonopt_root_positive_neighbor_20260627/`

输入是 V464 仍未 OPTIMAL 的 29 个实例，只取 root depth 0 的候选，`positive_neighbor` 策略抽取 48 条 full replay forced-pair 任务，并排除 V456 已跑过的条目。

V465 的目标是继续找严格正例和 hard negative：

- 如果 forced pair 把 V464 非最优实例变成 OPTIMAL，就是新的强正例。
- 如果 forced pair 仍超时或明显更慢，就是 hard negative。
- 新增标签合并进 v457/v464 数据集后，再训练下一版 branch action GAT，并导出覆盖更高的 score map。

当前最终目标仍未完成：20-scale random-TW 60-instance 尚未达到 `60/60 OPTIMAL within 600s`。
