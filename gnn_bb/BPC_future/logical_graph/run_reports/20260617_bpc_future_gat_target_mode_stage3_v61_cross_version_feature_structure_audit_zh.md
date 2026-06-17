# 2026-06-17 BPC_future GAT Stage 3 v61 Cross-version Feature/Structure Audit

## 读取范围

本轮按目标模式重新对比了：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- `BPC_future/docs/gat_roi_gate_optimization_handoff_zh.md`
- Stage 1 模型结构报告与 Stage 2 数据采集报告
- Stage 3 v36 / v41 / v44 / v45 / v50 / v51-v52 / v54-v56 / v57-v60
- Stage 4 v53 individual follow-up execution / reachability / A-B ROI / certificate audit
- Stage 5 20/30/50/100 exact-safe acceleration 目标
- 当前 `batch_impact_model.py` 与 `build_gat_batch_impact_dataset.py` 的候选特征和模型输入

边界保持不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能用于 discovery、ordering 和 finite-delay admission scheduling。进入 RMP 的列仍必须 true-RC verified；delay queue 只能有限延迟，不能永久 reject；最终 optimality certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 跨版本证据链

| version | 当时理解 | v61 后的更新判断 |
|---|---|---|
| v36 | ROI-neighbor repair 把问题收敛到少数 context，尤其 `b6d808`、`79fde`、`ac15`。 | 方向正确，但 early opportunity 口径偏粗；后续 A/B 证明部分 context 只能做 hard-negative / ambiguous。 |
| v41 | v39 的 44 个 false high-priority on delay 全部集中在 `sector-wave|20` 的 5 个 context。 | blocker 不是全局噪声，而是 context-local action ranking 失败。 |
| v44 | delay-safe shell 存在，但最多只接受 2 个 batch。 | 安全阈值不是不存在，而是安全壳覆盖太窄。 |
| v45/v46 | false-delay contrast 能把 false-delay 压下去，但 full coverage 后复发。 | loss 局部有效，但不能解决高覆盖和 delay-safe 同时成立的问题。 |
| v50 | 高 false-positive context-batch A/B 全部无正 trajectory ROI，`79fde/ac15` 被视为 hard-negative context。 | context-batch 标签过粗；v53 后发现 `79fde` 内存在 positive individual target。 |
| v51/v52 | 新 hard-negative 回流后出现 false-delay safe epoch，但没有 epoch 同时 coverage-ready 和 false-delay-safe。 | checkpoint selection 不是主 blocker；继续换 best_epoch 规则不能推进 Stage 4。 |
| v54-v56 | v53 individual rows 提高 same-context 正负对照密度，但 v55 仍不过 gate。 | v53 数据不是无效，但还没有改变模型的 coverage/safety tradeoff。 |
| v57-v60 | full frontier 0 feasible；v58 29/32 high-ROI missed；v60 focused pairs raw pass 1/4。 | 下一步不能简化为调 delay penalty。candidate head 在同 context 正负 target 上本身就没稳定排对。 |

## 最新关键事实

### 1. v53 修正了旧版 context-level 标签

v50 的 context-batch 结论曾把 `79fde658840fe2b8` 整体视为 negative primal context。v53 拆 individual target 后发现：

```text
79fde / 1,15,17       = negative_primal_roi
79fde / 12,4,13,5    = negative_primal_roi
79fde / 12,4,19,13   = positive_primal_roi
```

所以训练标签必须保留 target sequence / signature / materialized trace 粒度。只按 context hash 或 batch hash 贴 hard-negative 会误伤同 context 的正目标。

### 2. v60 说明问题不只是 delay-risk 太保守

v58/v59 表面上显示很多 missed high-ROI 被 delay-risk / risk-adjusted admission 压掉：

```text
high_roi_opportunities = 32
accepted_high_roi_opportunities = 3
missed_high_roi_opportunities = 29
risk_adjusted_suppressed_miss_count = 27
```

但 v60 聚焦 v53 individual rows 后显示：

```text
pair_count = 4
raw_pair_pass_rate = 0.25
admission_pair_pass_rate = 0.5
strict_pair_pass_rate = 0.25
primary = candidate_head_context_ranking_failure
```

这意味着只降低 delay penalty / 放宽 rescue window 会把 hard-negative 一起放回 HIGH_PRIORITY。候选头的 context-local raw ranking 先要过关。

### 3. `ac056` 已经从 opportunity 转成 retry hard-negative source

`ac056820151e9ad7` 是 v41 最大 false-positive cluster。v53 拆出的 3 个 individual target 全是 `negative_retry_roi`，没有 positive counterpart：

```text
20,16        = negative_retry_roi
15,5,16,7,3 = negative_retry_roi
15,20       = negative_retry_roi
```

它适合训练 delay / retry hard-negative，但不能单独训练正负排序。若继续围绕 `ac056`，必须采同 context positive counterpart，否则只会继续把安全壳收窄。

### 4. random-wave 盲区仍未被 v53 修复

v55 / v58 继续显示：

```text
random-wave high_roi = 6
random-wave accepted = 0
```

v53 主要覆盖 `sector-wave|20` 的 false-positive context，不能解释 random-wave 6/6 missed。下一批数据必须补 random-wave same-context positive/negative contrast，否则 family holdout 仍会失败。

## 当前模型输入的结构缺口

当前 `JourneyCandidateEncoder` 能看到：

