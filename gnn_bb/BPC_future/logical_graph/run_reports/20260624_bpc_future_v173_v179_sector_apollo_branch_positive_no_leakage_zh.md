# V173-V187: sector-wave/apollo15 seed61408 branch 正例闭环、反例与标签修正

日期：2026-06-24

## 背景

上一轮 V167/V171/V172 在 `sector-wave/tranquillitatis seed61718` 上得到的是 local-only hard negative：局部 proof-tail 成本下降，但整局仍 timeout，不能作为 `y_useful_tail_reduction` 正例。

本轮按 canonical random-TW 60-instance 口径，切换到完整实例路径：

```text
BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json
```

该实例在 full600 基线中为 `OPTIMAL`，wall `220.161s`，超过 20 规模 200 秒目标但不是纯 600 秒 timeout，适合寻找能把整局压进 200 秒内的 branch pair 正例。

## V173 top100 诊断

```text
csv = BPC_future/results/20260624_diag_top100_tail_action_sector_apollo_seed61408_260.csv
log = BPC_future/results/logs_20260624_diag_top100_tail_action_sector_apollo_seed61408_260
branch-impact = BPC_future/results/journey_branch_impact_audit_v173_sector_apollo_seed61408_diag260_20260624
tail-action = BPC_future/results/journey_tail_action_controller_audit_v173_sector_apollo_seed61408_diag260_20260624
```

结果：

```text
status = OPTIMAL
wall_time = 230.539874
solving_time = 216.861523
node_count = 7
pricing_calls = 75
exact_pricing_calls = 39
journey_branch_candidates = 3
journey_corrected_node_bound_audit = 32
completion_bound_retry = 7
```

自然分支事件完整可标注：

```text
branch_count = 3
candidate_log_branch_count = 3
complete_label_branch_count = 3
right_censored_branch_count = 0
usable_branch_impact_training_count = 3
自然 root selected pair = [1,6]
```

## V173-V176 root replay

root-only runbook：

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v173_sector_apollo_seed61408_root_only_20260624
entry_count = 6
time_limit = 230
```

6 条 forced root pair replay 结果：

```text
[6,16]   OPTIMAL  wall=184.847318  exact=35  pricing=67
[3,6]    OPTIMAL  wall=211.699278  exact=37  pricing=71
[3,14]   OPTIMAL  wall=213.392291  exact=40  pricing=76
[7,14]   OPTIMAL  wall=220.645029  exact=39  pricing=74
[14,19]  EXTERNAL_TIME_LIMIT  wall=230.018525
[14,16]  EXTERNAL_TIME_LIMIT  wall=230.017171
```

counterfactual delta：

```text
delta = BPC_future/results/journey_branch_counterfactual_delta_v175_v173_sector_apollo_seed61408_root_replay6_20260624
matched_counterfactual_count = 6
usable_counterfactual_training_count = 6
y_counterfactual_wall_improved = 4
y_counterfactual_proof_cost_improved = 2
y_counterfactual_timeout_regression = 2
```

ranking：

```text
ranking = BPC_future/results/journey_branch_counterfactual_ranking_v176_v175_sector_apollo_seed61408_root_replay6_20260624
context_count = 1
ranking_pair_count = 14
ranking_training_ready = true
context_type = mixed_positive_negative_context
```

解释：

`[6,16]` 是新的整局强正例：相对带日志诊断 baseline 减少约 `45.69s` wall，相对 full600 baseline `220.161s` 也进入 200 秒目标内。`[14,19]` / `[14,16]` 是明确回归，说明不能只看局部或 proxy 指标。

## V177-V178 score map opt-in

score map：

```text
score_map = BPC_future/results/journey_branch_score_map_v177_v176_sector_apollo_seed61408_root_replay6_20260624
entry_count = 6
best_pair = [6,16]
score([6,16]) = 1.825119013
score([14,19]) = -1.372875767
score([14,16]) = -1.3728532
```

opt-in：

```text
csv = BPC_future/results/20260624_v178_branch_score_horizon_v177_sector_apollo_seed61408_230.csv
log = BPC_future/results/logs_20260624_v178_branch_score_horizon_v177_sector_apollo_seed61408_230
priority = branch_score_horizon
context_require = tasks020_05_seed61408,sector-wave,apollo15_20km
```

结果：

```text
status = OPTIMAL
wall_time = 181.492537
solving_time = 179.444385
node_count = 7
pricing_calls = 67
exact_pricing_calls = 35
root selected pair = [6,16]
branch_score_source = node:0:depth:0:6,16
```

这完成了第二个 canonical 20-scale in-context 闭环：

```text
top candidate log -> root replay -> counterfactual ranking -> score map -> solver opt-in
```

仍不能解释为全量 20 规模达标；当前只覆盖一个新 context。

## V179 标签/特征修正

根据最新审阅意见，已修正离线训练行边界：

1. `features` / `decision_features` 只保留决策时可见字段；
2. child/subtree/delta/wall 等事后信息移入 `outcomes` / `outcome_labels`；
3. `tail_label_training_ready` 和 `contrastive_tail_training_ready` 改为严格门槛；
4. baseline result 同实例重复时 fail-closed；
5. tail-action row 匹配到多条同 key 时 fail-closed；
6. 统一训练行不再静默去重，改为记录 `duplicate_context_action_count`。
7. 新增 `y_budget_dominant_improvement`，用于标记同预算删失但全 run proof-work/gap 明显改善的中间样本；它不改变 `y_whole_run_improved` 或 `y_useful_tail_reduction`。

V179 重建 V171/V172：

```text
output = BPC_future/results/journey_tail_impact_training_rows_v179_v171_full_replay11_counterfactual_no_leakage_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_impact_training_rows_v179_v171_counterfactual_no_leakage_zh.md
training_row_count = 33
local_tail_improved = 5
whole_run_improved = 0
local_only_hard_negative = 5
minimal_tail_signal_ready = false
tail_label_training_ready = false
```

测试：

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest \
  BPC_future.tests.test_journey_branch_counterfactual_delta_audit \
  BPC_future.tests.test_journey_tail_impact_training_rows \
  BPC_future.tests.test_journey_tail_action_counterfactual_delta \
  BPC_future.tests.test_journey_branch_candidate_replay_runbook \
  BPC_future.tests.test_journey_branch_tail_positive_runbook

Ran 28 tests in 0.097s
OK
```

