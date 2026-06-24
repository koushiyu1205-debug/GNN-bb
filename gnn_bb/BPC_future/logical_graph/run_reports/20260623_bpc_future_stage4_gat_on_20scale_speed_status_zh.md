# BPC_future Stage 4：GAT 开启后的 20 规模精确求解加速状态

日期：2026-06-23

## 问题

用户要求：GAT 不要关闭，要能在 20 规模精确求解中真正用上，并确认当前 20 规模是否已经加速。

## 结论

当前不能说 20 规模精确求解已经整体加速达标。

后续主效果口径必须使用分层 random-TW 60-instance 集合：

`BPC_future/logical_graph/tasks_020/...`

本报告中的 `greedy/apollo20` 指 canonical `tasks_020/greedy-anchor/apollo15_20km` 集合内的实例，不是旧 `moon_trek_60` hard-set。旧 hard-set 结果只能作为诊断补充，不能计入主 benchmark 效果结论。

20 规模后续运行时间口径分两层：per-instance 600s 可以作为诊断/采样预算，用来观察 tail；最终目标仍是 canonical `tasks_020` 的 60 个实例全部在 200s 内 `OPTIMAL`。

已验证的局部加速来自 `completion-bound tail` 修复，而不是 v154/GAT 本身：

- sector/apollo20 等 tail 受 `profile_labeling_task_set_superset_pruning` 影响的实例，禁用大规模证书阶段 superset pruning 后可以从 time limit 降到秒级最优。
- greedy/apollo20 仍未在 200s 内完成，是当前 20 规模目标的主要阻塞点。

GAT 当前没有关闭，且实际被用上了：

- `journey_learning` 为 `ENABLED`；
- root/branch CG 中持续执行 `journey_learning_true_rc_filter`；
- GAT/learning-smoothed heuristic 发现并加入 true-RC 负列；
- 但加入的列大多是 `changed_inactive_only`，对 LP active support 和 wall-time 收敛帮助有限。

## 新增的 opt-in GAT 后续 repair 接入

为避免 GAT 只产出 inactive-only 列后没有后续利用，本轮在 `journey_driver.py` 增加了 opt-in worker：

`journey_active_support_repair_after_inactive_addition_enabled`

触发条件：

- GAT/heuristic 或 exact 本轮确实加入了列；
- 加入列的 changed task sets 主要不在当前 active support；
- 当前有 active task sets；
- `journey_replacement_repair_enabled=True`；
- 默认仍关闭，不影响 exact certificate。

作用边界：

- 只作为 worker 尝试当前 active support 的物理代表替换；
- 不作为 pricing oracle；
- 不提供 certificate；
- 找不到列不会改变精确性。

## 70s 诊断：GAT + active-support repair

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/active_support_repair_gat_on_greedy_apollo20_trigger_diag70_v2/`

实例：

`tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，70.02s。
- 最大 CG 轮次：53。
- `journey_learning_true_rc_filter`：53 次。
- GAT/heuristic negative journeys：1104。
- GAT/heuristic 加入列：
  - `changed_inactive_only`: 110
  - `active_replacement_task_set`: 4
- ordinary exact 加入列：
  - `active_replacement_task_set`: 53
- 新 active-support repair：
  - 触发 8 次；
  - 总 profile generation time 约 8.218s；
  - `negative_journeys=0`；
  - 全部为 `INCOMPLETE_LIMIT/time_limit`。

解释：

GAT 确实参与了列生成，但新增 repair worker 当前配置下只是额外花时间，没有找到可加入负列，不能作为加速来源。

## 200s 当前配置探针：GAT 开启、不叠加 active repair

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_greedy_apollo20_current_direct200/`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，200.03s。
- root node 最大 CG：56。
- branch node 1 最大 CG：4。
- `journey_learning_true_rc_filter`：60 次。
- GAT/heuristic negative journeys：1182。
- GAT/heuristic 加入列：
  - `changed_inactive_only`: 112
  - `active_replacement_task_set`: 4
- ordinary exact 加入列：
  - `active_replacement_task_set`: 65
  - `changed_inactive_only`: 4
- root completion-bound retry：
  - 时间约 142.22s；
  - `CERTIFIED_NO_NEGATIVE`；
  - profile generation time 约 31.52s。
- 之后进入 branch node 1，并在 200s 外部时限前仍未完成。

解释：

GAT 开启后能提供大量 true-RC 负列候选，但大部分不改变 active support。当前总时间仍主要卡在：

1. root CG 后段反复产生弱/边界负列；
2. completion-bound certificate 收口约 31.5s；
3. root 结束后仍进入分支，branch node 继续触发 exact/CB 路径。

## 200s 分支 tail 探针：GAT 开启 + pre-exact handoff

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_branch_cb_handoff_greedy_apollo20_direct200/`

配置覆盖：

- `journey_certificate_completion_bound_pre_exact_handoff_enabled=True`
- `journey_certificate_completion_bound_pre_exact_handoff_disable_on_branch_depth_gt=1`
- `journey_certificate_completion_bound_pre_exact_handoff_min_flat_rounds=0`
- `journey_certificate_completion_bound_pre_exact_handoff_max_remaining=60.0`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，200.02s。
- JSONL 位置：
  `.../gat_on_branch_cb_handoff_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/...json.jsonl`
- root 仍在约 142.5s 完成 completion-bound certificate，之后进入 depth=1 branch node。
- `journey_certificate_completion_bound_pre_exact_handoff` 触发次数为 0。
- branch node 的 LP objective 仍低于 incumbent，不是 certificate candidate；pre-exact handoff 的当前触发条件主要面向 certificate candidate，所以没有形成可见加速。

解释：

这个探针说明，当前 greedy/apollo20 的 200s 阻塞不是简单“把 CB handoff 提前”就能解决。depth=1 节点还不能 fathom，handoff 条件不稳定，GAT 虽然开启但仍没有转化为整体最优证明时间减少。

## 200s 分支 tail 探针：GAT 开启 + depth=1 early-branch child3

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_early_branch_child3_greedy_apollo20_direct200/`

配置覆盖：

- `journey_early_branching_enabled=True`
- `journey_early_branching_min_cg_iter=999`
- `journey_early_branching_child_min_cg_iter=3`
- `journey_early_branching_max_depth=1`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，200.02s。
- JSONL 位置：
  `.../gat_on_early_branch_child3_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/...json.jsonl`
- root early-branch 被显式关掉，只允许 depth=1 子节点更早下放。
- `journey_early_branch_trigger` 在 node 1、depth=1、cg=3、约 152.30s 触发。
- node 1 被分成 `RF(2,3)=same_vehicle` / `RF(2,3)=separate_vehicle`，但随后优先处理 root sibling node 2。
- node 2 在约 193.82s 仍是 `exact INCOMPLETE`，reason=`partial_profile_scan_no_negative_journey`，外部 200s 超时。

解释：

这个探针说明，仅靠现有 exact-safe early-branch 触发点把 depth=1 的 branch tail 下放，还不足以让 greedy/apollo20 达到 200s OPTIMAL。后续如果继续做 early-branch，应改成可观测的 branch-tail 调度策略，并保留 JSONL 事件，而不是只调阈值。

## 200s 分支调度探针：GAT 开启 + depth=1 early-branch child3 + width priority

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_early_branch_child3_width_greedy_apollo20_direct200/`

配置覆盖：

- `journey_early_branching_enabled=True`
- `journey_early_branching_min_cg_iter=999`
- `journey_early_branching_child_min_cg_iter=3`
- `journey_early_branching_max_depth=1`
- `journey_child_priority_by_width_enabled=True`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，200.03s。
- root 仍约 142.56s 完成 completion-bound certificate。
- node 1 在 depth=1、cg=3 触发 early-branch。
- width priority 生效：随后优先处理更窄的 depth=2 child node 3，而不是 root sibling node 2。
- node 3 在 198.30s 仍为 `exact INCOMPLETE`，reason=`weak_negative_journeys_filtered`。

解释：

width priority 改善了节点调度方向，但没有解决子节点仍持续产生负列的问题。它把超时位置从 root sibling proof tail 移到了更窄 child 的 column-generation tail。

## 200s root 提前分支探针：GAT 开启 + root55 + child3 + width priority

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root55_child3_width_greedy_apollo20_direct200/`

配置覆盖：

- `journey_early_branching_enabled=True`
- `journey_early_branching_min_cg_iter=55`
- `journey_early_branching_child_min_cg_iter=3`
- `journey_early_branching_max_depth=1`
- `journey_child_priority_by_width_enabled=True`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，200.02s。
- root 在 cg=55、约 80.20s 因 `negative_columns_tailing` 提前分支，跳过了原路径 root retry/CB。
- 随后 node 1 在 depth=1、cg=3、约 127.33s 再次提前分支。
- depth=2 node 3 到 198.24s 仍持续发现 exact negative journeys，未进入闭合证明。

解释：

root55 确实省掉了 root 约 31.5s 的 completion-bound 收口，但分支过早，子节点仍有大量负列，200s 内没有闭合。

## 新增 opt-in：incomplete no-column tail 提前分支

为避免 root55 在仍有明显负列时过早下放，本轮新增默认关闭的触发点：

`journey_early_branching_after_incomplete_no_column_enabled`

作用：

- 仅在 exact pricing `not exhausted`、本轮没有返回/加入 journeys、LP 仍 fractional、且 `_journey_should_early_branch(...)` 通过时触发；
- 触发后直接返回 `BRANCH`；
- `child_lower_bound_exact=false`；
- 不产生 certificate；
- 不把当前 RMP objective 当 official lower bound；
- 子节点仍必须由 true-dual exact pricing / final judge 完整闭合。

新增配置校验：

- `journey_early_branching_after_incomplete_no_column_min_remaining >= 0`

新增单测：

- `BPCFutureTests.test_journey_early_branch_after_incomplete_no_column_gate`

## 200s root no-column 提前分支探针：GAT 开启 + root56 no-column + width priority

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_branch_width_greedy_apollo20_direct200/`

配置覆盖：

- `journey_early_branching_enabled=True`
- `journey_early_branching_min_cg_iter=56`
- `journey_early_branching_child_min_cg_iter=3`
- `journey_early_branching_max_depth=1`
- `journey_child_priority_by_width_enabled=True`
- `journey_early_branching_after_incomplete_no_column_enabled=True`
- `journey_early_branching_after_incomplete_no_column_min_remaining=20.0`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，200.02s。
- root 在 cg=56、约 90.46s 触发 `reason=incomplete_no_column_tailing`。
- root 触发前 exact pricing 已返回 `weak_negative_journeys_filtered`，`negative_journeys=0`。
- 因此 root 没有进入原路径的 `exact_retry`、hidden patrol 和 completion-bound retry；相当于提前约 52s 进入子树。
- node 1 在 depth=1、cg=3、约 99.53s 因 `negative_columns_tailing` 再次提前分支。
- depth=2 node 3 到 198.25s 仍未闭合，最后一次 exact pricing 为 `weak_negative_journeys_filtered`。

解释：

这个 opt-in 证明了 root proof tail 可以 exact-safe 地被调度掉，但 greedy/apollo20 仍不能在 200s 内最优，因为省下来的时间被 depth=2 子节点继续找负列消耗。下一步不应把 early-branch 直接默认打开；应继续压缩子节点 exact pricing 的负列尾部，或结合更强的 branch candidate / child ordering，使提前分支减少子树规模而不是制造更深的负列链。

## 200s 分支候选探针：GAT 开启 + root56 no-column + pool_split + width priority

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_poolsplit_width_greedy_apollo20_direct200/`

配置覆盖：

- `journey_early_branching_enabled=True`
- `journey_early_branching_min_cg_iter=56`
- `journey_early_branching_child_min_cg_iter=3`
- `journey_early_branching_max_depth=1`
- `journey_child_priority_by_width_enabled=True`
- `journey_early_branching_after_incomplete_no_column_enabled=True`
- `journey_early_branching_after_incomplete_no_column_min_remaining=20.0`
- `journey_branch_fractionality_tie_tolerance=0.05`
- `journey_branch_candidate_priority=pool_split`
- `journey_branch_candidate_log_top_n=12`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，200.02s。
- root 分支从默认 `RF(1,18)` 改成 `RF(2,13)`。
- root child 当前池宽度从默认 `225/301` 改成 `240/264`，最大宽度确实变小。
- 但 node 1 到约 152.64s 才因 `incomplete_no_column_tailing` 再次提前分支，明显慢于默认 root56 的约 99.53s。
- node 1 再分成 `RF(4,18)`，child 当前池宽度 `146/219`。
- 之后 node 3 在 198.39s `weak_negative_journeys_filtered` 后 incomplete，node 4 只剩约 2s 进入 pricing。

解释：

`pool_split` 只按当前 column pool 的 child width 选分支，能让 root pool 最大宽度变小，但没有可靠降低 pricing 难度。这个实例上它反而把时间花在 depth=1 的较慢子问题上，不能作为当前默认候选。

## 200s 深一层提前分支探针：GAT 开启 + root56 no-column + max_depth=2 + width priority

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_depth2_width_greedy_apollo20_direct200/`

配置覆盖：

- `journey_early_branching_enabled=True`
- `journey_early_branching_min_cg_iter=56`
- `journey_early_branching_child_min_cg_iter=3`
- `journey_early_branching_max_depth=2`
- `journey_child_priority_by_width_enabled=True`
- `journey_early_branching_after_incomplete_no_column_enabled=True`
- `journey_early_branching_after_incomplete_no_column_min_remaining=20.0`
- `journey_branch_candidate_log_top_n=12`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，200.02s。
- root 在 cg=56、约 89.55s 因 `incomplete_no_column_tailing` 提前分支。
- node 1 在 depth=1、cg=3、约 98.55s 因 `negative_columns_tailing` 提前分支。
- node 3 在 depth=2、cg=3、约 125.03s 因 `negative_columns_tailing` 继续提前分支。
- depth=2 的 `RF(4,14)` child 当前池宽度为 `93/125`，比上一轮 depth=2 的 `131/216` 更窄。
- 但 depth=3 node 5 仍持续发现负列，随后在约 174.38s 触发 `ng_dssr_time_limit`，进入 `journey_exact_pricing_completion_bound_retry`，剩余约 26.95s，外部 200s 超时。

解释：

更深一层提前分支确实把当前池宽度进一步压小，并把 long tail 从 depth=2 移到 depth=3；但它没有消灭 exact pricing / completion-bound retry 的核心耗时。当前结论是：单纯继续加深 early-branch 会制造更多非 exact-bound open nodes，不足以形成 200s OPTIMAL。后续应优先让分支选择反映 pricing 难度和 GAT 预测的 branch-impact，而不只是当前 pool 宽度；同时要继续压缩深层节点的 exact/CB retry。

## 200s 深两层提前分支探针：GAT 开启 + root56 no-column + max_depth=3 + width priority

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_depth3_width_greedy_apollo20_direct200/`

配置覆盖：

- `journey_early_branching_enabled=True`
- `journey_early_branching_min_cg_iter=56`
- `journey_early_branching_child_min_cg_iter=3`
- `journey_early_branching_max_depth=3`
- `journey_child_priority_by_width_enabled=True`
- `journey_early_branching_after_incomplete_no_column_enabled=True`
- `journey_early_branching_after_incomplete_no_column_min_remaining=20.0`
- `journey_branch_candidate_log_top_n=12`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，200.02s。
- root、depth=1、depth=2 的分支路径与 max_depth=2 基本一致。
- depth=3 node 5 在 cg=3、约 155.21s 因 `incomplete_no_column_tailing` 继续提前分支，成功避开上一轮 depth=3 的 `journey_exact_pricing_completion_bound_retry`。
- node 5 分成 `RF(2,6)`，child 当前池宽度为 `83/108`。
- 随后优先处理 depth=4 node 7，但该节点到 198.20s 仍持续出现 true negative，最后仍是 `EXTERNAL_TIME_LIMIT`。

解释：

max_depth=3 证明了“继续分支”确实可以绕开一次深层 CB retry，但没有带来 200s OPTIMAL；它只是把负列链从 depth=3 推到 depth=4。后续不应继续机械加深分支，而应识别哪些分支会真正缩短后续 pricing/CB tail。

## 新增 audit-only：branch candidate priority 日志

为支持后续 GAT branch-impact 学习，本轮在 `journey_branch_candidates` 日志中新增：

- `selected`：当前 `journey_branch_candidate_priority` 实际选中的 Ryan-Foster pair；
- `priority_top`：按当前 priority mode 排序后的候选前列；
- `eligible_count`：在 fractionality tie tolerance 内参与 priority 选择的候选数；
- `pool_total_child_width`：与现有 `pool_max_child_width`、`pool_balance_gap` 一起记录当前 pool 分割特征。

作用边界：

- 仅用于 JSONL 诊断和后续离线 branch-impact 数据构建；
- 不改变 `_choose_journey_branch` 的选择结果；
- 不改变 pricing universe、RMP、reduced-cost 公式、lower bound 或 certificate。

新增单测：

- `BPCFutureTests.test_journey_branch_candidate_log_records_priority_selection`

## 当前判断

1. GAT 不能关，但也不能只停留在“找负列”。它必须服务于 active support 改变、branch 缩短或 certificate 收口。
2. 当前 v154/GAT 对 greedy/apollo20 尚无可验证整体 wall-time 加速；新增 early-branch 调度能省掉 root proof tail，并能把子问题继续切窄，但还没有把 200s OPTIMAL 打通。
3. 当前 20 规模已有局部实例加速，但整体目标未达标，尤其不能宣称 greedy/apollo20 已满足 200s 最优。
4. 新 active-support repair 接口是 exact-safe 的，但当前配置未产生收益，应继续作为 opt-in 诊断，不应默认打开。
5. 提前分支是 exact-safe branch scheduling，不是 heuristic 剪枝；只要未闭合节点的 bound 标记为非 exact，且所有子节点最终仍靠 exact pricing closure，精确性不变。未闭合时只能返回 TIME_LIMIT，不能报 OPTIMAL。
6. `pool_split` 和 `max_depth=2` 都是 exact-safe 调度，但在 greedy/apollo20 上仍为 `EXTERNAL_TIME_LIMIT`；它们不能作为“20 规模已加速达标”的证据。
7. `max_depth=3` 能避开一次 depth=3 CB retry，但仍无法闭合 depth=4 负列链；继续加深分支不是当前主解。
8. `pool_split selected-log` 对照再次确认：只缩小 current column pool 的 child width，不足以预测或降低后续 exact pricing / CB tail；GAT 后续必须直接学习 branch-impact，而不是依赖 width proxy。

## 为什么 GAT 没解决 root CG 后段弱/边界负列

GAT 本来应该缓解这个问题，但当前 v154/GAT 只解决了“更早发现 true-RC negative”的一部分，没有解决“哪些 negative 会让 RMP/branch/proof 更快收敛”。

本轮日志显示：

- `journey_learning_true_rc_filter` 持续触发，说明 GAT/learning 没有关；
- GAT/learning-smoothed heuristic 能找到大量 true-RC negative；
- 但 GAT 返回的列多数是 `changed_inactive_only`，只扩大 column pool，不改变 active support；
- root 后段和子节点后段仍由 weak/boundary negative、duplicate/filtered negative、NG-DSSR time limit 和 CB retry 主导；
- 当前 GAT 没有预测 branch-impact，也没有预测“这个负列是否会减少后续 exact pricing/CB tail”。

因此，问题不是 GAT 没参与，而是训练目标仍偏向 candidate safety / exact-safe hit / local ranking，和 20 规模精确求解真正需要的目标不完全一致。要让 GAT 真正解决该瓶颈，下一步需要把标签和在线使用点改成：

- active-support-changing probability；
- branch-impact score；
- predicted reduction of later exact pricing / CB retry；
- accepted batch trajectory ROI under same active basis / cut / branch / pool context。

## 新增离线审计：branch-impact 结果

本轮新增 `BPC_future/scripts/audit_journey_branch_impact.py`，只读解析 4 个 root56/width/depth 探针日志，不运行 BPC、pricing 或 RMP。

输出：

- `BPC_future/results/journey_branch_impact_audit_20260623/summary.json`
- `BPC_future/results/journey_branch_impact_audit_20260623/branch_impact_rows.jsonl`
- `BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_audit_zh.md`

聚合结果：

```text
log_count = 4
branch_count = 11
tail_class_counts = {'completion_bound_tail': 3, 'early_branch_continues': 7, 'negative_chain_continues': 1}
active_touch_branch_count = 5
inactive_only_branch_count = 6
unprocessed_child_count = 10
total_child_negative_pricing_events = 63
total_child_column_additions = 30
total_child_added_journeys = 163
total_child_completion_bound_retries = 5
total_child_early_branch_triggers = 7
production_ready = false
certificate_effect = false
official_bound_effect = false
```

解释：

这组数值确认了当前失败机制：GAT/learning 和提前分支确实在推着搜索往前走，但分支后的已处理子节点仍继续出现负列链、继续 early-branch 或进入 completion-bound tail。也就是说，当前策略没有消灭 root CG 后段弱/边界负列，只是把它迁移到更深、更窄的子节点。

`inactive_only_branch_count = 6` 也说明 GAT 找到的负列仍有大量只改变 inactive pool 的情况；这些列对 exact-safe 是合法的，但对 wall-time ROI 不够直接。

注：这 4 个探针是在 `selected` / `priority_top` 字段加入之前生成的旧日志，所以审计中的 `selected_match_count = 0` 不能解读为分支选择错误；新字段会在后续新跑日志里用于绑定实际 selected candidate。

## selected-log 刷新探针：root56 no-column + max_depth=3 + width priority

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_depth3_width_selectedlog_refresh_greedy_apollo20_direct200/`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，wall time `200.019457s`。
- root 在 cg=56、约 112.62s 因 `incomplete_no_column_tailing` 提前分支。
- 这条新日志包含 `journey_branch_candidates.selected`、`priority_top`、`eligible_count` 和 `pool_total_child_width`。
- 实际 selected 分支链：
  - depth 0：`RF(1,18)`，pool width `225/301`；
  - depth 1：`RF(2,3)`，pool width `131/216`；
  - depth 2：`RF(4,14)`，pool width `93/125`；
  - depth 3：`RF(2,6)`，pool width `83/108`。
- 仍未在 200s 内闭合，最后仍是更深子节点的负列链。

新增 selected-log branch-impact 审计：

```text
output_dir =
  BPC_future/results/journey_branch_impact_audit_selectedlog_refresh_20260623
report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_selectedlog_refresh_zh.md

branch_count = 4
branch_training_row_count = 4
selected_match_count = 4
priority_top_first_branch_count = 4
tail_class_counts = {'early_branch_continues': 3, 'negative_chain_continues': 1}
active_touch_branch_count = 1
inactive_only_branch_count = 3
total_child_negative_pricing_events = 19
total_child_column_additions = 10
total_child_added_journeys = 66
total_child_completion_bound_retries = 0
total_child_early_branch_triggers = 3
production_ready = false
certificate_effect = false
official_bound_effect = false
```

解释：

这次刷新没有让 greedy/apollo20 达到 200s OPTIMAL；它的价值是补齐了 branch-impact 训练数据最缺的实际 `selected` 绑定。现在每条分支训练 row 都能直接知道“被当前 priority mode 选中的 Ryan-Foster pair 是谁”，而不是从旧日志的 `top` 中反推。

这进一步确认当前失败机制：fractionality/width 链条能把子问题池宽从 `301` 压到 `108`，但后续已处理子节点仍继续产生 true negative 或 early-branch。下一步要让 GAT 学的是 branch-impact，即预测哪个候选会减少后续 negative pricing events / CB retry / inactive-only tail，而不是只学习当前 pool width 或 true-RC 命中。

## selected-log 对照探针：root56 no-column + pool_split + width priority

命令输出目录：

`BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_poolsplit_width_selectedlog_refresh_greedy_apollo20_direct200/`

结果：

- CSV 状态：`EXTERNAL_TIME_LIMIT`，wall time `200.020489s`。
- 这条日志同样包含 `selected` / `priority_top` / `eligible_count` / `pool_total_child_width`。
- `priority_mode_counts = {'pool_split': 2}`，`selected_match_count = 2`，说明实际选中候选能被审计脚本准确绑定。
- 实际 selected 分支链：
  - depth 0：`RF(2,13)`，pool width `240/264`；
  - depth 1：`RF(4,18)`，pool width `146/219`。
- 到 200s 前仍未闭合，node 3 最后停在 `weak_negative_journeys_filtered` / `INCOMPLETE_LIMIT`。

新增 pool_split selected-log branch-impact 审计：

```text
output_dir =
  BPC_future/results/journey_branch_impact_audit_poolsplit_selectedlog_refresh_20260623
report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_poolsplit_selectedlog_refresh_zh.md

branch_count = 2
branch_training_row_count = 2
selected_match_count = 2
priority_top_first_branch_count = 2
tail_class_counts = {'completion_bound_tail': 1, 'early_branch_continues': 1}
active_touch_branch_count = 1
inactive_only_branch_count = 1
unprocessed_child_count = 1
total_child_negative_pricing_events = 10
total_child_column_additions = 3
total_child_added_journeys = 22
total_child_completion_bound_retries = 1
total_child_early_branch_triggers = 1
production_ready = false
certificate_effect = false
official_bound_effect = false
```

