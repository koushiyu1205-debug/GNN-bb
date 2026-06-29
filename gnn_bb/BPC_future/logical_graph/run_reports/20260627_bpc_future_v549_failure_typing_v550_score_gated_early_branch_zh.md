# 20260627 V549 / V550：V545 剩余失败分型与 Score-Gated Early Branch Smoke

## 结论摘要

V545 当前是 20-scale random-TW 60-instance 的最佳分支排序版本：

- `36/60 OPTIMAL`
- `21 EXTERNAL_TIME_LIMIT`
- `3 TIME_LIMIT`
- capped mean `341.542949s`
- `<=200s OPTIMAL = 22/60`

V549 对 V545 的 60 个 JSONL 事件日志做了 failure typing。结论很明确：

| primary failure type | count |
|---|---:|
| `branch_tree_plus_completion_tail` | 21 |
| `completion_bound_proof_cost` | 2 |
| `lp_bound_below_incumbent` | 1 |

V550 进一步用 4 个代表性未解实例测试 V543 score-gated early branch。中途审计显示：

- early branch trigger：0
- no-column early branch trigger：0
- score gate pass：0
- selected pair changed：0
- exact-safe 异常：0

因此 V550 被提前停止；继续跑到 600 秒只会复现 V545 失败路径。

这说明当前问题不是 early branch 代码没有打开，而是当前 V543 score map 在这些失败 context 上没有足够高置信命中；score-gated early branch 按设计 fail-closed，没有改变求解轨迹。

## V549 输入与产物

输入：

`BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs/**/*.jsonl`

诊断产物：

- completion tail：`BPC_future/results/journey_completion_tail_profile_v549_v545_full60_20260627/summary.json`
- branch impact：`BPC_future/results/journey_branch_impact_audit_v549_v545_full60_20260627/summary.json`
- tail action：`BPC_future/results/journey_tail_action_controller_v549_v545_full60_20260627/summary.json`
- failure typing：`BPC_future/results/journey_failure_typing_v549_v545_full60_20260627/summary.json`

报告：

- `BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_completion_tail_profile_v549_v545_full60_zh.md`
- `BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_branch_impact_v549_v545_full60_zh.md`
- `BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_tail_action_controller_v549_v545_full60_zh.md`
- `BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_failure_typing_v549_v545_full60_zh.md`

这些脚本都是 diagnostic-only，只读日志，不运行 BPC / pricing / RMP。

## V549 关键数字

Completion-tail 汇总：

- completion retry class：
  - `completion_bound_certified_no_negative`: 55
  - `completion_bound_found_negative`: 2
  - `completion_bound_time_limit_no_column_uncertified`: 3
- incomplete tail count：3
- total profile generation time：`8289.953808s`
- tail min-fill candidate：74
- tail min-fill applied：0

Branch-impact 汇总：

- branch count：566
- right-censored branch count：429
- usable branch-impact training count：137
- unprocessed child count：395
- tail class：
  - `completion_bound_tail`: 365
  - `negative_chain_continues`: 10
  - `unprocessed_children`: 191
- total child completion-bound retries：2435
- total child exact pricing events：2919
- total child negative pricing events：2018

Tail-action controller 汇总：

- A frontier refinement：0
- B broad plateau：392
- C continue CG：839
- D early branch candidate：1393
- fathom possible if RC zero：649
- actual early branch trigger：0

Failure typing 汇总：

- unsolved count：24
- `branch_tree_right_censored`: 21
- `branch_tree_too_wide_or_deep`: 19
- `completion_bound_proof_cost`: 23
- `negative_chain_continues`: 21
- `lp_bound_below_incumbent`: 21
- `root_no_branch`: 3
- `completion_bound_uncertified_time_limit`: 3

## V549 的解释

21/24 个未解不是单纯 root CG 或单个 root pair 的问题，而是“分支树继续展开 + completion-bound proof cost 高”的叠加问题。

这解释了 V546/V548 的负结果：

