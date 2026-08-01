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

- model: `NATIVE_SPPRC_ACCEPTANCE_V1_S20_native_rcspp_inprocess`
- config hash: `402e71dc30170245`
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
- root-pool post-final-judge selected/new/replacement/added: `11377` / `11267` / `110` / `11377`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 20 | 20 | 20 | 0 | 31.324168 | 167.114766 | 19.795067 | None | 11.156695 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 20 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 5.671466 | 4.355804 | None | 0.967625 | 473 | 0 | 0 | 466 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 3.120355 | 2.072623 | None | 0.708068 | 427 | 0 | 0 | 405 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 6.003029 | 4.663565 | None | 0.954996 | 651 | 0 | 0 | 630 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 33.003907 | 4.718599 | None | 27.93507 | 500 | 0 | 0 | 494 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 48.240009 | 11.397411 | None | 36.471461 | 608 | 0 | 0 | 598 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 3.642105 | 2.583361 | None | 0.702628 | 455 | 0 | 0 | 433 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 3.317088 | 2.239909 | None | 0.735128 | 435 | 0 | 0 | 424 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 32.070316 | 26.365237 | None | 5.342459 | 521 | 0 | 0 | 500 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 68.651353 | 26.260237 | None | 42.04228 | 367 | 0 | 0 | 346 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 13.273883 | 10.511165 | None | 2.387651 | 613 | 0 | 0 | 590 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 100.714448 | 65.499535 | None | 34.865288 | 445 | 0 | 0 | 426 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 167.114766 | 133.035859 | None | 33.687291 | 712 | 0 | 0 | 702 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 64.91292 | 41.652647 | None | 22.863224 | 663 | 0 | 0 | 640 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 22.060656 | 17.3928 | None | 4.311801 | 486 | 0 | 0 | 463 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 8.806728 | 6.422801 | None | 1.986804 | 697 | 0 | 0 | 684 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 6.576239 | 5.068867 | None | 1.102544 | 719 | 0 | 0 | 696 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 13.688512 | 11.34501 | None | 1.897871 | 1072 | 0 | 0 | 1056 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 12.469878 | 10.485176 | None | 1.596431 | 726 | 0 | 0 | 710 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 7.176047 | 5.51139 | None | 1.287483 | 647 | 0 | 0 | 624 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 20 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 5.969649 | 4.319349 | None | 1.287803 | 510 | 0 | 0 | 490 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
