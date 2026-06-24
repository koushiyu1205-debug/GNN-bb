# BPC_future V113 Branch Child-Probe 标签报告

日期：2026-06-24

## 目的

把 branch-impact audit 从“分支后总体行为统计”推进到 child 级 proof-cost 标签，为后续 limited strong branching / fixed-expansion probe / GAT branch-ordering head 提供训练数据。

本次不运行新的 BPC 求解，不改变求解器行为，不产生 certificate 或 official bound。

## 代码变化

- `BPC_future/scripts/audit_journey_branch_impact.py`
  - 新增 `CHILD_PROBE_LABEL_SCHEMA`。
  - 新增 `child_probe_rows.jsonl` 输出。
  - branch label 增加 child exact pricing、fathom、safe/corrected bound gain 汇总。
  - child row 增加 proof CPU、time-to-certificate、time-to-fathom、CB retry、early branch trigger 等字段。
  - 修正 `child_lower_bound_gain` 口径：优先使用 `journey_branch.bound` 作为参考，缺失时才回退 parent node lower bound，避免 root `lower_bound=0` 造成假增益。
- `BPC_future/tests/test_journey_branch_impact_audit.py`
  - 增加 exact certificate、corrected bound、fathom event、child probe rows 的断言。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_journey_branch_impact_audit

PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/scripts/audit_journey_branch_impact.py \
  BPC_future/tests/test_journey_branch_impact_audit.py
```

两项均通过。

## V112 日志重跑

输入：

```text
BPC_future/results/logs_20260624_v112_branch_score_plus_tail_action_greedy_seed61001_140
```

输出：

```text
audit = BPC_future/results/journey_branch_impact_audit_v113_v112_child_probe_seed61001_20260624
machine_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v113_v112_child_probe_seed61001_zh.md
```

结果：

```text
branch_count = 2
branch_training_row_count = 2
child_probe_row_count = 4
tail_class_counts = {'completion_bound_tail': 2}
usable_branch_impact_training_count = 2
total_child_negative_pricing_events = 15
total_child_exact_pricing_events = 12
total_child_certificate_pricing_events = 3
total_child_completion_bound_retries = 9
total_child_early_branch_triggers = 1
total_child_fathom_events = 3
max_child_lower_bound_gain = 0.0
max_child_corrected_bound_gain = 5.109067
```

## 判断

V112 的 `[2,6]` 正例不是靠 child inherited/safe lower bound 直接变强；`max_child_lower_bound_gain = 0.0`。真正有用的信号在 child proof path：corrected bound gain、exact pricing 事件、CB retry、certificate/fathom 时间。

这符合当前优先级判断：branch pair / child ordering 不能只学“候选覆盖率”，必须学习子节点证明成本和 corrected bound 收口行为。

## V114 Positive Chain 批量审计

为了扩大 child-probe 样本，这次复用了已有真实 solver 日志，不跑新求解：

```text
inputs =
  BPC_future/results/logs_20260624_v63_branch_score_v61_tie02_optin_220_seed61001
  BPC_future/results/logs_20260624_v86_branch_score_horizon_v85_seed61001_220
  BPC_future/results/logs_20260624_v96_branch_score_horizon_v95_seed61001_220
  BPC_future/results/logs_20260624_seed61001_branch_score_root_only_replay6_optin_fixed_220
audit = BPC_future/results/journey_branch_impact_audit_v114_positive_chain_child_probe_seed61001_20260624
machine_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v114_positive_chain_child_probe_seed61001_zh.md
```

结果：

```text
log_count = 4
branch_count = 10
branch_training_row_count = 10
child_probe_row_count = 20
complete_label_branch_count = 9
usable_branch_impact_training_count = 9
tail_class_counts = {'completion_bound_tail': 9, 'unprocessed_children': 1}
total_child_negative_pricing_events = 66
total_child_exact_pricing_events = 67
total_child_certificate_pricing_events = 18
total_child_completion_bound_retries = 44
total_child_fathom_events = 14
max_child_lower_bound_gain = 0.0
max_child_corrected_bound_gain = 5.109067
```

判断：positive chain 的可学习信号主要集中在 child proof path，而不是 child safe lower bound 直接变强。`completion_bound_tail=9/10` 说明下一步 branch-ordering head 应优先建模 proof CPU、CB retry、certificate timing、corrected bound gain。`unprocessed_children=1` 是 right-censored，只能作为诊断或弱标签，不能当完整反事实正负例。

## V115 Coverage-Gap Hard Negative 审计

V107 coverage-gap runs 的原始日志仍在 runbook `runs` 目录下，因此可以直接重跑新版 audit：

```text
input = BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624/runs
audit = BPC_future/results/journey_branch_impact_audit_v115_v107_coverage_gap_child_probe_20260624
machine_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v115_v107_coverage_gap_child_probe_zh.md
```

结果：

```text
log_count = 5
branch_count = 35
branch_training_row_count = 35
child_probe_row_count = 70
right_censored_branch_count = 35
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
tail_class_counts = {'completion_bound_tail': 24, 'unprocessed_children': 11}
forced_pair_branch_count = 4
forced_pair_matched_branch_count = 4
total_child_negative_pricing_events = 117
total_child_exact_pricing_events = 139
total_child_certificate_pricing_events = 40
total_child_completion_bound_retries = 135
total_child_fathom_events = 10
max_child_lower_bound_gain = 0.0
max_child_corrected_bound_gain = 22.948295
```

判断：这批样本能说明 coverage-gap 候选会制造大量 proof-tail / CB retry 风险，但由于 35/35 都是 right-censored，不能作为完整正负排序标签。它们适合作 hard-negative 风险导航和采样优先级，不应混入 complete branch-impact training row。

## 下一步

1. 把 V114 的 positive-chain complete rows 和 V115 的 right-censored hard negatives 分开入库，先做 deterministic scorer 的离线验证，不直接上线。
2. 继续寻找不同实例、不同父节点的 complete mixed positive/negative child-probe 数据，避免只围绕 seed61001 单 context 学过窄规律。
3. 基于 child-probe rows 训练或先构造一个 deterministic score map，优先预测：
   - child corrected bound gain；
   - child proof CPU；
   - child CB retry；
   - child time-to-certificate。

20-task 200s 全量目标仍未达成；V113 是训练标签基础设施，不是新的求解性能结论。