## V180-V187 layered/proxy 反例

V180 从同一个 seed61408 root top100 candidate log 生成 layered 候选：

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v180_sector_apollo_seed61408_root_layered_top100_20260624
[1,11]  highest_fractionality
[1,14]  near_tie
[7,14]  min_max_child_width
[2,4]   balanced_child_width
[4,14]  rank_diversity
[6,16]  legacy_fill
```

关键点：已知强正例 `[6,16]` 只通过 `legacy_fill` 被保留下来，单靠 fractionality / near-tie / width/balance 会漏掉它。

V181-V183 对排除 V173 已跑 pair 后的 6 个新候选做 90s child probe，proxy ranking 把 `[9,11]`、`[1,14]` 排在前两名。但这些都是 right-censored proxy，不是可上线 score。

V184 230s full replay 验证 top-proxy 两条：

```text
[1,14] -> EXTERNAL_TIME_LIMIT, wall=230.015815
[9,11] -> TIME_LIMIT,          wall=212.377389, gap=0.002933, pricing=74, exact=38
```

V185 branch-impact：

```text
branch_count = 8
forced_pair_branch_count = 2
forced_pair_matched_branch_count = 2
right_censored_branch_count = 8
usable_branch_impact_training_count = 0
tail_class_counts = {'completion_bound_tail': 6, 'negative_chain_continues': 2}
total_child_completion_bound_retries = 35
total_child_negative_pricing_events = 32
```

V186 counterfactual delta 初版：

```text
matched_counterfactual_count = 2
status_pair_counts = {'OPTIMAL->EXTERNAL_TIME_LIMIT': 1, 'OPTIMAL->TIME_LIMIT': 1}
timeout_regression_count = 2
timeout_resolved_count = 0
counterfactual_training_ready = false
```

V187 fail-closed 重跑：

```text
output = BPC_future/results/journey_branch_counterfactual_delta_v187_v184_sector_apollo_seed61408_top_proxy_full_replay2_failclosed_20260624
schema_version = journey_branch_counterfactual_delta_audit_v3
matched_counterfactual_count = 2
label_positive_counts = {'y_counterfactual_regression': 2, 'y_counterfactual_timeout_regression': 2}
timeout_regression_count = 2
timeout_resolved_count = 0
counterfactual_training_ready = false
```

V187 同时修正 branch delta 对齐边界：

```text
baseline / alternative result 同实例重复时 fail-closed
baseline / alternative branch row 同 key 多重匹配时 fail-closed
缺失 solver 全局指标不按 0 参与 delta
timeout regression 不再打正向 proof-cost proxy label
```

结论：child-probe proxy 可用于采样导航，但不能直接转成 solver opt-in score。`[1,14]` 和 `[9,11]` 是新的反例：proxy 看起来较好，full replay 却相对 V173 baseline 回归。V187 修正后，这两条只保留 regression 标签，不再冒出正向 proxy 标签。当前可用强正例仍是 `[6,16]`，proxy 候选必须经过 full replay / timeout-resolved / both-optimal wall 改善验证后才能进 score map。

## 当前判断

现在不是“正例完全找不到”，而是必须主动选择可闭环 context。`sector-wave/apollo15 seed61408` 证明了除 seed61001 外，canonical 20-scale 中还存在能把实例压进 200 秒内的 branch 正例。

下一步不应直接训练 production GAT，而应：

1. 对 seed61408 补 top200 诊断或 early depth-1 分层采样，避免漏掉 101-190 名候选；
2. 在更多完整实例路径上重复同样闭环，目标至少达到 5 个 whole-run positives、3 个 parent contexts、3 个 instances、2 个时间窗族；
3. 继续使用 `y_budget_dominant_improvement` 作为删失排序样本，而不是强正例；
4. 保留 local-only hard negative 训练 payback-risk head；
5. 继续用 context gate 限制 score map，不做全局启用。
