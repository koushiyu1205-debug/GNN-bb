# P0V5 Native-Frontier Interaction-GAT QD1 Selector V7 运行手册

所有命令从项目根目录执行。不得并行运行 Native task，不得跳过 state gate。

## 1. 构建和初始化

```bash
cmake -S native/lunar_spprc -B build/native-spprc-frontier-gat-v7 -DCMAKE_BUILD_TYPE=Release
cmake --build build/native-spprc-frontier-gat-v7 -j2
ctest --test-dir build/native-spprc-frontier-gat-v7 --output-on-failure
PYTHONPATH=build/native-spprc-frontier-gat-v7:src \
  pytest -q tests/test_p0v5_native_frontier_gat_qd1_selector_v7.py
python scripts/initialize_p0v5_native_frontier_gat_qd1_selector_v7.py
```

初始化只建立 bootstrap freeze 和 `READY/PROBE_DIAGNOSTIC`，不会生成性能结论。

## 2. Probe overhead diagnostic

```bash
python scripts/run_p0v5_native_frontier_probe_matrix_v7.py diagnostic
```

它先冻结每个 context 的 Q0 milestone，再运行 literal Q0/QPF0 三重复。失败写 `FRONTIER_PROBE_OVERHEAD_FAILED` 并终止。

## 3. Fresh pilot

候选 census 可分批恢复：

```bash
python scripts/manage_p0v5_native_frontier_gat_corpus_v7.py pilot --screen-limit 1
python scripts/manage_p0v5_native_frontier_gat_corpus_v7.py pilot
python scripts/run_p0v5_native_frontier_probe_matrix_v7.py pilot
```

首个命令用于安全试跑一个候选；达到每规模 8 个 eligible instance 后自动冻结 pilot corpus。pilot 不通过时写 `NO_FRONTIER_SWITCH_HEADROOM`。

## 4. Fresh main corpus 和 matched matrix

```bash
python scripts/manage_p0v5_native_frontier_gat_corpus_v7.py main --screen-limit 1
python scripts/manage_p0v5_native_frontier_gat_corpus_v7.py main
python scripts/run_p0v5_native_frontier_probe_matrix_v7.py main
```

达到每规模 37 个 eligible instances 后冻结 20/8/6/3 split。main matrix 仅运行 train+calibration；heldout/E2E outcome 不会提前产生。

长矩阵可用 `--task-limit N` 分批运行；只有全部 frozen tasks 完成后才会 collapse 和 gate。

## 5. Dataset、五模型训练和 calibration

```bash
python scripts/build_p0v5_native_frontier_gat_dataset_v7.py
python scripts/train_p0v5_native_frontier_gat_selector_v7.py
```

训练器产生三 seed GAT、MLP、Linear、no-message 和 shuffled-topology 独立 checkpoint。只有 GAT 同时通过 safe threshold、simple-control advantage 和 topology contribution gate，才写 development candidate manifest 和 portable Native bundle。

## 6. 一次性 heldout

```bash
python scripts/run_p0v5_native_frontier_gat_heldout_v7.py
```

runner 先运行 Q0/QPF0、仅从 frontier graph 产生五模型 action 并冻结 action artifact，之后才运行 distinct QPD1 outcomes。失败后禁止改 seed、threshold、OOD 或第二名模型。

## 7. Development-E2E 和 formal full100

```bash
python scripts/run_p0v5_native_frontier_gat_full_bpc_v7.py development_e2e
python scripts/run_p0v5_native_frontier_gat_full_bpc_v7.py formal_full100
```

candidate side 通过 `run_lunar_ice_frontier_gat_acceptance_v7.py` 启动。bootstrap 在 solver 启动前校验 selected exact config 文件 SHA256；runtime 小规模/tree bypass 和 Native model/probe counters 进入最终审计。

## 8. 状态和恢复

```bash
python -m json.tool runs/p0v5_native_frontier_gat_qd1_selector_v7_20260817/state.json
```

raw task 文件存在时 runner 只读复用；partial output directory 无 canonical artifact 时必须先人工审计，不能静默覆盖。`terminal=true` 后所有 V7 writer 必须拒绝写入。

V7 是单机长实验。仅运行 fresh main replay 就可能需要数十小时，E2E/formal 还受 3600 秒预算约束；不要把“代码与 freeze 已完成”误写成“性能计划已完成”。

