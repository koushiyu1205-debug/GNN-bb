# V731/V732 Dynamic SRC Greedy-Anchor Seed61311 Smoke

日期：2026-06-28

## 目的

V729 显示 greedy-anchor 的 depth1/depth2 branch pair 替换没有改变 dual/gap。基于 V730 新增的 dynamic SRC audit-only 入口，本轮对 `tasks020_04_seed61311` 做一个短预算 smoke：

- V731: audit-only，不加 cut；
- V732: cut-on，加入 violated dynamic subset-row cuts；
- 两者都只跑 `max_nodes=3`、`max_cg_iterations=12`、外部 `120s`。

这不是最终性能实验，只用于判断 greedy-anchor 是否存在明显 SRC violation，以及 cut-on 是否能早期抬高 RMP relaxation。

## 配置

共同配置：

```text
config = BPC_future/configs/moon_trek_20_smoke.yaml
instance = tasks020_04_seed61311
time_limit = 120
max_nodes = 3
journey_max_nodes = 3
max_cg_iterations = 12
journey_max_cg_iterations = 12
journey_dynamic_subset_row_cut_budget = 600
journey_dynamic_subset_row_max_depth = 1
journey_dynamic_subset_row_max_rounds = 2
journey_dynamic_subset_row_max_subset_size = 6
journey_dynamic_subset_row_audit_top_n = 20
```

V731:

```text
journey_dynamic_subset_row_audit_enabled = True
journey_dynamic_subset_row_cuts_enabled = False
```

V732:

```text
journey_dynamic_subset_row_audit_enabled = True
journey_dynamic_subset_row_cuts_enabled = True
journey_dynamic_subset_row_max_added = 20
```

## 结果

| run | status | wall | solving_time | RMP solves | pricing | columns | cuts_added | subset_row_added | primal | exact dual |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| V731 audit-only | TIME_LIMIT | 26.895 | 5.882 | 12 | 12 | 276 | 1 | 0 | 580.206609 | unavailable |
| V732 cut-on | TIME_LIMIT | 6.305 | 4.568 | 12 | 11 | 272 | 9 | 8 | 580.206609 | unavailable |

`cuts_added=1` 是 fleet lower-bound cut；V732 额外加了 8 条 dynamic subset-row cuts。

## SRC 候选

V731 audit-only：

```text
cg_iter=1: generated=601, violated=0
cg_iter=2: generated=601, violated=8, best_violation=0.333333333
```

Top candidates：

```text
[3,8,10], k=2, rhs=1.0, violation=0.333333333, compactness=18.599668014
[5,10,14], k=2, rhs=1.0, violation=0.166666667, compactness=22.982320931
[10,13,19], k=2, rhs=1.0, violation=0.083333333, compactness=15.390573597
```

V732 cut-on 在 `cg_iter=2` 加入了这 8 条 SRC：

```text
[3,8,10]
[5,10,14]
[10,13,19]
[4,10,12]
[4,10,19]
[10,12,19]
[4,10,13]
[10,12,13]
```

## RMP Objective 信号

同样 12 轮 CG 下：

```text
V731 audit-only:
  iter 10 = 585.677505
  iter 11 = 569.685128
  iter 12 = 551.780755

V732 cut-on:
  iter 10 = 589.095879
  iter 11 = 585.677505
  iter 12 = 568.270994
```

V732 在 iter12 的 RMP objective 比 V731 高 `16.490239`。这不是 official node bound，因为两者都没有 exact pricing closure；但它是一个有用的 formulation 信号：dynamic SRC 能在 greedy-anchor 的早期 relaxation 上产生明显收紧。

## 判断

这轮结果支持 V729 的方向调整：

1. greedy-anchor 不是单纯缺 branch positive；它确实存在可利用的 subset-row violation。
2. dynamic SRC cut-on 能早期抬高 RMP objective，方向上对 `z_RMP < UB` 的 proof bottleneck 是相关的。
3. 还不能宣称加速或证明改善，因为本轮没有 exact dual bound，也没有跑到 final closure。

## 下一步

1. 对 seed61311/seed61635 做 `audit-only vs cut-on` 600s hard2 A/B：
   - RouteOpt/BKF branch controller 保持一致；
   - admission 不混入；
   - 记录 exact closure、dual bound、gap、fathom count、CB retry。
2. 如果 hard2 有正信号，再扩到 greedy-anchor family；如果小规模退化，需要加 cut gate：
   - `violated >= threshold`
   - `best_violation >= threshold`
   - `top SRC compactness / repeated task hub` 稳定
3. 继续保持 exact-safe：SRC 只通过 RMP coefficient 和 pricing reduced-cost updater 生效，不能替代 exhaustive exact pricing certificate。

## 验证

已完成：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/scripts/summarize_journey_paired_probe_runbook.py \
  BPC_future/tests/test_journey_paired_probe_summary.py
```

并完成 `very_small` 轻量函数验证：

```text
added=0
cuts=0
violated=1
best_violation=0.2
top0=[1,2,3], k=2
```
