# P0V5 Exact / QG2 TinyGAT 交接文档

交接日期：2026-08-07

工作目录：`/home/kai/work/GAT_BPC_moonTerk`

Git 根目录：`/home/kai/work`

当前分支/HEAD：`main` / `5453fbcdab4cd5febfea745fdb0a23b91af92c61`

实验状态：`TERMINATED_NEGATIVE`

## 1. 一句话结论

P0V4 + V5 Bidirectional Exact 仍是当前控制算法；本轮开发的
`QG2TinyGAT` 虽然能够较准确地拟合 label pair，但 fresh-process 求解实验中
3 个完整 context 全部退化，另一个重尾 context 中 Q0 两次完成而 TinyGAT 三次超时，
因此该模型已经按用户决定终止，禁止部署，也没有切换 production 或覆盖 Exact control。

后续接手者默认不应继续当前 TinyGAT queue-ordering 实验。若以后重新授权学习优化，
应作为新的独立方向重新 freeze、采集和验收。

## 2. 接手后先读什么

按以下顺序阅读即可恢复当前事实状态：

1. `runs/p0v5_qg2_v5_trace_first_20260807/TINYGAT_TERMINAL_DECISION.json`
   —— 最终停止决定，是本轮最高优先级的机器可读状态；
2. `runs/p0v5_qg2_v5_trace_first_20260807/CLOSEOUT_AUDIT_ZH.md`
   —— 已完成、未完成和禁止部署项；
3. `runs/p0v5_qg2_v5_trace_first_20260807/TINY_GAT_FORCE_ON_DIAGNOSIS_ZH.md`
   —— fresh-process 退化数据与原因；
4. `runs/p0v5_qg2_v5_trace_first_20260807/STATUS_ZH.md`
   —— 最终流水线状态和测试摘要；
5. `plan/GAT/P0V5_QG2_V5_TRACE_FIRST_REDESIGN_20260807_ZH.md`
   —— 原设计、动作边界和实验顺序。其第 9 节已补入最终负结果。

若上述历史设计与 terminal decision 冲突，以 terminal decision 和已经落盘的
fresh-process 结果为准。

## 3. 当前基准与 exact-safe 边界

### 3.1 当前应保留的控制算法

- 控制算法是 `P0V4 + V5 Bidirectional Exact`，队列基准动作记为 `Q0`；
- 本轮没有修改 P0V4/P0V5 Exact control 的合法 label/route 宇宙；
- 没有修改 dominance、bound、label deletion、true reduced cost、停止条件和
  certificate 路径；
- production 没有切换到 QG2；
- QG2 checkpoint 仅为 development artifact，不是可部署模型。

### 3.2 QG2 原本允许改变什么

QG2 只在 V5 midpoint 未完成、即将进入 P0V4 exhaustive fallback 时介入。
每个 pricing request 只运行一次 Python/PyTorch 推理，输出 node potential、
arc potential 和 15 维 label-state coefficients。Native 随后为 label 计算固定标量
priority，并使用以下逻辑键排序：

```text
terminal class
-> floor(partialRC / frozen bucket width)
-> -label-state potential
-> partialRC
-> creationID
```

QG2 不得过滤 label、改变 dominance、提供 lower bound、停止 exhaustive proof 或签发
certificate。gate、hash、OOD、NaN/Inf 或 binding 不通过时必须走 literal Q0 container。

这个 correctness 边界在已完成 replay 中没有出现红线；本轮失败是性能失败，不是
exactness 失败。

## 4. 本轮实际完成了什么

### 4.1 工程实现

- Native 增加 `QG2LabelStatePotential` queue policy、15 维 label-state 特征计算、
  priority、trace 和 ordering telemetry；
- 每个 label 不保存 embedding，`State` 的 176 B 约束未因模型增加字段；
- Python 增加 trace snapshot binding、Q0-only corpus、监督构造、TinyGAT 训练、
  checkpoint/feature envelope、runtime binding 和 force-on replay；
- 增加 instance-balanced split、训练曲线、train/calibration/heldout 指标和
  GAT attribution；
