# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 16
raw_proxy_branch_row_count = 6
proxy_branch_row_count = 4
filtered_out_proxy_branch_row_count = 2
proxy_context_count = 1
proxy_ranking_pair_count = 5
right_censored_proxy_ranking_pair_count = 5
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 1}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 4
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 4}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=4 spread=0.835418725 best=[1, 14] score=-3.233683208 promote=False worst=[3, 14] score=-4.069101933

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[1, 14] worse=[3, 14] gap=0.835418725 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[1, 14] worse=[3, 6] gap=0.835037517 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[1, 14] worse=[1, 6] gap=0.451210609 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[1, 6] worse=[3, 14] gap=0.384208116 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[1, 6] worse=[3, 6] gap=0.383826908 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