解释：

`pool_split` 确实让 root 当前池最大 child width 变小，但两条训练 row 的 `y_tail_improved` 都是 0。它没有解决弱/边界负列尾部，只是把 root 的尾部改写成 depth=1/depth=2 子节点的负列链和 completion-bound tail。

这也解释了为什么“GAT 已经在找负列”但没有形成 wall-time 改善：当前在线使用点仍没有让 GAT 判断哪个 branch candidate 会减少后续 pricing 事件、CB retry 或 inactive-only 列。`pool_split` 是一个手写 proxy，不是从 branch-impact 标签学出来的策略；它能缩小当前 pool，但不等价于降低 proof-tail 难度。

## 新增 offline GAT branch-impact 模型接口

为让 GAT 真正服务于 “减少 root/branch tail”，本轮新增 default-off / audit-only 模型结构：

- `BPC_future/learning/branch_impact_model.py`
- `BPC_future/tests/test_gat_branch_impact_model.py`
- 报告：`BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_branch_impact_model_schema_zh.md`

`GATBranchImpactModel` 复用 `HierarchicalOptionGAT` 的 task embedding，输入 Ryan-Foster pair、branch candidate 特征和 RMP/branch context，输出：

- `branch_priority`
- `tail_improved`
- `completion_bound_tail`
- `early_branch_continues`
- `negative_chain_continues`
- `active_touch`
- `inactive_only`
- child negative / CB retry / early-branch regression heads

边界：

```text
production_ready = false
pricing_oracle = false
branching_oracle = false
certificate_source = false
official_bound_effect = false
default_solver_effect = false
```

同时 `audit_journey_branch_impact.py` 现在额外输出：

```text
branch_training_rows =
  BPC_future/results/journey_branch_impact_audit_20260623/branch_training_rows.jsonl
branch_training_row_count = 11
```

这一步没有让 20 规模变快；它把 “当前分支后为什么还继续拖尾” 变成 GAT 可学习的监督接口。`selected-log` 刷新探针已经补上第一批实际 selected candidate 训练行，后续应继续补不同 priority mode / family 的正反例，再训练和 shadow 对比 branch-impact score。

## 新增离线审计：weak-negative tail

为把“root CG 后段反复产生弱/边界负列”从现象变成可训练证据，本轮新增：

- `BPC_future/scripts/audit_journey_weak_negative_tail.py`
- `BPC_future/tests/test_journey_weak_negative_tail_audit.py`
- 输出报告：
  - `BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_greedy_selectedlog_zh.md`
  - `BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_poolsplit_scan8_zh.md`

该审计只读 JSONL，不运行 BPC、pricing 或 RMP，不改变 certificate / official bound。它抽取 rough/profile negative 在 true-RC materialization 后被过滤的事件，作为 GAT/priority/delay 的弱负例和 proof-tail 诊断样本。

selected-log 聚合结果：

```text
log_count = 2
weak_event_count = 14
weak_training_row_count = 14
total_weak_negative_journeys_filtered = 446
total_profile_weak_filtered_materialized_count = 446
total_profile_generation_time = 32.396167
total_profile_dp_time = 55.205690
total_dp_state_count = 477956
best_rough_rc = -11.774451333
best_true_rc_after_materialization = -0.0
max_true_minus_rough = 29.129438
pricing_kind_counts = {'exact': 13, 'exact_retry': 1}
reason_counts = {'streaming_partial_negative_journey': 9, 'weak_negative_journeys_filtered': 5}
node_counts = {'depth=0|node=0': 10, 'depth=2|node=3': 3, 'depth=3|node=5': 1}
repeated_weak_mask_count = 4
repeated_weak_task_set_sample_count = 45
diagnostic_only = true
certificate_effect = false
official_bound_effect = false
production_ready = false
```

解释：

这组数值说明弱/边界负列不是偶发现象：同类 mask 和 task-set sample 会重复出现，且 rough RC 可以很负，但 true-RC materialization 后并不产生可加入的有效负列。这正是当前 GAT 没有解决 tail 的原因之一：它对 rough/local negative 有命中能力，但还没有学习 “rough negative 最终是否变成 inactive-only/filtered tail”。

这些样本可以作为后续 GAT 的 delay / priority / branch-impact 训练负例，但不能用于剪枝，也不能用于 no-negative certificate。真正的 certificate 仍必须来自 exact pricing exhaustive closure。

## 200s scan8 探针：pool_split + true-RC candidate scan factor

为验证“多 materialize 一些 weak/profile 候选”是否能减少 `weak_negative_journeys_filtered`，本轮跑了 opt-in 探针：

```text
output_dir =
  BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_poolsplit_width_scan8_selectedlog_greedy_apollo20_direct200

journey_pricing_late_profile_true_rc_candidate_scan_factor = 8
journey_pricing_late_profile_true_rc_candidate_scan_max_candidates = 128
```

结果：

```text
CSV status = EXTERNAL_TIME_LIMIT
return_code = 124
wall_time = 200.041679
```

scan8 日志的 weak-negative 审计：

```text
log_count = 1
weak_event_count = 7
weak_training_row_count = 7
total_weak_negative_journeys_filtered = 218
total_profile_weak_filtered_materialized_count = 218
total_profile_generation_time = 18.616330
total_profile_dp_time = 30.882644
total_dp_state_count = 245668
pricing_kind_counts = {'exact': 6, 'exact_retry': 1}
reason_counts = {'streaming_partial_negative_journey': 4, 'weak_negative_journeys_filtered': 3}
node_counts = {'depth=0|node=0': 5, 'depth=2|node=3': 2}
repeated_weak_mask_count = 3
repeated_weak_task_set_sample_count = 38
certificate_effect = false
official_bound_effect = false
production_ready = false
```

scan8 的 branch-impact 审计：

```text
branch_count = 2
selected_match_count = 2
priority_top_first_branch_count = 2
tail_class_counts = {'completion_bound_tail': 1, 'early_branch_continues': 1}
active_touch_branch_count = 1
inactive_only_branch_count = 1
total_child_negative_pricing_events = 11
total_child_column_additions = 3
total_child_added_journeys = 22
total_child_completion_bound_retries = 1
total_child_early_branch_triggers = 1
certificate_effect = false
official_bound_effect = false
```

结论：

scan8 没有带来 20 规模 wall-time 改善，仍是 200s 外部超时。它相对 pool_split selected-log 对照没有降低 tail，child negative pricing events 反而从 `10` 到 `11`。同时，关键尾部日志仍能看到相关 pricing path 的 `profile_true_rc_candidate_scan_factor=1`，说明 `journey_pricing_late_*` override 不是覆盖所有 learning/heuristic/exact 路径的充分杠杆。

因此不能把 scan8 当成加速方案。它的价值是进一步确认：单纯扩大 true-RC materialization 候选数，不能替代 active-support / branch-impact / proof-tail 标签。下一步若继续沿 GAT 方向，应把 weak-negative rows 和 branch-impact rows 合并成“哪些候选会制造 tail、哪些候选会缩短 tail”的监督数据，而不是只调 scan factor。

## 新增离线合成：tail-impact training rows

为把上一节的结论落成可训练接口，本轮新增：

- `BPC_future/scripts/build_journey_tail_impact_training_rows.py`
- `BPC_future/tests/test_journey_tail_impact_training_rows.py`
- 输出目录：`BPC_future/results/journey_tail_impact_training_rows_20260623/`
- 报告：`BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_zh.md`

输入：

- weak-negative audit：
  - `journey_weak_negative_tail_audit_greedy_selectedlog_20260623`
  - `journey_weak_negative_tail_audit_poolsplit_scan8_20260623`
- branch-impact audit：
  - `journey_branch_impact_audit_20260623`
  - `journey_branch_impact_audit_selectedlog_refresh_20260623`
  - `journey_branch_impact_audit_poolsplit_selectedlog_refresh_20260623`
  - `journey_branch_impact_audit_poolsplit_scan8_20260623`

合成结果：

```text
training_row_count = 40
raw_training_row_count = 40
deduplicated_row_count = 0
weak_row_count = 21
branch_row_count = 19
source_counts = {'branch_impact': 19, 'weak_negative_tail': 21}
tail_class_counts = {'completion_bound_tail': 5, 'early_branch_continues': 12, 'negative_chain_continues': 2, 'weak_negative_filtered': 21}
label_positive_counts = {
  'y_useful_tail_reduction': 0,
  'y_tail_risk': 40,
  'y_weak_negative_filtered': 21,
  'y_completion_bound_tail': 5,
  'y_early_branch_continues': 12,
  'y_negative_chain_continues': 2,
  'y_active_touch': 8,
  'y_inactive_only': 11,
  'y_child_negative_pricing_events': 19,
  'y_child_completion_bound_retries': 5,
  'y_child_early_branch_triggers': 12
}
regression_label_totals = {'child_negative_pricing_events': 103, 'child_completion_bound_retries': 7, 'child_early_branch_triggers': 12}
hard_negative_catalog_ready = true
contrastive_tail_training_ready = false
tail_label_training_ready = false
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

解释：

这是一个重要负结果：当前已有证据足够构成 hard-negative catalog，但没有任何 `y_useful_tail_reduction=1` 的正例。因此这批数据不能单独训练“选择好分支/好候选”的 GAT；它只能告诉模型哪些 weak/profile/branch 形态会制造 tail。下一步不能直接开训或调阈值，必须先挖到能实际减少 child negative pricing events / CB retry / early-branch chain 的 positive tail-reduction rows。

这也再次解释了为什么 GAT 当前没解决 root CG 后段弱/边界负列：我们现在拥有大量“坏 tail”的监督信号，但缺少同上下文下“好 tail 选择”的反事实正例。没有这个对照，模型只能学会保守避险，不能学会加速。

## 全 v154 日志正例缺口审计

为确认 `y_useful_tail_reduction=0` 不是前一节输入目录太窄造成的，本轮对整个 `journey_completion_tail_direction1_v154_20260623` 目录重新跑了 branch-impact 审计：

- 输出目录：`BPC_future/results/journey_branch_impact_audit_v154_alllogs_20260623/`
- 报告：`BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_v154_alllogs_zh.md`

聚合结果：

```text
branch_count = 109
branch_training_row_count = 109
tail_class_counts = {
  'completion_bound_tail': 72,
  'early_branch_continues': 14,
  'negative_chain_continues': 6,
  'node_incomplete_tail': 1,
  'unprocessed_children': 16
}
priority_mode_counts = {'fractionality': 11, 'not_logged': 92, 'pool_split': 6}
active_touch_branch_count = 15
inactive_only_branch_count = 52
total_child_negative_pricing_events = 285
total_child_column_additions = 135
total_child_added_journeys = 513
total_child_completion_bound_retries = 211
total_child_early_branch_triggers = 15
production_ready = false
certificate_effect = false
official_bound_effect = false
```

随后用这 109 条 branch row 加上 21 条 weak-negative row 重新合成 tail-impact rows：

- 输出目录：`BPC_future/results/journey_tail_impact_training_rows_v154_alllogs_20260623/`
- 报告：`BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_v154_alllogs_zh.md`

```text
training_row_count = 130
source_counts = {'branch_impact': 109, 'weak_negative_tail': 21}
label_positive_counts = {
  'y_useful_tail_reduction': 0,
  'y_tail_risk': 130,
  'y_weak_negative_filtered': 21,
  'y_completion_bound_tail': 72,
  'y_early_branch_continues': 14,
  'y_negative_chain_continues': 6,
  'y_active_touch': 15,
  'y_inactive_only': 52,
  'y_child_negative_pricing_events': 91,
  'y_child_completion_bound_retries': 72,
  'y_child_early_branch_triggers': 15
}
regression_label_totals = {'child_negative_pricing_events': 285, 'child_completion_bound_retries': 211, 'child_early_branch_triggers': 15}
hard_negative_catalog_ready = true
contrastive_tail_training_ready = false
tail_label_training_ready = false
```

新增正例缺口审计：

- `BPC_future/scripts/audit_journey_tail_positive_gap.py`
- `BPC_future/tests/test_journey_tail_positive_gap.py`
- 输出目录：`BPC_future/results/journey_tail_positive_gap_audit_v154_alllogs_20260623/`
- 报告：`BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_positive_gap_v154_alllogs_zh.md`

```text
row_count = 130
useful_tail_reduction_positive_count = 0
tail_risk_count = 130
active_touch_count = 15
active_touch_still_tail_risk_count = 15
active_touch_completion_bound_tail_count = 6
active_touch_early_branch_count = 7
active_touch_negative_chain_count = 2
weak_negative_filtered_count = 21
positive_gap_reason = no_useful_tail_reduction_positive
contrastive_tail_training_ready = false
production_ready = false
certificate_effect = false
official_bound_effect = false
```

最接近正例的 active-touch rows 仍然没有闭合 tail：

- `RF(2,6)` depth 3：active-touch 后仍 `negative_chain_continues`，child negative pricing events = 6；
- `RF(17,20)` depth 1：active-touch 后仍 `negative_chain_continues`，child negative pricing events = 11；
- 多个 `RF(2,3)` / `RF(2,13)`：active-touch 后仍 `early_branch_continues`，child negative pricing events = 5~6。

结论：

现在可以确定，不只是 v154 focused gate 的 77/78 问题，也不是单个 pool_split proxy 没调好；当前已有 v154 日志族里没有“active-touch 且 tail 真正缩短”的监督正例。GAT 要继续发挥作用，下一步必须主动生成正例：对同一 parent context 下多个 Ryan-Foster pair / child ordering 做受控短时 A/B，找出能把 `completion_bound_tail`、`early_branch_continues` 或 `negative_chain_continues` 降下来的分支选择。没有这个正例，训练只会变成 hard-negative suppression，不会变成加速策略。

## 5000 样本与新增 branch-tail 样本的关系

当前不是推倒 5000 个样本重来，而是在其基础上追加一层 branch-tail intervention 数据。

已有 5000 个样本仍然有用：

- 作为 Stage 3 admission / focused ranking / kNN-OOD / safety-shell 的基座；
- 作为 GAT graph/context embedding 和已有 hard-negative 结构的训练来源；
- 作为 candidate batch ROI 与 delay-risk 的历史对照。

但它们不能直接替代现在缺失的标签：

```text
missing_label = y_useful_tail_reduction
needed_context = same parent branch context
needed_intervention = different Ryan-Foster pair / child ordering
needed_outcome = lower child negative pricing events / CB retry / early-branch chain
```

因此后续数据策略应是：

```text
base_dataset = existing_5000_selected_rows
extension_dataset = branch_tail_intervention_rows
merge_policy = append_with_new_label_namespace
do_not_relabel_old_rows_as_branch_tail_positive = true
```

## 新增 opt-in：forced branch pair 采集入口

为生成上述缺失正例，本轮新增 default-off 分支候选入口：

```text
journey_branch_candidate_priority = force_pair:i,j
```

语义：

- 只在 `(i,j)` 是当前合法 fractional Ryan-Foster candidate 时把它排到最前；
- 如果该 pair 不存在或不合法，回退默认 fractionality 选择；
- 只改变 branch candidate ordering，不改变 pricing universe、RMP、reduced-cost 公式、lower bound 或 certificate；
- `journey_branch_candidates` 日志新增 `forced_pair` 与 `forced_pair_matched`，用于审计是否真的绑定到目标 pair。

新增测试覆盖：

- `test_journey_branch_can_force_pair_for_controlled_ab`
- `test_journey_branch_candidate_log_records_forced_pair_binding`

## 正例采集 runbook：root-level first tranche

新增 runbook builder：

- `BPC_future/scripts/build_journey_branch_tail_positive_runbook.py`
- `BPC_future/tests/test_journey_branch_tail_positive_runbook.py`
- 输出目录：`BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/`
- 报告：`BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_tail_positive_runbook_v154_root_force_zh.md`

runbook 只从 `near_positive_rows` 里选 root-level pair，避免第一批混入需要祖先路径绑定的 non-root parent context。当前生成 2 个 opt-in 条目：

```text
entry_count = 2
base_sample_strategy = extend_existing_5000_with_branch_tail_interventions
candidate_source = root_level_near_positive_rows

01 force_pair = [2, 13]
source_tail_class = early_branch_continues
source_child_negative_pricing_events = 5

02 force_pair = [2, 3]
source_tail_class = early_branch_continues
source_child_negative_pricing_events = 6

production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

这一步仍然没有运行 BPC，也没有产生正例。它只是把下一批正例采集变成可执行、可审计的 opt-in A/B 命令。跑完这些命令后，应重新执行 branch-impact / tail-impact / positive-gap 审计，只有出现 `y_useful_tail_reduction=1` 才能进入 tail-impact GAT 训练。

## forced-pair first tranche 实测结果

已执行上述 root-level first tranche 的 2 条 opt-in 命令：

```text
run_dir =
  BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs

01 force_pair:2,13 -> EXTERNAL_TIME_LIMIT, wall_time = 200.03s
02 force_pair:2,3  -> EXTERNAL_TIME_LIMIT, wall_time = 200.02s
```

绑定审计：

- `force_pair:2,13` 在 root node 合法绑定成功，`forced_pair_matched=true`，选中 `RF(2,13)`；
- 该 run 在 depth=1 仍于约 173.44s 触发二次 early-branch，后续实际选中 `RF(2,3)`；
- `force_pair:2,3` 在 root node 合法绑定成功，`forced_pair_matched=true`，选中 `RF(2,3)`；
- 该 run 在 depth=1 仍于约 138.64s 触发二次 early-branch，后续实际选中 `RF(17,20)`；
- 两条 run 都保持 exact-safe：只改变合法 Ryan-Foster candidate ordering，不改变 pricing universe、RMP、reduced-cost、official bound 或 certificate 语义。

branch-impact 审计：

```text
audit_dir =
  BPC_future/results/journey_branch_impact_audit_v154_forced_pairs_20260623
report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_v154_forced_pairs_zh.md

log_count = 2
branch_count = 4
branch_training_row_count = 4
tail_class_counts = {'completion_bound_tail': 1, 'early_branch_continues': 2, 'negative_chain_continues': 1}
priority_mode_counts = {'force_pair:2,13': 2, 'force_pair:2,3': 2}
selected_match_count = 4
active_touch_branch_count = 3
inactive_only_branch_count = 1
total_child_negative_pricing_events = 26
total_child_column_additions = 12
total_child_added_journeys = 42
total_child_completion_bound_retries = 1
total_child_early_branch_triggers = 2
```

tail-impact 合成：

```text
rows_dir =
  BPC_future/results/journey_tail_impact_training_rows_v154_forced_pairs_20260623
report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_v154_forced_pairs_zh.md

training_row_count = 4
y_useful_tail_reduction = 0
y_tail_risk = 4
y_active_touch = 3
y_child_negative_pricing_events = 4
child_negative_pricing_events_total = 26
hard_negative_catalog_ready = true
contrastive_tail_training_ready = false
stage4_candidate_ready = false
```

positive-gap 审计：

```text
gap_audit_dir =
  BPC_future/results/journey_tail_positive_gap_audit_v154_forced_pairs_20260623
report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_positive_gap_v154_forced_pairs_zh.md

row_count = 4
useful_tail_reduction_positive_count = 0
tail_risk_count = 4
active_touch_count = 3
active_touch_still_tail_risk_count = 3
positive_gap_reason = no_useful_tail_reduction_positive
```

本轮结论：

第一批 forced-pair 样本不是正例，而是更强的 branch-tail hard negatives。它们证明了 `force_pair` 入口本身可用，GAT 可以被接到 branch-candidate 选择的可审计数据闭环里；但这两个 root-level pair 仍只是把 root 后段 tail 下放到 depth=1/2 子节点，未减少 20 规模精确证明时间，也未产生 `y_useful_tail_reduction=1`。

这进一步说明：继续在旧 5000 样本上训练普通 admission / candidate ROI 头不会自然解决 proof tail。下一批样本需要更主动地覆盖同一 parent context 下的多 pair 对照，尤其是比较：

- root `RF(2,13)`、`RF(2,3)` 与未选中的 width/active-support 候选；
- depth=1 的 `RF(17,20)`、`RF(14,20)`、`RF(2,6)` 等后续候选；
- child ordering 与 completion-bound retry / exact pricing retry 的联动。

如果仍然没有正例，应把 GAT 的当前作用限定为 hard-negative suppression / branch-risk warning，同时主攻 exact-safe solver tail reduction，例如子节点 lower-bound 复用、completion-bound warm start、profile scan 预算绑定和 official proof-tail 复用。

## depth-scoped forced-pair 与第一条 depth-sequence A/B

root-only forced-pair 只能测试第一层分支，不能直接测试同一 parent context 下的 depth=1 候选。因此本轮继续新增兼容语法：

```text
journey_branch_candidate_priority = force_pair_depth:0:i,j;1:k,l
```

语义：

- legacy `force_pair:i,j` 保持全局生效；
- `force_pair_depth:0:i,j;1:k,l` 只在对应 depth 生效；
- 未匹配 depth 或目标 pair 非法时回退原有 priority；
- 仍只重排当前节点合法 fractional Ryan-Foster candidates，不改变 pricing universe、RMP、reduced-cost、lower bound 或 certificate。

新增测试：

- `test_journey_branch_candidate_log_records_depth_forced_pair_binding`
- 扩展 `test_journey_branch_can_force_pair_for_controlled_ab`，覆盖 depth=0 fallback 与 depth=1 binding。

已执行第一条 depth-sequence：

```text
run_dir =
  BPC_future/results/journey_branch_tail_depth_sequence_v154_20260623/runs/01_root_2_3_depth1_14_20_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph

priority_mode = force_pair_depth:0:2,3;1:14,20
status = EXTERNAL_TIME_LIMIT
wall_time = 200.02s
```

绑定结果：

- depth=0：`forced_pair=[2,3]`，`forced_pair_matched=true`；
- depth=1：`forced_pair=[14,20]`，`forced_pair_matched=true`；
- 原先 depth=1 默认/forced 对照选择的是 `RF(17,20)`，本条确实改成了 `RF(14,20)`。

depth-sequence branch-impact 审计：

```text
audit_dir =
  BPC_future/results/journey_branch_impact_audit_v154_depth_sequence_20260623
report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_v154_depth_sequence_zh.md

log_count = 1
branch_count = 2
branch_training_row_count = 2
tail_class_counts = {'completion_bound_tail': 1, 'early_branch_continues': 1}
selected_match_count = 2
active_touch_branch_count = 1
inactive_only_branch_count = 1
total_child_negative_pricing_events = 17
total_child_column_additions = 7
total_child_added_journeys = 17
total_child_completion_bound_retries = 1
total_child_early_branch_triggers = 1
```

tail-impact / positive-gap：

```text
rows_dir =
  BPC_future/results/journey_tail_impact_training_rows_v154_depth_sequence_20260623
gap_audit_dir =
  BPC_future/results/journey_tail_positive_gap_audit_v154_depth_sequence_20260623

training_row_count = 2
y_useful_tail_reduction = 0
y_tail_risk = 2
positive_gap_reason = no_useful_tail_reduction_positive
contrastive_tail_training_ready = false
stage4_candidate_ready = false
```

结论：

`RF(14,20)` 比 `RF(17,20)` 的 pool width 略小，但仍进入 completion-bound tail，并继续产生 inactive-only columns。它不是当前缺失的 useful tail-reduction positive。当前问题因此更具体：在 root `RF(2,3)` 之后，depth=1 的 top width / incumbent-relation 候选仍不能消除 depth=2 proof tail。下一轮如果继续采样，应优先测 `RF(2,6)`、`RF(6,12)`、`RF(7,14)` 或改为测试 child ordering / completion-bound warm-start，而不是只在 `17/20` 与 `14/20` 之间切换。

## cross-node cache 探针：GAT 开启 + branch 共享 pricing 构件

为排除“只是重复构建 pricing / physical catalog 导致找不到正例”的可能，本轮跑了一个不改默认配置的 opt-in 探针：

```text
run_dir =
  BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_crossnode_cache_greedy_apollo20_direct200

status = EXTERNAL_TIME_LIMIT
wall_time = 200.018320s
```

额外覆盖：

- `journey_branch_pricing_cross_node_cache_enabled=True`
- `journey_branch_pricing_cross_node_cache_max_entries=200000`
- `journey_pricing_profile_labeling_physical_catalog_share_across_branches_enabled=True`
- `journey_branch_pricing_profile_labeling_physical_catalog_share_across_branches_enabled=True`

审计结果：

