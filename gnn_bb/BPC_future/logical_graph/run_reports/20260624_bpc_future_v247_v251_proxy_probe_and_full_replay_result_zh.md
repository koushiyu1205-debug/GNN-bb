# V247-V251 Proxy Probe 与 Full Replay 结果

日期：2026-06-24

## 目的

执行 V247 root child-probe，审计 V248 branch impact，生成 V249 proxy ranking，再用 V250 对每个 random-wave context 的 top proxy pair 做 full replay 验证。本轮所有操作均为诊断/采样；GAT 分支策略没有接入默认求解，official bound 和 certificate 仍只来自 exact-safe 逻辑。

## V247 Child-Probe

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624
entry_count = 50
parallelism = 4
time_limit = 120
probe_max_nodes = 3
probe_max_cg_iterations = 20

status_counts = {
  'TIME_LIMIT': 38,
  'EXTERNAL_TIME_LIMIT': 12
}
```

V247 没有产生 strict positive。它只提供 child-bound/proof-cost proxy。

## V248 Branch-Impact Audit

```text
output = BPC_future/results/journey_branch_impact_audit_v248_v247_root_child_probe
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_audit_v248_v247_root_child_probe_zh.md

log_count = 50
branch_count = 84
branch_training_row_count = 84
child_probe_row_count = 168
forced_pair_branch_count = 38
forced_pair_matched_branch_count = 38
right_censored_branch_count = 84
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
max_child_corrected_bound_gain = 28.061849
```

解释：所有 branch-impact row 都是 right-censored，不能作为正式 branch-impact 训练标签。

## V249 Proxy Ranking

```text
output = BPC_future/results/journey_branch_child_probe_proxy_ranking_v249_v248_root_child_probe
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_child_probe_proxy_ranking_v249_v248_root_child_probe_zh.md

proxy_branch_row_count = 38
proxy_context_count = 7
proxy_ranking_pair_count = 63
right_censored_proxy_ranking_pair_count = 63
sampling_navigation_ready = true
ranking_training_ready = false
```

Top proxy candidates included:

```text
random-wave/apollo seed61408: [5,13]
random-wave/apollo seed61000: [3,17]
random-wave/tranquillitatis seed61001: [13,16]
random-wave/tranquillitatis seed61309: [2,5]
random-wave/tranquillitatis seed61411: [2,4]
random-wave/apollo seed61919: [14,20]
random-wave/tranquillitatis seed61717: [4,11]
```

## V250 Full Replay

新增可复用 runbook builder：

```text
script = BPC_future/scripts/build_journey_branch_proxy_full_replay_runbook.py
test = BPC_future/tests/test_journey_branch_proxy_full_replay_runbook.py
```

V250 runbook：

```text
output = BPC_future/results/journey_branch_proxy_full_replay_runbook_v250_v249_top_proxy_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_proxy_full_replay_runbook_v250_v249_top_proxy_zh.md
entry_count = 7
time_limit = 260
max_per_instance = 1

status_counts = {
  'EXTERNAL_TIME_LIMIT': 7
}
```

逐项结果：

```text
random-wave/apollo seed61408 [5,13] -> EXTERNAL_TIME_LIMIT, wall=260.017053
random-wave/apollo seed61000 [3,17] -> EXTERNAL_TIME_LIMIT, wall=260.018520
random-wave/tranquillitatis seed61001 [13,16] -> EXTERNAL_TIME_LIMIT, wall=260.016390
random-wave/tranquillitatis seed61309 [2,5] -> EXTERNAL_TIME_LIMIT, wall=260.018508
random-wave/tranquillitatis seed61411 [2,4] -> EXTERNAL_TIME_LIMIT, wall=260.016346
random-wave/apollo seed61919 [14,20] -> EXTERNAL_TIME_LIMIT, wall=260.018708
random-wave/tranquillitatis seed61717 [4,11] -> EXTERNAL_TIME_LIMIT, wall=260.016765
```

## V251 Full-Replay Audit

```text
output = BPC_future/results/journey_branch_impact_audit_v251_v250_top_proxy_full_replay
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_audit_v251_v250_top_proxy_full_replay_zh.md

branch_count = 63
forced_pair_branch_count = 7
forced_pair_matched_branch_count = 7
right_censored_branch_count = 63
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
```

## 结论

V247/V249 proxy 对采样导航有用，但本轮 V250 没有把 random-wave family 的 top proxy pair 转成 target-200 positive，也没有产生 strict hard negative。当前可训练 strict 数据量不变：

```text
target_200_positive = 6
serious_training_ready = false
optin_training_ready = false
```

后续不能把 child-probe proxy 直接转 score map。random-wave 需要更强的采样策略或先改善算法结构；否则只会继续得到大量 right-censored 样本。
