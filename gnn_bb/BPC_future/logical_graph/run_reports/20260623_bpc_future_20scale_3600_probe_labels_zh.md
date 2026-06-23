# BPC_future 20 规模 3600s 长跑前置标签与输出约定

日期：2026-06-23

## 目的

本次 3600s 长跑不是 Stage 4 通过证据，而是诊断当前 GAT 开启、exact-safe branch scheduling 下的 20 规模完整 proof tail：

```text
问题 1：3600s 内是否能求到 OPTIMAL
问题 2：如果能，200s 到 OPTIMAL 之间的主要耗时段在哪里
问题 3：如果不能，一小时内主要卡在哪类节点、pricing path 和 proof-tail 事件
```

## 代表实例

该实例属于主 benchmark 的分层 random-TW 60-instance 集合，路径在 canonical `BPC_future/logical_graph/tasks_020` 下；它不是旧 `moon_trek_60` hard-set。

```text
instance =
  BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json

reason =
  当前 greedy/apollo20 是 20 规模 200s OPTIMAL 目标的主要阻塞代表。
```

## 输出目录

```text
run_dir =
  BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600

results_csv =
  BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/results.csv

logs =
  BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/logs

solutions =
  BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/solutions

run_logs =
  BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/run_logs
```

## 配置边界

本次长跑不强制指定 Ryan-Foster pair：

```text
force_pair = disabled
force_pair_depth = disabled
```

保留 GAT 开启，并使用当前 exact-safe branch-tail 诊断线：

```text
journey_early_branching_enabled = True
journey_early_branching_min_cg_iter = 56
journey_early_branching_child_min_cg_iter = 3
journey_early_branching_max_depth = 3
journey_child_priority_by_width_enabled = True
journey_early_branching_after_incomplete_no_column_enabled = True
journey_early_branching_after_incomplete_no_column_min_remaining = 20.0
journey_branch_candidate_log_top_n = 20
```

开启不改变 proof 语义的诊断输出：

```text
journey_pricing_direct_journey_label_profile_timing_enabled = True
journey_branch_pricing_direct_journey_label_profile_timing_enabled = True
journey_pricing_profile_mask_diagnostics_enabled = True
journey_branch_pricing_profile_mask_diagnostics_enabled = True
journey_branch_pricing_cross_node_cache_enabled = True
journey_branch_pricing_cross_node_cache_max_entries = 200000
journey_pricing_profile_labeling_physical_catalog_share_across_branches_enabled = True
journey_branch_pricing_profile_labeling_physical_catalog_share_across_branches_enabled = True
```

以上配置只影响日志、合法分支调度和 exact-safe cache 复用；不改变 pricing universe、RMP、reduced-cost 公式、official lower bound 或 certificate 来源。

## 预置标签

长跑结束后必须生成以下标签/审计输出。

### Solver-level

```text
status
wall_time
solving_time
primal_bound
dual_bound
gap
node_count
rmp_solves
pricing_calls
exact_pricing_calls
columns
```

用途：判断 3600s 是否到 OPTIMAL，以及离 200s 目标的实际差距。

### Branch-impact labels

由 `audit_journey_branch_impact.py` 生成：

```text
y_tail_improved
y_completion_bound_tail
y_early_branch_continues
y_negative_chain_continues
y_active_touch
y_inactive_only
y_child_negative_pricing_events
y_child_completion_bound_retries
y_child_early_branch_triggers
```

用途：判断当前非 forced-pair 分支策略是否产生 useful tail-reduction positive，或只是继续制造 hard negatives。

### Weak-negative labels

由 `audit_journey_weak_negative_tail.py` 生成：

```text
y_weak_negative_filtered
weak_negative_journeys_filtered
profile_weak_filtered_materialized_count
weak_best_rough_rc
weak_best_true_rc
weak_max_true_minus_rough
repeated_weak_mask_count
repeated_weak_task_set_sample_count
```

用途：确认 root/branch 后段是否继续反复 materialize weak/boundary negative。

### Tail-impact labels

由 `build_journey_tail_impact_training_rows.py` 合并：

```text
y_useful_tail_reduction
y_tail_risk
child_negative_pricing_events
child_completion_bound_retries
child_early_branch_triggers
hard_negative_catalog_ready
contrastive_tail_training_ready
tail_label_training_ready
```

用途：判断这次长跑是否补到了真正能训练 GAT branch-tail head 的正例。

### Positive-gap labels

由 `audit_journey_tail_positive_gap.py` 生成：

```text
useful_tail_reduction_positive_count
active_touch_still_tail_risk_count
positive_gap_reason
near_positive_rows
```

用途：如果仍没有正例，定位最近正例差在哪个节点、哪个 pair、哪类 tail。

## 长跑后审计命令

```text
audit_branch =
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python
  BPC_future/scripts/audit_journey_branch_impact.py
  BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600
  --output-dir BPC_future/results/journey_branch_impact_audit_20scale_3600_v154_20260623
  --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_20scale_3600_v154_zh.md

audit_weak =
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python
  BPC_future/scripts/audit_journey_weak_negative_tail.py
  BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600
  --output-dir BPC_future/results/journey_weak_negative_tail_audit_20scale_3600_v154_20260623
  --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_20scale_3600_v154_zh.md

build_tail_rows =
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python
  BPC_future/scripts/build_journey_tail_impact_training_rows.py
  --branch-input BPC_future/results/journey_branch_impact_audit_20scale_3600_v154_20260623
  --weak-input BPC_future/results/journey_weak_negative_tail_audit_20scale_3600_v154_20260623
  --output-dir BPC_future/results/journey_tail_impact_training_rows_20scale_3600_v154_20260623
  --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_20scale_3600_v154_zh.md

audit_positive_gap =
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python
  BPC_future/scripts/audit_journey_tail_positive_gap.py
  BPC_future/results/journey_tail_impact_training_rows_20scale_3600_v154_20260623
  --output-dir BPC_future/results/journey_tail_positive_gap_audit_20scale_3600_v154_20260623
  --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_positive_gap_20scale_3600_v154_zh.md
  --top-n 20
```

## 判读规则

```text
OPTIMAL within 3600s:
  记录 200s 之后的关键耗时节点，找缩短到 200s 的主杠杆。

TIME_LIMIT / EXTERNAL_TIME_LIMIT:
  以最后 30 分钟的节点事件、pricing reason、CB retry、weak-negative 和 open-node 结构判断是否 proof-tail 发散。

y_useful_tail_reduction > 0:
  可以进入 GAT branch-tail contrastive training。

y_useful_tail_reduction = 0:
  继续主攻 exact-safe solver proof-tail reduction；GAT branch-tail head 暂时只能做 risk warning / hard-negative suppression。
```

## 安全边界

```text
pricing_oracle = false
branching_oracle = false
certificate_source = false
official_bound_effect = false
production_ready = false
stage4_candidate_ready = false
```
