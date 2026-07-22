# 50/100 规模实例生成与 5×3600 秒主线试跑报告

生成与试跑日期：2026-07-17  
项目：`GAT_BPC_moonTerk`  
代码提交：`7267b1d823bb0e6b19ca444806fb8272646f1ca7`  
Native engine build hash：`ee0ea1fb74eb8035`  
Acceptance config hash：`f949b2d19ae56aba73b1dab032aa9a64d416a0cdfda188658510ca79a66d9394`

## 1. 结论

本次要求的实例生成和受控试跑均已完成：

- 50 规模实例：20/20 个，全部被生成器正式 acceptance 检查接受。
- 100 规模实例：20/20 个，全部被生成器正式 acceptance 检查接受。
- 50 规模主线试跑：前 5 个实例全部完成一条受控 cold-start 行。
- 100 规模主线试跑：前 5 个实例全部完成一条受控 cold-start 行。
- 10 条求解行全部在 3600 秒行上限以内结束，且 no-cheat 与 certificate redline 全部为 0。
- 10 条求解行均未证明最优；最终状态全部为 `BPC_INCOMPLETE_PRICING / INCOMPLETE_LIMIT`。
- 每条行的 native exact host 都触及 8 GiB 硬内存限额，最终 engine 状态为 `MEMORY_LIMIT`，blocker 为 `host_memory_limit`。
- 这些 `MEMORY_LIMIT` 是设计内的 fail-closed 退出，不是整机 OOM 或求解器崩溃；没有生成 no-negative certificate，也没有把不完整搜索误报为最优。

因此，本轮拿到的是 50/100 规模上当前主线的安全、可复现基线，不是 50/100 规模最优解时间。

## 2. 实例生成与完整性

统一 manifest：

`data/manifests/lunar_ice_sp50_real_benchmark_manifest.json`

Manifest 当前状态：

- `status = complete`
- `accepted_total_count = 120`
- `total_target_count = 120`
- 六个正式规模 5/10/20/30/50/100 均为 20 个 accepted 实例。
- 120 个 instance path 唯一，120 个 instance ID 唯一，且 manifest 中的 120 个路径均存在。
- 50 规模目标目录包含 20 个 `instance_*_logical_graph.json`，约占 973 MiB。
- 100 规模目标目录包含 20 个 `instance_*_logical_graph.json`，约占 3.7 GiB。

生成器对 accepted 实例执行的关键检查包括：

- `validate_instance()` schema/模型检查无问题；
- `validation.accepted = true`；
- task 数等于目标 scale；
- logical node 数等于 `scale + 1`；
- logical edge 数等于 `scale × (scale + 1)`；
- 每条 edge 恰有三个 path options；
- candidate roles 至少包含 `hotspot_edge` 和 `exploration`。

完成求解试跑后，又对这 40 个目标 JSON 串行执行了一次独立只读复验，重新调用项目自身的 `validate_instance()` 和生成器 `_acceptance_issues()`：

- `validated = 40`
- `bad = 0`
- 复验进程最大 RSS：612,436 KiB（约 598 MiB）
- swap 次数：0
- 文件系统输出：0

50 规模生成阶段记录的单进程最大 RSS 为 452.316 MiB；100 规模为 1386.633 MiB。

## 3. 本次使用的当前主线

入口为：

`scripts/run_lunar_ice_native_spprc_acceptance.py`

其正式求解子流程为：

`scripts/run_lunar_ice_b4_2_cold_exact.py`

本轮绑定：

- exact backend：`native_rcspp_host`
- root engine：`b2b_r3_worker`
- worker pricer：`relaxed_labeling`
- final judge policy：`harvest_then_proof`
- exact final judge：开启
- exact-proof subset dominance：开启
- completion bound：关闭
- native cut state：关闭
- live master cuts：关闭
- resume：关闭
- external mature pool：禁止
- manual columns：禁止
- external source probe：禁止
- threads：4

这是当前项目的 native SPPRC host 主线，但本轮十例都在 root exact pricing 阶段因内存限额 fail-closed，没有进入可证明完整的 B&B 树闭合。因此这批结果不能描述成已经完成了 50/100 规模的正式 branch-price-and-cut 最优求解；尤其本轮 `live_master_cuts = false`。

## 4. 资源保护策略

机器环境：

- 逻辑 CPU：20
- 物理内存：15.524 GiB
- swap：4 GiB

考虑到机器此前已经发生两次崩溃重启，本轮采用：

- 每例 row time limit：3600 秒；
- native host hard memory limit：8 GiB；
- 线程数：4；
- OpenMP 线程：4；
- OpenBLAS/MKL/NumExpr：各 1 线程；
- 50/100 均使用独立 host，host 退出后释放全部 label 内存；
- 不复用上次 checkpoint，不使用旧列池；
- 运行中持续检查 `free -h`、`ps` 和 `df -h`。

实际观测：

- native host 峰值均约为 8.00–8.02 GiB；
- 达限后由 host monitor 终止，host exit code 为 `-15`；
- 高峰时整机最低可用内存仍约 4.3–4.9 GiB；
- swap 始终约 2.3 MiB，没有交换风暴；
- 完成后可用内存恢复到约 12 GiB；
- 运行产物合计约 585 MiB；
- 完成时磁盘仍约有 823 GiB 可用；
- 最终没有遗留 acceptance runner、cold-exact、compact probe 或 native host 进程。

