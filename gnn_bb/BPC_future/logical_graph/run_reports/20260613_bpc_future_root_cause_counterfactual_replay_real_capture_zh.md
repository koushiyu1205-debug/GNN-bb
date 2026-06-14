# BPC_future 根因补充：真实 20-task exact-context counterfactual replay

日期：2026-06-13

## 目标

本轮只验证一个问题：

> 在真实 20-task hard-tail context 中，Pulse worker 返回的 JourneyColumn batch 是否能在同一 RMP pool / true dual / cuts / effective fleet context 下产生可观测的局部 RMP impact？

这不是 production selector，也不是 official certificate gate。整个 replay 是 diagnostic-only / no-certificate-effect：

- 不改变默认 benchmark；
- 不更新 official lower bound；
- 不把 Pulse incomplete / no-column / duplicate-only 当证书；
- 只在已捕获的 exact context 上重放 RMP treatment。

## 输入

捕获实例：

```text
mt20_greedy_apollo_01
profile = strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority
```

capture log：

```text
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/logs/mt20_greedy_apollo_01__strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority__capture_t10_v2.jsonl
```

捕获的 replay context：

- `pricing_kind=sharded_pulse_hidden_negative_worker`
- `pricing_state=FOUND_NEGATIVE`
- `context_hash=080a188d2484ee3e`
- `task_count=20`
- `vehicle_count=17`
- `returned_journey_count=4`
- `pool_journey_payload_count=164`
- `returned_batch_complete=True`
- `pool_snapshot_complete=True`

## Audit / Manifest / Replay 结果

Audit：

```text
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/audit_v2/summary.json
```

结果：

- `all_checks_pass=true`
- `event_count=1`
- `captured_journey_count=4`
- `pool_journey_payload_count=164`
- context hash 非空；
- returned / pool journeys 都带完整 trip payload；
- no-certificate-effect checks 通过。

Manifest：

```text
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_manifest_v2/summary.json
```

结果：

- `all_checks_pass=true`
- `case_count=1`
- `ready_case_count=1`
- `candidate_count=4`
- `treatment_count=8`
- candidate summary：
  - `new_task_set_count=4`
  - `duplicate_signature_count=0`
  - `active_support_changing_count=0`
  - `weak_replacement_or_duplicate_count=0`

Replay：

```text
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_result_v2/summary.json
```

结果：

- `all_checks_pass=true`
- control RMP：
  - `status=OPTIMAL`
  - `objective=1061.554044`
  - `journey_count=164`
  - `selected_count=12`
- full returned batch treatment：
  - `objective=924.43786`
  - `objective_delta_vs_control=-137.116184`
  - `dual_l1_delta_vs_control=137.461444`
- `changed_treatment_count=7`
- `improving_treatment_count=7`
- `best_objective_delta=-137.116184`

最佳单列 treatment：

```text
candidate = journey_0000
task_set = [4,5,8]
sequence = [[8,5,4]]
true_reduced_cost = -137.15071
objective_delta_vs_control = -137.116184
```

其他单列 treatment 也都改善了局部 RMP：

- `[4,8,18]` / `[[8,4,18]]`：delta `-129.128532`
- `[5,8]` / `[[8,5]]`：delta `-70.080792`
- `[4,8]` / `[[8,4]]`：delta `-66.958244`

## 对根因判断的影响

这个结果比之前 observational logs 更强，因为它在同一 exact context 下重放了 treatment：

- 同一 RMP pool；
- 同一 true dual / cut payload；
- 同一 effective vehicle count；
- 完整 returned JourneyColumn payload；
- replay 明确是 no-certificate-effect。

它证明：

1. 20-task 中并不是所有 worker-returned negative 都无效；
2. 至少存在一个真实 captured Pulse returned batch 能显著改善局部 RMP objective；
3. “缺少优化方向”的问题进一步收紧为：还没有 addition-before selector 能稳定识别这类高-impact batch，同时保护 5/10 不退化。

它没有证明：

1. full BPC wall time 会下降；
2. OPTIMAL count 会增加；
3. gap 会稳定降低；
4. selector 能跨 instance / profile / repeat 泛化；
5. 5/10 no-regression 已经解决；
6. Pulse 可以打开 official certificate gate。

## 当前结论

当前根因判断应从：

> 可能需要 exact-context replay 才能验证 returned batch 是否有用。

更新为：

> exact-context replay 已经证明真实 20-task 中存在有局部 RMP impact 的 returned batch；但 production 失败的根因仍是缺少 addition-before、context-aware、可泛化、低开销的 returned-batch selector。

因此下一步不应继续扩大 worker budget 或打开 certificate gate，而应扩大 diagnostic-only exact-context replay 样本，专门学习哪些 returned batch 在加入前可预测为 high-impact。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_counterfactual_replay_capture.py \
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/logs/mt20_greedy_apollo_01__strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority__capture_t10_v2.jsonl \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/audit_v2

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/build_counterfactual_replay_manifest.py \
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/logs/mt20_greedy_apollo_01__strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority__capture_t10_v2.jsonl \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_manifest_v2

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_counterfactual_replay_from_manifest.py \
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_manifest_v2/replay_cases.json \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_result_v2
```

根因 evidence ledger 已纳入该检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/verify_root_cause_evidence.py \
--output-dir BPC_future/results/root_cause_evidence_ledger_20260613
```

结果：

```text
all_checks_pass=true
check_real_capture_replay_has_local_rmp_impact=true
```
