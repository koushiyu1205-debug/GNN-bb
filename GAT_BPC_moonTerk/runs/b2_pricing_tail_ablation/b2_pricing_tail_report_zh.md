# B2 Pricing-Tail Optimization 消融报告

## Completed Scope

- 当前只评估 B2 root pricing-tail；不进入 B3 branch tree、B4 cuts/formulation、B5 GAT guidance。
- B2B_seeded_tail_CG 是主模式；B2A_full_universe_rc_audit_fast_path 只作为显式 full-universe audit fast path。
- completion-bound pruning 默认关闭；只保留 audit / ordering / profiling 语义。

## Artifacts

- CSV rows: `GAT_BPC_moonTerk/runs/b2_pricing_tail_ablation/b2_pricing_tail_rows.csv`
- JSON summary: `GAT_BPC_moonTerk/runs/b2_pricing_tail_ablation/b2_pricing_tail_summary.json`

## Baseline Comparison Matrix

- 5-scale full: 20 instances。
- 10-scale: 5/20 instances。
- 20-scale fail-closed guard: 20 instances。
- 20-scale selected direct20 probe: 5 instances。
- 20-scale selected direct20 probe modes: B0_pure_direct_dp, B1A_full_universe_root_audit, B1B_seeded_root_CG, B2A_full_universe_rc_audit_fast_path, B2B_seeded_tail_CG, B2C_limited_pricing_diagnostic, B2D_proof_tail_kernel_profile, B2_PRODUCT_EXACT_SOLVER。
- 30-scale fail-closed diagnostic: 20 instances。

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

## Summary

| scale | group | candidate | runs | BPC node LP | fail-closed | timeout | mean wall | p90 wall | mean added | mean rounds | mean final judge | candidate negatives | addable negatives | duplicate-only | hidden-negative |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 5-scale full | B0_pure_direct_dp | 20 | 0 | 0 | 0 | 0.005572 | 0.008004 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B1A_full_universe_root_audit | 20 | 20 | 0 | 0 | 0.202434 | 0.274003 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B1B_seeded_root_CG | 20 | 20 | 0 | 0 | 0.281439 | 0.392598 | 20.05 | 3.25 | 3.25 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B2A_full_universe_rc_audit_fast_path | 20 | 20 | 0 | 0 | 0.012124 | 0.016923 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B2B_seeded_tail_CG | 20 | 20 | 0 | 0 | 0.28297 | 0.386306 | 20.05 | 3.25 | 3.25 | 1039 | 1039 | 0 | 0 |
| 5 | 5-scale full | B2C_limited_pricing_diagnostic | 20 | 0 | 0 | 0 | 0.1118 | 0.162444 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B2D_proof_tail_kernel_profile | 20 | 0 | 0 | 0 | 0.112329 | 0.166553 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 0 | 0.005292 | 0.007692 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale product exact full | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 0 | 0.149853 | 0.289189 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B0_pure_direct_dp | 5 | 0 | 0 | 0 | 0.088483 | 0.117858 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B1A_full_universe_root_audit | 5 | 0 | 5 | 5 | 10.0 | 10.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B1B_seeded_root_CG | 5 | 0 | 5 | 5 | 10.0 | 10.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B2A_full_universe_rc_audit_fast_path | 5 | 5 | 0 | 0 | 0.243048 | 0.293535 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B2B_seeded_tail_CG | 5 | 0 | 5 | 5 | 10.0 | 10.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B2C_limited_pricing_diagnostic | 5 | 0 | 0 | 0 | 0.091176 | 0.122606 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B2D_proof_tail_kernel_profile | 5 | 0 | 0 | 0 | 0.091241 | 0.120545 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B2_PRODUCT_EXACT_SOLVER | 5 | 0 | 0 | 0 | 0.088719 | 0.116809 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B0_pure_direct_dp | 20 | 0 | 20 | 0 | 0.000697 | 0.000791 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B1A_full_universe_root_audit | 20 | 0 | 20 | 0 | 0.000684 | 0.000772 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B1B_seeded_root_CG | 20 | 0 | 20 | 0 | 0.000676 | 0.000788 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2A_full_universe_rc_audit_fast_path | 20 | 0 | 20 | 0 | 0.000677 | 0.000757 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2B_seeded_tail_CG | 20 | 0 | 20 | 0 | 0.000726 | 0.000929 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 20 | 0 | 0.000705 | 0.000871 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B0_pure_direct_dp | 5 | 0 | 0 | 0 | 9.850529 | 11.958238 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B1A_full_universe_root_audit | 5 | 0 | 5 | 5 | 20.0 | 20.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B1B_seeded_root_CG | 5 | 0 | 5 | 5 | 20.0 | 20.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B2A_full_universe_rc_audit_fast_path | 5 | 0 | 5 | 5 | 20.0 | 20.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B2B_seeded_tail_CG | 5 | 0 | 5 | 5 | 20.0 | 20.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B2C_limited_pricing_diagnostic | 5 | 0 | 0 | 0 | 0.05454 | 0.058637 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B2D_proof_tail_kernel_profile | 5 | 0 | 0 | 0 | 0.053495 | 0.055078 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B2_PRODUCT_EXACT_SOLVER | 5 | 0 | 0 | 0 | 10.127871 | 12.538428 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B0_pure_direct_dp | 20 | 0 | 20 | 0 | 0.001605 | 0.00199 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B1A_full_universe_root_audit | 20 | 0 | 20 | 0 | 0.001599 | 0.001862 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B1B_seeded_root_CG | 20 | 0 | 20 | 0 | 0.001534 | 0.001582 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2A_full_universe_rc_audit_fast_path | 20 | 0 | 20 | 0 | 0.001659 | 0.001869 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2B_seeded_tail_CG | 20 | 0 | 20 | 0 | 0.001623 | 0.00174 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 20 | 0 | 0.001923 | 0.00231 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## 20-Scale Direct20 Probe Interpretation

