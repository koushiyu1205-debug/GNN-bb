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

- model: `P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE_S10_native_rcspp_bidirectional_root_partial_hybrid_v3`
- config hash: `c67a67196d062aeb`
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
| 10 | 20 | 20 | 20 | 0 | 1.189818 | 3.159665 | 0.716734 | None | 0.286515 |

## Per-Instance

| scale | instance | status | scope | pricing | exact | under300 | total | root | partition | tree | active cols | exact harvest | worker harvest | post-FJ added | post-partition added | terminal | provenance | fail reason |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 10 | instance_001 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.657583 | 0.256038 | None | 0.217778 | 61 | 0 | 0 | 51 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_002 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.685822 | 0.289571 | None | 0.216421 | 60 | 0 | 0 | 48 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_003 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.822262 | 0.411086 | None | 0.225172 | 96 | 0 | 0 | 84 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_004 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.759343 | 0.345508 | None | 0.228864 | 60 | 0 | 0 | 48 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_005 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.674964 | 1.138931 | None | 0.344943 | 78 | 0 | 0 | 66 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_006 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.934745 | 0.49375 | None | 0.259368 | 86 | 0 | 0 | 74 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_007 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.146546 | 0.690633 | None | 0.271887 | 87 | 0 | 0 | 75 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_008 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.184177 | 0.739886 | None | 0.259416 | 94 | 0 | 0 | 82 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_009 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 2.00991 | 1.509759 | None | 0.311543 | 86 | 0 | 0 | 75 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_010 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.804447 | 1.282031 | None | 0.329833 | 108 | 0 | 0 | 96 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_011 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 3.159665 | 2.31686 | None | 0.6525 | 101 | 0 | 0 | 89 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_012 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 1.039347 | 0.592885 | None | 0.258695 | 102 | 0 | 0 | 90 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_013 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 2.10047 | 1.467045 | None | 0.446537 | 85 | 0 | 0 | 74 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_014 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.862013 | 0.423713 | None | 0.248648 | 72 | 0 | 0 | 61 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_015 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.981696 | 0.546537 | None | 0.253564 | 83 | 0 | 0 | 71 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_016 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.715147 | 0.30359 | None | 0.222448 | 92 | 0 | 0 | 82 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_017 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.677253 | 0.275563 | None | 0.212259 | 85 | 0 | 0 | 75 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_018 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.986336 | 0.53281 | None | 0.266655 | 44 | 0 | 0 | 32 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_019 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.774654 | 0.325219 | None | 0.26557 | 60 | 0 | 0 | 48 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
| 10 | instance_020 | BPC_OPTIMAL | BPC_TREE_OPTIMAL | CERTIFIED_NO_NEGATIVE | True | True | 0.819978 | 0.393259 | None | 0.238208 | 71 | 0 | 0 | 60 | 0 | True | instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback |  |
