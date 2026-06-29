# V555：retry 关闭后果诊断（seed61717）

## 背景

针对 20 规模 random-TW 实例：

`tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json`

使用 V545 配置加 completion-bound profile timing 单实例复跑，外部时限 600s。

## 结果

- 求解状态：`EXTERNAL_TIME_LIMIT`
- wall time：`600.039479s`
- gap：`0.039594`
- completion retry 分类：`completion_bound_time_limit_no_column_uncertified`
- harvest tail 分类：`expensive_no_harvest_candidate`
- retry profile 总耗时：`295.849556s`
- retry negative journeys：`0`
- retry selected trips：`0`
- harvest candidate / selected：全部为 `0`

主要 profile 热点：

- `direct_label_profile_next_sortie_total_time = 230.297112s`
- `direct_label_profile_extend_time = 39.467256s`
- `direct_label_profile_bound_check_time = 36.320264s`
- `direct_label_profile_completed_process_time = 34.594679s`
- `direct_label_profile_stream_callback_time = 30.579666s`

## 对 retry 的判断

retry 不能简单全关。

它的正面作用是：在某些节点上补完 completion-bound / direct-label 的 no-negative certificate，或者发现隐藏的真负列。只要 retry 成功给出 `CERTIFIED_NO_NEGATIVE`，它就在帮助节点证明闭合。

但 seed61717 这类实例显示了反面：retry 可以消耗接近半个 600s 预算，却没有找到负列、没有选中 trip、没有 harvest candidate，最终仍然没有闭环。这说明问题不是“retry 永远有用”，而是 retry 缺少收益预测和停止条件。

## 如果不 retry，会发生什么

精确性上可以安全，但必须 fail-closed：

- 不能把未 retry 的节点当成 no-negative certificate。
- 不能用未闭合的 RMP objective 剪枝。
- 节点只能标记为未认证，继续走分支或最终超时。

性能上风险很大：

- 好处：可以省掉这类昂贵 zero-harvest retry 的时间。
- 坏处：本来能靠 retry 得到 certificate 的节点会失去闭合机会，分支树可能变宽，`OPTIMAL` 数可能下降。

## 建议

不要默认 `retry=False` 一刀切。下一步应做两个对照：

1. `retry off`：估计完全关闭 retry 的时间上界收益和 OPTIMAL 损失。
2. `retry gated`：只在预计能产生 certificate 或真负列时 retry；连续 zero-harvest、profile bucket 巨大、或 profile 超预算时 fail-closed 转 branch。

当前更推荐第二条，因为它保留 exact-safe certificate 的价值，同时避免 seed61717 这种昂贵无收获 proof tail。
