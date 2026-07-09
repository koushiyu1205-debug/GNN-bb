# B4.1 Targeted Restricted-Region Proof Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json`
- This report re-solves restricted/no-good pricing regions under true RMP duals.
- It is diagnostic-only and cannot claim an official no-negative certificate.

## Summary

| region | forbidden sets | rows | best bound | best RC | best variant | improved rows | time-limit rows |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| prefix_3 | 3 | 1 | -0.142071959 | -1.6569e-05 | V4_current_triple_time_window_infeasible | 1 | 1 |

## Rows

| region | variant | status | exact | best RC | dual bound | source bound | delta | pair TW cuts | triple TW cuts | quad TW cuts | wall s | cert allowed |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| prefix_3 | V4_current_triple_time_window_infeasible | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | -1.6569e-05 | -0.142071959 | -0.317649341 | 0.175577382 | 1092 | 210 | 0 | 110.130122 | False |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| restricted_no_good_claimed_certificate_count | 0 | 0 |
