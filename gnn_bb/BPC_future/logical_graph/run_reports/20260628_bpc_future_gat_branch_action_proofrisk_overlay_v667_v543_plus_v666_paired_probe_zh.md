# GAT Branch Action Proof-Risk Overlay

日期：2026-06-28

## 目的

把已完成 branch-score 实验中的整实例正负 evidence、timeout hard-negative evidence 和 paired child-probe hard-negative proxy 叠加到 score rows：严格收益分支 boost，changed 后仍非最优或已验证 timeout/paired-probe 高风险的分支 suppress。该脚本只读完成结果，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_branch_tree_policy_merged_overlay_v543_v467_plus_v540_20260627/journey_branch_score_rows.json
analysis_paths = []
timeout_evidence_paths = []
paired_probe_evidence_paths = ['BPC_future/results/journey_paired_probe_summary_v666_v664_external_score_child_probe_20260628/paired_probe_rows.jsonl']
output_dir = BPC_future/results/gat_branch_action_proofrisk_overlay_v667_v543_plus_v666_paired_probe_20260628
score_row_count = 20768
positive_overlay_keys = 0
negative_overlay_keys = 4
timeout_negative_overlay_keys = 0
paired_probe_positive_overlay_keys = 0
paired_probe_negative_overlay_keys = 4
overlay_counts = {'suppress_paired_probe_hard_negative': 2}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## Overlay Rows

- suppress_paired_probe_hard_negative: apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json node:0:depth:0:1,18 0.316227->0.050000, gain=19.262, BASELINE_CHILD_PROBE->TIME_LIMIT, evidence=paired_probe_hard_negative
- suppress_paired_probe_hard_negative: apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json node:0:depth:0:5,18 0.000019->0.000019, gain=-9.260, BASELINE_CHILD_PROBE->TIME_LIMIT, evidence=paired_probe_hard_negative

## 边界

输出只用于 opt-in branch ordering。它不能剪枝，不能替代 exact pricing closure，也不能作为 official lower bound。
