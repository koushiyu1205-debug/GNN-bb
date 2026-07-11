# B4.1 Required Task-Set Partition Probe

## Boundary

- Source probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_2_cold_exact_large_support_projection_smoke_30_001_120s_20260711/pools/scale_030/instance_001/stage_001/probe.json`
- Exact task-set regions plus the residual region form a candidate partition.
- This report is diagnostic-only; it does not claim an official no-negative certificate.

## Summary

- target_task_set_count: `32`
- partition_candidate_complete: `False`
- partition_candidate_can_certify_no_negative: `False`
- partition_candidate_gate_pass: `False`
- partition_candidate_gate_issue_codes: `['missing_residual_task_count_region']`
- official_certificate_allowed: `False`
- exact regions proven / incomplete / negative: `32` / `0` / `0`
- residual observed / proven / negative: `True` / `False` / `False`
- negative relation counts: already_active `0`; replacement `0`; new_task_set `0`
- dual/active scope: source active `224`; dual active `224`; delta `0`; mismatch rows `0`
- dual source: `refreshed_active_pool_restricted_rmp`; refresh status `RESTRICTED_RMP_OPTIMAL`; refresh min RC `-0.0`; refresh negatives `0`
- region MIP-start: enabled `32`; OK `13`; exact OK `13`; residual OK `0`
- negative RC audit fail count: `0`
- adaptive active-sortie refinement: enabled `False`; attempts `0`; coarse accepted `0`; refined `0`; discarded coarse wall `0.0`; total wall `10.573961`

| region | kind | variant | status | exact | best RC | manual RC | RC diff | dual cols | source cols | complete | region cert | negative | payload | active | relation |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- |
| exact_001 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | -0.0 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_002 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_003 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.09990881 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_004 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.016764619 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_005 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_006 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_007 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_008 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_009 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_010 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_011 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.15179681 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_012 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.229012286 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_013 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_014 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_015 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.37563281 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_016 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_017 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_018 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_019 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.24600562 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_020 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_021 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_022 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_023 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_024 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.116241619 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_025 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.357618953 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_026 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.312153239 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_027 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.219213286 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_028 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.342898858 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_029 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_030 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_031 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_OPTIMAL | REQUIRED_TASK_SET_PRICING_OPTIMAL | 0.159280619 |  |  | 224 | 224 | True | True | False | False | False |  |
| exact_032 | exact_task_set | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_TASK_SET_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_001 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_002 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_003 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE | REQUIRED_TASK_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_004 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_005 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_006 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_007 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_008 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_009 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_010 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_011 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_012 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_013 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_014 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_015 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_016 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_017 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_018 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_019 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_020 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |
| residual_task_count_022_active_sorties_021 | residual_task_count | V4_current_pair_conflict_capacity_bound | COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE | REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE | None |  |  | 224 | 224 | True | True | False | False | False |  |

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| certificate_claim_count | 0 | 0 |
| official_certificate_claim_count | 0 | 0 |
| full_space_certificate_claim_count | 0 | 0 |
