# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `601.887824` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `3`
- added_column_count: `2`
- final_judge_call_count: `3`
- final_judge phase: `negative_feasibility_search`
- final_judge negative_column_count: `0`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `13.371009`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_merged_staged_resume/stage_003/probe.json`
- resume initial columns: `302`
- active columns saved: `304`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -0.002400875 | -0.002400778 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.004995927 | -0.179857996 |  |
| 3 | INCOMPLETE_LIMIT | 0 | None | None | negative_feasibility_search |
