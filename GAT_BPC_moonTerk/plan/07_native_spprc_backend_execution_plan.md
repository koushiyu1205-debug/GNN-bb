# Native SPPRC/ESPPRC Backend 执行计划

## 1. 决策与当前状态

实施基线固定为 `48552b04c7bfc69ab95c0e2d664cbbe7c2ef206e`。依赖固定为
`lab-core/rcspp@2f1d53ba6806844e30ce43ee9c41041a5a1b4e79`。

默认决策是 pinned upstream + project-local C++/pybind extension。fork 只能是
feasibility/correctness evidence 和补丁生命周期的结论，不能是 spike 前提。当前 spike
证明 v1 可通过外部 exact 配置规避 pressure false-COMPLETE，因此 patch queue 为空，
`fork_required=false`。

当前 promotion 状态：

- Phase 0–8 已实现并通过 technical promotion；
- 5/10 differential、20-task 20/20 exact closure、30-instance001 和 001–005
  correctness/fail-closed contract 均已验证；
- `native_rcspp_inprocess` 可显式 opt-in，Python reference 仍是默认与 fallback；
- Phase 9 persistent host 已实现，scale50 已完成合法 incomplete/RSS gate，scale100
  实例与 bounded gate 仍在生成/执行；
- Phase 10 的 cut state、completion bound、visited-subset dominance 均有独立 feature flag；
- Phase 11 未通过：30-scale 004/005 仍会在 1800 秒边界合法 incomplete，尚不能默认切换。

完整实测证据见 `runs/native_spprc_implementation_report_zh.md`，upstream spike 见
`runs/native_spprc_feasibility_spike_report_zh.md`。

## 2. 构建与依赖

唯一 canonical build 是 standalone CMake tree，不和 scikit-build 隐式目录混用：

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
PROJECT_ROOT="$REPO_ROOT/GAT_BPC_moonTerk"
cd "$PROJECT_ROOT"

python3.13 -m venv .venv-native-spprc
. .venv-native-spprc/bin/activate
python -m pip install -U pip
python -m pip install cmake ninja pybind11 pytest numpy highspy
python -m pip install -e . --no-deps

PY_SITE="$(python -c 'import sysconfig; print(sysconfig.get_path("platlib"))')"
cmake -S native/lunar_spprc \
      -B build/native-spprc \
      -G Ninja \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DPython_EXECUTABLE="$(command -v python)" \
      -DLUNAR_SPPRC_PYTHON_INSTALL_DIR="$PY_SITE" \
      -DLUNAR_SPPRC_RCSPP_COMMIT="2f1d53ba6806844e30ce43ee9c41041a5a1b4e79"
