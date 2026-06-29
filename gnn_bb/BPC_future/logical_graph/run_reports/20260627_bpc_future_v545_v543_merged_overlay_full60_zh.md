# 20260627 V545 / V543 合并 Tree-Policy Overlay 全量 20 规模验证报告

## 结论摘要

本轮按 Branch Score 主线优化计划，完成了一个 exact-safe 的 state-scoped tree-policy overlay 验证版本：

- score map：`BPC_future/results/gat_branch_tree_policy_merged_overlay_v543_v467_plus_v540_20260627/journey_branch_score_rows.json`
- full60 结果：`BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/results.csv`
- 配置边界：只启用 branch score 排序；early branch 关闭；admission 关闭；learning pricing / dual anchor 继续开启。

V545 在 random-TW canonical 20-scale 60-instance 上达到：

| 版本 | OPTIMAL | TIME_LIMIT | EXTERNAL_TIME_LIMIT | capped mean | <=200s OPTIMAL |
|---|---:|---:|---:|---:|---:|
| baseline | 26/60 | 4 | 30 | 381.773895s | 20 |
| V468 current best | 33/60 | 3 | 24 | 348.261332s | 22 |
| V545 merged overlay | 36/60 | 3 | 21 | 341.542949s | 22 |

相对 V468：

- OPTIMAL 数：`33 -> 36`，新增 3 个完整闭环。
- capped mean：`348.261332s -> 341.542949s`，降低 `6.718383s/instance`。
- `<=200s OPTIMAL`：仍为 `22/60`，没有提升。
- `OPTIMAL -> non-OPTIMAL`：0 个。
- `non-OPTIMAL -> OPTIMAL`：3 个。

这说明：state-rehydrated branch replay 标签是有效的，能把少数 proof-tail 实例推到完整 OPTIMAL；但覆盖仍然太窄，所以还没有显著改善 200s 内闭环数量，p90/p95 仍然是 600s。

## 本轮实现内容

### 1. Strict Overlay 构建脚本

新增：

`BPC_future/scripts/apply_gat_tree_policy_strict_overlay.py`

用途：

- 将 strict tree-policy replay 事件覆盖到已有 branch score rows 上。
- 对严格正例提高分数，对 hard negative 压低分数。
- 对 depth > 0 的 replay 标签要求能恢复 `branch_state_key`；无法恢复时 fail-closed，不写入泛化 score。
- 输出 solver 可直接使用的 `journey_branch_score_rows.json/jsonl` 和 `journey_branch_score_map.json`。

exact-safe 元数据：

- `diagnostic_only=true`
- `production_ready=false`
- `runs_bpc_or_pricing=false`
- `official_bound_effect=false`
- `certificate_effect=false`

### 2. V540 state-rehydrated overlay

V540 从 V529 tree-policy event rows 中恢复深层 branch state：

- score row count：19931
- overlay events seen：84
- boost positive：31
- suppress negative：53
- appended overlay row：72

V541 smoke3 验证：

- seed61001：OPTIMAL 546.28s
- seed61309：OPTIMAL 465.06s
- seed61513：OPTIMAL 358.40s

这证明 deep branch-state replay 在已覆盖上下文中能复现成功路径。

### 3. V543 合并 overlay

V540 单独替换 V467 会丢掉 V467 已证明有效的 root score，导致 seed61000 回归。因此构造 V543：

- 输入 1：V467 conservative root overlay
- 输入 2：V540 state-rehydrated tree overlay
- 输出：V543 merged overlay

V543 summary：

- score row count：20768
- score >= 0.67：44
- score >= 0.85：30
- recommended min score：0.67
- recommended require state key：true
- production_ready：false

V544 smoke4：

- 4/4 OPTIMAL
- 包括 V468 已解的 seed61000，以及 V540 覆盖的 seed61001 / seed61309 / seed61513。

### 4. V545 full60 配置

V545 使用 V543 score rows：

