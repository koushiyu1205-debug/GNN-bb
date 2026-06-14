# Optimization Direction Candidate Registry 报告

日期：2026-06-14

## 目的

本报告回答“做了这么多工作为什么还不行”。它只汇总已有诊断
summary，不运行 solver，不改变 pricing / worker / certificate。

## 机器字段

```text
optimization_direction_candidate_registry = current
candidate_count = 11
approved_production_direction_count = 0
forbidden_direction_count = 3
allowed_calibration_direction_count = 5
production_direction_proven = false
goal_complete = false
missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup
current_allowed_next_stage = calibration_only_selector_holdout
all_checks_pass = true
```

## 一句话回答

不是 Pulse 子模块单点失效；5/10 被固定开销伤害，20 的 true-RC negative columns 又不足以稳定改变 RMP trajectory。当前缺的是 addition-before、低开销、跨 context/instance/dataset 通过的 selector。

## 当前方向状态表

| 方向 | 状态 | 允许的下一步 | 原因 |
|---|---|---|---|
| 继续修 Pulse 接线、物化或证书状态机 | `ruled_out_as_primary_root_cause` | `do_not_treat_as_production_speedup_direction` | 证书状态机和列物化已经能安全加入 true-RC negative columns；剩余失败是 downstream ROI，而不是接线本身。 |
| 继续找更多或更负的 true-RC negative columns | `ruled_out_as_sufficient_condition` | `only_as_calibration_signal_not_as_completion` | 20-task run 已经能加入 true-RC negative columns 和新 task sets，但仍没有稳定 wall-time/status/gap 改善。 |
| 扩大 worker 预算或默认启用 worker | `forbidden_for_current_stage` | `keep_default_disabled` | 5/10 对固定开销敏感；触发 worker/audit/probe 的行整体变慢，不触发的 no-op gate 才保持官方结果不变。 |
| 用 true-RC 阈值、task-set 或 sequence 局部特征筛列 | `not_production_validated` | `continue_holdout_only` | 局部阈值有 calibration signal，但存在 false positive 和 false negative；同一 task-set/sequence 可在不同 context 下相反。 |
| 简单 ML 或 batch-level selector | `not_production_validated` | `continue_context_instance_dataset_holdout` | 简单模型与 batch gate 有信号，但没有同时通过 context、instance、dataset 的生产 holdout。 |
| 用 active-basis hash churn / RMP degeneracy proxy 做 selector | `not_production_validated` | `do_not_promote_proxy_to_production_selector` | 3 个 addition-before RMP proxy 已进入离线 holdout；active-basis hash proxy 和 degeneracy proxy 仍不能跨 context/instance/dataset 稳定通过，不能当生产 gate。 |
| 把单 context replay 成功当生产证据 | `forbidden_shortcut` | `require_holdout_and_bpc_ab` | exact replay 同时包含 high-impact 和 no-op/replacement 样本；单点成功不能证明泛化 ROI。 |
| 继续扩 exact-context capture/replay 校准集 | `allowed_calibration_only` | `build_more_no_certificate_effect_replay_cases` | 该 gate 已可支持 selector calibration attempt，但仍不能直接进入 production A/B 或 certificate effect。 |
| 训练只使用 addition-before 特征的 selector | `calibration_only_not_production_validated` | `must_pass_context_instance_dataset_holdouts` | 存在 replay-calibrated selector 候选，但 blocker catalog 显示具体反例、fold gate、规则族和 context anatomy 仍阻塞上线。 |
| 进入 production candidate BPC A/B | `blocked` | `do_not_enter_until_selector_and_5_10_20_gates_pass` | 入口仍被 selector_not_validated、five_ten_full_no_regression_missing、twenty_speedup_missing 三项同时阻塞。 |
| 开放 Pulse official certificate gate | `forbidden_for_current_stage` | `keep_certificate_effect_disabled` | 当前正向信号是 calibration/worker 找列，不是完整 proof；certificate effect 在 production A/B 前仍是 forbidden shortcut。 |

## 结论

当前不是没有任何信号，而是信号还停留在 calibration 层：负列能被安全找到和加入，但不能稳定转化为 20-task wall-time/status/gap 改进；同时 5/10 对额外触发开销敏感。因此下一步只能继续 addition-before selector holdout，不能默认启用 worker，也不能打开 official certificate gate。
