# Journey Branch Target-200 Sampling Plan

日期：2026-06-25

## 目的

按 V244 readiness 缺口为 branch/action GAT 选择下一批 target-200 正例采样 context。该计划只生成命令，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
raw_result_count = 60
all_context_count = 60
actionable_context_count = 0
selected_context_count = 0
target_wall = 200.0
near_wall = 360.0
known_target200_instance_count = 3
known_target200_family_count = 2
known_target200_families = ['greedy-anchor', 'sector-wave']
known_target200_terrain_count = 2
attempted_context_count = 10
all_action_counts = {'DEFER_HARD_TIMEOUT_CONTEXT': 23, 'ROUTE_TO_ROOT_PRICING_TAIL': 4, 'SKIP_ALREADY_ATTEMPTED_CONTEXT': 10, 'SKIP_ALREADY_WITHIN_TARGET': 20, 'SKIP_KNOWN_TARGET200_INSTANCE': 3}
selected_action_counts = {}
selected_family_counts = {}
commands_path = BPC_future/results/journey_branch_target200_sampling_plan_v301_full600_v252_attempted_v300_20260625/commands.sh
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
```

## 推荐 context


## 边界

推荐 context 只是采样入口；只有后续 child-probe / full replay / counterfactual delta 闭环后，才能产生 target-200 positive 或 hard negative 训练标签。
`ROUTE_TO_ROOT_PRICING_TAIL` / `ROUTE_TO_PRICING_TAIL` 表示已有 top200 日志没有 branch event，该实例不应继续占用 branch-pair 采样预算。
