# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `29.663933` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `3`
- added_column_count: `64`
- final_judge_call_count: `3`
- final_judge phase: `negative_feasibility_search`
- final_judge profile: `V4SH`
- final_judge formulation profile: `B4V4_strengthened_pair_weighted_seed_harvest`
- final_judge phase mode: `harvest_then_proof`
- proof-only skipped negative feasibility: `False`
- full-space negative feasibility proof attempted: `False`
- full-space negative feasibility proof can certify: `False`
- final_judge negative_column_count: `0`
- sortie slot-position bounds enabled: `None`
- sortie slot-position bounds rows: `None`
- single-task energy LB enabled: `None`
- single-task energy LB rows: `None`
- single-task shadow LB enabled: `None`
- single-task shadow LB rows: `None`
- triple time-window infeasible cut enabled: `None`
- triple time-window infeasible cut rows: `None`
- quad time-window infeasible cut enabled: `None`
- quad time-window infeasible cut rows: `None`
- hidden_negative_count: `None`
- hidden_negative_audit status: `None`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- optimization harvest target: `None`
- optimization harvest no-good scope: `None`
- optimization harvest found count: `None`
- forbidden task-set count: `None`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `0.000317`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_2_cold_exact_partition_smoke_30_001_120s/pools/scale_030/instance_001/stage_001/probe.json`
- resume initial columns: `115`
- active columns saved: `179`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 32 | -0.503364167 | None |  |
| 2 | FOUND_NEGATIVE | 32 | -0.263870344 | None |  |
| 3 | INCOMPLETE_LIMIT | 0 | None | None | negative_feasibility_search |