```text
branch_impact_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_crossnode_cache_zh.md
weak_negative_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_crossnode_cache_zh.md

branch_count = 2
tail_class_counts = {'completion_bound_tail': 1, 'early_branch_continues': 1}
selected_match_count = 2
active_touch_branch_count = 1
inactive_only_branch_count = 1
total_child_negative_pricing_events = 12
total_child_column_additions = 5
total_child_added_journeys = 14
total_child_completion_bound_retries = 3
total_child_early_branch_triggers = 1

weak_event_count = 10
total_weak_negative_journeys_filtered = 288
total_profile_weak_filtered_materialized_count = 288
total_profile_generation_time = 20.519987
total_profile_dp_time = 71.160076
best_rough_rc = -35.51011308
best_true_rc_after_materialization = -0.0
```

cache 字段显示 physical catalog 确实有命中：

```text
profile_catalog_hit=True  count = 10
profile_catalog_hit=False count = 64
completion_bound_cache_hit=True count = 0
completion_bound_cache_hit=False count = 74
```

解释：

跨节点共享物理 catalog 可以减少一部分重复构件构造，但没有改变核心失败模式。该探针在 root `RF(1,18)` 后，depth=1 选择 `RF(2,3)`，随后 depth=2 child 进入 completion-bound tail，出现 3 次 CB retry，并在 200s 外部时限内仍未闭合。

这说明当前找不到正例不只是“没复用缓存”这么简单；更主要的问题仍是：现有 branch / candidate 选择不知道哪个动作会真正减少后续 negative pricing events、weak-negative materialization、CB retry 或 inactive-only tail。

## forced root RF(2,6) 探针：低 pool width 仍非正例

为验证 root 候选中更低 pool max width 的 `RF(2,6)` 是否可能成为 useful tail-reduction positive，本轮执行了受控 opt-in：

```text
run_dir =
  BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_force26_greedy_apollo20_direct200

journey_branch_candidate_priority = force_pair:2,6
status = EXTERNAL_TIME_LIMIT
wall_time = 200.017425s
```

绑定结果：

- root `RF(2,6)` 合法匹配，`forced_pair_matched=true`；
- 它在原 priority top 中 rank=2，被 force-pair 提到 priority rank=0；
- root pool width 为 `243/264`，max child width 比默认 `RF(1,18)` 的 `301` 更小；
- 但之后形成 depth 链：`RF(2,6)` -> `RF(14,17)` -> `RF(2,11)` -> `RF(4,5)`，最终仍进入 completion-bound tail。

branch-impact 审计：

```text
audit_dir =
  BPC_future/results/journey_branch_impact_audit_force26_20260623
report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_force26_zh.md

branch_count = 4
branch_training_row_count = 4
priority_mode_counts = {'force_pair:2,6': 4}
selected_match_count = 4
priority_top_first_branch_count = 4
tail_class_counts = {'completion_bound_tail': 1, 'early_branch_continues': 3}
active_touch_branch_count = 2
inactive_only_branch_count = 2
total_child_negative_pricing_events = 24
total_child_column_additions = 13
total_child_added_journeys = 44
total_child_completion_bound_retries = 1
total_child_early_branch_triggers = 3
```

weak-negative 审计：

```text
weak_audit_dir =
  BPC_future/results/journey_weak_negative_tail_audit_force26_20260623
report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_force26_zh.md

weak_event_count = 5
total_weak_negative_journeys_filtered = 216
total_profile_weak_filtered_materialized_count = 216
total_profile_generation_time = 10.119368
total_profile_dp_time = 10.653457
best_rough_rc = -11.774451333
best_true_rc_after_materialization = -0.0
node_counts = {'depth=0|node=0': 5}
```

tail-impact / positive-gap：

```text
rows_dir =
  BPC_future/results/journey_tail_impact_training_rows_force26_20260623
gap_audit_dir =
  BPC_future/results/journey_tail_positive_gap_audit_force26_20260623

training_row_count = 9
source_counts = {'branch_impact': 4, 'weak_negative_tail': 5}
y_useful_tail_reduction = 0
y_tail_risk = 9
y_weak_negative_filtered = 5
y_completion_bound_tail = 1
y_early_branch_continues = 3
y_active_touch = 2
y_inactive_only = 2
positive_gap_reason = no_useful_tail_reduction_positive
contrastive_tail_training_ready = false
stage4_candidate_ready = false
```

最接近正例的两条 active-touch 行仍然没有缩短 proof tail：

- depth=2 `RF(2,11)`：`early_branch_continues`，child negative pricing events = 4；
- depth=3 `RF(4,5)`：`completion_bound_tail`，child negative pricing events = 8，CB retry = 1。

结论：

`RF(2,6)` 不是当前缺失的正例，而是一个更有信息量的 near-positive hard negative。它说明“root pool width 更窄”和“后续 active-touch”仍不足以保证加速；真正要学习的是 child negative pricing events、CB retry、early-branch chain 是否下降。下一批若继续采样，应测试同一路径下的 depth-scoped 替代候选或 child ordering，而不是继续只按 root pool width 选分支。

## depth-scoped RF(4,9) 探针：局部 tail 变轻但仍未转正

为进一步缩小对照，本轮固定 force26 的祖先路径，只替换 depth=3 的候选：

```text
run_dir =
  BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_force26_depth3_49_greedy_apollo20_direct200

journey_branch_candidate_priority = force_pair_depth:0:2,6;1:14,17;2:2,11;3:4,9
status = EXTERNAL_TIME_LIMIT
wall_time = 200.018478s
```

选择这个候选的原因：

- force26 的 depth=3 默认 `RF(4,5)` 进入 completion-bound tail；
- 同一 parent context 下 `RF(4,9)` 与 `RF(4,5)` fractionality 相同；
- `RF(4,9)` 的 pool max child width 为 `108`，略小于 `RF(4,5)` 的 `109`。

审计结果：

```text
branch_impact_dir =
  BPC_future/results/journey_branch_impact_audit_force26_depth3_49_20260623
weak_audit_dir =
  BPC_future/results/journey_weak_negative_tail_audit_force26_depth3_49_20260623
rows_dir =
  BPC_future/results/journey_tail_impact_training_rows_force26_depth3_49_20260623
gap_audit_dir =
  BPC_future/results/journey_tail_positive_gap_audit_force26_depth3_49_20260623

branch_count = 4
tail_class_counts = {'completion_bound_tail': 1, 'early_branch_continues': 3}
active_touch_branch_count = 1
inactive_only_branch_count = 3
total_child_negative_pricing_events = 19
total_child_column_additions = 10
total_child_added_journeys = 18
total_child_completion_bound_retries = 1
total_child_early_branch_triggers = 3

weak_event_count = 5
total_weak_negative_journeys_filtered = 216
total_profile_weak_filtered_materialized_count = 216

training_row_count = 9
y_useful_tail_reduction = 0
y_tail_risk = 9
positive_gap_reason = no_useful_tail_reduction_positive
```

对比 force26 默认 depth=3 `RF(4,5)`：

- total child negative pricing events 从 `24` 降到 `19`；
- depth=3 child negative pricing events 从 `8` 降到 `3`；
- 但 completion-bound retry 仍为 `1`；
- 200s 内仍未闭合，仍不能作为 `y_useful_tail_reduction=1`。

结论：

`RF(4,9)` 是“局部更轻的 hard negative”，不是加速正例。它说明 regression labels 有价值：GAT branch-tail head 不应只学二分类正负，还应学 `child_negative_pricing_events`、`completion_bound_retries`、`early_branch_triggers` 的连续下降。但 Stage 4 opt-in 仍需要 binary useful-tail positive；否则模型最多能排序“坏得少一点”，还不能证明能把 20 规模 exact solve 推到 200s OPTIMAL。

## 为什么正例这么难找

当前正例定义很严格：

```text
same parent context
+ legal branch / child-ordering intervention
+ lower child negative pricing events / CB retry / early-branch chain
+ 仍保持 exact-safe closure
+ 对 20-scale wall-time 或 proof progress 有实质帮助
```

这比旧 5000 样本里的 “candidate true-RC negative / high ROI batch” 更难，因为它要求改变的是 proof tail，而不是单轮 column discovery。

找不到正例实际表示：

- 当前很多动作能找到负列，但不能让证明更快收口；
- current pool width、fractionality、active-touch 都只是 proxy，不等价于 pricing 难度下降；
- 负列链会从 root 后段迁移到 depth=1/2/3/4 子节点，而不是被消灭；
- rough/profile negative 很多，但 true-RC materialization 后大量变成 weak/filtered/inactive-only tail；
- completion-bound retry 和 exact pricing retry 的成本没有被 GAT 当前目标直接建模。

本质原因是目标错位：

```text
旧 GAT 学的是：
  哪些 true-RC negative / batch 值得优先 admission

20-scale exact 加速真正需要的是：
  哪个 branch / child ordering / candidate batch 会减少后续 proof work
```

对应到组件：

- `HierarchicalOptionGAT` / graph embedding 本身不是主要问题，它能提供图和路径结构信号；
- `ContextAwareColumnSelector` / v154 admission heads 仍偏 candidate-level safety / focused ranking，不能直接预测 branch proof tail；
- `_choose_journey_branch` 当前主要依赖 fractionality、width、forced-pair 等手写 proxy，缺少 learned branch-impact score；
- `audit_journey_branch_impact.py` 和 `build_journey_tail_impact_training_rows.py` 已经补上标签接口，但目前多是 hard negatives，缺少 useful-tail positives；
- `journey_pricing.py` 的 weak-negative / completion-bound path 是真实耗时来源之一，但它仍没有被旧 admission 标签覆盖。

所以问题不是 “GAT 没用”，而是 GAT 现在主要连在列发现/调度入口；20 规模的瓶颈已经转到 branch proof tail。要让 GAT 真正加速，需要新增 branch-tail head 和同 parent context 的正反事实样本；同时在 solver 侧继续做 exact-safe 的 proof-tail 复用、warm-start、child ordering 和 completion-bound 收口优化。

## 新 branch-tail 标签不会替代旧 GAT 能力

新增 branch-tail 标签不能直接混进旧的 high-priority / delay 标签里，否则确实会出现“顾着 proof tail，丢掉原来找 true-RC negative 的能力”的风险。

正确边界是：

- 保留旧的 5000-row admission / focused ranking / kNN-OOD / safety-shell 训练目标；
- 追加新的 label namespace：`y_useful_tail_reduction`、`y_tail_risk`、`y_child_negative_pricing_events`、`y_child_completion_bound_retries`、`y_child_early_branch_triggers`；
- 模型上使用独立 head：旧 head 继续判断 candidate / batch admission，新 head 只做 branch-impact / proof-tail 诊断；
- 训练时对旧 checkpoint 做冻结、低学习率微调或 distillation，避免 catastrophic forgetting；
- 每次新训练后仍必须跑旧 gate：focused pair、kNN/OOD safety、5/10 no-regression；
- 新 head 先 shadow，只能在“旧能力不退化 + 新 tail 正负例可分”后进入 opt-in。

在线含义也必须分层：

```text
candidate admission head:
  这个 true-RC negative column / batch 是否值得优先加入或有限延迟

branch-tail head:
  当前 Ryan-Foster pair / child ordering 是否可能减少后续 proof tail
```

如果一个候选在旧 head 看是好列，但新 head 看是 tail-risk，它不应被当作旧 admission 负例；它只说明该候选不适合作为 proof-tail 加速信号。这样才能保留 GAT 现在已有的列发现能力，同时让 GAT 新增“减少 20 规模证明时间”的能力。

## 专家分析后的理解：proof tail 需要 anytime official bound

`BPC_future/logical_graph/bpc_future_expert_analysis.md` 给出的核心判断是：当前 proof tail 最大的问题不是缺少一个更复杂的 completion bound，而是 pricing 只有“扫空后给 no-negative certificate”这一条强终止路径。

当前节点下界语义近似是：

```text
pricing exhausted and no negative journey
  -> lower bound official
pricing not exhausted
  -> RMP-only / heuristic, 不能用于 exact-safe fathom
```

专家建议把 exact pricing 改成 anytime proof procedure：即使没有扫空，也必须返回一个严格有效的 `global_remaining_rc_lb`。如果所有未探索 journey 的 reduced cost 都能证明至少为 `r_lb`，令：

```text
delta = max(0, -r_lb)
official_node_lb = z_RMP - active_fleet_limit * delta
```

直觉是：用 fleet dual repair 把所有潜在列的 reduced cost 修到非负，付出的代价是把节点 LB 保守地下调 `active_fleet_limit * delta`。这个 bound 不等于 full master LP certificate，但它是 branch-and-bound 可用的 official lower bound；只要它已经足够超过 incumbent，就可以 exact-safe fathom，不必把整个 pricing universe 扫空。

这直接解释了当前 20 规模的现象：我们已经能在深层节点看到 `direct_label_no_negative_journey`、`completion_bound_retry` 和 bound fathom，但它们出现得太晚，而且没有形成浅层可用的 corrected LB，导致树继续展开。

由此，GAT 的边界也更清楚：

- GAT 可以继续用于 true-RC verified batch admission、delay queue、pricing mode switch、CB trigger、branch ordering 和 exact judge 内部搜索顺序；
- GAT 不能当 pricing oracle、certificate source 或 official bound source；
- branch-impact GAT 的目标不应是 child width，而应是 `child corrected official LB`、`fathom probability`、`proof CPU`、`exact expansions`、`CB retries`；
- 新样本要做同 parent snapshot 的 counterfactual probes，并处理 right-censored child，而不是把 timeout child 简单标成 0。

我的新增疑问：

- 现有 `journey_pricing.py` 最小改动能否先从 completion-bound retry/frontier 中抽出一个保守 `global_remaining_rc_lb`，还是必须先重写成 heap/A* best-bound final judge？
- `active_fleet_limit` 是否始终是 `R_N` 的安全取值，还是要和 branch state、已固定 journey、task-cover 可推导上界取更小值？
- 对尚未生成 profile shard、start-time/path-option 分支、并行 worker shard，如果暂时没有 tight bound，应该返回哪个 trivial lower bound 才既安全又不至于完全无剪枝价值？
- limited strong-branch probe 的预算应该按 CPU、label expansion 还是 pricing frontier size 截断，才能得到可训练的 corrected-LB regret 标签？

## 3600s 20-scale 长跑：V154 + GAT 开启仍未闭合

按预先写好的标签 manifest：

- manifest：`BPC_future/logical_graph/run_reports/20260623_bpc_future_20scale_3600_probe_labels_zh.md`
- run dir：`BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600`
- instance：`tasks_020/greedy-anchor/apollo15_20km/...seed61308...json`
- 配置：GAT 开启，root56/depth3/width priority，cross-node physical/catalog cache 开启，diagnostic labels 开启，未 force pair。

结果：

```text
status = EXTERNAL_TIME_LIMIT
return_code = 124
wall_time = 3600.080041s
best_incumbent_seen_in_log = 503.939606 at t=2592.2s, node=48, depth=5
started_nodes = 63
queued_children = 86
bound_fathoms = 15
node_incomplete = 4
max_depth = 7
pricing_events = 468
completion_bound_related_events = 117
```

`results.csv` 因 external timeout 没有 solver final fields，最终以 run log / JSONL 审计为准。日志里的 incumbent 轨迹显示，root 早期在 `38.7s` 到 `506.923489`，之后直到 `2592.2s` 才改善到 `503.939606`。这说明 3600s 长跑不是完全停滞，但远远没有达到 20 规模 `200s OPTIMAL` 的 Stage 4 目标。

pricing reason 计数：

```text
streaming_partial_negative_journey = 142
negative_journey = 65
ng_dssr_time_limit = 59
no_negative_journey = 58
direct_label_no_negative_journey = 51
partial_negative_journey = 32
streaming_partial_dp_negative_journey = 31
negative_journeys_already_in_pool = 13
weak_negative_journeys_filtered = 4
time_limit = 4
direct_label_negative_journey = 2
```

这个分布很关键：不是单纯“找不到负列”，也不是单纯“最后一个节点 proof tail 卡死”。实际是负列生成、no-negative 证明、CB retry、分支扩树交替出现。后程确实出现连续 bound fathom，但节点树已经长到 60+，剪枝太晚。

审计结果：

```text
branch-impact:
  branch_training_row_count = 43
  active_touch_branch_count = 8
  inactive_only_branch_count = 22
  tail_class_counts = {
    completion_bound_tail: 30,
    early_branch_continues: 1,
    unprocessed_children: 12,
  }
  total_child_negative_pricing_events = 257
  total_child_completion_bound_retries = 126
  total_child_early_branch_triggers = 6

weak-negative:
  weak_event_count = 10
  total_weak_negative_journeys_filtered = 288
  repeated_weak_mask_count = 3

tail-impact rows:
  training_row_count = 53
  y_useful_tail_reduction = 0
  y_tail_risk = 53
  y_completion_bound_tail = 30
  y_weak_negative_filtered = 10
  y_inactive_only = 22

positive-gap:
  useful_tail_reduction_positive_count = 0
  positive_gap_reason = no_useful_tail_reduction_positive
```

报告文件：

- `BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_20scale_3600_v154_zh.md`
- `BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_20scale_3600_v154_zh.md`
- `BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_20scale_3600_v154_zh.md`
- `BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_positive_gap_20scale_3600_v154_zh.md`

结论：

V154/GAT 没有关掉，也不是完全没有作用：它能持续推进、能触发 completion-bound、后程也能 bound fathom 一些深层节点。但它没有真正解决 20 规模精确求解时间，因为它没有把 pricing 的局部证据转成浅层、可剪枝的 official lower bound，也没有学到哪一个 branch 会减少两边子树的总 proof CPU。

这次长跑和专家分析指向同一个下一步：先做 `global_remaining_rc_lb` 与 `official_node_lb = z_RMP - R_N * delta` 的 exact-safe 最小实现；GAT 继续保留，但短期只作为 admission / mode scheduling / branch ordering 的 shadow 或 opt-in hint，不碰 certificate。

## 下一步

主攻方向调整为先补 proof contract，再让 GAT 学真正的 proof ROI：

- 在 pricing 返回对象里新增 `global_remaining_rc_lb`、`bound_valid`、`frontier_state_count`，先实现 conservative 版本；
- 在 B&B 节点层新增 `bound_kind`、`pricing_global_rc_lb`、`dual_repair_delta`、`official_node_lb`；
- 用 `official_node_lb = z_RMP - active_fleet_limit * max(0, -global_remaining_rc_lb)` 做第一版 exact-safe corrected bound；
- 把当前 completion-bound retry / final judge 的 frontier、未处理 profile shard、未展开 path-option 都纳入 lower-bound 覆盖，不能覆盖时返回安全 trivial bound；
- 对 greedy/apollo20 做同一实例 A/B：旧 binary certificate only vs corrected official LB，目标是减少浅层之后的 children、CB retry CPU 和 p95 proof time；
- GAT/learning 继续开启，但短期只用于 true-RC batch admission、delay queue、mode scheduling、branch ordering shadow；
- branch-impact 新标签改为 counterfactual corrected-LB regret、child proof CPU、fathom probability、exact expansions、CB retries，并处理 right-censored child；
- 保留旧 5000 样本和旧 gate，新增标签 namespace，避免 branch-tail head 破坏已有 candidate admission 能力。

## 2026-06-23 V5 补充：branch-aware unique-task 与 AMCB

在 canonical random-TW 20 `seed61000` 上补跑了两个 proof-tail 探针：

- V5 branch-aware unique-task：300s 仍 `EXTERNAL_TIME_LIMIT`，但 node 1 `global_remaining_rc_lb` 从 V4 的 `-426.051783667` 收紧到 `-412.683770667`，说明 branch same/separate 松弛确实存在，但只解释了很小一部分尾部 gap。
- AMCB 全局 opt-in：300s 仍 `EXTERNAL_TIME_LIMIT`，root CB certificate 从 `104.93s` 变慢到 `130.66s`，node 1 `global_remaining_rc_lb=-414.107463667`，AMCB 因 `state_budget/deadline` disabled，不能作为全局开关。

当前结论：

- 20 规模还没有真正加速到 200s 目标；
- GAT/support-aware admission 对 root 有帮助，但 seed61000 node 1 的第一道门槛不是“把 frontier floor 抬到 0 就能 fathom”，而是 `z_RMP=580.221453667 < UB≈584.354872`；
- 直接全局打开更重的 route-aware/available-mask bound 会吃掉太多时间，而且不能改变当前 RMP objective；
- Tier 1 frontier refinement 只应作为 A 类节点工具：final-probe 已无待加入负列、`z_RMP >= UB - eps`、`fathom_rc_target` 存在、critical token/floor multiplicity 都小且 coverage 完整；
- 对 seed61000 node 1 这类 D 类节点，主线应转向 exact-safe early branch、branch-impact/child proof-cost、incumbent improvement、pricing-compatible cuts 或更强 formulation。

详细记录见：

- `BPC_future/logical_graph/run_reports/20260623_bpc_future_v5_branchaware_unique_task_and_amcb_probe_zh.md`

## 2026-06-23 V7 补充：水位式 frontier refinement 诊断

专家修正后，当前 frontier refinement 不再只盯一个最差 token，而是先计算当前节点要 fathom 所需的 reduced-cost 水位：

- 若 `z_RMP < UB - eps`，即使把所有 frontier token 证明到 `g>=0`，corrected node bound 也不能达到 incumbent，因此不应花 final-probe refinement 预算；
- 若 critical token 数很大，top-1/top-2 refinement 也不能改变 global floor，应 fail-fast 并记录分布。

已完成的实现：

- `JourneyPricingConfig/Result` 新增 `fathom_rc_target`、critical token、floor multiplicity、second/p05/p10/median active LB 等诊断；
- `FrontierBoundLedger` 支持安全更新 token lower bound，heap stale key 会被丢弃；
- driver 在 final-probe 前根据 `z_RMP/incumbent/R_N` 设置 target；target 不存在时 pricing 只记录诊断，不做 refinement。

canonical random-TW 20 `seed61000` 的 300s 诊断结果：

- status: `EXTERNAL_TIME_LIMIT`，wall `300.020187s`；
- root CB certificate: `105.138437s`；
- node 1 CB retry: `181.350206s`，`INCOMPLETE/time_limit`；
- node 1 `z_RMP=580.221453667`，当时 incumbent 约 `584.354872`，所以 `frontier_fathom_rc_target=null`；
- node 1 frontier 分布：`min=-412.683770667`、`second=-412.540795667`、`p05=-405.143052667`、`p10=-403.151726666`、`median=-395.956203667`。

最新结论：

- node 1 不是“单个 token 过低”导致不能剪枝，而是 `z_RMP` 本身低于 incumbent，proof-tail refinement 即使完美也无法 fathom；
- 下一步的 Tier 1 critical-token micro-expansion 只能作为 A 类节点工具：必须先满足 `z_RMP >= UB - eps`、`fathom_rc_target` 存在、critical token / floor multiplicity 稀疏、child 预算可控且 coverage 完整；seed61000 node 1 这类不可 fathom 的 D 类节点不应消耗 micro-expansion 预算，应同步关注 incumbent improvement、cuts/formulation、branch-impact / child proof cost，而不是继续全局加重 unique-route20 或 AMCB。

## 2026-06-23 修正：负列不会提高 `z_RMP`

需要明确修正一个表述：在最小化列生成中，加入新的负 reduced-cost 列只会让 RMP objective 下降或不变，不会提高 `z_RMP`。继续 CG 的意义是正确闭合 LP，不是把当前节点推入可剪枝区间。

对 seed61000 node 1：

- `z_RMP=580.221453667`
- incumbent 约 `584.354872`
- 即使完整证明 `global_remaining_rc_lb >= 0`，corrected node bound 最多也只是 `580.221453667`，仍然低于 incumbent。

因此 node 1 不属于 Tier 1 micro-expansion 可以直接 fathom 的节点。它更接近 Tail Action Controller 的 D 类：`z_RMP < UB - eps`，且 final probe 不能立即剪枝；若 CG 已经拖尾，应考虑 exact-safe early branch，并并行改善 incumbent、cuts/formulation 和 branch-impact。

Tier 1 micro-expansion 的适用范围收窄为 A 类节点：

- `z_RMP >= UB - eps`
- `fathom_rc_target` 存在
- `global_remaining_rc_lb` 有效且 frontier coverage 完整
- `global_remaining_rc_lb < fathom_rc_target`
- critical token count 和 floor multiplicity 都小
- 预计 child 总数不超预算
- frontier coverage 完整

如果 target 接近 0 但几百/几千 token 都低于 target，这是 B 类“大面积低水位”，不能逐 token split，应转向 aggregate route-aware bound、更强 completion relaxation、cuts/formulation 或 token region 重组。

2026-06-24 代码侧已把 Tail Action Controller 的 A 类标签收紧到这些必要条件：有 true-RC 负列时先继续 CG；缺 `fathom_rc_target`、global RC LB 无效、coverage 不完整、缺 global LB 或 global floor 已达到 target 时，都不会记录为 `FRONTIER_REFINEMENT`。这只是诊断分类收紧，不表示完整 Tier 1 split 已完成。

## 2026-06-23 V8 复验：Tail Action Controller 已绑定 incumbent

