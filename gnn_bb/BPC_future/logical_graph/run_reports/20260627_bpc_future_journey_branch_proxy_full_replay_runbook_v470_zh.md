# Journey Branch Proxy Full-Replay Runbook

日期：2026-06-27

## 目的

从 child-probe proxy branch rows 选择 root forced-pair，生成 full replay 命令。该脚本只生成命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
commands_path = BPC_future/results/journey_branch_proxy_full_replay_runbook_v470_v469_proxy_top12_20260627/commands.sh
raw_proxy_row_count = 224
candidate_row_count = 26
entry_count = 10
time_limit = 600
max_per_instance = 1
min_proxy_score = -7.5
min_fathom_count = None
min_corrected_bound_gain = 7.0
max_completion_bound_retry_count = None
max_negative_pricing_event_count = None
require_label_observation_complete = false
require_promotion_ready = false
candidate_log_top_n = 200
skipped_non_root_depth = 104
skipped_score_threshold = 94
skipped_fathom_threshold = 0
skipped_corrected_gain_threshold = 0
skipped_completion_retry_threshold = 0
skipped_negative_pricing_threshold = 0
skipped_incomplete_label = 0
skipped_promotion_unready = 0
skipped_max_per_instance = 16
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## Entries

- 001_proxy_full_replay_8_15_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph: pair=[8, 15], proxy_score=-3.195011475, instance=BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
- 002_proxy_full_replay_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph: pair=[2, 16], proxy_score=-4.179975525, instance=BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
- 003_proxy_full_replay_8_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph: pair=[8, 16], proxy_score=-4.19918355, instance=BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
- 004_proxy_full_replay_10_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph: pair=[10, 18], proxy_score=-4.965127342, instance=BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
- 005_proxy_full_replay_10_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph: pair=[10, 19], proxy_score=-6.249560797, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
- 006_proxy_full_replay_7_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph: pair=[7, 10], proxy_score=-6.781795006, instance=BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
- 007_proxy_full_replay_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph: pair=[5, 8], proxy_score=-6.96891255, instance=BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
- 008_proxy_full_replay_5_7_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph: pair=[5, 7], proxy_score=-7.124868233, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
- 009_proxy_full_replay_9_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph: pair=[9, 10], proxy_score=-7.1379989, instance=BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
- 010_proxy_full_replay_2_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph: pair=[2, 5], proxy_score=-7.335323158, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json

## 边界

这些命令用于验证 proxy top pair 是否能在 full replay 中转成 target-200 positive 或 hard negative。执行结果必须再经过 branch-impact / counterfactual delta 审计，不能直接作为训练标签或 solver opt-in 证据。
