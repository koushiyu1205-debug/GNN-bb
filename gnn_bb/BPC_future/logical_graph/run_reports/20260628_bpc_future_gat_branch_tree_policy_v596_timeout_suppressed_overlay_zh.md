# GAT Branch Action Proof-Risk Overlay

日期：2026-06-28

## 目的

把已完成 branch-score 实验中的整实例正负 evidence 和 timeout hard-negative evidence 叠加到 score rows：严格收益分支 boost，changed 后仍非最优或已验证 timeout 的分支 suppress。该脚本只读完成结果，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_branch_tree_policy_merged_overlay_v543_v467_plus_v540_20260627/journey_branch_score_rows.json
analysis_paths = []
timeout_evidence_paths = ['BPC_future/results/20260628_v569_branch_timeout_evidence/root_timeout_hard_negative_rows.jsonl']
output_dir = BPC_future/results/gat_branch_tree_policy_v596_timeout_suppressed_overlay_v543_20260628
score_row_count = 20768
positive_overlay_keys = 0
negative_overlay_keys = 8
timeout_negative_overlay_keys = 8
overlay_counts = {'suppress_timeout_hard_negative': 4}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## Overlay Rows

- suppress_timeout_hard_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:18,20 0.382223->0.050000, gain=-0.001, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT, evidence=timeout_hard_negative
- suppress_timeout_hard_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:16,17 0.394574->0.050000, gain=0.001, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT, evidence=timeout_hard_negative
- suppress_timeout_hard_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json node:0:depth:0:14,18 0.370151->0.050000, gain=-22.769, TIME_LIMIT->EXTERNAL_TIME_LIMIT, evidence=timeout_hard_negative
- suppress_timeout_hard_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node:0:depth:0:15,17 0.456029->0.050000, gain=-0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT, evidence=timeout_hard_negative

## 边界

输出只用于 opt-in branch ordering。它不能剪枝，不能替代 exact pricing closure，也不能作为 official lower bound。
