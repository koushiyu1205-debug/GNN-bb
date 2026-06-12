# Sharded Pulse Phase 7L Audit-only ROI Calibration 报告

日期：2026-06-12

## 目标

本轮只做 Phase 7L：`Audit-only ROI Calibration`。

目标不是继续写复杂 proof 算法，而是把 Phase 7K 已有的调度参数放进可重复的小矩阵校准脚本，观察：

1. refinement 是否值得做；
2. ROI gate 是否该停；
3. Pulse audit / worker 是否该启动；
4. 后续是否具备进入 proof-closed resume 的条件。

不做：

- official certificate gate；
- production default enable；
- hidden worker 默认启用；
- 20/100 A/B；
- parallel；
- persistent resume；
- cut / subset-row prefix bound。

## 实现摘要

新增脚本：

```text
BPC_future/scripts/run_sharded_pulse_roi_calibration.py
```

默认实例矩阵：

- `very_small`
- `apollo5`
- `tranq5`
- `apollo10`
- `tranq10_09`

默认 profiles：

- `baseline`
- `audit_no_refine`
- `audit_refine`
- `audit_refine_roi_low`
- `audit_refine_roi_mid`
- `audit_refine_roi_high`

ROI 三档：

| 档位 | prune_rate_floor | min_expanded | min_time |
|---|---:|---:|---:|
| low | 0.001 | 10 | 0.0 |
| mid | 0.01 | 25 | 0.01 |
| high | 0.05 | 50 | 0.02 |

输出文件：

```text
summary.json
summary.csv
logs/<instance>__<profile>.jsonl
```

脚本会记录：

- official status / dual bound / pricing state / best rc；
- official 是否相对 baseline 不变；
- audit status / comparison type / disagreement severity；
- shard total / certified / incomplete / negative / refined；
- low ROI shards；
- bound/archive/time-window/energy/return/capacity pruning counters；
- negative pool / harvested count；
- critical disagreement flag；
- per-run log path。

脚本对齐 main runner，加载 Moon Trek real instance 后会执行 `apply_fleet_bound_override()`，避免固定 fleet cap 造成初始 journey RMP infeasible。

若 audit profile 没有任何 audit event，summary 会显式写：

```text
pulse_audit_skipped=True
pulse_audit_skip_reason=legacy_not_called
```

避免校准表出现不可解释空白。

## 验证命令

脚本语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
-m py_compile BPC_future/scripts/run_sharded_pulse_roi_calibration.py
```

very_small smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7l_roi_calibration_smoke_20260612 \
--instances very_small \
--profiles baseline audit_refine_roi_mid \
--time-limit 2.0 \
--audit-time-limit 0.05 \
--pricing-time-limit 0.05 \
--max-cg-iterations 1 \
--quiet
```

Apollo5 smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7l_roi_calibration_apollo5_smoke_20260612 \
--instances apollo5 \
--profiles baseline audit_refine_roi_mid \
--time-limit 3.0 \
--audit-time-limit 0.08 \
--pricing-time-limit 0.05 \
--max-cg-iterations 1 \
--quiet
```

5 实例 x 6 profile 短矩阵：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7l_roi_calibration_20260612 \
--time-limit 3.0 \
--audit-time-limit 0.08 \
--pricing-time-limit 0.05 \
--max-cg-iterations 1 \
--quiet
```

输出：

```text
BPC_future/results/sharded_pulse_phase7l_roi_calibration_20260612/summary.json
BPC_future/results/sharded_pulse_phase7l_roi_calibration_20260612/summary.csv
```

## 短矩阵结果

短矩阵共 30 rows。

硬约束检查：

| 检查项 | 结果 |
|---|---:|
| official result changed vs baseline | 0 |
| critical disagreement | 0 |
| `legacy_certified_pulse_negative` | 0 |
| `legacy_negative_pulse_certified` | 0 |

所有 audit profiles 在当前短 cap 下都保持 official result 不变。

观察到的 audit 状态：

- `very_small`：`legacy_incomplete_pulse_negative`，warning；
- Apollo5：`legacy_incomplete_pulse_negative`，warning；
- Tranquillitatis5：`legacy_incomplete_pulse_negative`，warning；
- Apollo10：`legacy_incomplete_pulse_negative`，warning；
- Tranquillitatis10_09：`legacy_incomplete_pulse_negative`，warning。

典型信号：

- `pulse_audit_time_window_pruned > 0`；
- Apollo / Tranquillitatis real instances 上 `transition_return_pruned > 0`；
- `pulse_audit_harvested_count > 0`；
- `pulse_audit_shards_negative > 0`；
- `pulse_audit_low_roi_shards = 0`。

## 解释

这轮 calibration smoke 说明：

1. audit-only 链路是安全的：official status / dual / pricing state 未被改写；
2. 没有 critical disagreement；
3. 当前短 cap 下 Pulse audit 主要表现为 hidden-negative signal；
4. ROI gate 在这组短矩阵里没有成为主导因素，因为 Pulse 在 low-ROI 判定前已经 found negative；
5. 因此这轮不能直接给出 `prune_rate_floor` 的生产阈值。

## 当前判断

这轮结果更支持：

```text
Phase 7M-alt：strict hidden-negative worker retry
```

而不是立刻做：

```text
Phase 7M：proof-closed resume
```

理由：

- 真实小矩阵上 audit 经常 found negative；
- harvesting 有信号；
- 但 low-ROI / no-negative proof-hard 场景还没有被充分覆盖；
- resume 需要稳定 proof unit，而当前结果主要是 negative discovery，不是 proof progress。

如果继续 hidden worker 路线，仍必须保持严格 gate：

- `certificate_candidate=True`
- remaining time sufficient；
- instance size >= min tasks；
- previous audit had negative / high prune ROI / hard-tail incomplete；
- no certificate effect。

## 后续建议

优先级 1：

- 用更宽的 audit-only 矩阵补 no-negative / proof-hard / forced-incomplete 样本，让 low-ROI gate 真正触发；
- 或把当前 found-negative audit signal 接入 strict hard-tail worker retry 的小 smoke，但不得默认启用 worker。

优先级 2：

- 若后续 low-ROI calibration 稳定，再做 proof-closed child shard resume；
- resume 前仍需保证 frontier snapshot 非 proof，只有 proof-closed child shard record 能参与 certificate。

暂不建议：

- official certificate gate；
- default hidden worker；
- 20/100 A/B；
- parallel；
- cut/subset-row prefix bound。
