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

- model: `NATIVE_LIVE_SRI_P0V3_MEMORY_COMPACT_CANDIDATE_V3_S5_native_rcspp_inprocess`
- config hash: `09f58e9678d38e09`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `5`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `5`, exact harvest target `8`
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
- root-pool post-final-judge selected/new/replacement/added: `353` / `333` / `20` / `353`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 20 | 20 | 20 | 0 | 0.539998 | 1.918633 | 0.185413 | None | 0.194529 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 5 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.918633 | 1.187199 | None | 0.250204 | 22 | 0 | 0 | 17 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.44589 | 0.122179 | None | 0.178743 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.491406 | 0.134029 | None | 0.206714 | 26 | 0 | 0 | 21 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.464001 | 0.137702 | None | 0.18438 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.471648 | 0.128565 | None | 0.196061 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.46265 | 0.12027 | None | 0.202847 | 24 | 0 | 0 | 19 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.430201 | 0.118491 | None | 0.173187 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.483622 | 0.155486 | None | 0.188816 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.445876 | 0.123543 | None | 0.181911 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.518828 | 0.17849 | None | 0.19994 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.452311 | 0.121392 | None | 0.189091 | 17 | 0 | 0 | 12 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.460545 | 0.119449 | None | 0.197941 | 24 | 0 | 0 | 19 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.451225 | 0.119352 | None | 0.192816 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.462203 | 0.143548 | None | 0.176753 | 24 | 0 | 0 | 19 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.454912 | 0.113454 | None | 0.192143 | 26 | 0 | 0 | 21 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.478054 | 0.14309 | None | 0.193132 | 22 | 0 | 0 | 17 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.469818 | 0.113026 | None | 0.208933 | 13 | 0 | 0 | 8 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.4993 | 0.167412 | None | 0.189037 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.467151 | 0.121771 | None | 0.19992 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.471683 | 0.139808 | None | 0.188011 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
