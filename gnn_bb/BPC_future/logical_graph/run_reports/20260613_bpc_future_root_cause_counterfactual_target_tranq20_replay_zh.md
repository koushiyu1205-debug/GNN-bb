# BPC_future 根因审计补充：tranq20 target exact-context replay

日期：2026-06-13

## 目的

上一轮 target source-profile scan 命中了 `capture_target_003` 的 exact context，但 returned/captured batch 为 `0`，不能作为 replay treatment。

本轮只验证一个假设：

> 空 batch 是否由过低的 `pricing_max_dp_states=1` 诊断扫参造成，而不是该 context 本身没有负列？

本轮仍是 diagnostic-only / no-certificate-effect，不改变 production solver path，不产生 official bound。

## 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613 \
--instances tranq20_01 \
--profiles experimental_early_new_task_set_quota_3_return12_20_only experimental_l1_zero_dual_stabilization_20_only \
--time-limit 8.0 \
--max-cg-iterations 2 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--counterfactual-replay-capture \
--counterfactual-replay-capture-max-journeys 0 \
--counterfactual-replay-capture-pool-max-journeys 0 \
--quiet
```

随后运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_counterfactual_replay_capture.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/audit \
BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/logs

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/build_counterfactual_replay_manifest.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/replay_manifest \
BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/logs

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_counterfactual_replay_from_manifest.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/replay_result \
BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/replay_manifest/replay_cases.json

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_replay_impact_dataset.py \
--manifest BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/replay_manifest/replay_cases.json \
--replay-result BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/replay_result/replay_results.json \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/impact
```

## Capture 结果

```text
event_count = 4
captured_journey_count = 26
returned_journey_count = 26
complete_event_count = 4
truncated_event_count = 0
all_checks_pass = true
```

其中 `capture_target_003` 的 exact context 被两个 replay-ready events 覆盖：

```text
tranq20_01 / cg_iter=1 / pricing_kind=heuristic
rmp_objective_before = 838.0048415
active_hash_before = aa2b834c9d43f2a6
returned_journey_count = 12  # early-new-task-set profile
returned_journey_count = 1   # l1-zero profile
```

全局 target coverage 更新后：

```text
capture_event_count = 38
target_with_near_match_count = 3
target_with_exact_capture_count = 1
uncovered_target_count = 2
all_checks_pass = true
```

这证明上一轮 `capture_target_003` 空批次主要来自 `pricing_max_dp_states=1` 的 capture sweep 过窄；该 exact context 不是无负列。

## Replay / Impact 结果

Manifest：

```text
case_count = 4
ready_case_count = 4
candidate_count = 26
treatment_count = 41
all_checks_pass = true
```

Replay：

```text
case_count = 4
ready_case_count = 4
improving_treatment_count = 37
changed_treatment_count = 19
all_checks_pass = true
```

Impact dataset：

```text
candidate_row_count = 26
high_impact_candidate_count = 26
noop_candidate_count = 0
full_batch_count = 4
full_batch_improved_count = 4
best_objective_delta = -70.009099
all_checks_pass = true
```

## 当前解释

这轮新增了第二个真实 20-task exact-context replay 样本族：`tranq20_01`。

它支持两点：

1. 20 规模确实存在能显著改变 local RMP objective 的 returned batches；
2. 之前 target capture 为空不是根本数学原因，而是诊断 capture 上限过低。

但它仍不能证明 production 优化方向已经确定：

1. 这只是 local RMP replay，不是完整 BPC wall-time speedup；
2. `capture_target_001` 和 `capture_target_002` 仍未覆盖；
3. addition-before selector 仍未被证明能泛化；
4. 5/10 no-regression 仍依赖严格 gate，不能默认启用 worker；
5. no-op counterexample 仍然成立，负 RC 本身不是充分条件。

## 结论

根因判断被进一步收紧：

> 20 规模不是找不到有用列，而是缺少能在加入前、低开销、跨 context 泛化地区分 high-impact batch 与 no-op/replacement batch 的 selector。

下一步应继续补 `capture_target_001/002` 的非空 exact-context replay，扩大 high-impact/no-op 校准集，再重新审计 selector；仍不应放开 production worker 或 official certificate gate。
