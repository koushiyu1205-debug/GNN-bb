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

- model: `P0V4_BIDIRECTIONAL_MIDPOINT_ALL_SCALE_CANDIDATE_V1_S10_native_rcspp_bidirectional_midpoint_hybrid_v1`
- config hash: `3ac585277f88de95`
- root engine: `b2b_r3_worker`
- worker pricer: `relaxed_labeling`, max task cap `10`
- labeling harvest: support-aware `True`, weak replacement cap `8`, support overlap `0.6`
- labeling support-continuation: enabled `True`, max seed sets `240`, max neighbors `4`, protected `8`
- large-task direct worker: enabled `False`, max tasks `12`, candidate sets `240`, time cap `25.0`
- labeling final judge: `on`, max exact tasks `10`, exact harvest target `16`
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
- root-pool post-final-judge selected/new/replacement/added: `1381` / `1371` / `10` / `1381`
- root-partition post-final feedback selected/added: `0` / `0`
- all redlines zero: `True`
- accepted: `False`

| scale | rows | exact | under300 exact | fail-closed | mean total | max total | mean root | mean partition | mean tree |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 20 | 20 | 20 | 0 | 1.199763 | 3.209719 | 0.722873 | None | 0.295513 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 10 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.638538 | 0.261465 | None | 0.20081 | 61 | 0 | 0 | 51 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.674204 | 0.275169 | None | 0.22422 | 60 | 0 | 0 | 48 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.829347 | 0.416704 | None | 0.227193 | 96 | 0 | 0 | 84 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.762833 | 0.357574 | None | 0.230099 | 60 | 0 | 0 | 48 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.671575 | 1.16012 | None | 0.331991 | 78 | 0 | 0 | 66 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.912012 | 0.508127 | None | 0.227065 | 86 | 0 | 0 | 74 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.13036 | 0.700713 | None | 0.251397 | 87 | 0 | 0 | 75 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.139697 | 0.722896 | None | 0.239715 | 94 | 0 | 0 | 82 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 2.012802 | 1.564725 | None | 0.267541 | 86 | 0 | 0 | 75 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.794942 | 1.298053 | None | 0.304928 | 108 | 0 | 0 | 96 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 3.209719 | 2.402804 | None | 0.623235 | 101 | 0 | 0 | 89 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.993136 | 0.567757 | None | 0.236688 | 102 | 0 | 0 | 90 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 2.573646 | 1.474546 | None | 0.920996 | 85 | 0 | 0 | 74 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.826279 | 0.419942 | None | 0.225213 | 72 | 0 | 0 | 61 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.956393 | 0.537011 | None | 0.242776 | 83 | 0 | 0 | 71 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.691784 | 0.297391 | None | 0.21297 | 92 | 0 | 0 | 82 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.703398 | 0.286077 | None | 0.217314 | 85 | 0 | 0 | 75 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.943345 | 0.511952 | None | 0.252154 | 44 | 0 | 0 | 32 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.74085 | 0.323678 | None | 0.23411 | 60 | 0 | 0 | 48 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.790404 | 0.370747 | None | 0.239847 | 71 | 0 | 0 | 60 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
