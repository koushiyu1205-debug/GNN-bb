# 20260627 V546 / V548 失败实例 Branch Policy 负结果报告

## 结论摘要

本轮在 V545 之后尝试了两条扩大 branch policy 覆盖的路线：

- V546：对 V545 剩余失败实例做 root-level alternative pair forced full replay。
- V548：用 V545 已成功实例聚合出的 family/site/depth tree policy 去跑一批 tranquillitatis 失败实例。

结果都没有产生新的可训练正例：

| 实验 | 有效样本 | OPTIMAL | TIME_LIMIT | EXTERNAL_TIME_LIMIT | capped mean |
|---|---:|---:|---:|---:|---:|
| V546 root-alt forced replay | 16 | 0 | 0 | 16 | 600.021389s |
| V548 family/site/depth policy smoke | 11 | 0 | 0 | 11 | 600.020679s |

因此，这两条扩展方式不应继续大规模跑完：

1. 只替换 root 的前两名 alternative pair，不能稳定打开剩余失败实例的闭环路径。
2. 从成功实例直接聚合 family/site/depth 偏好，泛化粒度过粗，无法替代 state-scoped branch policy。
3. 当前 V545 的有效收益来自“具体 branch state 上连续命中 score 的路径”，不是来自某个通用 family 的固定 pair 偏好。

这一步没有改变 exact-safe 边界：所有尝试只改变 branch pair 排序或强制 replay，不提供 official bound，不提供 certificate，不剪枝。

## 背景：V545 当前位置

V545 使用 V543 合并 overlay，只打开 branch score 排序，关闭 early branch 和 admission。

在 20-scale random-TW canonical 60-instance 上：

| 版本 | OPTIMAL | TIME_LIMIT | EXTERNAL_TIME_LIMIT | capped mean | <=200s OPTIMAL |
|---|---:|---:|---:|---:|---:|
| baseline | 26/60 | 4 | 30 | 381.773895s | 20 |
| V468 current best | 33/60 | 3 | 24 | 348.261332s | 22 |
| V545 merged overlay | 36/60 | 3 | 21 | 341.542949s | 22 |

V545 相对 V468 多解出 3 个实例，且没有 `OPTIMAL -> non-OPTIMAL` 硬退化。说明 state-scoped branch replay label 是有效信号。

但 V545 仍有 24 个 20-scale 实例没有在 600 秒内闭环，且新增的 3 个 OPTIMAL 分别在约 553s、470s、360s 才闭环，`<=200s OPTIMAL` 没提升。这说明当前 score map 能降低一部分 proof-tail 失败率，但还没有把证书路径压到 200 秒以内。

## V546：root-alt forced full replay

### 设计

runbook：

`BPC_future/results/journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_20260627/runbook.json`

报告：

`BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_branch_candidate_replay_runbook_v546_v545_failed_root_alt2_zh.md`

配置要点：

- 输入：V545 剩余失败实例的 branch candidate events。
- 深度：只取 `depth=0`。
- 每个 root event 取 2 个 alternative pair。
- replay 模式：`full_replay`，600 秒外部时限。
- 计划条目：42 个。

### 实际结果

有效完成 16 个 replay，全部外部超时：

