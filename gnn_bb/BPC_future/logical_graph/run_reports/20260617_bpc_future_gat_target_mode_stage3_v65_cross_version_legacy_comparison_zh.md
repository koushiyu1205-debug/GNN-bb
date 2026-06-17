# 2026-06-17 BPC_future GAT Stage 3 v65 跨版本旧新对比综合报告

## 目的

根据最新要求，本轮不只看 v60-v64 的最近结果，也回看 v15 之后的关键版本，确认哪些旧理解仍成立、哪些已经被后续证据细化，以及当前真正的问题是否发生了转移。

本报告只读已有报告、dataset / audit 产物和当前 Stage 3 诊断结论，不运行 BPC、pricing、RMP、worker 或 certificate。

## Exact-safe Boundary

边界保持不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能用于 discovery、ordering 和 finite-delay admission scheduling。进入 RMP 的列仍必须 true-RC verified；delay queue 只能有限延迟，不能永久 reject；最终 optimality certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 版本线索

| version | 当时主要结论 | 现在的更新理解 |
|---|---|---|
| v15 / v30 / v32 / v43 | high-ROI missed 不是阈值差一点；`near_threshold_miss_count=0`，存在 candidate-head score gap 和 embedding structural gap。 | 仍成立，但不是完整解释。v55 后 raw score 接近阈值的样本变多，说明模型有进步；新 blocker 转向 context-local 正负排序和 delay-risk admission 的组合失败。 |
| v23 / v24 / v28 | boost high-ROI 会拉高 coverage，但 false-delay 爆；delay suppression / risk-adjusted scoring 能压 false-delay，但 coverage / CI 不足。 | 证明了高 ROI 覆盖和 delay-safe 之间存在 Pareto 张力。后续版本没有靠 loss multiplier 消掉这个张力。 |
| v36 | ROI-neighbor repair 把问题收敛到少数 context，如 `b6d808`、`79fde`、`ac15`。 | 方向正确，但早期 opportunity 口径偏粗。后续 A/B 显示 `b6d808` 更像 workload-only / ambiguous，不应再当 high-ROI anchor。 |
| v39 / v41 | neighbor-ROI + hard-negative 后 coverage 回升，但 44 个 false high-priority on delay 全集中在 `sector-wave|20` 的 5 个 context。 | blocker 不是全局噪声，而是少数 context 内 candidate action ranking 失败。candidate threshold 为 0 时，candidate head 实际失效，delay gate 被迫单独过滤。 |
| v44 / v45 / v46 | delay-safe shell 存在；smoke 可把 false-delay 压到 0，但 full coverage 后 false-delay 复发。 | 安全壳不是没有，而是太窄。只扫 threshold 会在“低覆盖安全”和“高覆盖 false-delay 爆”之间摆动。 |
| v50 | 高 false-positive context-batch A/B 全部无正 trajectory ROI；即时 objective movement 和 columns delta 会误导。 | 仍支持“不能用短视指标当 HIGH_PRIORITY 标签”。但 context-batch 标签过粗，后续 v53 证明同 context 内仍可能有 positive individual target。 |
| v51 / v52 / v56 | 存在 false-delay-safe epoch，也存在 coverage-ready epoch，但没有 epoch 同时满足二者。 | checkpoint selector 不是主 blocker。继续换 best epoch 规则不能把模型推进 Stage 4。 |
| v53 / v54 / v55 | individual follow-up 增加 9 条同 context target，v54 dataset ranking-ready，v55 仍不过 gate。 | v53 不是无效数据，但只补了少数 `sector-wave|20` 个体标签，不能泛化修复 coverage/safety tradeoff，也没有覆盖 random-wave 盲区。 |
| v57 / v58 / v59 / v60 | frontier 0 feasible；32 个 high-ROI 只 accepted 3 个；v60 focused pairs raw pass 1/4。 | 不能把下一步简化成调低 delay penalty。raw candidate head 在 `79fde/ac15` 同 context 正负 target 上本身就没稳定排对。 |
| v61 / v62 / v63 / v64 | 当前输入欠指定；trace/timing/resource payload 已可取；v64 把 candidate scalar schema 从 14 维扩到 36 维。 | 新方向从“调参”转成“补 action-consequence 表示”。v64 只是 schema smoke，还没证明训练后的 ranking / safety / Stage 4 readiness 改善。 |

## 新理解

### 1. 旧结论没有被推翻，而是被分层了

早期 v15 的结论是 missed high-ROI 不接近阈值，candidate head / embedding 分不开。这个判断对当时数据成立，也解释了为什么不能直接降 threshold。

但 v57-v60 之后，问题形态更细：v55 的很多 missed high-ROI 在 raw score 上已经接近阈值，表面像 delay-risk 过强；v60 又证明 focused individual pairs 的 raw ranking 仍只有 `1 / 4` 过。也就是说，当前不是单一“分数太低”，而是：

```text
candidate head context-local ranking 不稳
+ delay-risk / risk-adjusted admission 把一部分近阈值 positive 压掉
+ 高覆盖时 false-delay hard-negative 又会回流
```

### 2. context-level 标签只能定位区域，不能作为最终训练标签

v50 对 5 个 false-positive context-batch 的 A/B 结论很有价值：这些区域整体不应直接进 HIGH_PRIORITY。

但 v53 拆 individual target 后，`79fde658840fe2b8` 同 context 内同时出现 negative primal target 和 positive primal target。由此得到的新规则是：

