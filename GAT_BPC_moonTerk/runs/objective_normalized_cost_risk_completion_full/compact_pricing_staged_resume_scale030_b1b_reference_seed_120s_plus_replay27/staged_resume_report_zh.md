# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/compact_pricing_staged_resume_scale030_b1b_reference_seed_120s_plus_replay27/stage_001/probe.json`
- stage_count: `1`

| stage | batch | round cap | resume cols | active cols | added | rounds | state | scope | best RC | elapsed s |
|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|
| 1 | 10 | 4 | 189 | 191 | 2 | 3 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.090512962 | 893.568058 |
