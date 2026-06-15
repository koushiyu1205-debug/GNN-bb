# BPC Future GAT random-wave ord7 DELAY stratified v12 报告

日期：2026-06-15

## 目标

本轮继续验证同一规模跨地形训练 GAT 时，kNN/OOD 安全壳是否过保守。

上一轮 ord7 HIGH 候选全部来自 Tranq，且 3 条 HIGH 虽然都 target reachable、都返回 `FOUND_NEGATIVE`，但全部没有 observed primal ROI。为了检查 DELAY_QUEUE 是否漏掉正样本，本轮从 DELAY_QUEUE 里选 near-boundary 候选做 audit-only A/B：

- Apollo：取 DELAY 中 GAT probability 最高的一条；
- Tranq：取 DELAY 中 GAT probability 最高且被 kNN 拦下的一条；
- 仍然只做 explicit opt-in worker，不启用 certificate，不影响 official lower bound。

## DELAY 分层候选

候选数：2。

| region | decision_probability | best_true_rc | target |
|---|---:|---:|---|
| Apollo | 0.596985 | -1.137045 | `[17, 18, 14, 5, 3]` |
| Tranq | 0.677943 | -0.853594 | `[16, 4, 15, 19, 12, 11]` |

两条都是 true-RC negative、new support-changing，并且都处于 HIGH/DELAY 边界附近。

## A/B 结果

5/10 no-regression：

- task005：2 个实例均 `OPTIMAL`；
- task010：2 个实例均 `OPTIMAL`；
- 没有启用新 worker/gate。

20-task DELAY A/B：

| region | baseline | worker | primal improvement | ROI class |
|---|---|---|---:|---|
| Apollo | TIME_LIMIT / 642.358116 | TIME_LIMIT / 642.358116 | 0.0 | columns_only_roi |
| Tranq | TIME_LIMIT / 548.335796 | TIME_LIMIT / 548.335796 | 0.0 | no_observed_roi |

Reachability：

- Apollo：target intervention reachable，worker 返回 `FOUND_NEGATIVE`；
- Tranq：target intervention reachable，worker 返回 `FOUND_NEGATIVE`；
- 两条均有 target causal match；
- official_bound_effect=false；
- certificate_ready=false。

解释：这两条 DELAY 不是“没找到负列”，而是“找到目标负列后仍没有 primal 改善”。因此安全壳没有漏掉正 ROI，至少在本轮 near-boundary DELAY 子集上是合理的。

## v12 combined ROI 数据

将 v11 combined 与本轮 DELAY v12-only 合并：

- row_count：54；
- positive_primal_roi：18；
- negative_primal_roi：12；
- no_observed_roi：20；
- columns_only_roi：4。

构建 graph dataset 后：

- sample_count：50；
- `add`：18；
- `abstain`：32；
- `columns_only_roi` skipped：4；
- family_count：3；
- region_count：2。

## v12 GAT 与 kNN/OOD 审计

v12 GAT：

- sample_count：50；
- validation accuracy：0.75；
- validation add precision：0.0；
- validation add recall：0.0；
- selector_can_certificate=false。

v12 kNN/OOD：

- decision_record_count：50；
- predicted HIGH：3；
- HIGH precision：0.6667；
- HIGH recall：0.1111；
- validation predicted HIGH：1；
- validation HIGH precision：0.0；
- validation HIGH recall：0.0；
- validation false-positive HIGH on DELAY：1；
- negative recall delay queue：0.9091；
- production_ready=false；
- production_block_reasons：
  - `validation_false_high_priority_on_delay`
  - `validation_candidate_not_ready`

本轮同时收紧了 kNN/OOD 审计 summary/report 字段，显式输出：

- `validation_safety_ready`
- `validation_safety_checks`
- `production_block_reasons`

这样即使离线审计 `all_checks_pass=true`，也不会被误读成模型可生产。

## 当前判断

同规模跨地形合并训练仍然可行，但当前数据还不够：

1. v12 增加的是 hard-negative，不是 positive ROI；
2. Apollo DELAY near-boundary 未带来 primal 改善；
3. Tranq DELAY near-boundary 未带来 primal 改善；
4. validation 上出现 HIGH false-positive，说明 v12 不能生产；
5. GAT 仍只能作为 embedding / trajectory-impact 表达；
6. kNN/OOD 必须作为安全壳；
7. 不通过安全壳的 true-RC negative 只能进入 DELAY_QUEUE，不能永久丢弃。

## 下一步

继续采样时应减少盲目 near-boundary DELAY A/B，改为更有针对性的正样本发现：

- 优先找 Apollo random-wave 的 target-reachable positive ROI；
- 优先找 Tranq random-wave 中能真正改变 primal/dual trajectory 的 context；
- 采样时记录 worker 后下一轮 RMP objective delta / dual L1 delta；
- 对每个 region/family cell 建立正负平衡，而不是只增加 hard-negative；
- 在 validation false-positive 归零前，不允许进入生产 gate。

当前目标仍未达成：20-task 还没有在 200 秒内稳定精确求解，GAT/worker 也不能默认启用。
