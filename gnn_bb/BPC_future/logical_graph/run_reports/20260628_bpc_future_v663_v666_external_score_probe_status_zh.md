# V663-V666 External Branch Score Child-Probe Status

## 背景

本轮在 V660 checkpoint ranking 和 V661 walltime score map 之后，补了一条更直接的采样线：

- `routeopt_bkf`：混合 GAT 分数、fractionality、child width、balance gap、rank 等风险字段。
- `external_branch_score`：只按外部 score rows 的分数选 alternative pair，缺分候选排后。

目的不是上线新 score map，而是验证：V661 的 `predicted_walltime_gain` 高分 pair 本身是否足以成为下一批 full replay / training positive 的来源。

## 代码变更

修改：

- `BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py`
- `BPC_future/tests/test_journey_branch_candidate_replay_runbook.py`

新增 `candidate_selection=external_branch_score`：

- 先选有 `source_alt_branch_score` 的候选；
- 按 score 降序排序；
- 不用 child width / balance gap 重排；
- 记录 `source_alt_selection_reason=external_branch_score_priority`；
- 记录 `source_alt_external_branch_score_rank`。

这个模式只影响 runbook 采样顺序，不运行 BPC/pricing，不产生 official bound 或 certificate。

## V663 / V664 Runbook

V663：

- output: `BPC_future/results/journey_branch_candidate_replay_runbook_v663_v661_walltime_external_score_child_probe_20260628/`
- exclude: V644, V654, V662
- entries: `24`
- paired groups: `5`
- baseline entries: `5`
- alternative entries: `19`

V663 适合扩展新 pair 覆盖，但不适合作严格 paired 对比，因为 baseline 缺失较多。

V664：

- output: `BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/`
- exclude: V644, V654
- entries: `24`
- paired groups: `10`
- baseline entries: `10`
- alternative entries: `14`

V664 是本轮主 paired child-probe。

## V664 执行

24 条 child-probe 命令已完成：

- max workers: `4`
- failures: `0`
- status log: `BPC_future/results/journey_branch_candidate_replay_runbook_v664_v661_walltime_external_score_paired_child_probe_20260628/parallel_status.jsonl`

所有命令正常返回，未发生运行失败。

## V665 Branch Impact Audit

输出：

- `BPC_future/results/journey_branch_impact_v665_v664_external_score_child_probe_20260628/`
- report: `BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_branch_impact_v665_v664_external_score_child_probe_zh.md`

关键字段：

```text
branch_count = 62
forced_pair_branch_count = 24
forced_pair_matched_branch_count = 24
tail_class_counts = {'completion_bound_tail': 24, 'unprocessed_children': 38}
total_child_completion_bound_retries = 176
total_child_fathom_events = 8
total_child_negative_pricing_events = 153
total_child_exact_pricing_events = 217
run_status_counts = {'TIME_LIMIT': 62}
usable_branch_impact_training_count = 0
```

解释：forced pair 都成功绑定，但 child-probe 仍是右删失诊断，不能当 complete branch-impact label。

## V666 Paired Summary

输出：

- `BPC_future/results/journey_paired_probe_summary_v666_v664_external_score_child_probe_20260628/`
- report: `BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_paired_probe_summary_v666_v664_external_score_child_probe_zh.md`

关键字段：

```text
entry_count = 24
baseline_entry_count = 10
alternative_entry_count = 14
paired_group_count = 15
label_counts = {'hard_negative_proxy': 2, 'missing_baseline': 5, 'neutral_proxy': 7}
```

paired child-probe 中没有 positive_proxy。

较好的 wall gain 也都没有达到正例标准：

| instance | alt pair | wall gain | label |
|---|---:|---:|---|
| apollo sector seed61510 | `[1,18]` | `19.261906` | hard_negative_proxy |
| apollo random seed61919 | `[2,18]` | `14.421054` | neutral_proxy |
| tranq sector seed61410 | `[3,10]` | `7.651044` | neutral_proxy |
| apollo random seed61204 | `[1,18]` | `7.280904` | neutral_proxy |
| tranq random seed61103 | `[5,20]` | `3.100485` | neutral_proxy |

## 与 V648 RouteOpt-BKF 的对比

V648 routeopt_bkf child-probe：

```text
entry_count = 72
paired_group_count = 24
label_counts = {'hard_negative_proxy': 13, 'neutral_proxy': 33, 'positive_proxy': 2}
best wall gains = 102.684275, 33.891568, 29.792059, ...
```

本轮 V666 external_score：

```text
entry_count = 24
paired_group_count = 15
label_counts = {'hard_negative_proxy': 2, 'missing_baseline': 5, 'neutral_proxy': 7}
best wall gains = 19.261906, 14.421054, 7.651044, ...
```

结论：纯 V661 walltime 分数不如 `routeopt_bkf` 稳。直接按模型高分选 pair 会命中一些昂贵 proof-tail pair，当前不能作为 production score map 或 full replay 主采样策略。

## 判断

1. `predicted_walltime_gain` 作为离线排序有信号，但裸用不够。
2. RouteOpt-style BKF 混合 child width / balance / fractionality 风险是必要的。
3. 下一步 branch score 训练不能只学 wall gain，还要显式学：
   - child proof CPU；
   - completion-bound retry；
   - fathom gain；
   - gap improvement；
   - child width / balance 风险。
4. V661/V666 产生的 hard negative / neutral rows 应进入后续训练，作为“高分但不应裸选”的校准样本。

## Exact-Safe 边界

本轮新增代码和实验均为 diagnostic/sample-generation：

- 不改变默认 solver 行为；
- 不提供 official bound；
- 不提供 certificate；
- 不改变 fathom/prune 依据；
- forced pair 只用于 replay/probe，最终精确性仍由 exact pricing / BPC 逻辑保证。

## 测试

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_journey_branch_candidate_replay_runbook \
  BPC_future.tests.test_gat_branch_action_checkpoint_ranking

Ran 21 tests in 0.034s
OK
```

## 下一步

1. 不把 V661 walltime score map 直接上线。
2. 把 V666 的 neutral / hard-negative proxy 合并进 branch-action 数据集。
3. 继续以 RouteOpt-BKF 为主采样策略，但把 score 函数改成多目标：
   `wall gain + gap/fathom gain - proof CPU/retry/width risk`。
4. 对 V648 中两个 positive_proxy 做 full replay 或更深 child-probe，验证是否能转成 strict/weak positive。
