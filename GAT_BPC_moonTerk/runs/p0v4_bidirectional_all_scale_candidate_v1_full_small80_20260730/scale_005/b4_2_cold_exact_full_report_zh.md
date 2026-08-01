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

- model: `P0V4_BIDIRECTIONAL_MIDPOINT_ALL_SCALE_CANDIDATE_V1_S5_native_rcspp_bidirectional_midpoint_hybrid_v1`
- config hash: `076dd3de641c2af4`
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
- root-pool post-final-judge selected/new/replacement/added: `360` / `340` / `20` / `360`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 20 | 20 | 20 | 0 | 0.44207 | 0.49835 | 0.119188 | None | 0.181261 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 5 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.449239 | 0.107937 | None | 0.192853 | 22 | 0 | 0 | 17 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.437633 | 0.110268 | None | 0.183446 | 22 | 0 | 0 | 17 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.446513 | 0.122066 | None | 0.183823 | 26 | 0 | 0 | 21 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.442541 | 0.123944 | None | 0.178899 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.432223 | 0.120953 | None | 0.171283 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.422331 | 0.097937 | None | 0.185737 | 24 | 0 | 0 | 19 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.454709 | 0.119484 | None | 0.193428 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.443577 | 0.130533 | None | 0.175511 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.425809 | 0.094815 | None | 0.187929 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.49835 | 0.15105 | None | 0.204968 | 29 | 0 | 0 | 24 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.438009 | 0.120529 | None | 0.176491 | 17 | 0 | 0 | 12 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.447323 | 0.135586 | None | 0.168615 | 24 | 0 | 0 | 19 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.439869 | 0.123623 | None | 0.177586 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.418151 | 0.105263 | None | 0.170996 | 24 | 0 | 0 | 19 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.456154 | 0.122143 | None | 0.192661 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.416902 | 0.110495 | None | 0.164699 | 21 | 0 | 0 | 16 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.404323 | 0.105679 | None | 0.160178 | 13 | 0 | 0 | 8 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.47274 | 0.148963 | None | 0.182363 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.45007 | 0.110315 | None | 0.197075 | 25 | 0 | 0 | 20 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 5 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.44494 | 0.122172 | None | 0.176679 | 27 | 0 | 0 | 22 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
