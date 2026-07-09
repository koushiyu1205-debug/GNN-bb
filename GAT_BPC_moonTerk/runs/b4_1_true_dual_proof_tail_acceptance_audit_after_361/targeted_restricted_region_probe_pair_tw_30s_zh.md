# B4.1 Targeted Restricted-Region Proof Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json`
- This report re-solves restricted/no-good pricing regions under true RMP duals.
- It is diagnostic-only and cannot claim an official no-negative certificate.

## Summary

| region | forbidden sets | rows | best bound | best RC | best variant | improved rows | time-limit rows |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| prefix_2 | 2 | 1 | -0.188384591 | 0.01210349 | V4_current_strengthening | 0 | 1 |

## Rows

| region | variant | status | exact | best RC | dual bound | source bound | delta | pair TW cuts | wall s | cert allowed |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| prefix_2 | V4_current_strengthening | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 0.01210349 | -0.188384591 | -0.121782748 | -0.066601843 | 1092 | 27.247857 | False |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| restricted_no_good_claimed_certificate_count | 0 | 0 |
