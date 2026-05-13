# Vehicle-Schedule Pricing 测试说明

生成时间：2026-05-13 12:00:00 CST +0800

目标是验证 `branchpricecut/` 的数学一致性优先于性能优化。

## 已落地测试项

1. Reduced cost consistency：
   - Phase-I；
   - Phase-II；
   - partitioning；
   - covering；
   - vehicle lower-bound cut enabled。

2. Phase-I / Phase-II 切换：
   - Phase-I objective 到 0；
   - 重新 solve Phase-II；
   - 使用 Phase-II dual pricing。

3. Layer 1：
   - separate 分支过滤 route；
   - portfolio 至少包含 low-cbar、per-task、route-size、time-flexible、micro、branch-relevant、historical bucket。

4. Layer 2：
   - subset dominance；
   - empty label 不支配非空 label；
   - beam pruning 触发时 `exhausted=false`。

5. Tiny enumeration：
   - 小实例枚举全部 feasible schedules；
   - full master LP objective 与 CG objective 对齐。

6. Covering post-processing：
   - duplicate task removal；
   - shortcut rebuild；
   - exact schedule feasibility check；
   - 每个任务最终恰好出现一次。

7. Branching coverage：
   - `same(i,j)` 接受同时覆盖或同时不覆盖；
   - `separate(i,j)` 拒绝同时覆盖；
   - 单 column 上“不覆盖 i/j”的 schedule 会同时允许进入两个子节点，这是 RF column filtering 的正常行为。

8. ng-DSSR Layer 3：
   - very_small 上 ng-DSSR CG LP 与 full enumeration master LP 对齐；
   - negative non-elementary relaxed schedule 会触发 DSSR memory growth；
   - elementary negative schedule 会作为真实 column 返回；
   - relaxed exhaustive no-negative 可以 certificate 且不调用 full-memory fallback；
   - label/queue/time/memory limit 触发时不能 certificate；
   - dominance key 区分当前 sortie task set 和 same-component branch state；
   - same/separate branching 在 candidate 与 certificate 路径都执行。

## 测试方法映射

`tests/test_branchpricecut_vehicle_schedule.py` 当前包含 17 个 unittest 方法：

1. `test_01_reduced_cost_consistency_existing_columns`
2. `test_02_phase_i_to_phase_ii_dual_transition`
3. `test_03_vehicle_lower_bound_dual_sign_matches_solver_reduced_cost`
4. `test_04_layer1_separate_filtering_rejects_joint_route`
5. `test_05_layer1_portfolio_includes_required_route_buckets`
6. `test_06_layer2_subset_dominance_uses_branch_state`
7. `test_07_layer2_beam_pruning_failure_triggers_layer3`
8. `test_08_partitioning_default_and_covering_postprocess`
9. `test_09_tiny_full_enumeration_master_matches_cg_lp`
10. `test_10_branching_coverage_classifies_child_columns`
11. `test_11_ng_dssr_tree_matches_full_master_on_tiny_instance`
12. `test_12_ng_dssr_memory_growth_on_negative_non_elementary_schedule`
13. `test_13_ng_dssr_returns_elementary_negative_schedule`
14. `test_14_ng_dssr_relaxed_certificate_without_full_memory`
15. `test_15_ng_dssr_limits_do_not_certificate`
16. `test_16_ng_dssr_dominance_key_keeps_sortie_and_branch_state`
17. `test_17_ng_dssr_respects_same_and_separate_branching`

## 明确不按原文逐字实现的测试项

- `branching coverage` 原文要求 column 集合 `intersection empty`。当前测试按完整解空间语义检查：同时不覆盖分支对的 column 可被两个子节点共享。
- reduced-cost consistency 原文签名是 `check_schedule_reduced_cost_consistency(phase, num_samples=20)`。当前测试调用的是 `check_schedule_reduced_cost_consistency(solution, tolerance=...)`，并检查全部 active RMP columns。

## 运行

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_branchpricecut_vehicle_schedule
```

## 2026-05-13 21:43 CST 验证

```bash
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_branchpricecut_vehicle_schedule
```

结果：

```text
Ran 17 tests
OK
```
