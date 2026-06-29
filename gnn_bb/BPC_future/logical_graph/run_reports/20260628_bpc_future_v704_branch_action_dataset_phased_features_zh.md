# V704 Branch Action Dataset Phased-Testing 特征接入

## 结论

V704 把 V703 新增的 solver 内 phased-testing 诊断字段接入 GAT branch action 数据集和 score-map 导出链路。

新增 context feature：

```text
phased_testing_stage_code
phased_testing_decision_code
phased_testing_elimination_reason_code
phased_testing_phase0_passed
phased_testing_phase1_lp_complete
phased_testing_phase2_heuristic_complete
```

这些字段让 branch GAT 能区分：

- cheap screen 过滤；
- score gate winner 保护；
- dynamic-K 未覆盖；
- Phase1 LP probe 完成/不完整；
- Phase2 heuristic probe 完成/不完整；
- 候选被测过但最终排序落后。

## 同步修改

已同步的链路：

1. `build_gat_branch_action_sanity_dataset.py`
   - context schema 增加 phased-testing code / complete flags；
   - fixed code map 保持训练特征可解释、稳定；
   - manifest 继续标记 `production_ready=false`。
2. `export_gat_branch_action_score_map.py`
   - score-map 导出端使用同一套 context feature schema 和 code map；
   - 避免训练与推理 context 维度不一致。
3. delta-row 构建脚本透传 RouteOpt/BKF probe 字段：
   - `build_journey_branch_forced_replay_delta_rows.py`
   - `build_journey_branch_full_replay_gap_delta_rows.py`
   - `build_gat_branch_action_v437_delta_rows.py`
   - `build_journey_paired_probe_delta_rows.py`

同时补齐透传：

```text
phase1_min_child_lp_gain
phase1_child_lp_gain_product
phase1_child_width_balance
phase1_wall_time
phase1_dynamic_k_probe_count
phase2_negative_child_count
phase2_negative_journey_count
phase2_best_reduced_cost
phase2_worst_negative_severity
phase2_wall_time
phase2_dynamic_k_probe_count
```

这修正了一个关键问题：之前 replay delta row 即使来自 `routeopt_bkf_staged` 日志，也可能没有把 Phase1/Phase2 probe 指标写入 `alternative_raw_row`，导致最终 GAT context feature 默认为 0。

## Exact-Safe 边界

V704 仍然只影响离线训练/导出特征：

- 不运行 BPC；
- 不运行 pricing；
- 不运行 RMP；
- 不生成 certificate；
- 不生成 official bound；
- 不改变 solver 默认行为；
- 不把学习输出作为剪枝依据。

## 测试

通过：

```text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/scripts/export_gat_branch_action_score_map.py \
  BPC_future/scripts/build_journey_branch_forced_replay_delta_rows.py \
  BPC_future/scripts/build_journey_branch_full_replay_gap_delta_rows.py \
  BPC_future/scripts/build_gat_branch_action_v437_delta_rows.py \
  BPC_future/scripts/build_journey_paired_probe_delta_rows.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_dataset

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_training \
  BPC_future.tests.test_gat_branch_action_checkpoint_ranking

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_journey_branch_forced_replay_delta_rows \
  BPC_future.tests.test_journey_branch_full_replay_gap_delta_rows \
  BPC_future.tests.test_journey_paired_probe_delta_rows
```

## 下一步

下一步应重新构建最近一批 RouteOpt/BKF replay delta rows 和 GAT branch action dataset，检查：

- `phased_testing_stage_code` 是否覆盖 phase1/phase2，而不是大量 0；
- `phase1_min_child_lp_gain` / `phase1_child_lp_gain_product` 是否不再全 0；
- `skipped_by_dynamic_k` 中是否存在后验强正例；
- hard negative 是否集中在 `phase2_heuristic/probed_incomplete` 或高 retry-risk context。

如果这些分布正常，再训练下一版 branch action model；如果仍然稀疏，优先扩 state-scoped replay，而不是继续扩大无结构 top-K。
