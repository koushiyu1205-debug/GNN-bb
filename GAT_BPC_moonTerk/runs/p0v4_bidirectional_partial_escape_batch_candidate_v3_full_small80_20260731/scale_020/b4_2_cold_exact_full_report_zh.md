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

- model: `P0V4_BIDIRECTIONAL_PARTIAL_ESCAPE_BATCH_ALL_SCALE_CANDIDATE_V3_S20_native_rcspp_bidirectional_midpoint_partial_hybrid_v2`
- config hash: `98eaba3e82596d2b`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `20`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `20`, exact harvest target `32`
- rows: `20`
- no-cheat fail: `0`
- worker certificate leaks: `0`
- tail-dual certificate leaks: `0`
- true-dual RC recompute missing: `0`
- root-pool worker/tail-dual/redline counts: `0` / `0` / `0`
- root-pool support-continuation seeds/active/protected/leaks: `0` / `0` / `0` / `0`
- root-pool large-task direct worker seeds/rounds/columns/true-negatives/leaks: `0` / `0` / `0` / `0` / `0`
- root-pool exact harvest candidates/selected/new/replacement: `0` / `0` / `0` / `0`
- root-pool worker selected/new/replacement: `0` / `0` / `0`
- root-pool post-final-judge selected/new/replacement/added: `8200` / `8190` / `10` / `8200`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 20 | 20 | 20 | 0 | 20.102168 | 93.203409 | 10.272242 | None | 9.467016 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 20 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 6.752113 | 5.439122 | None | 0.975186 | 415 | 0 | 0 | 392 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.968253 | 0.927516 | None | 0.701283 | 375 | 0 | 0 | 352 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 3.248529 | 1.961551 | None | 0.930001 | 500 | 0 | 0 | 479 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 31.301067 | 2.728655 | None | 28.034172 | 375 | 0 | 0 | 352 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 26.248766 | 5.157238 | None | 20.740422 | 430 | 0 | 0 | 407 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.937526 | 0.888073 | None | 0.710515 | 314 | 0 | 0 | 291 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 2.228628 | 1.153761 | None | 0.746616 | 261 | 0 | 0 | 240 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 35.735 | 28.927394 | None | 6.452375 | 473 | 0 | 0 | 450 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 30.429319 | 9.620911 | None | 20.467582 | 368 | 0 | 0 | 347 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 5.991043 | 3.225719 | None | 2.398855 | 537 | 0 | 0 | 514 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 68.972743 | 34.733112 | None | 33.894016 | 360 | 0 | 0 | 338 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 93.203409 | 57.498054 | None | 35.328426 | 569 | 0 | 0 | 546 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 49.466262 | 24.618738 | None | 24.505712 | 310 | 0 | 0 | 287 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 14.314941 | 9.207415 | None | 4.771175 | 309 | 0 | 0 | 286 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 5.004711 | 2.674794 | None | 1.952539 | 482 | 0 | 0 | 459 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 4.000433 | 2.544647 | None | 1.074047 | 615 | 0 | 0 | 593 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 8.997345 | 6.900766 | None | 1.695652 | 752 | 0 | 0 | 729 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 5.173544 | 3.262918 | None | 1.564048 | 472 | 0 | 0 | 449 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 3.794607 | 2.327671 | None | 1.121002 | 378 | 0 | 0 | 355 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 3.275128 | 1.646791 | None | 1.276703 | 355 | 0 | 0 | 334 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
