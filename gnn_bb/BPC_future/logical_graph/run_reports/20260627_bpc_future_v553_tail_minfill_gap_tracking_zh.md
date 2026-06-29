# 20260627 V553：Tail Min-Fill Smoke 与非最优 Gap 记录

## Gap 记录口径

BPC_future 是最小化问题。非最优实例的 gap 只有在同时具备以下两项时才能计算：

- `UB`：当前最好整数可行解，也就是 incumbent / primal bound；
- `LB`：合法下界，也就是 exact-safe dual bound / exact child lower bound / valid corrected node lower bound。

相对 gap 计算为：

```text
gap = max(0, (UB - LB) / max(1, abs(UB)))
```

不能把未闭合 column generation 的当前 `z_RMP` 当作合法 `LB`。在最小化列生成中，restricted master objective 通常是受限列空间上的 LP 值；如果 pricing 尚未完成，它不是全局 LP 下界，也不能用于官方 gap。

## 代码改动

已更新：

- `BPC_future/scripts/run_bpc_future.py`
- `BPC_future/scripts/run_bpc_future_external_timeout_batch.py`
- `BPC_future/tests/test_run_bpc_future_external_timeout_batch.py`

后续结果 CSV 会增加：

- `gap_available`
- `gap_source`
- `gap_unavailable_reason`
- `best_primal_bound`
- `best_dual_bound`

原有字段 `primal_bound / dual_bound / gap` 仍保留。只有 exact-safe 可算时才填 `gap`；不可算时保留空，并用 `gap_unavailable_reason` 说明原因。

`run_bpc_future_external_timeout_batch.py` 在续跑已有 CSV 时，也会尝试根据对应 JSONL 日志回填旧行的这些 gap 元数据。

当前支持的典型原因：

- `no_feasible_incumbent`
- `no_exact_dual_bound`
- `no_exact_dual_bound_external_timeout_no_finish`
- `no_exact_dual_bound_invalid_corrected_bound`
- `global_tree_bound_reconstruction_unavailable`

这保证后续非最优实例不会只有空白字段，而是明确区分“没有 incumbent”和“有 incumbent 但没有合法 LB”。

验证：

```text
python -m py_compile BPC_future/scripts/run_bpc_future.py BPC_future/scripts/run_bpc_future_external_timeout_batch.py
python -m unittest BPC_future.tests.test_run_bpc_future_external_timeout_batch
```

结果：通过。

## V553 Tail Min-Fill Smoke3

目的：在 V545 branch-score 配置上，额外打开 depth<=4 的 tail low-min-fill opt-in：

```text
journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True
journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4
journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4
journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True
```

输入实例来自 V549/V545 completion-tail profile 中的 D 类 tail 候选。

结果：

| instance | V545 | V553 | 结论 |
|---|---:|---:|---|
| `apollo15_20km_random-wave_randomtw_tasks020_02_seed61102` | `TIME_LIMIT 239.46s` | `TIME_LIMIT 259.77s` | 退化约 20.30s |
| `apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818` | `TIME_LIMIT 540.26s` | `EXTERNAL_TIME_LIMIT 600.03s` | 硬退化 |
| `apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205` | `TIME_LIMIT 340.77s` | `TIME_LIMIT 439.23s` | 退化约 98.45s |

V553 没有产生 OPTIMAL，也没有 wall-time gain。

## V553 Completion-Tail 审计

产物：

- `BPC_future/results/20260627_v553_v545_tail_minfill_depth4_smoke3_tasks20/results.csv`
- `BPC_future/results/journey_completion_tail_profile_v553_tailminfill_smoke3_20260627/summary.json`
- `BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_completion_tail_profile_v553_tailminfill_smoke3_zh.md`

关键审计：

- tail min-fill applied：11
- completion retry classes：
  - `completion_bound_found_negative`: 1
  - `completion_bound_time_limit_no_column_uncertified`: 2
- total generated sequences：5,950,587
- total evaluated timed trips：7,533,252
- total profile generation time：459.898549s
- incomplete tail count：2

解释：

低 min-fill 确实生效了，也确实让 final judge 在部分位置更早返回真实负列；但这些列没有让完整求解更快闭环，反而增加了后续 CG / final-probe 往复。对这批样本，`min_fill=4` 相比 canonical `min_fill=10` 是 hard negative。

## 当前判断

1. 非最优 gap 后续必须记录，但只记录 exact-safe gap。
2. 有 incumbent 但没有合法 LB 时，不能用 `z_RMP` 硬算 gap。
3. V553 证明“深层 tail low-min-fill”不是当前可扩大主线。
4. 剩余优化仍应回到：
   - branch policy 的深层 state-aware 正例；
   - completion-bound proof cost / profile generation cost 降低；
   - final judge harvesting 质量，而不是单纯降低返回门槛。

## 对后续实验的要求

所有后续 random-TW 5/10/20 运行都应保留新增 gap 元数据字段。报告中统计非最优实例时应至少列出：

- `status`
- `best_primal_bound`
- `best_dual_bound`
- `gap`
- `gap_available`
- `gap_unavailable_reason`

如果 `gap_available=false`，该行不能参与官方 gap 均值，但应参与“gap 不可用原因”统计。
