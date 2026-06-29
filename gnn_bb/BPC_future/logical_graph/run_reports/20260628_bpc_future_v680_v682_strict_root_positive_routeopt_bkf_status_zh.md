# V680-V682 Strict Full-Replay Positive and RouteOpt/BKF Status

日期：2026-06-28

## 结论摘要

本轮把 V677 的 child-probe positive proxy 升级成了一条严格 full replay 正例。

核心结果：

- instance：`BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json`
- baseline root pair：`[2, 10]`
- alternative root pair：`[3, 10]`
- baseline：`OPTIMAL`, wall `345.182173s`, objective `641.659225`
- alternative：`OPTIMAL`, wall `50.186441s`, objective `641.659225`
- wall-time gain：`294.995732s`
- branch count：`15 -> 1`
- node count：`31 -> 3`
- pricing calls：`160 -> 29`
- exact pricing calls：`110 -> 17`
- completion-bound/final-judge retry：`31 -> 3`

这是一条真正的 strict full-replay branch counterfactual positive：两边都证明最优、目标值一致、alternative 明显更快。

## 产物

### V681 delta rows

- output：`BPC_future/results/journey_branch_counterfactual_delta_v681_v680_seed61411_root3_10_strict_full_replay_20260628/`
- report：`BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_branch_counterfactual_delta_v681_v680_seed61411_root3_10_strict_full_replay_zh.md`

机器字段：

```text
row_count = 1
label_type_counts = {"strong_positive": 1}
status_pair_counts = {"OPTIMAL->OPTIMAL": 1}
strict_full_replay_positive_count = 1
counterfactual_training_count = 1
production_ready = false
official_bound_effect = false
certificate_effect = false
```

注意：V681 只读既有 `results.csv` 和 JSONL，不运行 BPC/pricing/RMP，不产生 official bound 或 certificate。

### V682 dataset

- output：`BPC_future/data/gat_branch_action_sanity/v682_v679_plus_v681_strict_full_replay_20260628/`
- report：`BPC_future/logical_graph/run_reports/20260628_bpc_future_gat_branch_action_v682_v679_plus_v681_strict_full_replay_dataset_zh.md`

相对 V679：

| metric | V679 | V682 |
|---|---:|---:|
| raw rows | 304 | 305 |
| samples | 209 | 210 |
| walltime_gain_positive | 54 | 55 |
| aux_only_weak_positive | 13 | 13 |
| not_walltime_gain | 142 | 142 |
| tail_improved | 51 | 52 |

新增样本被归入 `walltime_gain_target_wall_crossing`，不是 proxy，也不是 weak-only。

### V682 training

- metrics：`BPC_future/results/gat_branch_action_v682_seed29_strict_full_replay_20260628/summary.json`
- checkpoint：`BPC_future/data/gat_branch_action_sanity/v682_v679_plus_v681_strict_full_replay_20260628/gat_branch_action_v682_seed29.pt`
- report：`BPC_future/logical_graph/run_reports/20260628_bpc_future_gat_branch_action_v682_seed29_strict_full_replay_train_zh.md`

与 V679 seed29 对比：

| metric | V679 | V682 |
|---|---:|---:|
| sample_count | 209 | 210 |
| walltime positives | 54 | 55 |
| best epoch | 12 | 12 |
| best validation total loss | 87.043339 | 92.819651 |
| validation precision | 0.263158 | 0.300000 |
| validation recall | 0.357143 | 0.400000 |
| validation F1 | 0.303030 | 0.342857 |

解释：新增强正例改善了 validation branch-priority 分类指标，但 validation total loss 变高，说明单条 strong positive 还不足以稳定 wall-time/proof-cost 回归头。V682 仍是 sanity/offline artifact，不是 production-ready checkpoint。

## 代码改动

`BPC_future/scripts/build_journey_branch_full_replay_gap_delta_rows.py` 现在支持两类标签：

1. both-OPTIMAL 且 objective match：生成 `strong_positive` / `regression` / `full_replay_neutral`。
2. right-censored：继续生成 weak gap/fathom auxiliary rows。

新增字段包括：

- `both_optimal`
- `optimal_objective_match`
- `objective_tolerance`
- `right_censored_counterfactual`
- `usable_for_counterfactual_training`
- `labels.y_counterfactual_wall_improved`
- `min_wall_improvement`
- `strict_full_replay_positive_count`
- `counterfactual_training_count`

新增测试：

- `test_both_optimal_wall_gain_becomes_strict_positive`

验证命令：

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_journey_branch_full_replay_gap_delta_rows \
  BPC_future.tests.test_gat_branch_action_sanity_dataset \
  BPC_future.tests.test_journey_branch_candidate_replay_runbook \
  BPC_future.tests.test_journey_paired_probe_delta_rows \
  BPC_future.tests.test_gat_branch_score_proofrisk_overlay \
  BPC_future.tests.test_gat_branch_action_checkpoint_ranking
```

结果：

```text
Ran 29 tests in 0.118s
OK
```

## 对 RouteOpt/BKF 主线的解释

这条 V680/V681 正例说明：branch pair selection 确实能把同一个 20-scale 实例从 `345s OPTIMAL` 缩到 `50s OPTIMAL`，而且不是靠改变 certificate 规则，也不是靠牺牲 exactness。

但它同时说明不能只做“全局 pair 记忆”：

- `[3,10]` 是 seed61411 当前 root state 的好 pair，不是全局永远好 pair。
- 它减少的是 branch tree、pricing calls、exact pricing calls 和 retry 数，属于 proof-cost 结构改善。
- 它没有提供新的 official bound；最终仍由 exact pricing closure 证明最优。

所以 RouteOpt/BKF 风格下一步应继续推进：

1. `routeopt_bkf_staged` 从离线 runbook 继续强化为正式 branch testing controller。
2. 候选评分加入双 child 均衡收益：
   - `min(child_lb_gain)`
   - `child_gain_product`
   - `child_width_balance`
   - `completion_bound_retry_delta`
   - `gap_improvement`
   - `time_to_certificate`
3. strict full replay 正例继续优先采集，但只对 child-probe / gap-fathom / retry-risk 多指标同时好的候选做 full replay。
4. score map 必须 state-scoped：绑定 `branch_state_key`、depth、parent constraints、support/fractional pattern 和 child width/retry risk。
5. retry gate 继续分类控制；减少无效 final-judge worker 化，但不能把 uncertified no-column 升级为 certificate。
6. 对 `best dual` 不动的 hard case，branch score 只能减 proof cost，仍需要 pricing-compatible cuts / formulation / incumbent heuristic 并行推进。

## 当前未达成项

本轮不是全量验收。

仍未达成：

- random-TW 20-scale `60/60 OPTIMAL within 600s`
- 20-scale 全部实例 `<=200s OPTIMAL`
- production-ready branch action checkpoint
- solver 内正式 phased branch testing controller

当前完成的是：把一条 RouteOpt/BKF staged probe 发现的 positive proxy 升级成严格 full-replay 训练正例，并验证它能进入 GAT branch action 数据集和训练流程。
