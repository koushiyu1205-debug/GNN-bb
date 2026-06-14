# Counterfactual Replay Payload Quality Audit

日期：2026-06-13

## 目标

本轮不改主线 solver，只检查已有 `mt20_greedy_apollo_01` capture logs 是否能扩展 exact-context replay 样本。

之前综合报告只使用了：

```text
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/logs/mt20_greedy_apollo_01__strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority__capture_t10_v2.jsonl
```

该 v2 capture 已证明一个真实 20-task returned batch 有局部 RMP impact。

这次审计把同目录下所有 capture logs 一起处理，检查是否还有额外 ready replay case。

## 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_counterfactual_replay_capture.py \
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/logs \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/audit_all_logs
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/build_counterfactual_replay_manifest.py \
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/logs \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_manifest_all_logs
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_counterfactual_replay_from_manifest.py \
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_manifest_all_logs/replay_cases.json \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_result_all_logs
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_replay_impact_dataset.py \
--manifest BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_manifest_all_logs/replay_cases.json \
--replay-result BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_result_all_logs/replay_results.json \
--output-dir BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/real_capture_mt20_apollo_all_logs
```

## 结果

### Capture audit

```text
event_count = 2
complete_event_count = 2
returned_journey_count = 7
captured_journey_count = 7
pool_journey_count = 328
all_checks_pass = true
```

两个 event 都是 `cg_iter=1`、同一个 context hash：

```text
context_hash = 080a188d2484ee3e
```

### Manifest

```text
case_count = 2
ready_case_count = 1
candidate_count = 7
treatment_count = 15
all_checks_pass = true
```

`capture_t10.jsonl` 因缺少 `vehicle_count` 被标记为不可 replay：

```text
capture_case_0001:
  ready_for_rmp_replay = false
  issues = [missing_vehicle_count_for_replay]

capture_case_0002:
  ready_for_rmp_replay = true
  vehicle_count = 17
```

manifest ready 只表示 exact-context replay 的必要输入可用，不等于任何 treatment 有优化价值。

### Replay

```text
case_count = 2
ready_case_count = 1
all_checks_pass = false
control_rmp_solved = true
no_replay_issues = false
```

逐 case：

```text
capture_case_0001:
  source = capture_t10.jsonl
  vehicle_count = None
  ready_for_replay = false
  issues = [missing_vehicle_count_for_replay]
  best_objective_delta = null

capture_case_0002:
  source = capture_t10_v2.jsonl
  vehicle_count = 17
  control.status = OPTIMAL
  control.objective = 1061.554044
  best_objective_delta = -137.116184
```

因此，runner 不再尝试为 bad payload 构造 control RMP；只有 v2 capture 进入 impact calibration。

### Impact dataset guard

本轮同步收紧了：

```text
BPC_future/scripts/analyze_counterfactual_replay_impact_dataset.py
```

新增检查：

```text
all_replay_controls_solved
all_single_candidates_have_finite_delta
unknown_candidate_count
control_unsolved_case_count
```

全日志 impact dataset 现在正确标记为：

```text
all_checks_pass = false
candidate_row_count = 7
single_candidate_with_replay_count = 4
high_impact_candidate_count = 4
unknown_candidate_count = 0
control_solved_case_count = 1
control_unsolved_case_count = 1
```

这避免把 `capture_t10.jsonl` 的 non-ready rows 误纳入 selector calibration。clean v2 dataset 仍为：

```text
all_checks_pass = true
candidate_row_count = 4
high_impact_candidate_count = 4
unknown_candidate_count = 0
control_unsolved_case_count = 0
best_objective_delta = -137.116184
```

## 根因判断影响

这次审计没有改变主根因，但收紧了证据边界：

1. `mt20_greedy_apollo_01` 的 high-impact replay 仍然成立；
2. 早期 capture payload 缺少 `vehicle_count`，现在会在 manifest 阶段被拒绝为 non-ready；
3. exact-context replay 样本扩展不能只看 capture schema ready，还必须要求 manifest ready、runner ready 和 control RMP `OPTIMAL`；
4. 当前可用 high-impact exact-context 样本仍主要是 v2 单 case；
5. production selector 仍未证明。

## 当前结论

Replay 工具链已经足够发现 payload 质量问题。

下一步如果继续扩展样本，必须要求：

- `vehicle_count` 非空；
- control RMP `OPTIMAL`；
- single candidate objective delta finite；
- replay no-certificate-effect；
- full pool snapshot 未截断；
- returned batch 未截断。

否则即使 capture event schema 通过，也不能进入 returned-batch selector calibration。