```text
context-batch A/B 用于定位 hard region；
admission label 必须落到 individual target / signature / trace 粒度。
```

否则会把同 context 的正目标也贴成 hard-negative，污染 candidate head 排序。

### 3. `ac056`、`79fde`、`ac15` 的角色要分开

`ac056820151e9ad7` 是 v41 最大 false-positive cluster，v53 拆出的 3 个 target 都是 `negative_retry_roi`。它适合做 retry / delay hard-negative source，但没有 positive counterpart，不能单独训练“positive > negative”的排序。

`79fde658840fe2b8` 有正负 individual target，是当前最直接的 context-local ranking 反例。

`ac15bc4e7e3d6fff` 暴露 workload/retry signal 和 primal trajectory 的冲突，说明 columns delta、retry 改善或 true-RC negative 不能自动等价于 HIGH_PRIORITY。

### 4. random-wave 仍是独立盲区

v53 主要补 `sector-wave|20` false-positive context。v55 / v58 仍显示 random-wave high-ROI：

```text
high_roi = 6
accepted = 0
```

所以后续若只围绕 sector-wave hard-negative 修，会继续留下 random-wave family holdout 失败。下一批数据需要补 random-wave same-context positive / negative contrast，尤其是 v15/v43 中 nearest negative closer 的 missed high-ROI context。

### 5. “安全壳太窄”比“没有安全阈值”更准确

v44、v45、v56 共同说明 delay-safe threshold/epoch 是存在的，但 accepted batch 太少，CI 不可信；一旦 coverage 拉上来，false-delay 又回到约 `0.45` 量级。

因此当前不能把问题描述为 threshold 没扫够。更准确的 blocker 是：

```text
模型尚未学会在高覆盖区域内区分
trajectory-positive true-RC negative
和 trajectory-delay / retry hard-negative true-RC negative。
```

### 6. v64 是必要输入修复，但还不是效果证明

v62 证明 focused pairs 在粗输入上不完全碰撞，但 3/4 pair 仍 raw misrank；v63 证明 trace/timing/resource payload 9/9 可取；v64 因此把 22 个 trace scalar features 接入 dataset schema。

这解决的是“模型有没有机会看到更多 action-consequence 信息”的一部分问题。它还没有证明：

- v55 / v57 false-delay blocker 被修复；
- focused ranking 从 `1 / 4` 改善；
- random-wave high-ROI 被捕获；
- kNN/OOD holdout 过；
- Stage 4 mutating admission 可启用；
- Stage 5 20-task `OPTIMAL < 200s` 成立。

## 当前问题

1. candidate head 在同 context individual 正负 target 上仍缺少稳定 raw ranking 能力。
2. delay-risk head 能产生安全壳，但安全壳覆盖太窄，不能过 Stage 3 CI / coverage gate。
3. 高覆盖 epoch 与 false-delay-safe epoch 分离，checkpoint selection 不是主 blocker。
4. random-wave high-ROI 仍未被最近的 v53/v64 路线覆盖。
5. 当前 v64 只补了 trace scalar，仍缺 `task_time_window_slack`、per-candidate branch/cut coefficients、active basis overlap、candidate signature embedding / tokenized path sequence。
6. true-RC negative、exact safe-id hit、columns reduction、即时 RMP objective movement 都不能作为 HIGH_PRIORITY 充分条件。
7. Stage 4/5 仍未满足：不能默认启用 mutating admission，也不能报告 exact proof acceleration。

## 下一步建议

1. 用 v64 schema 重建 v54/v51 历史完整 dataset，再训练新 checkpoint，重新跑 v57-v60 同类审计。
2. 新 checkpoint 的第一关不是全局 ROI point，而是 focused context ranking：
   - `79fde` positive target 必须排在同 context hard-negative 前；
   - `ac15` positive target 必须排在同 context hard-negative 前；
   - raw candidate score、risk-adjusted admission score、delay-risk score 都要分别报告。
3. 不直接降低 delay penalty。若 raw candidate head 没先排对，降低 delay penalty 会把 retry / delay hard-negative 放回 HIGH_PRIORITY。
4. 数据采集补两条线：
   - `ac056` 同 context positive counterpart；
   - random-wave missed high-ROI same-context positive / negative contrast。
5. v64 后继续补尚缺输入：
   - task time-window slack；
   - per-candidate branch/cut interaction；
   - active basis coefficient overlap；
   - candidate signature / arc-option token sequence。
6. Stage 4 继续保持 shadow / opt-in A/B；任何 mutating admission 前必须通过 precision / ROI / false-safe / coverage / CI / kNN-OOD / 5-10 no-regression / 20-task repeat ROI gate。

## 结论

跨版本对比后的新判断是：当前瓶颈已经从“GAT 能不能找到 true-RC negative / exact hit”转为“GAT 能不能在同一 RMP context 下，把真正改善 trajectory 的 true-RC negative 排到会拖尾的 true-RC negative 前面”。

v64 的 trace-feature schema 是正确的下一步，因为它补的是 action-consequence 输入，而不是继续在旧 14 维 scalar 上调 threshold。但它只是前置修复，必须通过完整 dataset 重训和 focused ranking / frontier / kNN-OOD / Stage 4 shadow 重新验证后，才能判断是否真正改变 v15-v60 反复出现的 coverage/safety tradeoff。

```text
v65_runs_bpc_or_pricing = false
v65_changes_solver_behavior = false
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
