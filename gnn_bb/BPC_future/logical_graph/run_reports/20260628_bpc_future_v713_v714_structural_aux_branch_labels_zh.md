# 20260628 V713/V714：Branch Structural-Aux Labels 接入训练链路

## 结论

本轮完成的是 Branch Score 主线的训练标签层改造，不改变 solver 行为。

核心变化：

- `weak_gap_positive` / `weak_gap_fathom_positive` / `weak_gap_regression` 不再被数据集过滤掉；
- 这类样本进入训练集时保持 `branch_priority_loss_weight = 0`，只训练结构性辅助头；
- GAT branch/action 模型新增多目标回归头：
  - `gap_improvement`
  - `primal_improvement`
  - `dual_bound_gain`
  - `fathom_gain`
  - `branch_count_delta`
  - `completion_bound_retry_gain`
- checkpoint 版本升级为 `gat_branch_action_sanity_v3_structural_aux`；
- exact-safe 边界保持不变：不产生 official bound，不产生 certificate，不参与剪枝，不接入默认 solver。

这对应当前 RouteOpt/BKF 方向里的第二项：branch score 不能只看 wall time，要学习两个 child 的均衡收益、gap/fathom/retry/proof-tail 信号。

## 代码改动

涉及文件：

- `BPC_future/scripts/build_gat_branch_action_sanity_dataset.py`
- `BPC_future/scripts/build_gat_tree_policy_event_dataset.py`
- `BPC_future/learning/branch_impact_model.py`
- `BPC_future/scripts/train_gat_branch_action_sanity.py`
- `BPC_future/tests/test_gat_branch_action_sanity_dataset.py`
- `BPC_future/tests/test_gat_branch_action_sanity_training.py`

新增/确认的数据字段：

```text
y_gap_improvement
gap_improvement_loss_weight
y_primal_improvement
primal_improvement_loss_weight
y_dual_bound_gain
dual_bound_gain_loss_weight
y_fathom_gain
fathom_gain_loss_weight
y_branch_count_delta
branch_count_delta_loss_weight
y_completion_bound_retry_gain
completion_bound_retry_gain_loss_weight
```

## V713：V637 weak gap/fathom 样本 smoke

输入：

`BPC_future/results/journey_branch_counterfactual_delta_v637_seed61311_root_full_replay_weak_20260628`

输出：

`BPC_future/data/gat_branch_action_sanity/v713_gap_fathom_aux_label_smoke_20260628`

结果：

```text
raw_row_count = 2
sample_count = 2
row_kind_counts = {'weak_gap_fathom_positive': 1, 'weak_gap_positive': 1}
branch_priority_label_counts = {'aux_only_weak_positive': 2}
sanity_training_dataset_ready = false
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

解释：

- `[16,20]` 和 `[16,17]` 这两条 seed61311 timeout replay 现在能进入数据集；
- 它们不会被当成 full-solve / walltime 正例；
- 它们只作为 gap/fathom/proof-tail 辅助监督。

## V714：mixed walltime + structural aux 训练 smoke

输入：

- V637 weak gap/fathom；
- V653 routeopt BKF positive full replay；
- V656 near-positive / regression full600；
- V681 strict full replay positive。

输出：

```text
dataset = BPC_future/data/gat_branch_action_sanity/v714_mixed_walltime_gap_aux_smoke_20260628
checkpoint = BPC_future/data/gat_branch_action_sanity/v714_mixed_walltime_gap_aux_smoke_20260628/gat_branch_action_v714_structural_aux_smoke.pt
metrics = BPC_future/results/gat_branch_action_v714_structural_aux_smoke_20260628/summary.json
```

数据集结果：

```text
raw_row_count = 8
sample_count = 8
row_kind_counts = {
  'changed_timeout_no_effect_hard_negative': 3,
  'hard_negative_regression': 1,
  'walltime_gain_target_wall_crossing': 2,
  'weak_gap_fathom_positive': 1,
  'weak_gap_positive': 1
}
branch_priority_label_counts = {
  'aux_only_weak_positive': 2,
  'not_walltime_gain': 4,
  'walltime_gain_positive': 2
}
sanity_training_dataset_ready = true
serious_training_dataset_ready = false
```

训练 smoke：

```text
epochs = 1
sanity_training_completed = true
all_checks_pass = true
production_ready = false
score_map_exported = false
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

训练 history 中已出现以下新 loss：

```text
gap_improvement_loss
primal_improvement_loss
dual_bound_gain_loss
fathom_gain_loss
branch_count_delta_loss
completion_bound_retry_gain_loss
```

这证明 structural aux 标签已真实进入训练 loss，而不是只写进 manifest。

## Tree-policy 兼容性修正

`build_gat_tree_policy_event_dataset.py` 也复用 `BRANCH_ACTION_LABEL_SCHEMA`。新增 structural fields 后，tree-policy-only 样本一开始缺少这些 key，会在构建 `branch_action_labels` 时失败。

已修正为：

- tree-policy 行默认补齐 structural label 为 0；
- 如果行内已有 `labels` / `deltas` 中的 gap、fathom、retry、branch-count 字段，则同步写入；
- sample 上也挂载对应 tensor，后续训练脚本可以读取；
- 不改变 tree-policy 原有主标签和 loss 权重。

## 验证

已通过：

```bash
python -m py_compile \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/scripts/train_gat_branch_action_sanity.py \
  BPC_future/learning/branch_impact_model.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_gat_branch_action_sanity_training.py

python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_dataset \
  BPC_future.tests.test_gat_branch_action_sanity_training
```

补充通过：

```bash
python -m unittest \
  BPC_future.tests.test_gat_tree_policy_event_dataset \
  BPC_future.tests.test_gat_branch_action_sanity_dataset \
  BPC_future.tests.test_gat_branch_action_sanity_training \
  BPC_future.tests.test_gat_branch_action_checkpoint_ranking \
  BPC_future.tests.test_gat_branch_score_proofrisk_overlay
```

单元测试覆盖：

- weak gap/fathom timeout 行作为 aux-only 样本进入；
- phased testing context features 被写入；
- tree-policy event dataset 与扩展后的 label schema 兼容；
- checkpoint 版本为 `gat_branch_action_sanity_v3_structural_aux`；
- checkpoint boundary 明确包含新增 structural regression heads；
- exactness contract 仍为非 certificate / 非 official bound / 非 solver default。

## 当前边界

V714 不能当 production 模型：

- 样本只有 8 条；
- `serious_training_ready = false`；
- `optin_training_ready = false`；
- 没有导出 score map；
- 没有做 full60 solver 验证。

它的价值是修通训练链路，让后续 RouteOpt/BKF phased testing 产出的 `gap/fathom/retry/child-balanced` 标签不会再丢失。

## 下一步

1. 继续把 `routeopt_bkf_staged` 从 solver 内日志/实验模式推进成标准 branch testing controller。
2. 在 solver 事件中稳定记录两个 child 的：
   - `min_child_lb_gain`
   - `child_gain_product`
   - `child_width_balance`
   - `completion_bound_retry_delta`
   - `fathom_gain`
   - `gap_improvement`
3. 对 V545 的 21 个 `branch_tree_plus_completion_tail` 未解实例做 depth 1-4 state-scoped replay，优先补齐 structural aux 标签。
4. 等样本量达到正式门槛后再导出 score map；当前 v714 checkpoint 只能作为 smoke artifact。
