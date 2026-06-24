# V166 Tail Action before-final-probe opt-in 探针

## 目的

V165 只证明 `profile_exhausted_no_column` final-probe funnel 里存在大量 D 类 early-branch 建议，但行为门关闭时不会运行 depth / width / branch-candidate guard。V166 在同一批 canonical random-TW 20 高 retry 实例上打开受控 opt-in，验证该策略是否实际减少 220s timeout。

## 配置

输入实例与 V165 相同：

- `tasks_020/sector-wave/tranquillitatis_balmer_like_20km/..._08_seed61718_logical_graph.json`
- `tasks_020/random-wave/tranquillitatis_balmer_like_20km/..._05_seed61411_logical_graph.json`
- `tasks_020/random-wave/tranquillitatis_balmer_like_20km/..._01_seed61001_logical_graph.json`

关键 opt-in：

```text
journey_tail_action_audit_enabled=True
journey_tail_action_no_column_early_branch_enabled=True
journey_tail_action_no_column_early_branch_before_final_probe_enabled=True
journey_tail_action_no_column_early_branch_allow_incomplete_limit_before_final_probe=True
journey_tail_action_no_column_early_branch_min_tasks=20
journey_tail_action_no_column_early_branch_min_depth=1
journey_tail_action_no_column_early_branch_max_depth=4
journey_tail_action_no_column_early_branch_require_complete_productivity_signals=False
journey_tail_action_no_column_early_branch_max_pool_child_width=180
journey_tail_action_no_column_early_branch_max_pool_total_child_width=360
journey_tail_action_no_column_early_branch_max_pool_balance_gap=180
```

输出：

```text
results = BPC_future/results/20260624_v166_tail_action_before_final_probe_optin_probe3_220.csv
logs    = BPC_future/results/logs_20260624_v166_tail_action_before_final_probe_optin_probe3_220
audit   = BPC_future/results/journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_20260624
report  = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_zh.md
```

## 结果

三例均为 `EXTERNAL_TIME_LIMIT`，220s 内没有求到最优。

审计摘要：

```text
tail_action rows = 155
EARLY_BRANCH = 86
CONTINUE_COLUMN_GENERATION = 44
BROAD_PLATEAU_FALLBACK = 25
early_branch_trigger = 20
tail_action_no_column_early_branch_trigger = 20
queued child = 40
non-exact queued child = 40
no-column gate rows = 46
no-column gate D rows = 32
```

gate 阻塞原因：

```text
width_guard_pool_child_width_exceeds_cap = 23
tail_action_not_early_branch = 14
depth_above_max = 6
depth_below_min = 3
```

按实例拆分：

```text
seed61718 sector-wave:
  triggers = 20
  exact_completion_bound_retry: V165 22 -> V166 8
  exact pricing rows:          V165 33 -> V166 46
  status: EXTERNAL_TIME_LIMIT

seed61001 random-wave:
  triggers = 0
  main blocker: pool child width exceeds cap
  exact_completion_bound_retry: V165 16 -> V166 18
  status: EXTERNAL_TIME_LIMIT

seed61411 random-wave:
  triggers = 0
  main blocker: pool child width exceeds cap / depth cap
  exact_completion_bound_retry: V165 17 -> V166 17
  status: EXTERNAL_TIME_LIMIT
```

## 判断

V166 证明 before-final-probe D 类 no-column early branch 的代码路径能真实触发，并且在 sector-wave 上确实减少了局部 completion-bound retry。但它没有带来整体加速：sector-wave 把 retry 成本转成了更大的 child subtree proof cost，两个 random-wave 又被 width guard 挡住而基本没有行为收益。

因此该 opt-in 不能扩大到 canonical 60-instance，也不能作为 20规模 200s 达标证据。下一步不能继续单独放宽 no-column early branch；需要把它和 branch pair / child ordering / child proof-cost 选择绑定，或者先改善 incumbent、cuts/formulation，使 D 类分支后的子节点更快闭合。

## 训练行沉淀

已把 V166 审计目录转成 tail-impact training rows：

```text
output = BPC_future/results/journey_tail_impact_training_rows_v166_tail_action_before_final_probe_optin_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_impact_training_rows_v166_tail_action_before_final_probe_optin_zh.md
```

摘要：

```text
training_row_count = 20
source_counts = {'tail_action_proof_cost': 20}
tail_class_counts = {'tail_action_no_column': 20}
y_tail_risk = 20
y_useful_tail_reduction = 0
y_child_negative_pricing_events = 12
y_child_completion_bound_retries = 7
y_child_early_branch_triggers = 10
y_subtree_no_column_chain = 10
production_ready = false
contrastive_tail_training_ready = false
hard_negative_catalog_ready = true
```

解释：这些行可以作为 GAT tail-risk / branch-impact 的 hard-negative catalog，帮助模型学会“某些 D 类 early branch 只是把 proof tail 推到 child subtree”。它们不能作为 useful-tail-reduction 正例，也不能作为 production branch/tail policy 的训练闭环。