在 V8 初次 300s 诊断中发现 corrected-bound audit 调用没有统一传入 incumbent，导致 `tail_action=UNKNOWN`。修复后用同一 canonical random-TW 20 `seed61000` 跑 220s 复验，结果仍为 `EXTERNAL_TIME_LIMIT`，但分类字段已按预期写出。

复验输出：

- CSV: `BPC_future/results/20260623_v8_tail_action_controller_220_randomtw20_seed61000.csv`
- JSONL: `BPC_future/results/logs_20260623_v8_tail_action_controller_220_randomtw20_seed61000/...jsonl`

关键日志：

- root final retry: `time=104.954704s`，`z_RMP=580.044467333`，incumbent `584.354872`，`global_remaining_rc_lb=0.0`，`tail_action=EARLY_BRANCH`，`fathom_possible_if_rc_zero=false`；
- node 1 final retry: `time=198.026044s`，`z_RMP=580.221453667`，incumbent `584.354872`，`global_remaining_rc_lb=-412.683770667`，`tail_action=EARLY_BRANCH`，`fathom_possible_if_rc_zero=false`；
- node 1 `frontier_micro_expansion_attempted=0`，`frontier_refinement_reason=missing_fathom_rc_target`。

node 1 floor band：

- `frontier_floor_band_count_0_1=1`
- `frontier_floor_band_count_1=8`
- `frontier_floor_band_count_5=761`
- `frontier_floor_band_count_10=2704`
- `frontier_region_count=25589`

结论：controller 现在能把 seed61000 node 1 正确归到 D 类，不会误用 Tier 1 micro-expansion。下一步应把这个日志解析扩到 random-TW 20 的 60-instance 集合，统计 A/B/C/D 类比例，再决定 refinement、branch、incumbent/cuts 哪条线优先吃预算。

详细记录见：

- `BPC_future/logical_graph/run_reports/20260623_bpc_future_v7_waterline_frontier_refinement_diag_zh.md`

## 2026-06-23 V9：Tail Action D 类 opt-in early branch

进一步补充 180s canonical random-TW 20 `seed61000` signal run，把 `recent_active_support_additions` 和 `recent_rmp_objective_progress` 接入 corrected-bound audit，并把 D 类接成默认关闭的 exact-safe early branch opt-in。

输出：

- CSV: `BPC_future/results/20260623_v9_tail_action_early_branch_180_randomtw20_seed61000.csv`
- audit summary: `BPC_future/results/journey_tail_action_controller_audit_v9_tail_action_early_branch_180_seed61000_20260623/summary.json`
- report: `BPC_future/logical_graph/run_reports/20260623_bpc_future_v9_tail_action_early_branch_180_seed61000_zh.md`

审计结果：

- `row_count=10`
- `CONTINUE_COLUMN_GENERATION=6`
- `EARLY_BRANCH=4`
- `recent_active_support_addition_row_count=4`
- `recent_rmp_objective_progress_row_count=3`
- `fathom_possible_if_rc_zero_count=0`
- `micro_expansion_attempt_row_count=0`

最关键的一行是 node 1 `cg_iter=2`：`recent_true_rc_productivity=1`，但 `recent_active_support_additions=0`、`recent_rmp_objective_progress=0.0`，因此 controller 给出 `EARLY_BRANCH`，reason 为 `rmp_below_incumbent_weak_columns_no_active_or_objective_progress`。随后实际触发：

```text
time=139.743157
event=journey_early_branch_trigger
trigger=tail_action_controller
node_id=1
cg_iter=2
inherited_lower_bound=580.044467
rmp_objective=580.221454
exact_bound_available=false
child_lower_bound_exact=false
```

node 1 的两个 child 都以 `lower_bound=580.044467`、`lower_bound_exact=false` 入队，没有使用当前 `z_RMP=580.221454` 作为 exact bound。

这说明当前实现已经不再把“还能找到负列”粗略等同于 C 类。只有负列继续改变 active support 或让 RMP objective 有实际移动时，才归为 C 类继续短预算 CG；否则归为 D 类，下一步可走 exact-safe early branch / branch-impact，而不是消耗 Tier 1 micro-expansion。

但该 180s opt-in 探针仍为 `EXTERNAL_TIME_LIMIT`：D 类 early branch 避开了 node 1 的一次 tail，但后续 node 2 仍卡住。因此这不是 20 规模 200s 的完成证据，而是一个 exact-safe 调度改动。

扩展后的审计脚本新增 `early_branch_trigger_rows.jsonl/csv`，把 D 类触发和 child queue 绑定起来。V9 seed61000 结果：

- `early_branch_trigger_count=1`
- `tail_action_early_branch_trigger_count=1`
- `nonexact_early_branch_trigger_count=1`
- `tail_action_queued_child_count=2`
- `tail_action_nonexact_queued_child_count=2`
- `tail_action_observed_child_audit_count=0`
- `queued_child_ids=3,4`
- `queued_child_min_allowed_current_journeys=118`
- `queued_child_max_allowed_current_journeys=167`

这说明 D 类分支确实生成了两个 non-exact child，但 180s 内没有处理到它们；搜索先进入 root sibling node 2。下一步的重点应转向 child ordering / branch-impact：不是只问“要不要早分支”，而是要判断 D 类分支后的 child 是否应该优先处理，以及哪个 child 更可能降低后续 exact pricing / CB tail。

后续代码已补默认关闭的 `journey_tail_action_child_priority_enabled`：它允许 D 类 tail-action child 使用 `journey_tail_action_child_priority_width` 调整队列顺序，并在 `journey_child_queued` / tail-action 审计中记录 `queue_priority_width`。该开关只是调度优先级，不改变 lower bound、exactness、分支约束或剪枝；现有 V9 日志早于该补丁，不能作为速度收益证据。

## 2026-06-23 V10：D 类 child-priority fresh probe

为验证 child-priority 是否真的改变队列顺序，重新跑 canonical random-TW 20 `seed61000`，外部预算 220s，并显式打开：

```text
journey_tail_action_early_branch_enabled=True
journey_tail_action_early_branch_min_cg_iter=35
journey_tail_action_early_branch_child_min_cg_iter=2
journey_tail_action_early_branch_max_depth=1
journey_tail_action_child_priority_enabled=True
journey_tail_action_child_priority_width=-1
```

输出：

- CSV: `BPC_future/results/20260623_v10_tail_action_child_priority_220_randomtw20_seed61000.csv`
- JSONL: `BPC_future/results/logs_20260623_v10_tail_action_child_priority_220_randomtw20_seed61000/...jsonl`
- audit summary: `BPC_future/results/journey_tail_action_controller_audit_v10_tail_action_child_priority_220_seed61000_20260623/summary.json`
- audit report: `BPC_future/logical_graph/run_reports/20260623_bpc_future_v10_tail_action_child_priority_220_seed61000_zh.md`

结果仍为 `EXTERNAL_TIME_LIMIT`，wall `220.034807s`。

关键事件：

```text
125.603298s  root exact_completion_bound_retry OPTIMAL
125.685520s  root branch，child 1/2 lower_bound_exact=true
162.723293s  node 1 tail-action early branch，trigger=tail_action_controller
162.761930s  child 3 queued，queue_priority_width=-1，lower_bound_exact=false
162.761971s  child 4 queued，queue_priority_width=-1，lower_bound_exact=false
162.781012s  node 3 RMP starts
216.582741s  node 3 enters exact_pricing_completion_bound_retry
220.034807s  external timeout
```

审计摘要：

- `row_count=13`
- `CONTINUE_COLUMN_GENERATION=6`
- `FRONTIER_REFINEMENT=3`
- `EARLY_BRANCH=4`
- `early_branch_trigger_count=1`
- `tail_action_queued_child_count=2`
- `tail_action_nonexact_queued_child_count=2`
- `tail_action_observed_child_audit_count=4`
- `tail_action_child_min_queue_priority_width=-1`
- `tail_action_child_max_queue_priority_width=-1`

结论：

- child-priority 成功解决 V9 暴露的“D 类 child 生成了但 180s 内没处理到”的队列问题：V10 中 node 1 分支后下一条 RMP 是 node 3，而不是 root sibling node 2。
- 但它没有解决 20 规模 200s/220s optimal：node 3 本身在后段进入 completion-bound retry，并在外部 220s 超时。
- V10 旧日志中 node 3 前几轮 `rmp_objective >= incumbent`，controller 给出 `FRONTIER_REFINEMENT`，但这些行仍是 `negative_journey_requires_column_addition`，不是 final-probe 可直接剪枝的 Tier 1 机会；后续控制器已收紧为“有负列先继续 CG”。到 no-negative 时，node 3 已变为 `rmp_objective=584.2437713 < incumbent=584.354872`，再次不属于可直接 fathom 的 A 类。

因此下一步不应继续只调队列顺序；主线应转到两件事：

1. 对 node 3 类 child 的 proof tail 做 exact-safe 提前 close：更早的 completion-bound handoff、child-level tail action gate、或 batch/aggregate completion relaxation。
2. 继续改善 incumbent/cuts/branch-impact，让子节点在 no-negative/final-probe 时仍保持 `z_RMP >= UB - eps`，否则 Tier 1 micro-expansion 仍没有直接剪枝空间。

## 2026-06-23 V11b：no-column D 类 gate fresh probe

V10 暴露的下一个阻塞是 node 3 在 local no-column 后进入 completion-bound retry。为验证是否可以 exact-safe 地跳过这类 retry，新增默认关闭的 no-column D 类 early-branch gate：

```text
journey_tail_action_no_column_early_branch_enabled=True
journey_tail_action_no_column_early_branch_min_depth=2
journey_tail_action_no_column_early_branch_max_depth=2
journey_tail_action_no_column_early_branch_child_min_cg_iter=4
```

这个 gate 只改变搜索调度：

- 不产生 certificate；
- 不把当前 RMP objective 当 exact node bound；
- 不用该 bound 剪枝；
- child 继承已有合法祖先下界，且 `lower_bound_exact=false`；
- child 仍必须通过 exact pricing / completion-bound closure。

输出：

- CSV: `BPC_future/results/20260623_v11b_tail_action_no_column_depth2_300_randomtw20_seed61000.csv`
- JSONL: `BPC_future/results/logs_20260623_v11b_tail_action_no_column_depth2_300_randomtw20_seed61000/...jsonl`
- audit summary: `BPC_future/results/journey_tail_action_controller_audit_v11b_tail_action_no_column_depth2_300_seed61000_20260623/summary.json`
- audit report: `BPC_future/logical_graph/run_reports/20260623_bpc_future_v11b_tail_action_no_column_depth2_300_seed61000_zh.md`

结果仍为 `EXTERNAL_TIME_LIMIT`，wall `300.029456s`。

关键事件：

```text
90.313525s   root local no-column D 类 audit，但 depth gate 阻止 root 误分支
105.265030s  root completion-bound certificate
142.493001s  node 1 普通 D 类 tail-action branch，child 3/4 lower_bound_exact=false
196.221668s  node 3 no-column D 类 branch，tail_action_no_column=true
231.713072s  node 4 cg1 进入 completion-bound retry
276.772964s  node 5 开始处理
294.162041s  node 5 仍找到 true negative journey
300.029456s  external timeout
```

审计摘要：

- `row_count=17`
- `tail_action_early_branch_trigger_count=2`
- `tail_action_no_column_early_branch_trigger_count=1`
- `tail_action_queued_child_count=4`
- `tail_action_nonexact_queued_child_count=4`
- `tail_action_child_min_queue_priority_width=-1`

结论：

- V11b 证明 no-column D 类 gate 可以 exact-safe 地跳过 V10 的 node 3 completion-bound retry。
- root 没有被误分支，说明 `min_depth=2` 的保护必要且有效。
- 但 300s 仍未 OPTIMAL，说明当前 20 规模阻塞不是单个 node3 retry，而是 sibling/deeper child 的 proof-tail 链。
- 如果下一步把 no-column gate 放宽到 cg1，必须同时加 branch-width、remaining time、depth、child-budget 等限制，否则可能只是更快制造更深子树。

因此下一阶段应三线并行：

1. 完成严格 gated 的 deterministic Tier 1，只用于 `z_RMP >= UB - eps` 的 A 类稀疏低水位节点。
2. 改善节点进入可剪枝区间的能力：incumbent improvement、pricing-compatible cuts、更强 formulation、branch strong-bound gain、child proof cost 和 child ordering。
3. 保留 GAT，但让它学习 tail action 调度：`time_to_next_official_bound`、`corrected_fathom_probability`、`final_probe_cpu`、`child_safe_bound_gain`、`child_time_to_certificate`、`incumbent_improvement_probability`。Tier 1 正确性仍由 deterministic exact-safe split 保证，不能交给 GAT。

## 2026-06-23 V12：cg1 no-column + width guard probe

V11b 后，补了 no-column D 类 gate 的宽度/child-budget 保护：

```text
journey_tail_action_no_column_early_branch_max_pool_child_width
journey_tail_action_no_column_early_branch_max_pool_total_child_width
journey_tail_action_no_column_early_branch_max_pool_balance_gap
```

这些限制只在配置后生效；若配置了限制但缺少 branch width context，则 fail-closed，不触发 early branch。触发日志会记录：

```text
no_column_branch_task_i/task_j
no_column_branch_pool_max_child_width
no_column_branch_pool_total_child_width
no_column_branch_width_guard_reason
```

V12 使用 canonical random-TW 20 `seed61000`，260s 预算，允许 depth=2、cg>=1 的 no-column 分支，并设置：

```text
max_pool_child_width=180
max_pool_total_child_width=360
max_pool_balance_gap=180
```

输出：

- CSV: `BPC_future/results/20260623_v12_no_column_cg1_widthguard_260_randomtw20_seed61000.csv`
- JSONL: `BPC_future/results/logs_20260623_v12_no_column_cg1_widthguard_260_randomtw20_seed61000/...jsonl`
- audit summary: `BPC_future/results/journey_tail_action_controller_audit_v12_no_column_cg1_widthguard_260_seed61000_20260623/summary.json`
- audit report: `BPC_future/logical_graph/run_reports/20260623_bpc_future_v12_no_column_cg1_widthguard_260_seed61000_zh.md`

结果仍为：

```text
status=EXTERNAL_TIME_LIMIT
wall_time=260.036938s
```

关键事件：

```text
160.171699s  node 1 普通 D 类 tail-action branch，child 3/4 lower_bound_exact=false
214.124725s  node 3 no-column D 类 branch，RF(4,12)，pool max/total=111/202，guard=ok
249.337568s  node 4 cg1 no-column D 类 branch，RF(1,9)，pool max/total=166/302，guard=ok
249.375707s  node 5 starts
260.036938s  external timeout
```

审计摘要：

- `tail_action_early_branch_trigger_count=3`
- `tail_action_no_column_early_branch_trigger_count=2`
- `tail_action_queued_child_count=6`
- `tail_action_nonexact_queued_child_count=6`
- child activity:
  - node 1 trigger subtree：`started=2/2` direct children，`subtree_nodes=6`，`pricing=11`，`negative_pricing=3`，`subtree_no_column=2`，observed span `90.093774s`
  - node 3 no-column subtree：`started=1/2` direct children，`pricing=1`，`negative_pricing=0`，observed span `36.140748s`
  - node 4 no-column subtree：`started=0/2` direct children，observed span `0.038115s`

结论：

- width guard 生效并保留了可审计字段；
- cg1 no-column gate 确实跳过了 V11b 中 node 4 的 completion-bound retry；
- 但 260s 仍没有 OPTIMAL，说明当前动作主要把 proof tail 从 node 3/4 下放到 node 5 及更深子树；
- 因此该 gate 只能继续作为受控 opt-in，不能作为 20-scale 加速达标方案。下一步的 branch-impact/GAT 标签应直接使用 subtree pricing、negative-pricing、completion retry、no-column-chain、child-start/timeout 这些 proof-cost 指标，而不是只看当前 branch pair 的 pool width 或是否跳过一次 retry。

## 2026-06-23 Tail-Impact Training Rows v2：接入 tail-action proof-cost

已扩展 `BPC_future/scripts/build_journey_tail_impact_training_rows.py`，新增 `--tail-action-input`，可读取 Tail Action Controller 审计目录中的 `early_branch_trigger_rows.jsonl`，把 early branch 后的子树 proof-cost 转成统一训练行。

V12 tail-action 输入：

```text
BPC_future/results/journey_tail_action_controller_audit_v12_no_column_cg1_widthguard_260_seed61000_20260623
```

输出：

```text
BPC_future/results/journey_tail_impact_training_rows_v12_tail_action_20260623
BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_v12_tail_action_zh.md
```

摘要：

```text
training_row_count = 3
source_counts = {'tail_action_proof_cost': 3}
tail_class_counts = {'tail_action_branch': 1, 'tail_action_no_column': 2}
y_tail_risk positives = 3
y_useful_tail_reduction positives = 0
child_negative_pricing_events total = 3
child_early_branch_triggers total = 2
child_unstarted total = 3
subtree_no_column_chain total = 2
```

结论：

- 这一步仍不改变 solver，也不提供 certificate / official bound；
- V12 tail-action row 可以作为 hard-negative / tail-risk 数据；
- 由于 `y_useful_tail_reduction=0`，它不能单独训练“选它会加速”的 GAT head；
- 下一批数据采集必须围绕同一 parent context 做 child ordering / branch candidate counterfactual，目标是找到 subtree proof-cost 真下降的正例。

## 2026-06-23 V13：depth-scoped child-ordering counterfactual

为采集 useful-tail-reduction 正例，新增 exact-safe child-ordering opt-in：

```text
journey_child_priority_mode=force_child_kind_depth:<depth>:same_vehicle|separate_vehicle
```

这个开关只改变 child 入队顺序：

- 不改变 branch constraint；
- 不改变 lower bound；
- 不把 RMP objective 当 exact bound；
- 不剪枝；
- child 仍靠 exact pricing / completion-bound closure。

同时扩展 `build_journey_branch_tail_positive_runbook.py`，可以从 V12 tail-impact rows 读取 `log_file`，反查该 node 的祖先 branch path，自动生成：

```text
journey_branch_candidate_priority=force_pair_depth:...
journey_child_priority_mode=force_child_kind_depth:...
```

V13 runbook：

```text
BPC_future/results/journey_branch_tail_positive_runbook_v13_child_order_20260623
BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_tail_positive_runbook_v13_child_order_zh.md
```

已执行两条 canonical random-TW 20 `seed61000` probe，均为 260s：

| probe | status | 关键对比 |
|---|---|---|
| node3 `RF(4,12)` separate-first | `EXTERNAL_TIME_LIMIT` | node3 subtree 从 V12 的 `pricing=1, negative=0, span=36.14s` 变成 `pricing=3, negative=1, span=44.70s` |
| node4 direction same-first | `EXTERNAL_TIME_LIMIT` | node1 subtree `pricing=17, negative=6, span=117.94s`；node3 subtree `pricing=7, negative=3, span=82.83s` |

结论：

- V13 验证了 counterfactual 采样闭环已经可执行：tail-action proof-cost row -> runbook -> forced replay -> audit -> training rows。
- 但两条 child-ordering counterfactual 都不是正例，仍然是 hard negatives。
- 当前证据说明“只换同一 branch 下的 child 顺序”不是 seed61000 的主杠杆；下一步要引入更强候选来源，例如 branch-impact score、incumbent/cut 变化、或更局部的 exact-safe completion relaxation。

## 2026-06-23 V14/V15：branch-pair alt replay 与 path-aware 修正

在 V13 hard negative 之后，runbook 继续扩展为可读取 tail-action row 对应 JSONL 中的 `journey_branch_candidates.priority_top`，自动生成目标节点的替代 Ryan-Foster pair replay。这个扩展仍是 opt-in 诊断：只改变分支候选选择，不改变 bound、certificate、pricing closure 或剪枝。

V14 先暴露了一个重要控制问题：

```text
journey_branch_candidate_priority = force_pair_depth:...
```

该语法只按 depth 生效，不按祖先路径生效。因此当目标 depth 有 sibling node 时，同一 depth 的兄弟节点也会被一起强制同一个 pair。V14 entry 13 的 depth-only `[4,14]` replay 中，node3 和 node4 都被改成 `[4,14]`，所以它不能解释为单个 node 的反事实。

已新增 path-aware replay 语法：

```text
journey_branch_candidate_priority = force_pair_path:0:i,j=kind;1:k,l=kind;2:target_i,target_j
```

语义：

- 只有当前 node 的祖先 `BranchConstraint` 完整匹配前面的 path segment，才在目标 depth 强制 pair；
- sibling node 的祖先路径不匹配时，`forced_pair=None`，回退默认 branch selection；
- 这仍只是 replay / sampling 控制，不提供 official bound，不改变 exact pricing certificate。

V15 runbook：

```text
BPC_future/results/journey_branch_tail_positive_runbook_v15_path_alt_pair_20260623
BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_tail_positive_runbook_v15_path_alt_pair_zh.md
```

已执行 V15 entry 13：

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
time_limit = 260
status = EXTERNAL_TIME_LIMIT
wall_time = 260.042870s
```

path-aware 绑定检查：

```text
depth=1 node1: forced_pair=None, selected=(2,10)
depth=2 target path: forced_pair=[4,14], forced_pair_matched=true, selected=(4,14)
depth=2 sibling path: forced_pair=None, selected=(1,9)
```

同口径 proof-cost 对比：

```text
V12_base:                  pricing=12, neg=3, early=2, no_col=2, max_span=90.094
V13_node4_same_depth_only: pricing=24, neg=9, early=2, no_col=2, max_span=117.941
V14_alt_4_14_depth_only:   pricing=20, neg=7, early=2, no_col=2, max_span=112.413
V15_alt_4_14_path_aware:   pricing=22, neg=9, early=2, no_col=2, max_span=114.697
```

结论：

- `force_pair_path` 是后续 branch counterfactual 的必要控制方式；`force_pair_depth` 只能用于全 depth 策略测试，不能作为 node-specific 标签。
- `[4,14]` path-aware 替代 pair 不是 useful-tail-reduction 正例；仍为 hard negative。
- 当前 pool width / total width 下降并不等价于 proof tail 下降。branch-impact/GAT 标签必须继续看 subtree pricing、true negative、no-column chain、child start/timeout 等后验成本。

## 2026-06-24 V16：late-negative tail 审计接入 tail-impact rows

为回答“proof tail 到底是 weak false-negative 还是 true-RC 负列仍在拖尾”，新增只读审计：

- `BPC_future/scripts/audit_journey_late_negative_tail.py`
- `BPC_future/tests/test_journey_late_negative_tail_audit.py`

它把 solver JSONL 中的 pricing event 与 column-addition event 绑定，区分 true negative active-support-changing、true negative inactive-only、未观察到 addition 的 true negative，以及 weak/profile filtered negative。该脚本不运行 BPC / pricing / RMP，不提供 certificate 或 official bound。

V12 no-column seed61000，取 `time >= 150s`：

```text
tail_event_count = 4
true_negative_event_count = 4
weak_filtered_event_count = 0
weak_false_negative_event_count = 0
total_active_changed_task_sets = 2
total_inactive_changed_task_sets = 5
tail_class_counts = {'true_negative_active_support_changing': 2, 'true_negative_inactive_only': 2}
```

V15 path-aware `[4,14]` hard-negative replay，取 `time >= 150s`：

```text
tail_event_count = 5
true_negative_event_count = 5
weak_filtered_event_count = 0
weak_false_negative_event_count = 0
total_active_changed_task_sets = 2
total_inactive_changed_task_sets = 25
tail_class_counts = {'true_negative_active_support_changing': 2, 'true_negative_inactive_only': 3}
```

解释：

- 这两条 tail 后段都不是 weak-only false-negative 主导，而是 exact true-negative tail；
- V15 path-aware 替代 pair 没有减少 active-support-changing burden，反而显著增加 inactive-only changed task sets；
- 所以单独扩大 weak materialization 或只做 weak-delay，不会解决 seed61000 这段 tail；
- 下一步的 GAT/admission 使用点应区分 active-support-changing / new task-set true negative 与 inactive-only replacement pressure。

`build_journey_tail_impact_training_rows.py` 已扩展 `--late-negative-input`，schema 升到 v3。V16 输出：

```text
output_dir = BPC_future/results/journey_tail_impact_training_rows_v16_late_negative_v12_after150_20260624
training_row_count = 7
source_counts = {'late_negative_tail': 4, 'tail_action_proof_cost': 3}
y_late_true_negative = 4
y_late_active_support_changing = 2
y_late_inactive_only = 2
y_late_weak_filtered = 0
y_useful_tail_reduction = 0
contrastive_tail_training_ready = false
tail_label_training_ready = false
```

结论：

- V16 没有让 20 规模变快，也不是 production training set；
- 它把 tail 结构拆成可学习字段，当前仍是 hard-negative / tail-risk / active-vs-inactive 数据；
- `y_useful_tail_reduction` 仍为 0，不能直接训练“选好分支/好候选”的 GAT；
- 支持后续实现默认关闭的 support-aware admission/delay：优先 active-support-changing 和 new task-set，inactive-only 只能 delay/降权，certificate 前必须 deterministic fallback 释放，不能永久丢列。

## 2026-06-24 V17：support-aware admission/delay 默认关闭实现

已把 V16 的 active-vs-inactive 结论接入在线 GAT admission scheduler，但仍保持默认关闭。

代码改动：

- `GATAdmissionQueue` 支持 candidate metadata 触发 forced high-priority；
- forced high-priority 只对 true-RC negative 生效，true-RC nonnegative 仍会被 `REJECT_NONNEGATIVE_ONLY` 拒绝；
- `_journey_gat_target_mode_admission_schedule()` 新增 support-aware 上下文：
  - 当前 active support task sets；
  - 当前 pool dominant task-set costs；
  - support overlap threshold；
- scheduler 会把 candidate 分类为：
  - `active_support_changing`
  - `new_task_set`
  - `inactive_only_replacement`
  - `duplicate_or_other`
- 默认 high-priority 类别为 `active_support_changing` 和 `new_task_set`；
- inactive-only replacement 默认可 demote 到 delay queue，即使旧 safe ID 命中也可以延迟。

新增配置：

```text
journey_gat_admission_support_aware_enabled
journey_gat_admission_support_high_priority_kinds
journey_gat_admission_support_demote_inactive_only
journey_gat_admission_support_overlap_threshold
```

日志新增：

```text
support_aware_admission_enabled
support_candidate_active_support_changing_journeys
support_candidate_new_task_set_journeys
support_candidate_inactive_only_journeys
support_online_high_priority_journeys
support_high_priority_journeys
support_delayed_inactive_only_journeys
support_demoted_safe_hit_journeys
```

精确性边界：

- 只调度 true-RC verified candidate；
- 不改变 pricing oracle；
- 不提供 certificate；
- 不剪枝；
- 不把 delay queue 当 proof；
- delayed true-negative 到期或 certificate 前仍由现有 finite-delay queue 释放，最终证明仍靠 exact pricing closure。

当前状态：

- 单元级 exact-safe 行为已验证；
- 已跑一个 random-TW 20 seed61000 小预算 opt-in probe；
- 因为仍为外部超时且没有 paired baseline 对照，不能声称 20 规模已经加速，只能说 support-aware admission/delay 的默认关闭实现和在线日志/release 行为已验证。

V17b 130s opt-in probe：

```text
results = BPC_future/results/20260624_v17b_support_aware_admission_130_randomtw20_seed61000.csv
logs    = BPC_future/results/logs_20260624_v17b_support_aware_admission_130_randomtw20_seed61000
status  = EXTERNAL_TIME_LIMIT
wall    = 130.026554s
```

admission 摘要：

```text
journey_gat_target_mode_admission events = 35
scheduled = 11
bypassed = 24
support_enabled_rows = 11
candidate_journeys = 109
admitted_journeys = 108
true_negative_journeys = 26
high_priority_journeys = 24
delay_queue_journeys = 2
released_journeys = 1
support_active = 19
support_new = 23
support_inactive = 2
support_high = 24
support_delayed_inactive = 2
support_demoted_safe = 0
```

关键日志：

```text
cg_iter=31 heuristic: inactive-only true negative delayed,
  delay_queue_size=1, certificate_blocked_by_delayed_negative=true

