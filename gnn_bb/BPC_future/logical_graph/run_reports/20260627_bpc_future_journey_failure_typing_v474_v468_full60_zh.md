# V474：V468 20 规模剩余失败分型

本报告只读取已有日志和审计结果，不运行 BPC、pricing 或 RMP；不影响 official bound、certificate 或剪枝逻辑。

## 总览

- 全量实例：60
- 未解实例：27
- status 计数：`{'OPTIMAL': 33, 'EXTERNAL_TIME_LIMIT': 24, 'TIME_LIMIT': 3}`
- primary failure type：`{'branch_tree_plus_completion_tail': 24, 'completion_bound_proof_cost': 2, 'lp_bound_below_incumbent': 1}`
- failure tag：`{'branch_tree_right_censored': 24, 'branch_tree_too_wide_or_deep': 22, 'completion_bound_proof_cost': 26, 'negative_chain_continues': 24, 'lp_bound_below_incumbent': 23, 'broad_plateau_or_missing_refinement_target': 6, 'early_branch_before_final_probe_disabled': 27, 'root_no_branch': 3, 'completion_bound_uncertified_time_limit': 3}`

## 关键判断

- 当前 27 个未解实例的主问题不是“root pair 正例不够”这一件事，而是 root/shallow 分支之后的深层分支树和 completion-bound proof cost 叠加。
- V469 child-probe 高分但 V470 full replay 全超时，和这里的分型一致：局部 child corrected-bound/proof-cost proxy 不能直接代表完整闭环。
- 后续 GAT branch score 应加入深层 branch、child ordering、completion retry/proof CPU 的反事实标签；单纯扩大 root top-k 会继续产生高分假阳性。

## 未解实例分型

| instance | status | primary | branch | depth | child CB retry | CB profile s | tags |
|---|---:|---|---:|---:|---:|---:|---|
| apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 12 | 4 | 52 | 233.1 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;broad_plateau_or_missing_refinement_target;early_branch_before_final_probe_disabled |
| apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205 | TIME_LIMIT | completion_bound_proof_cost |  |  |  | 90.0 | root_no_branch;completion_bound_uncertified_time_limit;early_branch_before_final_probe_disabled |
| apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 3 | 1 | 9 | 137.9 | branch_tree_right_censored;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 8 | 3 | 40 | 239.9 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;broad_plateau_or_missing_refinement_target;early_branch_before_final_probe_disabled |
| apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 6 | 2 | 31 | 176.3 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818 | TIME_LIMIT | completion_bound_proof_cost |  |  |  | 129.1 | root_no_branch;completion_bound_proof_cost;completion_bound_uncertified_time_limit;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 20 | 6 | 68 | 322.2 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 34 | 7 | 110 | 267.1 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 30 | 6 | 113 | 287.6 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 31 | 7 | 111 | 284.0 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 7 | 3 | 31 | 333.2 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| apollo15_20km_random-wave_randomtw_tasks020_01_seed61000 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 18 | 6 | 68 | 192.4 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;broad_plateau_or_missing_refinement_target;early_branch_before_final_probe_disabled |
| apollo15_20km_random-wave_randomtw_tasks020_02_seed61102 | TIME_LIMIT | lp_bound_below_incumbent |  |  |  | 147.1 | root_no_branch;completion_bound_proof_cost;completion_bound_uncertified_time_limit;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| apollo15_20km_random-wave_randomtw_tasks020_10_seed61919 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 11 | 4 | 30 | 172.7 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 26 | 10 | 158 | 278.9 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;broad_plateau_or_missing_refinement_target;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 18 | 6 | 61 | 305.2 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 26 | 6 | 108 | 318.1 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;broad_plateau_or_missing_refinement_target;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 9 | 4 | 29 | 303.0 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 25 | 8 | 80 | 215.1 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 3 | 2 | 21 | 249.2 | branch_tree_right_censored;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 21 | 5 | 74 | 246.9 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 11 | 3 | 31 | 180.4 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 35 | 8 | 143 | 251.8 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 23 | 5 | 112 | 341.0 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 41 | 11 | 126 | 316.2 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 31 | 8 | 145 | 236.4 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;broad_plateau_or_missing_refinement_target;early_branch_before_final_probe_disabled |
| tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718 | EXTERNAL_TIME_LIMIT | branch_tree_plus_completion_tail | 62 | 11 | 194 | 205.6 | branch_tree_right_censored;branch_tree_too_wide_or_deep;completion_bound_proof_cost;negative_chain_continues;lp_bound_below_incumbent;early_branch_before_final_probe_disabled |

## 下一步

1. 不把 V472/V473 直接放大全量；先补深层分支和 child-ordering 标签。
2. 对 failure type 为 `branch_tree_plus_completion_tail` 的实例，生成 depth 1-4 的 limited replay/runbook，而不是继续 root top-k。
3. 对 `completion_bound_proof_cost` 高的实例，单独做 final-probe/CB-tail profile 和 min-fill/cache/harvest 的精确安全优化。
4. 对 `lp_bound_below_incumbent` 或宽平台节点，转 incumbent/cuts/formulation，不把更多 pricing proof 误当作可剪枝能力。
