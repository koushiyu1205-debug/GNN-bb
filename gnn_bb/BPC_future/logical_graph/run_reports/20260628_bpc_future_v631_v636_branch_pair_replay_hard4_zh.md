# V631-V636 Branch Pair Replay Hard4 Summary

## 背景

本轮回到 branch-pair selection 主线，不再把 child-order 当主加速策略。

输入 hard cases 来自：

- `BPC_future/results/20260628_v622_retry_on_off_gate_smoke4_tasks20/retry_on/logs`

这些都是 random-TW 20 规模 hard case，V622 中 4/4 都在 600s 外部时限下未闭环。

## V630 Branch-Impact Audit

输出：

- `BPC_future/results/journey_branch_impact_v630_v622_retry_on_hard4_20260628/`

关键机器字段：

- branch_count: `162`
- tail_class_counts: `completion_bound_tail=83`, `negative_chain_continues=7`, `unprocessed_children=72`
- total_child_completion_bound_retries: `523`
- total_child_fathom_events: `8`
- right_censored_branch_count: `162`

解释：这些日志不是完整训练标签，但能定位 proof-tail 压力节点。所有 branch 都右删失，不能直接当 stable branch-impact positive。

## V631 Paired Branch-Pair Probe

输出：

- runbook: `BPC_future/results/journey_branch_candidate_replay_runbook_v631_v622_hard4_depth0_2_pairprobe_20260628/`
- branch impact: `BPC_future/results/journey_branch_impact_v632_v631_hard4_pairprobe_20260628/`
- paired summary: `BPC_future/results/journey_paired_probe_summary_v634_v631_hard4_pairprobe_20260628/`

设置：

- 4 个 hard instances
- 每个实例最多 2 个 source branch event
- depth: `0..2`
- 每组：selected baseline + 2 alternatives
- total: `8` paired groups, `24` replay commands
- probe mode: `child_probe`
- time_limit: `260`
- probe_max_cg_iterations: `36`
- probe_extra_nodes_after_branch: `5`

V634 关键结果：

- paired_group_count: `8`
- alternative_entry_count: `16`
- label_counts: `hard_negative_proxy=2`, `neutral_proxy=14`

虽然旧 summary 阈值没有给出 positive_proxy，但原始 group 里有一个值得 full replay 的候选：

- instance: `tasks020_04_seed61311`
- source: root pair selected `[17,20]`
- alternative: root pair `[16,20]`
- child-probe wall gain: `23.837619s`
- child CB retry gain: `5`
- gap improvement: `0.00593`

另一个 root candidate `[16,17]` 的 child-probe wall gain 小，但 gap 更好，因此也进入 full replay。

## V635/V636 Full Replay

实例：

- `BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json`

对比：

| root pair | status | wall | gap | best primal | best dual | branch | CB retry | fathom | columns | best incumbent |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `[17,20]` selected | EXTERNAL_TIME_LIMIT | 600.016897 | 0.045761 | 573.426825 | 547.186422 | 35 | 38 | 0 | 48 | 573.426825 |
| `[16,20]` alt | EXTERNAL_TIME_LIMIT | 600.016970 | 0.044568 | 572.711053 | 547.186422 | 36 | 38 | 0 | 48 | 572.711053 |
| `[16,17]` alt | EXTERNAL_TIME_LIMIT | 600.015880 | 0.041522 | 570.891015 | 547.186422 | 28 | 39 | 9 | 46 | 570.891015 |

结论：

- `[16,20]` 没有闭环，但比 selected `[17,20]` 略好：incumbent 和 gap 都改善。
- `[16,17]` 明显更好：gap 从 `0.045761` 降到 `0.041522`，fathom 从 `0` 增到 `9`，branch 数从 `35` 降到 `28`。
- 但 `[16,17]` 仍然 600s timeout，所以它不是 strict full-solve positive，只能作为 `gap/fathom/proof-tail weak positive`。

## 解释

这次结果说明 branch pair 的确能改变 proof-tail 结构，比 child-order 更接近主因。

但单次 root pair 替代还不够把 hard instance 推到 OPTIMAL：

1. root corrected lower bound 没变，best dual 仍是 `547.186422`。
2. 改善主要来自更好的 incumbent、较少 branch、更多 fathom，而不是直接提高 root proof bound。
3. completion-bound/final-judge retry 仍然高：`38-39` 次。
4. 说明仅靠 root pair 选择不够，还需要后续 depth 1/2 的 branch pair 继续配合，或者需要更强 incumbent/cuts/formulation。

## 对训练的影响

可加入 branch score 训练的标签类型：

- `[16,17]` over `[17,20]`：weak positive / gap-fathom positive
- `[16,20]` over `[17,20]`：weak positive / incumbent-gap positive
- V631 中明显更差的 alternatives：hard negative proxy

不能做的事情：

- 不能把 `[16,17]` 当作 strong full-solve positive，因为没有 `OPTIMAL`。
- 不能把 root RMP / corrected bound 当 exact prune 依据。
- 不能因为 child-probe 短预算改善就直接上线 score overlay；必须用 full replay 或至少 gap/fathom replay 验证。

## 下一步

1. 对 seed61311 继续做 depth-1/depth-2 paired full replay，沿 `[16,17]` root 后的实际 hard path 选择后续 pair。
2. 把 V635/V636 产物转成 branch-counterfactual weak rows，字段包含：
   - `wall_time_gain`
   - `gap_improvement`
   - `fathom_gain`
   - `branch_count_delta`
   - `completion_bound_retry_delta`
   - `label_type=weak_gap_fathom_positive`
3. score map 不能只追求 wall gain；应引入 gap/fathom/proof-tail 多目标 ranking。
4. 对 20-scale full60 的 timeout case，优先找能同时改善 incumbent、gap 和 fathom 的 root/depth1 pair，而不是只看 child-probe wall。
