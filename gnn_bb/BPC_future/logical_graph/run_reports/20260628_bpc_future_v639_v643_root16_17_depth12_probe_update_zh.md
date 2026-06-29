# 20260628 V639-V643：root `[16,17]` 后续 depth1/depth2 probe 更新

## 目的

V635/V636 已证明 seed61311 的 root pair 从 `[17,20]` 改成 `[16,17]` 后，gap、incumbent、branch count 和 fathom 结构都有改善，但 600 秒内仍未闭环。

本轮继续沿 `[16,17]` 后的实际 path，检查 depth1/depth2 的 alternative branch pair 是否能形成连续 state-scoped branch policy path。

边界：

- 只做 child-probe / paired probe；
- 不产生 official bound；
- 不产生 certificate；
- 不把 probe label 当完整求解正例；
- exact-safe 求解逻辑不变。

## 产物

```text
V639 runbook:
BPC_future/results/journey_branch_candidate_replay_runbook_v639_v636_root16_17_depth1_2_pairprobe_20260628/

V640 branch impact:
BPC_future/results/journey_branch_impact_v640_v639_root16_17_depth1_2_pairprobe_20260628/

V641 paired probe summary:
BPC_future/results/journey_paired_probe_summary_v641_v639_root16_17_depth1_2_pairprobe_20260628/

V642 proxy ranking:
BPC_future/results/journey_branch_child_probe_proxy_ranking_v642_v640_root16_17_depth1_2_20260628/

V643 probe readiness:
BPC_future/results/journey_branch_probe_training_readiness_v643_v642_root16_17_depth1_2_20260628/
```

## V639 设置

输入日志：

```text
BPC_future/results/journey_branch_full_replay_v636_seed61311_root16_17_20260628/alt_16_17/logs/...
```

筛选：

- depth：`1..2`
- source event time：`<=100s`
- paired groups：`4`
- 每组：selected baseline + 3 alternatives
- total commands：`16`
- mode：`child_probe`
- time limit：`240s`
- max workers：`4`
- max CG iterations：`36`

全部命令 `rc=0`。

## V641 paired-probe 结果

```text
paired_group_count = 4
baseline_entry_count = 4
alternative_entry_count = 12
observed_alternative_entry_count = 12
label_counts = {'hard_negative_proxy': 5, 'neutral_proxy': 7}
positive_proxy = 0
production_ready = false
official_bound_effect = false
certificate_effect = false
```

分组结论：

| context | selected baseline | best alt by wall | paired wall gain | paired CB retry gain | label |
|---|---:|---:|---:|---:|---|
| depth1 node1 | `[1,3]` | `[1,10]` | `0.016s` | `5` | hard-negative dominated |
| depth1 node2 | `[1,3]` | `[1,15]` | `0.912s` | `0` | neutral |
| depth2 node3 | `[1,10]` | `[3,10]` | `0.500s` | `0` | neutral |
| depth2 node4 | `[1,13]` | `[5,8]` | `21.507s` | `5` | hard-negative mixed |

关键点：`[5,8]` 虽然 probe wall time 快了约 21.5 秒，但 paired gap 变差，所以不能当正例。

## V642/V643 proxy readiness

V642 从 V640 `child_probe_rows.jsonl` 生成 proxy ranking：

```text
raw_child_probe_row_count = 272
raw_proxy_branch_row_count = 34
proxy_branch_row_count = 16
proxy_context_count = 5
proxy_ranking_pair_count = 28
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 16
right_censored_proxy_ranking_pair_count = 28
sampling_navigation_ready = true
ranking_training_ready = false
```

V643 readiness：

```text
row_count = 34
probe_positive_count = 0
probe_hard_negative_count = 16
probe_hard_negative_context_count = 16
probe_instance_count = 1
probe_time_window_family_count = 1
probe_debug_training_ready = false
probe_sanity_training_ready = false
probe_serious_training_ready = false
```

解释：

- 这批数据适合做 hard-negative / proof-tail risk 诊断；
- 不能用于训练正式 branch score 正例；
- 不能直接生成 promotion overlay；
- 只能作为后续搜索避坑或风险惩罚的辅助输入。

## 当前判断

V636 的 `[16,17]` root pair 是有效的弱 gap/fathom positive，但它后面的自然 depth1/depth2 alternatives 没有形成继续改善的 path。

这说明当前难点不是“找到一个更好的 root pair”就结束，而是：

1. root pair 需要后续 state-scoped branch path 配合；
2. child-probe wall-time gain 单独不可靠；
3. gap / incumbent / fathom / CB retry 必须一起看；
4. 对 right-censored child-probe，宁可保守标成 neutral/hard-negative，也不能晋升为正例。

## 对主线的影响

当前最好 full60 仍是 V545：

```text
20-scale random-TW full60:
OPTIMAL = 36/60
TIME_LIMIT = 3/60
EXTERNAL_TIME_LIMIT = 21/60
capped mean = 341.542949s
<=200s OPTIMAL = 22/60
```

目标 `60/60 OPTIMAL within 600s` 尚未达到。

下一步应继续围绕 V545 未闭环的 24 个实例寻找“连续 state-scoped positive path”，而不是只沿 seed61311 `[16,17]` 的当前 depth1/depth2 alternatives 深挖。

优先策略：

1. 从 V545 未闭环实例中找有早期 incumbent/gap/fathom 改善信号的 root/depth1 pair；
2. 对每个候选做 paired child-probe，但正例晋升必须同时满足 gap 不变差、CB retry 不明显上升、fathom/closed child 有改善；
3. 把 V641/V642 这类 hard-negative proxy 加入风险惩罚，防止模型追逐“probe wall 快但 gap 变坏”的 pair；
4. 只有 full replay 或至少 gap/fathom replay 证明稳定改善后，才写入 state-scoped score overlay。
