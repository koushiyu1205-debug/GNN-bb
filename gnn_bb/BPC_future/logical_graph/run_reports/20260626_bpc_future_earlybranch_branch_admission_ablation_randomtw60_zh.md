# 20260626 Early Branch × Branch Score × Admission 消融报告

实验对象是 random-TW canonical 60-instance，在 5/10/20 三个规模上分别比较 early branch off/on 与四种 learning 配置。所有组统一外部时限 600s、batch 内 max-workers=4，dual anchor / learning pricing 始终打开。本轮不引入 cuts、Tier 1 refinement 或新的 incumbent heuristic，也没有改 solver 代码。

## 总体结论

- 24 个 batch 全部完成，所有 `(early_branch_state, scale, config)` 都是 60 行；同一 `(early_branch_state, scale)` 内四组实例集合一致。
- 5/10 规模所有配置均为 60/60 OPTIMAL，没有正确性退化；时间差主要在秒级。
- 20 规模最好的 capped mean 是 `early branch on + branch + admission`：361.46s，30/60 OPTIMAL，22/60 在 200s 内 OPTIMAL。
- 20 规模 `early branch on + branch only` 与 `early branch on + branch + admission` 接近：362.92s vs 361.46s，说明主要收益来自 branch score，admission 的独立贡献很小。
- Early branch 单独打开在 20 规模 baseline 上退化：off baseline 380.93s，on baseline 403.10s。它需要 branch score 配合才有收益。
- 20 规模目标 `所有实例 200s 内求到最优` 尚未达成；当前最佳也只有 22/60 个实例满足 `<=200s OPTIMAL`。

## Score Map 覆盖

| early | scale | score rows | covered instances | logs scanned | score min | score mean | score max |
|---|---:|---:|---:|---:|---:|---:|---:|
| off | 5 | 14 | 2 | 60 | 0.4493 | 0.4577 | 0.4690 |
| off | 10 | 899 | 11 | 60 | 0.4492 | 0.5009 | 0.5398 |
| off | 20 | 22062 | 42 | 60 | 0.5311 | 0.7942 | 0.9790 |
| on | 5 | 14 | 2 | 60 | 0.4492 | 0.4577 | 0.4690 |
| on | 10 | 893 | 11 | 60 | 0.4492 | 0.5007 | 0.5399 |
| on | 20 | 24553 | 51 | 60 | 0.5103 | 0.7719 | 0.9769 |

score map 覆盖在 20 规模明显更充分；5/10 规模覆盖少，分支本身很少成为瓶颈，因此 branch score 在小规模上的统计意义有限。当前日志聚合没有直接保存“baseline 选中 pair 与 score-map 改写后 pair 是否不同”的逐节点字段，所以报告使用 branch score hit event count 与 score-map coverage 作为实际使用强度指标；后续若要精确 selected-pair-changed count，需要在分支选择点额外记录 baseline pair、scored pair 与 changed 标志。

## Early Branch Off：四配置对比

### tasks005

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission events/scheduled/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 60 | 0 | 0 | 60 | 3.00 | 3.00 | 2.05 | 2.05 | 2.51 | 15.98 | 16.03 | 0/0/60 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0/0/0/0 | 0 |
| branch only | 60 | 60 | 0 | 0 | 60 | 2.05 | 2.05 | 2.00 | 2.00 | 2.24 | 2.29 | 3.01 | 4/0/56 | +0.95 | 4/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0/0/0/0 | 0 |
| admission only | 60 | 60 | 0 | 0 | 60 | 2.05 | 2.05 | 2.00 | 2.00 | 2.24 | 2.35 | 2.93 | 4/0/56 | +0.95 | 4/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 51/0/0/0 | 0 |
| branch + admission | 60 | 60 | 0 | 0 | 60 | 1.99 | 1.99 | 1.95 | 1.95 | 2.19 | 2.24 | 2.71 | 4/0/56 | +1.01 | 4/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 51/0/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

### tasks010

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission events/scheduled/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 60 | 0 | 0 | 60 | 6.14 | 6.14 | 3.21 | 3.21 | 10.50 | 23.13 | 45.63 | 0/0/60 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0/0/0/0 | 0 |
| branch only | 60 | 60 | 0 | 0 | 60 | 6.10 | 6.10 | 3.19 | 3.19 | 6.82 | 17.72 | 64.80 | 4/4/52 | +0.04 | 4/3 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 66 | 66 | 0/0/0/0 | 0 |
| admission only | 60 | 60 | 0 | 0 | 60 | 6.12 | 6.12 | 3.20 | 3.20 | 10.38 | 23.31 | 45.72 | 0/0/60 | +0.01 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 175/1/0/0 | 0 |
| branch + admission | 60 | 60 | 0 | 0 | 60 | 6.07 | 6.07 | 3.22 | 3.22 | 6.85 | 17.76 | 64.73 | 4/4/52 | +0.06 | 4/3 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 66 | 66 | 173/1/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

