# B2 Pricing-Tail Optimization 消融报告

## Completed Scope

- 当前只评估 B2 root pricing-tail；不进入 B3 branch tree、B4 cuts/formulation、B5 GAT guidance。
- B2B_R3_true_dual_negative_search_worker 是本轮新增候选；B2B_R2_worker_before_final_judge 与 B2B_seeded_tail_CG 保留为对照。
- B2A_full_universe_rc_audit_fast_path 只作为显式 full-universe audit fast path。
- completion-bound pruning 默认关闭；只保留 audit / ordering / profiling 语义。

## Objective Boundary

- Official objective: `1.0 * normalized_operating_cost + 1.0 * normalized_risk + 0.4 * normalized_weighted_completion_time`。
- `makespan` 只作为 report/evaluation metric，不进入 pricing objective 或 reduced cost。
- `BPC_NODE_LP_CERTIFIED` 只证明 normalized additive objective 的 root LP closure。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/smoke/b2_scale005_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/smoke/b2_scale005_summary.json`

## Baseline Comparison Matrix

- 5-scale full: 0 instances。
- 10-scale: 0/0 instances。
- 20-scale fail-closed guard: 0 instances。
- 20-scale selected direct20 probe: 0 instances。
- 20-scale selected direct20 probe modes: 。
- 30-scale fail-closed diagnostic: 0 instances。

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| root_bound_gt_B0_violation_count | 0 | 0 |
| direct_root_official_leak_count | 0 | 0 |
| manual_rc_fail_count | 0 | 0 |
| pricing_rc_fail_count | 0 | 0 |
| certificate_scope_regression_count | 0 | 0 |
| objective_mismatch_count | 0 | 0 |
| b1_5scale_regression_count | 0 | 0 |
| proof_debt_unreleased_certified_count | 0 | 0 |
| selected_harvest_addability_fail_count | 0 | 0 |

## Summary

| scale | group | candidate | runs | BPC node LP | fail-closed | timeout | mean wall | p90 wall | mean added | mean rounds | mean final judge | candidate negatives | addable negatives | duplicate-only | hidden-negative |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 5-scale full normalized objective | B0_pure_direct_dp | 1 | 0 | 0 | 0 | 0.005646 | 0.005646 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full normalized objective | B1A_full_universe_root_audit | 1 | 1 | 0 | 0 | 0.012441 | 0.012441 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full normalized objective | B1B_seeded_root_CG | 1 | 1 | 0 | 0 | 0.011716 | 0.011716 | 19 | 3 | 3 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full normalized objective | B2A_full_universe_rc_audit_fast_path | 1 | 1 | 0 | 0 | 0.011664 | 0.011664 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full normalized objective | B2B_R2_worker_before_final_judge | 1 | 1 | 0 | 0 | 0.156904 | 0.156904 | 18 | 5 | 2 | 42 | 42 | 0 | 0 |
| 5 | 5-scale full normalized objective | B2B_R3_true_dual_negative_search_worker | 1 | 1 | 0 | 0 | 0.15821 | 0.15821 | 18 | 5 | 2 | 42 | 42 | 0 | 0 |
| 5 | 5-scale full normalized objective | B2B_seeded_tail_CG | 1 | 1 | 0 | 0 | 0.028297 | 0.028297 | 19 | 3 | 3 | 19 | 19 | 0 | 0 |
| 5 | 5-scale full normalized objective | B2C_limited_pricing_diagnostic | 1 | 0 | 0 | 0 | 0.04347 | 0.04347 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 5 | 5-scale full normalized objective | B2D_proof_tail_kernel_profile | 1 | 0 | 0 | 0 | 0.045195 | 0.045195 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 5 | 5-scale full normalized objective | B2_PRODUCT_EXACT_SOLVER | 1 | 0 | 0 | 0 | 0.006889 | 0.006889 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Addability Breakdown

- candidate_negative_count: 105。
- addable_negative_count: 103。
- selected_would_enter_master_count: 103。
- selected_harvest_addability_fail_count: 0。
- duplicate_in_current_master_count: 0。
- in_pool_not_master_count: 0。
- forbidden_signature_count: 0。
- branch_filtered_count: 0。
- cut_filtered_count: 0。

## Duplicate-Only Audit Breakdown

- duplicate_only_count: 0。
- duplicate_only_audit_status_counts: {'': 10}。

## Hidden-Negative Audit

- hidden_negative_count: 0。

## Product Exact / Diagnostic Metrics

- product_exact_solution_count_by_scope: {'DIRECT_DP_FIXED_GRAPH_OPTIMAL': 1}。
- direct_dp_fallback_count: 1。
- labels_generated: 2868。
- labels_generated_total: 2868。
- labels_extended: 82286。
- worker_found_addable_negative_count: 8。
- final_judge_saved_by_worker_count: 6。
- exact_first_step_bound_pruning_enabled: false；本轮只做 audit/order/profile。
- time_to_first_negative rows are diagnostic only; no B2C/B2D row can create an official lower bound。

## B2 Round3 Answers

- 1. B2_PRODUCT accepted: False；scope 必须保持 DIRECT_DP_FIXED_GRAPH_OPTIMAL，不是 BPC certificate。
- 2. B2A accepted: True；仅作为 full-universe membership RC audit fast path。
- 3. B2B_R3 accepted: False；B2B_R2 accepted: False。
- 4. 10/20 timeout bottleneck: 缺少 10/20 root pricing rows，无法归因。
- 5. 允许进入 B3: False；只有 B2B_R3 在 required coverage 上通过且 redlines 全 0 才能进入。

## B2 Accepted?

- B2 accepted: False。
- required coverage met: False。
- required direct20 modes met: False；missing: ['B0_pure_direct_dp', 'B1A_full_universe_root_audit', 'B1B_seeded_root_CG', 'B2A_full_universe_rc_audit_fast_path', 'B2B_R2_worker_before_final_judge', 'B2B_R3_true_dual_negative_search_worker', 'B2C_limited_pricing_diagnostic', 'B2D_proof_tail_kernel_profile', 'B2_PRODUCT_EXACT_SOLVER']。
- product exact required coverage met: False。
- B2A fast path accepted as full-universe audit optimization: True。
- B2B seeded tail accepted as next baseline: False。
- B2B_R2 seeded tail accepted as next baseline: False。
- B2B_R3 seeded tail accepted as next baseline: False。
- improvement_count: 4。
- B2B_R2 real-scale improvement count: 0。
- B2B_R2 10-scale improvement count: 0。
- B2B_R3 real-scale improvement count: 0。
- B2B_R3 10-scale improvement count: 0。
- reason: B2 remains diagnostic because required coverage is incomplete: need 10-scale selected>=5, 20-scale selected direct20>=5, and each required direct20 mode on >=5 instances. Undercovered direct20 modes: B0_pure_direct_dp,B1A_full_universe_root_audit,B1B_seeded_root_CG,B2A_full_universe_rc_audit_fast_path,B2B_R2_worker_before_final_judge,B2B_R3_true_dual_negative_search_worker,B2C_limited_pricing_diagnostic,B2D_proof_tail_kernel_profile,B2_PRODUCT_EXACT_SOLVER.。
- 20-scale selected direct20 probe did not run in this artifact; required coverage is incomplete.

## B3 Entry

- 只有 `b2b_r3_seeded_tail_accepted=true` 且 redlines 全为 0 时，才允许把 B2B_R3 作为进入 B3 的 accepted baseline。
