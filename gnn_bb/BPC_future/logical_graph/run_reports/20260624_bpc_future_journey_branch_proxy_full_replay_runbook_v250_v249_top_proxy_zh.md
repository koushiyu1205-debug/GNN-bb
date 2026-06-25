# Journey Branch Proxy Full-Replay Runbook

日期：2026-06-24

## 目的

从 child-probe proxy branch rows 选择 root forced-pair，生成 full replay 命令。该脚本只生成命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
commands_path = BPC_future/results/journey_branch_proxy_full_replay_runbook_v250_v249_top_proxy_20260624/commands.sh
raw_proxy_row_count = 67
candidate_row_count = 38
entry_count = 7
time_limit = 260
max_per_instance = 1
candidate_log_top_n = 200
skipped_non_root_depth = 29
skipped_max_per_instance = 31
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## Entries

- 001_proxy_full_replay_5_13_apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph: pair=[5, 13], proxy_score=-3.008555542, instance=BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json
- 002_proxy_full_replay_3_17_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph: pair=[3, 17], proxy_score=-5.406248167, instance=BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json
- 003_proxy_full_replay_13_16_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph: pair=[13, 16], proxy_score=-7.30457975, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
- 004_proxy_full_replay_2_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph: pair=[2, 5], proxy_score=-7.33900955, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json
- 005_proxy_full_replay_2_4_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph: pair=[2, 4], proxy_score=-7.544893217, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json
- 006_proxy_full_replay_14_20_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph: pair=[14, 20], proxy_score=-8.363341125, instance=BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json
- 007_proxy_full_replay_4_11_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph: pair=[4, 11], proxy_score=-9.315240467, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json

## 边界

这些命令用于验证 proxy top pair 是否能在 full replay 中转成 target-200 positive 或 hard negative。执行结果必须再经过 branch-impact / counterfactual delta 审计，不能直接作为训练标签或 solver opt-in 证据。
