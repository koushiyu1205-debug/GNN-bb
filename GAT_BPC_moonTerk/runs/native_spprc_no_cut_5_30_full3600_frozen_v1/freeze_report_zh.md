# FROZEN_NATIVE_NO_CUT_BASELINE_V1 冻结报告

冻结完成时间：2026-07-22 14:10（Asia/Shanghai）

## 结论

本目录已经成为 Native Live SRI BPC V1 的正式 no-cut control 锚点。全量
5/10/20/30 共 80 个 strict cold-start 实例全部精确闭合，全部通过 no-cheat、engine
binding、manual/pricing reduced-cost 和 certificate redline 审计；四个规模的历史恢复门槛
全部通过。

后续 paired benchmark 必须按本目录冻结的算法语义重新运行 control，不能直接把本次单次
wall-clock 当作 paired control 样本。

## 冻结绑定

- freeze ID：`FROZEN_NATIVE_NO_CUT_BASELINE_V1`
- Git commit：`ee2f853c003589cb717399209fe232dc793a854b`
- Native in-process engine：`66ab52c9b33b4551`
- Native module SHA-256：`61ab915afd4d55f3791e2971c3ab3833b4d88419fdbd26f3cd0afe123cf85f63`
- 冻结 YAML SHA-256：`beef1cf0c5f20fffff35fb87c06826926f2d15fc62294237d7ba5007af9a9f1a`
- Python：`/home/kai/miniconda3/bin/python`，3.13.13
- CMake：3.28.3
- C++ compiler：Ubuntu GCC 13.3.0
- CMake build type：`RelWithDebInfo`

冻结算法为 HiGHS restricted master、Native exact in-process SPPRC、Ryan–Foster
branching、visited-subset dominance、30 规模 adaptive sparse harvest 2 秒 cap；completion
bound、native cut state 和 live master cuts 均关闭。

## 全量结果

| 规模 | exact/no-cheat | mean | p50 | max | mean/历史 | p50/历史 | 恢复 gate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 20/20 | 0.395952s | 0.393683s | 0.438152s | 0.9745 | 0.9684 | PASS |
| 10 | 20/20 | 0.820660s | 0.754397s | 1.265936s | 0.9900 | 0.9902 | PASS |
| 20 | 20/20 | 32.352003s | 18.391300s | 129.718720s | 1.0379 | 1.0421 | PASS |
| 30 | 20/20 | 493.045466s | 346.038290s | 1736.858789s | 1.0862 | 1.0563 | PASS |

80 条树证书均满足 `incumbent_objective == global_lower_bound`（容差 `5e-6`），且 scope
均为 `BPC_TREE_OPTIMAL`。实例 JSON 内的 `reference_solution` 全部标记为
`exact_status=NOT_SOLVED`，因此它们只是构造性可行参考，不被误当作 exact objective
oracle；本次 objective 一致性由每例正式树级上下界闭合审计给出。

## 证据文件

- `baseline_freeze_manifest.json`：commit、工作树、80 个 instance hash、binary/build、
  Python/硬件与依赖快照；
- `baseline_summary.json`：80 行 JSON 与按规模 gate；
- `baseline_rows.csv`：逐例扁平审计；
- `resource_heartbeat.csv`：运行期间每 60 秒的进程树 RSS、available memory、swap、磁盘；
- `rows/`：每例新进程、`--no-resume` 的 launcher、RMP/pricing/tree 原始证据；
- `frozen_config.yaml`：正式冻结配置；
- `run_frozen_baseline.py`：串行 cold-start、资源保护和聚合逻辑。

`pip freeze` 因本环境中一个第三方 distribution 的 Version metadata 为 `None` 而返回 2；
原始错误栈完整保存在 manifest。为避免丢失依赖证据，manifest 同时保存了通过
`importlib.metadata` 生成的排序包清单，且该 fallback 成功返回 0。该问题未在基线期间修复，
也未更新任何依赖。

## 冻结边界

本冻结只认证 no-cut Native Branch-and-Price。它不认证 live SRI、Phase-I+cut、node cut
lineage、cut-aware certificate 或 cut 性能。Live SRI 仍须完成 readiness、分层 pilot 和 fresh
paired promotion；在 promotion 通过前，默认生产策略保持 no-cut。
