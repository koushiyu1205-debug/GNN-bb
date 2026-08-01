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
- config hash: `afb921ac43b6e9e1`
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
| 20 | 20 | 0 | 0 | 20 | 20.859533 | 134.90129 | 20.515919 | None | None |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 20 | instance_001 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 4.791823 | 4.462648 | None | None | 473 | 0 | 0 | 466 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_002 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 2.440582 | 2.124422 | None | None | 427 | 0 | 0 | 405 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_003 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 5.238956 | 4.890085 | None | None | 651 | 0 | 0 | 630 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_004 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 5.281048 | 4.950382 | None | None | 500 | 0 | 0 | 494 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_005 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 13.037298 | 12.69268 | None | None | 608 | 0 | 0 | 598 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_006 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 2.962767 | 2.632685 | None | None | 455 | 0 | 0 | 433 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_007 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 2.78999 | 2.467162 | None | None | 435 | 0 | 0 | 424 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_008 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 29.506539 | 29.155842 | None | None | 521 | 0 | 0 | 500 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_009 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 28.02129 | 27.705134 | None | None | 367 | 0 | 0 | 346 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_010 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 12.398532 | 12.053964 | None | None | 613 | 0 | 0 | 590 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_011 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 66.729303 | 66.402993 | None | None | 445 | 0 | 0 | 426 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_012 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 134.90129 | 134.539186 | None | None | 712 | 0 | 0 | 702 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_013 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 41.873776 | 41.515927 | None | None | 663 | 0 | 0 | 640 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_014 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 20.962701 | 20.625112 | None | None | 486 | 0 | 0 | 463 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_015 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 7.061427 | 6.70605 | None | None | 697 | 0 | 0 | 684 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_016 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 5.561545 | 5.212874 | None | None | 719 | 0 | 0 | 696 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_017 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 11.88449 | 11.491666 | None | None | 1072 | 0 | 0 | 1056 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_018 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 10.737269 | 10.380442 | None | None | 726 | 0 | 0 | 710 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_019 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 6.023322 | 5.667343 | None | None | 647 | 0 | 0 | 624 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
| 20 | instance_020 | BPC_INCOMPLETE_PRICING | DIAGNOSTIC_PRICING_FRONTIER | INCOMPLETE_LIMIT | False | False | 4.986706 | 4.641776 | None | None | 510 | 0 | 0 | 490 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback | root pool did not certify no-negative within cold-start row limit |
