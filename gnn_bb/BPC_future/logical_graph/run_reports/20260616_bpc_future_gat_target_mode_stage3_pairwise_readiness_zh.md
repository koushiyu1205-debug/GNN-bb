# 2026-06-16 BPC_future GAT Target Mode Stage 3 Pairwise Readiness 报告

## 结论

本轮把 Stage 3 的 pairwise ranking 前置成 dataset-level gate。当前 v3 signature
数据可以继续做 diagnostic classification / regression，但不能合法训练
same-context pairwise ranking。

核心数字：

```text
dataset = BPC_future/data/gat_batch_impact/v3_signature_20260616
sample_count = 294
candidate_count = 4569
training_ready = true
ranking_ready = false
context_count = 294
same_context_pair_count = 0
same_context_comparable_pair_count = 0
roi_diverse_context_count = 0
positive_negative_label_pair_count = 0
ranking_blockers = ['need_same_context_batch_pairs_for_pairwise_ranking']
```

这解释了为什么上一轮 hard-ROI loss 只能小幅改善 threshold frontier，不能解决
high-ROI capture 和 low-ROI accepted 的排序问题：当前训练集没有同一个 RMP context
下的多个 candidate batch 选项，模型无法学习
`score(high-ROI batch) > score(low-ROI batch)`。

## 本轮修改

- `BPC_future/scripts/build_gat_batch_impact_dataset.py`
  - 新增 `--min-same-context-pairs-for-ranking`；
  - manifest / summary / report 新增 `pairwise_context_stats`；
  - 新增 `ranking_ready` 和 `ranking_blockers`；
  - 区分 `training_ready` 与 `ranking_ready`，防止把普通二分类数据误当成
    pairwise ranking 数据。

- `BPC_future/scripts/train_gat_batch_impact.py`
  - 训练 summary / checkpoint / report 已记录 `context_pair_stats`；
  - 当前 checkpoint 标记 `pairwise_ranking_loss_active=false`；
  - 当前状态为 `pairwise_ranking_status=inactive_no_same_context_pairs`。

- `BPC_future/tests/test_gat_batch_impact_dataset.py`
  - 覆盖 singleton-context 数据下 `ranking_ready=false`；
  - 覆盖同 context 且 ROI 有差异时 `ranking_ready=true`。

## 当前 V3 Dataset 状态

family 维度：

```text
greedy-anchor: samples=54, contexts=54, same_context_pairs=0
random-wave:  samples=190, contexts=190, same_context_pairs=0
sector-wave:  samples=50, contexts=50, same_context_pairs=0
```

task-count 维度：

```text
tasks5:   samples=2,   contexts=2,   same_context_pairs=0
tasks10:  samples=8,   contexts=8,   same_context_pairs=0
tasks20:  samples=118, contexts=118, same_context_pairs=0
tasks30:  samples=76,  contexts=76,  same_context_pairs=0
tasks50:  samples=89,  contexts=89,  same_context_pairs=0
tasks100: samples=1,   contexts=1,   same_context_pairs=0
```

因此当前 Stage 3 阻塞不是单纯 sample count，而是 intervention design：
每个 context 只有一个被观测 batch，缺少同 context 下的 high-ROI / low-ROI 对照。

## 对 Stage 3 的影响

hard-ROI 训练后的最新 offline 审计仍显示：

```text
feasible_threshold_count = 0
best_accepted_batch_count = 14
best_safe_precision_ci_low = 0.7846829880728186
best_accepted_batch_roi_ci_low = 0.42537332534726846
accepted_high_roi_opportunities = 5 / 8
accepted_low_roi_or_bad = 9
missed_high_roi_opportunities = 3
```

结论：当前 checkpoint 仍只能是 diagnostic checkpoint，不能作为 Stage 4 safe source。
不能通过降低 threshold 或跨 context pairwise 训练来凑 Stage 4 candidate。

## 下一步

采样策略必须改成同 context 多 batch intervention：

```text
for each selected RMP context x_t:
  materialize multiple true-RC verified candidate batches U_t^1, U_t^2, ...
  include at least:
    best-RC / GAT-priority candidate batch
    diverse random negative-control batch
    replacement-heavy batch
    new-task-set / support-changing batch
  replay or observe each batch under the same x_t label window
  emit multiple rows sharing the same context_hash
```

下一批数据的 Stage 3 gate：

```text
ranking_ready = true
same_context_comparable_pair_count > 0
positive_negative_label_pair_count > 0
family/task buckets report pair counts
no post-addition features in model inputs
diagnostic_only = true
runs_bpc_or_pricing = false for builder/training/audits
```

## Exactness Boundary

本轮只修改离线数据转换、训练 metadata 和测试，不运行 BPC、pricing、RMP 或 final judge。
GAT / CBF / kNN / OOD 仍然：

- 不是 pricing oracle；
- 不能产生 official lower bound；
- 不能产生 no-negative certificate；
- 不能永久丢弃 true-RC negative；
- 不能替代 final exact pricing full closure。

最终 proof 仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的
`CERTIFIED_NO_NEGATIVE`。

