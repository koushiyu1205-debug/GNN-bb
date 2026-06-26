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

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | med Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission sch/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 60 | 0 | 0 | 60 | 3.00 | 3.00 | 2.05 | 2.05 | 2.51 | 15.98 | 16.03 | 0/0/60 | +0.00 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch only | 60 | 60 | 0 | 0 | 60 | 2.05 | 2.05 | 2.00 | 2.00 | 2.24 | 2.29 | 3.01 | 4/0/56 | +0.95 | +0.04 | 4/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0/0/0 | 0 |
| admission only | 60 | 60 | 0 | 0 | 60 | 2.05 | 2.05 | 2.00 | 2.00 | 2.24 | 2.35 | 2.93 | 4/0/56 | +0.95 | +0.08 | 4/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch + admission | 60 | 60 | 0 | 0 | 60 | 1.99 | 1.99 | 1.95 | 1.95 | 2.19 | 2.24 | 2.71 | 4/0/56 | +1.01 | +0.10 | 4/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

### tasks010

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | med Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission sch/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 60 | 0 | 0 | 60 | 6.14 | 6.14 | 3.21 | 3.21 | 10.50 | 23.13 | 45.63 | 0/0/60 | +0.00 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch only | 60 | 60 | 0 | 0 | 60 | 6.10 | 6.10 | 3.19 | 3.19 | 6.82 | 17.72 | 64.80 | 4/4/52 | +0.04 | +0.02 | 4/3 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 66 | 0/0/0 | 0 |
| admission only | 60 | 60 | 0 | 0 | 60 | 6.12 | 6.12 | 3.20 | 3.20 | 10.38 | 23.31 | 45.72 | 0/0/60 | +0.01 | +0.02 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch + admission | 60 | 60 | 0 | 0 | 60 | 6.07 | 6.07 | 3.22 | 3.22 | 6.85 | 17.76 | 64.73 | 4/4/52 | +0.06 | +0.01 | 4/3 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 66 | 0/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

### tasks020

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | med Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission sch/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 26 | 4 | 30 | 20 | 380.93 | 121.89 | 53.27 | 578.07 | 600.00 | 600.00 | 600.00 | 0/0/60 | +0.00 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch only | 60 | 28 | 5 | 27 | 19 | 367.96 | 128.62 | 54.11 | 501.00 | 600.00 | 600.00 | 600.00 | 13/7/40 | +12.98 | +0.00 | 8/6 | 7/6 | 5/2 | 0 | 3 | 1 | 0 | 0 | 0 | 602 | 0/0/0 | 0 |
| admission only | 60 | 26 | 4 | 30 | 19 | 381.17 | 122.30 | 53.54 | 578.17 | 600.00 | 600.00 | 600.00 | 0/8/52 | -0.24 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch + admission | 60 | 28 | 5 | 27 | 19 | 368.85 | 130.25 | 55.25 | 504.34 | 600.00 | 600.00 | 600.00 | 9/7/44 | +12.08 | +0.00 | 8/7 | 5/6 | 5/2 | 0 | 3 | 1 | 0 | 0 | 0 | 597 | 0/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

## Early Branch On：四配置对比

### tasks005

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | med Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission sch/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 60 | 0 | 0 | 60 | 2.00 | 2.00 | 1.97 | 1.97 | 2.11 | 2.16 | 2.73 | 0/0/60 | +0.00 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch only | 60 | 60 | 0 | 0 | 60 | 2.05 | 2.05 | 1.99 | 1.99 | 2.33 | 2.38 | 2.80 | 0/0/60 | -0.05 | -0.01 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0/0/0 | 0 |
| admission only | 60 | 60 | 0 | 0 | 60 | 2.06 | 2.06 | 2.03 | 2.03 | 2.23 | 2.35 | 2.91 | 0/0/60 | -0.06 | -0.01 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch + admission | 60 | 60 | 0 | 0 | 60 | 2.04 | 2.04 | 1.98 | 1.98 | 2.27 | 2.37 | 2.91 | 0/0/60 | -0.05 | +0.01 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

### tasks010

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | med Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission sch/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 60 | 0 | 0 | 60 | 6.18 | 6.18 | 3.23 | 3.23 | 9.60 | 23.70 | 46.25 | 0/0/60 | +0.00 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch only | 60 | 60 | 0 | 0 | 60 | 6.07 | 6.07 | 3.24 | 3.24 | 6.90 | 14.29 | 64.97 | 4/4/52 | +0.11 | -0.01 | 4/2 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0/0/0 | 0 |
| admission only | 60 | 60 | 0 | 0 | 60 | 6.20 | 6.20 | 3.27 | 3.27 | 9.61 | 23.54 | 46.28 | 0/0/60 | -0.02 | -0.02 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch + admission | 60 | 60 | 0 | 0 | 60 | 6.10 | 6.10 | 3.26 | 3.26 | 6.89 | 14.44 | 65.16 | 4/4/52 | +0.08 | -0.03 | 4/2 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

