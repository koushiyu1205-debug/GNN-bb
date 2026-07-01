# B2 Pricing-Tail Optimization 消融报告

## Completed Scope

- 当前只评估 B2 root pricing-tail；不进入 B3 branch tree、B4 cuts/formulation、B5 GAT guidance。
- B2B_seeded_tail_CG 是主模式；B2A_full_universe_rc_audit_fast_path 只作为显式 full-universe audit fast path。
- completion-bound pruning 默认关闭；只保留 audit / ordering / profiling 语义。

## Artifacts

- CSV rows: `runs/b2_pricing_tail_ablation/safe_probe_rows.csv`
- JSON summary: `runs/b2_pricing_tail_ablation/safe_probe_summary.json`

## Baseline Comparison Matrix

- 5-scale full: 20 instances。
- 10-scale: 1/20 instances。
- 20-scale fail-closed guard: 20 instances。
- 20-scale selected direct20 probe: 0 instances。
- 20-scale selected direct20 probe modes: B0_pure_direct_dp, B1A_full_universe_root_audit, B1B_seeded_root_CG, B2A_full_universe_rc_audit_fast_path, B2B_seeded_tail_CG。
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

## Summary

| scale | group | candidate | runs | BPC node LP | fail-closed | timeout | mean wall | p90 wall | mean added | mean rounds | mean final judge | candidate negatives | addable negatives | duplicate-only | hidden-negative |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 5-scale full | B0_pure_direct_dp | 20 | 0 | 0 | 0 | 0.00521 | 0.007018 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B1A_full_universe_root_audit | 20 | 20 | 0 | 0 | 0.198995 | 0.264497 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B1B_seeded_root_CG | 20 | 20 | 0 | 0 | 0.277097 | 0.383298 | 20.05 | 3.25 | 3.25 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B2A_full_universe_rc_audit_fast_path | 20 | 20 | 0 | 0 | 0.011483 | 0.015471 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 5 | 5-scale full | B2B_seeded_tail_CG | 20 | 20 | 0 | 0 | 0.278741 | 0.382996 | 20.05 | 3.25 | 3.25 | 1039 | 1039 | 0 | 0 |
| 10 | 10-scale selected5 | B0_pure_direct_dp | 1 | 0 | 0 | 0 | 0.11901 | 0.11901 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B1A_full_universe_root_audit | 1 | 0 | 1 | 1 | 10.0 | 10.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B1B_seeded_root_CG | 1 | 0 | 1 | 1 | 10.0 | 10.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B2A_full_universe_rc_audit_fast_path | 1 | 1 | 0 | 0 | 0.2579 | 0.2579 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 10 | 10-scale selected5 | B2B_seeded_tail_CG | 1 | 0 | 1 | 1 | 10.0 | 10.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B0_pure_direct_dp | 20 | 0 | 20 | 0 | 0.000706 | 0.000848 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B1A_full_universe_root_audit | 20 | 0 | 20 | 0 | 0.000671 | 0.000791 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B1B_seeded_root_CG | 20 | 0 | 20 | 0 | 0.000671 | 0.000773 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2A_full_universe_rc_audit_fast_path | 20 | 0 | 20 | 0 | 0.00078 | 0.000894 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2B_seeded_tail_CG | 20 | 0 | 20 | 0 | 0.000676 | 0.000727 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B0_pure_direct_dp | 20 | 0 | 20 | 0 | 0.001553 | 0.001842 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B1A_full_universe_root_audit | 20 | 0 | 20 | 0 | 0.00152 | 0.001677 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B1B_seeded_root_CG | 20 | 0 | 20 | 0 | 0.001503 | 0.001747 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2A_full_universe_rc_audit_fast_path | 20 | 0 | 20 | 0 | 0.001655 | 0.001823 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2B_seeded_tail_CG | 20 | 0 | 20 | 0 | 0.001538 | 0.00169 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

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
- duplicate_only_audit_status_counts: {'': 305}。

## Hidden-Negative Audit

- hidden_negative_count: 0。

## B2 Accepted?

- B2 accepted: False。
- required coverage met: False。
- B2A fast path accepted as full-universe audit optimization: True。
- B2B seeded tail accepted as next baseline: False。
- improvement_count: 105。
- reason: B2 remains diagnostic because required coverage is incomplete: need 10-scale selected>=5 and 20-scale selected direct20>=1.。

## Notes

- B2 runner is serial by default to avoid concurrent 20-scale final-judge memory spikes.
- Completion-bound pruning remains disabled; completion-bound data is audit/order/profiling only.
- 10-scale ran selected 1/20 first; full 20 is deferred until row time is acceptable.
- 20-scale fail-closed guard deliberately sets max_direct_tasks below 20; B0/B1/B2 fail-closed is expected.

## B3 Entry

- 只有 `b2b_seeded_tail_accepted=true` 且 redlines 全为 0 时，才允许把 B2B 作为进入 B3 的 accepted baseline。
