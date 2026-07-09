# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `595.500219` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `3`
- added_column_count: `2`
- final_judge_call_count: `3`
- final_judge phase: `optimization_proof`
- final_judge negative_column_count: `0`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `0.035646975`
- final_judge_wall_time: `124.430481`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_replay_merge/plus57_stage001_round3_v4_merged_probe.json`
- resume initial columns: `298`
- active columns saved: `300`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -0.004483331 | -0.004483238 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.005703396 | -0.578392616 |  |
| 3 | INCOMPLETE_LIMIT | 0 | 0.035646975 | -0.192496096 | optimization_proof |
