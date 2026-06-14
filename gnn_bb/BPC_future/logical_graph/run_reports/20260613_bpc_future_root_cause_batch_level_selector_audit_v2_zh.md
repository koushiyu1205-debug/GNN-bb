# BPC_future 根因审计补充：batch-level selector audit v2

日期：2026-06-13

## 目标

上一轮确认 `candidate_rows.csv` 的 improved / worsened 是 batch/run outcome 展开到 returned candidates，不是单列因果标签。

因此本轮直接回到 `stage_rows.csv` 的 batch 粒度，检查：

> 只用 batch-level addition-before features，是否能稳定预测 20-task improved / worsened。

本轮仍然只读，不运行 solver，不修改 pricing / RMP / Pulse 主线。

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_batch_level_selector.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_batch_level_selector.py \
--output-dir BPC_future/results/root_cause_batch_level_selector_20260613
```

输出：

```text
BPC_future/results/root_cause_batch_level_selector_20260613/summary.json
```

## 样本

20-task strict stage rows：

- rows：`288`
- improved：`136`
- worsened：`152`

这个粒度避免了 candidate expansion 对 label balance 的放大。

## Aggregate batch signal

最强 addition-before batch feature：

```text
feature = returned_union_size
auc_positive_higher = 0.6897977941176471
positive_mean = 6.147058823529412
negative_mean = 3.7697368421052633
```

最强 post-addition / hindsight feature：

```text
feature = incumbent_within2
auc_positive_higher = 0.718266253869969
positive_mean = 0.6470588235294118
negative_mean = 0.21052631578947367
```

解释：

- addition-before batch features 有信号；
- 但最强信号仍是 batch size / returned coverage 相关；
- 后验 incumbent trajectory 仍更接近 improved / worsened 的真实差异。

## Leave-one-dataset

只用单特征阈值规则，每次 held out 一个 result-set。

| feature set | accuracy | precision | recall | tp | fp | tn | fn |
|---|---:|---:|---:|---:|---:|---:|---:|
| pre-batch | `0.4201388888888889` | `0.4392156862745098` | `0.8235294117647058` | `112` | `143` | `9` | `24` |
| post-addition / hindsight | `0.6909722222222222` | `0.6821705426356589` | `0.6470588235294118` | `88` | `41` | `111` | `48` |

pre-batch 规则的问题很明确：

- recall 高；
- precision 很低；
- false positive `143`；
- 实际上是把大量 worsened batch 也预测为 improved。

这不能作为 production worker / selector gate。

## Leave-one-instance

只用单特征阈值规则，每次 held out 一个 instance。

| feature set | accuracy | precision | recall | tp | fp | tn | fn |
|---|---:|---:|---:|---:|---:|---:|---:|
| pre-batch | `0.4618055555555556` | `0.46619217081850534` | `0.9632352941176471` | `131` | `150` | `2` | `5` |
| post-addition / hindsight | `0.6805555555555556` | `0.6617647058823529` | `0.6617647058823529` | `90` | `46` | `106` | `46` |

pre-batch 在 instance 外推下更明显是“几乎全报正例”：

- tp `131`；
- fp `150`；
- tn 只有 `2`。

这解释了为什么 20-task 上某些 batch 扩张策略会偶发改善，却无法稳定上线。

## 对根因判断的影响

本轮把前面的 candidate-level 结论提升到 batch-level：

> 即使用正确的 batch/stage 粒度，addition-before batch features 仍不能形成稳定 selector。当前最强 pre-batch 信号主要是 returned coverage / batch size，泛化时 false positive 太多。

这说明：

- 不应继续把 candidate-level label 当单列因果标签；
- 也不应认为 batch-level returned_count / union_size 阈值能解决问题；
- 真正缺的是能在加列前预测后续 active-basis / incumbent trajectory 的 batch-level selector；
- 这个 selector 需要更强的 counterfactual / replay / causal evidence。

## 当前不能得出的结论

不能说：

- returned_union_size 完全没用；
- 多返回列一定坏；
- hindsight feature 可以用于 production。

只能说：

- batch size / coverage 是相关信号；
- 但当前泛化 precision 不足；
- 后验 incumbent trajectory 更能解释 improved / worsened；
- production 方向仍未闭环。

## 结论

根因进一步稳定为：

> BPC_future 当前 20-task hard-tail 的主要缺口，是没有一个能从 addition-before batch/context 信息稳定预测后续 RMP active-basis / incumbent trajectory 的 selector。

这不是 Pulse 单点问题，也不是简单增大 worker、profile-DP cap、return count 或 pricing time 能直接解决的问题。
