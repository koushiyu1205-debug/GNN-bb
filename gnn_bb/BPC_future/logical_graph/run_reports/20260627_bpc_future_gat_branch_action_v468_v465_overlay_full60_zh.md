# 20260627 V468：V465 严格 replay 叠加后的 full-60 结果

## 结论

V468 在 random-TW canonical 20-scale 60 个实例上完成全量测试。它使用 V467 conservative overlay score map，只改变 Ryan-Foster branch ordering；early branch 和 admission 都保持关闭，因此学习组件不参与 official bound、certificate 或剪枝。

相对基线和 V464：

| config | OPT | TL | EXT_TL | <=200 OPT | capped mean | p50 | p90 | p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline 20260624 | 26 | 4 | 30 | 20 | 381.77 | 577.87 | 600.00 | 600.00 |
| V464 | 31 | 3 | 26 | 22 | 353.77 | 375.29 | 600.00 | 600.00 |
| V468 | 33 | 3 | 24 | 22 | 348.26 | 344.77 | 600.00 | 600.00 |

V468 是当前这一条 branch-score 主线里最好的 full-60 结果：

- 相对 baseline：`+7` 个 OPTIMAL，capped mean 降低 `33.51s`。
- 相对 V464：`+2` 个 OPTIMAL，capped mean 降低 `5.51s`。
- 相对 20260626 消融 best `early branch on + branch + admission`：`30/60 -> 33/60 OPTIMAL`，`361.46s -> 348.26s`。
- `OPTIMAL -> TIME_LIMIT/EXTERNAL`：0。

但最终目标仍未达成：V468 仍有 `27/60` 非最优实例，p90/p95 仍为 600s。

## V465 到 V468 的因果链

V465 对 V464 仍未 OPTIMAL 的实例做 root forced replay：

- 48 条 full replay 反事实。
- 2 条 strong positive：`EXTERNAL_TIME_LIMIT -> OPTIMAL`。
- 46 条 hard negative。
- 另有 1 条 `EXTERNAL_TIME_LIMIT -> TIME_LIMIT 403.7s`，但因为未到 OPTIMAL，在 strict overlay 中按 negative 处理。

两个新增强正例：

| instance | forced pair | V464 | forced replay | V468 |
|---|---|---:|---:|---:|
| apollo greedy seed61614 | `[4,19]` | EXTERNAL 600 | OPTIMAL 342.88 | OPTIMAL 340.47 |
| apollo random seed61408 | `[5,13]` | EXTERNAL 600 | OPTIMAL 473.07 | OPTIMAL 475.39 |

这两个强正例都在 V468 full-60 中复现，说明 strict replay 标签可以直接转化为真实 full-run 收益。

## V466 模型诊断

V465 标签合并后生成 V466 dataset：

- sample_count：188
- wall-time gain positive：51
- not-walltime-gain：125
- aux-only weak positive：12

V466 训练完成，但裸模型验证集很差：

- validation precision：0.077
- validation recall：0.111
- validation F1：0.091

因此没有直接使用 V466 checkpoint 裸分数。V467 使用 conservative overlay：

- base score rows：2255
- boost positive：10
- suppress negative：62
- positive overlay keys：12
- negative overlay keys：78
- boost score：0.74
- suppress score：0.05

这一步的关键判断是：模型泛化还不可靠，但严格 replay 证据可靠，所以只能把已证明的 pair 写入 opt-in score map。

## Gate 审计

V468 日志：

- `journey_branch_candidates`：603
- `journey_branch`：603
- `journey_fathom`：169
- `journey_tail_action_no_column_early_branch_gate`：897
- `journey_early_branch_trigger`：0

branch score selection gate：

- `ok`：8
- `score_below_min`：29
- `missing_score_source`：566

8 个通过 gate 的 root pair：

| instance | baseline pair | selected pair | score |
|---|---|---|---:|
| tranq greedy seed61001 | `[2,18]` | `[3,4]` | 0.74 |
| tranq greedy seed61414 | `[13,16]` | `[6,20]` | 0.74 |
| tranq greedy seed61103 | `[10,15]` | `[6,15]` | 0.74 |
| apollo greedy seed61614 | `[1,2]` | `[4,19]` | 0.74 |
| apollo greedy seed61000 | `[3,7]` | `[12,20]` | 0.74 |
| tranq random seed61411 | `[1,9]` | `[2,10]` | 0.74 |
| apollo random seed61408 | `[2,5]` | `[5,13]` | 0.74 |
| tranq sector seed61923 | `[1,13]` | `[13,20]` | 0.74 |

没有 early branch 触发；没有把 RMP objective 当 exact bound；没有学习组件参与剪枝。

## 相对 V464 的变化

V468 vs V464：

- `>5s` win/loss/tie：`2/1/57`
- `>30s` improve/regress：`2/0`
- `>100s` improve/regress：`2/0`
- `TIMEOUT -> OPTIMAL`：2
- `OPTIMAL -> TIMEOUT`：0

两个大收益正是 V465 新增强正例：

| instance | V464 | V468 | gain |
|---|---:|---:|---:|
| apollo greedy seed61614 | EXTERNAL 600.00 | OPTIMAL 340.47 | +259.53 |
| apollo random seed61408 | EXTERNAL 600.00 | OPTIMAL 475.39 | +124.61 |

唯一 `>5s` loss 是 apollo greedy seed61000：V464 `342.41s`，V468 `347.79s`，仍为 OPTIMAL，属于小幅运行时间波动，不是闭环退化。

## 剩余失败

V468 仍未 OPTIMAL 的 27 个实例包括：

- greedy/apollo：5 个 EXTERNAL，2 个 TIME_LIMIT
- greedy/tranq：5 个 EXTERNAL
- random/apollo：2 个 EXTERNAL，1 个 TIME_LIMIT
- random/tranq：4 个 EXTERNAL
- sector/apollo：4 个 EXTERNAL
- sector/tranq：5 个 EXTERNAL

这说明当前 branch score overlay 只能救已经找到强正例的少数 root context。剩余失败多数不是“同一类候选里再调一个分数”能解决，至少需要：

1. 对剩余失败做更聪明的反事实采样，而不是继续盲跑 positive-neighbor full replay。
2. 使用 child-probe / fixed-expansion probe 先筛候选，再把少数高希望 pair 做 full replay。
3. 对长期 600s 的 context 做失败分型：root pair 不足、深层分支不足、incumbent 不足、pricing-compatible cuts 需求、final-probe/CB tail。
4. 在 exact-safe score-gated early branch 上只测试已被 strict replay 证明的 pair，不裸开 early branch。

## 下一步建议

不要直接降低 gate 阈值。V466 裸模型验证很差，降低阈值会把未证实 pair 放进求解路径，风险高。

下一步应改采样策略：

- 对 V468 剩余 27 个非最优实例建立 child-probe runbook。
- 每个失败实例先用 6-10 个候选做短 fixed-expansion probe，筛出 child proof CPU / child safe-bound gain 最好的 1-2 个。
- 只对筛出的 pair 做 600s full replay。
- 新 strict positive 继续 overlay，hard negative 继续 suppress。

当前最可靠的结论是：strict replay evidence overlay 有效，但正例寻找效率仍低；要达到 60/60，必须提高反事实采样命中率，而不是单纯增加 full replay 数量。