- task GAT embedding；
- candidate task membership；
- candidate sequence positions；
- set / order / first / last pooled task embedding；
- 14 维 candidate scalar features；
- shared context embedding；
- batch-level pooled embedding。

当前 batch-impact candidate feature schema 是：

```text
true_reduced_cost, cost, task_count, vehicle_count,
new_task_set, strict_replacement_by_cost, weak_replacement_or_duplicate,
duplicate_signature, duplicate_signature_pool_count_before,
task_set_pool_count_before, sequence_length, sortie_count,
order_observed, best_position
```

其中 `strict_replacement_by_cost` 当前固定返回 `0.0`；`best_position` 对正常候选几乎总是 `1.0`；`order_observed` 在 v53 focused rows 中都是 `1.0`；signature id 只写入 sample metadata，不作为模型输入。

这解释了 v60 的现象：模型知道“覆盖哪些 task”和粗序列位置，但缺少更直接的 action-consequence 特征：

- arc-option / path-option 类型序列；
- start time / sortie timing / multi-trip gap；
- time-window slack / energy slack / load slack；
- per-leg travel / service / energy / risk aggregate；
- candidate signature embedding；
- candidate 与 active basis / pool 的具体 overlap；
- per-candidate branch/cut coefficient interaction；
- candidate 加入后可能触发的 RMP degeneracy / retry / proof-tail proxy。

因此 `79fde/ac15` 这种“同 context、同为 true-RC negative，但一个改善 trajectory、另一个拖尾”的情况，当前输入很可能欠指定。

## 新理解

### 1. 旧问题不是被推翻，而是被细化了

早期结论“不是阈值差一点”仍成立。但 v59 显示 v55 的 raw score 已比 v15 接近阈值，说明模型有进步；真正的新问题是 raw score 接近仍不够，因为 focused context 内正负 target 的相对排序没稳定成立。

### 2. context-local individual attribution 是必要条件

v50 证明 context-batch A/B 能发现有害区域；v53 证明 context-batch 标签会误伤正目标。之后的数据采集必须采用 same-context individual attribution，否则会同时污染 positive 和 hard-negative label。

### 3. 高覆盖安全区缺失不是 checkpoint selector 问题

v52 和 v56 都显示：

```text
coverage_and_false_delay_safe_epoch_count = 0
```

因此继续只改 checkpoint selection、validation loss 排序、threshold frontier 搜索，不能把 checkpoint 送进 Stage 4。

### 4. true-RC negative / exact hit / columns reduction 都不是 HIGH_PRIORITY 充分条件

v38/v40/v50/v53 共同支持这个判断：即时 objective improvement、columns delta、exact safe-id hit、best true-RC 都可能和 final trajectory ROI 冲突。HIGH_PRIORITY 标签必须继续绑定 RMP trajectory、tail retry、pricing workload 和 proof-tail 后果。

### 5. Stage 4/5 仍未满足

当前只有 diagnostic / shadow / opt-in A/B 证据。Stage 4 mutating admission 还不能默认启用；Stage 5 要求的 20-task agreed matrix `OPTIMAL < 200s`、official dual bound available、exact pricing closure proof source 仍未满足。

## 当前问题列表

1. candidate head 在 `79fde/ac15` focused pairs 上 raw ranking 不稳。
2. delay-risk head 可以形成安全壳，但 accepted coverage 远不足以过 Stage 3 CI gate。
3. v53 individual rows 增加了 pairwise 密度，但数据规模和 family 覆盖不足。
4. random-wave high-ROI 仍是 0 accepted blind spot。
5. 当前 candidate schema 缺少 path-option / timing / slack / basis-overlap / branch-cut interaction / signature embedding。
6. context-level 标签会误伤 individual positive target。
7. 20-task 仍是 `TIME_LIMIT` / `dual_bound=None` 的诊断区，不能报告 exact proof improvement。

## 下一步

1. 先做 feature/structure gap 的可量化审计，不要直接再扫 threshold：
   - 固定 `79fde/ac15` focused pairs；
   - 比较正负 target 在 candidate scalar features、sequence positions、signature metadata、context/batch features 上的可分性；
   - 明确哪些信息只在 metadata/log 中，未进入模型输入。
2. 增加 focused regression gate：
   - `79fde positive > 79fde hard-negative`；
   - `ac15 positive > ac15 hard-negative`；
   - 这个 gate 先作为 diagnostic，不作为 production admission gate。
3. 数据侧补两类样本：
   - `ac056` 同 context positive counterpart；
   - random-wave missed high-ROI 的 same-context positive/negative contrast。
4. 模型侧优先考虑候选输入增强，而不是单纯 loss multiplier：
   - candidate signature / trace encoder；
   - arc-option / timing / slack aggregate；
   - active basis / pool overlap；
   - per-candidate branch/cut interaction；
   - trajectory-tail proxy features。
5. Stage 4 只继续 shadow / opt-in A/B；任何 mutating admission 前仍需通过 5/10 no-regression、20-task repeat ROI、kNN/OOD holdout、certificate safety。

## Exactness Boundary

```text
v61_runs_bpc_or_pricing = false
v61_changes_solver_behavior = false
production_ready = false
default_enabled = false
stage4_candidate_ready = false
stage5_ready = false
certificate_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

最终证明仍必须由当前 branch/cut/dual 下 exact pricing exhaustive no-negative closure 产生；本报告只用于 Stage 3 diagnostic 和下一轮数据/模型结构修复。
