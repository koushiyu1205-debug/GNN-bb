# B4.2 Cold-Start Exact 300s Report

## 边界

- 正式行必须从 `instance_XXX_logical_graph.json` 冷启动。
- 禁止外部 mature probe、同实例历史列池、手工补列、按实例调参。
- 同一次 run 内 staged checkpoint 可以续跑，但所有 stage 时间计入 `cold_start_total_sec`。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective，不证明 makespan-in-objective。
- B4.2 V1 固定 seed 为 B0 incumbent + singleton，并启用固定 route-template pre-harvest worker；worker 只找列，不给 no-negative 证书。
- root pool 使用固定 `b2b_r3_worker`，默认 worker 为 `relaxed_labeling`；fixed worker max task cap 是全局 config/hash 字段，不允许按实例调参。
- tail dual stabilization 只作用于 worker candidate search。
- support-continuation seed 只基于当前 RMP support 自动生成 add/drop/swap 邻域列；只找列，不给 no-negative 证书。
- final judge 使用 `labeling_final_judge=auto`：5/10 默认走 exact labeling proof，超过 fixed max exact tasks 时自动回到 compact/exhaustive proof。

## 汇总

- model: `P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE_S50_native_rcspp_bidirectional_root_partial_hybrid_v3`
- config hash: `2cad104170e715a6`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `50`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `50`, exact harvest target `128`
- rows: `19`
- no-cheat fail: `0`
- worker certificate leaks: `0`
- tail-dual certificate leaks: `0`
- true-dual RC recompute missing: `0`
- root-pool worker/tail-dual/redline counts: `0` / `0` / `0`
- root-pool support-continuation seeds/active/protected/leaks: `0` / `0` / `0` / `0`
- root-pool large-task direct worker seeds/rounds/columns/true-negatives/leaks: `0` / `0` / `0` / `0` / `0`
- root-pool exact harvest candidates/selected/new/replacement: `0` / `0` / `0` / `0`
- root-pool worker selected/new/replacement: `0` / `0` / `0`
- root-pool post-final-judge selected/new/replacement/added: `123773` / `123771` / `2` / `123773`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 19 | 14 | 3 | 5 | 1320.366814 | 3605.752605 | 908.626936 | None | 457.142813 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 50 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 461.654479 | 315.716546 | None | 142.878596 | 7641 | 0 | 0 | 7586 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 286.143112 | 232.597785 | None | 50.687261 | 6944 | 0 | 0 | 6889 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 215.726727 | 191.350815 | None | 21.944398 | 5336 | 0 | 0 | 5281 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 995.274358 | 644.563916 | None | 348.665111 | 3729 | 0 | 0 | 3674 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 258.450223 | 222.636525 | None | 33.052098 | 6583 | 0 | 0 | 6528 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 444.221861 | 398.670935 | None | 42.448069 | 8173 | 0 | 0 | 8118 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_008 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 2709.370656 | 1381.25386 | None | 1325.683248 | 5466 | 0 | 0 | 5411 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | tree closure did not produce BPC_TREE_OPTIMAL |
| 50 | instance_009 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 1374.324974 | 1372.212835 | None | None | 5788 | 0 | 0 | 5733 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 1682.032236 | 923.392689 | None | 756.102224 | 6071 | 0 | 0 | 6016 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 1460.672683 | 1221.034482 | None | 236.837656 | 7005 | 0 | 0 | 6950 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 3310.865551 | 2992.076973 | None | 315.691557 | 8595 | 0 | 0 | 8540 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_013 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 3604.158503 | 3187.788431 | None | 413.928515 | 5611 | 0 | 0 | 5556 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | tree closure did not produce BPC_TREE_OPTIMAL |
| 50 | instance_014 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 1534.572321 | 1532.536308 | None | None | 5073 | 0 | 0 | 5020 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 50 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 425.374146 | 381.28487 | None | 41.394907 | 6234 | 0 | 0 | 6179 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 469.028863 | 441.69099 | None | 23.916807 | 8327 | 0 | 0 | 8272 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 954.843056 | 274.574887 | None | 677.488017 | 6385 | 0 | 0 | 6330 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 573.526366 | 512.099454 | None | 57.967709 | 9137 | 0 | 0 | 9082 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 50 | instance_019 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 3605.752605 | 859.518709 | None | 2743.170644 | 7411 | 0 | 0 | 7356 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | tree closure subprocess reached its inherited row deadline; partial proof state was discarded and no certificate was issued |
| 50 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | False | 720.976754 | 178.910766 | None | 539.571006 | 5307 | 0 | 0 | 5252 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
