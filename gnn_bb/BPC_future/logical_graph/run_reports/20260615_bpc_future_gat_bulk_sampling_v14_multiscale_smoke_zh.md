# GAT Bulk Sampling v14 Multiscale Smoke 报告

日期：2026-06-15

## 目标

v13 已经把 same-run 正样本推到 97 条，但总样本只有 128 条，非改善样本只有 31 条。v14 的目标是把 capture-only 批量采样扩展到 `30/50/100`，验证更大规模是否能补充总样本和 DELAY / non-improving 标签。

## 实现摘要

`build_gat_bulk_sampling_runbook.py` 已扩展：

- 新增 `--bulk-scales`；
- 支持 `30/50/100` capture-only waves；
- 仍保留 5/10 baseline/capture sentinel；
- 仍强制 `max_workers=1`；
- 不启用 worker；
- 不启用 certificate；
- 不产生 official lower bound；
- GAT/kNN/OOD 仍只作为 offline audit 和 delay scheduler。

由于当前没有独立的 30/50/100 证明配置，v14 对 `30/50/100` 暂时复用 `moon_trek_20_smoke.yaml` 作为 capture-only 模板，实际实例由 `--instances` 覆盖。该设置只用于采样，不代表生产证明配置。

## v14 Runbook

生成位置：

- `BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/summary.json`
- `BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_bulk_sampling_runbook_v14_multiscale_zh.md`

规划：

```text
existing_row_count = 128
existing_positive_count = 97
target_total_samples = 300
target_positive_samples = 100
bulk_scales = [30, 50, 100]
selected_new_instance_count = 25
selected_wave_count = 13
estimated_total_after = 303
estimated_positive_after = 135
```

按规模选择：

```text
30-task random-wave Apollo = 5
30-task random-wave Tranquillitatis = 4
50-task random-wave Apollo = 4
50-task random-wave Tranquillitatis = 4
100-task random-wave Apollo = 4
100-task random-wave Tranquillitatis = 4
```

## Smoke 执行

只执行第一个 multiscale bulk wave：

```text
task030_050_bulk_capture_wave01
max_workers = 1
```

结果：

| instance | status | wall |
|---|---|---:|
| tasks_030 random-wave Apollo ordinal 1 | OPTIMAL | 58.51s |
| tasks_050 random-wave Apollo ordinal 1 | EXTERNAL_TIME_LIMIT | 200.03s |

命令返回码为 0，说明 batch runner 能处理 30/50 capture-only 组合，且限时实例仍保留日志用于标签构建。

## Smoke 标签产出

从第一个 wave 构建 same-run rows：

```text
row_count = 26
positive_objective_improvement_count = 16
non_improving_objective_count = 10
objective_positive_rate = 0.615385
objective_non_improving_rate = 0.384615
source_file_count = 2
all_checks_pass = true
```

对比 v13：

- v13 非改善率约 24.2%；
- v14 首个 30/50 smoke 非改善率约 38.5%。

这说明扩到更大规模确实更可能补到 DELAY / non-improving 样本，方向正确。

## 当前边界

- 只执行了 v14 的第一个 wave；
- 还没有跑 100-task capture；
- 还没有把 v13 + v14 合并成最终 250-300 same-run 训练集；
- 还没有做 v14 GAT 训练；
- 没有启用任何生产 worker；
- 没有证书或 official bound 影响。

## 下一步

1. 继续执行 v14 剩余 waves，但仍保持 `max_workers=1`；
2. 每完成若干 waves 重新构建 rows，优先观察 non-improving / DELAY 是否增加；
3. 如果 100-task 单实例太慢或日志收益低，应限制 100-task wave 数量；
4. 合并 v13 与 v14 rows，目标是 same-run 总样本达到 250-300，正样本保持 80-100 以上，且非改善样本显著增加；
5. 训练新的 audit-only GAT；
6. 只对 HIGH/DELAY top-K 做 target worker A/B，不默认启用。
