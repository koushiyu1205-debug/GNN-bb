# 20260627 V471-V473 Branch Action 状态报告

## 结论

本轮继续推进 branch score 主线，但没有达到 `20-scale 60/60 OPTIMAL within 600s`。

当前仍以 V468 为最好 full-60 结果：

| version | OPTIMAL | TIME_LIMIT | EXTERNAL_TIME_LIMIT | capped mean | <=200s OPT |
|---|---:|---:|---:|---:|---:|
| baseline 20260624 | 26/60 | 4 | 30 | 381.77s | 20 |
| V464 | 31/60 | 3 | 26 | 353.77s | 22 |
| V468 | 33/60 | 3 | 24 | 348.26s | 22 |

V471-V473 的主要收获不是新增 OPTIMAL，而是确认：

- strict replay overlay 仍然可靠，V468 已知正例在 V472 smoke 中复现。
- child-probe proxy 的 corrected-bound gain 不能单独预测 full-solve 闭环。
- V471 裸模型虽然验证指标较 V466 改善，但仍会给未闭环分支很高分，不能直接全量启用。
- V473 只能作为更保守的 suppress score map，不是新 best。

## V469 Child-Probe

输入：V468 剩余 27 个非最优实例的 root 候选。

产物：

- runbook：`BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/runbook.json`
- child-probe 结果：`BPC_future/results/journey_branch_candidate_replay_runbook_v469_v468_nonopt_root_child_probe_layered_20260627/v469_child_probe_results.csv`
- audit：`BPC_future/results/journey_branch_impact_audit_v469_v468_nonopt_root_child_probe_20260627/`
- proxy ranking：`BPC_future/results/journey_branch_child_probe_proxy_ranking_v469_v468_nonopt_root_20260627/`

结果：

- 160 条 child-probe，`130 TIME_LIMIT + 30 EXTERNAL_TIME_LIMIT`。
- audit 标记为 diagnostic/right-censored，`production_ready=false`。
- proxy ranking 只适合作为采样导航，不能作为训练正例或 score gate 依据。

## V470 Strict Full Replay

从 V469 proxy 中选 10 条高 proxy / 高 corrected-gain root pair 做 600s full replay。

产物：

- runbook：`BPC_future/results/journey_branch_proxy_full_replay_runbook_v470_v469_proxy_top12_20260627/summary.json`
- replay results：`BPC_future/results/journey_branch_proxy_full_replay_runbook_v470_v469_proxy_top12_20260627/v470_proxy_full_replay_results.csv`
- delta：`BPC_future/results/journey_branch_counterfactual_delta_v470_v469_proxy_top10_full600_20260627/`

结果：

- 10/10 都是 `EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT`。
- delta label：`changed_timeout_no_effect_hard_negative = 10`。

解释：

这些 pair 的 child-probe 局部 bound 或 proof-cost 信号看起来较好，但完整 600s replay 没有闭环。说明当前 proof tail 的关键不是“某个 child 局部水位更好”，而是整棵分支子树是否能快速完成 certificate。

## V471 Training

V470 hard negatives 合入 V466 数据集后生成 V471：

- dataset：`BPC_future/data/gat_branch_action_sanity/v471_v466_plus_v470_hard_negative_20260627/`
- checkpoint：`BPC_future/data/gat_branch_action_sanity/v471_v466_plus_v470_hard_negative_20260627/gat_branch_action_v471_weighted.pt`
- metrics：`BPC_future/results/gat_branch_action_v471_weighted_walltime_20260627/summary.json`

数据集变化：

- sample_count：188 -> 198
- wall-time positive：51 -> 51
- not-walltime-gain：125 -> 135

训练指标：

- V471 validation precision/recall/F1：`0.50 / 0.20 / 0.286`
- V466 validation precision/recall/F1：`0.077 / 0.111 / 0.091`

判断：

V471 比 V466 明显好，但验证正例只有 5 个，recall 仍低，并且后续 smoke 证明高分误报存在。因此它不能裸用，只能作为诊断候选生成器。

## V472 Smoke

V472 = V471 score map + 历史 strict overlay + V470 suppress。

12-instance smoke：

- 7 个已知可解/正收益实例全部 OPTIMAL。
- 5 个 V468 未解 / V470 相关实例全部 EXTERNAL。
- 已知正例没有被破坏：
  - apollo greedy seed61000：332.14s
  - apollo greedy seed61614：343.83s
  - apollo random seed61408：473.40s
  - tranq greedy seed61001：57.69s
  - tranq greedy seed61103：452.24s
  - tranq random seed61411：341.53s
  - tranq sector seed61923：405.80s

6-instance high-score non-opt smoke：

- 6/6 全部 EXTERNAL。
- 这 6 个都是 V471 高分且 gate=ok 的实际 changed root pair：
  - sector/tranq seed61104 `[2,18]`
  - sector/tranq seed61718 `[4,7]`
  - sector/tranq seed61206 `[6,10]`
  - sector/tranq seed61513 `[4,20]`
  - sector/apollo seed61204 `[5,12]`
  - sector/apollo seed61000 `[5,12]`

判断：

V472 保住了 V468 的已知收益，但没有新增闭环；裸模型高分在未解实例上误报严重，因此不应跑全量作为候选 best。

## V473 Overlay

把 V472 smoke 中 6 个 changed-nonoptimal 高分误报转成 suppress evidence：

- analysis：`BPC_future/results/gat_branch_action_v471_weighted_walltime_20260627/analysis_v473_v472_smoke_overlay_input.json`
- score map：`BPC_future/results/gat_branch_action_v471_weighted_walltime_20260627/score_map_v473_conservative_overlay_with_smoke_suppress_on_branchonly60/journey_branch_score_rows.json`

overlay 统计：

- positive_overlay_keys：12
- negative_overlay_keys：93
- touched rows：`boost_positive=10`，`suppress_negative=76`

V473 的定位：

它是更保守的 score map，主要用途是防止 V471 的高分误触发；它不是新的加速 best。

## 当前判断

本轮否定了两个假设：

1. `child_probe corrected gain 高 -> full replay 更容易 OPTIMAL`
2. `V471 裸模型高分 -> 可以扩大 full-60 score gate`

真正有效的仍然是 strict full replay 证明过的 root pair overlay。但正例寻找效率仍低，V470 和 V472 high-score smoke 都没有新增正例。

## 下一步

要继续向 60/60 推进，不能再只扩大 root 候选 full replay。更合理的方向是：

1. 分析 V468 剩余 27 个未解实例的失败类型，区分是 root pair 不足、深层分支不足、incumbent 不足、final-probe/CB tail，还是需要 cuts/formulation。
2. 对深层 branch event 建立 replay，而不是只看 root pair。
3. 标签从单个 pair 的局部 child-probe 改成完整 branch path / child ordering 的 wall-time delta。
4. 对 V471 高分误报构造 hard negative，训练目标增加 calibration/OOD 或 score-source confidence，而不是继续降低 gate。

## 验证

通过单测：

```text
python -m unittest \
  BPC_future.tests.test_journey_branch_forced_replay_delta_rows \
  BPC_future.tests.test_gat_branch_action_sanity_dataset \
  BPC_future.tests.test_gat_branch_action_sanity_training \
  BPC_future.tests.test_gat_branch_score_proofrisk_overlay \
  BPC_future.tests.test_journey_branch_proxy_full_replay_runbook
```

结果：`Ran 12 tests ... OK`。