### tasks020

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission events/scheduled/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 26 | 4 | 30 | 20 | 380.93 | 121.89 | 53.27 | 578.07 | 600.00 | 600.00 | 600.00 | 0/0/60 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 661 | 0 | 0/0/0/0 | 0 |
| branch only | 60 | 28 | 5 | 27 | 19 | 367.96 | 128.62 | 54.11 | 501.00 | 600.00 | 600.00 | 600.00 | 13/7/40 | +12.98 | 8/6 | 7/6 | 5/2 | 0 | 3 | 1 | 0 | 0 | 602 | 602 | 0/0/0/0 | 0 |
| admission only | 60 | 26 | 4 | 30 | 19 | 381.17 | 122.30 | 53.54 | 578.17 | 600.00 | 600.00 | 600.00 | 0/8/52 | -0.24 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 654 | 0 | 1821/699/5/4 | 0 |
| branch + admission | 60 | 28 | 5 | 27 | 19 | 368.85 | 130.25 | 55.25 | 504.34 | 600.00 | 600.00 | 600.00 | 9/7/44 | +12.08 | 8/7 | 5/6 | 5/2 | 0 | 3 | 1 | 0 | 0 | 597 | 597 | 1812/673/4/4 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

## Early Branch On：四配置对比

### tasks005

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission events/scheduled/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 60 | 0 | 0 | 60 | 2.00 | 2.00 | 1.97 | 1.97 | 2.11 | 2.16 | 2.73 | 0/0/60 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0/0/0/0 | 0 |
| branch only | 60 | 60 | 0 | 0 | 60 | 2.05 | 2.05 | 1.99 | 1.99 | 2.33 | 2.38 | 2.80 | 0/0/60 | -0.05 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 0/0/0/0 | 0 |
| admission only | 60 | 60 | 0 | 0 | 60 | 2.06 | 2.06 | 2.03 | 2.03 | 2.23 | 2.35 | 2.91 | 0/0/60 | -0.06 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 51/0/0/0 | 0 |
| branch + admission | 60 | 60 | 0 | 0 | 60 | 2.04 | 2.04 | 1.98 | 1.98 | 2.27 | 2.37 | 2.91 | 0/0/60 | -0.05 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 51/0/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

### tasks010

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission events/scheduled/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 60 | 0 | 0 | 60 | 6.18 | 6.18 | 3.23 | 3.23 | 9.60 | 23.70 | 46.25 | 0/0/60 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 1 | 64 | 0 | 0/0/0/0 | 0 |
| branch only | 60 | 60 | 0 | 0 | 60 | 6.07 | 6.07 | 3.24 | 3.24 | 6.90 | 14.29 | 64.97 | 4/4/52 | +0.11 | 4/2 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 64 | 64 | 0/0/0/0 | 0 |
| admission only | 60 | 60 | 0 | 0 | 60 | 6.20 | 6.20 | 3.27 | 3.27 | 9.61 | 23.54 | 46.28 | 0/0/60 | -0.02 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 1 | 64 | 0 | 175/1/0/0 | 0 |
| branch + admission | 60 | 60 | 0 | 0 | 60 | 6.10 | 6.10 | 3.26 | 3.26 | 6.89 | 14.44 | 65.16 | 4/4/52 | +0.08 | 4/2 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 64 | 64 | 172/1/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

### tasks020

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission events/scheduled/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 26 | 1 | 33 | 19 | 403.10 | 147.75 | 80.44 | 600.00 | 600.00 | 600.00 | 600.00 | 0/0/60 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 133 | 729 | 0 | 0/0/0/0 | 0 |
| branch only | 60 | 30 | 1 | 29 | 22 | 362.92 | 132.30 | 85.27 | 394.58 | 600.00 | 600.00 | 600.00 | 11/11/38 | +40.17 | 11/10 | 10/4 | 9/2 | 0 | 4 | 0 | 0 | 126 | 593 | 593 | 0/0/0/0 | 0 |
| admission only | 60 | 25 | 1 | 34 | 19 | 403.62 | 130.81 | 77.33 | 600.00 | 600.00 | 600.00 | 600.00 | 4/5/51 | -0.53 | 0/2 | 0/0 | 0/0 | 0 | 0 | 0 | 1 | 133 | 734 | 0 | 1891/671/6/5 | 0 |
| branch + admission | 60 | 30 | 1 | 29 | 22 | 361.46 | 130.03 | 84.11 | 380.78 | 600.00 | 600.00 | 600.00 | 11/10/39 | +41.64 | 11/9 | 11/4 | 9/2 | 0 | 4 | 0 | 0 | 126 | 602 | 602 | 1869/668/4/3 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

