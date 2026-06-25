# Journey Branch Holdout Sampling Plan

日期：2026-06-25

该计划只读 benchmark / label / log 文件，生成下一批 holdout-oriented 采样建议；不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## Machine Fields

```text
candidate_context_count = 40
actionable_context_count = 2
selected_context_count = 2
known_strict_positive_instance_count = 4
known_strict_positive_family_count = 2
known_target200_positive_instance_count = 3
known_target200_positive_family_count = 2
candidate_log_top_n = 200
selected_action_counts = {'BUILD_CHILD_PROBE_RUNBOOK': 2}
all_action_counts = {'BUILD_CHILD_PROBE_RUNBOOK': 2, 'ALREADY_HAS_TARGET200_POSITIVE': 3, 'DEFER_NONOPTIMAL_CONTEXT': 34, 'ROUTE_TO_ROOT_PRICING_TAIL': 1}
official_bound_effect = false
certificate_effect = false
```

## Rows

- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=143.785261, wall=522.147389, nodes=51, family=sector-wave, seed=61821, known_strict=True, known_target200=False, candidates=25, branch_events=25, cg_before_branch=19, probe_cg=27, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=139.76798, wall=287.679798, nodes=7, family=sector-wave, seed=61308, known_strict=False, known_target200=False, candidates=1, branch_events=1, cg_before_branch=28, probe_cg=36, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json

## 边界

该计划用于减少盲扫；只有已产生 target-200 positive 的实例会被视为覆盖完成，普通 strict positive 但未进入 200 秒的实例仍会继续采样。推荐命令仍需实际运行并通过 strict counterfactual delta 才能产生训练正例。
`ROUTE_TO_ROOT_PRICING_TAIL` / `ROUTE_TO_PRICING_TAIL` 表示已有日志显示没有可采 branch event，该实例应转到 pricing/final-probe/Tail Action Controller 线，不应继续生成 branch-pair replay。
