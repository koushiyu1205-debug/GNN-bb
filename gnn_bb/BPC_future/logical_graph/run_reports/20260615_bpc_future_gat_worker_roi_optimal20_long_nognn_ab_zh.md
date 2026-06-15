# GAT Worker ROI 已求得 OPTIMAL 20 实例 A/B 复查报告

日期：2026-06-15

## 目标

本轮选择一个历史上已经由 no-GNN baseline 求得 `OPTIMAL` 的真实 20 规模实例，测试当前 `v34_focal_hard frac0.5` GAT worker 是否能带来加速。

实例：

`BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json`

历史参考：

- CSV：`BPC_future/results/20260611_post360_tasks20_no_gnn_baseline_external_timeout_parallel.csv`
- 历史状态：`OPTIMAL`
- 历史 wall time：`1392.753867s`
- 历史 primal/dual：`548.335796 / 548.335796`
- 历史 pricing calls / exact pricing calls：`14 / 4`

## 本轮运行边界

本轮实际跑的是 runbook 生成的两组命令：

1. `mainline baseline + context capture`
2. `mainline baseline + context capture + GAT target-priority worker`

注意：该 runbook 保留主线 `journey_learning`，没有关闭旧 GAT/learning 路径。`runbook` 的外部 `--time-limit` 为 3600s，但当前 solver 在 cg=9 的 final pricing/proof 阶段返回 `TIME_LIMIT`，实际约 66s 结束。

GAT worker 仍是 opt-in、无证书效果：

```text
certificate_ready=false
official_bound_effect=false
negative_discard_allowed=false
safe_negative_action=HIGH_PRIORITY
unsafe_negative_action=DELAY_QUEUE
```

## 候选

当前最佳 no-new-data 变体：

`gat_worker_roi_knn_ood_audit_v34_focal_hard_20260615_frac_0p5`

与历史 OPTIMAL 20 实例交集里唯一 `HIGH_PRIORITY` 候选：

```text
name = tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13
expected_context_hash = 55a386bc49af1dda
target_sequence = [16, 4, 14, 11, 13]
score = 0.6094081401824951
source_roi_class = no_observed_roi
label_worker_roi_positive = 0
```

这个候选虽然被当前模型判为 `HIGH_PRIORITY`，但已有标签是 `0 / no_observed_roi`，本身就是一个疑似 false HIGH_PRIORITY 压力测试。

## 结果

| run | status | solving_time | primal | dual | rmp_solves | pricing_calls | exact_pricing_calls | columns |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | `TIME_LIMIT` | `65.932584` | `548.335796` |  | `9` | `13` | `4` | `560` |
| GAT worker | `TIME_LIMIT` | `65.908239` | `548.335796` |  | `9` | `13` | `4` | `560` |

修正后的 A/B 审计分类：

```text
result_roi_class = no_observed_roi
roi_class = target_not_reached
target_reachability_class = worker_context_not_reached
target_training_label_allowed = false
primal_improvement = 0.0
pricing_calls_delta = 0
exact_pricing_calls_delta = 0
official_bound_effect = false
certificate_effect = false
```

## 关键日志结论

worker 没有真正注入列：

```text
event = journey_sharded_pulse_hidden_negative_worker
pulse_worker_status = SKIPPED
pulse_worker_skip_reason = residual_target_context_mismatch
pulse_worker_returned_journeys = 0
pulse_worker_context_hash = b9b20654990e6234
expected_context_hash = 55a386bc49af1dda
```

reachability 审计：

```text
reachability_class_counts = {"worker_context_not_reached": 1}
reachable_target_intervention_count = 0
training_ready = false
```

也就是说，当前运行没有到达该候选采集时的 residual/RMP context。按 exact-safe 规则，target-priority worker 不能把旧 context 下的负列强行注入当前 true-dual / cuts / forbidden-signature context。

## 与历史 OPTIMAL 的差异

历史 no-GNN 轨迹：

```text
cg_iter 9  -> RMP objective 548.335796
cg_iter 10 -> RMP objective 548.335796
cg_iter 11 -> RMP objective 548.335796
final completion-bound pricing exhausted=true
duplicate-only certificate audit accepted
status=OPTIMAL
time=1392.069827s
```

当前轨迹：

```text
cg_iter 8 -> RMP objective 548.335796
cg_iter 9 -> RMP objective 548.335796
journey_exact_pricing_completion_bound_retry
journey_node_incomplete reason=time_limit
status=TIME_LIMIT
time≈66s
```

当前代码/配置路径没有复现 2026-06-11 的历史长证明轨迹。它更早进入 `weak_negative_journeys_filtered` / completion-bound retry，并以未证 `TIME_LIMIT` 返回。

## 判断

本轮没有观察到 20 规模加速，但这次不能判定为“GAT 模型本身无效”。

直接原因是：

1. 当前运行的 context 与候选采集 context 不匹配；
2. exact-safe guard 正确跳过 worker；
3. worker 对 RMP 轨迹没有任何实际干预；
4. baseline 与 worker 的 primal、pricing calls、exact calls、columns 完全一致；
5. 修正后的审计把该样本标记为 `target_not_reached`，不允许进入 ROI 训练标签。

更准确的结论是：

- 这是 `offline replay candidate` 的部署覆盖问题；
- 不是一次有效的 online GAT ROI 干预；
- 也不是可用于训练的负 ROI 样本；
- 当前模型指标本身仍未达生产线，`v34_focal_hard frac0.5` 的验证 precision/recall 还不足以默认启用。

## 下一步

短期不要继续把旧 context 下的固定 target 硬套到新轨迹。

下一步应改成：

```text
current-run candidate generation
  -> GAT/kNN/OOD online scoring
  -> HIGH_PRIORITY / DELAY_QUEUE scheduling
  -> same-run 20 A/B
```

只有当 worker 在当前 context 中实际触发，并且 `target_training_label_allowed=true`，这条 A/B 才能用来判断：

- 是训练不足；
- 是模型表达不够；
- 还是 GAT worker 真正没有 20-scale ROI。