cg_iter=32 heuristic: delayed negative released,
  released_journeys=1, delay_queue_size=0,
  certificate_blocked_by_delayed_negative=false
```

解释：V17 的 finite-delay / release 机制在线生效；但 130s 仍外部超时，这只是机制验证，不是 wall-time ROI 证据。

## 2026-06-24 V18：root-safe support-aware delay

V17b 和当前默认 baseline 做同 budget 对照后，暴露出 root 阶段 delay inactive-only 的负效应：

```text
baseline_default_130:
  status = EXTERNAL_TIME_LIMIT
  root_cb_retry_time = 90.987572s
  root_branch_time = 105.531289s
  max_depth = 1
  added_journeys = 110
  inactive_changed_task_sets = 105

v17b_support_delay_root_130:
  status = EXTERNAL_TIME_LIMIT
  root_cb_retry_time = 114.484022s
  root_branch_time = None
  max_depth = 0
  added_journeys = 108
  inactive_changed_task_sets = 103
  support_delayed_inactive = 2
```

结论：root 阶段延迟 2 个 inactive-only true negative 没有带来加速，反而把 root completion-bound retry 推迟约 23.5 秒，并导致 130s 内没有进入分支。因此不能把 root inactive-only delay 作为默认 opt-in 策略。

V18 修正：

- 新增 `journey_gat_admission_support_delay_min_depth`，默认 `1`；
- 当 `depth < support_delay_min_depth` 时，inactive-only 不进 delay queue，而是 forced admit，并记录 `support_delay_depth_blocked_journeys`；
- 当 `depth >= support_delay_min_depth` 时，才允许 inactive-only 进入 finite-delay queue；
- active-support-changing / new task-set 仍可 high-priority；
- certificate / exact pricing 边界不变。

V18 同 budget opt-in probe：

```text
v18_support_root_safe_130:
  status = EXTERNAL_TIME_LIMIT
  root_cb_retry_time = 90.478242s
  root_branch_time = 105.094511s
  max_depth = 1
  added_journeys = 110
  inactive_changed_task_sets = 105
  support_delayed_inactive = 0
  support_delay_depth_blocked = 1
```

V18 基本恢复了 baseline 的 root 进度，但仍不是加速证据。下一步应在 depth>=1 的 branch tail 上做 paired probe，看 inactive-only delay 是否真的减少 child proof cost、CB retry 和 wall time。

## 2026-06-24 V19：branch-tail support-aware paired probe

继续使用 canonical random-TW 20 `seed61000`，220s 外部预算，跑当前默认 baseline、V18 root-safe support-aware，以及显式把 `exact` 加入 admission scheduler pricing kinds 的 opt-in：

```text
v19a_default_baseline_220:
  status = EXTERNAL_TIME_LIMIT
  wall = 220.018935s
  root_branch_time = 104.760930s
  node1_window = 104.761s -> 197.915s
  node2_window = 197.916s -> 218.344s
  depth1_pricing = 10
  depth1_added_journeys = 3
  depth1_inactive_changed_task_sets = 3

v19b_support_root_safe_220:
  status = EXTERNAL_TIME_LIMIT
  wall = 220.019739s
  root_branch_time = 105.825993s
  node1_window = 105.826s -> 198.909s
  node2_window = 198.909s -> 218.425s
  depth1_added_journeys = 3
  support_delayed_inactive = 0
```

V19b 没有真正调度 depth=1 的 negative exact columns：两条 depth=1 admission 事件都是 `pricing_kind_not_mutated`，因为默认 mutating pricing kinds 仍只包括 `heuristic` 和 hidden-negative worker。该配置因此只能说明 root-safe support-aware 不再伤害 baseline，不能证明 branch-tail delay 有效。

为确认这个 gap，又跑了 `v19c_support_root_safe_exact_optin_220`：

```text
v19c_support_root_safe_exact_optin_220:
  status = EXTERNAL_TIME_LIMIT
  wall = 220.019074s
  root_branch_time = 105.205676s
  node1_window = 105.206s -> 197.764s
  node2_window = 197.764s -> 218.228s
  depth1_candidate_journeys = 3
  depth1_true_negative_journeys = 3
  depth1_support_active = 3
  depth1_support_new = 2
  depth1_support_inactive = 0
  support_delayed_inactive = 0
```

结论：这条 seed61000 branch-tail 不是 inactive-only delay 的正例。把 exact 加入 opt-in 后，depth=1 的 3 个 true-negative 都是 active-support-changing / new task-set，没有 inactive-only 可以延迟，所以搜索轨迹与 baseline 基本一致，仍然 220s 外部超时。

本轮还补了一个默认无扰动观测改动：即使 `exact` 默认不属于 mutating pricing kind，`journey_gat_target_mode_admission` 的 bypass 日志也会写 `support_candidate_active_support_changing_journeys` / `support_candidate_new_task_set_journeys` / `support_candidate_inactive_only_journeys`。这不改变列加入顺序、不影响证书，只是为后续 random-TW 20 60-instance 的 branch exact 负列构成统计提供数据。

下一步不能继续只调 inactive-only delay。应先用默认无扰动日志扩到 random-TW 20 的 60-instance，判断 branch exact tail 中 inactive-only 到底占多少；同时把 GAT 目标转到 branch-impact / child proof-cost / incumbent-search 调度。

## 2026-06-24 V20：branch exact support-aware shadow audit

新增只读审计脚本：

```text
BPC_future/scripts/audit_journey_support_aware_branch_exact_tail.py
```

它读取 solver JSONL 中的 `journey_gat_target_mode_admission`，默认筛选 `depth>=1` 且 `pricing_kind` 以 `exact` 开头的 branch exact tail，统计 active-support-changing、new task-set、inactive-only、delayed inactive-only 以及 support-aware 是否启用。该脚本不运行 BPC / pricing / RMP，不产生 certificate 或 official bound；输出 `summary.json`、`support_aware_branch_exact_tail_rows.jsonl/csv` 和中文报告。

用 V19b/V19c 旧日志验证后，又补跑了一个 160s shadow-only probe：

```text
results = BPC_future/results/20260624_v20_support_shadow_nomutate_160_randomtw20_seed61000.csv
logs    = BPC_future/results/logs_20260624_v20_support_shadow_nomutate_160_randomtw20_seed61000
audit   = BPC_future/results/journey_support_aware_branch_exact_tail_v20_shadow_seed61000_20260624
report  = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_support_aware_branch_exact_tail_v20_shadow_seed61000_zh.md
```

V20 的运行配置：

```text
journey_gat_admission_scheduler_enabled=True
journey_gat_admission_support_aware_enabled=True
journey_gat_admission_allow_unsourced_delay=True
journey_gat_admission_scheduler_pricing_kinds=[]
```

这表示 scheduler runtime 存在，但所有 pricing kind 都不 mutating；GAT 不改变任何列加入，只记录 support-aware 分类。

V20 审计结果：

```text
admission_event_count = 2
support_enabled_event_count = 2
pricing_kind_counts = {"exact": 2}
reason_counts = {"pricing_kind_not_mutated": 2}
total_candidate_journeys = 3
total_support_active_journeys = 3
total_support_new_journeys = 2
total_support_inactive_journeys = 0
support_inactive_share = 0.0
runs_bpc_or_pricing = false
certificate_effect = false
official_bound_effect = false
```

这确认 V20 可以作为 random-TW 20 60-instance 的无扰动统计入口。当前 seed61000 仍支持同一个判断：这条 branch exact tail 不是 inactive-only delay 正例，下一步应扩样本统计，而不是继续在该实例上调 delay 阈值。

## 2026-06-24 V21：random-TW 20 60-instance shadow 统计

使用 V20 shadow-only 配置扩到 canonical random-TW 20 的 60-instance：

```text
results = BPC_future/results/20260624_v21_support_shadow_nomutate_160_randomtw20_60instances.csv
logs    = BPC_future/results/logs_20260624_v21_support_shadow_nomutate_160_randomtw20_60instances
audit   = BPC_future/results/journey_support_aware_branch_exact_tail_v21_shadow_randomtw20_60instances_20260624
report  = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_support_aware_branch_exact_tail_v21_shadow_randomtw20_60instances_zh.md
```

批跑配置仍为：

```text
journey_gat_admission_scheduler_enabled=True
journey_gat_admission_support_aware_enabled=True
journey_gat_admission_allow_unsourced_delay=True
journey_gat_admission_scheduler_pricing_kinds=[]
```

也就是只记录 support-aware 分类，不让 GAT 改变任何列加入顺序。

160s shadow-only 批跑终态：

```text
60 instances
OPTIMAL = 17
TIME_LIMIT = 2
EXTERNAL_TIME_LIMIT = 41
```

这不是 200s official gate，也不是加速达标证据；它只用于采集 branch exact tail 构成。

V21 审计结果：

```text
log_count = 60
admission_event_count = 219
support_enabled_event_count = 219
pricing_kind_counts = {"exact": 219}
reason_counts = {"pricing_kind_not_mutated": 171, "certificate_candidate_release": 48}
depth_counts = {"1": 105, "2": 76, "3": 28, "4": 5, "5": 2, "6": 3}
total_candidate_journeys = 1890
total_support_active_journeys = 563
total_support_new_journeys = 1684
total_support_inactive_journeys = 132
support_inactive_share = 0.055485
support_tail_class_counts = {
  "active_support_changing": 168,
  "new_task_set": 47,
  "inactive_only": 4
}
runs_bpc_or_pricing = false
certificate_effect = false
official_bound_effect = false
```

结论：branch exact tail 的主量不是 inactive-only。按 journey 计 inactive-only 只占约 `5.55%`；按事件主类，纯 inactive-only 只有 `4/219`。因此当前不应继续围绕 inactive-only delay 做 A/B 或调阈值。V21 把方向进一步收窄到：

- branch-impact：预测哪个 branch pair 会减少后续 exact pricing events / completion-bound retry / subtree proof cost；
- child proof-cost / ordering：优先处理更快 close 或更可能提高 safe bound 的 child；
- incumbent-search / cuts / formulation：让节点进入可剪枝区间，而不是依赖更多负列提高 `z_RMP`。

## 2026-06-24 V22：random-TW 20 60-instance branch-impact 只读审计

为确认 V21 这批 canonical random-TW 20 60-instance shadow logs 能否直接生成 branch-impact 训练 row，运行：

```text
script = BPC_future/scripts/audit_journey_branch_impact.py
input  = BPC_future/results/logs_20260624_v21_support_shadow_nomutate_160_randomtw20_60instances
audit  = BPC_future/results/journey_branch_impact_audit_v22_shadow_randomtw20_60instances_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v22_shadow_randomtw20_60instances_zh.md
```

审计是只读的，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。脚本已补 `right_censored`、`label_observation_complete`、`usable_for_branch_impact_training`，防止把外部 160s 截断后的未处理 child 误当成稳定标签。

V22 摘要：

```text
log_count = 60
branch_count = 176
branch_training_row_count = 176
tail_class_counts = {
  "completion_bound_tail": 110,
  "negative_chain_continues": 10,
  "unprocessed_children": 56
}
candidate_log_branch_count = 0
right_censored_branch_count = 170
complete_label_branch_count = 6
usable_branch_impact_training_count = 0
active_touch_branch_count = 27
inactive_only_branch_count = 74
total_child_negative_pricing_events = 647
total_child_completion_bound_retries = 437
total_child_early_branch_triggers = 0
```

结论：

- 这批 V21 日志不能直接作为 GAT branch-impact 正例训练集：没有 branch-candidate 特征，且 170/176 个 branch row 右删失；
- 它可以作为 proof-cost 诊断：child completion-bound tail 是主量，后续负列链仍存在；
- 下一批 random-TW 20 600s 诊断必须打开 branch candidate logging，并把 right-censoring 作为训练 row 过滤条件；否则只会继续得到 hard-negative / tail-risk 数据。

## 2026-06-24 V23：branch-candidate log 通路验证

为确认 V22 的 `candidate_log_branch_count=0` 是配置问题而不是日志/审计代码问题，单独跑 canonical random-TW 20 `seed61000` 130s，只打开：

```text
journey_branch_candidate_log_top_n = 12
```

输出：

```text
CSV    = BPC_future/results/20260624_v23_branch_candidate_log_130_randomtw20_seed61000.csv
logs   = BPC_future/results/logs_20260624_v23_branch_candidate_log_130_randomtw20_seed61000
audit  = BPC_future/results/journey_branch_impact_audit_v23_branch_candidate_log_130_seed61000_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v23_branch_candidate_log_seed61000_zh.md
```

结果是 `EXTERNAL_TIME_LIMIT`，不是性能证据；但字段通路验证成功：

```text
branch_count = 1
candidate_log_branch_count = 1
selected_match_count = 1
top_contains_branch_count = 1
top_first_branch_count = 1
priority_top_first_branch_count = 1
right_censored_branch_count = 1
usable_branch_impact_training_count = 0
```

结论：下一批 600s branch-impact 采样必须显式设置 `journey_branch_candidate_log_top_n=12` 或更高。V23 仍右删失，所以不能作为训练正例；它只证明下一批日志能够包含分支候选特征。

## 2026-06-24 V24：600s 完整 branch-impact 标签小样本

从 V21 的 random-TW 20 60-instance 结果中选了 3 个 160s 内 `OPTIMAL` 且有 branch 的实例，使用 600s 上限重跑并打开：

```text
journey_branch_candidate_log_top_n = 12
```

输出：

```text
CSV    = BPC_future/results/20260624_v24_branch_candidate_log_600_randomtw20_3opt_branch.csv
logs   = BPC_future/results/logs_20260624_v24_branch_candidate_log_600_randomtw20_3opt_branch
audit  = BPC_future/results/journey_branch_impact_audit_v24_branch_candidate_log_600_3opt_branch_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v24_branch_candidate_log_3opt_branch_zh.md
```

3 个实例全部 `OPTIMAL`，wall 约 `156.94s / 128.99s / 42.29s`。审计摘要：

```text
branch_count = 6
candidate_log_branch_count = 6
complete_label_branch_count = 6
right_censored_branch_count = 0
usable_branch_impact_training_count = 6
tail_class_counts = {'completion_bound_tail': 6}
active_touch_branch_count = 1
inactive_only_branch_count = 5
total_child_negative_pricing_events = 48
total_child_completion_bound_retries = 28
```

结论：字段通路和完整标签通路已经可用；但 V24 仍只是当前 fractionality top-1 策略的结果标签，不能替代同节点 alternative 的反事实。

## 2026-06-24 V25/V26：branch alternative replay 通路

新增离线 runbook：

```text
script  = BPC_future/scripts/build_journey_branch_impact_alt_runbook.py
test    = BPC_future/tests/test_journey_branch_impact_alt_runbook.py
runbook = BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624
report  = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_alt_runbook_v25_from_v24_zh.md
```

它从 V24 完整 branch-impact rows 的 `priority_top` 中生成 12 条同节点 alternative forced-pair replay 命令；depth>0 时保留祖先 branch path，例如：

```text
force_pair_path:0:2,5=same_vehicle;1:8,18
```

这些命令只改变 branch candidate 优先级；exact pricing closure、node bound 和 fathom 仍由原求解流程给出。

已实际执行 V25 entry 08：把 `random-wave/tranquillitatis...seed61820` 的 root branch 从 V24 原始 `[1,2]` 强制改成 `[1,4]`。

```text
result = OPTIMAL
wall = 53.77s
audit = BPC_future/results/journey_branch_impact_audit_v25_alt08_randomtw20_20260624
forced_pair_branch_count = 1
forced_pair_matched_branch_count = 1
candidate_log_branch_count = 2
complete_label_branch_count = 2
usable_branch_impact_training_count = 2
```

与 V24 原始同实例相比，root 局部 child negative pricing events 从 `10` 降到 `5`，但总 wall 从约 `42.29s` 增到约 `53.77s`，branch_count 从 `1` 增到 `2`。这说明 branch 排序不能只优化局部 child 负列事件或 pool width；必须看全子树 proof cost / wall-time / completion-bound retry。

V26 合成 V24+V25 的 branch tail-impact rows：

```text
output = BPC_future/results/journey_tail_impact_training_rows_v26_branch_counterfactual_v24_v25_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_impact_training_rows_v26_branch_counterfactual_zh.md
training_row_count = 8
branch_row_count = 8
tail_class_counts = {'completion_bound_tail': 8}
y_useful_tail_reduction = 0
y_tail_risk = 8
hard_negative_catalog_ready = true
contrastive_tail_training_ready = false
```

当前判断：已经有完整 hard negatives 和一条可复用反事实 replay 通路，但还没有真正减少 proof tail / wall-time 的正例。因此下一步不是训练 branch-impact GAT 排序器，而是继续执行 V25 fast/medium alternatives，找到 `y_useful_tail_reduction>0` 或显著降低全子树 proof cost 的对照样本。

## 2026-06-24 V27：branch counterfactual delta 标签

V26 暴露出一个标签问题：单条 branch-impact row 的 absolute tail class 不能表达“这个 alternative 相对原始 branch 是否更快”。因此新增离线 delta audit：

```text
script = BPC_future/scripts/audit_journey_branch_counterfactual_delta.py
test   = BPC_future/tests/test_journey_branch_counterfactual_delta_audit.py
output = BPC_future/results/journey_branch_counterfactual_delta_v27_v24_v25_alt07_alt08_alt09_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v27_alt07_alt08_alt09_zh.md
```

它按 `instance/node/depth/baseline_pair/forced_pair` 对齐 V24 baseline 与 V25 replay，输出 run-level 和 branch-level delta：

```text
wall_time_delta
solving_time_delta
pricing_calls_delta
exact_pricing_calls_delta
node_count_delta
child_negative_pricing_events_delta
child_completion_bound_retries_delta
```

并生成相对标签：

```text
y_counterfactual_wall_improved
y_counterfactual_proof_cost_improved
y_counterfactual_regression
```

已纳入 V25 entry 07、08、09：

```text
matched_counterfactual_count = 3
forced_pair_matched_count = 3
status_pair_counts = {'OPTIMAL->OPTIMAL': 3}
label_positive_counts = {
  'y_counterfactual_regression': 2,
  'y_counterfactual_wall_improved': 1
}
counterfactual_training_ready = true
```

具体 delta：

```text
entry 07: [1,2] -> [1,18], wall_time_delta = -4.178415s, y_counterfactual_wall_improved = 1
entry 08: [1,2] -> [1,4],  wall_time_delta = +11.479765s, y_counterfactual_regression = 1
entry 09: [5,6] -> [6,7],  wall_time_delta = +65.673870s, y_counterfactual_regression = 1
```

解释：

- entry 07 的 child negative pricing events 没有减少，反而 `+1`，但全局 wall-time 更短；
- entry 08/09 的 child negative pricing events 减少了，但 exact pricing calls、node_count 或 wall-time 增加，整体更慢；
- 因此 branch-impact 不能用“局部负列少”或 pool width 作为主标签，必须用同节点 counterfactual wall/proof-cost delta。

V28 继续执行 V25 entry 10 和 entry 01，delta 样本扩到 5 条：

```text
output = BPC_future/results/journey_branch_counterfactual_delta_v28_v24_v25_alt01_alt07_to_alt10_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v28_alt01_alt07_to_alt10_zh.md
matched_counterfactual_count = 5
forced_pair_matched_count = 5
status_pair_counts = {'OPTIMAL->OPTIMAL': 5}
label_positive_counts = {
  'y_counterfactual_proof_cost_improved': 1,
  'y_counterfactual_regression': 3,
  'y_counterfactual_wall_improved': 2
}
```

新增 delta：

```text
entry 10: [5,6] -> [7,11], wall_time_delta = +78.788880s, y_counterfactual_regression = 1
entry 01: [2,5] -> [3,18], wall_time_delta = -89.781081s, exact_pricing_calls_delta = -18, node_count_delta = -4, y_counterfactual_wall_improved = 1, y_counterfactual_proof_cost_improved = 1
```

entry 01 是当前最强正例：absolute tail class 仍是 `completion_bound_tail`，但相对原始 branch 少了 18 次 exact pricing call、少了 4 个 node，wall-time 快约 89.8s。V28 仍不是上线条件，样本只有 5 条、覆盖 3 个实例；但它已经从“只有 hard negatives”推进到 2 正 / 3 负的最小 branch-ranking 信号。

V29 继续补 V25 entry 02，delta 样本扩到 6 条：

```text
output = BPC_future/results/journey_branch_counterfactual_delta_v29_v24_v25_alt01_alt02_alt07_to_alt10_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v29_alt01_alt02_alt07_to_alt10_zh.md
matched_counterfactual_count = 6
forced_pair_matched_count = 6
status_pair_counts = {'OPTIMAL->OPTIMAL': 6}
label_positive_counts = {
  'y_counterfactual_proof_cost_improved': 1,
  'y_counterfactual_regression': 4,
  'y_counterfactual_wall_improved': 2
}
counterfactual_training_ready = true
```

新增 delta：

```text
entry 02: [2,5] -> [5,8], wall_time_delta = +140.922309s, exact_pricing_calls_delta = +35, node_count_delta = +8, pricing_calls_delta = +49, child_negative_pricing_events_delta = -3, y_counterfactual_regression = 1
```

V29 的重点不是样本量，而是同一个 greedy root baseline `[2,5]` 下已经有一个强正和一个强负：

```text
[2,5] -> [3,18]: wall -89.781081s, exact pricing -18, node -4, 正例
[2,5] -> [5,8] : wall +140.922309s, exact pricing +35, node +8, 负例
```

entry 02 的局部 child negative pricing events 少了 3，但全局 exact pricing、node 和 wall-time 都大幅变差。这再次确认 branch-impact GAT 不能用 child negative count、pool width 或 absolute tail class 当排序标签；必须使用同 parent context 的 counterfactual proof-cost / wall delta。

V32 跑完 V25 runbook 全部 12 条 alternative，并生成完整 counterfactual delta：

```text
output = BPC_future/results/journey_branch_counterfactual_delta_v32_v24_v25_all12_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v32_all12_zh.md
matched_counterfactual_count = 12
forced_pair_matched_count = 12
status_pair_counts = {'OPTIMAL->OPTIMAL': 12}
label_positive_counts = {
  'y_counterfactual_proof_cost_improved': 1,
  'y_counterfactual_regression': 9,
  'y_counterfactual_wall_improved': 2
}
counterfactual_training_ready = true
```

新增 depth-1 alternatives 的主要结果：

```text
entry 03: [2,17] -> [8,18], wall_time_delta = +77.206493s, exact_pricing_calls_delta = +21, node_count_delta = +4, child_negative_pricing_events_delta = -4, regression
entry 04: [2,17] -> [8,17], wall_time_delta = +111.093631s, exact_pricing_calls_delta = +28, node_count_delta = +4, child_negative_pricing_events_delta = +2, regression
entry 05: [3,17] -> [3,18], wall_time_delta = +1.015413s, exact_pricing_calls_delta = +2, pricing_calls_delta = +4, regression
entry 06: [3,17] -> [13,18], wall_time_delta = +41.544674s, exact_pricing_calls_delta = +14, node_count_delta = +4, child_negative_pricing_events_delta = -2, regression
entry 11: [5,7] -> [7,10], wall_time_delta = +1.666250s, regression
entry 12: [5,7] -> [6,7], wall_time_delta = -0.255814s, below 1s improvement threshold
```

V32 的价值是把 V25 反事实闭环做完整，而不是证明可以上线：12 条里只有 entry 01 是强正例，entry 07 是弱 wall 正例，其余大多是 regression 或近似持平。当前 `priority_top` 候选源偏向产生 hard negatives；下一步 branch-impact/GAT 线需要扩大 canonical random-TW 20 的同 parent 采样，并引入更强候选生成方式寻找强正例。

V33 在 V32 delta 之上新增离线 ranking 审计：

```text
script = BPC_future/scripts/audit_journey_branch_counterfactual_ranking.py
test   = BPC_future/tests/test_journey_branch_counterfactual_ranking_audit.py
output = BPC_future/results/journey_branch_counterfactual_ranking_v33_v32_all12_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_ranking_v33_v32_all12_zh.md
counterfactual_row_count = 12
context_count = 6
ranking_pair_count = 6
label_counts = {'proof_cost_improved': 1, 'regression': 9, 'wall_improved': 2}
context_counts = {'mixed_positive_negative_context': 2, 'regression_only_context': 4}
proxy_contradiction_counts = {'fewer_child_negative_but_regressed': 6, 'more_child_negative_but_wall_improved': 1}
ranking_training_ready = true
```

关键排序对：

```text
baseline [2,5]:  [3,18] 优于 [5,8]，wall gap = 230.703390s，exact pricing gap = 53
baseline [1,2]:  [1,18] 优于 [1,4]，wall gap = 15.658180s，exact pricing gap = 6
baseline [3,17]: [3,18] 优于 [13,18]，wall gap = 40.529261s，exact pricing gap = 12
```

这一步把 branch-impact GAT 的数据接口从单条 absolute label 推到同 parent pairwise ranking rows。它仍然只是训练/评估数据，不影响 official bound，也不运行 pricing；由于 mixed positive/negative context 只有 2 个，下一步需要继续扩大 canonical random-TW 20 的 counterfactual 采样，优先补强正例和 mixed context。

V34 在 solver 侧新增默认关闭的 branch-score opt-in：

```text
journey_branch_candidate_priority=branch_score
或
journey_branch_candidate_priority=branch_score_horizon
journey_branch_candidate_score_map={...}
或
journey_branch_candidate_score_path=...
```

它允许外部 branch-impact/GAT ranking 输出以 score map 形式影响 Ryan-Foster pair 的候选排序。`branch_score` 的排序范围仍受 `journey_branch_fractionality_tie_tolerance` 控制；`branch_score_horizon` 会在显式 opt-in 时对正分 scored candidate 自动打开最小 candidate horizon，默认上限为 `journey_branch_candidate_score_horizon_tie_tolerance=0.2`。负分 scored candidate 不触发扩展，也不参与 horizon 优先排序，只按原 deterministic fractionality fallback 处理。支持的 key 包括全局 pair、depth-specific pair、node+depth-specific pair，例如 `1,2`、`depth:0:1,2`、`node:9:depth:0:1,2`；日志会在 `journey_branch_candidates.selected/priority_top` 中记录 `branch_score` 和 `branch_score_source`，并记录 `effective_tie_tolerance` / `effective_eligible_count`。

这个入口只改变 opt-in 的分支 pair 调度，不改变 RMP、pricing、official bound、fathom 或 certificate。缺少 score 时会回退到 deterministic fractionality 顺序；因此它是把 V33/GAT ranking 接入实际 solver 的安全调度口，不是证明口。当前只验证了接口和日志行为，尚未证明 20-scale wall-time 改善。

V35 新增离线转换脚本，把 V33 ranking rows 变成 solver 可读的 branch-score map：

```text
script = BPC_future/scripts/build_journey_branch_score_map.py
test   = BPC_future/tests/test_journey_branch_score_map.py
input  = BPC_future/results/journey_branch_counterfactual_ranking_v33_v32_all12_20260624
output = BPC_future/results/journey_branch_score_map_v35_v33_all12_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_map_v35_v33_all12_zh.md
ranking_pair_row_count = 6
branch_score_row_count = 12
branch_score_map_entry_count = 12
instance_count = 3
key_scope = node_depth
production_ready = false
official_bound_effect = false
```

使用方式：

```text
journey_branch_candidate_priority=branch_score
journey_branch_candidate_score_path=BPC_future/results/journey_branch_score_map_v35_v33_all12_20260624/journey_branch_score_rows.json
```

V35 的输出示例：

```text
node:0:depth:0:3,18 = +10.0
node:0:depth:0:5,8  = -10.0
node:2:depth:1:3,18 = +2.875487683
node:2:depth:1:13,18 = -2.875487683
```

这一步仍然是 diagnostic-only：它只把离线反事实排序数据接到 solver 的 opt-in 调度入口，不运行 BPC / pricing / RMP，不改变 official bound，也没有证明 20-scale wall-time 改善。下一步才是用该 score map 做受控 A/B，并继续扩充 canonical random-TW 20 的 mixed positive/negative context。

V36 用 V33/V35 中最强正例实例做了第一个 branch-score opt-in 真实求解 A/B：

```text
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_v36_branch_score_optin_ab_seed61846_zh.md
```

结果：

| 指标 | baseline | branch_score | delta |
|---|---:|---:|---:|
| status | `OPTIMAL` | `OPTIMAL` | - |
| wall_time | `175.215707s` | `67.302853s` | `-107.912854s` |
| solving_time | `144.360625s` | `65.120653s` | `-79.239972s` |
| node_count | `7` | `3` | `-4` |
| branch_nodes | `3` | `1` | `-2` |
| rmp_solves | `35` | `24` | `-11` |
| pricing_calls | `72` | `43` | `-29` |
| exact_pricing_calls | `37` | `19` | `-18` |

root branch 审计：

```text
baseline:     priority_mode=fractionality, selected=[2,5]
branch_score: priority_mode=branch_score, selected=[3,18], branch_score=10.0, source=node:0:depth:0:3,18
```

V36 说明 V33 ranking rows -> V35 score map -> V34 solver opt-in 的链路已经在真实 run 中打通，并在该 in-sample 实例上复现了强正例收益。边界仍然严格：这是单个 in-sample A/B，不是 random-TW 20 全量结论，也不是 production GAT 泛化证据；`branch_score` 仍只改变 branch pair 调度，不改变 official bound / certificate。

V37 把 V36 的人工日志解析固化成 A/B 审计脚本：

```text
script = BPC_future/scripts/audit_journey_branch_score_ab.py
test   = BPC_future/tests/test_journey_branch_score_ab_audit.py
output = BPC_future/results/journey_branch_score_ab_audit_v37_v36_seed61846_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_ab_audit_v37_seed61846_zh.md
paired_instance_count = 1
selected_pair_changed_count = 1
branch_score_used_count = 1
wall_time_delta_sum = -107.912854
exact_pricing_calls_delta_sum = -18.0
node_count_delta_sum = -4.0
production_ready = false
official_bound_effect = false
```

该脚本只读已完成 CSV / JSONL，不运行 BPC / pricing / RMP；后续多实例 branch-score A/B 都应统一用它汇总 selected pair、score source 和 proof-cost delta。

V38/V40 做了第一个 leave-instance-out 负检验。目标仍是 seed61846，但 score map 排除了 seed61846 自身 ranking rows，并使用 pair-scope：

```text
score_map = BPC_future/results/journey_branch_score_map_v38_leave_seed61846_pair_20260624
score_map_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_map_v38_leave_seed61846_pair_zh.md
optin_csv = BPC_future/results/20260624_v39_branch_score_leave_seed61846_pair_optin_220_seed61846.csv
ab_audit = BPC_future/results/journey_branch_score_ab_audit_v40_v39_leave_seed61846_pair_20260624
ab_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_ab_audit_v40_leave_seed61846_pair_zh.md
raw_ranking_pair_row_count = 6
filtered_out_row_count = 3
ranking_pair_row_count = 3
branch_score_map_entry_count = 5
selected_pair_changed_count = 0
branch_score_used_count = 0
exact_pricing_calls_delta_sum = 0.0
node_count_delta_sum = 0.0
```

排除 seed61846 后剩余 score pairs 是 `[1,18]`、`[1,4]`、`[6,7]`、`[7,10]`、`[7,11]`，没有命中 seed61846 root 的 29 个 eligible branch candidates。于是 opt-in 虽然启用了 `priority_mode=branch_score`，但 selected 仍是 `[2,5]`，`branch_score_source=None`。V40 的结论是：当前 V33 数据太稀疏，pair-scope lookup 不能 out-of-sample 泛化；后续必须继续扩充跨实例 mixed positive/negative context，或者训练真正基于节点/实例特征泛化的 branch-impact ranking head。

V41/V42 增加了 branch-score candidate coverage 审计，用来区分“score map 能命中候选但效果不好”和“score map 根本没有命中候选”：

```text
script = BPC_future/scripts/audit_journey_branch_score_candidate_coverage.py
test   = BPC_future/tests/test_journey_branch_score_candidate_coverage.py
diagnostic_only = true
runs_bpc_or_pricing = false
official_bound_effect = false
```

V41 用 V35 in-sample score map 审计 V36 baseline 的 `journey_branch_candidates` 日志：

```text
coverage_output = BPC_future/results/journey_branch_score_candidate_coverage_v41_v35_on_v36_baseline_20260624
coverage_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_candidate_coverage_v41_v35_on_v36_baseline_zh.md
candidate_event_count = 3
candidate_event_with_score_hit_count = 3
candidate_event_with_selected_score_count = 0
candidate_event_would_change_selected_count = 3
full_logged_candidate_coverage_count = 0
score_entry_count = 12
scored_candidate_count_sum = 6
selected_unscored_count = 3
unscored_logged_candidate_count_sum = 30
```

三条 branch event 都命中了 scored candidate，并且 best scored pair 都会改变默认 selected pair：root 从 `[2,5]` 指向 `[3,18]`，两个 depth-1 节点也各有 scored alternative。这解释了 V36 为什么能在同一个 in-sample 实例上产生真实 branch action 和 proof-cost 降低。`full_logged_candidate_coverage_count=0` 的含义是 V36 baseline 只记录了 top 12，而 event 自身 candidate_count 为 29/17/17；它不是完整候选宇宙覆盖结论。

V42 用 V38 leave-seed61846-out pair-scope score map 审计同一批 V36 baseline 候选日志：

```text
coverage_output = BPC_future/results/journey_branch_score_candidate_coverage_v42_v38_on_v36_baseline_20260624
coverage_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_candidate_coverage_v42_v38_on_v36_baseline_zh.md
candidate_event_count = 3
candidate_event_with_score_hit_count = 0
candidate_event_with_selected_score_count = 0
candidate_event_would_change_selected_count = 0
full_logged_candidate_coverage_count = 0
score_entry_count = 5
scored_candidate_count_sum = 0
selected_unscored_count = 3
unscored_logged_candidate_count_sum = 36
```

这证明 V40 没动作的直接原因是 score map 对已记录候选 0 命中，不是 solver opt-in 接口失效。下一批 random-TW 20 采样必须把 `journey_branch_candidate_log_top_n` 提高到足以覆盖完整候选列表，例如 100，并围绕默认 selected pair、附近高 fractionality 候选和已知强正例补 counterfactual replay。当前 V33/V38 的 pair overlap 太少，pair lookup 只能作为诊断桥接，不能作为 production 泛化策略。

V43 新增了从 candidate log 直接生成 forced-pair replay runbook 的工具：

```text
script = BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py
test   = BPC_future/tests/test_journey_branch_candidate_replay_runbook.py
input  = BPC_future/results/logs_20260624_v36_branch_score_ab_baseline_220_seed61846
output = BPC_future/results/journey_branch_candidate_replay_runbook_v43_v36_seed61846_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_candidate_replay_runbook_v43_seed61846_zh.md
candidate_event_count_seen = 3
entry_count = 12
alt_pairs_per_event = 4
candidate_log_top_n = 100
diagnostic_only = true
official_bound_effect = false
```

它直接读取 `journey_branch_candidates` 日志，从 `priority_top` / `top` 中挑 alternative pair，生成同 node path 的 `force_pair_path` 命令。V43 在 seed61846 的 3 个 branch candidate event 上生成 12 条 replay 命令，其中 depth-1 条目保留祖先约束方向，例如：

```text
force_pair_path:0:2,5=same_vehicle;1:8,18
force_pair_path:0:2,5=separate_vehicle;1:3,18
```

这一步解决的是采样闭环的一个实际缺口：后续 canonical random-TW 20 的 60-instance 日志只要打开 `journey_branch_candidate_log_top_n=100`，就可以直接生成 path-bound forced-pair replay 清单，而不必先人工从日志里挑候选。它仍然不运行 BPC，不改变 RMP/pricing/official bound，也不是性能收益结论；真正的标签要等这些 replay 跑完，再用 branch-impact / counterfactual-delta 审计生成。

V44 跑了第一批 canonical random-TW 20 balanced6 的 top100 候选日志采样：

```text
instances = 6
time_limit = 220
max_workers = 3
journey_branch_candidate_log_top_n = 100
csv = BPC_future/results/20260624_v44_candidate_log_top100_randomtw20_balanced6_220.csv
log_dir = BPC_future/results/logs_20260624_v44_candidate_log_top100_randomtw20_balanced6_220
status_count = {'EXTERNAL_TIME_LIMIT': 5, 'OPTIMAL': 1}
wall_time_sum = 1124.466s
candidate_event_files = 5
candidate_event_count = 29
candidate_count_sum = 816
priority_top_count_minmax = 12..60
```

这不是性能改善：6 个实例里 5 个在 220s 外部时限触发，只有 `sector-wave/tranquillitatis_balmer_like_20km/...seed61002` 在 `24.337408s` 达到 `OPTIMAL`。因此当前 20-scale 200s 全量目标仍未达成。

但它验证了采样路径：`top_n=100` 候选日志生效，5 个实例产生了 29 个 branch-candidate event，候选总数 816，`priority_top` 不再固定在 12；某些 event 最大只有 60 是因为自身候选数不足 100。

随后用 V43 工具从 V44 日志生成了 V44 replay runbook：

```text
output = BPC_future/results/journey_branch_candidate_replay_runbook_v44_top100_balanced6_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_candidate_replay_runbook_v44_top100_balanced6_zh.md
candidate_event_count_seen = 29
candidate_event_count_with_replay_entries = 15
entry_count = 60
entry_limit_reached = true
source_depth_counts = {0: 16, 1: 24, 2: 12, 3: 8}
```

`entry_limit_reached=true` 表示这批 balanced6 日志已经足够继续扩展 replay；当前只截取 60 条 path-bound forced-pair 命令，没有穷尽 29 个 candidate event。下一步应先跑 V44 runbook 的代表性子集，生成 branch-impact / counterfactual-delta rows，再判断是否找到了新的 mixed positive/negative context。

V45 对 V44 baseline 日志做了 branch-impact audit：

```text
input = BPC_future/results/logs_20260624_v44_candidate_log_top100_randomtw20_balanced6_220
output = BPC_future/results/journey_branch_impact_audit_v45_v44_top100_balanced6_baseline_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v45_v44_top100_balanced6_baseline_zh.md
branch_count = 29
candidate_log_branch_count = 29
right_censored_branch_count = 29
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
tail_class_counts = {'completion_bound_tail': 19, 'negative_chain_continues': 1, 'unprocessed_children': 9}
total_child_negative_pricing_events = 132
total_child_completion_bound_retries = 89
```

这确认了 V44 的问题：候选覆盖够宽，但 220s 下所有 branch row 都是右删失。它们可以导航下一批采样，不能直接训练 branch-impact GAT。

V46 从 V44 runbook 中取第一个 root context 的 4 个 alternative，用同样 220s 预算 replay：

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_candidate_replay_runbook_v46_root4_220_zh.md
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
baseline_pair = [3,7]
forced_pairs = [3,10], [10,13], [9,10], [4,5]
```

