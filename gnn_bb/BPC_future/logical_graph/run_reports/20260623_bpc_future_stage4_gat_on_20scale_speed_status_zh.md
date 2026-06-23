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
- GAT/support-aware admission 对 root 有帮助，但 proof tail 的主要剩余问题仍是 frontier suffix bound 太松；
- 直接全局打开更重的 route-aware/available-mask bound 会吃掉太多时间；
- 下一步应做 tail-only / active-token-only frontier refinement，只对 final-probe ledger 中最小 active frontier token 做更强局部下界，失败时保留原 bound。

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
- 下一步应实现 Tier 1 critical-token micro-expansion，并同步关注提高 incumbent / RMP bound / branch 选择，而不是继续全局加重 unique-route20 或 AMCB。

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
- `global_remaining_rc_lb < fathom_rc_target`
- critical token count 和 floor multiplicity 都小
- 预计 child 总数不超预算
- frontier coverage 完整

如果 target 接近 0 但几百/几千 token 都低于 target，这是 B 类“大面积低水位”，不能逐 token split，应转向 aggregate route-aware bound、更强 completion relaxation、cuts/formulation 或 token region 重组。

详细记录见：

- `BPC_future/logical_graph/run_reports/20260623_bpc_future_v7_waterline_frontier_refinement_diag_zh.md`

## 验证

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
