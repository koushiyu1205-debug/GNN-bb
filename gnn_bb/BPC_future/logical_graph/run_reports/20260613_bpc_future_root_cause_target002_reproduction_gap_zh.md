# BPC_future 根因审计补充：target002 reproduction gap

日期：2026-06-13

## 目的

本轮只检查一个缺口：

> 为什么 `capture_target_002 / mt20_greedy_apollo_01 / cg3 / heuristic / active=16862add48072518 / obj=780.586496` 在当前 no-certificate-effect capture sweep 中仍然无法复现？

这不是新的优化实验，也不是 solver 主线修改。目标是把 target002 的未覆盖原因从“仍未覆盖”收紧成可复查的分叉证据。

## 结论

target002 不是在 cg3 才偏离，而是在 cg1 的 returned batch 就已经偏离。

旧 `phase10h` 轨迹 cg1 之后的 active hash 是：

```text
c6ea96127d7c5d7b -> 427b1308ea279e0c -> 16862add48072518
```

当前代码的 no-capture mirror 与 target capture 都变成：

```text
c6ea96127d7c5d7b -> 6907bf1e60739a97 -> a37fc1e4e8451f9b
```

因此当前 run 无法到达 target002 要求的 cg3 exact context。near match 不能当作 exact treatment。

## 对比证据

### 旧 phase10h r2

日志：

```text
BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl
```

cg1 returned / added task sets：

```text
[4,5,8]
[4,5,15]
[4,8,15]
[5,8,12]
[5,8,15]
[5,12,15]
[5,15,18]
[8,15,18]
```

summary 中 active trajectory：

```text
early_column_active_hash_before_sequence = ["c6ea96127d7c5d7b","427b1308ea279e0c","16862add48072518","22631672c7543445"]
early_column_active_hash_after_sequence  = ["427b1308ea279e0c","16862add48072518","22631672c7543445","8f346beb623b7737"]
```

这条轨迹能到达 target002 所需的：

```text
cg3 / heuristic / active_hash_before=16862add48072518 / rmp_objective_before=780.586496
```

### 当前 target capture r2

日志：

```text
BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl
```

cg1 returned / added task sets：

```text
[4,5,8]
[4,5,15]
[4,5,18]
[4,8,15]
[5,8,15]
[5,8,18]
[8,15,16]
[8,15,18]
```

summary 中 active trajectory：

```text
early_column_active_hash_before_sequence = ["c6ea96127d7c5d7b","6907bf1e60739a97","a37fc1e4e8451f9b"]
early_column_active_hash_after_sequence  = ["6907bf1e60739a97","a37fc1e4e8451f9b","3cc433cd72470337"]
```

当前到达的 Apollo cg3 context 是：

```text
active_hash_before = a37fc1e4e8451f9b
rmp_objective_before = 761.626550333
```

不是 target002 要求的：

```text
active_hash_before = 16862add48072518
rmp_objective_before = 780.586496
```

### 当前 no-capture mirror

为排除 `--counterfactual-replay-capture` 诊断开关本身造成副作用，补跑了单 repeat no-capture mirror：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_target002_current_code_no_capture_mirror_20260613 \
--instances mt20_greedy_apollo_01 \
--profiles experimental_early_new_task_set_quota_3_20_only \
--repeat-count 1 \
--time-limit 6 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--quiet
```

结果同当前 target capture 一致，cg1 returned / added task sets 为：

```text
[4,5,8]
[4,5,15]
[4,5,18]
[4,8,15]
[5,8,15]
[5,8,18]
[8,15,16]
[8,15,18]
```

active trajectory 为：

```text
c6ea96127d7c5d7b -> 6907bf1e60739a97 -> a37fc1e4e8451f9b
```

因此 capture logging 不是分叉原因。

## 解释

target002 的未覆盖原因是 trajectory drift：

1. 旧 phase10h 的 cg1 returned batch 与当前代码返回 batch 不同；
2. cg1 returned batch 不同会改变 RMP active pool hash；
3. active pool hash 改变后，cg2/cg3 的 true dual、pool、candidate universe 和 returned batch 都随之改变；
4. 所以当前 run 到达的是 Apollo near match，而不是 target002 的 exact context；
5. near match 不具备同一 RMP pool / true dual / cuts / effective fleet / returned payload，因此不能作为 exact counterfactual treatment。

这不是 target002 “没有高 impact batch”的证据，也不是当前 capture 机制错误的证据。它说明旧 target002 是一个对早期 returned-batch composition 极敏感的 trajectory 样本。

## 对根因判断的影响

这一步加强了当前根因判断：

> 20-task hard-tail 的关键不只是有没有负列，也不只是返回多少列，而是 early returned batch 的具体 task-set / sequence / signature / timing 会把 RMP active trajectory 推向不同分支。当前缺少 addition-before、context-aware、低开销、可泛化的 selector，所以同一 profile 在代码/选择语义轻微漂移后就无法复现旧 target context。

因此：

- target001/003 的 replay-ready exact captures 仍然证明 high-impact batch 存在；
- target002 未覆盖仍是重要缺口；
- 当前不能把 target002 near match 计入 exact replay calibration；
- 当前也不能把 existing replay 证据升级成 production selector；
- `production_direction_proven=false` 仍然成立。

## 结论

target002 当前未覆盖的直接原因已经明确：当前代码在 `mt20_greedy_apollo_01 / experimental_early_new_task_set_quota_3_20_only` 的 cg1 returned batch 与旧 phase10h 不一致，导致 active trajectory 从第一轮加列后就分叉。

这进一步说明下一步优化方向不能是简单提高 return limit、扩大 worker budget 或继续增加 probe，而必须先解决 returned-batch selector 的前置可泛化问题。
