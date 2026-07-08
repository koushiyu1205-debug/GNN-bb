# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `281.660664` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `1`
- added_column_count: `1`
- final_judge_call_count: `1`
- final_judge phase: `optimization_proof`
- final_judge negative_column_count: `1`
- compact batch found count: `None`
- compact batch search calls: `None`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.471208376`
- final_judge_wall_time: `281.633462`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/compact_pricing_staged_resume_scale030_b1b_reference_seed_120s/stage_014/probe.json`
- resume initial columns: `87`
- active columns saved: `88`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -0.471208376 | -1.214487284 | optimization_proof |
