# BPC_future Stage 4 方向一续跑报告：GAT 作用边界与 20-task root CG 瓶颈

日期：2026-06-23

## 结论

本轮主攻方向一：不让 GAT 参与证明或裁剪，只围绕精确求解的 root CG、pricing 调度和 completion-bound 尾部做 exact-safe 优化。

关键结论是：当前剩余 20-task apollo greedy-anchor 失败实例的主瓶颈不是 V154 分类精度，也不是 final completion-bound proof 被晚调用，而是根节点 column generation 尚未收敛。日志显示到 190s 仍不断有真实负列被 exact pricing 找到，且大量新增列为 inactive-only，RMP objective 仍未稳定到 certificate candidate。因此，把 V154 的 77/78 修到 78/78 预计不能直接带来 20-task wall-time 改善。

GAT 在这里的正确角色应是：

- 作为候选列/候选 task-set 的排序和注入器；
- 作为 learned helper 是否值得运行的 ROI gate；
- 作为 shadow/opt-in 观测源，用于判断哪些 learned 调用真正减少 RMP/pricing 轮数；
- 不能作为 no-negative certificate，不能裁剪官方列空间，不能改变 lower bound。

## 已做代码改动

文件：`BPC_future/solver/journey_driver.py`

1. 给 root exact pricing 路径补齐和 branch 路径一致的 completion-bound final probe 预览、pre-retry reserve、pre-exact handoff 钩子。
2. 给 root ordinary retry 增加 pre-reserve 后跳过普通 retry、直达 final probe 的 exact-safe 调度分支。
3. 给 same-dual supplement 增加 `journey_same_dual_supplement_require_certificate_candidate` 可选开关，默认 `True`，不改变默认行为；实验时可允许非 certificate candidate 的退化小批量 exact 后补采同一 dual 下的真实负列。

这些改动只改变 oracle 调度和 worker 触发条件。任何 no-column / miss 仍不能证明节点；节点闭合仍必须依赖 exact pricing 或 completion-bound certificate。

## 20-task apollo greedy-anchor 诊断

实例：

`BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json`

基准 direct190 handoff probe：

- 状态：`TIME_LIMIT`
- solving_time：`190.075670`
- node_count：`1`
- rmp_solves：`42`
- pricing_calls / exact_pricing_calls：`52 / 10`
- columns：`347`
- completion-bound retry：`0`

日志要点：

- 后半段 exact pricing 仍持续找到负列；
- `cg_iter=41` 仍找到 reduced cost 约 `-0.017726` 的列；
- `certificate_candidate=False`，`certificate_flat_rounds=0`；
- 最后一次 exact/retry 只剩约 3s，状态为 `INCOMPLETE_LIMIT / ng_dssr_time_limit`；
- 没有进入 completion-bound final proof，说明不是 final judge 单点尾部问题。

## 负结果 probe

1. root pre-reserve + skip ordinary retry + batch12 + no hidden patrol：
   - 200s 外部超时；
   - 无实质改善。

2. root pre-exact handoff + batch12 + no hidden patrol：
   - 200s 外部超时；
   - direct190 可返回内部 `TIME_LIMIT`，但没有 completion-bound retry；
   - 说明尚未进入可证明尾部。

3. 非 certificate same-dual supplement：
   - `exact_same_dual_supplement` 触发 8 次；
   - 每次 `negative_journeys=0`；
   - 结果仍为 `TIME_LIMIT`，`rmp_solves=42`，`columns=347`；
   - 该机制对本实例不是有效突破口。

4. late selection mode 改为 `reduced_cost`：
   - 结果仍为 `TIME_LIMIT`，`rmp_solves=42`，`columns=347`；
   - 排序模式单独不是主瓶颈。

## 5/10 回归验证

5-task sentinel：

- apollo sector-wave：`OPTIMAL`，solving_time `0.298675`，wall `2.313428`
- tranq sector-wave：`OPTIMAL`，solving_time `0.312206`，wall `2.314902`

10-task sentinel：

- apollo sector-wave：`OPTIMAL`，solving_time `2.607320`，wall `4.457562`
- tranq sector-wave：`OPTIMAL`，solving_time `1.456471`，wall `3.304849`

最小 5/10 no-regression 通过。

## 下一步建议

不要继续把主线压在 V154 分类阈值或普通 GAT precision/recall 上。对 20-task 真正有希望的方向是：

1. 提高 root CG 中会改变 LP 支撑的列的发现比例，而不是增加 inactive-only 列；
2. 设计 active-support / replacement-focused exact worker，但每条列仍做 true reduced-cost 校验；
3. 从日志中抽取 active_changed_task_set、inactive_changed_task_set、objective_delta 的同轮数据，训练或规则化一个 ROI gate，让 GAT 只服务于“减少 RMP/pricing 轮数”的候选注入；
4. 对 sector/tranq 继续单独处理 branch tree closure；它和 apollo root CG 瓶颈不是同一类失败。

