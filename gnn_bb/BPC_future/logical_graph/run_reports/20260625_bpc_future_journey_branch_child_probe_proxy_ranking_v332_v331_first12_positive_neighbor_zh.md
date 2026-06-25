# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 42
raw_proxy_branch_row_count = 20
proxy_branch_row_count = 8
filtered_out_proxy_branch_row_count = 12
proxy_context_count = 2
proxy_ranking_pair_count = 9
right_censored_proxy_ranking_pair_count = 9
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 2}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 8
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 8}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=4 spread=4.760059667 best=[11, 12] score=-4.026591192 promote=False worst=[17, 18] score=-8.786650859
- node=0 depth=0 alts=4 spread=0.642085758 best=[4, 12] score=-7.994652392 promote=False worst=[7, 13] score=-8.63673815

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[11, 12] worse=[17, 18] gap=4.760059667 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[11, 12] worse=[1, 7] gap=4.496866403 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[11, 12] worse=[5, 7] gap=3.997496075 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[5, 7] worse=[17, 18] gap=0.762563592 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[4, 12] worse=[7, 13] gap=0.642085758 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[4, 20] worse=[7, 13] gap=0.615215958 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[12, 18] worse=[7, 13] gap=0.61300525 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[5, 7] worse=[1, 7] gap=0.499370328 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[1, 7] worse=[17, 18] gap=0.263193264 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