| entry | instance | forced pair | status |
|---|---|---|---|
| 001 | `apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103` | `[1,5]` | EXTERNAL_TIME_LIMIT |
| 002 | `apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103` | `[1,10]` | EXTERNAL_TIME_LIMIT |
| 003 | `apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308` | `[2,3]` | EXTERNAL_TIME_LIMIT |
| 004 | `apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308` | `[2,6]` | EXTERNAL_TIME_LIMIT |
| 005 | `apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410` | `[7,15]` | EXTERNAL_TIME_LIMIT |
| 006 | `apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410` | `[7,17]` | EXTERNAL_TIME_LIMIT |
| 007 | `apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512` | `[1,4]` | EXTERNAL_TIME_LIMIT |
| 008 | `apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512` | `[1,8]` | EXTERNAL_TIME_LIMIT |
| 009 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206` | `[3,5]` | EXTERNAL_TIME_LIMIT |
| 010 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206` | `[3,9]` | EXTERNAL_TIME_LIMIT |
| 011 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311` | `[1,13]` | EXTERNAL_TIME_LIMIT |
| 012 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311` | `[1,19]` | EXTERNAL_TIME_LIMIT |
| 013 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520` | `[4,8]` | EXTERNAL_TIME_LIMIT |
| 014 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520` | `[4,9]` | EXTERNAL_TIME_LIMIT |
| 015 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635` | `[1,9]` | EXTERNAL_TIME_LIMIT |
| 016 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635` | `[1,12]` | EXTERNAL_TIME_LIMIT |

停止原因：

- 前 16 个有效样本已经是 `0/16 OPTIMAL`。
- 继续跑完剩余 26 个条目大概率只会增加 hard negative，不能有效补强正例。
- 停止时还有 12 个已创建但为空的 `results.csv`，这些不计入有效训练样本。

### 解释

V546 说明剩余失败实例不是简单的“root pair 第二选择没试到”。即使强制选择 root 的高 fractionality / near-tie alternative pair，仍然没有让完整 BPC 在 600 秒内闭环。

本质上，root pair 只决定第一层切分。V545 已经证明真正有效的实例通常需要后续 child state 也连续选对；如果深层 policy 没覆盖，root 强制 replay 很容易只是换一个同样难证的子树。

## V548：family/site/depth tree policy 泛化

### 设计

score map：

`BPC_future/results/journey_tree_policy_score_map_v547_v545_success_family_site_depth_20260627/`

报告：

`BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_tree_policy_score_map_v547_v545_success_family_site_depth_zh.md`

配置要点：

- 输入：V545 的 36 个 OPTIMAL 成功日志。
- key scope：`depth`。
- context scope：`family_site`。
- 输出：
  - branch score rows：124
  - child score rows：248
- early branch 关闭。
- admission 关闭。
- 启用 branch score 排序和 child score ordering。

### 实际结果

选择 11 个 V545 失败的 tranquillitatis 实例做 smoke，全部外部超时：

| instance | status |
|---|---|
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410` | EXTERNAL_TIME_LIMIT |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718` | EXTERNAL_TIME_LIMIT |

### 解释

V548 说明“同 family/site、同 depth 的成功 pair”不能直接迁移到失败实例。

原因不是 branch score 机制失效，而是泛化键太粗：

- Ryan-Foster pair 的好坏强依赖当前 fractional support、branch constraints、active columns、child width、completion-bound 风险。
- 只用 `family/site/depth` 会把不同 branch state 混在一起。
- 成功实例里的 pair 可能只是该 state 下有效，换到另一个 state 就不是低 proof-cost 分支。

因此，后续不能把成功日志简单聚合成宽泛 policy。必须保留更细的 state/context 特征，或者用 full replay / child proof-cost 反事实数据训练模型，而不是直接规则覆盖。

## 这两个负结果说明什么

### 1. Branch score 主线仍然成立，但要更强调 state-scoped 因果标签

V545 的 3 个新增 OPTIMAL 证明 branch score 是有效的；V546/V548 证明低信息量扩展无效。

可用信号必须满足至少一个条件：

- 同一个 branch state 或可恢复的近邻 state 上，某 pair 已经通过 full replay 证明能降低 wall time。
- 有 child proof-cost / time-to-certificate 观测，能说明该 pair 让两个 child 更容易完成 exact closure。
- 有可靠的 score gate，能避免在陌生 context 上盲目替换 baseline pair。

### 2. 当前瓶颈不是“再找更多 root pair”

V546 已经覆盖了 root alternative 的一批高 fractionality / near-tie 候选，但没有出现正例。继续把 root top2 扩成 top5/top10，边际价值会很低，成本很高。

