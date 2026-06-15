# GAT Cross-Family Sample 5/10 No-Regression Guard 报告

日期：2026-06-15

## 目标

验证 cross-family GAT 有效样本采集 runbook 在 5/10 小规模上不会改变当前主线求解结果。

本轮只运行 runbook 中的 5/10 baseline 与 capture 命令：

- 不启用 worker；
- 不启用 certificate 或 official lower-bound shortcut；
- capture 只增加日志采集；
- `max_workers=1`，避免并行内存风险。

## 输入

Runbook：

```text
BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/summary.json
```

覆盖 family / region：

```text
tasks_005:
  greedy-anchor: apollo + tranquillitatis
  random-wave: apollo + tranquillitatis
  sector-wave: apollo + tranquillitatis

tasks_010:
  greedy-anchor: apollo + tranquillitatis
  random-wave: apollo + tranquillitatis
  sector-wave: apollo + tranquillitatis
```

## 结果

```text
task005_baseline:
  instance_count = 6
  status_counts = {OPTIMAL: 6}

task005_capture:
  instance_count = 6
  status_counts = {OPTIMAL: 6}

task010_baseline:
  instance_count = 6
  status_counts = {OPTIMAL: 6}

task010_capture:
  instance_count = 6
  status_counts = {OPTIMAL: 6}
```

baseline vs capture 对照：

```text
task005 mismatch_count = 0
task010 mismatch_count = 0
compared_fields = status, primal_bound, dual_bound, gap
```

## 判断

5/10 no-regression guard 通过。

这只证明 cross-family capture-only 采样不会影响 5/10 official result；它不证明 GAT 可以上线，也不证明 20-task ROI 成立。

下一步可以在同一个 runbook 下继续执行 20-task baseline/capture 与离线 GAT+kNN/OOD 候选抽取，用于补 `greedy-anchor` / `random-wave` family 的 ROI target-intervention 样本。

