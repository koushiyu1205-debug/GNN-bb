# Selector Context Feature Gap Audit 报告

日期：2026-06-14

## 目的

本报告审计当前 addition-before selector 缺哪类上下文信息。它只读既有
summary，不运行 solver，不改变 pricing / worker / certificate。

## 机器字段

```text
selector_context_feature_gap_audit = current
proxy_count = 7
current_status = feature_gap_identified_not_production_selector
current_allowed_work = calibration_only_feature_design_and_holdout
all_checks_pass = true
```

## 代理特征审计

| 代理 | 状态 | 结论 |
|---|---|---|
| `local_sequence` | `insufficient` | task_set/sequence 相同仍会跨 context 出现 improved/noop 混合。 |
| `online_flags_and_cg_iter` | `insufficient` | 加入 new_task_set、replacement/support flags、cg_iter 后仍有混合组。 |
| `instance_identity` | `insufficient` | 同一 instance 内仍存在 high-impact 与 low/noop context。 |
| `dataset_identity` | `reduces_but_insufficient` | dataset 能减少混合，但不能消除混合，也不能解释同一 dataset 内差异。 |
| `exact_context_hash` | `diagnostic_only_too_specific` | context_hash 在当前样本上消除混合，说明根因在 context/RMP 轨迹；但 hash 是身份特征，不能直接作为可泛化生产 selector。 |
| `control_objective_bin_100` | `calibration_signal_not_holdout_stable` | control_objective bin 在当前样本能消除混合，但 holdout recall 失败，仍只能作为 calibration lead。 |
| `threshold_context_scalar` | `calibration_signal_not_holdout_stable` | 简单 scalar 阈值要么高 recall 但低 precision，要么高 precision 但漏 context；没有模型通过全部 holdout。 |

## 下一步特征必须满足

- `addition_before_observable`：必须在加列前可观测；不能用 objective_delta、dual_after、active_after 或 replay label。
- `rmp_trajectory_context`：必须编码当前 RMP / active-basis / dual / pool saturation 轨迹信息，不能只依赖 task_set、sequence、true_rc 或 new_task_set。
- `less_specific_than_hash`：必须比 exact context_hash 更可泛化；hash 可做诊断分层，不能直接作为生产规则。
- `stronger_than_scalar_context`：必须比 control_objective 单 scalar 或粗 bin 更强，因为这些代理当前样本有信号但 holdout 不稳。
- `holdout_stable`：必须同时通过 context、instance、dataset holdout，再进入 5/10 no-regression 与 selected 20 hard-repeat BPC A/B。

## 结论

当前缺的不是更多局部列指标，而是可泛化的 RMP/context trajectory 表示：它必须加列前可观测，比 instance/dataset/online flags 更强，又不能像 exact context hash 那样只记身份。control_objective 是线索，但单 scalar / bin 还没有通过 holdout。
