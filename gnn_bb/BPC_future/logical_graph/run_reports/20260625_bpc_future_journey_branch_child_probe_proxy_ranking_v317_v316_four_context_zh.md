# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 96
raw_proxy_branch_row_count = 44
proxy_branch_row_count = 16
filtered_out_proxy_branch_row_count = 28
proxy_context_count = 4
proxy_ranking_pair_count = 24
right_censored_proxy_ranking_pair_count = 24
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 4}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 16
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 16}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=4 spread=0.724274593 best=[1, 19] score=-7.91794835 promote=False worst=[2, 11] score=-8.642222943
- node=0 depth=0 alts=4 spread=1.086922066 best=[3, 12] score=-7.316561992 promote=False worst=[1, 2] score=-8.403484058
- node=0 depth=0 alts=4 spread=1.9588245 best=[5, 8] score=-6.97303365 promote=False worst=[2, 9] score=-8.93185815
- node=0 depth=0 alts=4 spread=1.19257715 best=[1, 2] score=-8.24484245 promote=False worst=[1, 12] score=-9.4374196

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[5, 8] worse=[2, 9] gap=1.9588245 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[5, 8] worse=[2, 10] gap=1.889836567 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[1, 2] worse=[1, 12] gap=1.19257715 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[3, 12] worse=[1, 2] gap=1.086922066 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 12] worse=[2, 9] gap=1.0314883 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[3, 12] worse=[1, 12] gap=0.972606116 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 12] worse=[2, 10] gap=0.962500367 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[5, 8] worse=[8, 12] gap=0.9273362 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 7] worse=[1, 12] gap=0.864149783 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[3, 12] worse=[1, 9] gap=0.847875008 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[1, 19] worse=[2, 11] gap=0.724274593 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[14, 16] worse=[1, 12] gap=0.713017892 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
