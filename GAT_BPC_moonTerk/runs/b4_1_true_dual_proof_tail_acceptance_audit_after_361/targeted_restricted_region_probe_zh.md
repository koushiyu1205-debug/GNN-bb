# B4.1 Targeted Restricted-Region Proof Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json`
- This report re-solves restricted/no-good pricing regions under true RMP duals.
- It is diagnostic-only and cannot claim an official no-negative certificate.

## Summary

| region | forbidden sets | rows | best bound | best RC | best variant | improved rows | time-limit rows |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| prefix_2 | 2 | 2 | -0.189663739 | 0.030820431 | V4_current_strengthening | 0 | 2 |

## Rows

| region | variant | status | exact | best RC | dual bound | source bound | delta | wall s | cert allowed |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| prefix_2 | V2_latest_service_start_slot_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 0.119161098 | -0.571479122 | -0.121782748 | -0.449696374 | 28.573405 | False |
| prefix_2 | V4_current_strengthening | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 0.030820431 | -0.189663739 | -0.121782748 | -0.067880991 | 27.865564 | False |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| restricted_no_good_claimed_certificate_count | 0 | 0 |
