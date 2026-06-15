# BPC Future GAT random-wave ord7 ROI sampling v11 报告

日期：2026-06-15

## 目标

本轮回答并验证一个问题：同一规模下，不同地形/区域的样本是否可以合并给 GAT 训练。

结论先行：

- 可以合并同一规模样本训练共享 GAT encoder；
- 不能把不同地形当成同分布样本；
- 必须保留 `region / family / terrain / ordinal / scale` 条件特征；
- 必须继续使用 kNN/OOD 安全壳；
- 通过安全壳的负列只能进入 `HIGH_PRIORITY`，未通过的负列进入 `DELAY_QUEUE`，不能永久丢弃，也不能参与证书。

## ord7 capture 结果

本轮先在 random-wave ord7 上采集 same-run batch-impact 样本：

- 样本数：13；
- objective-positive：9；
- non-improving：4；
- Apollo：3 positive / 2 non-improving；
- Tranquillitatis：6 positive / 2 non-improving；
- graph candidate：199；
- `add` label：172；
- `abstain` label：27。

5/10 no-regression 与 20 capture 均按单 worker 顺序执行，没有默认启用 worker/certificate。

## ord7 本地 GAT + kNN/OOD

训练结果：

- sample_count：13；
- validation accuracy：0.8136；
- validation add precision：0.8776；
- validation add recall：0.8958；
- diagnostic_only：true；
- selector_can_certificate：false。

kNN/OOD 审计：

- decision_record_count：13；
- predicted HIGH：3；
- HIGH precision：1.0；
- HIGH recall：0.3333；
- validation predicted HIGH：0；
- validation HIGH recall：0；
- negative recall delay queue：1.0；
- production_ready：false。

这说明本地 ord7 模型能表达一部分 trajectory impact，但安全壳在跨 split 上很保守，不允许作为生产 gate。

## task20 候选抽取

HIGH 候选：

- 数量：3；
- 全部来自 `random-wave | tranquillitatis_balmer_like_20km | task020 | ordinal 7`；
- 全部是 `new_support_changing`；
- 全部 true-RC negative；
- Apollo 没有 HIGH 候选。

DELAY 候选：

- 数量：5；
- Apollo：2；
- Tranquillitatis：3；
- 全部是 `new_support_changing`。

这验证了一个重要边界：同规模跨地形合并后，安全壳没有把 Apollo 的不确定样本强行放行，而是保留在 DELAY_QUEUE。

## HIGH worker A/B

对 3 条 HIGH 候选执行 explicit opt-in target-priority worker A/B：

- 5-task no-regression：通过；
- 10-task no-regression：通过；
- 20-task baseline/worker：3 组均完成；
- official_bound_effect：false；
- certificate_ready：false。

ROI 审计结果：

- record_count：3；
- positive_primal_roi：0；
- negative_primal_roi：0；
- no_observed_roi：3；
- baseline status：均为 `TIME_LIMIT`；
- worker status：均为 `TIME_LIMIT`；
- baseline primal：548.335796；
- worker primal：548.335796；
- primal_improvement：0。

Reachability 审计结果：

- 3 条均为 `target_intervention_reachable`；
- 3 条均有 target causal match；
- worker 均在 expected context 返回 `FOUND_NEGATIVE`；
- training_label_allowed：true。

解释：这批 HIGH 不是“找不到负列”，而是“找到并注入了目标负列，但在当前 85 秒窗口内没有观察到 primal 改善”。它们应作为可达但无 ROI 的负样本，而不是生产正样本。

## v11 combined ROI 数据集

将 v10 combined 与 ord7 HIGH v11-only 合并：

- row_count：52；
- positive_primal_roi：18；
- negative_primal_roi：12；
- no_observed_roi：19；
- columns_only_roi：3。

构建 graph dataset：

- sample_count：49；
- `add`：18；
- `abstain`：31；
- skipped `columns_only_roi`：3；
- family_count：3；
- region_count：2；
- production_ready：false。

## v11 GAT 训练与安全壳

v11 GAT：

- sample_count：49；
- validation accuracy：0.75；
- validation add precision：0；
- validation add recall：0；
- diagnostic_only：true。

v11 kNN/OOD：

- predicted HIGH：1；
- HIGH precision：1.0；
- HIGH recall：0.0556；
- validation predicted HIGH：0；
- validation HIGH recall：0；
- negative recall delay queue：1.0；
- production_ready：false。

结论：合并同规模跨地形样本后，模型仍然非常保守。新增 ord7 数据让安全壳更倾向 DELAY_QUEUE，有助于避免误放行，但还没有解决正样本稀疏和 validation recall 问题。

## 当前判断

同一规模、不同地形的样本可以合并训练 GAT，但必须满足：

1. 输入保留地形/区域/族/ordinal 条件；
2. validation 必须按 region/family/ordinal 分层或 holdout；
3. 每个关键 region/family cell 至少要有正负 ROI 证据；
4. kNN/OOD 必须作为安全壳；
5. 没通过安全壳的 true-RC negative 只能 DELAY，不能丢弃；
6. GAT/kNN/OOD 不能证书，不能影响 official lower bound。

本轮 ord7 只补到了 3 条可达但无 ROI 的负样本，没有补到新的正 ROI。因此 v11 仍然不是生产模型。

## 下一步

继续采样时，不应盲目扩大同地形同 ordinal 的 HIGH A/B。更有效的方向是：

- 针对 Apollo random-wave 增加 target-reachable positive 样本；
- 针对 Tranq random-wave 继续寻找能产生 primal improvement 的 context；
- 对每个 region/family cell 保持正负样本平衡；
- 把 DELAY_QUEUE 作为 hard-negative pool，用来训练 GAT 不误放行“负 RC 但无收益”的列。

生产化条件仍未满足，20-task 200 秒精确求解目标也尚未达成。