在正式试跑前还发现并终止了一个已运行约 13.5 小时的遗留实例生成进程树；只终止该生成树，没有清理其已有产物。终止后释放约 1 GiB RSS，为本轮求解留出安全余量。

## 5. 50 规模结果

统一统计：

- 5/5 行完成；
- exact closure：0/5；
- fail-closed：5/5；
- 3600 秒以内：5/5；
- 平均用时：440.744088 秒；
- p50：404.561351 秒；
- 最大用时：641.914692 秒；
- 外层总 wall time：2204.836870 秒；
- post-final-judge harvest 总计加入 38,002 列。

| 实例 | 总用时（秒） | Active columns | Final-judge rounds | Harvest 加入 | Host 峰值（GiB） | 最终状态 |
|---|---:|---:|---:|---:|---:|---|
| 001 | 404.561351 | 5,062 | 54 | 5,007 | 8.012 | `MEMORY_LIMIT` |
| 002 | 339.137098 | 7,785 | 83 | 7,731 | 8.000 | `MEMORY_LIMIT` |
| 003 | 413.698829 | 5,086 | 56 | 5,039 | 8.010 | `MEMORY_LIMIT` |
| 004 | 404.408468 | 8,179 | 86 | 8,124 | 8.000 | `MEMORY_LIMIT` |
| 005 | 641.914692 | 12,156 | 129 | 12,101 | 8.007 | `MEMORY_LIMIT` |

## 6. 100 规模结果

统一统计：

- 5/5 行完成；
- exact closure：0/5；
- fail-closed：5/5；
- 3600 秒以内：5/5；
- 平均用时：880.900929 秒；
- p50：860.160410 秒；
- 最大用时：1093.099068 秒；
- 外层总 wall time：4412.404509 秒；
- post-final-judge harvest 总计加入 87,444 列。

| 实例 | 总用时（秒） | Active columns | Final-judge rounds | Harvest 加入 | Host 峰值（GiB） | 最终状态 |
|---|---:|---:|---:|---:|---:|---|
| 001 | 752.263734 | 14,700 | 115 | 14,592 | 8.015 | `MEMORY_LIMIT` |
| 002 | 761.816769 | 14,464 | 115 | 14,356 | 8.006 | `MEMORY_LIMIT` |
| 003 | 860.160410 | 18,796 | 147 | 18,688 | 8.002 | `MEMORY_LIMIT` |
| 004 | 1093.099068 | 21,228 | 166 | 21,120 | 8.002 | `MEMORY_LIMIT` |
| 005 | 937.164663 | 18,796 | 147 | 18,688 | 8.001 | `MEMORY_LIMIT` |

## 7. Certificate 与正确性边界

十条行共同满足：

- `no_cheat_pass = true`
- `certificate_leak = 0`
- `manual_rc_fail = 0`
- `pricing_rc_fail = 0`
- `true_dual_rc_recompute_missing = 0`
- engine build hash 无漂移
- official certificate scope 为 `DIAGNOSTIC_PRICING_FRONTIER`
- `can_certify_no_negative = false`
- `search_exhaustive = false`
- `frontier_empty = false`
- `exact_certificate = false`

由于 host 在提交完整 BackendResult 前达到内存限额，本轮没有可保留的 partial native negative-column payload：

- `partial_columns_valid = false`
- `native_partial_negative_columns_retained = false`
- host proof state 已被丢弃

这不影响此前已加入 master 的、通过主线审计的 harvest 列，但该 pricing call 不能产生 no-negative proof，也不能形成 BPC 最优证书。

## 8. 当前卡点

本轮最直接的卡点不是 3600 秒时间上限，而是 exact native label frontier 的内存增长：

- 50 规模通常在 339–642 秒达到 8 GiB；
- 100 规模通常在 752–1093 秒达到 8 GiB；
- 因此即使把行限时从 1800 秒提高到 3600 秒，当前机器上也不会自动获得最优时间，因为搜索先撞到内存上限。

在这台 15.5 GiB 机器上继续简单提高 host memory limit 风险较大：VS Code 等常驻进程约占 1.5–2 GiB，若把 host 放到默认的约 10.9 GiB effective cap，系统安全余量会显著收窄。下一步若要追求 50/100 exact closure，应优先检查 label 数、dominance、frontier/bucket 表示和 completion bound，而不是仅继续放宽时间。

## 9. 主要产物

- 本轮配置：`runs/native_spprc_50_100_5x3600_20260717/acceptance_config.yaml`
- 50 外层汇总：`runs/native_spprc_50_100_5x3600_20260717/scale50_acceptance/native_spprc_acceptance_summary.json`
- 50 详细报告：`runs/native_spprc_50_100_5x3600_20260717/scale50_acceptance/scale_050/b4_2_cold_exact_full_report_zh.md`
- 100 外层汇总：`runs/native_spprc_50_100_5x3600_20260717/scale100_acceptance/native_spprc_acceptance_summary.json`
- 100 详细报告：`runs/native_spprc_50_100_5x3600_20260717/scale100_acceptance/scale_100/b4_2_cold_exact_full_report_zh.md`
- 50/100 每例 probe：对应 scale 目录下的 `pools/scale_*/instance_*/stage_001/probe.json`
