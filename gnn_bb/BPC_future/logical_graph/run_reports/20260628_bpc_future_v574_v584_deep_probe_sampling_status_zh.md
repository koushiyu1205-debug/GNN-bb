# 20260628：V574-V584 深层 Branch Probe 采样状态

## 结论

本轮没有改变 solver 的 bound、certificate 或剪枝逻辑，主要推进的是 Branch Score 主线所需的深层 proof-tail 标签采样。

核心结论：

- V574 的高 retry child-probe 能产生深层 child 标签，但单条成本太高，前两条分别约 `516s` 和 `553s`。
- V577 / V580 的轻量档位太轻，`max_cg_iterations=12` 在 root 阶段就截断，无法到达 source branch，因此无训练价值。
- V582 的中等档位较合适：`source_event_time<=120s`、`max_cg_iterations=36`、`extra_nodes_after_branch=2`、`time_limit=240s`。前两条约 `103s`，能产生 branch / child / completion-bound retry 标签。
- 目前新增数据仍是 right-censored risk / hard-negative 风险信号，不是 strict positive，也不是 production-ready score map。

## 运行与产物

### V574：高 retry child-probe runbook

Runbook：

`BPC_future/results/journey_branch_candidate_replay_runbook_v574_v573_v545_high_retry_child_probe_20260628/`

配置特征：

- `probe_extra_nodes_after_branch=4`
- `probe_max_cg_iterations=36`
- `time_limit=600`
- `min_source_depth=1`
- `max_source_depth=4`
- `limit=24`

本轮实际只跑前两条：

| entry | forced pair | status | wall | gap | dual | primal |
|---:|---|---:|---:|---:|---:|---:|
| 001 | `[1,8]` | `TIME_LIMIT` | `516.05s` | `0.081871` | `514.020685` | `559.856463` |
| 002 | `[1,10]` | `TIME_LIMIT` | `552.68s` | `0.066927` | `514.020685` | `550.889866` |

V575 branch-impact 审计：

`BPC_future/results/journey_branch_impact_v575_v574_first2_child_probe_20260628/`

关键字段：

```text
branch_count = 11
right_censored_branch_count = 11
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
forced_pair_branch_count = 4
forced_pair_matched_branch_count = 4
tail_class_counts = {'completion_bound_tail': 6, 'unprocessed_children': 5}
total_child_completion_bound_retries = 40
total_child_exact_pricing_events = 49
total_child_negative_pricing_events = 65
total_child_certificate_pricing_events = 9
total_child_fathom_events = 0
```

forced pair 对比：

| forced pair | tail | child CB retry | child exact events | child negative events | fathom | max corrected gain |
|---|---|---:|---:|---:|---:|---:|
| `[1,8]` | completion-bound tail | `6` | `9` | `22` | `0` | `22.782057727` |
| `[1,10]` | completion-bound tail | `16` | `14` | `22` | `0` | `34.365177` |

解释：

- `[1,10]` 的最终 gap 更小，但 proof-tail 更重，尤其 separate child 有 `13` 次 completion-bound retry。
- 两者都没有 fathom，不能作为正例。
- 这些行适合做 right-censored risk / hard-negative，不适合做 strict branch wall-time positive。

V576 child score map：

- complete-only：
  - `raw_child_probe_row_count=22`
  - `child_score_row_count=0`
  - `production_ready=False`
- right-censored risk：
  - `child_score_row_count=10`
  - `child_score_map_entry_count=7`
  - `production_ready=False`

## V577 / V580：过轻 probe 的失败

V577：

`BPC_future/results/journey_branch_candidate_replay_runbook_v577_v573_v545_high_retry_light_child_probe_20260628/`

配置：

- `time_limit=240`
- `probe_extra_nodes_after_branch=2`
- `probe_max_cg_iterations=12`
- 排除 V574 runbook entry

前两条结果：

```text
status = TIME_LIMIT
wall ~= 11.5s
branch_count = 0
gap_available = false
gap_unavailable_reason = no_exact_dual_bound
```

V580：

`BPC_future/results/journey_branch_candidate_replay_runbook_v580_v573_v545_early_high_retry_light_child_probe_20260628/`

配置相同，但增加：

- `max_source_event_time=120`

前两条结果：

```text
status = TIME_LIMIT
wall ~= 8s
node_count = 1
branch_count = 0
gap_available = false
gap_unavailable_reason = no_exact_dual_bound
```

判断：

`max_cg_iterations=12` 太低，会在 root CG 阶段截断，根本到不了 source branch。这类数据不能用作 branch score 标签。

