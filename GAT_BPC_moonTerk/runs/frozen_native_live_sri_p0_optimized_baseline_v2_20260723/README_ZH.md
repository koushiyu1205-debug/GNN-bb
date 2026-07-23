# 新冻结基准：Native Live SRI P0 Optimized Baseline V2

冻结编号：

`FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2`

这是后续 GAT 定价引导与 Ryan–Foster 分支候选排序实验的当前 control。它是当前优化后的精确 Native Branch-Price-and-Cut：

- HiGHS restricted master；
- Native exact SPPRC in-process；
- Ryan–Foster branching；
- root-only SRI-3；
- exact nonzero-dual pricing projection；
- SRI-3 2-bit、SRI-5 3-bit 的精确 packed overlap state；
- node-level cut separation 默认关闭；
- GAT 不参与 cut 选择。

## 冻结内容

- `baseline_freeze_manifest.json`：总入口；
- `frozen_config.yaml`：冻结配置副本；
- `native/lunar_spprc_native.cpython-313-x86_64-linux-gnu.so`：保留可直接按原模块名加载的冻结 Native binary；
- `candidate_freeze_manifest_snapshot.json`：132 个源码、配置、测试和 Native 文件的逐文件 SHA-256；
- `performance/`：2026-07-23 全量 5/10/20/30、每规模 20 例、P0/no-cut 各一次的结果快照。

## 性能边界

这次 160 个 slot 全部 exact、零 redline，但每实例每模式只有一次，因此：

- 可以作为后续 GAT 实验的新固定 control；
- 可以记录为当前最好单重复性能证据；
- 不能冒充原计划的 5/10 十次、20/30 三次正式 promotion。

| 规模 | 旧 no-cut mean / p50 | 新 P0 mean / p50 |
|---:|---:|---:|
| 5 | 0.395952 / 0.393683s | 0.389514 / 0.389853s |
| 10 | 0.820660 / 0.754397s | 0.808323 / 0.738066s |
| 20 | 32.352003 / 18.391300s | 24.104670 / 14.371486s |
| 30 | 493.045466 / 346.038290s | 371.514460 / 274.684953s |

这张表用于保留纵向版本记录，不是同轮 paired 因果比较。正式对比应使用 performance
snapshot 中同轮运行的 no-cut control。

## 旧基准仍然保留

旧基准没有被覆盖：

`runs/native_spprc_no_cut_5_30_full3600_frozen_v1/`

其冻结编号仍为：

`FROZEN_NATIVE_NO_CUT_BASELINE_V1`

后续实验的主要 control 使用本目录的新 P0 基准；旧 no-cut 基准用于纵向历史对照、回滚和复现实验。