cmake --build build/native-spprc --parallel 4
ctest --test-dir build/native-spprc --output-on-failure
cmake --install build/native-spprc
```

LFS 只在 checkout 实际包含 LFS 文件且本机有 git-lfs 时运行。patch manifest 位于
`third_party/patches/rcspp/manifest.json`；CTest 校验 pinned HEAD、每个 upstream blob
hash 和 `git apply --check`。

建立 fork 的触发条件保持为：production correctness patch 长期必需、30 天或一个
upstream release 未合入、相互依赖 core patches 超过 3 个，或需要独立发布 patched
binary/长期安全维护。即便建立 fork，也不默认使用 submodule。

## 3. Backend 与证明契约

统一入口为 `PricingBackend.solve(BackendPricingRequest) -> BackendResult`。registry 包含：

- `PythonReferenceBackend`；
- `NativeRcsppInprocessBackend`；
- `NativeRcsppHostBackend`（persistent spawn host、same-instance delta IPC、graph reuse、
  cancellation、RSS hard kill、stale build hash restart）。

`BackendResult` 分离：

- `best_found_rc`：已找到并审计的最好值；
- `global_min_rc/global_min_rc_is_exact`：只有精确全局值才填写；
- `proved_no_rc_below`：允许只证明阈值，不虚构正 RC 全局最小值；
- `unexplored_rc_lower_bound`、`search_exhaustive`、`frontier_empty`；
- `labels_dropped`、`partial_columns_valid` 和 `certificate_blockers`。

只有 exact global minimum 不低于阈值，或 exhaustive/frontier-empty 的 threshold proof，
才能进入 certificate audit。`labels_dropped=True` 无条件阻止证书。

TIMEOUT、MEMORY_LIMIT、INTERRUPTED 或异常只丢弃 proof state。已经完整传回并通过：

1. Python reconstruction；
2. physical feasibility；
3. branch/cut feasibility；
4. `manual_journey_reduced_cost()` true-dual audit；

的负列仍可加入 column pool。

## 4. 数学状态与能力边界

native label 使用 `double` 保存唯一原始加性分量：

```text
raw_operating_cost
raw_risk
raw_weighted_completion
task_dual_reward
cut_dual_reward       # v1 默认 = 0；Phase 10 flag 可启用
fleet_dual_applied
```

inner loop 不做六位 rounding。Python 重建 `JourneyColumn` 后执行现有 canonical rounding，
最终 RC 审计源仍是 `manual_journey_reduced_cost()`。epsilon 分离为：

- negative `1e-6`；
- dominance `1e-12`；
- resource `1e-9`；
- reconstruction `2e-6`。

branch context 只影响 label feasibility/terminal acceptance，不产生 branch dual；cut dual
只通过受支持的 cut coefficient 进入 RC。v1 默认 official native 只支持：

```text
BranchContext.empty
CutContext.empty
```

非空 context 返回 `UNSUPPORTED_FEATURE` 并走 Python exact fallback。subset-row 的
`floor(overlap/divisor)` threshold crossing、fleet coefficient 和 cut-aware state 已在
Phase 10 feature flag 下实现并通过 5-task differential，但 `native_cut_state_enabled`
默认关闭；Phase-I + 非空 cut 始终 fail closed。

cyclic multi-sortie 图强制：无 depot-depot 空 sortie、每个 sortie 至少访问一个新任务、
visited 在 recharge 后不清空、每个 cycle 的 visited cardinality 和 global time 严格增加、
`sortie_count <= visited_task_count`。

## 5. 六规模 runner

现有 `run_lunar_ice_b4_3_spprc_labeling.py` 保持 30-scale 固定语义。通用入口为：

- `scripts/run_lunar_ice_native_spprc_acceptance.py`；
- `configs/benchmarks/native_spprc_acceptance.yaml`；
- `NativeSpprcScaleProfile`。

| scale | worker/exact cap | NG schedule | harvest | row/worker sec | nominal RSS | backend/cache |
|---:|---:|---|---:|---:|---:|---|
| 5 | 5/5 | 3,5 | 8 | 120/10 | 2 GB | in-process/LRU 4 |
| 10 | 10/10 | 4,7,10 | 16 | 300/30 | 4 GB | in-process/LRU 2 |
| 20 | 20/20 | 6,10,14,20 | 32 | 900/90 | 8 GB | in-process/LRU 1 |
| 30 | 30/30 | 6,10,14,30 | 64 | 1800/180 | 16 GB | in-process/LRU 1 |
| 50 | 50/50 | 8,16,32,50 | 96 | 1800/300 | 24 GB | host/single graph |
| 100 | 100/100 | 10,20,40,70,100 | 128 | 1800/300 | 32 GB | host/single graph |

effective RSS 是 `min(nominal, 70% physical RAM)`。资源 preflight 不满足最低内存时返回
`RESOURCE_INSUFFICIENT`，不静默降低 exact 语义。proof 继承 row absolute deadline，预算
等于 row deadline 减实际 worker elapsed，不启动第二个完整时钟。v1 root gate 使用
exact-first，因此 worker actual elapsed 为 0。

## 6. 分阶段 gate

1. Phase 0：冻结 commit、hardware、config/instance/build hash 和 cold-start baseline；
2. Phase 1：只读 upstream spike 和 false-COMPLETE reproducer；
3. Phase 2：5-task empty branch/cut forward exact in-process；
4. Phase 3：5 full、10 representative differential 与 fail-closed；
5. Phase 4：registry、shadow、official opt-in，shadow 不改变任何 official state；
6. Phase 5：20-task exact closure/RC/certificate/performance/RSS；
7. Phase 6：只有 Phase 5 通过后运行 30-instance001 root proof ≤1800 秒；
8. Phase 7：30-scale 001–005 correctness 后才允许 technical opt-in promotion；
9. Phase 8：Ryan–Foster feasibility/terminal state 和 child differential；
10. Phase 9：persistent host、50/100 RSS guard/cancel/stale hash/round resume；
11. Phase 10：subset-row、fleet cut、completion bound、bucket、bidirectional 逐项 gate；
12. Phase 11：30-scale 20/20、每例 ≤1800、median ≤900 后才切默认。

当前 technical promotion 已通过，Phase 11 default release 未通过。PathWyse、DSSR、NG worker 在 v1
只可作候选列；未来只有模型表达、license 和 certificate differential 完成后才重评 exact
role。BALDES 只记录为构建、资源扩展和 certificate 适配尚未审计，不宣称 correctness defect。

## 7. 验收命令与 release boundary

```bash
ctest --test-dir build/native-spprc --output-on-failure
python -m pytest -q tests/native
python -m pytest -q tests/test_lunar_ice_labeling_pricer.py
python -m pytest -q tests/test_lunar_ice_smoke.py
python -m pytest -q

python scripts/run_lunar_ice_native_spprc_acceptance.py \
  --config configs/benchmarks/native_spprc_acceptance.yaml \
  --scales 5 10 20 \
  --backend native_rcspp_inprocess \
  --no-resume
```

Technical promotion 需要 5/10 differential、20 gate、30-instance001 ≤1800、001–005
correctness 和零 certificate leak。Default release 还需要 30-scale 20/20、median ≤900、
5/10/20 performance gate、50/100 bounded stability、Ryan–Foster child differential、
fallback/rollback/hash/resume 和许可证材料全部通过。