### tasks020

| config | rows | OPT | TL | EXT_TL | <=200 OPT | capped mean | OPT mean | OPT median | p50 | p90 | p95 | max | win/loss/tie vs baseline | mean Δ | med Δ | >5 imp/reg | >30 imp/reg | >100 imp/reg | TL->OPT | EXT->OPT | OPT->TL | OPT->EXT | early triggers | branch events | branch hits | admission sch/delay/release | exact bad |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 26 | 1 | 33 | 19 | 403.10 | 147.75 | 80.44 | 600.00 | 600.00 | 600.00 | 600.00 | 0/0/60 | +0.00 | +0.00 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch only | 60 | 30 | 1 | 29 | 22 | 362.92 | 132.30 | 85.27 | 394.58 | 600.00 | 600.00 | 600.00 | 11/11/38 | +40.17 | +0.00 | 11/10 | 10/4 | 9/2 | 0 | 4 | 0 | 0 | 0 | 0 | 593 | 0/0/0 | 0 |
| admission only | 60 | 25 | 1 | 34 | 19 | 403.62 | 130.81 | 77.33 | 600.00 | 600.00 | 600.00 | 600.00 | 4/5/51 | -0.53 | +0.00 | 0/2 | 0/0 | 0/0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0/0/0 | 0 |
| branch + admission | 60 | 30 | 1 | 29 | 22 | 361.46 | 130.03 | 84.11 | 380.78 | 600.00 | 600.00 | 600.00 | 11/10/39 | +41.64 | +0.00 | 11/9 | 11/4 | 9/2 | 0 | 4 | 0 | 0 | 0 | 0 | 602 | 0/0/0 | 0 |

说明：`mean Δ` 为相对同组 baseline 的 capped wall-time 改善，正数表示更快；TL 表示 solver 内部 `TIME_LIMIT`，EXT_TL 表示外部 600s 截断。

## Early Branch On vs Off

同一 scale/config 下，`mean Δ` 为 off capped time - on capped time，正数表示 early branch on 更快。

| scale | config | off mean | on mean | mean Δ | med Δ | OPT gain | OPT loss | >30 imp/reg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 5 | baseline | 3.00 | 2.00 | +1.00 | +0.06 | 0 | 0 | 0/0 |
| 5 | branch only | 2.05 | 2.05 | -0.00 | +0.01 | 0 | 0 | 0/0 |
| 5 | admission only | 2.05 | 2.06 | -0.01 | -0.01 | 0 | 0 | 0/0 |
| 5 | branch + admission | 1.99 | 2.04 | -0.05 | -0.03 | 0 | 0 | 0/0 |
| 10 | baseline | 6.14 | 6.18 | -0.04 | -0.03 | 0 | 0 | 0/0 |
| 10 | branch only | 6.10 | 6.07 | +0.03 | -0.04 | 0 | 0 | 0/0 |
| 10 | admission only | 6.12 | 6.20 | -0.07 | -0.06 | 0 | 0 | 0/0 |
| 10 | branch + admission | 6.07 | 6.10 | -0.03 | -0.07 | 0 | 0 | 0/0 |
| 20 | baseline | 380.93 | 403.10 | -22.16 | +0.00 | 3 | 3 | 7/11 |
| 20 | branch only | 367.96 | 362.92 | +5.03 | +0.00 | 4 | 2 | 9/10 |
| 20 | admission only | 381.17 | 403.62 | -22.45 | +0.00 | 2 | 3 | 7/11 |
| 20 | branch + admission | 368.85 | 361.46 | +7.39 | +0.00 | 4 | 2 | 10/10 |

early branch 在 5/10 上没有正确性问题，但差异基本是秒级。20 规模上，baseline/admission-only 打开 early branch 会变慢；branch score 打开后 early branch 才表现为互补。

## Branch Score 净效果

这里拆成两条：无 admission 时比较 `branch only - baseline`；有 admission 时比较 `branch + admission - admission only`。`mean Δ` 为前者相对后者的 capped wall-time 改善，正数表示 branch score 有收益。