## Early Branch On vs Off

同一 scale/config 下，`mean Δ` 为 off capped time - on capped time，正数表示 early branch on 更快。

| scale | config | off mean | on mean | mean Δ | med Δ | OPT gain | OPT loss | >30 imp/reg | early triggers off/on |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | baseline | 3.00 | 2.00 | +1.00 | +0.06 | 0 | 0 | 0/0 | 0/0 |
| 5 | branch only | 2.05 | 2.05 | -0.00 | +0.01 | 0 | 0 | 0/0 | 0/0 |
| 5 | admission only | 2.05 | 2.06 | -0.01 | -0.01 | 0 | 0 | 0/0 | 0/0 |
| 5 | branch + admission | 1.99 | 2.04 | -0.05 | -0.03 | 0 | 0 | 0/0 | 0/0 |
| 10 | baseline | 6.14 | 6.18 | -0.04 | -0.03 | 0 | 0 | 0/0 | 0/1 |
| 10 | branch only | 6.10 | 6.07 | +0.03 | -0.04 | 0 | 0 | 0/0 | 0/0 |
| 10 | admission only | 6.12 | 6.20 | -0.07 | -0.06 | 0 | 0 | 0/0 | 0/1 |
| 10 | branch + admission | 6.07 | 6.10 | -0.03 | -0.07 | 0 | 0 | 0/0 | 0/0 |
| 20 | baseline | 380.93 | 403.10 | -22.16 | +0.00 | 3 | 3 | 7/11 | 0/133 |
| 20 | branch only | 367.96 | 362.92 | +5.03 | +0.00 | 4 | 2 | 9/10 | 0/126 |
| 20 | admission only | 381.17 | 403.62 | -22.45 | +0.00 | 2 | 3 | 7/11 | 0/133 |
| 20 | branch + admission | 368.85 | 361.46 | +7.39 | +0.00 | 4 | 2 | 10/10 | 0/126 |

early branch 在 5/10 上没有正确性问题，但触发极少。20 规模上，baseline/admission-only 打开 early branch 会变慢；branch score 打开后 early branch 才表现为互补。

## Branch Score 净效果

这里拆成两条：无 admission 时比较 `branch only - baseline`；有 admission 时比较 `branch + admission - admission only`。`mean Δ` 为前者相对后者的 capped wall-time 改善，正数表示 branch score 有收益。

| early | scale | no-admission mean Δ | no-admission OPT gain/loss | no-admission >30 imp/reg | with-admission mean Δ | with-admission OPT gain/loss | with-admission >30 imp/reg | branch hit count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| off | 5 | +0.95 | 0/0 | 0/0 | +0.06 | 0/0 | 0/0 | 2/2 |
| off | 10 | +0.04 | 0/0 | 0/0 | +0.05 | 0/0 | 0/0 | 66/66 |
| off | 20 | +12.98 | 3/1 | 7/6 | +12.32 | 3/1 | 7/6 | 602/597 |
| on | 5 | -0.05 | 0/0 | 0/0 | +0.01 | 0/0 | 0/0 | 2/2 |
| on | 10 | +0.11 | 0/0 | 0/0 | +0.10 | 0/0 | 0/0 | 64/64 |
| on | 20 | +40.17 | 4/0 | 10/4 | +42.16 | 5/0 | 11/4 | 593/602 |

结论：20 规模 branch score 是当前最清晰的正向组件。off 组从 380.93s 降到 367.96s；on 组从 403.10s 降到 362.92s，并把 OPTIMAL 数从 26 提到 30。

## Admission 净效果

这里拆成两条：无 branch score 时比较 `admission only - baseline`；有 branch score 时比较 `branch + admission - branch only`。

