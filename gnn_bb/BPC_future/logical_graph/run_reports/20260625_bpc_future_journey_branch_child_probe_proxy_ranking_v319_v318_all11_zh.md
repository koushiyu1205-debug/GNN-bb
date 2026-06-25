# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 190
raw_proxy_branch_row_count = 83
proxy_branch_row_count = 36
filtered_out_proxy_branch_row_count = 47
proxy_context_count = 9
proxy_ranking_pair_count = 53
right_censored_proxy_ranking_pair_count = 53
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 8, 'has_uncensored_pair_context': 1}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 1
promotion_blocked_branch_count = 35
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 35}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=4 spread=2.9967023 best=[15, 16] score=-6.064932267 promote=False worst=[1, 5] score=-9.061634567
- node=0 depth=0 alts=4 spread=0.263684675 best=[1, 4] score=-9.266275342 promote=False worst=[7, 19] score=-9.529960017
- node=0 depth=0 alts=4 spread=4.640058934 best=[15, 19] score=-4.430321583 promote=False worst=[1, 16] score=-9.070380517
- node=0 depth=0 alts=4 spread=0.724274593 best=[1, 19] score=-7.91794835 promote=False worst=[2, 11] score=-8.642222943
- node=0 depth=0 alts=4 spread=19.58906 best=[6, 20] score=9.848762492 promote=True worst=[1, 2] score=-9.740297508
- node=0 depth=0 alts=4 spread=1.086922066 best=[3, 12] score=-7.316561992 promote=False worst=[1, 2] score=-8.403484058
- node=0 depth=0 alts=4 spread=1.9588245 best=[5, 8] score=-6.97303365 promote=False worst=[2, 9] score=-8.93185815
- node=0 depth=0 alts=4 spread=1.19257715 best=[1, 2] score=-8.24484245 promote=False worst=[1, 12] score=-9.4374196
- node=0 depth=0 alts=4 spread=5.842843175 best=[2, 16] score=-4.2464302 promote=False worst=[1, 14] score=-10.089273375

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[6, 20] worse=[1, 2] gap=19.58906 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[6, 20] worse=[16, 17] gap=15.499941425 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[6, 20] worse=[13, 17] gap=13.015900542 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[13, 17] worse=[1, 2] gap=6.573159458 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 16] worse=[1, 14] gap=5.842843175 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 16] worse=[1, 15] gap=5.12323555 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[15, 19] worse=[1, 16] gap=4.640058934 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 16] worse=[7, 10] gap=4.63150725 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[15, 19] worse=[8, 14] gap=4.533771834 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[15, 19] worse=[1, 4] gap=4.099466167 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[16, 17] worse=[1, 2] gap=4.089118575 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[15, 16] worse=[1, 5] gap=2.9967023 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