- 增加 fail-closed manifest/hash/OOD 检查；
- 增加 QD1/QB1/Context GAT 等后续工具，但这些后续实验没有启动。

主要实现入口：

- `native/lunar_spprc/include/lunar_spprc/native_pricer.hpp`
- `native/lunar_spprc/src/native_pricer.cpp`
- `native/lunar_spprc/src/pybind_module.cpp`
- `src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py`
- `src/lunar_ice_bpc/guidance/proof_queue_label_state_gat_v3.py`
- `src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py`
- `src/lunar_ice_bpc/guidance/qg2_admission_supervision_v3.py`
- `scripts/collect_p0v5_qg2_v5_trace_corpus.py`
- `scripts/train_p0v5_qg2_v5_label_gat.py`
- `scripts/replay_p0v5_qg2_label_state_snapshot.py`
- `scripts/run_p0v5_qg2_v5_force_on_after_binding_repair.py`

### 4.2 Trace corpus

冻结了 45 个完整 Q0 future-trace context：

| 规模 | 完整 context | 说明 |
|---:|---:|---|
| scale30 | 33 | 已完成选定集合 |
| scale50 | 12 | 原计划 20；其余在负结果形成后不再采集 |
| 合计 | 45 | 19 个 instance，按 instance 切分 |

scale50 另有一个 600 秒 right-censored context 和 7 个已选择但未运行 context；它们
不能伪装成完整训练样本，也没有必要为已终止模型继续补采。

核心数据文件：

- `runs/p0v5_qg2_v5_trace_first_20260807/trace_supervision_corpus.json`
- `runs/p0v5_qg2_v5_trace_first_20260807/trace_training_view.json`
- `runs/p0v5_qg2_v5_trace_first_20260807/trace_corpus/progress.json`
- `runs/p0v5_qg2_v5_trace_first_20260807/trace_selection_freeze.json`

### 4.3 TinyGAT 训练

当前模型不是早期 arc-only QG1，也不是一个泛称模型；它是
`QG2TinyGAT`：2 层 edge-aware attention、hidden 32、2 heads，共 24,337 个参数。

| 项目 | 结果 |
|---|---:|
| 完成 epochs | 27 |
| 最佳 epoch | 19 |
| Train instance-balanced pair accuracy | 0.860516 |
| Calibration instance-balanced pair accuracy | 0.874620 |
| Heldout instance-balanced pair accuracy | 0.879074 |
| Checkpoint SHA-256 | `c283fa1fcecc70f67cd9540ff92b24253d692b9e9e8fdb0bdf53e98dea1c4836` |

训练产物：

- `runs/p0v5_qg2_v5_trace_first_20260807/label_gat/qg2_v3_gat.pt`
- `runs/p0v5_qg2_v5_trace_first_20260807/label_gat/training_curve.jsonl`
- `runs/p0v5_qg2_v5_trace_first_20260807/label_gat/training_report.json`
- `runs/p0v5_qg2_v5_trace_first_20260807/label_gat/feature_envelope.json`
- `runs/p0v5_qg2_v5_trace_first_20260807/label_gat_attribution.json`

训练 accuracy 较高，但这只是 pairwise surrogate 指标，不是求解性能权威。

### 4.4 模型归因诊断

| 诊断 | Pair accuracy 变化 |
|---|---:|
| 完整模型 baseline | 0.874539 |
| 去掉 edge feature group | -0.042170 |
| 去掉 node feature group | -0.013120 |
| 去掉 context feature group | +0.003390 |
| 关闭 message passing | -0.020240 |
| shuffle topology | +0.000258 |

可支持的解释是：edge 信息和 message aggregation 对监督任务有用，但尚不能证明真实
graph topology 提供稳定增益，也没有发现某一个输入特征单独支配全部准确率。更关键的是，
这些离线表现没有转化为更少 labels 或更短 wall time。

## 5. 决定停止的性能证据

### 5.1 三个完整 scale30 matched context

每个 context 均使用 fresh process，并分别对 Q0 和 TinyGAT 做三次重复；两边完成相同
`EXACT_PROOF_COMPLETION`，correctness 审计一致。

