# Journey Branch Score Structural Proof-Tail Overlay

日期：2026-06-28

## 目的

把 full-run timeout hard-negative 从精确 key 扩展到结构性 proof-tail 风险：深层重复失败 pair、同 random-TW family 的深层高分路径会被降分。该脚本只改 opt-in score map，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_branch_action_v612_v607_plus_v610_failure_hardneg_20260628/score_map_v613_v610_failure_overlay_on_v612_hybrid/journey_branch_score_rows.json
evidence_paths = ['BPC_future/results/journey_branch_score_failure_evidence_v610_v609_v608_highscore_external_20260628/score_timeout_hard_negative_rows.jsonl', 'BPC_future/results/journey_branch_score_failure_evidence_v615_v614_v613_smoke4_20260628/score_timeout_hard_negative_rows.jsonl']
output_dir = BPC_future/results/gat_branch_action_v612_v607_plus_v610_failure_hardneg_20260628/score_map_v617_conservative_structural_prooftail_overlay_on_v613
score_row_count = 18823
evidence_row_count = 224
exact_evidence_scope_count = 448
overlay_counts = {'exact_timeout_hard_negative': 224, 'family_deep_high_score': 492, 'family_retry_tail_risk': 607, 'repeated_failed_pair': 3135}
touched_row_count = 4329
depth_p50 = 4.000
depth_p75 = 6.000
score_p50 = 0.878990
score_p75 = 0.900729
completion_retry_p50 = 43.000
completion_retry_p75 = 65.000
high_depth_threshold = 6
high_score_threshold = 0.900729
repeated_pair_min_depth = 3
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

- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:7:depth:3:4,12 depth=3 0.875978->0.350000 reason=repeated_failed_pair:4,12
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:8:depth:3:4,12 depth=3 0.882798->0.350000 reason=repeated_failed_pair:4,12
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:10:depth:3:13,19 depth=3 0.900925->0.350000 reason=repeated_failed_pair:13,19
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:10:depth:3:3,17 depth=3 0.899912->0.350000 reason=repeated_failed_pair:3,17
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:10:depth:3:3,9 depth=3 0.898849->0.350000 reason=repeated_failed_pair:3,9
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:10:depth:3:3,7 depth=3 0.898359->0.350000 reason=repeated_failed_pair:3,7
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:10:depth:3:2,5 depth=3 0.897881->0.350000 reason=repeated_failed_pair:2,5
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:10:depth:3:5,14 depth=3 0.897043->0.350000 reason=repeated_failed_pair:5,14
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:13,19 depth=3 0.911188->0.350000 reason=repeated_failed_pair:13,19
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:18,20 depth=3 0.910120->0.350000 reason=repeated_failed_pair:18,20
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:3,17 depth=3 0.910053->0.350000 reason=repeated_failed_pair:3,17
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:7,11 depth=3 0.909029->0.350000 reason=repeated_failed_pair:7,11
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:3,9 depth=3 0.908849->0.350000 reason=repeated_failed_pair:3,9
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:3,7 depth=3 0.908312->0.350000 reason=repeated_failed_pair:3,7
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:10,14 depth=3 0.907985->0.350000 reason=repeated_failed_pair:10,14
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:2,7 depth=3 0.907150->0.350000 reason=repeated_failed_pair:2,7
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:1,10 depth=3 0.907144->0.350000 reason=repeated_failed_pair:1,10
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:2,10 depth=3 0.906886->0.350000 reason=repeated_failed_pair:2,10
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:5,14 depth=3 0.906832->0.350000 reason=repeated_failed_pair:5,14
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:12:depth:3:2,5 depth=3 0.905460->0.350000 reason=repeated_failed_pair:2,5
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:16:depth:4:13,19 depth=4 0.890404->0.350000 reason=repeated_failed_pair:13,19
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:16:depth:4:3,17 depth=4 0.889288->0.350000 reason=repeated_failed_pair:3,17
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:16:depth:4:7,11 depth=4 0.888810->0.350000 reason=repeated_failed_pair:7,11
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:16:depth:4:3,9 depth=4 0.888314->0.350000 reason=repeated_failed_pair:3,9
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:16:depth:4:5,13 depth=4 0.888082->0.350000 reason=repeated_failed_pair:5,13
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:16:depth:4:3,7 depth=4 0.887754->0.350000 reason=repeated_failed_pair:3,7
- apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:16:depth:4:5,8 depth=4 0.887652->0.350000 reason=repeated_failed_pair:5,8
- apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:7:depth:3:15,17 depth=3 0.900700->0.350000 reason=repeated_failed_pair:15,17
- apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:7:depth:3:16,17 depth=3 0.900093->0.350000 reason=repeated_failed_pair:16,17
- apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:7:depth:3:2,8 depth=3 0.899245->0.350000 reason=repeated_failed_pair:2,8

## 边界

输出只能用于 branch ordering。它不能剪枝，不能替代 exact pricing closure，也不能作为 official lower bound。root 只做精确失败 row suppress，不做结构性泛化 suppress。
