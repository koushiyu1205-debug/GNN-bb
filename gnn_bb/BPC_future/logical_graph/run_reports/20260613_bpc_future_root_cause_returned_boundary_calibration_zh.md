# BPC_future 根因审计补充：returned-boundary calibration

日期：2026-06-13

## 目标

上一轮已经新增两个只读诊断字段：

- `diagnostic_returned_boundary_candidate_samples`
- `diagnostic_truncated_boundary_candidate_samples`

本轮用它们做一个极窄 calibration：

**在 Apollo20 上直接观察 returned cut 边界：哪些 candidate 被返回，哪些 candidate 因 return limit 被截断。**

本轮不启用 Pulse worker，不启用 certificate，不改 production 默认配置。  
本轮不是优化 A/B 结论，只是验证根因链条中的 returned-cut 边界是否能被直接观测。

## 运行

### 第一次尝试：dp state cap = 1

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/root_cause_returned_boundary_apollo20_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline experimental_early_new_task_set_quota_3_20_only \
  --repeat-count 3 \
  --time-limit 8.0 \
  --pricing-time-limit 0.2 \
  --pricing-max-dp-states 1 \
  --max-cg-iterations 8 \
  --quiet
```

结果：

- cg1 即 `profile_dp_incomplete`；
- `profile_selected_candidate_input_count = 0`；
- `diagnostic_returned_boundary_candidate_samples = []`；
- `diagnostic_truncated_boundary_candidate_samples = []`。

结论：

state cap 太低时，候选还没生成，无法观测 returned cut。  
这说明 returned-boundary calibration 必须先让 profile-DP 产生候选，否则诊断字段为空不是“没有截断”，而是“没有进入候选层”。

### 第二次尝试：dp state cap = 1000

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/root_cause_returned_boundary_apollo20_dp1000_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline experimental_early_new_task_set_quota_3_20_only \
  --repeat-count 3 \
  --time-limit 8.0 \
  --pricing-time-limit 0.2 \
  --pricing-max-dp-states 1000 \
  --max-cg-iterations 8 \
  --quiet
```

结果目录：

- `BPC_future/results/root_cause_returned_boundary_apollo20_dp1000_20260613/summary.csv`
- `BPC_future/results/root_cause_returned_boundary_apollo20_dp1000_20260613/logs/*.jsonl`

## 结果摘要

### Baseline

三次 repeat 相同：

| repeat | primal | cg additions | final active fractional sum |
|---:|---:|---:|---:|
| 0 | 921.640296 | 3 | 5.5 |
| 1 | 921.640296 | 3 | 5.5 |
| 2 | 921.640296 | 3 | 5.5 |

baseline 每轮只加 1 条：

| cg | added task-set | returned boundary | first truncated examples |
|---:|---|---|---|
| 1 | `[5,8,15]` | rank0 `[5,8,15]`, rough `-139.913748` | rank1 `[4,5,8]`, rough `-137.150710`; rank2 `[5,8,18]`, rough `-136.660461`; rank3 `[4,5,15]`, rough `-136.347326` |
| 2 | `[5,12,18]` | rank0 `[5,12,18]`, rough `-128.547499` | rank1 `[4,5,12]`, rough `-127.163214`; rank2 `[4,12,18]`, rough `-126.250004`; rank3 `[4,12,17]`, rough `-124.735118` |
| 3 | `[4,8,12]` | rank0 `[4,8,12]`, rough `-125.928982` | rank1 `[12,16,17]`, rough `-123.681417`; rank2 `[8,12,17]`, rough `-122.913897`; rank3 `[4,12,17]`, rough `-121.087285` |

直接观察：

- baseline 不是没有后续 candidate；
- 每轮都有多个强 negative candidates 排在 rank1+；
- 这些 rank1+ 没有 returned，因此不会进入 pool。

### Early quota return8

三次 repeat 相同：

| repeat | primal | cg additions | final active fractional sum |
|---:|---:|---:|---:|
| 0 | 793.914380 | 3 | 5.666667 |
| 1 | 793.914380 | 3 | 5.666667 |
| 2 | 793.914380 | 3 | 5.666667 |

cg1：

```text
input = 32
scanned = 8
materialized = 8
returned = 8
truncated = 24
```

returned boundary：

```text
rank0  rough=-139.913748  tasks=(5, 8, 15)
rank1  rough=-137.150710  tasks=(4, 5, 8)
rank2  rough=-136.660461  tasks=(5, 8, 18)
rank3  rough=-136.347326  tasks=(4, 5, 15)
rank4  rough=-136.011232  tasks=(4, 8, 15)
rank5  rough=-134.743366  tasks=(4, 5, 18)
rank6  rough=-132.930824  tasks=(8, 15, 16)
rank7  rough=-132.886574  tasks=(8, 15, 18)
```

