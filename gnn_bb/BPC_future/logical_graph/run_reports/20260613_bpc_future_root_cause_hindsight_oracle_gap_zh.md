# BPC_future 根因审计补充：hindsight oracle gap

日期：2026-06-13

## 目标

本轮继续只做只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

目标是验证一个关键问题：

> improved / worsened trajectory 是否本身可分？如果可分，当前失败是否主要来自 addition-before 特征无法预测后续 active-basis / incumbent 轨迹？

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/candidate_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_hindsight_oracle_gap.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_hindsight_oracle_gap.py \
--output-dir BPC_future/results/root_cause_hindsight_oracle_gap_20260613
```

输出：

```text
BPC_future/results/root_cause_hindsight_oracle_gap_20260613/summary.json
```

## 对比对象

Addition-before features：

- candidate position / sequence / start time / arc composition；
- active overlap / active jaccard；
- batch returned count / pair overlap / pair jaccard；
- batch active overlap / redundant / bridge。

Hindsight trajectory features：

- `candidate_future_active_within2`
- `candidate_future_active_value`
- `incumbent_within2`
- `zero_fractional_within2`
- `next_negative_count`
- `next_incomplete_count`

注意：hindsight features 不能用于 production selector。它们只用于定位“真正需要提前预测的目标”。

## 样本

20-task strict candidate rows：

- rows：`848`
- improved：`553`
- worsened：`295`

## Aggregate signal

最强 addition-before feature：

```text
feature = batch_pair_overlap
auc_positive_higher = 0.6995310632298403
positive_mean = 0.40580566710765625
negative_mean = 0.2401496808276469
```

最强 hindsight trajectory feature：

```text
feature = incumbent_within2
auc_positive_higher = 0.7848223863671192
positive_mean = 0.6781193490054249
negative_mean = 0.10847457627118644
```

解释：

- improved runs 更常在后续两轮内触发 incumbent movement；
- worsened runs 即使也有 negative / added candidates，后续 incumbent trajectory 明显不同；
- 因此问题不是“候选完全没有信息”，而是当前 addition-before features 没有稳定预测后续 trajectory。

## Leave-one-dataset 对比

只用单特征阈值规则、每次 held out 一个 result-set。

| feature set | accuracy | precision | recall | tp | fp | tn | fn |
|---|---:|---:|---:|---:|---:|---:|---:|
| addition-before | `0.6132075471698113` | `0.676056338028169` | `0.7811934900542495` | `432` | `207` | `88` | `121` |
| hindsight trajectory | `0.6780660377358491` | `0.7880658436213992` | `0.6925858951175407` | `383` | `103` | `192` | `170` |

Hindsight trajectory rule 的 precision 明显更高，false positive 从 `207` 降到 `103`。

这说明：如果能提前预测“是否会进入 incumbent-producing trajectory”，就能过滤很多 currently false-positive 的 batch。

## Leave-one-instance 对比

只用单特征阈值规则、每次 held out 一个 instance。

| feature set | accuracy | precision | recall | tp | fp | tn | fn |
|---|---:|---:|---:|---:|---:|---:|---:|
| addition-before | `0.42452830188679247` | `0.5895316804407713` | `0.38698010849909587` | `214` | `149` | `146` | `339` |
| hindsight trajectory | `0.5872641509433962` | `0.6723259762308998` | `0.7160940325497287` | `396` | `193` | `102` | `157` |

Hindsight 在 instance 外推下也不是 production selector，但比 addition-before 明显更接近目标：recall 从 `0.38698` 到 `0.71609`。

## 对根因判断的影响

本轮证据把根因再推进一步：

> 20-task 的 returned-batch 选择不是不可分问题；后验 trajectory 信号能区分 improved / worsened。当前缺口是：addition-before 可观察特征不能稳定预测这些后验 trajectory 信号。

换句话说，真正需要优化的不是继续扩大候选生成，而是建立一个能够在加列前预测以下结果的 selector：

- 这批列是否会进入后续 active basis；
- 是否会减少后续 incomplete；
- 是否会触发 incumbent-producing trajectory；
- 是否只是 replacement / degenerate movement。

## 当前不能得出的结论

不能把 hindsight result 当生产方案：

- `incumbent_within2` 是后验结果；
- `zero_fractional_within2` 是后续求解轨迹；
- `next_incomplete_count` 也是后续状态；
- 它们不能在 pricing addition 前直接使用。

因此本轮不是优化成功证据，而是 root-cause 证据：

- objective trajectory 本身可分；
- current addition-before features 抓不稳；
- 下一步若继续，应围绕“预测后验 trajectory 的 addition-before proxy”构造证据。

## 结论

当前失败的核心不是 Pulse、profile-DP 或 return count 单点，而是：

> BPC_future 缺少一个能从加列前 candidate/batch/context 信息预测后续 RMP active-basis / incumbent trajectory 的 selector。

在这个 selector 未被证明前，继续扩大 worker / cap / return count 只会增加候选和开销，不会保证 5/10 no-regression 和 20-task 大幅加速。
