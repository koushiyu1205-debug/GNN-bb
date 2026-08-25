# P0V5 Minimal Interaction-GAT QD1 Selector V6 实施与运行手册

## 1. 实施结论

V6 将 P0V5 queue-policy portfolio 缩减为 `Q0/QD1`，不再修补 QGR1，也不执行 QB1。正式候选是两层、两头、hidden 16 的 edge-aware Interaction-GAT；它在每个合法 `root_cg` V5 fallback context 上只决定是否把 literal Q0 request 改为 QD1 request。

本链不修改 Native、`State`、Q0/QD1 comparator 或 exact engine，继续绑定 V5 engine `3a2c89d88ca5b431`。QGR1/QB1 在 manifest 中永久 veto，V6 checkpoint 没有对应神经元，runtime 也不接受 ranker 字段。

## 2. 代码与证据边界

主要实现：

- `src/lunar_ice_bpc/guidance/interaction_gat_queue_v6.py`：一个 QD1 arm、三个输出 head 的 GAT 及四类独立 control。
- `src/lunar_ice_bpc/guidance/interaction_gat_queue_runtime_v6.py`：fail-closed、root-only、scale30/50-only runtime。
- `scripts/initialize_p0v5_minimal_interaction_gat_qd1_selector_v6.py`：验证并冻结 V5 QD1 evidence。
- `scripts/build_p0v5_minimal_interaction_gat_qd1_dataset_v6.py`：构造 action 前图特征、实例等权数据集和 train-only normalization/OOD。
- `scripts/train_p0v5_minimal_interaction_gat_qd1_selector_v6.py`：5-fold instance-grouped OOF、三 seed、按规模校准与 threshold 冻结。
- `scripts/run_p0v5_minimal_interaction_gat_qd1_heldout_v6.py`：一次性 heldout prediction、fresh matched Q0/QD1 与最终判定。
- `scripts/run_p0v5_minimal_interaction_gat_qd1_full_bpc_v6.py`：Development-E2E 和 formal full100。

V5 只读输入必须同时满足：terminal reason 正确、所有 artifact hash 正确、444 个 raw matched tasks、74 个 collapsed QD1 outcomes、heldout/E2E/formal 未暴露 outcome。任何不一致均写作 `V6_V5_EVIDENCE_IMPORT_DRIFT`，不得继续。

实际冻结证据中有一条 scale50 calibration outcome 是 Q0 完成而 QD1 三个 block 全部 censor；它已经是 determined adverse，ratio 为冻结 cap-based ratio。V6 不为这唯一一条记录建立不可校准的 resource head，而是保留审计字段并将它并入 adverse target。任何 selected-QD1 resource failure 在 heldout/E2E 仍直接判失败。

## 3. 运行顺序

在仓库根目录运行，Native Python 模块路径继续使用冻结 V5 build：

```bash
export PYTHONPATH=src:build/native-spprc-residual-gat-v4

python -m pytest tests/test_p0v5_minimal_interaction_gat_qd1_selector_v6.py -q
python scripts/initialize_p0v5_minimal_interaction_gat_qd1_selector_v6.py
python scripts/build_p0v5_minimal_interaction_gat_qd1_dataset_v6.py
python scripts/train_p0v5_minimal_interaction_gat_qd1_selector_v6.py
```

训练通过后才可一次性读取 heldout：

```bash
python scripts/run_p0v5_minimal_interaction_gat_qd1_heldout_v6.py predict
python scripts/run_p0v5_minimal_interaction_gat_qd1_heldout_v6.py milestone
python scripts/run_p0v5_minimal_interaction_gat_qd1_heldout_v6.py freeze
python scripts/run_p0v5_minimal_interaction_gat_qd1_heldout_v6.py run
```

只有 heldout gate 通过后才运行完整 BPC：

```bash
python scripts/run_p0v5_minimal_interaction_gat_qd1_full_bpc_v6.py development_e2e
python scripts/run_p0v5_minimal_interaction_gat_qd1_full_bpc_v6.py formal_full100
```

审计当前状态：

```bash
python scripts/finalize_p0v5_minimal_interaction_gat_qd1_v6.py
```

## 4. 强制安全语义

- scale5/10/20 和所有 tree request 在 manifest、构图和 Torch import 前返回同一个 Q0 request 对象。
- incoming policy 非 Q0、非 exact、非 official、非 V5 fallback、schema/hash/OOD/NaN/Inf 或 threshold 检查失败均返回同一个 Q0 对象。
- runtime 每次 request 重新决策，QD1 不继承到下一 request。
- GAT 只能更换 queue comparator；合法 label/route、dominance、bound、reduced cost、branch/cut、停止条件和 certificate 完全不变。
- candidate 永远是 `development_only=true`，本链不授权部署或 production switch。

## 5. 终止解释

V6 只允许 GAT 成为候选。若没有安全 calibration threshold、message passing 不优于 controls、heldout/E2E/formal 任一 gate 失败，写机器可读 negative terminal 并停止；不得改选 MLP/Linear、调 heldout threshold 或恢复 QGR1。V6 通过时也只能声明 `Interaction-GAT-gated QD1 queue-policy acceleration`。
