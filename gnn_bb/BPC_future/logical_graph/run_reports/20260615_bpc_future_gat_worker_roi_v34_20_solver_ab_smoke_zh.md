# GAT Worker ROI v34 20规模 Solver A/B Smoke 报告

日期：2026-06-15

## 目标

用最新 `paired_worker_ab_trajectory_roi` 标签样本训练得到的 GAT v34 做一次 20 规模 opt-in worker A/B，检查：

1. 对 20 规模实例是否有实际 solver ROI；
2. 5/10 规模默认路径是否保持 no-regression；
3. GAT + kNN/OOD shell 的当前问题是训练不足，还是模型/表示能力不足；
4. 是否能在不增加训练集数量的情况下改善召回率和准确率。

本轮仍是 diagnostic-only：

- 不默认启用 worker；
- 不产生 certificate；
- 不产生 official lower bound；
- 不把 unsafe 负列丢弃，只进入 DELAY_QUEUE。

## 使用的数据与模型

最新样本与模型：

- dataset summary：`BPC_future/results/gat_worker_roi_dataset_v34_after_v33_sampling_20260615/summary.json`
- GAT graph dataset：`BPC_future/data/gat_worker_roi/v34_after_v33_sampling_20260615`
- GAT training summary：`BPC_future/results/gat_worker_roi_training_v34_after_v33_sampling_20260615/summary.json`
- kNN/OOD audit：`BPC_future/results/gat_worker_roi_knn_ood_audit_v34_after_v33_sampling_20260615/summary.json`
- solver A/B runbook：`BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_after_v33_sampling_20260615/summary.json`
- solver A/B audit：`BPC_future/results/gat_worker_roi_solver_ab_runbook_v34_after_v33_sampling_20260615/ab_audit/summary.json`

样本规模：

```text
row_count = 229
training_row_count = 197
positive_trajectory_roi_count = 61
negative_trajectory_roi_count = 137
duplicate_candidate_count = 0
```

训练标签语义仍是：

```text
target_label = paired_worker_ab_trajectory_roi
```

即标签来自 paired baseline vs worker A/B 的 trajectory ROI，不是 reduced cost、same-run proxy 或单纯列可行性标签。

## GAT 与 kNN/OOD 当前表现

裸 GAT validation：

```text
add_precision = 0.3810
add_recall = 0.9412
add_f1 = 0.5424
tp_add = 16
fp_add = 26
fn_add = 1
```

严格 kNN/OOD shell validation：

```text
predicted_high_priority = 5
add_precision = 0.8000
add_recall = 0.2353
false_high_priority_rate = 0.0278
true_positive_high_priority = 4
false_positive_high_priority = 1
```

解释：

- 裸 GAT 可以抓到大部分正 ROI，但误报很多；
- 严格 kNN/OOD shell 可以把误报压低，但会把大量真阳性放进 DELAY_QUEUE；
- 当前不是“完全没有信号”，而是 precision/recall tradeoff 太硬，尚不能生产化。

## 20规模 Solver A/B 结果

本轮从 kNN/OOD `HIGH_PRIORITY` 中选出 5 个候选做 20 规模 A/B。

总体：

```text
record_count = 5
positive_trajectory_roi_count = 4
negative_trajectory_roi_count = 1
official_bound_effect = false
certificate_ready = false
production_ready = false
```

5/10 no-regression sentinel：

```text
task005: OPTIMAL, primal=dual=284.084294, time=0.407s
task010: OPTIMAL, primal=dual=456.756326, time=3.195s
```

20 规模成对结果摘要：

| 候选 | ROI类 | primal改善 | solving_time_delta | exact_pricing_calls_delta | pricing_calls_delta |
|---|---|---:|---:|---:|---:|
| tranq sector 02 / 4-19-10-17 | positive_retry_roi | 0.0000 | -7.6697s | -1 | 0 |
| tranq greedy 09 / 7-12 | positive_retry_roi | 0.0000 | +0.2950s | -1 | 0 |
| apollo sector 02 / 7-6-1-19-2-8 | positive_primal_roi | +4.2860 | -17.8712s | 0 | +2 |
| apollo sector 02 / 7-14-6-19-11 | positive_primal_roi | +1.4014 | -18.5554s | 0 | +3 |
| apollo sector 03 / 4-6-20-11 | negative_retry_roi | 0.0000 | +4.4161s | +2 | +4 |

