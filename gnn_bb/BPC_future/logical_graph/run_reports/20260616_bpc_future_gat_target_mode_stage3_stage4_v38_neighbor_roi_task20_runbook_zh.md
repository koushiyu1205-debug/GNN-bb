# 2026-06-16 BPC_future GAT Stage 3/4 v38 Neighbor-ROI Task20 Runbook 桥接报告

## 读取范围

本轮先复读了 `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`、Stage 1/2 结构与采集报告、v15 Stage 3 hard-negative / missed high-ROI 相关结论、最新 v37 neighbor-ROI task20 contrast plan、Stage 4 exact-safe A/B / certificate audit，以及 Stage 5 的 20/30/50/100 scale acceleration 目标。

当前主线没有改变：GAT / CBF / kNN / OOD 只能让前段 column generation 更聪明，影响候选发现、排序、admission scheduling 和 opt-in worker target；所有进入 RMP 的列仍必须经过当前 true dual / cut / branch 下的 true reduced-cost 验证；最终 OPTIMAL / no-negative certificate 只能来自当前 branch/cut/dual 下覆盖整个配置宇宙的 exact pricing closure。

## v15 结论对本轮的约束

v15 不是一个可以直接进入 Stage 4 的 checkpoint。它把 v14 exact safe-hit batch8 的真实 trajectory ROI 回流为 hard-negative 是正确方向，并消除了 false-safe，但 accepted batch 证据量和 safe precision CI lower bound 仍不足。

更重要的是，v15 后续 opportunity mining / score-margin audit 已经回答了“missed high-ROI 是差一点还是结构性分不开”：主 blocker 不是 batch threshold 差一点，而是 candidate head 对 high-ROI batch 内 safe candidate 的分数结构性偏低，并且还有若干 missed high-ROI 缺 same-context low-ROI / delay 对照。因此本轮不能靠降低 precision / ROI / CI 门槛推进，而应继续补 same-context 正负对照和可回流的 target-worker trajectory rows。

## v37 到 v38 runbook

v37 输入：

```text
summary = BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/summary.json
candidates = BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/candidates.json
status = ready
candidate_count = 16
selected_context_count = 4
pairwise_context_target_count = 4
official_bound_effect = false
certificate_ready = false
runs_bpc_or_pricing = false
```

四个 task20 same-context 候选组：

| context | candidates | opportunity_score | instance |
|---|---:|---:|---|
| `b6d808ebac2a6dd8` | 4 | 41.318527 | `apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715` |
| `9fadf4f7b39742a2` | 4 | 27.367254 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206` |
| `ac15bc4e7e3d6fff` | 4 | 0.809451 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104` |
| `79fde658840fe2b8` | 4 | 0.773408 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718` |

本轮生成了 guarded worker A/B runbook：

```text
runbook_summary = BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/summary.json
runbook_markdown = BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook.md
status = ready
worker_method = target_materialization_fixed
worker_batch_size = 1
input_candidate_count = 16
candidate_group_count = 16
candidate_run_count = 16
context_count = 4
instance_count = 4
command_count = 34
small_no_regression_count = 2
all_checks_pass = true
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_ready = false
production_ready = false
default_enabled = false
```

`command_count = 34` 的含义是：2 条 5/10 no-regression sentinel 命令，加上 16 组 task20 candidate 的 mainline baseline / target-priority worker 成对命令。生成 runbook 本身没有执行 BPC，也没有执行 pricing；当前目录下没有 candidate run 的 `results.csv`。

## Exact-safe 防线

本 runbook 的 worker 是显式 opt-in，并且作用域固定为 same-context `target_materialization_fixed`：

- candidate baseline / worker 都保留主线 GAT/learning，用于复现旧 captured context；
- worker 只物化指定 target traces，不启用 Pulse search、harvest、archive、adaptive sharding、bound pruning；
- current-probe 仅用于 expected context 触发，不提供 certificate；
- 通过安全壳的 true-RC negative 可以作为 `HIGH_PRIORITY`，不安全或拖尾风险候选只能有限延迟进入 `DELAY_QUEUE`，不能永久丢弃；
- 所有 candidate 必须携带完整 `expected_context_hash`、`true_dual_hash`、`cut_hash`、`branch_hash`、`forbidden_signature_hash`、active / pool hashes；
- runbook 不启用 sharded Pulse certificate 或 official lower-bound effect。

因此 v38 仍是 Stage 3 数据采集到 Stage 4 opt-in A/B 的桥接物，不是 Stage 4 结论，也不是 Stage 5 加速结论。

## 下一步判据

执行该 runbook 必须是显式 opt-in。执行后先看四类证据：

1. 5/10 no-regression sentinel 仍为 `OPTIMAL`，objective 不劣化；
2. task20 candidate baseline / worker 是否到达同一 `expected_context_hash`，否则只能把实际到达 context 回流下一轮；
3. worker 是否真的改善 trajectory：RMP objective movement、dual / basis 稳定性、tail retry、wall time、node completion、accepted column ROI；
4. certificate audit 必须继续显示 worker/GAT 对 official bound 无影响；若要证明 OPTIMAL，仍要由 exact pricing 在当前 branch/cut/dual 下完成 no-negative closure。

Stage 5 的硬目标仍是 agreed 20-task benchmark matrix 在 200s 内稳定 `OPTIMAL`，并且 official dual bound / proof source 可审计。当前 v38 只准备了一个 task20 neighbor-ROI 对照批次，目标是缩小 blocker：确认 selected target families 能否让 trajectory 真实变好，以及 missed high-ROI 是否能通过 same-context target materialization 回流为有效训练样本。

