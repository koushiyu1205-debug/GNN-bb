# Journey Branch Probe Training Readiness Audit

日期：2026-06-25

## 目的

汇总 child-probe / proof-cost proxy rows，判断是否足够先启动离线 branch/proof-head 训练。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不改变 official bound 或 certificate。

## 机器字段

```text
row_count = 801
probe_positive_count = 2
strict_uncensored_probe_positive_count = 2
probe_hard_negative_count = 429
probe_positive_context_count = 2
probe_hard_negative_context_count = 372
probe_instance_count = 27
probe_time_window_family_count = 3
family_counts = {'greedy-anchor': 313, 'random-wave': 162, 'sector-wave': 326}
probe_hard_negative_reason_counts = {'completion_bound_retry': 420, 'low_proxy_score': 429, 'negative_pricing_event': 427, 'right_censored_probe': 429, 'unstarted_child': 27}
min_started_child_count = 1
min_probe_positive_proxy_score = 0.0
max_hard_negative_proxy_score = -1.0
probe_debug_training_ready = False
probe_sanity_training_ready = False
probe_serious_training_ready = False
probe_debug_training_requirements = {'probe_branch_row_min': 100, 'probe_positive_min': 10, 'probe_hard_negative_min': 10, 'probe_positive_context_min': 2, 'probe_hard_negative_context_min': 2, 'probe_instance_min': 3}
probe_sanity_training_requirements = {'probe_branch_row_min': 500, 'probe_positive_min': 30, 'probe_hard_negative_min': 30, 'probe_positive_context_min': 6, 'probe_hard_negative_context_min': 6, 'probe_instance_min': 8, 'probe_time_window_family_min': 2}
probe_serious_training_requirements = {'probe_branch_row_min': 1000, 'probe_positive_min': 50, 'probe_hard_negative_min': 50, 'probe_positive_context_min': 10, 'probe_hard_negative_context_min': 10, 'probe_instance_min': 12, 'probe_time_window_family_min': 3}
remaining_for_probe_debug_training = {'probe_positive_min': 8}
remaining_for_probe_sanity_training = {'probe_positive_min': 28, 'probe_positive_context_min': 4}
remaining_for_probe_serious_training = {'probe_branch_row_min': 199, 'probe_positive_min': 48, 'probe_positive_context_min': 8}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
proxy_only = True
production_ready = False
optin_training_ready = False
```

## 解释

- `probe_positive` 来自 child-probe proxy 的 promotion-ready 分支行；它可以训练排序/调度头，但不等价于整局 target-200 strong positive。
- `probe_hard_negative` 是带有明显 proxy 失败信号的分支行，例如低 proxy score、右删失、completion-bound retry、negative pricing event 或 child 未启动。
- `probe_debug_training_ready=true` 只表示可以先跑离线数据加载、loss、checkpoint 和排序 sanity，不允许 production opt-in。
- `probe_sanity_training_ready=true` 接近“可以开始一次像样的 probe 级离线训练”；production/opt-in 仍必须回到 strict full-replay 与 target-200 readiness。

## 当前判断

probe 级数据连 debug 训练都偏薄，应继续补 top200 child-probe contexts。
probe 级数据还不足以支撑稳定试训，主要缺口见 remaining_for_probe_sanity_training。
无论 readiness 是否为 true，这份审计都不授权把 proxy score map 接入 production opt-in。
