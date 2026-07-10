# B4.1 Required Task-Set Partition Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_v4_residual_task_count_k5_variant_sweep_probe/probe_after_k5_partition_negative_merge.json`
- Exact task-set regions plus the residual region form a candidate partition.
- This report is diagnostic-only; it does not claim an official no-negative certificate.

## Summary

- target_task_set_count: `3`
- partition_candidate_complete: `False`
- partition_candidate_can_certify_no_negative: `False`
- partition_candidate_gate_pass: `False`
- partition_candidate_gate_issue_codes: `['missing_residual_task_count_region', 'negative_bound_residual_task_count_region', 'negative_residual_task_count_region', 'unproven_residual_task_count_region']`
- official_certificate_allowed: `False`
- exact regions proven / incomplete / negative: `3` / `0` / `0`
- residual observed / proven / negative: `True` / `False` / `True`
- negative relation counts: already_active `0`; replacement `1`; new_task_set `0`
- dual/active scope: source active `347`; dual active `347`; delta `0`; mismatch rows `0`
- dual source: `refreshed_active_pool_restricted_rmp`; refresh status `RESTRICTED_RMP_OPTIMAL`; refresh min RC `-1e-09`; refresh negatives `0`
- region MIP-start: enabled `4`; OK `4`; exact OK `3`; residual OK `1`
- negative RC audit fail count: `0`

| region | kind | variant | status | exact | best RC | manual RC | RC diff | dual cols | source cols | complete | region cert | negative | payload | active | relation |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| exact_001 | exact_task_set | V4_current_triple_time_window_infeasible | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.001147623 |  |  | 347 | 347 | True | True | False | False | False |  |
| exact_002 | exact_task_set | V4_current_triple_time_window_infeasible | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.000785049 |  |  | 347 | 347 | True | True | False | False | False |  |
| exact_003 | exact_task_set | V4_current_triple_time_window_infeasible | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.001083476 |  |  | 347 | 347 | True | True | False | False | False |  |
| residual_task_count_005 | residual_task_count | V4_current_triple_time_window_infeasible | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | -0.000325 | -0.000325 | 0.0 | 347 | 347 | True | False | True | True | False | replacement |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| official_certificate_claim_count | 0 | 0 |
| full_space_certificate_claim_count | 0 | 0 |
