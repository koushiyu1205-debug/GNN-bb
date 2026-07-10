# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `38.003708` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `2`
- added_column_count: `8`
- final_judge_call_count: `2`
- final_judge phase: `negative_feasibility_batch`
- final_judge profile: `V4SZ`
- final_judge formulation profile: `B4V4_strengthened_pair_weighted_zero_capacity_slot_truncation`
- final_judge phase mode: `harvest_then_proof`
- proof-only skipped negative feasibility: `False`
- full-space negative feasibility proof attempted: `False`
- full-space negative feasibility proof can certify: `False`
- final_judge negative_column_count: `4`
- sortie slot-position bounds enabled: `True`
- sortie slot-position bounds rows: `59`
- single-task energy LB enabled: `False`
- single-task energy LB rows: `0`
- single-task shadow LB enabled: `False`
- single-task shadow LB rows: `0`
- triple time-window infeasible cut enabled: `True`
- triple time-window infeasible cut rows: `24`
- quad time-window infeasible cut enabled: `False`
- quad time-window infeasible cut rows: `0`
- hidden_negative_count: `None`
- hidden_negative_audit status: `None`
- compact batch found count: `4`
- compact batch search calls: `4`
- compact no-good scope: `arc`
- optimization harvest target: `None`
- optimization harvest no-good scope: `None`
- optimization harvest found count: `None`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.157736`
- final_judge_wall_time: `20.078259`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_2_cold_exact_300s_full/pools/scale_030/instance_001/stage_002/probe.json`
- resume initial columns: `50`
- active columns saved: `58`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 4 | -0.133135 | 0.0 |  |
| 2 | FOUND_NEGATIVE | 4 | -0.157736 | 0.0 | negative_feasibility_batch |
