# Journey Branch Proxy Full-Replay Runbook

日期：2026-06-25

## 目的

从 child-probe proxy branch rows 选择 root forced-pair，生成 full replay 命令。该脚本只生成命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
commands_path = BPC_future/results/journey_branch_proxy_full_replay_runbook_v299_v298_seed61103_top2_600/commands.sh
raw_proxy_row_count = 11
candidate_row_count = 4
entry_count = 2
time_limit = 600
max_per_instance = 2
candidate_log_top_n = 200
skipped_non_root_depth = 7
skipped_max_per_instance = 0
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## Entries

- 001_proxy_full_replay_10_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph: pair=[10, 19], proxy_score=-6.667612505, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json
- 002_proxy_full_replay_1_5_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph: pair=[1, 5], proxy_score=-7.69520995, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json

## 边界

这些命令用于验证 proxy top pair 是否能在 full replay 中转成 target-200 positive 或 hard negative。执行结果必须再经过 branch-impact / counterfactual delta 审计，不能直接作为训练标签或 solver opt-in 证据。