更应该找的是：

- 哪些节点根本没有进入有效 branch 前就卡在 CG/final-probe；
- 哪些节点 branch 后 child proof cost 爆炸；
- 哪些节点是 incumbent 不够好，导致 LP bound 即使闭合也不能 fathom；
- 哪些节点需要 cuts/formulation，而不是分支排序。

### 3. 不能把粗粒度成功路径当成 production policy

V548 是一个明确反例：从成功样本提炼出的 family/site/depth 偏好，在失败样本上没有闭环收益。

这意味着 score map 必须继续保持 `production_ready=false`，并且 solver 侧必须继续要求 score source / state key 或其他强置信条件。

## 下一步修改方向

### A. 先做 V545 failure typing

对 24 个 V545 剩余失败实例分型，至少区分：

- root/final-probe proof tail：没有进入足够分支，主要卡在 exact pricing closure。
- branch tree too wide：进入分支但 child 数或证明成本过大。
- child proof-cost dominant：某些 child 反复 CB retry / exact pricing events 多。
- incumbent gap dominant：`z_RMP < UB`，即使 LP closure 也不能剪。
- score coverage missing：有分支机会，但 score map 没覆盖当前 state。

这一步比继续盲跑 forced pair 更重要，因为不同类型需要不同动作。

### B. branch score 训练改用 child proof-cost / full replay 严格标签

保留 V545 的 3 个强正例路径，V546 的 16 个 root-alt hard negative，V548 的 11 个泛化 hard negative。

但不要把 V548 这类粗粒度 policy 当成正向训练来源；它只能作为 hard negative / regression guard。

下一批正例应优先来自：

- full replay 确认的 `TIME_LIMIT/EXTERNAL -> OPTIMAL`；
- `gain >= 30s/100s` 的完整闭环加速；
- child proof CPU、time-to-certificate、completion-bound retry 明显下降的成对反事实。

### C. score-gated early branch 只在 failure typing 后测试

V545 的收益来自 branch ordering，不是 early branch。V546/V548 也没有证明裸 early branch 会有收益。

下一轮可以做 opt-in smoke，但必须按类型触发：

- CG 已拖尾，继续收列收益低；
- branch score 或 child proof-cost 模型有高置信 pair；
- child width / balance 受控；
- 子节点仍只继承合法旧 lower bound，不使用 RMP objective 剪枝。

如果 score 缺失或低置信，回退到正常 CG/final-probe。

### D. 对非 branch 可解瓶颈，不要继续用 branch score 硬顶

如果 failure typing 显示一批节点属于 `z_RMP < UB` 或系统性 relaxation 过松，那么 branch score 只能改善搜索顺序，不能把节点直接剪掉。

这些实例需要并行推进：

- incumbent improvement；
- pricing-compatible cuts；
- 更紧 master formulation；
- 更有效的 child lower-bound gain 分支。

## 当前验收状态

截至 V548：

- 5/10 小规模退化风险本轮未新增，因为 V546/V548 只在 20-scale 失败 smoke 上运行。
- 20-scale 当前最佳仍是 V545：
  - `36/60 OPTIMAL`
  - capped mean `341.542949s`
  - `<=200s OPTIMAL = 22/60`
- 距离最终目标仍很远：
  - 还差 24 个实例才能达到 `60/60 OPTIMAL within 600s`。
  - 还差大量证书路径压缩，才能达到用户目标的“20 规模所有实例 200 秒内最优”。

## 操作结论

不建议继续扩大 V546 root-alt forced replay 或 V548 family/site/depth policy。

建议下一步直接进入：

1. V545 24 个失败实例的 failure typing；
2. 基于分型选择少量 exact-safe score-gated early-branch smoke；
3. 将 V546/V548 负样本纳入 hard negative / regression guard；
4. 只把 full replay 或 child proof-cost 证实的路径作为下一版 branch score 正向标签。
