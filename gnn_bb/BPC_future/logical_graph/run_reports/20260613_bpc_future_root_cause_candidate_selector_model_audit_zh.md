# BPC_future 根因审计补充：candidate selector model generalization audit

日期：2026-06-13

## 目标

本轮不改 solver / pricing / RMP / Pulse / certificate。

目标是检查：

> 如果把 candidate + batch-context 特征交给稍微强一点的离线模型，是否能跨 dataset / instance 稳定识别 improved candidates？

这一步只用于 calibration。它不能产生 production selector，也不能影响 official lower bound。

## 输入

输入文件：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/candidate_rows.csv
```

使用样本：

```text
scale = 20
run_improvement_class in {improved, worsened}
rows = 848
improved = 553
worsened = 295
```

只使用 addition-before 特征：

- candidate position；
- sequence length；
- start time；
- arc count；
- low_time / low_risk / low_energy fraction；
- candidate active overlap / Jaccard；
- batch returned count；
- batch pair overlap / Jaccard；
- batch active overlap / redundancy / bridge fraction。

不使用后验字段：

- candidate added；
- future active；
- incumbent within 2；
- zero fractional；
- next incomplete。

## 模型

无外部依赖，使用三个简单模型：

1. `nearest_centroid`
2. `linear_mean_diff`
3. `shallow_tree_depth3`

验证方式：

- leave-one-dataset；
- leave-one-instance。

## leave-one-dataset 结果

```text
nearest_centroid:
  accuracy = 0.41037735849056606
  precision = 0.6055776892430279
  recall = 0.27486437613019893
  tp/fp/tn/fn = 152 / 99 / 196 / 401

linear_mean_diff:
  accuracy = 0.5778301886792453
  precision = 0.6633165829145728
  recall = 0.7160940325497287
  tp/fp/tn/fn = 396 / 201 / 94 / 157

shallow_tree_depth3:
  accuracy = 0.34787735849056606
  precision = 0.5
  recall = 0.0108499095840868
  tp/fp/tn/fn = 6 / 6 / 289 / 547
```

解释：

- `linear_mean_diff` 能抓到较多 positives，但 false positives 很多，precision 只有 `0.6633`；
- `nearest_centroid` recall 很低；
- `shallow_tree_depth3` 基本退化成几乎不抓 positives；
- 没有模型达到一个保守 production selector 起点：`precision >= 0.75 and recall >= 0.5`。

## leave-one-instance 结果

```text
nearest_centroid:
  accuracy = 0.24882075471698112
  precision = 0.33064516129032256
  recall = 0.14828209764918626
  tp/fp/tn/fn = 82 / 166 / 129 / 471

linear_mean_diff:
  accuracy = 0.6898584905660378
  precision = 0.7230769230769231
  recall = 0.8499095840867993
  tp/fp/tn/fn = 470 / 180 / 115 / 83

shallow_tree_depth3:
  accuracy = 0.375
  precision = 0.5327635327635327
  recall = 0.33815551537070526
  tp/fp/tn/fn = 187 / 164 / 131 / 366
```

解释：

- `linear_mean_diff` 的 leave-one-instance recall 较高，但 false positives 仍有 `180`，precision `0.7231`，没有达到 `0.75`；
- `nearest_centroid` 和 `shallow_tree_depth3` 仍然明显不够；
- 跨 instance 也没有稳定、低误报的 production selector。

## 结论

这轮结果说明：

> candidate + batch-context 特征确实有信号，但简单离线模型仍不能跨 dataset / instance 稳定泛化到可上线 selector。

因此当前不能把任何简单模型接进 production path，也不能用它触发 worker / return-count / profile-DP cap。

目标仍未完成。

当前下一步仍只能是 calibration-only：

1. 扩展更多 20-task contexts；
2. 增加更完整的 candidate/rank/true-RC/batch trajectory features；
3. 使用严格 leave-one-instance / leave-one-dataset；
4. 只有 selector 同时保护 5/10 no-op 且稳定改善 20 hard set，才进入 opt-in A/B。
