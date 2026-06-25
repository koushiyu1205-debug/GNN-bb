# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-24

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 168
raw_proxy_branch_row_count = 67
proxy_branch_row_count = 38
filtered_out_proxy_branch_row_count = 29
proxy_context_count = 7
proxy_ranking_pair_count = 63
right_censored_proxy_ranking_pair_count = 63
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 7}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=6 spread=3.50503335 best=[3, 17] score=-5.406248167 worst=[5, 18] score=-8.911281517
- node=0 depth=0 alts=2 spread=4.008015066 best=[5, 13] score=-3.008555542 worst=[2, 13] score=-7.016570608
- node=0 depth=0 alts=6 spread=1.06811335 best=[14, 20] score=-8.363341125 worst=[1, 14] score=-9.431454475
- node=0 depth=0 alts=6 spread=1.460184167 best=[13, 16] score=-7.30457975 worst=[17, 18] score=-8.764763917
- node=0 depth=0 alts=6 spread=1.341908797 best=[2, 5] score=-7.33900955 worst=[17, 20] score=-8.680918347
- node=0 depth=0 alts=6 spread=1.282341008 best=[2, 4] score=-7.544893217 worst=[5, 11] score=-8.827234225
- node=0 depth=0 alts=6 spread=0.03992855 best=[4, 11] score=-9.315240467 worst=[5, 11] score=-9.355169017

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[5, 13] worse=[2, 13] gap=4.008015066 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[3, 17] worse=[5, 18] gap=3.50503335 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[3, 17] worse=[8, 15] gap=3.362572008 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[3, 17] worse=[14, 18] gap=2.381961475 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[3, 17] worse=[10, 17] gap=2.212846875 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[3, 17] worse=[15, 18] gap=1.965150483 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[15, 18] worse=[5, 18] gap=1.539882867 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[13, 16] worse=[17, 18] gap=1.460184167 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[13, 16] worse=[12, 17] gap=1.4342937 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[15, 18] worse=[8, 15] gap=1.397421525 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[13, 16] worse=[13, 17] gap=1.396928358 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[13, 16] worse=[8, 17] gap=1.381168642 reason=corrected_gain_then_proxy_score right_censored=True

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
