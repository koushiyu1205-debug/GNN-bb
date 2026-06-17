# 2026-06-16 BPC_future GAT Target Mode Stage 3 v35 Rescue+kNN/ROI Shell 综合报告

## 结论

v35 是一次 Stage 3 offline / diagnostic-only 审计推进，不是 Stage 4 candidate。

本轮先复读五阶段优化计划、Stage 1/2 基础报告、Stage 3 v23/v24/v27/v28/v29/v31
结论、Stage 4 v23 A/B / reachability / certificate 审计，以及 Stage 5
20/30/50/100 exact target。当前主 blocker 已不是 v15 那种大面积 raw score
结构性分不开，而是：

```text
rescue / positive boost 能恢复 high-ROI recall，
但必须同时压住 low-ROI / delay-risk admission；
kNN/OOD safety shell 可以压住 false-safe，
但当前 embedding 邻域不能稳定证明 accepted ROI CI。
```

因此 v35 没有把任何 checkpoint 升级为 Stage 4。正确下一步不是继续放宽 rescue
window，也不是继续扫全局 penalty，而是补充 ROI-stable same-context contrast 或改进
embedding / neighbor metric，使 kNN/OOD 后的 accepted ROI lower bound 能稳定过线。

## 本轮实现

只修改 offline audit 工具：

- `audit_gat_batch_impact_knn_ood.py` 支持 audit-only gate override：
  - `candidate_admission_score_mode`
  - `candidate_delay_score_penalty`
  - `candidate_delay_gate_enabled`
  - `candidate_delay_risk_threshold`
  - `candidate_rescue_*`
- 增加默认关闭的 ROI-aware kNN shell：
  - `--min-neighbor-accepted-batch-roi`
  - `--min-neighbor-accepted-batch-roi-ci-low`

这些参数只作用于离线审计 summary / decision records，不改 checkpoint，不改 solver /
pricing / RMP / worker，不产生 certificate。

## v35 审计结果

固定 rescue window：

```text
candidate_admission_score_mode = risk_adjusted_rescue_window
candidate_rescue_raw_score_threshold = 0.30
candidate_rescue_delay_risk_threshold = 0.75
candidate_rescue_delay_score_penalty = 0.25
knn_k = 3 or 5
max_neighbor_delay_fraction = 0.0
```

核心对比：

| variant | accepted | ROI | ROI CI low | safe CI low | false-safe | blocker |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v28 rescue+kNN k3 | 39 | 2.8588 | 0.1001 | 0.9103 | 0.0 | ROI CI low |
| v29_p075 rescue+kNN k3 | 44 | 1.2449 | -0.0535 | 0.9197 | 0.0 | ROI CI low |
| v28 ROI-CI shell k3 | 0 | n/a | n/a | n/a | 0.0 | zero coverage |
| v29_p075 ROI-CI shell k3 | 0 | n/a | n/a | n/a | 0.0 | zero coverage |
| v28 ROI-mean shell k3 | 8 | 9.3771 | -1.6188 | 0.6756 | 0.0 | sample/ROI CI |
| v29_p075 ROI-mean shell k3 | 8 | 5.7352 | -0.8463 | 0.6756 | 0.0 | sample/ROI CI |
| v28 ROI-mean shell k5 | 8 | 5.9255 | -3.9969 | 0.6756 | 0.0 | random-wave missing |
| v29_p075 ROI-mean shell k5 | 8 | 5.6549 | -0.9592 | 0.6756 | 0.0 | random-wave missing |

读法：

- kNN/OOD 安全壳对 rescue 有效：v28/v29 rescue 的 false-safe / false delay 都压到 0。
- 但 rescue+kNN 的 accepted ROI CI-low 仍远低于 Stage 3/4 `>= 0.65` gate。
- 加 `neighbor ROI CI-low >= 0.65` 太保守，直接 zero coverage。
- 加 `neighbor ROI mean >= 0.65` 能保留少量高 point ROI 样本，但 accepted count 只有 8，
  safe precision CI-low 只有 `0.6756`，ROI CI-low 为负。
- k=5 没有改善，反而使 random-wave high-ROI opportunity 被全部 delay。

## 判断

v35 证明了两个事实：

1. `rescue window + kNN/OOD` 可以作为安全诊断壳，但不是 ROI-stable admission rule。
2. 当前 embedding 邻域对 ROI 的局部估计太稀疏 / 高方差，不能支撑 Stage 4 gate。

这意味着下一步应优先补数据和表示，而不是继续调全局阈值：

- 对 v28/v29 中被 ROI-neighbor shell 拦掉但真实 high-ROI 的 context 补
  same-context positive/negative contrast；
- 对 accepted point ROI 高但 CI 为负的 8 条样本做 context-level decomposition，
  判断是否由单一大 ROI outlier 撑起；
- 改进 embedding / kNN metric，使邻域按 RMP trajectory impact 聚类，而不是只按
  batch/context 表示相近；
- 后续如果继续 rescue，必须先过 kNN/OOD safety，再过 ROI-neighbor 或等价
  ROI-stability shell。

## Exact-safe 边界

```text
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
official_bound_effect = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT / CBF / kNN / OOD 只能做 discovery ordering 和 finite-delay admission
scheduling。true-RC negative 不能永久丢弃；DELAY_QUEUE 不参与 no-negative
certificate。最终 OPTIMAL / no-negative reduced-cost certificate 仍只能来自当前
branch/cut/true-dual 下 exact pricing 对完整配置宇宙的 exhaustive closure。

## 产物

```text
v28 rescue+kNN =
  BPC_future/results/gat_batch_impact_knn_ood_v35_v28_rescue_window_global_20260616/summary.json
v29 rescue+kNN =
  BPC_future/results/gat_batch_impact_knn_ood_v35_v29_p075_rescue_window_global_20260616/summary.json
v28 ROI CI shell =
  BPC_future/results/gat_batch_impact_knn_ood_v35_v28_rescue_roi_ci065_global_20260616/summary.json
v29 ROI CI shell =
  BPC_future/results/gat_batch_impact_knn_ood_v35_v29_p075_rescue_roi_ci065_global_20260616/summary.json
v28 ROI mean shell =
  BPC_future/results/gat_batch_impact_knn_ood_v35_v28_rescue_roi_mean065_global_20260616/summary.json
v29 ROI mean shell =
  BPC_future/results/gat_batch_impact_knn_ood_v35_v29_p075_rescue_roi_mean065_global_20260616/summary.json
v28 ROI mean k5 =
  BPC_future/results/gat_batch_impact_knn_ood_v35_v28_rescue_roi_mean065_k5_global_20260616/summary.json
v29 ROI mean k5 =
  BPC_future/results/gat_batch_impact_knn_ood_v35_v29_p075_rescue_roi_mean065_k5_global_20260616/summary.json
```

## 下一步

不要把 v35 任一审计规则送 Stage 4。建议下一步做 v36：

1. 从 v35 decision records 中抽取 `knn_roi_mean_delay_queue` 且真实 high-ROI 的样本，
   形成 narrow same-context contrast / embedding-neighborhood repair plan。
2. 对 v35 accepted 8 条高 point ROI 样本做 outlier / context decomposition，确认
   ROI CI 为负的来源。
3. 若要继续模型训练，目标应增加 ROI-neighborhood stability 或 context-local ROI
   ranking，而不是继续加大 positive boost / 放宽 rescue。
