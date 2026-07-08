# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `286.933474` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `1`
- added_column_count: `5`
- final_judge_call_count: `1`
- final_judge phase: `negative_feasibility_batch`
- final_judge negative_column_count: `5`
- compact batch found count: `5`
- compact batch search calls: `5`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.423840484`
- final_judge_wall_time: `286.89477`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/compact_pricing_staged_resume_scale030_b1b_reference_seed_120s/stage_018/probe.json`
- resume initial columns: `103`
- active columns saved: `108`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 5 | -0.423840484 | -1.645937208 | negative_feasibility_batch |
