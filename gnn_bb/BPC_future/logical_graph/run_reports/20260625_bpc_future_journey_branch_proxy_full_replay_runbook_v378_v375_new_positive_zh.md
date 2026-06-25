# Journey Branch Proxy Full-Replay Runbook

日期：2026-06-25

## 目的

从 child-probe proxy branch rows 选择 root forced-pair，生成 full replay 命令。该脚本只生成命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
commands_path = BPC_future/results/journey_branch_proxy_full_replay_runbook_v378_v375_new_positive/commands.sh
raw_proxy_row_count = 226
candidate_row_count = 1
entry_count = 1
time_limit = 600
max_per_instance = 1
min_proxy_score = 0.0
min_fathom_count = 2.0
min_corrected_bound_gain = 5.0
max_completion_bound_retry_count = None
max_negative_pricing_event_count = None
require_label_observation_complete = true
require_promotion_ready = true
candidate_log_top_n = 200
skipped_non_root_depth = 88
skipped_score_threshold = 137
skipped_fathom_threshold = 0
skipped_corrected_gain_threshold = 0
skipped_completion_retry_threshold = 0
skipped_negative_pricing_threshold = 0
skipped_incomplete_label = 0
skipped_promotion_unready = 0
skipped_max_per_instance = 0
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## Entries

- 001_proxy_full_replay_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph: pair=[3, 10], proxy_score=8.119794042, instance=BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json

## 边界

这些命令用于验证 proxy top pair 是否能在 full replay 中转成 target-200 positive 或 hard negative。执行结果必须再经过 branch-impact / counterfactual delta 审计，不能直接作为训练标签或 solver opt-in 证据。
