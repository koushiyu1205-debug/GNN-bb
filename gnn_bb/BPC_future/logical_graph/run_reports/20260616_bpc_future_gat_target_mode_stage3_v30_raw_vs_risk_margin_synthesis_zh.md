# 2026-06-16 BPC_future GAT Stage 3 v30 Raw-vs-Risk Margin Synthesis

## 结论

本轮按计划复读 `gat_bpc_future_target_mode_optimization_plan_zh`、Stage 1/2
报告、v15 / v23 / v29 Stage 3-4 报告和 Stage 5 目标后，只做 offline
raw-vs-risk score-margin 审计增强，不改 solver、pricing、RMP、worker 或
certificate path。

核心结论：

```text
v30_raw_vs_risk_audit_completed = true
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
```

v15 missed high-ROI 不是“分数差一点”或 risk penalty 压低为主：
16 个 missed high-ROI 全部 raw candidate score 低于阈值，且没有
risk-adjusted suppression。v15 的正确下一步是补 same-context contrast / 改进
candidate 表示，不是降阈值。

v29_p075 则相反：8 个 missed high-ROI 里 7 个 raw candidate score 已经过阈值，
但被 risk-adjusted score / delay gate 压到阈值下。这说明 two-stage rescue
window 有明确作用对象，但不能全局放松 penalty，因为 v29 已证明 false-safe 会爆炸。

## 代码 / 审计改动

增强：

```text
BPC_future/scripts/audit_gat_batch_impact_score_margins.py
BPC_future/tests/test_gat_batch_impact_score_margins.py
```

新增 machine-checkable 字段：

```text
missed_raw_candidate_score_margin_min / mean / median / max
raw_candidate_margin_bucket_counts
risk_adjusted_suppressed_miss_count
raw_candidate_score_gap_miss_count
batch_score_gap_miss_count
risk_adjusted_suppressed_miss
raw_candidate_margin_bucket
raw_candidate_score_gap_to_threshold
```

这些字段区分三类 blocker：

- raw candidate score 本身低于阈值；
- raw score 已过阈值但 risk-adjusted / delay gate 压低；
- candidate 已过，但 batch score / family threshold 拦住。

## v30 审计产物

```text
v15_summary =
  BPC_future/results/gat_batch_impact_score_margin_audit_v30_v15_raw_vs_risk_20260616/summary.json
v15_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v30_v15_raw_vs_risk_score_margin_audit_zh.md

v23_summary =
  BPC_future/results/gat_batch_impact_score_margin_audit_v30_v23_raw_vs_risk_20260616/summary.json
v23_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v30_v23_raw_vs_risk_score_margin_audit_zh.md

v29_p075_summary =
  BPC_future/results/gat_batch_impact_score_margin_audit_v30_v29_p075_raw_vs_risk_20260616/summary.json
v29_p075_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v30_v29_p075_raw_vs_risk_score_margin_audit_zh.md
```

## 对比

| variant | high ROI | accepted high ROI | missed | raw gap miss | risk-suppressed miss | batch gap miss | raw buckets | admission buckets |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| v15 | 28 | 12 | 16 | 16 | 0 | 0 | deep 11, moderate 5 | deep 11, moderate 5 |
| v23 | 30 | 27 | 3 | 1 | 0 | 3 | deep 1, near 2 | deep 1, near 2 |
| v29_p075 | 30 | 22 | 8 | 1 | 7 | 0 | deep 1, near 7 | deep 1, moderate 1, near 6 |

关键 margin：

| variant | candidate threshold | missed raw mean | missed raw min | missed raw max | missed admission mean | missed admission min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| v15 | 0.901963 | -0.382917 | -0.856920 | -0.072269 | -0.382917 | -0.856920 |
| v23 | 0.286639 | -0.029230 | -0.282270 | 0.135371 | -0.029230 | -0.282270 |
| v29_p075 | 0.242547 | 0.064877 | -0.237887 | 0.128279 | -0.062816 | -0.242073 |

## 解读

### v15

v15 的 missed high-ROI 全部是 raw score gap：

```text
missed_high_roi = 16
raw_candidate_score_gap_miss_count = 16
risk_adjusted_suppressed_miss_count = 0
batch_score_gap_miss_count = 0
missed_without_same_context_contrast_count = 7
```

因此 v15 不是轻微阈值问题。候选 head 没把这些 high-ROI batch 的 candidate
score 打高，且 7 个 missed 缺 same-context low-ROI / delay contrast。对 v15
直接降 threshold 会把 safety gate 变软，不能作为 Stage 3/4 方向。

### v23

v23 positive boost 已经基本解决 high-ROI recall：

```text
accepted_high_roi = 27 / 30
missed_high_roi = 3
batch_score_gap_miss_count = 3
risk_adjusted_suppressed_miss_count = 0
```

剩余 missed 主要是 batch threshold / batch ROI ranking 问题。但 v23 的主失败不是
missed，而是 accepted low-ROI / delay-risk 过多，导致 false-safe 过高。

### v29_p075

v29_p075 的 missed high-ROI 大多是可恢复的 risk-adjusted suppression：

```text
missed_high_roi = 8
raw_candidate_score_gap_miss_count = 1
risk_adjusted_suppressed_miss_count = 7
raw_candidate_margin_bucket_counts = {'deep_candidate_score_gap': 1, 'near_candidate_threshold': 7}
```

这证明 two-stage rescue window 有明确作用对象：raw score 已经过阈值、但被
delay-risk exponent 或 delay gate 压下去的 near-miss。问题是同一轮 v29 也证明
全局放松 penalty 会把 false-safe 拉到 35% 以上，因此 rescue 不能是单值 penalty
放松。

## 下一步算法方向

不要继续盲扫全局 `candidate_delay_score_penalty`。下一步应做 audit-only two-stage
admission score：

```text
stage A:
  使用 v28 strict risk-adjusted score 控 false-safe；

stage B:
  只对 raw candidate score 已过阈值、
  且 kNN/OOD/CBF-safe 或 context-family safe 的 near-miss
  启用 rescue window；

report:
  单独报告 rescue_promoted_count、
  rescue_accepted_high_roi_count、
  rescue_accepted_low_roi_or_bad_count、
  rescue_false_high_priority_on_delay、
  rescue_false_safe_rate_union、
  accepted_batch_roi_ci_low。
```

如果 rescue 后 false-safe、safe CI、ROI-CI 任一失败，仍必须判定：

```text
stage4_candidate_ready = false
production_ready = false
```

v15 剩余 missed 不应由 rescue 处理；它们应进入 same-context contrast 采样或
candidate 表示增强。

## Exactness Boundary

本轮所有 artifact 都是 offline / diagnostic-only：

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```

GAT / CBF / kNN / OOD 仍只能做 ordering、priority 或 finite-delay scheduling。
最终 optimality certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整
配置宇宙的 exhaustive no-negative closure。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
  BPC_future/scripts/audit_gat_batch_impact_score_margins.py \
  BPC_future/tests/test_gat_batch_impact_score_margins.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
  BPC_future.tests.test_gat_batch_impact_score_margins

Ran 1 test in 0.014s
OK
```