| early | scale | no-branch mean Δ | no-branch OPT gain/loss | no-branch >30 imp/reg | with-branch mean Δ | with-branch OPT gain/loss | with-branch >30 imp/reg | admission events/scheduled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| off | 5 | +0.95 | 0/0 | 0/0 | +0.06 | 0/0 | 0/0 | 51/0 |
| off | 10 | +0.01 | 0/0 | 0/0 | +0.02 | 0/0 | 0/0 | 175/1 |
| off | 20 | -0.24 | 0/0 | 0/0 | -0.90 | 0/0 | 0/0 | 1821/699 |
| on | 5 | -0.06 | 0/0 | 0/0 | +0.01 | 0/0 | 0/0 | 51/0 |
| on | 10 | -0.02 | 0/0 | 0/0 | -0.03 | 0/0 | 0/0 | 175/1 |
| on | 20 | -0.53 | 0/1 | 0/0 | +1.46 | 0/0 | 0/0 | 1891/671 |

结论：admission scheduler 确实被调用，20 规模约有 1800-1900 个 admission 事件、约 670-700 个 scheduled 事件，但它没有形成稳定收益。它没有破坏 exact pricing，但对 tail proof 的主瓶颈帮助有限。

## Branch + Admission 协同效果

`actual` 是 branch+admission 相对 baseline 的实际 capped mean 改善；`additive` 是 branch-only 改善与 admission-only 改善的简单相加；`synergy = actual - additive`，正数表示组合优于线性相加。

| early | scale | branch Δ | admission Δ | actual combo Δ | additive | synergy |
|---|---:|---:|---:|---:|---:|---:|
| off | 5 | +0.95 | +0.95 | +1.01 | +1.89 | -0.89 |
| off | 10 | +0.04 | +0.01 | +0.06 | +0.05 | +0.01 |
| off | 20 | +12.98 | -0.24 | +12.08 | +12.74 | -0.66 |
| on | 5 | -0.05 | -0.06 | -0.05 | -0.11 | +0.07 |
| on | 10 | +0.11 | -0.02 | +0.08 | +0.09 | -0.01 |
| on | 20 | +40.17 | -0.53 | +41.64 | +39.65 | +1.99 |

20 规模的组合收益主要来自 branch score。on 组 combo 最好，但 admission 并没有显著扩大 OPTIMAL 数；它更像是小幅扰动而不是主因。

## 机制解释与问题定位

### 1. Dual anchor / learning pricing

本轮所有配置都打开 dual anchor / learning pricing，所以它不是消融变量。它的作用是用学习到的 task-cover dual anchor 改善启发式定价起点，让 root/节点 CG 更快找到真实负列。由于它固定打开，本轮结论不能说明 learning pricing 的绝对收益，只能说明在 learning pricing 已经打开的前提下，后续 branch score、admission、early branch 的增量效果。

### 2. Branch score

branch score 是本轮最有效组件，原因是 20 规模的主要瓶颈已经从“有没有负列”转为“分支后能不能更快闭环证明”。Ryan-Foster pair 选得好，会把任务关系切成两个更容易证明的 child；选得差，则会制造两个仍然很宽、仍然需要大量 pricing/final-probe 的 child。20 规模 score map 覆盖 42/60 到 51/60 个实例，branch score hit 约 600 次，正好覆盖了大量真正影响搜索树的分支点，所以能把 capped mean 明显降下来。

但 branch score 还没有解决全部问题：最佳配置仍有 30/60 个 600s 附近失败，p90/p95 仍为 600s。这说明当前 score 只改对了一部分关键分支，尚未稳定学到“哪个 pair 会让完整证明闭环最快”。

### 3. Early branch

early branch 的本质不是剪枝，也不是提高当前 RMP bound，而是在 CG 已经拖尾、继续找列收益低时，提前把节点拆成 child，让 exact closure 在更小的分支区域里完成。它保持 exact-safe：日志审计中 `exact_bound_available=False`、`child_lower_bound_exact=False` 没有违规，不能把 early branch 生成的当前 RMP objective 当 exact bound。

实验结果说明 early branch 的收益强依赖分支质量。20 规模 baseline/admission-only 中，early branch on 触发 133 次左右，但均值反而从 380.93s 退到 403.10s/403.62s；这表示如果 pair 还是 fractionality/default 口径，提前分支只是提前制造更多难 child。branch score 打开后，early trigger 降到 126 次，branch event 从 729/734 降到 593/602，均值降到 362.92s/361.46s，说明它在更合适的 pair 上提前切分，减少了一部分无效搜索。

### 4. Admission scheduler

admission scheduler 的作用是对已经通过真实 RC 验证的候选列做优先级/延迟调度，不能永久删除真实负列，也不能替代 exact pricing certificate。因此它主要影响“列进入 RMP 的顺序”，不直接决定 branch tree，也不直接提供 node proof。

