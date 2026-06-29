# GAT Branch Action v438 Proof-Risk Gate Smoke

日期：2026-06-26

## 目的

v436 证明 branch score 能带来真实 OPTIMAL 加速，但 0.62 gate 放进了多条 changed 后仍 600s timeout 的无效分支。v438 不再继续放宽阈值，而是在 v433 scoped score map 上叠加 v436 proof-risk evidence：

- 两个严格正例 root pair boost 到 `0.68`。
- 六个 `changed -> EXTERNAL_TIME_LIMIT` 的 root pair suppress 到 `0.05`。
- solver 仍只使用 score 做 opt-in branch 排序，不提供 official bound、certificate 或剪枝依据。

## 产物

```text
v437_delta_rows = BPC_future/results/journey_branch_counterfactual_delta_v437_from_v436_selection_gate062_20260626
v437_dataset = BPC_future/data/gat_branch_action_sanity/v437_randomtw60_branch_replay_20260626
v437_checkpoint = BPC_future/data/gat_branch_action_sanity/v437_randomtw60_branch_replay_20260626/gat_branch_action_v437.pt
v438_score_map = BPC_future/results/gat_branch_action_v437_randomtw60_20260626/score_map_v438_v433_plus_v436_proofrisk_overlay/journey_branch_score_rows.json
v438_run = BPC_future/results/20260626_v438_branch_score_proofrisk_gate067_smoke20_topscore12
```

v437 纯训练 checkpoint 的离线分离效果不好：它把 `seed61923` 真正例打得偏低，也把部分 no-effect timeout 打得很高。因此没有直接用 v437 checkpoint score map 跑 smoke，而是用了 v438 proof-risk overlay。

## v438 Smoke 配置

```text
base_config = BPC_future/configs/moon_trek_20_smoke.yaml
instances = same 12 top-score 20-scale smoke instances
selection_gate_min_score = 0.67
selection_gate_total_child_width <= 700
selection_gate_balance_gap <= 100
selection_gate_max_child_width <= 380
admission = off
early_branch = off
subset cuts = off
external_limit = 600s
max_workers = 4
```

## 结果

```text
status_counts = {'EXTERNAL_TIME_LIMIT': 8, 'TIME_LIMIT': 1, 'OPTIMAL': 3}
capped_mean = 497.043s
baseline_capped_mean = 535.693s
v430_capped_mean = 496.919s
v432_capped_mean = 513.508s
v436_capped_mean = 497.213s
gain_vs_baseline = +38.650s
gain_vs_v432 = +16.465s
gain_vs_v436 = +0.170s
<=200s OPTIMAL = 2/12
selected_pair_changed_count = 2
selection_gate_pass_count = 2
early_branch_trigger_count = 0
non_exact_child_count = 0
```

实际 changed pair 只有两个，且都是严格正例：

- `greedy-anchor seed61001`: `[2,18] -> [3,12]`, `327.7s OPTIMAL -> 58.4s OPTIMAL`。
- `sector-wave seed61923`: `[1,13] -> [13,20]`, `600s EXTERNAL -> 405.1s OPTIMAL`。

v436 中六个 no-effect changed timeout 在 v438 全部被压回 baseline branch：

- `apollo15 greedy seed61103`: `[1,20]` 被 suppress，root 保持 `[1,2]`。
- `tranq greedy seed61520`: `[6,11]` 被 suppress，root 保持 `[4,7]`。
- `tranq random-wave seed61411`: `[1,12]` 被 suppress，root 保持 `[1,9]`。
- `tranq greedy seed61103`: `[1,4]` 被 suppress，root 保持 `[10,15]`。
- `tranq sector-wave seed61104`: `[1,2]` 被 suppress，root 保持 `[5,14]`。
- `tranq random-wave seed61001`: `[8,19]` 被 suppress，root 保持 `[8,13]`。

## 判断

v438 比 v436 更健康：同样 3/12 OPTIMAL，但 changed branch 从 11 次降到 2 次，且 2 次都是已验证收益。它说明当前最有效的方向不是继续放开 GAT，而是把 branch score 变成 proof-risk gated opt-in。

但 v438 仍然没有达到目标：

- 20-scale smoke 仍有 8/12 外部超时。
- 12-smoke 没有达到全量推广条件，更不能说明所有 20-scale 能在 600s 内 OPTIMAL。
- 当前 score 只解决了“少数 root 错分支/好分支选择”，没有解决大多数 baseline-hard 实例的 proof tail。

## 下一步

1. 把 v438 proof-risk overlay 固化成可复用的 score-map postprocessor，而不是一次性脚本。
2. 用 v438 作为新的 branch-score safety baseline，扩充更多 random-TW 20-scale root contexts，但每次都要求：
   - only changed if known-positive or proof-risk gate passed；
   - changed-but-timeout 自动回流为 hard negative；
   - score map 不允许跨实例 key 泄漏。
3. 继续补 child proof-cost 标签。当前模型失败点是无法泛化预测 `time_to_certificate`，不是缺 branch-probability 头。
4. 在 12-smoke 上尝试 score-gated early branch 前，必须先让 normal branch selection 的 changed-but-timeout 数继续接近 0。
5. 20 全量 600s OPTIMAL 仍需要和 branch score 并行推进 proof tail 改造：更强 branch child ordering、safe child proof reuse、以及后续 pricing-compatible cuts / formulation strengthening。

