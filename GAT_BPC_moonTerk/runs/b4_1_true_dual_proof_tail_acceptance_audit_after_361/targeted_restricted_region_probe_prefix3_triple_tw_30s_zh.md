# B4.1 Targeted Restricted-Region Proof Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json`
- This report re-solves restricted/no-good pricing regions under true RMP duals.
- It is diagnostic-only and cannot claim an official no-negative certificate.

## Summary

| region | forbidden sets | rows | best bound | best RC | best variant | improved rows | time-limit rows |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| prefix_3 | 3 | 1 | -0.186524912 | 0.098483078 | V4_current_triple_time_window_infeasible | 1 | 1 |

## Rows

| region | variant | status | exact | best RC | dual bound | source bound | delta | pair TW cuts | triple TW cuts | wall s | cert allowed |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| prefix_3 | V4_current_triple_time_window_infeasible | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 0.098483078 | -0.186524912 | -0.317649341 | 0.131124429 | 1092 | 210 | 27.302873 | False |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| restricted_no_good_claimed_certificate_count | 0 | 0 |
