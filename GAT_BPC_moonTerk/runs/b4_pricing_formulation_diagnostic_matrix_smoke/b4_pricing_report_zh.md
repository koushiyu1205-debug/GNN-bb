# B4C/B4D Pricing Formulation 诊断报告

## Certificate Boundary

- 本报告只诊断 compact pricing formulation 对 proof-tail 的影响。
- negative-feasibility 可以找负列，但不能证明 no-negative。
- 只有 unrestricted exact pricing proof 且 dual bound 非负时，才允许 `can_certify_no_negative=True`。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_pricing_formulation_diagnostic_matrix_smoke/b4_pricing_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_pricing_formulation_diagnostic_matrix_smoke/b4_pricing_summary.json`

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| restricted_negative_feasibility_claimed_certificate_count | 0 | 0 |
| positive_incumbent_rc_claimed_certificate_count | 0 | 0 |

## Summary

| variant | rows | negatives | cut violations | best RC | best dual bound | certified | mean wall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V0_current_compact_pricing | 1 | 0 | 0 | None | None | 0 | 5.078425 |
| V1_endpoint_order_plus_pair_adjacency | 1 | 0 | 0 | None | None | 0 | 9.184051 |
| V2_latest_service_start_slot_bound | 1 | 0 | 0 | None | None | 0 | 4.30061 |
| V3_time_window_arc_pruning | 1 | 0 | 0 | None | None | 0 | 4.035932 |
| V4_combined_endpoint_pair_latest_start_time_window | 1 | 0 | 0 | None | None | 0 | 3.70992 |
| V5_subset_row_master_diagnostic_only | 1 | 0 | 0 | None | None | 0 | None |

## B4D Frontier Readout

- Pricing formulation diagnostic accepted: `False`。
- B4E pricing-formulation accepted: `False`。
- Measurable proof-tail progress rows: `0`。
- Measurable improvement vs V0 rows: `0`。
- No-negative certified rows: `0`。
- Tested variants: `V0_current_compact_pricing, V1_endpoint_order_plus_pair_adjacency, V2_latest_service_start_slot_bound, V3_time_window_arc_pruning, V4_combined_endpoint_pair_latest_start_time_window, V5_subset_row_master_diagnostic_only`。
- Missing variants: ``。

## Plan Questions

- Previous accepted baseline: B3B is accepted for 5/10/20; 30-scale remains diagnostic frontier.
- Formulation modes tested: `V0_current_compact_pricing, V1_endpoint_order_plus_pair_adjacency, V2_latest_service_start_slot_bound, V3_time_window_arc_pruning, V4_combined_endpoint_pair_latest_start_time_window, V5_subset_row_master_diagnostic_only`。
- Cut violation/binding: V5 subset-row active-pool diagnostic reports this through `cut_violated_count`; it does not add rows.
- Live cut audit: not part of B4C/B4D; live subset-row is gated in the cut report.
- Root/tree bound movement: not certified here; this report only measures compact pricing/frontier diagnostics.
- Node count / certificate time improvement: not claimed.
- Compact pricing best observed dual bound: `None`。
- Diagnostic accidentally claimed certificate: `False`。
- B4E accepted: `False`。
- Next target: run missing V0/V1/V3 under the same staged frontier dual before claiming formulation improvement.
