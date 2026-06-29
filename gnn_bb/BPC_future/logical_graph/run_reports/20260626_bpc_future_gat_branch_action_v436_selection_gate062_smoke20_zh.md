# GAT Branch Action v436 Selection-Gate Smoke 与下一步计划

日期：2026-06-26

## 本轮已实现

- 补齐 branch/action 训练链路：`branch_impact_model` 已包含 `predicted_walltime_gain`、`predicted_child_proof_cpu`、`predicted_time_to_certificate`。
- 数据集构建改成以连续 wall-time gain 为主标签，200s 只保留为评估指标，不再作为训练正例硬阈值。
- `journey_branch_candidates` / `journey_branch` / `journey_child_queued` 日志已记录 baseline/scored/selected pair、score coverage、selected changed、exact-safe child bound 字段。
- score map 导出支持 `branch_probability` / `walltime_gain` / `hybrid`，并新增 `scoped_key`，避免不同实例的 `node/depth/pair` 同名 key 相互覆盖。
- solver 侧修正 score-map 归一化：无 context 时不再把 instance-scoped rows 投影成 generic key；有当前实例 context 时才允许转成 solver lookup key。
- 实现并测试 score-gated branch selection 与 score-gated early branch 的安全壳；v436 smoke 只打开普通 branch selection gate，early branch 全关，用来隔离 branch score 本身的效果。

## v436 实测配置

```text
run_dir = BPC_future/results/20260626_v436_branch_score_selection_gate062_smoke20_topscore12
base_config = BPC_future/configs/moon_trek_20_smoke.yaml
score_map = BPC_future/results/gat_branch_action_v430_randomtw60_20260626/score_map_v433_v421_depth01_top200_hybrid_scoped/journey_branch_score_rows.json
selection_gate_min_score = 0.62
selection_gate_total_child_width <= 700
selection_gate_balance_gap <= 100
selection_gate_max_child_width <= 380
admission = off
early_branch = off
subset cuts = off
max_workers = 4
external_limit = 600s
```

## 总体结果

```text
status_counts = {'EXTERNAL_TIME_LIMIT': 8, 'TIME_LIMIT': 1, 'OPTIMAL': 3}
capped_mean = 497.213s
baseline_capped_mean = 535.693s
v430_capped_mean = 496.919s
v432_capped_mean = 513.508s
gain_vs_baseline = +38.480s
gain_vs_v430 = -0.294s
gain_vs_v432 = +16.295s
<=200s OPTIMAL = 2/12
selected_pair_changed_count = 11
selection_gate_pass_count = 12
early_branch_trigger_count = 0
non_exact_child_count = 0
```

v436 的核心收益是新增了一个严格 OPTIMAL 正例：

- `sector-wave seed61923`: baseline/v430/v432 都是 600s 外部超时，v436 变成 `OPTIMAL 405.2s`。root branch 从 `[1,13]` 改成 `[13,20]`，score=0.626996，gate=ok。

同时保住了之前的强正例：

- `greedy-anchor seed61001`: baseline `327.7s OPTIMAL`，v436 `58.8s OPTIMAL`，root branch 从 `[2,18]` 改成 `[3,12]`。

但 v436 没有解决整体 20-scale proof tail：

- 12 个 smoke 里仍有 8 个外部超时。
- 降阈值到 0.62 后虽然多了 10 次以上 branch changed，但大部分只改变搜索路径，没有产生闭环证书。
- 这说明当前 score 已能识别少数好分支，但 precision/coverage 仍不足，不能直接全量推广。

## 关键判断

1. **branch score 有真实作用，但作用是局部的。**  
   它能把某些 root RF pair 换成更快闭环的 pair，例如 `seed61001` 和 `seed61923`。这类收益是 exact-safe 的，因为分支只改变搜索顺序/子问题结构，不提供 official bound，也不剪枝。

2. **selection gate 是必须的。**  
   v432/v436 都证明了 gate 能拦住高分但 child pool 过宽的分支，避免 `seed61414`、`seed61846` 这类 full-open 退化扩大。问题是 v436 的 0.62 gate 又放进了不少“无效果改分支”，下一版要把这些作为 hard negative。

