# GAT Sequential Target-materialization Utility Rows 报告

日期：2026-06-16

## 目的

把 sequential target-materialization run 的结果转成 longer-horizon workload-aware
batch-impact rows。该脚本只读已有日志和 CSV，不运行 BPC / pricing / RMP。

## 机器字段

```text
status = built
candidate_count = 2
row_count = 2
positive_utility_row_count = 0
negative_utility_row_count = 2
bad_mode_row_count = 2
accepted_batch_roi_label = -4.1411999999999995
rmp_solves_delta = 5
pricing_calls_delta = 8
exact_pricing_calls_delta = 3
generated_sequences_delta = 11106
evaluated_timed_trips_delta = 23359
workload_worse = true
all_checks_pass = true
```

## 判定

如果 workload 变重，即使 worker 物化了 true-RC negative active replacement，
也必须作为 bad-mode / DELAY_QUEUE 训练信号，不能标成 Stage 4 HIGH_PRIORITY 正例。
