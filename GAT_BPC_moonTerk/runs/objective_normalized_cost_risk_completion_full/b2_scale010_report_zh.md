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

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/b2_scale010_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/b2_scale010_summary.json`

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
| certificate_scope_regression_count | 2 | 0 |
| objective_mismatch_count | 0 | 0 |
| b1_5scale_regression_count | 0 | 0 |
| proof_debt_unreleased_certified_count | 0 | 0 |
| selected_harvest_addability_fail_count | 0 | 0 |

## Summary

| scale | group | candidate | runs | BPC node LP | fail-closed | timeout | mean wall | p90 wall | mean added | mean rounds | mean final judge | candidate negatives | addable negatives | duplicate-only | hidden-negative |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 10-scale full normalized objective | B0_pure_direct_dp | 20 | 0 | 0 | 0 | 0.288507 | 0.586071 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale full normalized objective | B1A_full_universe_root_audit | 20 | 20 | 0 | 0 | 0.358161 | 0.713977 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| 10 | 10-scale full normalized objective | B1B_seeded_root_CG | 20 | 20 | 0 | 0 | 0.325141 | 0.598744 | 150.5 | 3.4 | 3.4 | 0 | 0 | 0 | 0 |
| 10 | 10-scale full normalized objective | B2A_full_universe_rc_audit_fast_path | 20 | 20 | 0 | 0 | 0.354968 | 0.69485 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale full normalized objective | B2B_R2_worker_before_final_judge | 20 | 19 | 1 | 0 | 1.457648 | 2.607069 | 96.05 | 6.4 | 3.35 | 3128 | 3128 | 0 | 647 |
| 10 | 10-scale full normalized objective | B2B_R3_true_dual_negative_search_worker | 20 | 19 | 1 | 0 | 1.456425 | 2.617062 | 96.05 | 6.4 | 3.35 | 3128 | 3128 | 0 | 647 |
| 10 | 10-scale full normalized objective | B2B_seeded_tail_CG | 20 | 20 | 0 | 0 | 1.508895 | 3.456532 | 120.55 | 3.9 | 3.9 | 3301 | 3301 | 0 | 0 |
| 10 | 10-scale full normalized objective | B2C_limited_pricing_diagnostic | 20 | 0 | 0 | 0 | 0.923344 | 1.381209 | 0 | 0 | 0 | 65 | 0 | 0 | 0 |
| 10 | 10-scale full normalized objective | B2D_proof_tail_kernel_profile | 20 | 0 | 0 | 0 | 0.920141 | 1.353319 | 0 | 0 | 0 | 65 | 0 | 0 | 0 |
| 10 | 10-scale full normalized objective | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 0 | 1.3e-05 | 1.6e-05 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Addability Breakdown

- candidate_negative_count: 9687。
- addable_negative_count: 9557。
- selected_would_enter_master_count: 8353。
- selected_harvest_addability_fail_count: 0。
- duplicate_in_current_master_count: 0。
- in_pool_not_master_count: 0。
- forbidden_signature_count: 0。
- branch_filtered_count: 0。
- cut_filtered_count: 0。

## Duplicate-Only Audit Breakdown

- duplicate_only_count: 0。
- duplicate_only_audit_status_counts: {'': 200}。

## Hidden-Negative Audit

- hidden_negative_count: 1294。

## Product Exact / Diagnostic Metrics

- product_exact_solution_count_by_scope: {'DIRECT_DP_FIXED_GRAPH_OPTIMAL': 20}。
- direct_dp_fallback_count: 20。
- labels_generated: 351228。
- labels_generated_total: 351228。
- labels_extended: 4149026。
- worker_found_addable_negative_count: 142。
- final_judge_saved_by_worker_count: 122。
- exact_first_step_bound_pruning_enabled: false；本轮只做 audit/order/profile。
- time_to_first_negative rows are diagnostic only; no B2C/B2D row can create an official lower bound。

## B2 Round3 Answers

- 1. B2_PRODUCT accepted: False；scope 必须保持 DIRECT_DP_FIXED_GRAPH_OPTIMAL，不是 BPC certificate。
- 2. B2A accepted: False；仅作为 full-universe membership RC audit fast path。
- 3. B2B_R3 accepted: False；B2B_R2 accepted: False。
- 4. 10/20 timeout bottleneck: final judge / label generation：closure 阶段耗时或 labels_generated 主导。
- 5. 允许进入 B3: False；只有 B2B_R3 在 required coverage 上通过且 redlines 全 0 才能进入。

## B2 Accepted?

- B2 accepted: False。
- required coverage met: False。
- required direct20 modes met: False；missing: ['B0_pure_direct_dp', 'B1A_full_universe_root_audit', 'B1B_seeded_root_CG', 'B2A_full_universe_rc_audit_fast_path', 'B2B_R2_worker_before_final_judge', 'B2B_R3_true_dual_negative_search_worker', 'B2C_limited_pricing_diagnostic', 'B2D_proof_tail_kernel_profile', 'B2_PRODUCT_EXACT_SOLVER']。
- product exact required coverage met: False。
- B2A fast path accepted as full-universe audit optimization: False。
- B2B seeded tail accepted as next baseline: False。
- B2B_R2 seeded tail accepted as next baseline: False。
- B2B_R3 seeded tail accepted as next baseline: False。
- improvement_count: 79。
- B2B_R2 real-scale improvement count: 0。
- B2B_R2 10-scale improvement count: 0。
- B2B_R3 real-scale improvement count: 0。
- B2B_R3 10-scale improvement count: 0。
- reason: B2 remains diagnostic because required coverage is incomplete: need 10-scale selected>=5, 20-scale selected direct20>=5, and each required direct20 mode on >=5 instances. Undercovered direct20 modes: B0_pure_direct_dp,B1A_full_universe_root_audit,B1B_seeded_root_CG,B2A_full_universe_rc_audit_fast_path,B2B_R2_worker_before_final_judge,B2B_R3_true_dual_negative_search_worker,B2C_limited_pricing_diagnostic,B2D_proof_tail_kernel_profile,B2_PRODUCT_EXACT_SOLVER.。
- 20-scale selected direct20 probe did not run in this artifact; required coverage is incomplete.

## B3 Entry

- 只有 `b2b_r3_seeded_tail_accepted=true` 且 redlines 全为 0 时，才允许把 B2B_R3 作为进入 B3 的 accepted baseline。
