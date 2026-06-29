# V596/V597：timeout hard-negative overlay 与 root035 smoke4 结果

## 结论

V596 做成了一个离线 proof-risk overlay：把 V569 中已经确认的 4 条 root score timeout hard-negative pair 从 V543/V545 score map 中压到 `0.05`。V597 用同样 4 个 20-scale random-TW 实例、同样 `score>=0.35`、同样 strict state-key gate 复跑。

结果：**没有带来实际求解闭环改善**。

- V597：`0/4 OPTIMAL`，`4/4 EXTERNAL_TIME_LIMIT`。
- mean wall：`600.024s`。
- mean gap：`0.0483545`，只比 V569 的 `0.0485165` 小一点，不是求解加速。
- branch impact：`88` 个 branch 全部 right-censored，`usable_branch_impact_training_count=0`。
- child completion-bound retries：`349`，高于 V569 的 `323`。
- completion-tail profile time：`1006.103s`，高于 retry-on/gate/cap smoke 的约 `972-982s`。

这说明：只避开已知 root timeout hard negatives 不够。当前瓶颈仍是 deep branch context score 缺失和 child proof-cost 控制不足。

## 代码与产物

### 代码改动

`BPC_future/scripts/apply_gat_branch_score_proofrisk_overlay.py` 新增：

- `--timeout-evidence` 输入；
- 读取 `root_timeout_hard_negative_rows.jsonl`；
- 用 `log_file` 还原 canonical instance path；
- 对 `y_branch_score_hard_negative=1` 的 selected root pair 做 scoped suppression；
- 输出 `proofrisk_overlay=suppress_timeout_hard_negative`。

测试：

```text
python -m unittest BPC_future.tests.test_gat_branch_score_proofrisk_overlay
python -m unittest BPC_future.tests.test_journey_branch_timeout_evidence
```

结果均通过。

### V596 overlay

输入：

```text
base_score_rows = BPC_future/results/gat_branch_tree_policy_merged_overlay_v543_v467_plus_v540_20260627/journey_branch_score_rows.json
timeout_evidence = BPC_future/results/20260628_v569_branch_timeout_evidence/root_timeout_hard_negative_rows.jsonl
```

输出：

```text
BPC_future/results/gat_branch_tree_policy_v596_timeout_suppressed_overlay_v543_20260628/journey_branch_score_rows.json
```

overlay 统计：

```text
score_row_count = 20768
suppress_timeout_hard_negative = 4
score>=0.35: 1077 -> 1073
score>=0.67: 44 -> 44
score>=0.85: 30 -> 30
```

被压低的 4 条：

| instance | pair | old score | new score |
|---|---:|---:|---:|
| seed61103 | `[18,20]` | 0.382223 | 0.05 |
| seed61206 | `[16,17]` | 0.394574 | 0.05 |
| seed61717 | `[14,18]` | 0.370151 | 0.05 |
| seed61718 | `[15,17]` | 0.456029 | 0.05 |

## V597 smoke 设置

实例：同 V569 的 4 个 20-scale random-TW hard cases。

关键配置：

```text
journey_branch_candidate_priority=branch_score_horizon
journey_branch_candidate_score_path=BPC_future/results/gat_branch_tree_policy_v596_timeout_suppressed_overlay_v543_20260628/journey_branch_score_rows.json
journey_branch_candidate_score_require_state_key=True
journey_branch_candidate_score_selection_gate_enabled=True
journey_branch_candidate_score_selection_gate_min_score=0.35
journey_branch_candidate_score_horizon_tie_tolerance=1.0
early branch off
admission off
retry gate/cap off
600s external timeout
max-workers=4
```

结果目录：

```text
BPC_future/results/20260628_v597_v596_timeout_suppressed_root035_strict_state_smoke4_tasks20/
```

## V568 / V569 / V597 对比

| run | score behavior | status | mean wall | mean gap |
|---|---|---:|---:|---:|
| V568 | gate/cap 修复对照 | 3 external timeout + 1 time limit | 594.328s | 0.0488675 |
| V569 | V543 score, root gate 0.35 | 4 external timeout | 600.020s | 0.0485165 |
| V597 | V596 suppressed score, root gate 0.35 | 4 external timeout | 600.024s | 0.0483545 |

