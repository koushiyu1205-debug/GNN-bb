# B4.1 Required Task-Set Partition Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_v4_residual_task_count_k4_fallback_20s_probe/probe_after_k4_partition_negative_merge.json`
- Exact task-set regions plus the residual region form a candidate partition.
- This report is diagnostic-only; it does not claim an official no-negative certificate.

## Summary

- target_task_set_count: `1`
- partition_candidate_complete: `False`
- partition_candidate_can_certify_no_negative: `False`
- partition_candidate_gate_pass: `False`
- partition_candidate_gate_issue_codes: `['incomplete_residual_task_count_region', 'missing_residual_task_count_region', 'mixed_formulation_partition_rows', 'mixed_variant_partition_rows', 'negative_bound_residual_task_count_region', 'unproven_residual_task_count_region']`
- official_certificate_allowed: `False`
- exact regions proven / incomplete / negative: `1` / `0` / `0`
- residual observed / proven / negative: `True` / `False` / `False`
- negative relation counts: already_active `0`; replacement `0`; new_task_set `0`
- dual/active scope: source active `346`; dual active `346`; delta `0`; mismatch rows `0`
- dual source: `refreshed_active_pool_restricted_rmp`; refresh status `RESTRICTED_RMP_OPTIMAL`; refresh min RC `0.0`; refresh negatives `0`
- region MIP-start: enabled `8`; OK `8`; exact OK `4`; residual OK `4`
- negative RC audit fail count: `0`

| region | kind | variant | status | exact | best RC | manual RC | RC diff | dual cols | source cols | complete | region cert | negative | payload | active | relation |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| exact_001 | exact_task_set | V4_current_strengthening | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.0098698 |  |  | 346 | 346 | True | True | False | False | False |  |
| exact_001 | exact_task_set | V4_current_pair_weighted_completion_lb | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.0098698 |  |  | 346 | 346 | True | True | False | False | False |  |
| exact_001 | exact_task_set | V4_current_triple_time_window_infeasible | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.0098698 |  |  | 346 | 346 | True | True | False | False | False |  |
| exact_001 | exact_task_set | V4_current_quad_time_window_infeasible | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.0098698 |  |  | 346 | 346 | True | True | False | False | False |  |
| residual_task_count_005 | residual_task_count | V4_current_strengthening | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 0.0 |  |  | 346 | 346 | False | False | False | False | False |  |
| residual_task_count_005 | residual_task_count | V4_current_pair_weighted_completion_lb | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 0.0 |  |  | 346 | 346 | False | False | False | False | False |  |
| residual_task_count_005 | residual_task_count | V4_current_triple_time_window_infeasible | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | -0.0008186 | -0.0008186 | 0.0 | 346 | 346 | False | False | True | True | False | new_task_set |
| residual_task_count_005 | residual_task_count | V4_current_quad_time_window_infeasible | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 0.0 |  |  | 346 | 346 | False | False | False | False | False |  |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| official_certificate_claim_count | 0 | 0 |
| full_space_certificate_claim_count | 0 | 0 |
