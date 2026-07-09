# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_merged_staged_resume/stage_004/probe.json`
- stage_count: `4`

| stage | batch | round cap | resume cols | active cols | added | rounds | state | scope | best RC | elapsed s |
|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|
| 1 | 5 | 4 | 298 | 300 | 2 | 3 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.005703396 | 595.500219 |
| 2 | 5 | 4 | 300 | 301 | 1 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.006394256 | 592.348639 |
| 3 | 5 | 4 | 301 | 302 | 1 | 2 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.006368 | 587.023451 |
| 4 | 5 | 4 | 302 | 304 | 2 | 3 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.004995927 | 601.887824 |