| early | scale | no-admission mean Δ | no-admission OPT gain/loss | no-admission >30 imp/reg | with-admission mean Δ | with-admission OPT gain/loss | with-admission >30 imp/reg |
|---|---:|---:|---:|---:|---:|---:|---:|
| off | 5 | +0.95 | 0/0 | 0/0 | +0.06 | 0/0 | 0/0 |
| off | 10 | +0.04 | 0/0 | 0/0 | +0.05 | 0/0 | 0/0 |
| off | 20 | +12.98 | 3/1 | 7/6 | +12.32 | 3/1 | 7/6 |
| on | 5 | -0.05 | 0/0 | 0/0 | +0.01 | 0/0 | 0/0 |
| on | 10 | +0.11 | 0/0 | 0/0 | +0.10 | 0/0 | 0/0 |
| on | 20 | +40.17 | 4/0 | 10/4 | +42.16 | 5/0 | 11/4 |

结论：20 规模 branch score 是当前最清晰的正向组件。off 组从 380.93s 降到 367.96s；on 组从 403.10s 降到 362.92s，并把 OPTIMAL 数从 26 提到 30。

## Admission 净效果

这里拆成两条：无 branch score 时比较 `admission only - baseline`；有 branch score 时比较 `branch + admission - branch only`。

| early | scale | no-branch mean Δ | no-branch OPT gain/loss | no-branch >30 imp/reg | with-branch mean Δ | with-branch OPT gain/loss | with-branch >30 imp/reg |
|---|---:|---:|---:|---:|---:|---:|---:|
| off | 5 | +0.95 | 0/0 | 0/0 | +0.06 | 0/0 | 0/0 |
| off | 10 | +0.01 | 0/0 | 0/0 | +0.02 | 0/0 | 0/0 |
| off | 20 | -0.24 | 0/0 | 0/0 | -0.90 | 0/0 | 0/0 |
| on | 5 | -0.06 | 0/0 | 0/0 | +0.01 | 0/0 | 0/0 |
| on | 10 | -0.02 | 0/0 | 0/0 | -0.03 | 0/0 | 0/0 |
| on | 20 | -0.53 | 0/1 | 0/0 | +1.46 | 0/0 | 0/0 |

结论：admission alone 没有形成稳定收益。20 规模 off/on 的 admission only 都比对应 baseline 略慢；与 branch score 同开时，on 组只有约 1.46s 的均值改善，off 组反而略退。

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

## Early Branch 与 GAT 组件的关系

- 与 branch score：20 规模表现为互补。early branch 单独打开会让 baseline 从 380.93s 退到 403.10s；但配合 branch score 后，branch only 从 off 的 367.96s 进一步到 on 的 362.92s，branch+admission 从 368.85s 到 361.46s。
- 与 admission：没有看到稳定互补。admission only 在 off/on 两组都没有提升，说明当前 admission 调度不是 20 规模性能的主要瓶颈。
- 对小规模：5/10 都保持 60/60 OPTIMAL。early branch on 在小规模没有破坏 exactness，但部分配置有秒级退化，应继续作为 opt-in，而不是默认 canonical benchmark。

## 安全性和一致性验证

- driver log flag matrix issues: `none`，24 个 batch 的 `600s`、`max-workers=4`、dual anchor / learning pricing、early branch off/on、branch score、admission 开关和 score-map 路径均按矩阵出现。
- row count issues: `none`
- instance set issues within each `(early, scale)`: `none`
- optimal objective mismatches across the 8 groups of each scale: `none`
- exact_bad_count total: `0`
- early_branch_exact_boundary_bad_count total: `0`
- admission_exact_bad_count total: `0`

early branch on 组的审计没有发现把当前 RMP objective 当作 exact node bound 或 child exact lower bound 的违规记录；admission 组没有发现 exact pricing 被 delay/reject 的违规记录。也就是说，本轮结果可以按 exact-safe opt-in 实验解释。

## 最终判断

- 本轮消融完成了 2 × 3 × 4 × 60 的全量实验。
- 当前可保留的有效信号是：branch score 对 20 规模有明确收益，early branch 只有在 branch score 配合下才值得继续研究。
- admission scheduler 当前不应被视为主加速来源；后续如果继续保留，应重点查它为什么没有稳定减少 tail proof 时间。
- 20 规模 600s 内最佳仍只有 30/60 OPTIMAL，且 200s 内 OPTIMAL 只有 22/60，距离“所有 20 规模实例 200s 内最优”还有明显差距。下一步应优先把 full-open 加速路径抽成严格 replay 标签，继续训练 branch score 学完整闭环速度，而不是继续扩大 admission 小组件。

## 附：最佳配置

| scale | best early | best config | capped mean | OPT | <=200 OPT |
|---:|---|---|---:|---:|---:|
| 5 | off | branch + admission | 1.99 | 60 | 60 |
| 10 | on | branch only | 6.07 | 60 | 60 |
| 20 | on | branch + admission | 361.46 | 30 | 22 |