4 个 replay 都触发外部时限：

```text
status_pairs = EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT for all 4
forced_pair_matched_count = 4
```

V47 对 V46 forced replay 日志做 branch-impact audit：

```text
output = BPC_future/results/journey_branch_impact_audit_v47_v46_root4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v47_v46_root4_220_zh.md
branch_count = 7
forced_pair_branch_count = 4
forced_pair_matched_branch_count = 4
right_censored_branch_count = 7
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
tail_class_counts = {'completion_bound_tail': 5, 'negative_chain_continues': 1, 'unprocessed_children': 1}
```

V48 修正了 counterfactual-delta 的右删失标签契约，并重算 V46 root4 delta：

```text
script = BPC_future/scripts/audit_journey_branch_counterfactual_delta.py
test = BPC_future/tests/test_journey_branch_counterfactual_delta_audit.py
schema_version = journey_branch_counterfactual_delta_audit_v2
output = BPC_future/results/journey_branch_counterfactual_delta_v48_v46_root4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v48_root4_220_zh.md
matched_counterfactual_count = 4
forced_pair_matched_count = 4
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 4}
right_censored_counterfactual_count = 4
usable_counterfactual_training_count = 0
label_positive_counts = {'y_counterfactual_proof_cost_proxy_improved': 1, 'y_counterfactual_right_censored': 4}
counterfactual_training_ready = false
```

关键修正：`EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT` 中局部 child retry / negative event 下降只记 `y_counterfactual_proof_cost_proxy_improved`，不再记正式 `y_counterfactual_proof_cost_improved`。这避免 GAT 把右删失 proxy 当成强正例。

V49 ranking audit 也验证这批不能进入 ranking 训练：

```text
output = BPC_future/results/journey_branch_counterfactual_ranking_v49_v48_root4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_ranking_v49_root4_220_zh.md
counterfactual_row_count = 4
context_count = 1
ranking_pair_count = 0
ranking_training_ready = false
context_counts = {'neutral_only_context': 1}
```

结论：只按 root pool-width 排前的 alternative 没有把 timeout 实例救回 220s 内，也没有产生可训练正例。下一批 replay 应避开同一 root context 的继续盲试，改挑 V45 中 active-touch / completion-bound-retry 高的不同实例或 depth context，并继续保持同预算对照。

V50 已把 V45 branch-impact audit 作为优先级输入接进 `build_journey_branch_candidate_replay_runbook.py`，不再按日志顺序从第一个 root context 盲取 replay。

```text
script = BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py
test = BPC_future/tests/test_journey_branch_candidate_replay_runbook.py
input = BPC_future/results/logs_20260624_v44_candidate_log_top100_randomtw20_balanced6_220
branch_impact_input = BPC_future/results/journey_branch_impact_audit_v45_v44_top100_balanced6_baseline_20260624
output = BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_zh.md
branch_impact_priority_context_count = 29
candidate_event_count_seen = 29
candidate_event_count_with_replay_entries = 3
entry_count = 12
entry_limit_reached = true
```

优先级公式当前为：

```text
10 * y_active_touch
+ 2 * y_child_completion_bound_retries
+ y_child_negative_pricing_events
+ 5 * (tail_class == unprocessed_children)
+ 2 * (tail_class == completion_bound_tail)
+ right_censored
```

V50 产出的 12 条 replay 来自 3 个高风险 context：

- sector-wave/apollo15，node 2 depth 1，默认 `[5,8]`，priority `46.0`，替代 `[8,12]`、`[8,14]`、`[14,18]`、`[8,18]`；
- greedy-anchor/tranquillitatis，node 0 depth 0，默认 `[2,18]`，priority `45.0`，替代 `[7,15]`、`[2,15]`、`[6,8]`、`[7,11]`；
- random-wave/apollo15，node 0 depth 0，默认 `[8,18]`，priority `42.0`，替代 `[3,17]`、`[10,17]`、`[10,20]`、`[2,13]`。

边界：V50 只是 prioritized runbook，不是 BPC replay 结果；没有产生 certificate、official bound 或 wall-time 改善结论。下一步应先跑前 4 条 sector-wave depth-1 replay，再用 V45/V47/V48/V49 同一审计链条判断是否得到可训练的同节点正/负排序样本。

V51-V53 已跑完 V50 前 4 条 sector-wave depth-1 replay：

```text
runs = 001..004
context = sector-wave/apollo15 node 2 depth 1
baseline_pair = [5,8]
forced_pairs = [8,12], [8,14], [14,18], [8,18]
status_pairs = EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT for all 4
```

V51 branch-impact audit：

```text
output = BPC_future/results/journey_branch_impact_audit_v51_v50_first4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v51_v50_first4_220_zh.md
branch_count = 28
forced_pair_branch_count = 4
forced_pair_matched_branch_count = 4
right_censored_branch_count = 28
usable_branch_impact_training_count = 0
tail_class_counts = {'completion_bound_tail': 15, 'negative_chain_continues': 1, 'unprocessed_children': 12}
total_child_negative_pricing_events = 150
total_child_completion_bound_retries = 51
```

V52 counterfactual delta：

```text
output = BPC_future/results/journey_branch_counterfactual_delta_v52_v50_first4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v52_v50_first4_220_zh.md
matched_counterfactual_count = 4
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 4}
right_censored_counterfactual_count = 4
usable_counterfactual_training_count = 0
label_positive_counts = {'y_counterfactual_proof_cost_proxy_improved': 4, 'y_counterfactual_right_censored': 4}
```

局部 proxy delta：

```text
[8,12]:  child_completion_bound_retries_delta=-4, child_negative_pricing_events_delta=-4
[8,14]:  child_completion_bound_retries_delta=-4, child_negative_pricing_events_delta=-10
[14,18]: child_completion_bound_retries_delta=-4, child_negative_pricing_events_delta=-9
[8,18]:  child_completion_bound_retries_delta=-4, child_negative_pricing_events_delta=-9
```

V53 ranking audit：

```text
output = BPC_future/results/journey_branch_counterfactual_ranking_v53_v52_v50_first4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_ranking_v53_v50_first4_220_zh.md
context_count = 1
ranking_pair_count = 0
ranking_training_ready = false
context_counts = {'neutral_only_context': 1}
```

结论：V50 priority 确实挑到了一个比 root4 更有局部 proof-cost 变化的 context，但 220s 下仍全部右删失。V52 的 proxy 改善不能转成正式 branch-ranking 正例；这批只能作为采样导航。后续要么对 `[8,14]` / `[14,18]` 这类 proxy 最强 pair 做 600s 诊断，看能否变成完整 delta；要么转向 V50 的第二、第三个高风险 context，继续寻找 `timeout_resolved`、`both_optimal` 或 complete proof-cost positive。

V54-V57 对 V52 中 proxy 最强的 `[8,14]`、`[14,18]` 做了 600s 公平诊断，并补跑同 budget baseline `[5,8]`。

三条 600s 结果：

```text
baseline [5,8]:  EXTERNAL_TIME_LIMIT, wall=600.016911s
alt [8,14]:      EXTERNAL_TIME_LIMIT, wall=600.026557s
alt [14,18]:     EXTERNAL_TIME_LIMIT, wall=600.021964s
```

V55 branch-impact audit：

```text
output = BPC_future/results/journey_branch_impact_audit_v55_v54_proxy_top2_600_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v55_v54_proxy_top2_600_zh.md
branch_count = 78
forced_pair_branch_count = 3
forced_pair_matched_branch_count = 3
right_censored_branch_count = 78
usable_branch_impact_training_count = 0
tail_class_counts = {'completion_bound_tail': 41, 'negative_chain_continues': 1, 'unprocessed_children': 36}
total_child_negative_pricing_events = 300
total_child_completion_bound_retries = 158
```

V56 fair 600s delta：

