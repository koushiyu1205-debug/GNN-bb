# P0V5 Residual-GAT Coverage-Repair V5 实施与运行说明

日期：2026-08-16

## 1. 状态边界

V5 是独立证据链，run root 固定为：

```text
runs/p0v5_residual_gat_censor_aware_selector_v5_20260816/
```

V4 的 `FAIL / INSUFFICIENT_FRESH_ROOT_COVERAGE` 保持只读。V5 只修复
scale30 selector-heldout 从 `1/4` 到 `4/4` 的 candidate census，不改变
Native、exact engine、Q0/QD1/QGR1 comparator、Interaction-GAT 架构、训练门槛或
runtime 行为。runtime policy 继续是
`P0V5_ROOT_INTERACTION_GAT_SELECTOR_V4`，不制造语义相同的新 policy ID。

V5 的候选仍是 development-only。生产默认仍为
`no_cut + P0V4/P0V5 Exact + Q0`。scale5/10/20 和全部 tree requests 继续使用
V4 runtime 的 manifest/graph/Torch 前 literal-Q0 bypass。

## 2. 两层冻结

### 2.1 Bootstrap freeze

`initialize_p0v5_residual_gat_coverage_repair_v5.py` 在任何新 candidate screen
前完成以下校验和冻结：

- V4 terminal、source freeze、prearm registry 和 500-case differential 的固定
  SHA256；
- Native engine `3a2c89d88ca5b431` 和 binary SHA256；
- V4 frozen source、exact config、Native binary 和 differential 未漂移；
- V4 尚未生成 performance freeze、QD1/QGR1/selector outcome；
- 42 个 fixed instances、94 个 fixed snapshots；
- 1 个 scale30 和 4 个 scale50 eligible candidate instances，共 11 snapshots；
- 3 个 scale30 zero-context candidates 只保留为 screened-ineligible；
- 所有 snapshot 都是 official/exact/root-CG/literal-Q0、无 label drop、绑定完整且
  不含 outcome/winner/ratio/selected-action 字段；
- formal/protected content hash 无重叠。

105 个 V4 Q0-only snapshots 以内容哈希校验后复制到 V5 run root。V4 原 artifact
不被修改或重绑。bootstrap registry 同时冻结 V5 config、initializer、census
manager、generator、专项测试和本文档的源码哈希。

初始化命令：

```bash
python scripts/initialize_p0v5_residual_gat_coverage_repair_v5.py
```

### 2.2 Performance freeze

scale30 新 census 找到前三个 eligible instances 后，manager 立即停止生成并冻结：

- V4 导入的 fixed 14/4/3 instances；
- scale30 heldout：V4 已有 1 个 eligible + V5 首 3 个 eligible；
- scale50 heldout：V4 已有 4 个 eligible；
- 全部 context IDs、instance split、5-fold grouped CV、QGR1 calibration primary
  contexts 和 Q0 milestone schedule；
- V4 execution、threshold、acceptance 和 stop gates；
- 最终 immutable registry。

performance freeze 的 schema 保持 V4 downstream 所需接口。`context_weight` 始终为
`1 / instance_context_count`，每实例总权重为 1；同一实例不得跨 partition/fold。

## 3. Candidate census 执行

候选目录固定为：

```text
data/p0v5_residual_gat_censor_aware_selector_v5_candidates/
```

manager 使用 seed base `260816000`，只生成 scale30，最大接受并 screen 26 个新实例。
每次只把 generator target 增加一个 accepted index；生成成功后立即执行一次 literal-Q0
root collection，300 秒 cap，最多记录 3 个自然 root fallback snapshots。筛选只读取：

```text
accepted_instance_index
legal_snapshot_count >= 1
```

不会读取 wall、round、active-column density 或 arm outcome。选择顺序只按 accepted
instance index；找到前三个 eligible 后立即停止。单次调用可用 `--screen-limit` 控制
本轮最多新增的 screen 数，但不会改变最终选择。

```bash
# 查看当前状态，不写 artifact
python scripts/manage_p0v5_residual_gat_coverage_census_v5.py status

# 可恢复地持续运行，直至找到 3 个 eligible 或耗尽 26 个
python scripts/manage_p0v5_residual_gat_coverage_census_v5.py run

# 调试时一次只 screen 一个
python scripts/manage_p0v5_residual_gat_coverage_census_v5.py run --screen-limit 1
```

若第 26 个仍不能补齐，写入 immutable terminal：

```text
FAIL / INSUFFICIENT_SCALE30_HELDOUT_COVERAGE
```

此后所有 V5 writer fail closed。已生成但未被前三个 eligible 选中的实例只作为
reserve，不进入任何 partition。

## 4. Performance 阶段命令和边界

只有 performance freeze 成功后，才允许使用冻结的 V4 downstream 脚本，并始终传入
V5 run root：

```bash
V5_RUN=runs/p0v5_residual_gat_censor_aware_selector_v5_20260816

python scripts/run_p0v5_residual_gat_matrix_v4.py milestone --run-root "$V5_RUN"
python scripts/run_p0v5_residual_gat_matrix_v4.py matrix --run-root "$V5_RUN"
```

milestone 阶段先对 train+calibration 运行 trace-off Q0 screen；未达到 milestone、
resource-censored 或 label-drop context 写为 `REPLAY_INELIGIBLE`，不会产生非 Q0
task。只有 eligible train contexts 会额外采集 telemetry-only literal-Q0 reservoir
trace，该次 wall 不具性能授权。matrix 仍采用 Q0/QD1、3 blocked fresh repeats、每
block 重跑 Q0、state-hash 轮转、scale30/50 为 300/600 秒、10.867 GiB、单 Native
process。

如果 QD1 gate 通过，后续依次使用 V4 已冻结的 QGR1 trainer/force-on、portfolio
finalizer、Interaction-GAT trainer、heldout 和 full-BPC runner。任何阶段都不得因为
V5 census 修复而改变 V4 的 admission、oracle、GAT-vs-controls、heldout、E2E 或 formal
门槛。

## 5. 审计与测试

冻结前运行：

```bash
python -m py_compile \
  scripts/p0v5_residual_gat_coverage_repair_v5_common.py \
  scripts/initialize_p0v5_residual_gat_coverage_repair_v5.py \
  scripts/manage_p0v5_residual_gat_coverage_census_v5.py

pytest -q tests/test_p0v5_residual_gat_coverage_repair_v5.py
pytest -q tests/test_p0v5_residual_gat_censor_aware_selector_v4.py
ctest --test-dir build/native-spprc-residual-gat-v4 --output-on-failure
git diff --check
```

V5 专项测试覆盖真实 V4 import 数量、zero-context 排除、accepted-index 确定性、26 个
耗尽边界、instance weight、partition 隔离、terminal writer guard，以及 engine、
runtime 和 development-only 约束。原 V4 测试继续覆盖 reservoir、censor collapse、
runtime fail-closed、小规模/tree bypass、GAT/controls 和 QGR1 veto。

## 6. 合法停止语义

Coverage 阶段只存在三个合法结果：

1. `CONTINUE`：尚未补齐且尚未耗尽，不能写 terminal；
2. `READY`：首三个 V5 eligible 已确定，立即冻结 4-instance/scale heldout；
3. `EXHAUSTED`：26 个全部 screen 后仍不足，写 coverage terminal。

进入 performance 阶段后沿用 V4 的 correctness、QD1、QGR1、portfolio、GAT、heldout、
E2E 和 formal terminal 边界。任一 negative terminal 都是本研究链的合法结论，不能改用
MLP/Linear、降低 heldout 数量、引入 tree supplement 或修改阈值把失败改写为成功。
