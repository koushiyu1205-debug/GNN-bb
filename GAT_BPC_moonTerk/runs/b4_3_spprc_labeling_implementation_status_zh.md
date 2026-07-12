# B4.3 SPPRC Labeling 实现状态

## 当前结论

B4.3 的 no-cheat cold-start runner、SPPRC pricing facade、RELAXED/EXACT 证书边界和 30-scale 001 探针已经接入，但 **B4.3 尚未验收**。

当前最稳定的正式配置仍无法在 30-scale instance 001 上给出 `BPC_TREE_OPTIMAL < 1800s`。失败不是 redline 或作弊边界问题，而是 exact elementary no-negative proof 覆盖能力不足。

## 已实现

- 新增正式模型入口：`scripts/run_lunar_ice_b4_3_spprc_labeling.py`。
- 新增稳定 SPPRC API：`SpprcPricingRequest -> SpprcPricingResult`。
- 新增 SPPRC facade：`src/lunar_ice_bpc/exact/bpc/pricing/spprc_pricer.py`。
- 保留两层语义：
  - `RELAXED_NG_WORKER`：candidate search only，不能发 no-negative 证书。
  - `EXACT_ELEMENTARY_PROOF`：唯一 official no-negative certificate 路径。
- root/tree/final judge 仍走 true-dual audit，worker/no-column 不允许 certify。
- B4.2 `(k,m)` partition ledger 在 B4.3 中不是 official certificate path。
- cold-start runner 记录并校验：
  - `config_hash`
  - `engine_build_hash`
  - `column_provenance`
  - `manual_rc_fail`
  - `pricing_rc_fail`
  - `certificate_leak`
- 新增 same-run checkpoint/orphan probe recovery，防止 stage subprocess timeout 后丢掉已落盘 probe。
- 新增 fixed config 的 stage 策略字段，当前正式默认保持 early/tail 都一轮一 checkpoint，避免长 stage 超时丢进度。

## 30-scale 001 关键探针

### 当前最稳定 B4.3 one-round checkpoint

目录：

`runs/b4_3_spprc_round1_tailadaptive64_30_001_1800s_20260712_221000/`

结果：

- `algorithm_status = BPC_INCOMPLETE_PRICING`
- `certificate_scope = DIAGNOSTIC_PRICING_FRONTIER`
- `pricing_state = INCOMPLETE_LIMIT`
- `cold_start_total_sec = 1801.86196`
- `root_cg_sec = 1794.368535`
- `root_pool_stage_count = 9`
- `root_pool_active_column_count = 6913`
- `manual_rc_fail = 0`
- `pricing_rc_fail = 0`
- `certificate_leak = 0`

解释：

stage 9 已经没有新增负列，但 final judge 只剩约 18 秒，coverage ledger 仍然 incomplete，不能升级为 no-negative certificate。

### early=16, tail=1 hybrid stage

目录：

`runs/b4_3_spprc_hybridstage_30_001_1800s_20260712_233000/`

结果：

- `cold_start_total_sec = 1807.974709`
- `root_pool_stage_count = 3`
- `root_pool_active_column_count = 6913`
- 仍有新增真实负列，未进入 no-negative proof。

解释：

减少了 early restart，但长 stage 在空 harvest/拖尾上耗时更大，整体不优。

### early=1, tail=2

目录：

`runs/b4_3_spprc_early1_tail2_30_001_1800s_20260713_000500/`

结果：

- `cold_start_total_sec = 1605.086711`
- `root_pool_stage_count = 7`
- `root_pool_active_column_count = 6467`
- stage 8 超时，未保存可恢复 probe。

解释：

tail=2 试图在同一 subprocess 里完成“最后一批列 + proof”，但超时前没有落盘，反而比 tail=1 差。因此正式默认已恢复为 tail=1。

## 当前瓶颈

当前 `SPPRC_ENGINE_SOURCE = internal_resource_label_core`，它还不是成熟高性能 C++ SPPRC/ESPPRC labeling engine。

实际 exact proof 仍通过 `price_full_universe_incremental_journey_columns` 做 Python 内部 full-subset elementary pricing。30-scale 的 proof space 太大，表现为：

- root stage 持续发现 true-dual negative columns；
- active column pool 到约 6913 后才接近无新列；
- no-negative proof 需要完整 coverage，但当前 final judge 常在 coverage incomplete 时耗尽预算；
- 长 stage 可以减少重启，但会丢 checkpoint 风险；
- 短 stage 能保进度，但反复重建/RMP/final judge 开销太大。

## 未完成验收项

- 30-scale instance 001 尚未 `BPC_TREE_OPTIMAL < 1800s`。
- selected 5 个 30-scale 尚未启动。
- full 30-scale 20/20 尚未启动。
- full 5/10/20 同 config regression 尚未启动。

## 下一步必须做

短期 stage 参数已经接近上限，继续调参不会解决根问题。下一步应实现真正的 high-performance SPPRC labeler：

- C++ sidecar 或等价 native extension；
- bidirectional / bucket labeling；
- ng-route + DSSR 只作 worker；
- exact elementary proof 使用 checkpointable frontier；
- dominance 状态包括 branch/cut/resource/visited-state；
- 每个 frontier shard 可以独立 checkpoint，timeout 后不丢覆盖状态；
- Python 只负责 RMP、true-dual RC audit、certificate gate。

只有当 exact proof frontier 能被 checkpoint 并高效推进，B4.3 才可能达到 full 30-scale `BPC_TREE_OPTIMAL < 1800s`。