## V582：当前更合理的中等 probe 档位

Runbook：

`BPC_future/results/journey_branch_candidate_replay_runbook_v582_v573_v545_early_high_retry_mid_child_probe_20260628/`

配置：

- `time_limit=240`
- `max_source_event_time=120`
- `probe_extra_nodes_after_branch=2`
- `probe_max_cg_iterations=36`
- `max_events_per_instance=1`

前两条运行结果：

```text
entry 001 wall ~= 103.21s, status = TIME_LIMIT
entry 002 wall ~= 103.76s, status = TIME_LIMIT
```

两条都产生了 `journey_branch`、`journey_child_queued`、`exact_completion_bound_retry` 和 child label。

V583 branch-impact 审计：

`BPC_future/results/journey_branch_impact_v583_v582_first2_mid_child_probe_20260628/`

关键字段：

```text
branch_count = 8
right_censored_branch_count = 8
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
forced_pair_branch_count = 4
forced_pair_matched_branch_count = 4
tail_class_counts = {'completion_bound_tail': 4, 'unprocessed_children': 4}
total_child_completion_bound_retries = 18
total_child_exact_pricing_events = 26
total_child_negative_pricing_events = 34
total_child_certificate_pricing_events = 6
total_child_fathom_events = 0
```

V584 child score map：

- complete-only：
  - `raw_child_probe_row_count=16`
  - `child_score_row_count=0`
  - `production_ready=False`
- right-censored risk：
  - `child_score_row_count=6`
  - `child_score_map_entry_count=3`
  - `production_ready=False`

Right-censored risk top rows：

| pair | child kind | score | CB retry | negative events | proof CPU | max corrected gain |
|---|---|---:|---:|---:|---:|---:|
| `[4,11]` | same | `-2.7869` | `3` | `4` | `23.08s` | `9.527032` |
| `[2,3]` | separate | `-4.7657` | `3` | `5` | `19.83s` | `0.747548667` |
| `[2,3]` | same | `-5.6615` | `3` | `8` | `28.11s` | `0.363567` |

解释：

- V582 档位能在约 100 秒内采到 proof-tail 风险标签。
- 它仍不是 strict positive，因为全局 run 是 `TIME_LIMIT`，branch rows 右删失。
- 但它比 V574 更适合批量扩展 hard-negative / proof-tail risk 标签。

## 对 Branch Score 主线的影响

目前新增证据支持以下判断：

1. 继续盲跑完整 600 秒 child-probe 不划算。
   - V574 前两条消耗约 `1069s`，仍没有 strict label。

2. 过低 CG cap 没有价值。
   - V577/V580 很快结束，但没有 branch event、没有 dual bound、没有 child label。

3. 当前可用的采样档位是 V582。
   - 需要足够 CG 到达 source branch；
   - branch 后限制额外节点；
   - source event time 要受控；
   - 输出只能作为 risk / hard-negative，不能 production-ready。

4. 当前模型最缺的仍是正向闭环标签。
   - V575/V583 都没有 `fathom`；
   - `usable_branch_impact_training_count=0`；
   - right-censored risk 可以教模型避开 bad branch / bad child order；
   - 但还不能教模型“哪个 pair 会让完整求解更快最优”。

## 下一步

建议按以下顺序推进：

1. 用 V582 档位扩到 12 条 smoke。
   - 每次 `max-workers=2`；
   - 只读结果后再决定是否扩到 24；
   - 不再运行 V574 的剩余重 probe。

2. 把 V582/V583/V584 的 risk rows 接入 tree-policy / branch-score 训练为 hard negative。
   - 右删失行不能作为正例；
   - 重点惩罚 high completion-bound retry、high proof CPU、no fathom 的 branch/child。

3. 另建 positive-mining runbook。
   - 只选历史 full60 中 `OPTIMAL` 且 proof-tail 较短的深层 context；
   - 对同 context 做小规模 alternative replay；
   - 目标是找到 `fathom` 或 `time_to_certificate` 明显降低的 pair。

4. 后续 full60 前必须先满足：
   - 深层 score coverage 提升；
   - smoke 中 `missing_score_source` 明显减少；
   - risk gate 不再只会 fail-closed；
   - 不能把 right-censored TIME_LIMIT 当成优化正例。

## Exact-Safe 边界

本轮所有新增产物都是 diagnostic-only：

- 不提供 official lower bound；
- 不提供 certificate；
- 不改变 pruning；
- 不把 RMP objective 当 exact node bound；
- right-censored score map 只能用于 shadow / opt-in / risk 诊断，不能作为 production-ready 策略。
