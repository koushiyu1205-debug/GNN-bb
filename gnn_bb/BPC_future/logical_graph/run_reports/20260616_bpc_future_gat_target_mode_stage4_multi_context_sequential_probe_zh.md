# 2026-06-16 BPC_future GAT Target Mode Stage 4 Multi-context Sequential Target-materialization 报告

## 结论

本轮实现并实测了 default-off 多 context target-materialization worker，用来表达：

```text
context ac056820151e9ad7 -> materialize [15,20]
context 7b430465c7ae76b3 -> materialize [1,9]
```

两个 target 都在当前 context 下由 `materialize_pulse_leaf_candidate()` 重新构造并用当前 true dual / cut 做 true-RC 验证；worker 仍不能 certificate，exact fallback 仍覆盖完整配置宇宙。

实测结果显示 sequential active-replacement 仍未通过 20-task ROI gate：

```text
stage4_multi_context_worker_functional = true
both_expected_contexts_hit = true
both_targets_true_rc_negative = true
sequential_active_replacement_roi_gate = failed
stage4_20_mutating_opt_in_ready = false
stage5_ready = false
```

核心原因：第二阶段 `[1,9]` 虽然也触发 active replacement，但没有减少 tail workload，反而把 RMP / pricing / exact 轮次继续推高。

## 修改文件

- `BPC_future/solver/journey_driver.py`
  - 新增 `journey_sharded_pulse_hidden_negative_worker_target_materialization_contexts`；
  - 该配置默认不存在，因此默认关闭；
  - 若旧的单 `journey_sharded_pulse_hidden_negative_worker_expected_context_hash` 存在，旧逻辑优先，保持兼容；
  - 若多 context 列表存在，则只有当前 context 命中列表时 worker 才允许执行；
  - 命中后将该 context 的 traces / journeys / target diagnostics 映射成旧式单 context config，再调用现有 target-materialization path。

- `BPC_future/tests/test_bpc_future.py`
  - 覆盖多 context guard 命中 / 错配；
  - 覆盖命中 context payload 后能实际物化对应 true-RC negative journey；
  - 确认 materialized worker result 仍不是 global certificate。

## 实验配置

候选来源：

```text
BPC_future/results/gat_active_replacement_target_candidates_active_only_tranq20_01_20260616/candidates.json
BPC_future/results/gat_active_replacement_target_candidates_stage2_after_15_20_tranq20_01_20260616/candidates.json
```

运行 artifact：

```text
BPC_future/results/gat_target_mode_stage4_sequential_target_materialization_20260616/
```

新增 multi-context payload：

```text
BPC_future/results/gat_target_mode_stage4_sequential_target_materialization_20260616/sequential_contexts.json
BPC_future/results/gat_target_mode_stage4_sequential_target_materialization_20260616/sequential_command.json
```

核心开关：

```text
journey_sharded_pulse_hidden_negative_worker_enabled=True
journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe
journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True
journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True
journey_sharded_pulse_hidden_negative_worker_target_materialization_contexts=[...]
```

仍保持：

```text
default_enabled = false
worker_certificate_effect = false
global_certificate_capable = false
final_judge_certificate_capable = false
```

## Worker 命中结果

日志确认两个 expected contexts 均命中：

| cg_iter | context | target | status | true_rc | returned |
| --- | --- | --- | --- | ---: | ---: |
| 7 | `ac056820151e9ad7` | `[15,20]` | `FOUND_NEGATIVE` | -3.417330 | 1 |
| 9 | `7b430465c7ae76b3` | `[1,9]` | `FOUND_NEGATIVE` | -1.397984 | 1 |

之后其他 context 均按预期 skip：

```text
skip_reason = residual_target_context_mismatch
```

certificate audit:

```text
worker_certificate_violations = 0
gat_target_mode_certificate_audit_all_checks_pass = true
gat_target_mode_certificate_audit_violation_count = 0
```

Audit artifact：

```text
BPC_future/results/gat_target_mode_stage4_sequential_target_materialization_20260616/certificate_audit/summary.json
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_multi_context_sequential_certificate_audit_zh.md
```

## 20-task A/B 对比

baseline 和 active-only 数值来自前序同实例报告 / artifact；本轮新增 sequential run。

| run | status | primal | time | rmp | pricing | exact | generated | evaluated | columns |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| shared baseline | `TIME_LIMIT` | 632.987632 | 53.477662 | 9 | 14 | 5 | 30378 | 48696 | 236 |
| active `[15,20]` | `TIME_LIMIT` | 632.987632 | 53.314711 | 11 | 17 | 6 | 34828 | 58047 | 271 |
| sequential `[15,20] -> [1,9]` | `TIME_LIMIT` | 632.987632 | 54.910337 | 14 | 22 | 8 | 41484 | 72055 | 262 |

sequential run 的 addition path：

```text
cg7  worker [15,20]: added=1 replacement=1 active_changed=1
cg9  worker [1,9]:  added=1 replacement=1 active_changed=1
cg11 exact:          added=31 new=26 replacement=5 active_changed=2
cg12 exact:          added=48 new=45 replacement=3 active_changed=0
cg13 exact:          added=2  new=2  replacement=0 active_changed=0
```

判定：

```text
multi_context_target_materialization_correctness = passed
sequential_active_replacement_roi = negative
single_or_two_step_active_replacement_label_quality = insufficient
```

## Exactness Boundary

本轮没有改变 proof 语义：

- target worker 只返回 true-RC negative candidate columns；
- worker result 显式 `global_certificate_capable=false`；
- worker no-column / skip 不会升级为 certificate；
- final certificate 仍必须由 exact pricing 在当前 branch/cut/dual 下对完整配置宇宙执行 no-negative closure；
- 所有新开关默认关闭，官方 benchmark config 未启用。

## 下一步

1. 不再把 “active replacement 单列/两步序列” 自动标成 positive ROI。
2. Stage 3 标签必须升级为 longer-horizon sequential trajectory utility，至少惩罚 RMP / pricing / exact 轮次和 generated/evaluated workload 上升。
3. 继续保留 multi-context target-materialization 作为 diagnostic intervention 工具，用于采集 causal rows，而不是作为 opt-in admission policy。
4. 下一轮优先做 Pareto-aware / coverage-aware training selection，避免只追高 ROI-CI 或只追 active-support movement。
