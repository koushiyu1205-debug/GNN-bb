# Selector Failure Mechanism Audit 报告

日期：2026-06-14

## 目的

本报告进一步回答 selector 为什么还不能生产化。它只读既有诊断
summary，不运行 solver，不改变 pricing / worker / certificate。

## 机器字段

```text
selector_failure_mechanism_audit = current
mechanism_count = 6
current_production_selector_status = not_validated
current_allowed_work = calibration_only_selector_holdout
all_checks_pass = true
```

## 机制结论

### opposite_context_failure_modes

```text
status = proved
```

同一 selector family 在不同 context 下既会全错报，也会漏掉正例，还会 precision/recall 同时不稳；这不是简单阈值偏松或偏紧。

### local_column_shape_insufficient

```text
status = proved
```

task-set / sequence 级别的局部列形态仍有混合标签；当前样本里context hash 可以消除混合，但 hash 本身太具体，不能直接当生产 selector。

### instance_and_dataset_do_not_explain_context

```text
status = proved
```

同一 instance 和同一 dataset 内都同时存在 high-impact 与 low/noop context；不能用实例族或数据集族整体解释。

### micro_average_hides_fold_failures

```text
status = proved
```

micro-average 上通过的局部特征，在 context/instance/dataset fold 上不稳定；不能用整体 precision/recall 代替 holdout。

### simple_context_scalars_not_enough

```text
status = proved
```

control objective 等 addition-before scalar 有校准信号，但没有模型同时通过 dataset / instance / context holdout。

### train_holdout_rule_family_not_stable

```text
status = proved
```

即使每个训练 split 都重新选择 best rule family，context holdout 仍不是 all-pass；说明不是固定一条规则选错，而是现有特征族不够。

## 下一步必须通过的测试

- `addition_before_only_feature_scope`：selector 只能使用加列前可观测特征，不能使用 post-addition objective delta、active basis change 或 hindsight 标签。
- `context_instance_dataset_holdout`：必须同时通过 context、instance、dataset holdout，不能只看 micro average 或单 context replay。
- `opposite_failure_mode_coverage`：必须同时压住 false-positive-only context 和 missed-positive context；只调阈值不能作为生产方向。
- `exact_context_replay_no_certificate_effect`：训练与验证样本必须来自 no-certificate-effect exact-context replay，避免 certificate 或 worker side effect 污染标签。
- `production_bpc_ab_after_selector`：selector 通过 holdout 后，仍必须跑 full BPC A/B：5/10 不退化，selected 20 hard repeat 有 wall-time/gap/status/tail 改善。

## 结论

当前 selector 卡住不是因为某个单阈值没调好，而是局部列特征与下游 RMP 影响之间存在 context 依赖。下一步必须构造只用 addition-before 特征、但能解释 context/RMP trajectory 的 selector，并通过 context / instance / dataset holdout。
