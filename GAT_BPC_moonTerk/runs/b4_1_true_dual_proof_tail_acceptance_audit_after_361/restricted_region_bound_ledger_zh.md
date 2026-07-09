# B4.1 Restricted-Region Bound Ledger

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_358_600s/stage_001/probe.json`
- This ledger is diagnostic-only.
- It may reuse source phase bounds and targeted restricted/no-good probe bounds.
- It cannot claim an official full-space no-negative certificate.

## Summary

- pricing_proof_kind: `FRONTIER_BOUND_INCOMPLETE`
- best_known_global_remaining_rc_lb: `-0.142071959`
- source_bound_reuse_count: `2`
- targeted_bound_improvement_count: `1`

| region | forbidden sets | selected source | best known LB | source LB | targeted best LB | targeted variant | cert allowed |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| prefix_2 | 2 | source_phase | -0.121782748 | -0.121782748 | -0.189663739 | V4_current_strengthening | False |
| prefix_3 | 3 | targeted_probe | -0.142071959 | -0.317649341 | -0.142071959 | V4_current_triple_time_window_infeasible | False |
| prefix_1 | 1 | source_phase | -0.002763188 | -0.002763188 | None |  | False |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| official_bound_claim_count | 0 | 0 |