- B0 direct20 solved rows: 5/5。
- B2_PRODUCT direct20 fixed-graph exact solved rows: 5/5。
- B1/B2 direct20 timeout rows: 20/20。
- 若 B0 direct20 闭合而 B1/B2 root rows timeout，本组应解释为 BPC root proof-tail 成本问题，不是 B0 direct-DP 失败。
- B2B real-scale improvement rows: 0。

## Addability Breakdown

- candidate_negative_count: 1039。
- addable_negative_count: 1039。
- duplicate_in_current_master_count: 0。
- in_pool_not_master_count: 0。
- forbidden_signature_count: 0。
- branch_filtered_count: 0。
- cut_filtered_count: 0。

## Duplicate-Only Audit Breakdown

- duplicate_only_count: 0。
- duplicate_only_audit_status_counts: {'': 500}。

## Hidden-Negative Audit

- hidden_negative_count: 0。

## Product Exact / Diagnostic Metrics

- product_exact_solution_count_by_scope: {'DIRECT_DP_FIXED_GRAPH_OPTIMAL': 50}。
- direct_dp_fallback_count: 50。
- labels_generated: 200679。
- time_to_first_negative rows are diagnostic only; no B2C/B2D row can create an official lower bound。

## B2 Accepted?

- B2 accepted: False。
- B2 product exact accepted as fixed-graph product fallback: True。
- required coverage met: True。
- product exact required coverage met: True。
- B2A fast path accepted as full-universe audit optimization: True。
- B2B seeded tail accepted as next baseline: False。
- improvement_count: 111。
- reason: B2 remains diagnostic until B2B shows a 10/20-scale improvement without redline violations.。

## Notes

- B2 runner is serial by default to avoid concurrent 20-scale final-judge memory spikes.
- Completion-bound pruning remains disabled; completion-bound data is audit/order/profiling only.
- 10-scale ran selected 5/20 first; full 20 is deferred until row time is acceptable.
- 20-scale fail-closed guard deliberately sets max_direct_tasks below 20; B0/B1/B2 fail-closed is expected.
- This artifact contains only the 20-scale selected direct20 probe rows.
- 20-scale selected direct20 probe used 1 instance(s), modes B0/B1A/B1B/B2A/B2B.
- 20-scale selected direct20 probe rows merged: 1 instance(s).
- 20-scale selected direct20 probe used 4 instance(s) from offset 1, modes B0/B1A/B1B/B2A/B2B.
- 20-scale selected direct20 probe rows merged: 5 instance(s).
- B2_PRODUCT rows were added as fixed-graph product exact/fallback rows and never as BPC certificates.
- B2C/B2D rows are limited pricing/proof-tail diagnostics only; they cannot create official bounds.
- 20-scale fail-closed guard deliberately uses `max_direct_tasks < 20`; this group verifies fail-closed behavior only.
- 20-scale fail-closed guard is not evidence that B0 direct20 failed or timed out.

## B3 Entry

- 只有 `b2b_seeded_tail_accepted=true` 且 redlines 全为 0 时，才允许把 B2B 作为进入 B3 的 accepted baseline。
