# GAT Target-Priority Bridge / ROI 小结

日期：2026-06-14

## 当前主线

GAT 没有被放弃。当前定位是：

- GAT：负责 embedding / trajectory impact / residual-family 表达；
- kNN/OOD：负责安全壳；
- true-RC negative 且通过安全壳：可进入 `HIGH_PRIORITY`；
- true-RC negative 但未通过安全壳：进入 `DELAY_QUEUE`；
- true-RC negative 不能永久丢弃；
- GAT/kNN/OOD、delay queue、Pulse worker 都不能参与 no-negative certificate 或 official lower bound。

## 本轮新增

### 1. GAT 决策到 worker target 的自动桥接

新增：

```text
BPC_future/scripts/build_gat_target_priority_candidates.py
```

作用：

1. 读取 GAT/kNN/OOD `decision_records.jsonl`；
2. 读取对应 `gat_validation_dataset/manifest.json`；
3. 用 manifest 里的 `context_hash/source_file` 精确回到 capture JSONL；
4. 从真实 returned negative journeys 中选择 best true-RC negative；
5. 抽取第一段 sortie 的 task sequence 与 arc-option sequence；
6. 输出可直接喂给 worker A/B runbook 的 `candidates.json`。

这个脚本只读离线日志，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

### 2. GAT target-priority worker A/B runbook

新增：

```text
BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py
```

作用：

- 生成 5/10 no-regression 命令，保留主线 GAT/learning，不启用新 worker；
- 生成 20-task no-learning baseline 与 target-priority worker A/B 命令；
- 使用 `shlex.join`，确保 `0->20:low_risk:2` 这类 arc-option 不会被 shell 当成重定向；
- 禁止任何 certificate / official-bound effect。

## 实跑证据

### 5/10 no-regression

主线 GAT/learning 保持开启，新 worker/gate 未启用：

| scale | instance | status | primal | dual | gap | wall |
|---:|---|---|---:|---:|---:|---:|
| 5 | Apollo sector-wave #1 | OPTIMAL | 284.084294 | 284.084294 | 0.0 | 2.276397s |
| 5 | Tranq sector-wave #1 | OPTIMAL | 179.982081 | 179.982081 | 0.0 | 2.173830s |
| 10 | Apollo sector-wave #1 | OPTIMAL | 456.756326 | 456.756326 | 0.0 | 5.153385s |
| 10 | Tranq sector-wave #1 | OPTIMAL | 330.363821 | 330.363821 | 0.0 | 3.551559s |

结论：5/10 主线不退化。

### 20-task 正 ROI 候选

从 20roi smoke 的 GAT validation 中自动抽出：

```text
context_hash = c488c428ee5822de
target_sequence = 20,17,16
target_arc_options =
  0->20:low_risk:2
  20->17:low_risk:2
  17->16:low_risk:2
  16->0:low_risk:2
best_true_reduced_cost = -14.8269665
```

该候选对应的实跑 A/B：

| profile | status | primal | dual_bound | rmp_solves | pricing_calls | exact_pricing_calls | columns |
|---|---|---:|---|---:|---:|---:|---:|
| no-learning baseline | TIME_LIMIT | 740.122399 | None | 12 | 16 | 6 | 257 |
| target-priority worker | TIME_LIMIT | 739.158736 | None | 13 | 16 | 7 | 259 |

结论：该候选有真实正 ROI，primal 改善 `0.963663`，但仍没有 exact certificate。

### 20-task 无 ROI 候选

从 sector-wave capture validation 中自动抽出的另一个 HIGH_PRIORITY 候选：

```text
context_hash = a3b5b5263e1cfe17
target_sequence = 14,5,8,18,12
best_true_reduced_cost = -9.747246
```

实跑结果：

```text
status = TIME_LIMIT
primal = 740.122399
dual_bound = None
columns = 257
```

它与 no-learning baseline 完全一致，说明：

- GAT/kNN/OOD 安全通过只说明候选值得尝试；
- 不能直接推导 worker ROI；
- 生产化必须要求跨候选、跨实例的稳定收益，而不是单个 HIGH_PRIORITY 决策。

## 当前判断

1. GAT 主线仍然有效，但角色必须是 trajectory-impact 表达，不是 pricing oracle；
2. kNN/OOD 是安全壳，不是证书来源；
3. 自动桥接已经能把 GAT HIGH_PRIORITY 决策转换为 worker target；
4. 已验证一个自动桥接候选有正 ROI，也验证一个 HIGH_PRIORITY 候选无 ROI；
5. 因此下一步重点不是默认启用，而是扩大 20-task audit-only / opt-in A/B，统计 ROI 稳定性。

## 生产化标准

必须同时满足：

1. 5/10 主线 no-regression 持续成立；
2. 20-task 多实例上 worker 触发后 wall time、primal、tail retry 或 exact-pricing call 有稳定改善；
3. 不出现 official result 变差；
4. worker 返回列必须全部 true-RC negative；
5. GAT/kNN/OOD 不能永久丢弃 negative；
6. 不能启用 certificate / official lower-bound effect；
7. 未通过 kNN/OOD 的负列只能 delay，不能 reject；
8. 生产默认仍关闭，直到多实例 A/B 证明 ROI。

## 验证

```text
test_gat_target_priority_candidates: OK
test_gat_target_priority_worker_ab_runbook: OK
py_compile: OK
git diff --check: OK
```

## 下一步

继续扩大 20-task target-priority A/B：

1. 对 Apollo20 #5 跑 baseline / worker；
2. 对 Tranq20 sector-wave 的 DELAY_QUEUE 候选只做 delay 记录，不启用 worker；
3. 汇总每个候选的 `worker_added_columns / primal_delta / exact_pricing_calls_delta / status`；
4. 只有多实例正 ROI 后，才考虑 hard-tail trigger；仍不进入 certificate gate。