```text
output = BPC_future/results/journey_branch_counterfactual_delta_v56_v54_proxy_top2_600_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v56_v54_proxy_top2_600_zh.md
matched_counterfactual_count = 2
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 2}
right_censored_counterfactual_count = 2
usable_counterfactual_training_count = 0
label_positive_counts = {'y_counterfactual_proof_cost_proxy_improved': 2, 'y_counterfactual_right_censored': 2}
```

同 budget 下 proxy 仍存在，但没有转成正式信号：

```text
[8,14]:  child_completion_bound_retries_delta=-4, child_negative_pricing_events_delta=-10
[14,18]: child_completion_bound_retries_delta=-4, child_negative_pricing_events_delta=-9
```

V57 ranking audit：

```text
output = BPC_future/results/journey_branch_counterfactual_ranking_v57_v56_proxy_top2_600_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_ranking_v57_proxy_top2_600_zh.md
context_count = 1
ranking_pair_count = 0
ranking_training_ready = false
context_counts = {'neutral_only_context': 1}
```

结论：这个 context 的 branch pair 可以减少局部 completion-bound retry / negative-pricing 事件，但即使放宽到 600s 也不能形成 timeout resolved、both-optimal delta 或正式 ranking positive。继续在同一 context 上加预算硬试的边际价值低；下一步应转向 V50 的第二/第三高风险 context，或推进 incumbent/cuts/formulation/strong-branch-gain 这类能改变可剪枝区间的算法线。

V58-V60 已转向 V50 第二个 high-risk context：canonical random-TW 20 `greedy-anchor/tranquillitatis_balmer_like_20km/...seed61001` 的 root node，baseline pair `[2,18]`，替代 `[7,15]`、`[2,15]`、`[6,8]`、`[7,11]`。

四条 220s replay：

```text
[7,15]: EXTERNAL_TIME_LIMIT, wall=220.028613s
[2,15]: OPTIMAL, wall=206.685515s
[6,8]:  OPTIMAL, wall=171.802948s
[7,11]: OPTIMAL, wall=171.793737s
```

V58 branch-impact audit：

```text
output = BPC_future/results/journey_branch_impact_audit_v58_v50_second4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v58_v50_second4_220_zh.md
branch_count = 17
forced_pair_branch_count = 4
forced_pair_matched_branch_count = 4
complete_label_branch_count = 10
right_censored_branch_count = 7
usable_branch_impact_training_count = 10
tail_class_counts = {'completion_bound_tail': 14, 'unprocessed_children': 3}
total_child_negative_pricing_events = 91
total_child_completion_bound_retries = 83
```

V59 counterfactual delta：

```text
output = BPC_future/results/journey_branch_counterfactual_delta_v59_v58_second4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v59_v58_second4_220_zh.md
matched_counterfactual_count = 4
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 1, 'EXTERNAL_TIME_LIMIT->OPTIMAL': 3}
timeout_resolved_count = 3
right_censored_counterfactual_count = 1
usable_counterfactual_training_count = 3
label_positive_counts = {'y_counterfactual_proof_cost_proxy_improved': 4, 'y_counterfactual_right_censored': 1, 'y_counterfactual_timeout_resolved': 3}
```

相对 baseline `[2,18]`：

```text
[7,15]: wall_delta=+0.001630, child_cb_retries_delta=-4, child_negative_delta=-1, still censored
[2,15]: wall_delta=-13.341468, child_cb_retries_delta=-8, child_negative_delta=+1, timeout resolved
[6,8]:  wall_delta=-48.224035, child_cb_retries_delta=-8, child_negative_delta=-1, timeout resolved
[7,11]: wall_delta=-48.233246, child_cb_retries_delta=-4, child_negative_delta=0, timeout resolved
```

V60 ranking audit：

```text
output = BPC_future/results/journey_branch_counterfactual_ranking_v60_v59_second4_220_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_ranking_v60_second4_220_zh.md
context_count = 1
ranking_pair_count = 6
ranking_training_ready = true
```

V61-V64 把 V60 ranking rows 接入 solver opt-in：

```text
score_map = BPC_future/results/journey_branch_score_map_v61_v60_second4_20260624
coverage = BPC_future/results/journey_branch_score_candidate_coverage_v62_v61_on_v44_baseline_20260624
optin_csv = BPC_future/results/20260624_v63_branch_score_v61_tie02_optin_220_seed61001.csv
ab_audit = BPC_future/results/journey_branch_score_ab_audit_v64_v63_seed61001_20260624
```

关键结果：

```text
V61 top score = [7,11], score=2.061865917
V62 score hits = 1/29 candidate events
V62 eligible score hits = 1/29 candidate events
V62 would_change_selected = 1
V62 tie_tolerance_override = 0.2
V63 priority_mode = branch_score
V63 tie_tolerance = 0.2
V63 root selected = [7,11]
V63 branch_score_source = node:0:depth:0:7,11
V63 status = OPTIMAL
V63 wall_time = 169.284521
V63 solving_time = 167.230269
V63 nodes = 7
V63 exact_pricing_calls = 31
V64 baseline_selected = [2,18]
V64 optin_selected = [7,11]
V64 wall_time_delta = -50.742462
```

解释：V61 的 scored pairs 在该 root context 中属于 fractionality `0.2`，而 V44 baseline 默认最高层是 `0.4` 并选 `[2,18]`。所以 V63 必须设置 `journey_branch_fractionality_tie_tolerance=0.2` 才能让 branch-score 实际生效。这个设置只放宽 branch candidate horizon，并改变 Ryan-Foster pair 排序；它不改变 official bound / certificate，所有 child 仍靠 exact pricing closure。

V65-V67 已跑完 V50 第三个 high-risk context，即 canonical random-TW 20 `random-wave/apollo15 seed61000` root context：

```text
forced pairs = [3,17], [10,17], [10,20], [2,13]
branch_impact = BPC_future/results/journey_branch_impact_audit_v65_v50_third4_220_20260624
delta = BPC_future/results/journey_branch_counterfactual_delta_v66_v65_third4_220_20260624
ranking = BPC_future/results/journey_branch_counterfactual_ranking_v67_v66_third4_220_20260624
```

机器结果：

```text
V65 branch_count = 24
V65 forced_pair_branch_count = 4
V65 forced_pair_matched_branch_count = 4
V65 right_censored_branch_count = 24
V65 complete_label_branch_count = 0
V65 usable_branch_impact_training_count = 0
V66 matched_counterfactual_count = 4
V66 status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 4}
V66 timeout_resolved_count = 0
V66 usable_counterfactual_training_count = 0
V67 ranking_pair_count = 0
V67 ranking_training_ready = false
```

相对 baseline `[8,18]`：

```text
[3,17]:  wall_delta=-0.022767, child_cb_retries_delta=-4, child_negative_delta=+4, right_censored
[10,17]: wall_delta=-0.020530, child_cb_retries_delta=-4, child_negative_delta=-3, right_censored
[10,20]: wall_delta=-0.017246, child_cb_retries_delta=-4, child_negative_delta=-4, right_censored
[2,13]:  wall_delta=-0.022012, child_cb_retries_delta=-4, child_negative_delta=+3, right_censored
```

解释：这四条 forced root pair 都来自低 fractionality `0.125` 的远端候选。proxy 上 completion-bound retry 少 4 次，但全部仍是 `EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT`，wall delta 只有 0.02s 量级，实质是 timeout 抖动，不能作为正例或 ranking row。

V68-V69 新增 `branch_score_horizon` opt-in，并在同一 `seed61001` context 上验证真实求解路径：

```text
mode = journey_branch_candidate_priority=branch_score_horizon
score_map = BPC_future/results/journey_branch_score_map_v61_v60_second4_20260624/journey_branch_score_rows.json
optin_csv = BPC_future/results/20260624_v68_branch_score_horizon_v61_optin_220_seed61001.csv
ab_audit = BPC_future/results/journey_branch_score_ab_audit_v69_v68_horizon_seed61001_20260624
```

关键结果：

```text
V68 base tie_tolerance = 0.0
V68 root effective_tie_tolerance = 0.2
V68 root eligible_count = 12
V68 root effective_eligible_count = 30
V68 root selected = [7,11]
V68 branch_score_source = node:0:depth:0:7,11
V68 status = OPTIMAL
V68 wall_time = 169.756047
V68 solving_time = 167.701594
V68 nodes = 7
V68 exact_pricing_calls = 31
V69 wall_time_delta = -50.270936
```

解释：`branch_score_horizon` 只在显式 opt-in 时启用；它不会全局固定 `tie_tolerance=0.2`，而是在当前候选中找正分 scored candidate，并把 `effective_tie_tolerance` 最小放宽到覆盖该 candidate。V68 因此在不手工设置全局 0.2 的情况下复现 V63 的 `[7,11]` 路径；后续节点没有 score 命中时，`effective_tie_tolerance` 回到 0。这个入口仍只改变 branch pair 调度，official bound / certificate 仍来自 exact pricing closure。

V70-V71 把同一个 `branch_score_horizon` score map 放回 V44 的 canonical random-TW 20 balanced6 子集：

```text
optin_csv = BPC_future/results/20260624_v70_branch_score_horizon_v61_balanced6_220.csv
ab_audit = BPC_future/results/journey_branch_score_ab_audit_v71_v70_horizon_balanced6_20260624
ab_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_ab_audit_v71_v70_horizon_balanced6_zh.md
paired_instance_count = 6
branch_score_used_count = 1
selected_pair_changed_count = 1
production_ready = false
```

实际结果：

```text
greedy-anchor/apollo15 seed61000:           timeout -> timeout, pair unchanged [3,7]
greedy-anchor/tranquillitatis seed61001:   timeout -> OPTIMAL 168.915588s, pair [2,18] -> [7,11]
random-wave/apollo15 seed61000:            timeout -> timeout, pair unchanged [8,18]
random-wave/tranquillitatis seed61001:     timeout -> timeout, pair unchanged [8,13]
sector-wave/apollo15 seed61000:            timeout -> timeout, pair unchanged [2,3]
sector-wave/tranquillitatis seed61002:     OPTIMAL -> OPTIMAL, no branch event
```

解释：V70 证明 V68 的收益可以在 fixed balanced6 batch 中复现，但覆盖非常窄。真正使用 score 的只有 `greedy-anchor/tranquillitatis seed61001` 这一条；其余超时实例没有 score 命中，`branch_score_horizon` 回退到原 deterministic fractionality 顺序。V71 的 `wall_improved_count=6` 不能解释成泛化加速，其中 4 条是 220s 外部超时边界的毫秒级抖动，sector/tranquillitatis 本来就很快最优。当前结论应是：solver opt-in 链路是安全可用的，branch-impact 标签覆盖不足，不是 20-scale 200s overall gate 达标证据。

V72-V78 继续从 V44 top100 balanced6 / V45 branch-impact priority 里采样，但用新增的 `--exclude-runbook` 跳过 V50 已经跑过的 12 条 forced-pair entry：

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v72_v45_prioritized_excluding_v50_220_20260624
excluded_entry_skip_count = 12
entry_count = 12
candidate_event_count_with_replay_entries = 3
```

先跑 V72 的前 8 条，覆盖两个后续 context：

```text
random-wave/apollo15 seed61000 depth=1 node=2, selected [2,3], 4 alternatives
sector-wave/apollo15 seed61000 root node=0, selected [2,3], 4 alternatives
```

审计结果：

```text
V77 matched_counterfactual_count = 8
V77 status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 8}
V77 timeout_resolved_count = 0
V77 usable_counterfactual_training_count = 0
V78 context_count = 2
V78 ranking_pair_count = 0
V78 ranking_training_ready = false
```

解释：V72 前 8 条都 forced-pair matched，但全部仍是右删失 timeout，最多只有 proxy proof-cost 改善，不能形成 ranking row。这个负结果比 V65-V67 更明确：仅按 V45 的 completion-tail 风险 priority 往后扫，正例密度很低；继续扫同类候选大概率只会累积 hard-negative/right-censored 样本。后续采样应围绕已知 timeout-resolved 的 V58-V60 context 做局部邻域扩展，或者把实例类别、candidate horizon、fractionality band、pool width、child proof-cost proxy 合并为更强的采样策略。

V80-V89 修正了 V72 的采样偏移：`--exclude-runbook` 现在会先跳过已跑 pair，再从同一 candidate event 继续补足后续 alternatives。随后只输入 V58-V60 的已知正例实例日志，围绕同一 root context `[2,18]` 扩邻域：

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v80_v58_positive_context_next4_220_20260624
forced_pairs = [6,7], [2,6], [7,18], [9,15]
```

V82/V83 结果：

```text
V82 matched_counterfactual_count = 4
V82 status_pair_counts = {'EXTERNAL_TIME_LIMIT->OPTIMAL': 3, 'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 1}
V82 timeout_resolved_count = 3
V82 usable_counterfactual_training_count = 3
V83 ranking_pair_count = 6
V83 ranking_training_ready = true
```

具体 delta：

```text
[2,6]:  EXTERNAL_TIME_LIMIT -> OPTIMAL, wall_delta=-124.575827, exact_delta=+20, node_delta=+5
[6,7]:  EXTERNAL_TIME_LIMIT -> OPTIMAL, wall_delta=-78.492286,  exact_delta=+32, node_delta=+7
[7,18]: EXTERNAL_TIME_LIMIT -> OPTIMAL, wall_delta=-21.022308,  exact_delta=+35, node_delta=+7
[9,15]: EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT, wall_delta=-0.009337, right_censored
```

V84 合并 V59 与 V82 后，同一 parent context 扩到 `8` 条 alternatives、`27` 条 ranking pairs；best pair 变成 `[2,6]`，worst 仍是 `[7,15]`，`wall_delta_spread=124.577457`。V85 用 V84 生成新 score map，`[2,6]` 得分最高 `3.692166045`，旧 `[7,11]` 降为 `0.709450217`。V86/V87 用 `branch_score_horizon` + V85 真实求解同一实例：

```text
V86 status = OPTIMAL
V86 wall_time = 95.59s
V87 selected_pair = [2,6]
V87 root effective_tie_tolerance = 0.2
V87 branch_score = 3.692166045
V87 wall_time_delta_sum = -124.43789
```

V88/V89 的离线 coverage 审计说明 V85 仍只命中 balanced6 中 `1/29` 个 branch-candidate event；即使 horizon=0.2，命中事件数也仍是 1。结论是：局部邻域扩展非常有效，但当前仍是 in-context score map，不是 production 泛化模型。

V90-V98 继续围绕 V58/V82 已经证实的 timeout-resolved root context 做聚焦扩展。新增 `--focus-delta-input` 后，runbook 只保留已有 positive delta context，`focus_context_count=1`、`focus_event_skip_count=28`，不再从 balanced6 的 29 个 event 里盲扫。V90 四个后续候选结果：

```text
[6,13]: EXTERNAL_TIME_LIMIT -> OPTIMAL, wall_delta=-75.315375, exact_delta=+32, node_delta=+7
[2,11]: EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT, right_censored
[6,9]:  EXTERNAL_TIME_LIMIT -> TIME_LIMIT, right_censored
[9,11]: EXTERNAL_TIME_LIMIT -> OPTIMAL, wall_delta=-33.071120, exact_delta=+39, node_delta=+9
```

V92 新增 `2/4` timeout-resolved 正例；V94 合并 V59/V82/V92 后，同一 parent context 扩到 `12` 条 alternatives、`63` 条 ranking pairs。V95 score map 仍把 `[2,6]` 排第一，score `3.751747162`，新增 `[6,13]` 为正分强候选。V96 用 `branch_score_horizon + V95` 真实求解同一 seed61001，`OPTIMAL`，wall `95.74s`；V97 A/B 审计确认 root selected pair 从 `[2,18]` 改到 `[2,6]`，`wall_time_delta_sum=-124.287061`。

V99-V103 把 V95 放回 V44 balanced6 做 opt-in A/B，并修正了一个重要边界。V99/V100 暴露 `branch_score_horizon` 仍会让负分候选 `[9,11]` 在 sector-apollo 上压过无分 baseline `[2,3]`；这不符合“只让正分候选打开 horizon”的语义。代码已修正为：`score <= journey_branch_candidate_score_horizon_min_score` 的候选在 horizon 模式下视为 unscored，不触发扩展，也不参与 score 优先排序。V101/V102 复跑后，sector-apollo 回到 baseline `[2,3]`，`branch_score_used_count` 从 `3` 降到 `2`，`selected_pair_changed_count` 从 `3` 降到 `2`，`wall_regressed_count=0`；真正解决 timeout 的仍只有 seed61001。V103 coverage 用 `--min-score 0.0` 重算后，positive-only eligible score hit 为 `2/29`，不是旧 V98 的 `3/29`。

V104 没有跑求解，只补 branch-tail positive runbook 的候选上下文字段：tail-action alternative pair 条目现在记录 `source_selected_fractionality`、`source_alt_fractionality`、`source_alt_fractionality_gap_to_selected`、`source_alt_required_tie_tolerance` 以及 selected/alt 的 pool width 对比。用 V14/V15 同一输入重生 `BPC_future/results/journey_branch_tail_positive_runbook_v104_horizon_fields_20260624`，共 `14` 个条目，其中 `8` 个 tail-action alternative pair，新字段完整；这批 alt pair 的 `source_alt_required_tie_tolerance` 全为 `0.0`，说明当前 seed61000 tail alt-pair 采样仍是同 fractionality 层内替换，不是 V61/V68 那类需要打开 0.2 horizon 的远端正例。这一步的价值是把后续 branch-impact/GAT 训练所需的 candidate horizon 标签落到样本闭环里，不是新的加速证据。

V105 进一步把 `required_tie_tolerance` 接入 branch-score candidate coverage 审计。用 V103 同一输入和正分口径重跑 V95-on-V44：`candidate_event_count=29`、`candidate_event_with_score_hit_count=2`、`candidate_event_with_eligible_score_hit_count=2`、`candidate_event_would_change_selected_count=2`。新增 horizon 分布为：`best_scored_required_tie_tolerance_count=2`，其中 `<=0` 为 `1`，`<=0.2` 为 `2`，`>0.2` 为 `0`，最大值 `0.2`。两条命中分别是 seed61000 root `[6,13]`，required tolerance `0.0`；seed61001 root `[2,6]`，required tolerance `0.2`。这说明 V95 的主要瓶颈不是 horizon 阈值不够，而是 balanced6 里 positive score hit 只有 `2/29` event；继续扩大 horizon 本身不会自动带来覆盖，必须扩 mixed positive/negative context 和泛化特征。

V106 把 V105 的 coverage-gap 行接入 `build_journey_branch_candidate_replay_runbook.py`。新增 `--coverage-input` / `--coverage-gap-only` 后，runbook 可以只保留无 score hit 或无 eligible score hit 的 branch-candidate event，并把 `coverage_gap_priority`、`coverage_gap_priority_reason`、coverage hit 状态和每个替代 pair 的 `source_alt_required_tie_tolerance` 写入条目。用 V44 top100 balanced6 日志、V105 coverage、并排除 V44/V50/V72/V80/V90 已采 forced pairs 后，生成 `BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624`：`entry_count=24`，覆盖 `12` 个无 score-hit event，`coverage_gap_skip_count=2`，`excluded_entry_skip_count=48`。24 条候选的 required tolerance 分布为 `{0.0, 0.2, 0.25, 0.375}`，其中 `<=0.2` 为 `18/24`。这一步仍不运行求解，只是把“覆盖不足”转成下一批可执行 counterfactual replay 命令。

结论：V58-V60/V80-V106 是当前 branch-impact 线上最有价值的新信号。它证明在一个 canonical 20 实例的同一 root context 下，path-forced branch pair 能把 baseline 220s 超时稳定转成约 95s `OPTIMAL`，并形成 `63` 条合并 pairwise ranking rows；V61-V64/V68-V71/V80-V87/V90-V102 进一步证明这些 ranking rows 可以通过 `branch_score_horizon` 接入真实求解，且不改变 exact proof 边界。V65-V67 和 V72-V78 则是负结果：低 fractionality `0.125` 远端 root 候选、random-wave/apollo depth=1 替换、sector-wave/apollo root 后续替换都没有解决 timeout，也没有产出正式排序样本。V99-V103 进一步说明不能让负分/弱分 score map 改变分支；当前 positive-only coverage 只有 `2/29` event。V104/V105/V106 把 candidate horizon/tie-tolerance 标签写入后续 runbook 与 coverage 样本，并把 coverage-gap event 转成新的 replay 命令，但还没有产生新的正例或 20-scale gate 证据。边界也要写清楚：这些仍是 diagnostic-only / context-level 证据，不是 20-scale 200s overall gate 达标；后续 branch-impact/GAT 调度应记录 candidate horizon/tie-tolerance/fractionality band 和实例类别，并优先扩展 mixed positive/negative context，而不是只按 tail 风险或 completion-tail priority 盲目扩大候选 horizon。

