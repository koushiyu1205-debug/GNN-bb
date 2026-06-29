# Journey Branch Score Structural Proof-Tail Overlay

日期：2026-06-28

## 目的

把 full-run timeout hard-negative 从精确 key 扩展到结构性 proof-tail 风险：深层重复失败 pair、同 random-TW family 的深层高分路径会被降分。该脚本只改 opt-in score map，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_branch_action_v612_v607_plus_v610_failure_hardneg_20260628/score_map_v613_v610_failure_overlay_on_v612_hybrid/journey_branch_score_rows.json
evidence_paths = ['BPC_future/results/journey_branch_score_failure_evidence_v610_v609_v608_highscore_external_20260628/score_timeout_hard_negative_rows.jsonl', 'BPC_future/results/journey_branch_score_failure_evidence_v615_v614_v613_smoke4_20260628/score_timeout_hard_negative_rows.jsonl']
output_dir = BPC_future/results/gat_branch_action_v612_v607_plus_v610_failure_hardneg_20260628/score_map_v616_structural_prooftail_overlay_on_v613
score_row_count = 18823
evidence_row_count = 224
exact_evidence_scope_count = 448
overlay_counts = {'exact_timeout_hard_negative': 224, 'family_deep_high_score': 6517, 'repeated_failed_pair': 4599}
touched_row_count = 9508
depth_p50 = 4.000
depth_p75 = 6.000
score_p50 = 0.878990
score_p75 = 0.900729
completion_retry_p50 = 43.000
completion_retry_p75 = 65.000
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## Top Failed Pairs

- [1, 10]: 15
- [4, 7]: 13
- [4, 11]: 11
- [1, 9]: 10
- [15, 17]: 8
- [3, 5]: 7
- [3, 9]: 6
- [7, 15]: 6
- [13, 20]: 6
- [2, 6]: 5

## Touched Rows Sample

- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:17,20 depth=1 0.895221->0.350000 reason=repeated_failed_pair:17,20
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:14,16 depth=1 0.894442->0.350000 reason=repeated_failed_pair:14,16
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:11,20 depth=1 0.894312->0.350000 reason=repeated_failed_pair:11,20
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:13,20 depth=1 0.894217->0.350000 reason=repeated_failed_pair:13,20
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:10,19 depth=1 0.893785->0.350000 reason=repeated_failed_pair:10,19
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:4,12 depth=1 0.893247->0.350000 reason=repeated_failed_pair:4,12
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:5,14 depth=1 0.893214->0.350000 reason=repeated_failed_pair:5,14
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:4,11 depth=1 0.893039->0.350000 reason=repeated_failed_pair:4,11
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:16,17 depth=1 0.892983->0.350000 reason=repeated_failed_pair:16,17
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:3,7 depth=1 0.892914->0.350000 reason=repeated_failed_pair:3,7
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:4,8 depth=1 0.892583->0.350000 reason=repeated_failed_pair:4,8
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:3,17 depth=1 0.892550->0.350000 reason=repeated_failed_pair:3,17
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:5,8 depth=1 0.892518->0.350000 reason=repeated_failed_pair:5,8
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:2,9 depth=1 0.892344->0.350000 reason=repeated_failed_pair:2,9
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:2,10 depth=1 0.892104->0.350000 reason=repeated_failed_pair:2,10
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:3,9 depth=1 0.892041->0.350000 reason=repeated_failed_pair:3,9
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:2,3 depth=1 0.891866->0.350000 reason=repeated_failed_pair:2,3
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:4,5 depth=1 0.891631->0.350000 reason=repeated_failed_pair:4,5
- apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:2:depth:1:3,13 depth=1 0.891355->0.350000 reason=repeated_failed_pair:3,13
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:1:depth:1:18,20 depth=1 0.881671->0.350000 reason=repeated_failed_pair:18,20
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:1:depth:1:4,12 depth=1 0.879804->0.350000 reason=repeated_failed_pair:4,12
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:1:depth:1:10,14 depth=1 0.879408->0.350000 reason=repeated_failed_pair:10,14
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:1:depth:1:5,14 depth=1 0.878903->0.350000 reason=repeated_failed_pair:5,14
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:1:depth:1:2,10 depth=1 0.878886->0.350000 reason=repeated_failed_pair:2,10
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:1:depth:1:1,10 depth=1 0.878831->0.350000 reason=repeated_failed_pair:1,10
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:1:depth:1:2,5 depth=1 0.878322->0.350000 reason=repeated_failed_pair:2,5
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:2:depth:1:4,12 depth=1 0.888375->0.350000 reason=repeated_failed_pair:4,12
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:3:depth:2:18,20 depth=2 0.879176->0.350000 reason=repeated_failed_pair:18,20
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:3:depth:2:10,14 depth=2 0.878021->0.350000 reason=repeated_failed_pair:10,14
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:3:depth:2:4,12 depth=2 0.877219->0.350000 reason=repeated_failed_pair:4,12

## 边界

输出只能用于 branch ordering。它不能剪枝，不能替代 exact pricing closure，也不能作为 official lower bound。root 只做精确失败 row suppress，不做结构性泛化 suppress。