| State 前缀 | Q0 median (s) | TinyGAT median (s) | Wall ratio | Processed-label ratio | 结论 |
|---|---:|---:|---:|---:|---|
| `098f8374d1680b19` | 4.174 | 5.392 | 1.292 | 1.317 | 退化 |
| `0e222da795d14da2` | 2.273 | 2.615 | 1.150 | 1.154 | 退化 |
| `0761d9c2343be849` | 0.358 | 0.526 | 1.468 | 1.460 | 退化 |

- paired geometric mean ratio：`1.296944`；
- beneficial contexts：`0/3`；
- ratio 大于 1 表示 TinyGAT 更慢。

### 5.2 重尾 scale30 context

State：`1ceab640c7be1580bfbbe75807b8609870783c51746b739f23006aedd2feb9f3`。

| Arm | 重复结果 |
|---|---|
| Q0 | 278.956 s 完成；290.750 s 完成；第 3 次在用户决定停止后中断 |
| TinyGAT，bucket `1e-3` | 301.646 s、301.663 s、301.780 s，三次均 timeout |

第 3 次 Q0 中断没有被写成完成结果。TinyGAT timeout 也没有签发 certificate，属于
fail-closed adverse censor。

第 1 次重尾 replay 的机制数据：

| Arm | Processed labels | Dominance candidate checks |
|---|---:|---:|
| Q0 | 7,795,188 | 15,333,054,857 |
| TinyGAT | 6,882,700 | 17,093,640,348 |

TinyGAT 的 Native label scoring 估算只有约 0.827 s，因此主要问题不是 PyTorch 推理税，
而是 queue ordering 改变了 frontier：虽然 processed label 数未增加，但每个阶段遇到的
候选集合更宽、更难 dominance，导致 candidate checks 明显增加并无法在预算内完成证明。

### 5.3 动作面过宽

TinyGAT 对所有 scored labels 给出非零 priority。三个快速 context 分别产生约 15.8 万、
158.6 万和 188.7 万次 ordering differences；重尾第 1 次约 3,073.8 万次。
所以“只在同一 RC bucket 内重排”并不等于局部干预，当前实现实际上重写了很大一部分
fallback 轨迹。

同一重尾 state 的 leaked-QO2 历史诊断还显示 bucket 很敏感：`1e-4` 为 258.050 s，
`3e-4` 为 252.663 s，`1e-3` 则 301.341 s timeout。这只能说明存在更窄动作的研究空间，
不能推翻当前可部署 TinyGAT 候选已经退化的结论。用户已决定不再为窄 bucket 继续耗时。

## 6. 最终决定与当前进程状态

机器可读决定位于：
`runs/p0v5_qg2_v5_trace_first_20260807/TINYGAT_TERMINAL_DECISION.json`。

冻结结论如下：

- `status = TERMINATED_NEGATIVE`；
- `development_only = true`；
- `deployable = false`；
- `production_switch_authorized = false`；
- `exact_control_modified = false`；
- `next_action = do_not_continue_current_tinygat_queue_ordering_experiments`。

交接时已经检查，没有 QG2 collection、training、replay 或 force-on 求解进程在后台运行。
也没有启动自动 handoff runner。

## 7. 明确没有执行的内容

以下内容不是“待后台完成”，而是因为前置 fresh-process gate 失败而取消：

- 剩余 scale50 Q0 trace；
- scale50 TinyGAT force-on；
- TinyGAT narrow-bucket replay；
- 新的 QD1/QB1 三重复 matched collection；
- Context GAT；
- MLP 和 Linear 对照；
- development E2E；
- scale5/10/20/30/50 full20；
- production candidate freeze。

`scripts/continue_p0v5_qg2_v5_after_force_on.py`、
`scripts/screen_p0v5_qg2_v5_tinygat_bucket_arms.py`、
`scripts/run_p0v5_qg2_v5_matched_arms.py` 等文件只是 development tooling。
不得因文件存在就认为它们已执行或获得继续运行授权。

## 8. QD1/QB1 的遗留诊断如何理解

当前 engine 的 33 个 scale30 proof context 中已有一次性 matched 参考：