## 验证

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/logs_20260624_v44_candidate_log_top100_randomtw20_balanced6_220 --output-dir BPC_future/results/journey_branch_impact_audit_v45_v44_top100_balanced6_baseline_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v45_v44_top100_balanced6_baseline_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py BPC_future/results/logs_20260624_v44_candidate_log_top100_randomtw20_balanced6_220 --output-dir BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_candidate_replay_runbook_v46_root4_220_zh.md --time-limit 220 --limit 4 --alt-pairs-per-event 4 --candidate-source priority_top --candidate-log-top-n 100`
- `bash -lc 'while IFS= read -r cmd; do bash -lc "$cmd" & done < BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/commands.sh; wait'`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runs --output-dir BPC_future/results/journey_branch_impact_audit_v47_v46_root4_220_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v47_v46_root4_220_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_counterfactual_delta.py --runbook BPC_future/results/journey_branch_candidate_replay_runbook_v46_top100_balanced6_root4_220_20260624/runbook.json --baseline-result BPC_future/results/20260624_v44_candidate_log_top100_randomtw20_balanced6_220.csv --baseline-branch-input BPC_future/results/journey_branch_impact_audit_v45_v44_top100_balanced6_baseline_20260624 --alt-branch-input BPC_future/results/journey_branch_impact_audit_v47_v46_root4_220_20260624 --output-dir BPC_future/results/journey_branch_counterfactual_delta_v48_v46_root4_220_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v48_root4_220_zh.md --min-wall-improvement 1.0`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_counterfactual_ranking.py BPC_future/results/journey_branch_counterfactual_delta_v48_v46_root4_220_20260624 --output-dir BPC_future/results/journey_branch_counterfactual_ranking_v49_v48_root4_220_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_ranking_v49_root4_220_zh.md --min-wall-gap 1.0 --min-exact-pricing-gap 1`
- `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/audit_journey_branch_counterfactual_delta.py BPC_future/tests/test_journey_branch_counterfactual_delta_audit.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_branch_counterfactual_delta_audit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 220 --results-csv BPC_future/results/20260624_v44_candidate_log_top100_randomtw20_balanced6_220.csv --log-dir BPC_future/results/logs_20260624_v44_candidate_log_top100_randomtw20_balanced6_220 --solution-dir BPC_future/results/solutions_20260624_v44_candidate_log_top100_randomtw20_balanced6_220 --run-log-dir BPC_future/results/run_logs_20260624_v44_candidate_log_top100_randomtw20_balanced6_220 --timeout-kill-after 30s --max-workers 3 --quiet --set journey_branch_candidate_log_top_n=100`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py BPC_future/results/logs_20260624_v44_candidate_log_top100_randomtw20_balanced6_220 --output-dir BPC_future/results/journey_branch_candidate_replay_runbook_v44_top100_balanced6_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_candidate_replay_runbook_v44_top100_balanced6_zh.md --time-limit 600 --limit 60 --alt-pairs-per-event 4 --candidate-source priority_top --candidate-log-top-n 100`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py BPC_future/results/logs_20260624_v44_candidate_log_top100_randomtw20_balanced6_220 --branch-impact-input BPC_future/results/journey_branch_impact_audit_v45_v44_top100_balanced6_baseline_20260624 --output-dir BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_zh.md --time-limit 220 --limit 12 --alt-pairs-per-event 4 --candidate-source priority_top --candidate-log-top-n 100`
- `bash -lc 'i=0; while IFS= read -r cmd && [ "$i" -lt 4 ]; do i=$((i + 1)); bash -lc "$cmd" & done < BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/commands.sh; wait'`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runs --output-dir BPC_future/results/journey_branch_impact_audit_v51_v50_first4_220_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v51_v50_first4_220_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_counterfactual_delta.py --runbook BPC_future/results/journey_branch_candidate_replay_runbook_v50_v45_prioritized_220_20260624/runbook.json --baseline-result BPC_future/results/20260624_v44_candidate_log_top100_randomtw20_balanced6_220.csv --baseline-branch-input BPC_future/results/journey_branch_impact_audit_v45_v44_top100_balanced6_baseline_20260624 --alt-branch-input BPC_future/results/journey_branch_impact_audit_v51_v50_first4_220_20260624 --output-dir BPC_future/results/journey_branch_counterfactual_delta_v52_v50_first4_220_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v52_v50_first4_220_zh.md --min-wall-improvement 1.0`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_counterfactual_ranking.py BPC_future/results/journey_branch_counterfactual_delta_v52_v50_first4_220_20260624 --output-dir BPC_future/results/journey_branch_counterfactual_ranking_v53_v52_v50_first4_220_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_ranking_v53_v50_first4_220_zh.md --min-wall-gap 1.0 --min-exact-pricing-gap 1`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/alt_8_14/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/alt_8_14/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/alt_8_14/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/alt_8_14/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:8,14' --set journey_branch_candidate_log_top_n=100`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/alt_14_18/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/alt_14_18/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/alt_14_18/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/alt_14_18/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:14,18' --set journey_branch_candidate_log_top_n=100`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/baseline_5_8/results.csv --log-dir BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/baseline_5_8/logs --solution-dir BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/baseline_5_8/solutions --run-log-dir BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/baseline_5_8/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set 'journey_branch_candidate_priority=force_pair_path:0:2,3=separate_vehicle;1:5,8' --set journey_branch_candidate_log_top_n=100`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624 --output-dir BPC_future/results/journey_branch_impact_audit_v55_v54_proxy_top2_600_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v55_v54_proxy_top2_600_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_counterfactual_delta.py --runbook BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/runbook.json --baseline-result BPC_future/results/journey_branch_candidate_replay_v54_proxy_top2_600_20260624/baseline_5_8/results.csv --baseline-branch-input BPC_future/results/journey_branch_impact_audit_v55_v54_proxy_top2_600_20260624 --alt-branch-input BPC_future/results/journey_branch_impact_audit_v55_v54_proxy_top2_600_20260624 --output-dir BPC_future/results/journey_branch_counterfactual_delta_v56_v54_proxy_top2_600_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_delta_v56_v54_proxy_top2_600_zh.md --min-wall-improvement 1.0`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_counterfactual_ranking.py BPC_future/results/journey_branch_counterfactual_delta_v56_v54_proxy_top2_600_20260624 --output-dir BPC_future/results/journey_branch_counterfactual_ranking_v57_v56_proxy_top2_600_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_counterfactual_ranking_v57_proxy_top2_600_zh.md --min-wall-gap 1.0 --min-exact-pricing-gap 1`
- `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py BPC_future/tests/test_journey_branch_candidate_replay_runbook.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_branch_candidate_replay_runbook`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py BPC_future/results/logs_20260624_v36_branch_score_ab_baseline_220_seed61846 --output-dir BPC_future/results/journey_branch_candidate_replay_runbook_v43_v36_seed61846_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_candidate_replay_runbook_v43_seed61846_zh.md --time-limit 600 --limit 12 --alt-pairs-per-event 4 --candidate-source priority_top --candidate-log-top-n 100`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_score_candidate_coverage.py --score-path BPC_future/results/journey_branch_score_map_v35_v33_all12_20260624/journey_branch_score_rows.json BPC_future/results/logs_20260624_v36_branch_score_ab_baseline_220_seed61846 --output-dir BPC_future/results/journey_branch_score_candidate_coverage_v41_v35_on_v36_baseline_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_candidate_coverage_v41_v35_on_v36_baseline_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_score_candidate_coverage.py --score-path BPC_future/results/journey_branch_score_map_v38_leave_seed61846_pair_20260624/journey_branch_score_rows.json BPC_future/results/logs_20260624_v36_branch_score_ab_baseline_220_seed61846 --output-dir BPC_future/results/journey_branch_score_candidate_coverage_v42_v38_on_v36_baseline_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_candidate_coverage_v42_v38_on_v36_baseline_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/audit_journey_branch_score_candidate_coverage.py BPC_future/tests/test_journey_branch_score_candidate_coverage.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_branch_score_candidate_coverage`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_branch_score_map.py BPC_future/results/journey_branch_counterfactual_ranking_v33_v32_all12_20260624 --output-dir BPC_future/results/journey_branch_score_map_v38_leave_seed61846_pair_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_map_v38_leave_seed61846_pair_zh.md --key-scope pair --exclude-instance-contains seed61846`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 220 --results-csv BPC_future/results/20260624_v39_branch_score_leave_seed61846_pair_optin_220_seed61846.csv --log-dir BPC_future/results/logs_20260624_v39_branch_score_leave_seed61846_pair_optin_220_seed61846 --solution-dir BPC_future/results/solutions_20260624_v39_branch_score_leave_seed61846_pair_optin_220_seed61846 --run-log-dir BPC_future/results/run_logs_20260624_v39_branch_score_leave_seed61846_pair_optin_220_seed61846 --timeout-kill-after 30s --quiet --set journey_branch_candidate_log_top_n=100 --set journey_branch_candidate_priority=branch_score --set journey_branch_candidate_score_path=BPC_future/results/journey_branch_score_map_v38_leave_seed61846_pair_20260624/journey_branch_score_rows.json`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_score_ab.py --baseline-csv BPC_future/results/20260624_v36_branch_score_ab_baseline_220_seed61846.csv --optin-csv BPC_future/results/20260624_v39_branch_score_leave_seed61846_pair_optin_220_seed61846.csv --baseline-log-dir BPC_future/results/logs_20260624_v36_branch_score_ab_baseline_220_seed61846 --optin-log-dir BPC_future/results/logs_20260624_v39_branch_score_leave_seed61846_pair_optin_220_seed61846 --output-dir BPC_future/results/journey_branch_score_ab_audit_v40_v39_leave_seed61846_pair_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_ab_audit_v40_leave_seed61846_pair_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/audit_journey_branch_score_ab.py BPC_future/tests/test_journey_branch_score_ab_audit.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_branch_score_ab_audit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_score_ab.py --baseline-csv BPC_future/results/20260624_v36_branch_score_ab_baseline_220_seed61846.csv --optin-csv BPC_future/results/20260624_v36_branch_score_ab_optin_220_seed61846.csv --baseline-log-dir BPC_future/results/logs_20260624_v36_branch_score_ab_baseline_220_seed61846 --optin-log-dir BPC_future/results/logs_20260624_v36_branch_score_ab_optin_220_seed61846 --output-dir BPC_future/results/journey_branch_score_ab_audit_v37_v36_seed61846_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_ab_audit_v37_seed61846_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/build_journey_branch_score_map.py BPC_future/tests/test_journey_branch_score_map.py BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_branch_score_map BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_prioritize_branch_score_opt_in BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_branch_score_selection`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_branch_score_map.py BPC_future/results/journey_branch_counterfactual_ranking_v33_v32_all12_20260624 --output-dir BPC_future/results/journey_branch_score_map_v35_v33_all12_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_map_v35_v33_all12_zh.md --key-scope node_depth`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 220 --results-csv BPC_future/results/20260624_v36_branch_score_ab_baseline_220_seed61846.csv --log-dir BPC_future/results/logs_20260624_v36_branch_score_ab_baseline_220_seed61846 --solution-dir BPC_future/results/solutions_20260624_v36_branch_score_ab_baseline_220_seed61846 --run-log-dir BPC_future/results/run_logs_20260624_v36_branch_score_ab_baseline_220_seed61846 --timeout-kill-after 30s --quiet --set journey_branch_candidate_log_top_n=12`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 220 --results-csv BPC_future/results/20260624_v36_branch_score_ab_optin_220_seed61846.csv --log-dir BPC_future/results/logs_20260624_v36_branch_score_ab_optin_220_seed61846 --solution-dir BPC_future/results/solutions_20260624_v36_branch_score_ab_optin_220_seed61846 --run-log-dir BPC_future/results/run_logs_20260624_v36_branch_score_ab_optin_220_seed61846 --timeout-kill-after 30s --quiet --set journey_branch_candidate_log_top_n=12 --set journey_branch_candidate_priority=branch_score --set journey_branch_candidate_score_path=BPC_future/results/journey_branch_score_map_v35_v33_all12_20260624/journey_branch_score_rows.json`
- `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile BPC_future/solver/gat_admission_queue.py BPC_future/solver/journey_driver.py BPC_future/tests/test_gat_target_mode_scheduler.py BPC_future/tests/test_gat_target_mode_certificate_safety.py BPC_future/tests/test_bpc_future.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_gat_target_mode_scheduler BPC_future.tests.test_gat_target_mode_certificate_safety BPC_future.tests.test_bpc_future.BPCFutureTests.test_tail_action_controller_classifies_sparse_broad_and_branch_tail BPC_future.tests.test_bpc_future.BPCFutureTests.test_frontier_refinement_target_requires_rmp_to_reach_incumbent_floor BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_priority_selection BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_after_incomplete_no_column_gate`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 130 --results-csv BPC_future/results/20260624_v17b_support_aware_admission_130_randomtw20_seed61000.csv --log-dir BPC_future/results/logs_20260624_v17b_support_aware_admission_130_randomtw20_seed61000 --solution-dir BPC_future/results/solutions_20260624_v17b_support_aware_admission_130_randomtw20_seed61000 --run-log-dir BPC_future/results/run_logs_20260624_v17b_support_aware_admission_130_randomtw20_seed61000 --timeout-kill-after 30s --quiet --set journey_gat_admission_scheduler_enabled=True --set journey_gat_admission_support_aware_enabled=True --set journey_gat_admission_allow_unsourced_delay=True --set journey_gat_admission_max_delay_rounds=1 --set journey_gat_admission_max_delay_queue_size=256 --set journey_gat_admission_support_demote_inactive_only=True --set journey_gat_admission_support_overlap_threshold=0.6`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 130 --results-csv BPC_future/results/20260624_v17c_default_baseline_130_randomtw20_seed61000.csv --log-dir BPC_future/results/logs_20260624_v17c_default_baseline_130_randomtw20_seed61000 --solution-dir BPC_future/results/solutions_20260624_v17c_default_baseline_130_randomtw20_seed61000 --run-log-dir BPC_future/results/run_logs_20260624_v17c_default_baseline_130_randomtw20_seed61000 --timeout-kill-after 30s --quiet`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 130 --results-csv BPC_future/results/20260624_v18_support_aware_root_safe_130_randomtw20_seed61000.csv --log-dir BPC_future/results/logs_20260624_v18_support_aware_root_safe_130_randomtw20_seed61000 --solution-dir BPC_future/results/solutions_20260624_v18_support_aware_root_safe_130_randomtw20_seed61000 --run-log-dir BPC_future/results/run_logs_20260624_v18_support_aware_root_safe_130_randomtw20_seed61000 --timeout-kill-after 30s --quiet --set journey_gat_admission_scheduler_enabled=True --set journey_gat_admission_support_aware_enabled=True --set journey_gat_admission_allow_unsourced_delay=True --set journey_gat_admission_max_delay_rounds=1 --set journey_gat_admission_max_delay_queue_size=256 --set journey_gat_admission_support_demote_inactive_only=True --set journey_gat_admission_support_overlap_threshold=0.6`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/20260624_v19a_default_baseline_220_randomtw20_seed61000.csv --log-dir BPC_future/results/logs_20260624_v19a_default_baseline_220_randomtw20_seed61000 --solution-dir BPC_future/results/solutions_20260624_v19a_default_baseline_220_randomtw20_seed61000 --run-log-dir BPC_future/results/run_logs_20260624_v19a_default_baseline_220_randomtw20_seed61000 --timeout-kill-after 30s --quiet`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/20260624_v19b_support_aware_depth1_220_randomtw20_seed61000.csv --log-dir BPC_future/results/logs_20260624_v19b_support_aware_depth1_220_randomtw20_seed61000 --solution-dir BPC_future/results/solutions_20260624_v19b_support_aware_depth1_220_randomtw20_seed61000 --run-log-dir BPC_future/results/run_logs_20260624_v19b_support_aware_depth1_220_randomtw20_seed61000 --timeout-kill-after 30s --quiet --set journey_gat_admission_scheduler_enabled=True --set journey_gat_admission_support_aware_enabled=True --set journey_gat_admission_allow_unsourced_delay=True --set journey_gat_admission_max_delay_rounds=1 --set journey_gat_admission_max_delay_queue_size=256 --set journey_gat_admission_support_demote_inactive_only=True --set journey_gat_admission_support_overlap_threshold=0.6`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 220 --results-csv BPC_future/results/20260624_v19c_support_aware_exact_depth1_220_randomtw20_seed61000.csv --log-dir BPC_future/results/logs_20260624_v19c_support_aware_exact_depth1_220_randomtw20_seed61000 --solution-dir BPC_future/results/solutions_20260624_v19c_support_aware_exact_depth1_220_randomtw20_seed61000 --run-log-dir BPC_future/results/run_logs_20260624_v19c_support_aware_exact_depth1_220_randomtw20_seed61000 --timeout-kill-after 30s --quiet --set journey_gat_admission_scheduler_enabled=True --set journey_gat_admission_support_aware_enabled=True --set journey_gat_admission_allow_unsourced_delay=True --set journey_gat_admission_max_delay_rounds=1 --set journey_gat_admission_max_delay_queue_size=256 --set journey_gat_admission_support_demote_inactive_only=True --set journey_gat_admission_support_overlap_threshold=0.6 --set \"journey_gat_admission_scheduler_pricing_kinds=['heuristic','sharded_pulse_hidden_negative_worker','exact']\"`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 160 --results-csv BPC_future/results/20260624_v20_support_shadow_nomutate_160_randomtw20_seed61000.csv --log-dir BPC_future/results/logs_20260624_v20_support_shadow_nomutate_160_randomtw20_seed61000 --solution-dir BPC_future/results/solutions_20260624_v20_support_shadow_nomutate_160_randomtw20_seed61000 --run-log-dir BPC_future/results/run_logs_20260624_v20_support_shadow_nomutate_160_randomtw20_seed61000 --timeout-kill-after 30s --quiet --set journey_gat_admission_scheduler_enabled=True --set journey_gat_admission_support_aware_enabled=True --set journey_gat_admission_allow_unsourced_delay=True --set \"journey_gat_admission_scheduler_pricing_kinds=[]\"`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_support_aware_branch_exact_tail.py BPC_future/results/logs_20260624_v20_support_shadow_nomutate_160_randomtw20_seed61000 --output-dir BPC_future/results/journey_support_aware_branch_exact_tail_v20_shadow_seed61000_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_support_aware_branch_exact_tail_v20_shadow_seed61000_zh.md --min-depth 1`
- `find BPC_future/logical_graph/tasks_020 -name '*_logical_graph.json' | sort > /tmp/bpc_future_tasks020_60.txt`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances $(cat /tmp/bpc_future_tasks020_60.txt) --time-limit 160 --results-csv BPC_future/results/20260624_v21_support_shadow_nomutate_160_randomtw20_60instances.csv --log-dir BPC_future/results/logs_20260624_v21_support_shadow_nomutate_160_randomtw20_60instances --solution-dir BPC_future/results/solutions_20260624_v21_support_shadow_nomutate_160_randomtw20_60instances --run-log-dir BPC_future/results/run_logs_20260624_v21_support_shadow_nomutate_160_randomtw20_60instances --timeout-kill-after 30s --max-workers 3 --quiet --set journey_gat_admission_scheduler_enabled=True --set journey_gat_admission_support_aware_enabled=True --set journey_gat_admission_allow_unsourced_delay=True --set "journey_gat_admission_scheduler_pricing_kinds=[]"`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_support_aware_branch_exact_tail.py BPC_future/results/logs_20260624_v21_support_shadow_nomutate_160_randomtw20_60instances --output-dir BPC_future/results/journey_support_aware_branch_exact_tail_v21_shadow_randomtw20_60instances_20260624 --report BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_support_aware_branch_exact_tail_v21_shadow_randomtw20_60instances_zh.md --min-depth 1`
- `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/audit_journey_support_aware_branch_exact_tail.py BPC_future/tests/test_journey_support_aware_branch_exact_tail_audit.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_support_aware_branch_exact_tail_audit`
- `PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/audit_journey_late_negative_tail.py BPC_future/scripts/build_journey_tail_impact_training_rows.py BPC_future/scripts/build_journey_branch_tail_positive_runbook.py BPC_future/scripts/audit_journey_tail_action_controller.py BPC_future/solver/journey_driver.py BPC_future/tests/test_journey_late_negative_tail_audit.py BPC_future/tests/test_journey_tail_impact_training_rows.py BPC_future/tests/test_journey_branch_tail_positive_runbook.py BPC_future/tests/test_journey_tail_action_controller_audit.py BPC_future/tests/test_bpc_future.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_late_negative_tail_audit BPC_future.tests.test_journey_tail_impact_training_rows BPC_future.tests.test_journey_branch_tail_positive_runbook BPC_future.tests.test_journey_tail_action_controller_audit BPC_future.tests.test_bpc_future.BPCFutureTests.test_tail_action_controller_classifies_sparse_broad_and_branch_tail BPC_future.tests.test_bpc_future.BPCFutureTests.test_frontier_refinement_target_requires_rmp_to_reach_incumbent_floor BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_priority_selection BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_after_incomplete_no_column_gate`
- `git diff --check`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/solver/journey_driver.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_resource_pareto_completion`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_child_min_iter_and_child_order BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_after_incomplete_no_column_gate`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... gat_on_root56_no_column_poolsplit_width_greedy_apollo20_direct200 ...`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... gat_on_root56_no_column_depth2_width_greedy_apollo20_direct200 ...`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... gat_on_root56_no_column_depth3_width_greedy_apollo20_direct200 ...`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_prioritize_pool_split_width BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_priority_selection BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_after_incomplete_no_column_gate`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/audit_journey_branch_impact.py BPC_future/tests/test_journey_branch_impact_audit.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_branch_impact_audit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py ... --output-dir BPC_future/results/journey_branch_impact_audit_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_audit_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/learning/branch_impact_model.py BPC_future/tests/test_gat_branch_impact_model.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_gat_branch_impact_model`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_branch_impact_audit BPC_future.tests.test_gat_branch_impact_model`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... gat_on_root56_no_column_depth3_width_selectedlog_refresh_greedy_apollo20_direct200 ...`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py ... --output-dir BPC_future/results/journey_branch_impact_audit_selectedlog_refresh_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_selectedlog_refresh_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... gat_on_root56_no_column_poolsplit_width_selectedlog_refresh_greedy_apollo20_direct200 ...`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py ... --output-dir BPC_future/results/journey_branch_impact_audit_poolsplit_selectedlog_refresh_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_poolsplit_selectedlog_refresh_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/audit_journey_weak_negative_tail.py BPC_future/tests/test_journey_weak_negative_tail_audit.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_weak_negative_tail_audit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_weak_negative_tail.py ... --output-dir BPC_future/results/journey_weak_negative_tail_audit_greedy_selectedlog_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_greedy_selectedlog_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... gat_on_root56_no_column_poolsplit_width_scan8_selectedlog_greedy_apollo20_direct200 ...`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_weak_negative_tail.py ... --output-dir BPC_future/results/journey_weak_negative_tail_audit_poolsplit_scan8_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_poolsplit_scan8_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py ... --output-dir BPC_future/results/journey_branch_impact_audit_poolsplit_scan8_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_poolsplit_scan8_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/build_journey_tail_impact_training_rows.py BPC_future/tests/test_journey_tail_impact_training_rows.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_tail_impact_training_rows`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_tail_impact_training_rows.py ... --output-dir BPC_future/results/journey_tail_impact_training_rows_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/journey_completion_tail_direction1_v154_20260623 --output-dir BPC_future/results/journey_branch_impact_audit_v154_alllogs_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_v154_alllogs_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_tail_impact_training_rows.py ... --output-dir BPC_future/results/journey_tail_impact_training_rows_v154_alllogs_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_v154_alllogs_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/audit_journey_tail_positive_gap.py BPC_future/tests/test_journey_tail_positive_gap.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_tail_positive_gap`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_tail_positive_gap.py BPC_future/results/journey_tail_impact_training_rows_v154_alllogs_20260623 --output-dir BPC_future/results/journey_tail_positive_gap_audit_v154_alllogs_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_positive_gap_v154_alllogs_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py BPC_future/scripts/build_journey_branch_tail_positive_runbook.py BPC_future/tests/test_journey_branch_tail_positive_runbook.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_prioritize_pool_split_width BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_force_pair_for_controlled_ab BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_priority_selection BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_forced_pair_binding BPC_future.tests.test_journey_branch_tail_positive_runbook`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_branch_tail_positive_runbook.py BPC_future/results/journey_tail_positive_gap_audit_v154_alllogs_20260623/summary.json --output-dir BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_tail_positive_runbook_v154_root_force_zh.md --limit 8`
- `/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... --set journey_branch_candidate_priority=force_pair:2,13 ...`
- `/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... --set journey_branch_candidate_priority=force_pair:2,3 ...`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/journey_branch_tail_positive_runbook_v154_root_force_20260623/runs --output-dir BPC_future/results/journey_branch_impact_audit_v154_forced_pairs_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_v154_forced_pairs_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_tail_impact_training_rows.py --branch-input BPC_future/results/journey_branch_impact_audit_v154_forced_pairs_20260623 --output-dir BPC_future/results/journey_tail_impact_training_rows_v154_forced_pairs_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_v154_forced_pairs_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_tail_positive_gap.py BPC_future/results/journey_tail_impact_training_rows_v154_forced_pairs_20260623 --output-dir BPC_future/results/journey_tail_positive_gap_audit_v154_forced_pairs_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_positive_gap_v154_forced_pairs_zh.md --top-n 10`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_prioritize_pool_split_width BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_can_force_pair_for_controlled_ab BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_priority_selection BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_forced_pair_binding BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_candidate_log_records_depth_forced_pair_binding`
- `/home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... --set 'journey_branch_candidate_priority=force_pair_depth:0:2,3;1:14,20' ...`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/journey_branch_tail_depth_sequence_v154_20260623/runs --output-dir BPC_future/results/journey_branch_impact_audit_v154_depth_sequence_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_v154_depth_sequence_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_tail_impact_training_rows.py --branch-input BPC_future/results/journey_branch_impact_audit_v154_depth_sequence_20260623 --output-dir BPC_future/results/journey_tail_impact_training_rows_v154_depth_sequence_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_v154_depth_sequence_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_tail_positive_gap.py BPC_future/results/journey_tail_impact_training_rows_v154_depth_sequence_20260623 --output-dir BPC_future/results/journey_tail_positive_gap_audit_v154_depth_sequence_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_positive_gap_v154_depth_sequence_zh.md --top-n 10`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... gat_on_root56_depth3_width_crossnode_cache_greedy_apollo20_direct200 ...`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_crossnode_cache_greedy_apollo20_direct200 --output-dir BPC_future/results/journey_branch_impact_audit_crossnode_cache_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_crossnode_cache_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_weak_negative_tail.py BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_crossnode_cache_greedy_apollo20_direct200 --output-dir BPC_future/results/journey_weak_negative_tail_audit_crossnode_cache_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_crossnode_cache_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... gat_on_root56_depth3_width_force26_greedy_apollo20_direct200 ... --set journey_branch_candidate_priority=force_pair:2,6`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_force26_greedy_apollo20_direct200 --output-dir BPC_future/results/journey_branch_impact_audit_force26_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_force26_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_weak_negative_tail.py BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_force26_greedy_apollo20_direct200 --output-dir BPC_future/results/journey_weak_negative_tail_audit_force26_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_force26_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_tail_impact_training_rows.py --branch-input BPC_future/results/journey_branch_impact_audit_force26_20260623 --weak-input BPC_future/results/journey_weak_negative_tail_audit_force26_20260623 --output-dir BPC_future/results/journey_tail_impact_training_rows_force26_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_force26_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_tail_positive_gap.py BPC_future/results/journey_tail_impact_training_rows_force26_20260623 --output-dir BPC_future/results/journey_tail_positive_gap_audit_force26_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_positive_gap_force26_zh.md --top-n 10`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py ... gat_on_root56_depth3_width_force26_depth3_49_greedy_apollo20_direct200 ... --set 'journey_branch_candidate_priority=force_pair_depth:0:2,6;1:14,17;2:2,11;3:4,9'`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_force26_depth3_49_greedy_apollo20_direct200 --output-dir BPC_future/results/journey_branch_impact_audit_force26_depth3_49_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_force26_depth3_49_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_weak_negative_tail.py BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_force26_depth3_49_greedy_apollo20_direct200 --output-dir BPC_future/results/journey_weak_negative_tail_audit_force26_depth3_49_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_weak_negative_tail_force26_depth3_49_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/build_journey_tail_impact_training_rows.py --branch-input BPC_future/results/journey_branch_impact_audit_force26_depth3_49_20260623 --weak-input BPC_future/results/journey_weak_negative_tail_audit_force26_depth3_49_20260623 --output-dir BPC_future/results/journey_tail_impact_training_rows_force26_depth3_49_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_impact_training_rows_force26_depth3_49_zh.md`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_tail_positive_gap.py BPC_future/results/journey_tail_impact_training_rows_force26_depth3_49_20260623 --output-dir BPC_future/results/journey_tail_positive_gap_audit_force26_depth3_49_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_positive_gap_force26_depth3_49_zh.md --top-n 10`
