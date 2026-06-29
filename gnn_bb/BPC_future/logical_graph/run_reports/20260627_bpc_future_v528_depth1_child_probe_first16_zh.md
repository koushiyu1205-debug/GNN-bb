# V528 depth=1 child-probe 首批 16 条诊断

日期：2026-06-27

## 结论

这批 V528 probe 没有发现可转入 600s strict replay 的正向候选。

- 16 条短 probe 中，depth=1 forced pair 真正命中的有 12 条；另外 4 条在 root 阶段因 `max_cg_iterations` 停止，未到目标 depth=1 pair。
- 36 个 branch-impact row 全部 right-censored，`usable_branch_impact_training_count = 0`。
- `complete_label_branch_count = 0`，没有完整 child 证书标签。
- `max_child_corrected_bound_gain = 0.258784333`，几乎没有下界改善信号。
- proxy ranking 的 `promotion_ready_branch_count = 0`，所有候选都被 `proxy_score_below_promotion_threshold` 阻断。

## 机器字段

```text
probe_row_count = 16
probe_status_counts = {'EXTERNAL_TIME_LIMIT': 12, 'TIME_LIMIT': 4}
depth1_forced_pair_valid_count = 12
depth1_forced_pair_invalid_count = 4
impact_log_count = 16
branch_count = 36
forced_pair_branch_count = 24
forced_pair_matched_branch_count = 24
right_censored_branch_count = 36
complete_label_branch_count = 0
child_probe_row_count = 72
tail_class_counts = {'completion_bound_tail': 23, 'negative_chain_continues': 1, 'unprocessed_children': 12}
total_child_completion_bound_retries = 83
total_child_exact_pricing_events = 106
total_child_negative_pricing_events = 145
total_child_fathom_events = 0
proxy_branch_row_count = 8
proxy_ranking_pair_count = 11
right_censored_proxy_ranking_pair_count = 11
promotion_ready_branch_count = 0
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 有效 depth=1 forced pair 行为

| pair | tail_class | CB retry | exact pricing | negative pricing | processed child | unprocessed child |
|---|---:|---:|---:|---:|---:|---:|
| [2,10] | completion_bound_tail | 1 | 2 | 2 | 1 | 1 |
| [5,11] | negative_chain_continues | 0 | 1 | 1 | 1 | 1 |
| [5,10] | completion_bound_tail | 1 | 2 | 3 | 1 | 1 |
| [15,16] | completion_bound_tail | 1 | 2 | 4 | 1 | 1 |
| [5,20] | completion_bound_tail | 1 | 1 | 0 | 1 | 1 |
| [10,18] | completion_bound_tail | 1 | 2 | 3 | 1 | 1 |
| [4,13] | unprocessed_children | 0 | 0 | 0 | 0 | 2 |
| [4,15] | unprocessed_children | 0 | 0 | 0 | 0 | 2 |
| [12,13] | unprocessed_children | 0 | 0 | 0 | 0 | 2 |
| [15,16] | unprocessed_children | 0 | 0 | 0 | 0 | 2 |
| [12,15] | unprocessed_children | 0 | 0 | 0 | 0 | 2 |
| [4,16] | unprocessed_children | 0 | 0 | 0 | 0 | 2 |

## 解释

这批样本的问题不是 forced pair 没有命中。前 12 条确实在 depth=1 选到了指定 Ryan-Foster pair，但 child probe 只观察到右删失的尾部状态：completion-bound retry、exact pricing 和负列链仍在继续，没有 child fathom，也没有完整 label。

因此它们最多可以进入 hard-negative / 风险诊断池，不能作为 “这个分支能让完整求解更快闭环” 的正例。后 4 条连目标 depth=1 都没到，更不能用于 pair 质量判断。

这个结果说明，继续盲目扩 depth=1 candidate probe 的性价比很低。下一步应优先从已有 full60 的真实成功/失败路径里抽取 high-information contexts：例如 V468 中从 TIME_LIMIT 变 OPTIMAL 或明显缩短的路径、old success path prefix、以及临近闭环但失败的节点，而不是对所有 depth=1 候选做固定预算扫描。

## 产物

- Probe summary CSV: `BPC_future/results/journey_branch_candidate_replay_runbook_v528_v468_nonopt_depth1_child_probe_layered_20260627/v528_first16_probe_summary.csv`
- Branch impact audit: `BPC_future/results/journey_branch_impact_v528_depth1_first16_20260627/summary.json`
- Child-probe proxy ranking: `BPC_future/results/journey_branch_child_probe_proxy_ranking_v528_depth1_first16_20260627/summary.json`