3. **scoped score map 是必要修正。**  
   旧 score rows 的 generic key 会让不同实例的 `node:0:depth:0:i,j` 互相覆盖。v433 scoped map 修掉后，训练/评估才不再混入跨实例泄漏或覆盖污染。

4. **当前瓶颈不是继续找负列，而是 branch proof tail 的闭环质量。**  
   v436 的失败实例大多不是“没有 branch score 命中”，而是命中后仍然 600s 超时，说明模型缺少 child proof CPU、child width、time-to-certificate 的强因果标签。

5. **early branch 不能裸开。**  
   本轮没有打开 early branch；这是对的。普通 branch score 还没有足够 precision，直接 score-gated early branch 只会放大错误分支的代价。

## 下一步优化计划

### P0：构造 v437 hard-negative 强化数据集

把 v436 结果并入 branch/action 数据集：

- strong positive：
  - `seed61001`: `327.7s -> 58.8s OPTIMAL`
  - `seed61923`: `600s timeout -> 405.2s OPTIMAL`
- hard negative / no-effect changed：
  - v436 中 root changed 但仍 600s 的实例，例如 `seed61103`、`seed61520`、`seed61411`、`seed61104`、`random-wave seed61001`
- guarded negative：
  - gate 因 child width 过宽拒绝的高分 pair，继续作为 child-width 风险标签。

输出新数据集目录建议：

```text
BPC_future/data/gat_branch_action_sanity/v437_randomtw60_branch_replay_20260626/
```

训练目标调整：

- `walltime_gain` 主 loss 保持。
- hard negative 权重上调，尤其是“高 score 但仍 timeout”的 changed pair。
- `child_proof_cpu` / `time_to_certificate` 辅助头权重上调，避免模型只学到“看起来像好分支”，却不学 proof cost。
- 导出 score map 时优先试 `hybrid` 与 `walltime_gain` 两种模式，不再只看 branch probability。

### P1：把 gate 从“分数阈值”改成“分数 + proof-risk”阈值

v436 说明 `score >= 0.62` 太粗。下一版 gate 应要求：

```text
selected_score >= calibrated_min_score
predicted_walltime_gain >= min_gain
predicted_child_proof_cpu <= max_child_proof_cpu
pool_total_child_width <= width_cap
pool_balance_gap <= balance_cap
score_source present
```

这样把 `seed61923` 这种真收益留下，把“改了但仍 600s”的 pair 压下去。

### P2：先做 12-instance 双 score-map smoke，不直接全量 60

下一轮不直接跑全量。先在同一 12-instance 上比较：

- v437-hybrid gate
- v437-walltime-gain gate
- v436 gate 0.62
- v432 gate 0.67

通过线：

- OPTIMAL 不低于 3/12；
- capped mean 明显低于 v436，目标至少再降 10s；
- 不新增 `OPTIMAL -> timeout`；
- changed-but-timeout 数明显下降。

### P3：score-gated early branch 只在 P2 通过后打开

early branch 的目标是减少 proof tail，但它会提前改变树形结构，所以必须延后：

- 只在 score source 命中、proof-risk gate 通过时触发；
- child 继续继承合法旧 lower bound；
- `exact_bound_available=False`、`child_lower_bound_exact=False` 只能审计，不能用于 fathom/prune；
- 对 5/10 先跑 no-regression smoke，再跑 20。

### P4：admission 继续做诊断，不回到主加速线

本轮 branch score 已经能给出更直接的 wall-time 正例。admission 暂时只保留：

- active support 是否改变；
- RMP objective 是否改变；
- 后续 branch pair 是否改变；
- 是否 delay/release/pass-through。

不把 admission 与 v437 主实验混跑，避免再次把列调度和分支效果混在一起。

## 当前结论

v436 证明 branch score 主线值得继续：它新增了一个严格 OPTIMAL 加速实例，并保持了已有强正例。但 v436 也证明当前模型还不能直接扩到全量 20-scale，因为多数 changed branch 仍然没有带来 certificate closure。下一版关键不是继续放宽 gate，而是把 v436 这些“改了但没用”的 pair 转成 hard negative，让 GAT 学会 proof-cost 风险。

