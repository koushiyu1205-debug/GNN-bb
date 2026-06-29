# 20260628 V671-V679：RouteOpt/BKF Staged Probe 与 Score-Floor 修正状态

## 结论

本轮把 RouteOpt/BKF 的启发落到 branch-pair replay 数据采集上，核心收获是：

1. 纯结构 BKF staged 采样不够。V671 在 hard contexts 上生成了 12 个 paired group / 24 个 alternatives，但 V673 全部是 `neutral_proxy`，没有可训练正例或 hard negative。
2. 原因不是 child-probe 预算太小，而是这些 hard contexts 的 external branch score 基本接近 0，V671 实际靠 fractionality / width / balance 在挑候选，不是真正的 GAT score 命中。
3. 因此实现了 score-floor fail-closed：`staged_bkf_min_branch_score` 与 `staged_bkf_allow_filtered_fallback=False`。同时修复 paired runbook 的 baseline-only 污染，只有存在可运行 alternative 时才生成 selected baseline。
4. V675 在同一批输入上只保留 3 个高置信 paired group / 6 条命令，运行后 V677 产生 1 个 `positive_proxy`、2 个 `neutral_proxy`。
5. V678 将这 1 条 `paired_probe_positive_proxy` 转成右删失 proxy row；V679 数据集把它作为 auxiliary weak-positive / proof-cost 样本接入，不作为 full-run wall-time 正例。

这还没有达到 production score-map 条件，但比 V671 更干净：少跑无效 probe，并且新样本语义没有越过 exact-safe 边界。

## 代码改动

### Runbook builder

文件：

- `BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py`

新增：

- `--staged-bkf-min-branch-score`
- `--staged-bkf-disable-filtered-fallback`

语义：

- 如果候选没有 branch score，或 score 低于 floor，则被过滤。
- 如果所有候选都被过滤，并且禁用 fallback，则该 branch event 不生成 replay。
- paired 模式下先确认至少有一个可运行 alternative，再生成 selected baseline，避免 baseline-only group。

### Dataset builder

文件：

- `BPC_future/scripts/build_gat_branch_action_sanity_dataset.py`

新增：

- `paired_probe_positive_proxy` 进入样本，但只作为 auxiliary weak-positive / proof-cost 信号。
- 主 `branch_priority_loss_weight = 0`，因此不会被当作 full-run wall-time 正例。

## V671/V673：无 score-floor 的 staged probe

V671 runbook：

- `entry_count = 36`
- `paired_group_count = 12`
- `paired_baseline_entry_count = 12`
- `paired_alternative_entry_count = 24`

V673 paired summary：

- `paired_group_count = 12`
- `alternative_entry_count = 24`
- `label_counts = {'neutral_proxy': 24}`

V674 delta conversion：

- `output_row_count = 0`
- `input_paired_label_counts = {'neutral_proxy': 24}`

解释：这批不应进入训练集。它证明了“只靠结构 BKF 在 hard contexts 里扩采”会大量产出中性、右删失、低信号样本。

## V675：score-floor fail-closed runbook

配置：

```text
candidate_selection = routeopt_bkf_staged
staged_bkf_require_score = True
staged_bkf_min_branch_score = 0.67
staged_bkf_allow_filtered_fallback = False
staged_bkf_max_pool_child_width = 900
staged_bkf_max_pool_total_child_width = 1800
staged_bkf_max_pool_balance_gap = 500
paired_probe = True
```

结果：

```text
entry_count = 6
paired_group_count = 3
paired_baseline_entry_count = 3
paired_alternative_entry_count = 3
candidate_event_count_with_replay_entries = 3
```

这说明 score floor 后只保留了 3 个真正有 score 支持的上下文。

## V676/V677：探测结果

V676 branch-impact：

```text
branch_count = 11
complete_label_branch_count = 3
forced_pair_branch_count = 8
forced_pair_matched_branch_count = 8
run_status_counts = {'OPTIMAL': 3, 'TIME_LIMIT': 8}
tail_class_counts = {'completion_bound_tail': 8, 'unprocessed_children': 3}
total_child_completion_bound_retries = 42
total_child_exact_pricing_events = 48
total_child_fathom_events = 9
usable_branch_impact_training_count = 3
```

V676 completion-tail：

```text
completion_retry_class_counts = {'completion_bound_certified_no_negative': 6}
completion_retry_harvest_tail_class_counts = {'no_harvest_candidate': 6}
completion_retry_total_profile_generation_time = 128.258361
completion_retry_total_generated_sequences = 5224311
completion_retry_total_negative_journeys = 0
```

V677 paired labels：

```text
label_counts = {'neutral_proxy': 2, 'positive_proxy': 1}
```

唯一 positive proxy：

- instance: `random-wave/tranquillitatis tasks020_05_seed61411`
- baseline pair: `[2,10]`
- alternative pair: `[3,10]`
- alternative status: `OPTIMAL`
- paired gap improvement: `0.013779`
- paired wall gain: `-0.021741s`

注意：这里的正向来自 child-probe 状态改善与 gap improvement，不是完整 600s full replay positive。

## V678/V679：数据集接入

V678：

```text
output_row_count = 1
output_counterfactual_label_counts = {'paired_probe_positive_proxy': 1}
production_ready = false
```

V679 dataset：

```text
raw_row_count = 304
sample_count = 209
branch_priority_label_counts = {
  'aux_only_weak_positive': 13,
  'not_walltime_gain': 142,
  'walltime_gain_positive': 54
}
row_kind_counts['paired_probe_positive_proxy'] = 1
```

V679 seed29 training：

```text
best_epoch = 12
best_validation_total_loss = 87.043339
validation_branch_priority_f1 = 0.303030
validation_branch_priority_precision = 0.263158
validation_branch_priority_recall = 0.357143
```

对比 V670 seed29：

```text
V670 sample_count = 208
V670 best_validation_total_loss = 88.403393
V670 validation_branch_priority_f1 = 0.303030
```

解释：V679 的辅助样本让 total loss 有小幅改善，但 branch priority F1 没变。这符合预期，因为新样本没有进入主 wall-time gain loss。

## Exact-Safe 边界

本轮新增内容不改变求解器默认行为：

- runbook 只是生成 replay 命令；
- paired-probe row 是 right-censored proxy；
- `paired_probe_positive_proxy` 不能作为 production score 或 full-run 正例；
- 不产生 official bound；
- 不产生 certificate；
- 不参与剪枝；
- child 最终仍靠 exact pricing / completion-bound closure。

## 下一步

1. 保留 score-floor fail-closed 作为之后 RouteOpt/BKF staged replay 的默认采样方式。
2. 对 V677 的 `[3,10] over [2,10]` 做 full replay 或 depth-1 follow-up replay，确认它是否能从 child-probe positive 变成 full-run weak/strict positive。
3. 如果继续做 RouteOpt 风格 testing，应加入三阶段字段：cheap structural screen、short heuristic-CG probe、exact child-probe，并记录每阶段 `down/up gain` 与测试耗时。
4. 对没有 score 命中的 hard contexts，不再用结构候选硬扫；这些节点应转向 cuts/formulation/incumbent 或更强 state-scoped GAT coverage。
