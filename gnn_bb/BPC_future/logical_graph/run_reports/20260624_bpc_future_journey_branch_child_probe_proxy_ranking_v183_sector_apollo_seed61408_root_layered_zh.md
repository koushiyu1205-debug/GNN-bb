# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-24

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 16
raw_proxy_branch_row_count = 8
proxy_branch_row_count = 6
filtered_out_proxy_branch_row_count = 2
proxy_context_count = 1
proxy_ranking_pair_count = 14
right_censored_proxy_ranking_pair_count = 14
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 1}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=6 spread=2.327094961 best=[9, 11] score=-6.143066367 worst=[1, 11] score=-8.470161328

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[9, 11] worse=[1, 11] gap=2.327094961 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 14] worse=[1, 11] gap=2.288463278 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[9, 11] worse=[4, 14] gap=2.248974583 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 14] worse=[4, 14] gap=2.2103429 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[11, 20] worse=[1, 11] gap=2.18795857 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[11, 20] worse=[4, 14] gap=2.109838192 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[2, 4] worse=[1, 11] gap=1.693617553 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[2, 4] worse=[4, 14] gap=1.615497175 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[9, 11] worse=[2, 4] gap=0.633477408 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 14] worse=[2, 4] gap=0.594845725 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[11, 20] worse=[2, 4] gap=0.494341017 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[9, 11] worse=[11, 20] gap=0.139136391 reason=corrected_gain_then_proxy_score right_censored=True

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
