# B4.2 Cold-Start Exact 500s Report

## 边界

- 正式行必须从 `instance_XXX_logical_graph.json` 冷启动。
- 禁止外部 mature probe、同实例历史列池、手工补列、按实例调参。
- 同一次 run 内 staged checkpoint 可以续跑，但所有 stage 时间计入 `cold_start_total_sec`。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。
- B4.2 V1 固定 seed 为 B0 incumbent + singleton，并启用固定 route-template pre-harvest worker；worker 只找列，不给 no-negative 证书。

## 汇总

- model: `B4_2_COLD_EXACT_V1`
- config hash: `065144647562266b`
- rows: `1`
- no-cheat fail: `0`
- accepted: `False`

| scale | rows | exact | under500 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 1 | 0 | 0 | 1 | 95.110398 | 95.110398 | 54.654009 | 39.746138 | None |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under500 | total | root | partition | tree | active cols | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 30 | instance_001 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 95.110398 | 54.654009 | 39.746138 | None | 148 | instance_json_fixed_seed_and_same_run_checkpoints | parallel partition gate did not satisfy official B4.2 criteria |