合计：

```text
5个 HIGH_PRIORITY 中 4个正 ROI，1个负 ROI
总 primal_improvement = +5.6874
总 solving_time_delta = -39.3852s
```

注意：所有 20 规模 run 仍是 `TIME_LIMIT`，没有出现 20 规模 OPTIMAL 或 official bound 改善。

## 结论

### 是否有加速？

有局部 solver ROI 信号，但还不是生产级加速。

正面信号：

- 5 个 HIGH_PRIORITY 中 4 个在 solver A/B 中为正 ROI；
- Apollo sector 02 两个候选带来 primal 改善，并降低约 18s wall time；
- 一个 Tranquillitatis 候选减少 1 次 exact pricing call，并降低约 7.7s wall time；
- 5/10 no-regression 仍然保持 OPTIMAL；
- 没有 certificate / official lower-bound 副作用。

不足：

- 所有 20 规模仍是 `TIME_LIMIT`；
- 没有把 20 规模推进到 exact optimal；
- 一个 false HIGH_PRIORITY 明确拖慢；
- retry ROI 与 primal ROI 不稳定，同一类高分候选不总是带来 wall-time 改善；
- kNN/OOD shell 当前召回过低，很多潜在正 ROI 还在 DELAY_QUEUE。

### 原因是训练不够还是模型问题？

不是单纯训练不够。

当前样本数确实还偏小，但更主要的问题是“表示与决策边界不够好”：

1. 裸 GAT 召回高、精度低，说明模型能感知部分 ROI 信号，但无法可靠分开正负 ROI；
2. kNN/OOD shell 精度高、召回低，说明安全壳很保守，牺牲了大量真阳性；
3. 放松 shell 可以提高召回，但 false high-priority 会快速上升；
4. solver A/B 中已经出现 4/5 正 ROI，说明信号存在；但 false positive 的代价也真实存在。

所以当前瓶颈不是“再多训练几轮”能解决，而是：

- GAT embedding 对 trajectory ROI 的区分能力还不够；
- safety shell 的边界太粗；
- 训练目标还是单点候选分类，尚未真正建模 batch / trajectory-level impact。

## 不增加训练集数量时的改进方向

可以改善，但不能保证直接达到生产阈值。

优先级建议：

1. 训练目标改成 recall/precision 可控的 cost-sensitive objective：
   - focal loss；
   - 正负样本重加权；
   - false-positive cost 与 false-negative cost 分开调。

2. 从 binary classifier 改成 ranking / pairwise loss：
   - 同一 context 内比较正 ROI 候选和负 ROI 候选；
   - 训练“谁更值得 HIGH_PRIORITY”，而不是只问“是不是 add”。

3. 使用当前训练集做 hard-negative mining：
   - 把 false HIGH_PRIORITY 的负 ROI 样本提高权重；
   - 把 false DELAY_QUEUE 的正 ROI 样本提高权重；
   - 不增加样本数量，只改变采样权重。

4. 重新校准 kNN/OOD shell：
   - 不只用固定 neighbor delay fraction；
   - 按 family / scale / ROI class 做分层阈值；
   - 目标不是全局最高 precision，而是控制 false-high-priority 同时提升召回。

5. 增强现有特征而不增加样本：
   - 加入 context-level dual movement、support churn、pricing retry history；
   - 加入 family/scale embedding；
   - 加入 candidate 与当前 active support 的相似度/替代性特征。

## 当前判定

GAT 没被否定。相反，这次是第一次看到：

```text
HIGH_PRIORITY solver A/B: 4/5 正 ROI
```

但它仍不能生产化，因为：

```text
kNN/OOD validation recall = 0.2353
source validation_candidate_ready = false
20规模仍 TIME_LIMIT
false HIGH_PRIORITY 仍会拖慢
```

下一步不应该继续盲目采样，也不应该默认启用 worker。

建议下一步做：

1. 同一 v34 数据集上训练 2-3 个无增量数据变体：
   - weighted BCE；
   - focal loss；
   - pairwise/ranking objective。
2. 对每个模型固定跑同一套 kNN/OOD + 20 solver A/B；
3. 只接受同时满足：
   - 5/10 no-regression；
   - high-priority precision 不低于当前 0.8 太多；
   - recall 明显高于 0.235；
   - 20 规模 solver A/B 正 ROI 稳定；
   - false HIGH_PRIORITY 不导致明显拖慢。