first truncated：

```text
rank8   rough=-132.876349  tasks=(5, 15, 16)
rank9   rough=-132.854609  tasks=(5, 15, 18)
rank10  rough=-132.373685  tasks=(5, 8, 16)
rank11  rough=-130.315874  tasks=(15, 16, 18)
rank12  rough=-130.166318  tasks=(5, 16, 18)
rank13  rough=-129.981311  tasks=(8, 16, 18)
rank14  rough=-129.932369  tasks=(4, 8, 18)
rank15  rough=-129.918502  tasks=(5, 8, 17)
```

cg2 同样：

```text
input = 32
scanned = 8
materialized = 8
returned = 8
truncated = 24
```

returned boundary：

```text
rank0  rough=-123.681417  tasks=(12, 16, 17)
rank1  rough=-121.654710  tasks=(4, 12, 17)
rank2  rough=-74.761131   tasks=(12, 14, 16)
rank3  rough=-74.197467   tasks=(12, 14, 17)
rank4  rough=-73.864202   tasks=(4, 12, 14)
rank5  rough=-72.262031   tasks=(14, 16, 17)
rank6  rough=-71.648997   tasks=(11, 16, 17)
rank7  rough=-70.814616   tasks=(11, 12, 17)
```

cg3：

```text
input = 5
scanned = 5
materialized = 5
returned = 5
truncated = 0
```

## 直接证据

这轮补上了之前缺失的直接边界证据：

1. baseline 每轮只返回 rank0，rank1+ strong negative candidates 被截断；
2. early quota return8 把 baseline 会截断的 rank1-rank7 直接带进 returned batch；
3. 这批额外 returned columns 全部走正常 `journey_column_addition` path；
4. Apollo20 该 dp1000 calibration 中，primal 从 baseline `921.640296` 降到 `793.914380`；
5. 改善不是因为单个 rank0 `[5,8,15]`，因为 baseline 和 return8 都返回了 `[5,8,15]`；
6. 改善更像是 rank1-rank7 的 batch effect：`[4,5,8]`、`[5,8,18]`、`[4,5,15]`、`[4,8,15]` 等额外 candidate 改变了后续 RMP trajectory。

## 不能过度解释的地方

这轮不能被写成 production 优化成功：

1. 这是 Apollo20 单实例、dp1000、early quota 的 calibration，不是完整 5/10/20 gate；
2. 旧 Phase 10H 已经证明同类 return8 / return12 在不同 20-task hard cases 上方向相反；
3. final active fractional sum 反而从 baseline `5.5` 变为 return8 `5.666667`，说明 final fractional pressure 仍不是可靠优化指标；
4. 所有 addition 仍是 `changed_inactive_only`，改善不是 immediate active_changed，而是后续 RMP trajectory；
5. state cap 从 1 提到 1000 本身会改变候选域，因此不能与旧 r0/r2 完全等同。

## 当前根因更新

当前根因链条更完整：

1. 低 state cap 时，profile-DP 卡在候选生成前，returned-boundary 无法观测；
2. 候选生成足够后，baseline returned cut 确实会截掉大量强 negative candidates；
3. 扩大 returned cut 能把这些 candidates 带进池子，并可在 Apollo20 单点改善；
4. 但跨日志证据显示扩大 returned cut 在其他 20-task context 可能变差；
5. 因此根因不是“returned 太少”这么简单，而是“缺少能选择有益 returned batch 的 candidate/signature/timing 级 selector”。

一句话：

**这轮证明了 returned cut 边界是真实存在且可观测的机制；但也再次证明，仅扩大 returned cut 不是最终优化方向。**

## 下一步

如果继续推进，应做 calibration-only selector feature audit：

1. 对 returned 与 truncated candidates 提取 addition 前可见特征：
   - rank；
   - rough/true RC；
   - task-set；
   - profile start；
   - sequence/signature/timing；
   - relation to current active top samples；
   - new/replacement/support-changing class；
2. 离线追踪这些 candidate 后续是否进入 active basis / zero-fractional episode / incumbent update；
3. 只有当这些前置信号能稳定区分 improved/worsened，才允许做 opt-in selector A/B；
4. 在此之前，不应默认 return8/return12，不应扩大 Pulse worker，也不应打开 official certificate gate。

