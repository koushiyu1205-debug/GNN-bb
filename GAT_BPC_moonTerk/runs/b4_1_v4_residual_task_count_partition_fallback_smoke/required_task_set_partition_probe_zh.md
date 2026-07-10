# B4.1 Required Task-Set Partition Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_342_600s/stage_001/probe.json`
- Exact task-set regions plus the residual region form a candidate partition.
- This report is diagnostic-only; it does not claim an official no-negative certificate.

## Summary

- target_task_set_count: `1`
- partition_candidate_complete: `False`
- partition_candidate_can_certify_no_negative: `False`
- partition_candidate_gate_pass: `False`
- partition_candidate_gate_issue_codes: `['incomplete_residual_task_count_region', 'missing_residual_task_count_region', 'negative_bound_residual_task_count_region', 'unproven_residual_task_count_region']`
- official_certificate_allowed: `False`
- exact regions proven / incomplete / negative: `1` / `0` / `0`
- residual observed / proven / negative: `True` / `False` / `False`
- negative relation counts: already_active `0`; replacement `0`; new_task_set `0`
- dual/active scope: source active `345`; dual active `345`; delta `0`; mismatch rows `0`
- dual source: `refreshed_active_pool_restricted_rmp`; refresh status `RESTRICTED_RMP_OPTIMAL`; refresh min RC `-0.0`; refresh negatives `0`
- region MIP-start: enabled `5`; OK `5`; exact OK `1`; residual OK `4`
- negative RC audit fail count: `0`

| region | kind | variant | status | exact | best RC | manual RC | RC diff | dual cols | source cols | complete | region cert | negative | payload | active | relation |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| exact_001 | exact_task_set | V4_current_strengthening | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.0085135 |  |  | 345 | 345 | True | True | False | False | False |  |
| residual_task_count_001 | residual_task_count | V4_current_strengthening | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.096858 |  |  | 345 | 345 | True | True | False | False | False |  |
| residual_task_count_002 | residual_task_count | V4_current_strengthening | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.0336345 |  |  | 345 | 345 | True | True | False | False | False |  |
| residual_task_count_003 | residual_task_count | V4_current_strengthening | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.0012365 |  |  | 345 | 345 | True | True | False | False | False |  |
| residual_task_count_004 | residual_task_count | V4_current_strengthening | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 0.0025715 |  |  | 345 | 345 | False | False | False | False | False |  |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| official_certificate_claim_count | 0 | 0 |
| full_space_certificate_claim_count | 0 | 0 |
