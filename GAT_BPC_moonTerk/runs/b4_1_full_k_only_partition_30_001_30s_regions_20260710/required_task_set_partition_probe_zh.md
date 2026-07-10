# B4.1 Required Task-Set Partition Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_after_epsilon_band_merge_official_eps_600s/stage_002/probe.json`
- Exact task-set regions plus the residual region form a candidate partition.
- This report is diagnostic-only; it does not claim an official no-negative certificate.

## Summary

- target_task_set_count: `0`
- partition_candidate_complete: `False`
- partition_candidate_can_certify_no_negative: `False`
- partition_candidate_gate_pass: `False`
- partition_candidate_gate_issue_codes: `['incomplete_residual_task_count_region', 'negative_bound_residual_task_count_region', 'unproven_residual_task_count_region']`
- official_certificate_allowed: `False`
- exact regions proven / incomplete / negative: `0` / `0` / `0`
- residual observed / proven / negative: `True` / `False` / `False`
- negative relation counts: already_active `0`; replacement `0`; new_task_set `0`
- dual/active scope: source active `371`; dual active `338`; delta `33`; mismatch rows `30`
- dual source: `selected_history_dual`; refresh status ``; refresh min RC `None`; refresh negatives `0`
- region MIP-start: enabled `10`; OK `4`; exact OK `0`; residual OK `4`
- negative RC audit fail count: `0`

| region | kind | variant | status | exact | best RC | manual RC | RC diff | dual cols | source cols | complete | region cert | negative | payload | active | relation |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| residual_task_count_001 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.114704 |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_002 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.054656 |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_003 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.035014 |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_004 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.026086 |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_005 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.004873 |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_006 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.001272 |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_007 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.0 |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_008 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_COUNT_PRICING_OPTIMAL | 0.0 |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_009 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | -0.0 |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_010 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | 8.1e-05 |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_011 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | None |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_012 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | None |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_013 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | None |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_014 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | None |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_015 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | None |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_016 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | None |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_017 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | None |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_018 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | None |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_019 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED | NOT_SOLVED | None |  |  | 338 | 371 | False | False | False | False | False |  |
| residual_task_count_020 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_021 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_022 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_023 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_024 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_025 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_026 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_027 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_028 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_029 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |
| residual_task_count_030 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 338 | 371 | True | True | False | False | False |  |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| official_certificate_claim_count | 0 | 0 |
| full_space_certificate_claim_count | 0 | 0 |
