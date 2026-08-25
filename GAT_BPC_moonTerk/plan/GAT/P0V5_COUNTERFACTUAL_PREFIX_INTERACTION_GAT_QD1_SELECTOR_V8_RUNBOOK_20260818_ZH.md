# P0V5 Counterfactual-Prefix Interaction-GAT QD1 Selector V8 运行手册

## 启动与阶段 A

```bash
cmake --build build/native-spprc-counterfactual-prefix-v8 -j2
ctest --test-dir build/native-spprc-counterfactual-prefix-v8 --output-on-failure
PYTHONPATH=build/native-spprc-counterfactual-prefix-v8:src pytest -q \
  tests/test_p0v5_counterfactual_prefix_gat_qd1_selector_v8.py \
  tests/test_p0v5_native_frontier_gat_qd1_selector_v7.py \
  tests/test_p0v5_proof_queue_gat.py
PYTHONPATH=build/native-spprc-counterfactual-prefix-v8:src \
  python scripts/initialize_p0v5_counterfactual_prefix_gat_qd1_selector_v8.py
```

初始化器只接受空 run root，校验 V7R3 terminal、38/228/38 计数、Native CTest、ABI、binary/engine/config hash，并把 pre-action snapshots 重绑定到 V8 engine。它不会导入 arm outcome 作为性能证据。

## Representation development

每次只运行一个或少量 prefix task，支持只读恢复：

```bash
python scripts/run_p0v5_counterfactual_representation_v8.py collect --task-limit 1
python scripts/run_p0v5_counterfactual_representation_v8.py materialize
python scripts/train_p0v5_counterfactual_representation_v8.py
```

`collect` 共 76 个 task（38 context × Q0/QD1 prefix）。已有完整 canonical artifact 会复用；不完整 artifact 不会自动删除或覆盖。`materialize` 产生 128/512/2048 三个预算的 114 个 triplet。trainer 使用 instance-grouped 五折 OOF 和独立 GAT/MLP/Linear/no-message/shuffled-topology controls。

若 `state.json.terminal=true`，必须停止。若 representation 通过，状态进入 `PILOT_CENSUS`，随后才可冻结全新 pilot census；V7R3 数据仍无性能授权。

## 审计要点

- 每次恢复前执行 `verify_freezes(run_root)`。
- `prefix.exact` 必须为 false，routes/certificate 必须为空。
- Q0/QD1 prefix 的 `base_graph_hash` 必须相同。
- small-scale/tree 的 manifest/probe/graph/model counters 必须为零。
- terminal 后任何 writer 报错是预期行为，不能以新目录复制失败数据继续同一证据链。
