# Counterfactual Replay Readiness 审计报告

日期：2026-06-13

## 目标

本轮不运行 solver、不接 driver、不改 production pricing path。

目标是检查首批 `counterfactual replay` 候选是否已经具备直接执行 no-certificate-effect controlled replay 的信息量。这个检查服务根因目标：避免把 observational candidate manifest 误当成已经能证明优化方向的因果 replay 证据。

## 输入

候选 manifest：

```text
BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/summary.json
```

stage rows：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

candidate rows：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/candidate_rows.csv
```

脚本：

```text
BPC_future/scripts/audit_counterfactual_replay_readiness.py
```

输出：

```text
BPC_future/results/root_cause_counterfactual_replay_readiness_20260613/summary.json
```

## 审计口径

一个 replay candidate 若要成为 exact controlled replay 输入，至少需要：

- source log path；
- repeat index；
- full journey signatures；
- sortie boundaries；
- concrete arc option ids；
- start times；
- true RC per journey；
- RMP pool snapshot；
- true dual snapshot；
- cut snapshot。

这些字段的作用是保证 replay 注入的是同一个 exact context 下的同一批 feasible `JourneyColumn`，且 replay 不产生 certificate / official lower-bound side effect。

## 结果

```text
recommended_candidate_count = 3
descriptor_count = 6
ready_candidate_count = 0
descriptors_with_truncated_sampling = 1
descriptors_with_candidate_row_start_times = 6
descriptors_with_ambiguous_candidate_row_start_times = 0
```

检查：

```text
recommended_candidates_present = true
no_candidate_ready_for_exact_replay = true
manifest_lacks_required_replay_fields = true
candidate_rows_are_not_exact_context_snapshots = true
needs_new_no_certificate_effect_replay_capture = true
```

## 候选明细

### replay_candidate_001

exact context：

```text
mt20_greedy_tranq_01 | cg_iter=2 | heuristic | active=5c6420f757a39d2d | rmp=761.814403
```

stage exact-context rows：

```text
35
```

描述符状态：

- improved descriptor：`returned_count=1`，sequence entries `1/1`，可从 candidate rows 找到 start time；
- worsened descriptor：`returned_count=1`，sequence entries `1/1`，可从 candidate rows 找到 start time；
- 仍不可 replay，因为缺 full journey signature、concrete arc option ids、sortie boundaries、source log path / repeat 唯一定位、true-RC 和 RMP/dual/cut snapshot。

### replay_candidate_003

exact context：

```text
mt20_greedy_apollo_01 | cg_iter=3 | heuristic | active=16862add48072518 | rmp=780.586496
```

stage exact-context rows：

```text
2
```

描述符状态：

- improved descriptor：`returned_count=8`，sequence entries `8/8`，可从 candidate rows 找到 start times；
- worsened descriptor：`returned_count=8`，sequence entries `8/8`，可从 candidate rows 找到 start times；
- 仍不可 replay，因为 start time 只是 candidate-row 层面的回源结果，不是完整 JourneyColumn snapshot；还缺 arc option ids、sortie boundaries、true dual/cuts/RMP snapshot。

### replay_candidate_004

exact context：

```text
tranq20_01 | cg_iter=1 | heuristic | active=aa2b834c9d43f2a6 | rmp=838.004841
```

stage exact-context rows：

```text
51
```

描述符状态：

- improved descriptor：`returned_count=12`，但 `returned_sequences` / `returned_arc_families` 只有 `8` 条采样，缺 `4` 条；
- worsened descriptor：`returned_count=1`，sequence entries `1/1`；
- 这个候选适合作为 high-coverage stress context，但当前日志采样已截断 improved batch，不能 exact replay。

## 对根因判断的影响

这轮没有改变根因结论，反而进一步收紧了下一步边界：

1. 现有 observational manifest 可以定位值得 replay 的 exact contexts；
2. 但它还不是 exact replay 输入；
3. 当前 logs / CSV 足以证明“run-level 标签不是 batch-level 因果标签”，不足以直接证明哪个 batch 应该上线；
4. 下一步若要继续，必须先实现 no-certificate-effect replay capture / harness，捕获完整 JourneyColumn batch、RMP pool、true dual、cuts 和 source run identity；
5. 在 controlled replay 证明前，不能把任何 selector / worker / return policy 作为 production 优化方向。

## 结论

首批 3 个 replay 候选仍然有价值，但它们只能作为 controlled replay 的目标 context，不是可直接执行的 exact replay payload。

当前根因目标仍未完成：根因解释已经有证据，但“保证 exactness、5/10 不退化、20 大幅加速”的优化方向还没有被 controlled replay 证明。