本轮 admission 确实有事件：20 规模有约 1800-1900 个 admission 事件、约 670-700 个 scheduled 事件，但收益不稳定。原因大概率是当前 20 规模主瓶颈不再是候选列 flood，而是 branch proof tail 和 child closure；调度列顺序只能微调 CG 轨迹，不能改变核心分支结构。它没有 exact bad，说明安全性没问题，但性价比暂时不高。

### 5. 这个结果说明的问题

- 5/10 规模已经不是瓶颈，任何新组件都必须首先保证不回归。
- 20 规模失败主要集中在 tail：很多实例 capped 到 600s，最佳也只有 30/60 OPTIMAL。
- 当前最有价值的学习目标不是“找更多列”，而是“选哪个分支、什么时候提前分支、哪个 child 先证明”。
- early branch 不能全局裸开；没有高质量 branch score 时，它会把拖尾节点变成更多拖尾 child。
- admission 可以保留为安全组件，但不应继续作为主攻方向，除非后续证明某些实例仍是候选列调度瓶颈。

## 优化修改方向

1. 主攻 branch score：继续抽取 full-open 中 `TIME_LIMIT -> OPTIMAL`、`>100s 改善`、`>30s 改善` 的严格 replay 标签，同时把退化样本作为 hard negative。训练目标应从“是否 200s 内”改成连续 wall-time gain / child proof CPU / time-to-certificate。

2. 提升 branch score 覆盖和反事实质量：记录 baseline pair、scored pair、是否 changed、child corrected LB gain、child exact pricing events、child proof CPU、child fathom reason。没有 selected-pair-changed 字段，就很难判断 score 是真正改了决策还是只在已有候选上命中。

3. early branch 改成 score-gated opt-in：只在 CG unproductive、score map coverage 命中、top pair 分数足够高、child width/balance 不太差时触发。对无 score 或低置信度节点回退到正常 CG/final-probe。

4. admission 降级为辅助线：先保留安全审计和事件统计，不继续扩大复杂度。下一步只分析 admission scheduled 的那批列是否真的改变 active support / RMP objective / branch pair；如果没有，就只在 root CG 或候选爆炸场景启用。

5. 对剩余 20 规模 timeout 做失败分型：区分 `z_RMP < UB 无法 fathom`、`可 fathom 但 final probe 证书慢`、`branch tree 太宽`、`incumbent 不够好`。不同类型需要不同手段：branch score、incumbent heuristic、pricing-compatible cuts、completion-bound/Tier1 refinement 不能混着调。

6. 评价指标继续看平均和分布，不要只盯 200s 阈值。当前 branch score 把一些 600s 实例变成 200s 以上的 OPTIMAL，这是实际收益；但 p90/p95 仍为 600s，说明还需要专门攻最难尾部。

## 安全性和一致性验证

- driver log flag matrix issues: `none`，24 个 batch 的 `600s`、`max-workers=4`、dual anchor / learning pricing、early branch off/on、branch score、admission 开关和 score-map 路径均按矩阵出现。
- row count issues: `none`
- instance set issues within each `(early, scale)`: `none`
- optimal objective mismatches across the 8 groups of each scale: `none`
- early_exact_boundary_bad total: `0`
- admission_exact_bad total: `0`

early branch on 组的审计没有发现把当前 RMP objective 当作 exact node bound 或 child exact lower bound 的违规记录；admission 组没有发现 exact pricing 被 delay/reject 的违规记录。也就是说，本轮结果可以按 exact-safe opt-in 实验解释。

## 最终判断

- 本轮消融完成了 2 × 3 × 4 × 60 的全量实验。
- 当前可保留的有效信号是：branch score 对 20 规模有明确收益，early branch 只有在 branch score 配合下才值得继续研究。
- admission scheduler 当前不应被视为主加速来源；它安全但收益弱，下一步应先做作用路径诊断。
- 20 规模 600s 内最佳仍只有 30/60 OPTIMAL，且 200s 内 OPTIMAL 只有 22/60，距离“所有 20 规模实例 200s 内最优”还有明显差距。下一步应优先把 full-open 加速路径抽成严格 replay 标签，继续训练 branch score 学完整闭环速度。

## 附：最佳配置

| scale | best early | best config | capped mean | OPT | <=200 OPT |
|---:|---|---|---:|---:|---:|
| 5 | off | branch + admission | 1.99 | 60 | 60 |
| 10 | on | branch only | 6.07 | 60 | 60 |
| 20 | on | branch + admission | 361.46 | 30 | 22 |
