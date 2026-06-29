# GAT Branch/Action Sanity Dataset

日期：2026-06-28

## 目的

把已完成 branch counterfactual replay 转成小规模 GAT branch/action sanity dataset。该数据集只用于离线试训模型管线，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
output_dir = BPC_future/data/gat_branch_action_sanity/v705_routeopt_bkf_phased_replay_20260628
target_wall = 200.0
wall_cap = 600.0
min_wall_improvement = 30.0
min_wall_regression = 30.0
raw_row_count = 13
sample_count = 10
row_kind_counts = {'changed_timeout_no_effect_hard_negative': 3, 'hard_negative_regression': 1, 'paired_probe_hard_negative_proxy': 2, 'paired_probe_positive_proxy': 1, 'right_censored_neutral': 1, 'walltime_gain_target_wall_crossing': 3, 'weak_gap_fathom_positive': 1, 'weak_gap_positive': 1}
branch_priority_label_counts = {'aux_only_weak_positive': 1, 'not_walltime_gain': 6, 'walltime_gain_positive': 3}
target_wall_crossing_label_counts = {'not_target_wall_crossing': 7, 'target_wall_crossing_positive': 3}
tail_improved_aux_label_counts = {'tail_improved': 3, 'tail_not_improved': 7}
skipped_counts = {'not_training_sample:right_censored_neutral': 1, 'not_training_sample:weak_gap_fathom_positive': 1, 'not_training_sample:weak_gap_positive': 1}
instance_count = 8
family_count = 3
sanity_training_dataset_ready = true
serious_training_dataset_ready = false
optin_training_dataset_ready = false
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## 标签边界

- 主 `branch_priority` 标签使用 capped wall-time gain，不把 200 秒作为训练硬断点。
- `target_wall_crossing_positive` 只作为验收/报告字段；`199s -> 201s` 这类小变化不会成为强负例，`500s -> 300s` 会成为高权重正例。
- `weak_positive_not_target` 样本保留在数据集中；只要有足够 wall-time gain，也会进入主标签，否则仅作为 `tail_improved` 辅助标签。
- `local_only_hard_negative` 和未校准右删失 proxy 不进入主训练样本；`paired_probe_hard_negative_proxy` 只作为 proof-risk hard-negative calibration 进入，不能当 full-run 反例。
- `paired_probe_positive_proxy` 只进入 auxiliary weak-positive / proof-cost 训练头，主 wall-time gain loss 权重保持 0，不能当 full-run 正例或 production score 依据。

## Schema

```json
{
  "branch_feature_schema": [
    "depth",
    "candidate_count",
    "eligible_count",
    "has_candidate_log",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "same_mass",
    "fractionality",
    "support_count",
    "incumbent_relation_known",
    "incumbent_relation_same",
    "incumbent_disagreement",
    "pool_same_allowed",
    "pool_separate_allowed",
    "pool_max_child_width",
    "pool_total_child_width",
    "pool_balance_gap"
  ],
  "context_feature_schema": [
    "node_id",
    "depth",
    "branch_time",
    "candidate_count",
    "eligible_count",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "phased_testing_stage_code",
    "phased_testing_decision_code",
    "phased_testing_elimination_reason_code",
    "phased_testing_phase0_passed",
    "phased_testing_phase1_lp_complete",
    "phased_testing_phase2_heuristic_complete",
    "baseline_task_i",
    "baseline_task_j",
    "alternative_task_i",
    "alternative_task_j",
    "phase1_min_child_lp_gain",
    "phase1_child_lp_gain_product",
    "phase1_child_width_balance",
    "phase1_wall_time",
    "phase1_dynamic_k_probe_count",
    "phase2_negative_child_count",
    "phase2_negative_journey_count",
    "phase2_best_reduced_cost",
    "phase2_worst_negative_severity",
    "phase2_wall_time",
    "phase2_dynamic_k_probe_count"
  ],
  "label_schema": [
    "y_branch_priority_walltime_gain",
    "branch_priority_loss_weight",
    "capped_wall_time_delta",
    "capped_wall_time_delta_ratio",
    "y_target_wall_crossing_positive",
    "y_strict_full_replay_positive",
    "y_weak_positive_not_target",
    "y_counterfactual_regression",
    "y_timeout_regression",
    "y_timeout_resolved",
    "y_tail_improved_aux",
    "tail_improved_loss_weight",
    "y_walltime_gain",
    "walltime_gain_loss_weight",
    "y_child_proof_cpu",
    "child_proof_cpu_loss_weight",
    "y_time_to_certificate",
    "time_to_certificate_loss_weight"
  ]
}
```

