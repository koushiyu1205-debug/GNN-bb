# BPC_future 随机时间窗 60-instance 5/10 规模 600s 当前回归报告

日期：2026-06-23

## 口径

用户指出“10 规模平均 5 秒”指的是随机时间窗 60-instance 数据，不是旧 `moon_trek_60` hard 20-instance 数据。

本次按同一口径复跑：

- 5 规模旧基线：`BPC_future/results/20260610_tasks5_ablation_no_gnn_baseline.csv`
- 10 规模旧基线：`BPC_future/results/20260610_tasks10_ablation_no_gnn_baseline.csv`
- 当前 5 规模：`BPC_future/results/20260623_current_full600_randomtw60_tasks5.csv`
- 当前 10 规模：`BPC_future/results/20260623_current_full600_randomtw60_tasks10.csv`

实例结构：

- 每个规模 60 个实例；
- 2 个地形：`apollo15_20km`、`tranquillitatis_balmer_like_20km`；
- 3 种时间窗模式：`greedy-anchor`、`random-wave`、`sector-wave`；
- 每个地形/时间窗模式 10 个实例。

运行方式：

- per-instance solver time limit：600s；
- batch runner：`BPC_future/scripts/run_bpc_future_external_timeout_batch.py`；
- config：
  - 5 规模：`BPC_future/configs/moon_trek_5_journey.yaml`
  - 10 规模：`BPC_future/configs/moon_trek_10_journey.yaml`
- 对比指标使用 CSV 中的内部 `solving_time`，不使用外层子进程 `wall_time`。外层 `wall_time` 含 Python/SCIP/torch 导入和单实例进程启动开销，不等价于旧基线的 solver time。

## 总体结果

| 规模 | 版本 | OPTIMAL | avg solving_time | median | p90 | p95 | max | sum |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 5 | 旧基线 | 60/60 | 0.321070s | 0.296889s | 0.371346s | 0.423329s | 0.854388s | 19.264211s |
| 5 | 当前 | 60/60 | 0.347385s | 0.314546s | 0.432270s | 0.469372s | 1.005447s | 20.843118s |
| 10 | 旧基线 | 60/60 | 5.030619s | 1.703567s | 9.196825s | 26.743378s | 52.723129s | 301.837122s |
| 10 | 当前 | 60/60 | 5.479933s | 1.876931s | 10.031230s | 28.400749s | 56.850713s | 328.795979s |

## 判断

5 规模没有正确性退化：60/60 OPTIMAL。时间有轻微上升：

- avg：+0.026315s；
- max：+0.151059s。

10 规模没有正确性退化：60/60 OPTIMAL。时间有轻微但可见退化：

- avg：+0.449314s，约 +8.9%；
- median：+0.173364s；
- max：+4.127584s；
- 所有实例仍在 600s 内最优。

这说明当前 global RC LB / frontier ledger / corrected-bound 审计改动没有把 5/10 随机时间窗基准打坏，但 10 规模已经有小幅 runtime tax。后续如果继续往 20 规模 proof tail 加功能，必须保持这些新逻辑默认 fail-closed 或 opt-in，避免让 5/10 的普通证书路径继续涨成本。

## 分组结果

### 5 规模

| 分组 | 旧 avg | 当前 avg | 旧 max | 当前 max |
|---|---:|---:|---:|---:|
| greedy-anchor | 0.331143s | 0.358407s | 0.434689s | 0.499670s |
| random-wave | 0.309502s | 0.331023s | 0.854388s | 1.005447s |
| sector-wave | 0.322565s | 0.352727s | 0.815842s | 0.953514s |
| apollo | 0.305050s | 0.326254s | 0.854388s | 1.005447s |
| tranq | 0.337090s | 0.368517s | 0.815842s | 0.953514s |

### 10 规模

| 分组 | 旧 avg | 当前 avg | 旧 max | 当前 max |
|---|---:|---:|---:|---:|
| greedy-anchor | 5.196276s | 5.733927s | 34.696029s | 37.375806s |
| random-wave | 6.582659s | 7.124590s | 52.723129s | 56.850713s |
| sector-wave | 3.312921s | 3.581282s | 26.743378s | 28.400749s |
| apollo | 1.823866s | 1.970788s | 6.635623s | 7.189243s |
| tranq | 8.237371s | 8.989078s | 52.723129s | 56.850713s |

退化主要集中在 `tranquillitatis_balmer_like_20km`，尤其是 `random-wave` 和少数 `greedy-anchor` 长尾。`apollo` 基本仍是几秒级。

## 10 规模最大退化实例

| 实例 | 旧 | 当前 | delta |
|---|---:|---:|---:|
| `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_06_seed51521` | 52.723129s | 56.850713s | +4.127584s |
| `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_04_seed51316` | 47.644228s | 51.753196s | +4.108968s |
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_10_seed51929` | 34.696029s | 37.375806s | +2.679777s |
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_08_seed51725` | 17.917168s | 19.610095s | +1.692927s |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_09_seed51864` | 26.743378s | 28.400749s | +1.657371s |

## 对主线目标的含义

当前状态：

- 5/10 随机时间窗回归：通过 correctness gate；
- 10 规模平均仍接近用户记忆中的 5 秒水平，但当前不是完全无退化；
- 20 规模 200s 最优目标仍未证明，需要继续主攻 proof tail / late negative tail。

下一步建议：

1. 把 10 规模长尾的新增耗时拆成：
   - learning prewarm / smoothing；
   - completion-bound final judge；
   - frontier/global RC LB 审计字段；
   - two-cycle small-budget gate；
   - logging/diagnostic overhead。
2. 继续保持 corrected-bound fathom 默认关闭，只用 audit/proof artifact。
3. 在修 20 规模前，用上述 5 个 10-scale 长尾实例做小型 guard set，防止 proof-tail 新改动继续扩大 5/10 runtime tax。

