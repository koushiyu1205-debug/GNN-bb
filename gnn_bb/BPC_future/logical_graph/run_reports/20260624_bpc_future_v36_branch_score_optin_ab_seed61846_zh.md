# BPC_future V36 branch-score opt-in A/B

日期：2026-06-24

## 目的

验证 V35 生成的 `branch_score` score map 是否能在真实 solver run 中改变 Ryan-Foster branch pair，并观察它对 proof cost / wall-time 的实际影响。

这是 in-sample 受控探针：实例来自 V33/V35 的 counterfactual ranking 数据，因此不能作为泛化或 production-ready 证据；但它可以验证“V33 ranking rows -> V35 score map -> solver branch_score opt-in”这条链路是否打通。

## 实例

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
```

## 配置

baseline：

```text
time_limit = 220
journey_branch_candidate_log_top_n = 12
journey_branch_candidate_priority = fractionality
```

branch-score opt-in：

```text
time_limit = 220
journey_branch_candidate_log_top_n = 12
journey_branch_candidate_priority = branch_score
journey_branch_candidate_score_path = BPC_future/results/journey_branch_score_map_v35_v33_all12_20260624/journey_branch_score_rows.json
```

## 结果

| 指标 | baseline | branch_score | delta |
|---|---:|---:|---:|
| status | `OPTIMAL` | `OPTIMAL` | - |
| wall_time | `175.215707s` | `67.302853s` | `-107.912854s` |
| solving_time | `144.360625s` | `65.120653s` | `-79.239972s` |
| node_count | `7` | `3` | `-4` |
| branch_nodes | `3` | `1` | `-2` |
| rmp_solves | `35` | `24` | `-11` |
| pricing_calls | `72` | `43` | `-29` |
| exact_pricing_calls | `37` | `19` | `-18` |
| generated_sequences | `1772673` | `774336` | `-998337` |
| evaluated_timed_trips | `445257` | `239011` | `-206246` |
| primal_bound | `502.273983` | `502.273983` | `0` |
| dual_bound | `502.273983` | `502.273983` | `0` |

root branch 选择：

| run | priority_mode | selected pair | branch_score | branch_score_source |
|---|---|---:|---:|---|
| baseline | `fractionality` | `[2,5]` | null | null |
| branch_score | `branch_score` | `[3,18]` | `10.0` | `node:0:depth:0:3,18` |

## 结论

V36 证明了三件事：

- V35 score map 可以被 solver 读取；
- `branch_score` opt-in 在真实 run 中能把 root branch 从默认 `[2,5]` 改到 V33 强正例 `[3,18]`；
- 在该 in-sample 实例上，proof cost 明显下降：exact pricing calls 减少 18 次，node_count 减少 4，wall-time 减少约 108 秒。

边界同样明确：

- 这是单个 in-sample 实例，不是 random-TW 20 全量结论；
- `branch_score` 只改变 branch pair 调度，不改变 RMP、pricing、official bound、fathom 或 certificate；
- 该结果不能说明 20-scale 200s 目标已达成；
- 下一步需要跑更多 canonical random-TW 20 mixed context，并做 out-of-sample 或 leave-instance-out 的 score-map / GAT ranking A/B。

## 产物

```text
BPC_future/results/20260624_v36_branch_score_ab_baseline_220_seed61846.csv
BPC_future/results/logs_20260624_v36_branch_score_ab_baseline_220_seed61846/...
BPC_future/results/20260624_v36_branch_score_ab_optin_220_seed61846.csv
BPC_future/results/logs_20260624_v36_branch_score_ab_optin_220_seed61846/...
BPC_future/results/journey_branch_score_ab_audit_v37_v36_seed61846_20260624/summary.json
BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_ab_audit_v37_seed61846_zh.md
```
