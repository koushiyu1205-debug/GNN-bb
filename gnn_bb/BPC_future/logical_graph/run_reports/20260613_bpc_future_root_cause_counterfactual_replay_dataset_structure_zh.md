# BPC_future 根因补充：exact replay selector 数据结构审计

日期：2026-06-13

## 目标

本轮继续做 calibration-only 根因审计，不修改主线求解器。

目标是解释当前 `addition_before_selector` gate 失败的结构原因：它到底只是因为单特征 / 二特征 / 简单模型太弱，还是当前 exact replay impact rows 本身仍存在跨数据集标签覆盖不足。

## 输入

读取 4 组 `candidate_impact_rows.csv`：

- `duplicate_noop_smoke`
- `real_capture_mt20_apollo`
- `root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613`
- `root_cause_counterfactual_target_capture_dp1000_tranq20_20260613`

脚本：

```text
BPC_future/scripts/analyze_counterfactual_replay_dataset_structure.py
```

输出：

```text
BPC_future/results/root_cause_counterfactual_replay_dataset_structure_20260613/summary.json
```

## 关键结果

总体：

```text
row_count = 207
label_counts = improved:147, noop:60
all_checks_pass = true
```

按 `impact_dataset`：

```text
group_count = 4
mixed_label_group_count = 1
pure_improved_group_count = 2
pure_noop_group_count = 1
single_label_row_count = 31
single_label_row_share = 0.1497584541062802
```

4 个 replay dataset 中只有 1 个同时包含 improved 与 noop：

```text
duplicate_noop_smoke:
  rows = 1
  labels = noop:1

real_capture_mt20_apollo:
  rows = 4
  labels = improved:4

root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613:
  rows = 176
  labels = improved:117, noop:59

root_cause_counterfactual_target_capture_dp1000_tranq20_20260613:
  rows = 26
  labels = improved:26
```

按 `instance`：

```text
group_count = 4
mixed_label_group_count = 2
pure_improved_group_count = 1
pure_noop_group_count = 1
single_label_row_count = 27
single_label_row_share = 0.13043478260869565
```

按 `context_hash`：

```text
group_count = 22
mixed_label_group_count = 5
pure_improved_group_count = 13
pure_noop_group_count = 4
single_label_row_count = 127
single_label_row_share = 0.6135265700483091
```

22 个 exact context 中只有 5 个同时包含 improved 与 noop；61.35% 的 rows 位于单标签 context。

## 解释

这说明当前 selector gate 失败不只是“模型太弱”。

更准确地说：

1. exact replay rows 已经足够支持 calibration attempt；
2. 但跨 dataset 标签覆盖仍然不均衡；
3. 多个 dataset 是纯 improved 或纯 noop；
4. 多数 context 也是单标签；
5. 因此 leave-one-dataset / leave-one-context 下，selector 很容易学到 dataset/context-specific 规律，而不是 production 可泛化规律。

这解释了之前的现象：

- full sample true-RC threshold 可以看起来不错；
- context / instance holdout 有些模型能过；
- dataset holdout 没有模型通过；
- pair rule 在 full sample precision 很高，但 dataset precision / context recall 失败。

## 对根因判断的影响

根因判断进一步收紧：

> 20-task 不是没有 high-impact returned batch；当前 replay 数据也已经包含 high-impact 和 no-op/replacement。但这些标签在 dataset/context 上仍然集中，导致 addition-before selector 还不能被证明可泛化。生产失败的根因仍是缺少跨 context 可泛化的 returned-batch impact selector，而不是缺少负列或单个 Pulse bug。

当前三道 evidence gate 状态保持不变：

```text
exact_context_capture_and_replay_dataset = ready_for_selector_calibration_attempt
addition_before_selector = failed_current_rules
production_candidate_ab = blocked_until_selector_and_20_speedup_pass
```

这轮新增的具体约束是：

> 继续做 selector 之前，应该优先增加跨 dataset / context 的双标签 exact replay coverage，而不是继续在当前数据上堆更复杂模型。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_replay_dataset_structure.py \
--output-dir BPC_future/results/root_cause_counterfactual_replay_dataset_structure_20260613
```

结果：

```text
all_checks_pass = true
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/analyze_counterfactual_replay_dataset_structure.py
```

结果：通过。
