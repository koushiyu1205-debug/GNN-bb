# B4.2 Cold-Start Exact 300s Report

## 边界

- 正式行必须从 `instance_XXX_logical_graph.json` 冷启动。
- 禁止外部 mature probe、同实例历史列池、手工补列、按实例调参。
- 同一次 run 内 staged checkpoint 可以续跑，但所有 stage 时间计入 `cold_start_total_sec`。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。
- B4.2 V1 固定 seed 为 B0 incumbent + singleton，并启用固定 route-template pre-harvest worker；worker 只找列，不给 no-negative 证书。
- root pool 使用固定 `b2b_r3_worker`，默认 worker 为 `relaxed_labeling`；tail dual stabilization 只作用于 worker candidate search。
- final judge 使用 `labeling_final_judge=auto`：5/10 默认走 exact labeling proof，超过 fixed max exact tasks 时自动回到 compact/exhaustive proof。

## 汇总

- model: `B4_2_COLD_EXACT_V1`
- config hash: `f79997e4a2301127`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`
- labeling final judge: `auto`, max exact tasks `10`, exact harvest target `5`
- rows: `1`
- no-cheat fail: `0`
- worker certificate leaks: `0`
- tail-dual certificate leaks: `0`
- true-dual RC recompute missing: `0`
- root-pool worker/tail-dual/redline counts: `0` / `0` / `0`
- root-pool exact harvest candidates/selected/new/replacement: `0` / `0` / `0` / `0`
- root-pool worker selected/new/replacement: `0` / `0` / `0`
- root-pool post-final-judge selected/new/replacement/added: `0` / `0` / `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 1 | 0 | 0 | 1 | 91.094438 | 91.094438 | 54.367297 | 35.701771 | None |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 30 | instance_001 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 91.094438 | 54.367297 | 35.701771 | None | 265 | 0 | 0 | 0 | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | parallel partition gate did not satisfy official B4.2 criteria |
