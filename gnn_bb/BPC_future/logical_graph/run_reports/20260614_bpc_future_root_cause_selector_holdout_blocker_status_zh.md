# Selector Holdout Blocker Status 报告

日期：2026-06-14

## 结论

当前不是没有采集入口，也不是采集命令不安全；阻塞点是 production selector validation 所需的 full-snapshot 标签覆盖仍不够。

```text
status = selector_holdout_blocked_by_snapshot_label_mix
all_checks_pass = true
runs_bpc_or_pricing = false
diagnostic_only = true
```

## 已确认安全的部分

- 普通 collection capture：`command_count=6`，`capture_event_count=78`，`no_certificate_bad_count=0`，`active_basis_bad_count=0`；
- priority capture：`command_count=1`，`capture_event_count=12`，`no_certificate_bad_count=0`，`active_basis_bad_count=0`；
- 两类 capture 都没有 certificate / official bound effect；
- 两类 capture 的 active-basis payload 检查通过。

## 仍然阻塞的部分

- 普通 collection expected contexts：`9/10` hit，`missing_expected_context_count=1`；
- priority expected contexts：`0/3` hit，`missing_expected_context_count=3`；
- base selector rows：`row_count=280`，但 `complete_snapshot_row_count=0`；
- complete snapshot rows：`row_count=62`，`label_counts={'improved': 59, 'noop': 3}`，即 `59 improved / 3 noop`，且 mixed-label context 为 `0`；
- complete explicit forbidden rows：`row_count=48`，`label_counts={'improved': 48}`，即 `48 improved / 0 noop`，仍是 positive-only；

## 对根因判断的影响

这进一步收紧了当前根因：我们已经能安全采集 active-basis / pool / forbidden payload，但 production selector 仍缺负例/混合 context 的 full-snapshot 覆盖。

因此下一步可以继续做 calibration-only 数据补齐，但不能直接进入 production BPC A/B，也不能把现有 selector、Pulse worker 或 return policy 当成主线优化。

production selector validation 与 production BPC A/B 仍被阻塞。需要先补齐：

1. no-certificate-effect full-snapshot 的 noop / false-positive contexts；
2. explicit forbidden / pool payload 下同时包含 improved 和 noop 的 rows；
3. context / instance / dataset holdout 全部通过后的 selector。

在这些证据之前，当前目标仍保持 active，不能宣称 5/10 no-regression 与 20-task wall-time speedup 已被证明。
