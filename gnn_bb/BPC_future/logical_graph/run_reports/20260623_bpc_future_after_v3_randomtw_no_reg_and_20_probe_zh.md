# BPC_future V3 corrected-bound 后 random-TW no-regression 与 20 规模诊断

日期：2026-06-23

## 口径

本报告只使用 canonical 分层 random-TW 60-instance：

- 5 规模：`BPC_future/logical_graph/tasks_005`
- 10 规模：`BPC_future/logical_graph/tasks_010`
- 20 规模诊断实例：`BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json`

旧 hard-set 不计入本报告结论。

## 5/10 默认配置 no-regression

本轮验证的是 V3 corrected-bound guarded fathom 合入后的默认配置。`journey_corrected_node_bound_fathom_enabled` 默认关闭。

结果文件：

```text
BPC_future/results/20260623_after_v3_default_full600_randomtw60_tasks5.csv
BPC_future/results/20260623_after_v3_default_full600_randomtw60_tasks10.csv
```

5 规模：

```text
status = 60/60 OPTIMAL
avg = 0.338764s
median = 0.283343s
p90 = 0.409191s
p95 = 0.850825s
max = 0.908696s
```

对照上一份 current full600：

```text
status = 60/60 OPTIMAL
avg = 0.347385s
median = 0.314546s
p90 = 0.432270s
p95 = 0.469372s
max = 1.005447s
```

10 规模：

```text
status = 60/60 OPTIMAL
avg = 4.750018s
median = 1.638110s
p90 = 8.986406s
p95 = 23.789413s
max = 50.060277s
```

对照上一份 current full600：

```text
status = 60/60 OPTIMAL
avg = 5.479933s
median = 1.876931s
p90 = 10.031230s
p95 = 28.400749s
max = 56.850713s
```

结论：

- 5/10 correctness 没有退化，均为 `60/60 OPTIMAL`。
- 5 规模平均、median、p90、max 没有退化；p95 有小幅波动，但绝对值仍小于 1s。
- 10 规模 avg、median、p90、p95、max 均优于上一份 current full600。
- 因为 V3 fathom 默认关闭，这说明本轮代码合入没有破坏默认 5/10 主 benchmark。

## 20 规模 V3 opt-in 600s 诊断

运行文件：

```text
BPC_future/results/20260623_v3_corrected_bound_600_randomtw20_seed61000.csv
```

配置增量：

```text
journey_pricing_direct_journey_label_frontier_bound_ledger_enabled=true
journey_pricing_direct_journey_label_global_certificate_enabled=true
journey_corrected_node_bound_audit_enabled=true
journey_corrected_node_bound_fathom_enabled=true
```

结果：

```text
status = EXTERNAL_TIME_LIMIT
return_code = 124
wall_time = 600.022094s
```

日志摘要：

```text
journey_pricing events = 84
journey_rmp events = 45
journey_corrected_node_bound_audit = 31
journey_exact_pricing_completion_bound_retry = 9
branch_count = 4
max_node = 8
max_depth = 3
journey_corrected_node_bound_fathom = 0
```

pricing state 分布：

```text
FOUND_NEGATIVE = 50
INCOMPLETE_LIMIT = 22
LOCAL_NO_COLUMN_UNCERTIFIED = 8
CERTIFIED_NO_NEGATIVE = 4
```

pricing reason 前几项：

```text
streaming_partial_negative_journey = 46
no_negative_journey = 8
ng_dssr_time_limit = 7
time_limit = 6
partial_profile_scan_no_negative_journey = 6
direct_label_no_negative_journey = 4
weak_negative_journeys_filtered = 4
```

corrected-bound audit：

```text
negative_journey_requires_column_addition = 12
pricing_not_global_certificate_capable = 13
ok = 6
valid corrected audits = 6
corrected fathoms = 0
```

6 条 valid corrected audit 中，4 条是 full certificate：

```text
bound_kind = FULL_LP_CERTIFICATE
global_remaining_rc_lb = 0.0
```

真正属于 incomplete frontier corrected bound 的 2 条都太松：

```text
node 1 depth 1 cg 3:
  global_remaining_rc_lb = -424.350733
  corrected_node_lb = -6633.817616

node 7 depth 3 cg 3:
  global_remaining_rc_lb = -426.022325
  corrected_node_lb = -6662.158066
```

因此它们不能用于 fathom。

## 判断

V3 入口已经接通，也能在真实 20 规模日志中产生 valid corrected-bound artifact；但当前 frontier lower bound 太松，无法形成有用剪枝。

这个实例 600s 未闭合的主要原因不是 V3 开关没生效，而是：

- root 和 branch 节点仍持续发现真实负列；
- hidden-negative patrol 经常 `ng_dssr_time_limit`；
- completion-bound retry 有时继续发现强负列；
- incomplete frontier 的 `global_remaining_rc_lb` 约 `-424`，经过 `R_N` 修正后 LB 变成极低值，完全没有剪枝价值。

下一步应优先：

1. 收紧 direct-label frontier LB，而不是只打开 corrected-bound fathom；
2. 针对 canonical 20 的 late true-negative 做 support-aware batch admission / earlier materialization；
3. 继续保留 V3 默认关闭，直到 canonical 20 诊断中出现稳定、有用的 corrected-bound fathom。