- V546 强制 root alternative pair，前 16 个有效样本全是外部 600 秒超时。
- V548 用成功实例聚合出的 family/site/depth policy，11 个失败样本全是外部 600 秒超时。

这些策略只改变浅层选择，不能解决深层 child 的 proof cost、right-censoring 和 completion-bound retry。

## V550 配置

V550 使用 4 个代表性 V545 未解实例：

- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718`
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410`
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311`
- `apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205`

配置：

- V543 branch score rows：
  `BPC_future/results/gat_branch_tree_policy_merged_overlay_v543_v467_plus_v540_20260627/journey_branch_score_rows.json`
- branch score ordering：ON
- admission：OFF
- regular early branch：ON
- tail-action early branch：ON
- no-column early branch before final probe：ON
- score gate：
  - min score `0.67`
  - require score source
  - require state key
  - max pool total child width `900`
  - max pool balance gap `200`

运行约 4 分钟后中止，因为事件日志已经显示所有 gate 都 fail-closed。

## V550 中途审计

| instance | branch events | selected score present | selected pair changed | score gate pass | early branch trigger | main gate reasons |
|---|---:|---:|---:|---:|---:|---|
| `apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205` | 0 | 0 | 0 | 0 | 0 | `score_below_min` |
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311` | 16 | 1 | 0 | 0 | 0 | `score_below_min`, `missing_score_source`, `depth_above_max` |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410` | 14 | 1 | 0 | 0 | 0 | `score_below_min`, `missing_score_source`, `depth_above_max` |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718` | 25 | 1 | 0 | 0 | 0 | `score_below_min`, `missing_score_source`, `depth_above_max` |

V550 没有产生 `results.csv` 有效完成行，因为它是中途诊断停止，不是完整求解实验。

## 为什么 V550 没起作用

V550 的 early branch 是 score-gated 的，不是裸开。当前 V543 score map 在这 4 个失败 context 上：

- root 或浅层分数低于阈值；
- 深层 state 没有 score source；
- 设定的 early branch 最大深度只有 1，超过后直接 fail-closed。

所以 solver 保持 exact-safe 回退，没有提前分支，也没有改变 pair selection。这是正确行为，但也说明当前 score map 覆盖不了这些失败状态。

## 对优化方向的影响

### 不应继续做的事

1. 不继续扩大 root top-k forced replay。
2. 不把 family/site/depth 成功路径当成泛化 production policy。
3. 不把 score-gated early branch 直接全量打开；当前 score 缺失时它不会触发。

### 应该继续做的事

1. 构造深层 branch path / child proof-cost 反事实数据。
   - 重点对象是 `branch_tree_plus_completion_tail` 的 21 个实例。
   - 关注 depth 1-4 的 selected path、child ordering、completion retry、time-to-certificate。

2. 把 V546/V548/V550 作为 hard negative / regression guard。
   - root alternative 不闭环；
   - 粗粒度 family/site 泛化不闭环；
   - score-gated early branch 无 score 时不触发。

3. 对 `completion_bound_proof_cost` 的 2 个 root/no-branch 实例单独优化 final-probe / CB-tail。
   - 这里 branch score 没有抓手。
   - 方向应是 completion-bound harvest、cache、min-fill、profile generation cost。

4. 对 `lp_bound_below_incumbent` 的 1 个实例不要继续用 pricing proof 硬顶。
   - 需要 incumbent、cuts、formulation 或能明显提高 child LP bound 的分支。

5. 下一版 branch score 需要预测“深层 path 是否能让 child 更快 certificate”，不是只预测 root pair 或局部 corrected-bound。

## 当前状态

V545 仍是当前最佳完整求解结果；V546/V548/V550 都没有超过它。

当前主线应从“继续试更多浅层 pair”切到：

`failure typing -> deep path replay / child proof-cost labels -> 新 score map -> 小规模 smoke -> full60`

否则继续全量跑只会增加大量 right-censored hard negative，不能有效推动 20-scale 60/60 OPTIMAL。
