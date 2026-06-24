# V156-V157 Longer Proxy Replay 负结果

日期：2026-06-24

## 目的

验证 V155 child-probe proxy ranking 中排名最高的两个候选是否能升级为 full replay 正例：

- seed61000 root `[2,9]`
- seed61103 root `[10,18]`

这两条都来自 canonical random-TW `tasks_020/greedy-anchor/apollo15_20km`，不是旧 hard-set。

## 运行

```text
config = BPC_future/configs/moon_trek_20_smoke.yaml
time_limit = 600
candidate_priority = force_pair_path

seed61000:
  instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
  forced_pair = [2,9]
  result = BPC_future/results/v156_longer_replay_seed61000_pair_2_9_600_20260624/results.csv

seed61103:
  instance = BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
  forced_pair = [10,18]
  result = BPC_future/results/v156_longer_replay_seed61103_pair_10_18_600_20260624/results.csv
```

`moon_trek_20_smoke.yaml` 默认保持：

```text
journey_corrected_node_bound_fathom_enabled = False
journey_tail_action_early_branch_enabled = False
journey_tail_action_no_column_early_branch_enabled = False
```

所以本次只验证 forced root branch pair，不引入 corrected-bound fathom 或 tail-action early branch 行为。

## 结果

两条均未解决 timeout：

```text
seed61000 [2,9]:
  status = EXTERNAL_TIME_LIMIT
  wall = 600.02s
  return_code = 124

seed61103 [10,18]:
  status = EXTERNAL_TIME_LIMIT
  wall = 600.02s
  return_code = 124
```

与 full600 baseline 一样，这两个 canonical 实例仍为 `EXTERNAL_TIME_LIMIT`。

## V157 审计

```text
audit = BPC_future/results/journey_branch_impact_audit_v157_v156_longer_proxy_replay_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v157_v156_longer_proxy_replay_zh.md

branch_count = 19
forced_pair_branch_count = 2
forced_pair_matched_branch_count = 2
right_censored_branch_count = 19
usable_branch_impact_training_count = 0
tail_class_counts = {
  completion_bound_tail: 12,
  negative_chain_continues: 1,
  unprocessed_children: 6
}
total_child_negative_pricing_events = 90
total_child_exact_pricing_events = 93
total_child_completion_bound_retries = 78
total_child_fathom_events = 5
max_child_corrected_bound_gain = 19.255997
```

根 forced pair 行：

```text
[2,9] seed61000:
  forced_pair_matched = true
  tail_class = completion_bound_tail
  active_touch = 1
  inactive_only = 0
  child_negative_pricing_events = 16
  child_exact_pricing_events = 9
  child_completion_bound_retries = 11
  child_fathom_events = 1
  child_max_corrected_bound_gain = 3.321616

[10,18] seed61103:
  forced_pair_matched = true
  tail_class = completion_bound_tail
  active_touch = 0
  inactive_only = 1
  child_negative_pricing_events = 6
  child_exact_pricing_events = 5
  child_completion_bound_retries = 6
  child_fathom_events = 0
  child_max_corrected_bound_gain = 0.936492333
```

直接 child 观测：

```text
[2,9]:
  same_vehicle:
    gain = 3.321616
    negative = 9
    exact = 6
    retry = 8
    cpu = 74.050431
    fathom = 1
  separate_vehicle:
    gain = 0.338651667
    negative = 7
    exact = 3
    retry = 3
    cpu = 58.716846
    fathom = 0

[10,18]:
  same_vehicle:
    gain = 0.040789333
    negative = 4
    exact = 3
    retry = 3
    cpu = 41.250984
    fathom = 0
  separate_vehicle:
    gain = 0.936492333
    negative = 2
    exact = 2
    retry = 3
    cpu = 17.292136
    fathom = 0
```

## 解释

V155 的 proxy 排名方向没有完全错：`[2,9]` 确实比普通候选更有 bound/fathom 信号，一个 child 在 181.8s fathom；但它不是 full replay 正例。600s 内搜索继续向更深层扩展，seed61000 后续仍出现多个 branch，最后一次 branch 在约 588.5s，仍未证明完成。

seed61103 的 `[10,18]` 更弱：只有 corrected-bound gain，没有 root child fathom；600s 末尾仍在 depth 5，最后记录为 `completion_bound_final_probe_time_limit`。

## 结论

不能把 V155 proxy ranking 直接当作可生产 branch score 或强正例。当前证据说明：

1. child-probe proxy 适合筛选“值得继续看”的候选；
2. 但 full replay 能否解决 timeout 仍需要更强标签验证；
3. 单靠换 root pair 不能解决这两个 apollo greedy 20-scale 实例；
4. 后续必须并行推进 child ordering / tail-action / incumbent / cuts / formulation，而不是继续把 proxy top pair 直接升级成 score map。
