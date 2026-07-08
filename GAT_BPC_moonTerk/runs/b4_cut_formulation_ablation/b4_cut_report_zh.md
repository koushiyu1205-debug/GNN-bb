# B4 Cut/Formulation 消融报告

## Objective Boundary

- Official objective: `normalized_cost + normalized_risk + 0.4 * normalized_weighted_completion_time`。
- `makespan` 只作为 report metric，不进入 pricing objective。
- B4A restricted cut diagnostics 不能升级 certificate；B4B live subset-row 必须通过 cut/RMP/pricing audit。

## Artifacts

- CSV rows: `runs/b4_cut_formulation_ablation/b4_cut_rows.csv`
- JSON summary: `runs/b4_cut_formulation_ablation/b4_cut_summary.json`

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| objective_mismatch_count | 0 | 0 |
| certificate_scope_regression_count | 0 | 0 |
| direct_dp_certificate_leak_count | 0 | 0 |
| manual_rc_with_cuts_fail_count | 0 | 0 |
| pricing_rc_with_cuts_fail_count | 0 | 0 |
| cut_coefficient_audit_fail_count | 0 | 0 |
| cut_dual_sign_audit_fail_count | 0 | 0 |
| cut_dominance_compatibility_fail_count | 0 | 0 |
| fleet_lower_bound_live_enabled_without_proof_count | 0 | 0 |
| completion_bound_unsafe_with_cuts_count | 0 | 0 |
| restricted_pricing_claimed_no_negative_count | 0 | 0 |
| positive_incumbent_rc_claimed_certificate_count | 0 | 0 |

## Summary

| scale | group | mode | runs | tree | node LP | cut candidates | violated | max violation | mean wall | fail-closed |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 5-scale B4B live subset-row smoke | B4B_root_live_subset_row | 1 | 1 | 1 | 11 | 0 | 0.0 | 0.192997 | 0 |
| 5 | 5-scale full B4A diagnostic | B4A_cut_diagnostic_only | 20 | 20 | 20 | 220 | 0 | 0.0 | 0.384671 | 0 |
| 10 | 10-scale full B4A diagnostic | B4A_cut_diagnostic_only | 20 | 20 | 20 | 220 | 33 | 0.5 | 2.394534 | 0 |
| 20 | 20-scale full B4A restricted-pool diagnostic | B4A_cut_diagnostic_only | 20 | 0 | 0 | 220 | 0 | 0.0 | 0.033709 | 20 |
| 30 | 30-scale selected B4A restricted-pool diagnostic | B4A_cut_diagnostic_only | 1 | 0 | 0 | 11 | 0 | 0.0 | 0.103617 | 1 |

## Acceptance

- B4A diagnostic safe: `True`。
- B4B live subset-row accepted: `False`。
- B4E accepted candidate: `False`。
- Measurable improvement rows: `0`。

## Notes

- `cut_candidate_count > 0` 或 `cut_added_count > 0` 本身不是 B4 成功。
- restricted cut RMP 的 bound movement 只作为 diagnostic bound movement。
- fleet lower-bound cut 仍然不允许 live。

## Plan Questions

- Previous accepted baseline: `B3B_seeded_branch_price_tree` on normalized objective v1; 5/10/20 exact baseline is external to this B4 diagnostic report.
- Cut/formulation modes tested here: `B4A_cut_diagnostic_only, B4B_root_live_subset_row`。
- Any cut violated and bound on current RMP: `True`；see `cut_violated_count`, `would_bind_on_current_rmp`, and `max_violation` columns.
- Any live cut passed RC/pricing/dominance audits: `False`。
- Root/tree bound moved in accepted-safe cut run: `False`。
- Node count / certificate time improvement: not observed in B4A; B4B batch was not accepted.
- Compact pricing proof-bound movement on 30-scale: reported in `runs/b4_pricing_formulation_diagnostic/b4_pricing_report_zh.md`.
- Diagnostic accidentally claimed certificate: `False`。
- B4 accepted: `False`。
- Next target: compact pricing cut-dual/formulation support before expanding live subset-row cuts.