单实例：

| instance | V568 gap | V569 gap | V597 gap | V597 status |
|---|---:|---:|---:|---|
| seed61717 | 0.039594 | 0.037603 | 0.036955 | EXTERNAL_TIME_LIMIT |
| seed61103 | 0.026290 | 0.026290 | 0.026290 | EXTERNAL_TIME_LIMIT |
| seed61206 | 0.085809 | 0.086396 | 0.086396 | EXTERNAL_TIME_LIMIT |
| seed61718 | 0.043777 | 0.043777 | 0.043777 | EXTERNAL_TIME_LIMIT |

V597 的 root pair 确实变了：

| instance | V569 root pair | V597 root pair | V597 gate |
|---|---:|---:|---|
| seed61103 | `[18,20]` | `[12,15]` | ok |
| seed61206 | `[16,17]` | `[18,19]` | ok |
| seed61717 | `[14,18]` | `[4,9]` | score_below_min，回退 baseline |
| seed61718 | `[15,17]` | `[7,8]` | ok |

所以 V596 overlay 是有效改变了 root 决策的；问题是改变 root 决策仍不足以闭环。

## Proof-tail 结构

branch impact 对比：

| run | branch | right-censored | child CB retry | usable training rows | tail classes |
|---|---:|---:|---:|---:|---|
| V568 | 102 | 102 | 342 | 0 | completion_bound_tail 55, negative_chain 5, unprocessed 42 |
| V569 | 99 | 99 | 323 | 0 | completion_bound_tail 53, negative_chain 3, unprocessed 43 |
| V597 | 88 | 88 | 349 | 0 | completion_bound_tail 56, unprocessed 32 |

V597 completion-tail aggregate：

```text
completion_retry_total_profile_generation_time = 1006.103303
completion_retry_total_generated_sequences = 34042350
completion_retry_harvest_tail_class_counts = {
  expensive_no_harvest_candidate: 2,
  harvest_returned_new_task_set: 2
}
```

解释：

- root 选择变了，但深层大部分 branch 仍然 `missing_score_source`。
- V597 的 88 个 branch 全部 right-censored，没有一个可作为完整 branch-impact 正例。
- child completion-bound retry 没降，反而比 V569 更高。
- gap 轻微改善主要来自 seed61717，没有转化为 OPTIMAL 或明显 wall-time 改善。

## 当前判断

V596 overlay 的价值是防止后续低阈值实验重复选择已知坏 root pair；它不是主加速策略。

当前 20-scale proof-tail 的核心仍是：

1. root score 可以改变第一刀，但完整求解由深层 branch context 决定；
2. strict state-key 下深层 score coverage 严重不足；
3. 分支仍会产生大量 child completion-bound retry；
4. 这些 retry 多数是 exact-safe 证明链的一部分，不能用 retry-off 方式跳过；
5. 现有 right-censored rows 只能做 hard-negative / risk 诊断，不能当完整正例训练。

## 下一步

不继续降低 root score gate 阈值。

下一步应集中做两件事：

1. **补 deep branch context score coverage**
   - 使用 V568/V569/V597 的 `missing_score_source` 深层 rows；
   - 用 branch_state_key + branch constraints 重建 state-scoped score rows；
   - 优先覆盖 depth 1-4 中高频 proof-tail contexts。

2. **把 proof-tail risk 纳入训练/overlay**
   - 惩罚 `child_completion_bound_retries` 高的 pair；
   - 惩罚 `completion_bound_tail` / right-censored 子树；
   - 奖励能减少 child certificate pricing events、减少 proof CPU、快速 fathom child 的 pair；
   - right-censored 样本只作为风险负信号，不作为完整 wall-time 正例。

短期验收指标不应只看 root pair 是否 changed，而要看：

- `child_completion_bound_retries` 是否下降；
- `completion_retry_total_profile_generation_time` 是否下降；
- deep `missing_score_source` 是否下降；
- gap 是否明显改善；
- 最终是否增加 OPTIMAL 数。

