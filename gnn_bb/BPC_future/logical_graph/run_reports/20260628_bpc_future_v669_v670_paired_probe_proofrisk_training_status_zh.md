# 20260628 V669/V670：Paired-Probe Proof-Risk Training Status

## 结论

本轮把 V666 paired child-probe 中暴露的 `hard_negative_proxy` 接入 branch-action 训练数据链路，但仍保持 exact-safe 和 proxy-only 边界。

完成内容：

- V669：把 `paired_probe_rows.jsonl` 转成兼容 `branch_counterfactual_delta_rows.jsonl` 的 proof-risk calibration rows。
- V670：把 V669 的 2 条 hard-negative proxy 合并进 V658 all-counterfactual 数据集。
- V670 seed29：做了一次 sanity/offline 训练，验证训练管线可读取新 proof-risk 负例。

本轮不导出生产 score map，不运行 full60，不改变 solver 默认行为。

## 代码改动

新增：

- `BPC_future/scripts/build_journey_paired_probe_delta_rows.py`
- `BPC_future/tests/test_journey_paired_probe_delta_rows.py`

修改：

- `BPC_future/scripts/build_gat_branch_action_sanity_dataset.py`
- `BPC_future/tests/test_gat_branch_action_sanity_dataset.py`

新增标签：

- `counterfactual_label_type = paired_probe_hard_negative_proxy`

该标签只作为 proof-risk hard-negative calibration 进入数据集；它的 row 保持：

```text
proxy_only = true
right_censored_counterfactual = true
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## V669：Paired-Probe Delta Rows

输入：

- `BPC_future/results/journey_paired_probe_summary_v666_v664_external_score_child_probe_20260628/paired_probe_rows.jsonl`

输出：

- `BPC_future/results/journey_paired_probe_delta_rows_v669_v666_external_score_child_probe_20260628/branch_counterfactual_delta_rows.jsonl`
- `BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_paired_probe_delta_rows_v669_v666_external_score_child_probe_zh.md`

机器结果：

```text
input_row_count = 24
output_row_count = 2
input_paired_label_counts = {'hard_negative_proxy': 2, 'missing_baseline': 5, 'neutral_proxy': 7}
output_counterfactual_label_counts = {'paired_probe_hard_negative_proxy': 2}
skipped_counts = {'neutral_proxy_excluded': 7, 'not_convertible': 15}
```

输出样本：

| instance | pair | wall gain | gap improvement | hard-negative weight |
|---|---:|---:|---:|---:|
| `apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817` | `[5,18]` | -9.259593 | -0.002354 | 3.486 |
| `apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510` | `[1,18]` | +19.261906 | -0.001218 | 2.609 |

注意：第二条虽然短 probe wall gain 为正，但 gap 变差且 paired summary 判为 `hard_negative_proxy`，因此不能当正例。

## V670：合并数据集

输入：

- V658 manifest 中记录的 53 个原始 `branch_counterfactual_delta_rows.jsonl`
- V669 paired-probe delta rows

输出：

- `BPC_future/data/gat_branch_action_sanity/v670_v658_plus_v669_paired_probe_proofrisk_20260628/`
- `BPC_future/logical_graph/run_reports/20260628_bpc_future_gat_branch_action_v670_v658_plus_v669_paired_probe_proofrisk_dataset_zh.md`

相对 V658：

| dataset | raw rows | samples | not walltime gain | walltime positive | paired hard-negative proxy |
|---|---:|---:|---:|---:|---:|
| V658 | 301 | 206 | 140 | 54 | 0 |
| V670 | 303 | 208 | 142 | 54 | 2 |

V670 机器字段：

```text
raw_row_count = 303
sample_count = 208
branch_priority_label_counts = {'aux_only_weak_positive': 12, 'not_walltime_gain': 142, 'walltime_gain_positive': 54}
row_kind_counts['paired_probe_hard_negative_proxy'] = 2
family_count = 3
instance_count = 34
sanity_training_dataset_ready = true
serious_training_dataset_ready = false
optin_training_dataset_ready = false
```

## V670 seed29 sanity training

输出：

- checkpoint: `BPC_future/data/gat_branch_action_sanity/v670_v658_plus_v669_paired_probe_proofrisk_20260628/gat_branch_action_v670_seed29.pt`
- metrics: `BPC_future/results/gat_branch_action_v670_seed29_paired_probe_proofrisk_20260628/summary.json`
- report: `BPC_future/logical_graph/run_reports/20260628_bpc_future_gat_branch_action_v670_seed29_paired_probe_proofrisk_train_zh.md`

对比 V658 seed29：

| training | samples | best val loss | val precision | val recall | val F1 |
|---|---:|---:|---:|---:|---:|
| V658 seed29 | 206 | 92.401454 | 0.000000 | 0.000000 | 0.000000 |
| V670 seed29 | 208 | 88.403393 | 0.263158 | 0.357143 | 0.303030 |

解释：

- V670 sanity 指标比 V658 seed29 好，说明新数据和改动没有破坏训练链路。
- 但 V670 只新增 2 条 proof-risk proxy；validation 指标仍来自很小且非严格生产集。
- 因此不能把 V670 checkpoint 直接导出成 production score map。

## 已跑验证

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest BPC_future.tests.test_journey_paired_probe_delta_rows BPC_future.tests.test_gat_branch_action_sanity_dataset
PYTHONDONTWRITEBYTECODE=1 python -m unittest BPC_future.tests.test_gat_branch_score_proofrisk_overlay BPC_future.tests.test_journey_branch_candidate_replay_runbook BPC_future.tests.test_gat_branch_action_checkpoint_ranking
```

全部通过。

## 对主目标的意义

这一步解决的是一个具体训练偏差：

- 裸 wall-time head 会把部分短 probe 看似省时、但 proof-risk 高的 pair 打高分；
- V669/V670 把这类 pair 明确加入 hard-negative calibration；
- 后续模型/score-map 可以学习“短期 wall gain 不等于完整闭环收益”。

但这一步还不能直接提升 20-scale full60：

- 没有新增 strict full-solve positive；
- 没有运行新的 full60；
- 当前最佳仍是 V545 的 `36/60 OPTIMAL`；
- 距离 20-scale `60/60 OPTIMAL within 600s` 还有明显差距。

## 下一步判断

不建议马上把 V670 checkpoint 导出到 solver 跑 full60。更合理的下一步是按 RouteOpt/BKF 思路做 staged branch testing：

1. 用现有 V543/V667/V668/V670 score 做候选初筛；
2. 对 hard 20-scale context 生成 topK，但 K 动态受 child width、balance gap、retry risk 控制；
3. 对少量候选做 fixed-budget paired child-probe；
4. 只把左右 child 都改善 gap/fathom/retry 的 pair 进入 full replay；
5. 用 full replay 或强 paired evidence 再更新 score map。

也就是说，V670 是校准数据，不是最终加速版本。下一轮应主攻 staged testing / BKF candidate controller，而不是裸导出 V670 score map。
