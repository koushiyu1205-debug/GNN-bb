# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 68
raw_proxy_branch_row_count = 31
proxy_branch_row_count = 12
filtered_out_proxy_branch_row_count = 19
proxy_context_count = 3
proxy_ranking_pair_count = 16
right_censored_proxy_ranking_pair_count = 16
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 3}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 12
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 12}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=4 spread=4.242349377 best=[2, 16] score=-4.183580875 promote=False worst=[7, 13] score=-8.425930252
- node=0 depth=0 alts=4 spread=1.564639225 best=[8, 10] score=-5.081387233 promote=False worst=[4, 9] score=-6.646026458
- node=0 depth=0 alts=4 spread=1.813986875 best=[7, 8] score=-6.943709825 promote=False worst=[3, 13] score=-8.7576967

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[2, 16] worse=[7, 13] gap=4.242349377 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[3, 5] worse=[7, 13] gap=2.671619869 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[3, 9] worse=[7, 13] gap=2.416902427 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 16] worse=[3, 9] gap=1.82544695 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[7, 8] worse=[3, 13] gap=1.813986875 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[7, 8] worse=[3, 9] gap=1.779067708 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 16] worse=[3, 5] gap=1.570729508 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 10] worse=[4, 9] gap=1.564639225 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 10] worse=[8, 9] gap=1.544928617 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[1, 10] worse=[3, 13] gap=1.510308383 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[1, 10] worse=[3, 9] gap=1.475389216 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[4, 8] worse=[4, 9] gap=1.152756833 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