- `journey_branch_candidate_priority=branch_score_horizon`
- `journey_branch_candidate_score_selection_gate_enabled=True`
- `journey_branch_candidate_score_selection_gate_min_score=0.67`
- `journey_branch_candidate_score_selection_gate_require_score_source=True`
- `journey_branch_candidate_score_require_state_key=True`
- `journey_branch_candidate_log_top_n=200`

显式关闭：

- `journey_early_branching_enabled=False`
- `journey_early_branching_after_incomplete_no_column_enabled=False`
- `journey_tail_action_early_branch_enabled=False`
- `journey_tail_action_no_column_early_branch_enabled=False`
- `journey_tail_action_no_column_early_branch_before_final_probe_enabled=False`
- `journey_gat_admission_scheduler_enabled=False`

因此 V545 的收益只来自 branch pair ordering，不来自 early branch，也不来自 admission。

## Full60 结果细节

### 相对 V468 的 3 个新增闭环

| instance | V468 | V545 | capped gain |
|---|---:|---:|---:|
| `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001` | EXTERNAL 600.020s | OPTIMAL 553.215s | +46.785s |
| `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309` | EXTERNAL 600.017s | OPTIMAL 470.458s | +129.542s |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513` | EXTERNAL 600.019s | OPTIMAL 360.178s | +239.822s |

这 3 个都是完整求解闭环，不是预测指标。

### 相对 V468 的退化

没有 `OPTIMAL -> TIME_LIMIT/EXTERNAL_TIME_LIMIT`。

秒级退化主要发生在原本已经 OPTIMAL 的实例上：

- sector/apollo seed61408：慢 5.54s
- sector/tranquillitatis seed61821：慢 5.47s
- greedy/apollo seed61716：慢 4.37s
- random/tranquillitatis seed61411：慢 4.02s
- greedy/apollo seed61614：慢 3.91s

这些退化没有破坏最优性，只影响 wall time。

### 相对 V468 的 win/loss/tie

- `gain > 1s`：9 个
- `loss > 1s`：10 个
- `abs(diff) <= 1s`：41 个
- `gain > 30s`：3 个
- `gain > 100s`：2 个
- `loss > 30s`：0 个

总体收益主要来自 3 个状态转化，而不是普遍加速。

## Branch Score 日志审计

V545 full60 日志：

- `journey_branch_candidates`：566
- `journey_branch`：566
- `journey_child_queued`：1132
- selected pair changed：26
- selected score present：68
- selected score >= 0.67：37
- selected score >= 0.85：29
- early branch trigger：0
- admission scheduler event：0

日志中存在 `journey_tail_action_no_column_early_branch_gate` 审计事件，但 early branch 配置关闭，没有真正触发提前分支。

### 转化实例的 score 命中

`random-wave/tranquillitatis seed61001`：

- branch count：19
- score gate passed：3
- selected pair changed：3
- root：`[5,19]`
- depth 1 same child：`[8,12]`
- depth 1 separate child：`[13,19]`

`random-wave/tranquillitatis seed61309`：

- branch count：14
- score gate passed：14
- selected pair changed：10
- root：`[2,5]`
- 后续多层 branch state 都由 state-rehydrated overlay 命中。

`sector-wave/tranquillitatis seed61513`：

- branch count：12
- score gate passed：12
- selected pair changed：5
- root：`[3,19]`
- depth 1 / depth 2 / depth 3 都有 state-scoped score 命中。

这说明真正有效的不是单个 root pair，而是一条能覆盖后续 child state 的 branch policy path。

## 为什么会是这个结果

### 1. V543 起作用的原因

V468 的主要能力是 root-level 保守 score overlay。它能在部分实例上选择更好的 root Ryan-Foster pair，所以相对 baseline 已经明显提高。

V540/V543 新增的是深层 state-rehydrated tree-policy label。它解决的是另一个问题：root pair 选对以后，子节点还需要继续选择合适的 pair，否则 proof tail 仍可能在子树中爆炸。

V545 的 3 个新增闭环都出现在 state-scoped score 连续命中的实例上，说明“branch policy path”比“单点 root pair”更接近真实因果。

### 2. 为什么收益还不够大

覆盖太窄。

566 次 branch decision 中，只有 68 次有 selected score，只有 37 次达到 0.67 阈值。大量节点仍然回退到 baseline Ryan-Foster 规则。

这意味着 V545 不是一个泛化模型，而是一个严格 gated 的 replay overlay。它能安全复现已知好路径，但不能在陌生 state 上主动创造新路径。

### 3. 为什么 `<=200s OPTIMAL` 没有提升

新增 3 个 OPTIMAL 的时间分别是 553s、470s、360s，都仍在 200s 之外。

这说明当前 branch score 确实降低了 proof tail 的失败率，但还没有把 certificate path 压缩到 200s 内。要做到 200s，光靠已知 replay path 不够，还需要继续降低子树证明成本、child ordering 和 final certificate CPU。

### 4. 为什么 exact-safe 没被破坏

本轮学习组件只改变 Ryan-Foster branch pair 的排序：

- 不生成 official bound。
- 不生成 certificate。
- 不使用 RMP objective 剪枝。
- 不启用 early branch。
- 不启用 admission。

所有 OPTIMAL 仍由原 exact pricing closure 和 BPC 逻辑证明。

## 当前问题

1. 正例路径太少，且集中在少数 family/context。
2. 现有 GAT score-map 仍主要靠 overlay/replay，不是稳定泛化。
3. root pair 正例不够，deep child policy 更不够。
4. 现有目标改善的是 600s 内闭环数量和 capped mean，不是 200s 内快速闭环。
5. 仍有 21 个 EXTERNAL_TIME_LIMIT，说明 proof tail 远没有解决。

## 下一步优化方向

### A. 继续主攻 branch policy path，不回到 admission 主线

V545 已证明 branch score 主线能产生真实完整求解收益。admission 本轮关闭，仍然能从 33/60 提到 36/60，因此主线应该继续放在 branch decision / child proof cost。

### B. 扩大 state-scoped replay 数据

优先补以下标签：

- root pair
- child pair
- branch_state_key
- child status
- child proof CPU
- child time to certificate
- child completion-bound retries
- selected path 是否最终闭环

目标不是“更多孤立正例”，而是更多可复现的 branch policy path。

### C. 训练时从单 pair 分类改成 path-aware ranking

V545 说明单个 pair 的标签不够。训练目标应更接近：

- 同一 node/context 下，好 pair 比差 pair分数高。
- 同一 instance/family 下，能让子树更快闭环的 path 分数更高。
- 对 553s/470s/360s 这种 OPTIMAL 转化给正权重，即使没有进 200s。

200s 只能作为评估指标，不应作为正例硬门槛。

### D. score gate 保留，但增加覆盖分层

当前 gate 很安全，但太保守。建议分三档：

- strict replay：`score >= 0.85`，state key 完整，允许深层命中。
- conservative root：`score >= 0.67`，只在 root 或已验证 family 使用。
- model-generalized：需要单独标记 `production_ready=false`，只用于 smoke/diagnostic，不进入主 benchmark。

### E. 专门分析剩余 21 个 EXTERNAL

对每个失败实例分类：

- score 缺失，完全回退 baseline；
- root score 命中但 child policy 缺失；
- child score 命中但证明仍慢；
- z_RMP/UB gap 问题；
- final pricing certificate 太慢；
- branch tree 太宽。

这一步比继续盲目增加样本更重要。

## 验收状态

本轮达到：

- 20-scale capped mean 相对 V468 继续降低。
- 20-scale OPTIMAL 数从 33/60 提高到 36/60。
- 无 OPTIMAL -> non-OPTIMAL 硬退化。
- exact-safe 边界保持清楚。

本轮未达到：

- 20-scale 全量 60/60 OPTIMAL。
- 所有 20-scale 实例 200s 内最优。
- `<=200s OPTIMAL` 提升。

因此 V545 是一个有效的中间进展，不是最终目标完成。