## RouteOpt/BKF phased 字段覆盖审计

本次 V705 使用 V704 schema 重建数据集，确认数据管线已经可以承载 RouteOpt/BKF staged branch testing 特征，但旧 replay/delta rows 本身没有这些字段。

输入 rows 审计结果：

```text
raw_rows = 13
samples = 10
phased_testing_stage present/nonempty = 0/0
phased_testing_decision present/nonempty = 0/0
phased_testing_elimination_reason present/nonempty = 0/0
phased_testing_phase0_passed present/nonempty = 0/0
phased_testing_phase1_lp_complete present/nonempty = 0/0
phased_testing_phase2_heuristic_complete present/nonempty = 0/0
phase1_min_child_lp_gain present/nonempty = 0/0
phase1_child_lp_gain_product present/nonempty = 0/0
phase1_child_width_balance present/nonempty = 0/0
phase1_wall_time present/nonempty = 0/0
phase1_dynamic_k_probe_count present/nonempty = 0/0
phase2_negative_child_count present/nonempty = 0/0
phase2_negative_journey_count present/nonempty = 0/0
phase2_best_reduced_cost present/nonempty = 0/0
phase2_worst_negative_severity present/nonempty = 0/0
phase2_wall_time present/nonempty = 0/0
phase2_dynamic_k_probe_count present/nonempty = 0/0
```

输出样本审计结果：

```text
phased_testing_stage_code nonzero_samples = 0/10
phased_testing_decision_code nonzero_samples = 0/10
phased_testing_elimination_reason_code nonzero_samples = 0/10
phased_testing_phase0_passed nonzero_samples = 0/10
phased_testing_phase1_lp_complete nonzero_samples = 0/10
phased_testing_phase2_heuristic_complete nonzero_samples = 0/10
phase1_min_child_lp_gain nonzero_samples = 0/10
phase1_child_lp_gain_product nonzero_samples = 0/10
phase1_child_width_balance nonzero_samples = 0/10
phase1_wall_time nonzero_samples = 0/10
phase1_dynamic_k_probe_count nonzero_samples = 0/10
phase2_negative_child_count nonzero_samples = 0/10
phase2_negative_journey_count nonzero_samples = 0/10
phase2_best_reduced_cost nonzero_samples = 0/10
phase2_worst_negative_severity nonzero_samples = 0/10
phase2_wall_time nonzero_samples = 0/10
phase2_dynamic_k_probe_count nonzero_samples = 0/10
```

结论：V705 只能证明“dataset/export schema 已接通”，不能证明“RouteOpt/BKF phased testing 特征已经可训练”。现有 V637/V651/V652/V653/V656/V681/V669/V674/V678 delta rows 生成时间早于 V703 的 phased logging 透传，`alternative_raw_row` 里缺少这些字段，所以训练时这些新增维度全是默认 0。

## 对当前主线的含义

这解释了为什么不能马上用 V704/V705 去训练一个真正理解 RouteOpt/BKF 分阶段测试的 GAT：模型会看到字段名，但看不到信号。若直接训练，新增 context features 只会成为常数列，无法学习：

- 哪些 pair 通过 Phase 0 cheap screen；
- 哪些 pair 的 Phase 1 child LP probe 真的抬高两个 child；
- 哪些 pair 在 Phase 2 heuristic probe 里暴露负列链风险；
- 哪些 pair 是因为 dynamic-K / width / balance 被过滤。

因此当前可用的 V705 数据集只适合继续验证旧的 wall-time gain / hard-negative 标签管线，不适合作为 production-ready RouteOpt/BKF score-map 来源。

## 下一步

正确顺序应改为：

1. 用 V703 之后的 solver logs 重新抽取 branch candidate / branch impact / paired probe rows，确保 `phased_testing_*`、`phase1_*`、`phase2_*` 字段进入原始 rows。
2. 用更新后的 delta-row builders 重新生成 full replay / paired probe delta rows。
3. 再跑 V706 dataset audit，验收新增字段非零覆盖率。
4. 只有当 phased/phase1/phase2 字段在正例和 hard negative 中都有覆盖时，才训练 GAT 并导出 score map。

本轮不需要回退 V703/V704 代码；问题在于旧证据链需要重采样/重抽取，而不是 schema 或模型接口缺失。
