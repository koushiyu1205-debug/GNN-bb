# P0V5 QG2 V5 Trace-First GAT 状态

更新时间：2026-08-07

## 当前阶段

<!-- AUTO_PROGRESS_BEGIN -->
`TINYGAT_FORCE_ON_TERMINATED_NEGATIVE`

- 更新时间：`2026-08-07T12:28:46+08:00`；
- pipeline：STOPPED；用户确认现有证据已足以判定效果差；
- Q0 trace：`45/53`；scale30 `33/33`，scale50 `12/20`；
- Label GAT smoke：完成；
- Label GAT formal：完成；
- Q0/QG2 force-on：3个完整matched context均退化；另1个重尾context中Q0两次完成、TinyGAT三次超时；
- TinyGAT窄bucket screen：取消，不再继续花费求解时间；
- Context GAT与QD1/QB1新采集：未启动；
- MLP/Linear：未启动，且不会抢在 GAT fresh 之前运行；
- production/P0V4/P0V5 Exact control：未改动。
<!-- AUTO_PROGRESS_END -->

## TinyGAT force-on 实时结果

<!-- AUTO_FORCE_RESULTS_BEGIN -->
| scale | state | Q0 median (s) | TinyGAT median (s) | ratio | labels ratio | result |
|---:|---|---:|---:|---:|---:|---|
| 30 | `098f8374d1680b19` | 4.174 | 5.392 | 1.292 | 1.317 | harmful |
| 30 | `0e222da795d14da2` | 2.273 | 2.615 | 1.150 | 1.154 | harmful |
| 30 | `0761d9c2343be849` | 0.358 | 0.526 | 1.468 | 1.460 | harmful |
| 30 | `1ceab640c7be1580` | 284.853 (2 reps) | >300 (3 timeouts) | adverse censor | n/a | harmful |

scale30 当前 paired GM：`1.2969`；beneficial `0/3`。

结论：当前`QG2TinyGAT + 1e-3 bucket`不具备部署或继续扩展实验的依据。
<!-- AUTO_FORCE_RESULTS_END -->

## 原关键路径（已停止）

```text
Q0 trace gate
 -> 1 epoch Label GAT smoke
 -> formal Label GAT
 -> Q0/QG2 force-on
 -> QD1/QB1 matched outcomes
 -> Context GAT
 -> calibration + heldout fresh
 -> MLP/Linear controls only if GAT is positive
 -> development E2E
 -> scale5/10/20/30/50 full20
```

该路径停在Q0/QG2 force-on；后续节点均未启动。

Random 与 leaked-QO2 bucket arms 已从训练关键路径移除；它们仅保留为历史诊断。

## 已完成工程检查

- 新 Q0-only trace collector：已实现并通过语法检查；
- 新 GAT-only instance-balanced trainer wrapper：已实现并通过语法检查；
- 新增专项 + instance-balanced/controller 回归：`95 passed`；
- 全部 QG2 回归：`410 passed / 4 failed`；4项为历史 V2 freeze SHA 漂移，
  新 trace-first 链没有新增行为失败；
- 旧 Oracle execution freeze：131个文件 hash 校验通过；
- 新增文件 `git diff --check`：通过；
- Exact、dominance、bound、RC 和 certificate 路径：本轮未修改。

## 运行产物

开始后将维护：

- `trace_selection_freeze.json`；
- `trace_corpus/progress.json`；
- `trace_supervision_corpus.json`；
- `trace_training_view.json`；
- `label_gat_smoke/training_curve.jsonl`；
- `label_gat/training_curve.jsonl`；
- `label_gat/training_report.json`。