| Arm | Matched | GM | Beneficial |
|---|---:|---:|---:|
| QD1 | 33 | 0.8383 | 26 |
| QB1 | 26 | 1.3484 | 1 |
| leaked-QO2 `1e-4` | 32 | 0.9793 | 23 |
| leaked-QO2 `3e-4` | 32 | 0.9889 | 19 |
| leaked-QO2 `1e-3` | 31 | 0.9992 | 20 |

这些是单次 development 诊断，不是 3 次 blocked-replicate 正式证据。它们说明：

- QD1 在 scale30 proof tail 上值得未来单独核验；
- 固定强制一种 ordering 在不同 context 上风险很高；
- 若以后重开 context-level multi-arm selector，Q0 必须是模型外 fallback；
- scale50 当前 engine 仍缺 QD1/QB1 matched evidence。

不能据此直接部署 QD1，也不能用这些数据把本轮 TinyGAT 负结果改写为成功。

## 9. 测试状态

已落盘状态报告记录：

- 新增专项、instance-balanced 和 controller 回归：`95 passed`；
- 全部 QG2 回归：`410 passed / 4 failed`；
- 4 个失败来自历史 V2 freeze SHA drift，新 trace-first 链没有新增行为失败；
- 旧 Oracle execution freeze 的 131 个文件 hash 校验通过；
- `tests/test_p0v5_qg2_v5_trace_first.py` 最近一次为 `11 passed`；
- 新增文件 `git diff --check` 通过；
- 已完成 fresh replay 中 objective、legal universe、global minimum、RC 和 certificate
  没有红线。

这些测试证明已运行范围的工程和 exact-safe 边界；它们不构成性能通过或部署授权。

## 10. Worktree 注意事项

交接时 Git 根目录是 `/home/kai/work`，不是当前项目目录本身。当前 worktree 很脏，
约有 238 个 Git-visible 变更，其中包括大量用户已有修改、生成结果、QG2 代码和未跟踪文件。

接手时必须：

- 不执行 `git reset --hard`、`git checkout --` 或批量删除；
- 不把所有未跟踪 QG2 文件默认视为同一次可提交变更；
- 在提交前检查 `/home/kai/work` 下其他项目和 nested repositories；
- 以当前 `runs/` 证据为实验事实，不以 Git tracked/untracked 状态推断实验是否执行；
- 如果要冻结当前研究快照，先单独确定提交范围和生成结果保留策略。

## 11. 若未来重新开启 GAT，建议的安全起点

默认建议是继续以 P0V5 Exact/Q0 为控制，不恢复当前 TinyGAT。

若用户明确授权新方向，可考虑 context-level selective multi-arm 研究，但必须新建独立
plan、run root、manifest、checkpoint 和 terminal decision，至少满足：

1. 先对当前 engine 的 QD1/QB1 做 scale30/50 fresh matched replicates；
2. 模型只在 context 层选择经过验证的 ordering arm，不再对所有 context 强制 QG2；
3. 所有 arm 均未通过 risk/benefit/OOD/hash gate 时 literal 回 Q0；
4. inference、tensorization 和回 Q0 的成本全部计入 net wall；
5. 训练/校准/heldout 按 instance 隔离；
6. fresh-process wall 高于 surrogate accuracy；
7. exactness 红线仍是零容忍；
8. 新方向没有通过前，不修改 production 或 Exact control。

这只是可行的后续研究入口，不是已授权的当前任务，也不是继续运行旧脚本的理由。

## 12. 交接检查清单

- [x] P0V4/P0V5 Exact control 未覆盖；
- [x] TinyGAT checkpoint 标记为 development-only；
- [x] 负结果和停止权威已机器可读落盘；
- [x] 后台 collection/training/replay 进程已停止；
- [x] 未完成实验没有被伪装成通过；
- [x] 重尾 Q0 第 3 次中断没有被伪造为完成；
- [x] scale50、Context GAT、MLP/Linear、E2E/full20 均明确标为未启动；
- [x] production switch 明确禁止；
- [x] worktree 脏状态和 Git 根目录已说明；
- [x] 若未来重开，必须建立新的授权与 freeze。
