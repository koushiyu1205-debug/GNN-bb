# Native SPPRC feasibility spike 报告

## 结论

- upstream：`lab-core/rcspp@2f1d53ba6806844e30ce43ee9c41041a5a1b4e79`。
- GCC 13.3、C++23、CMake 3.28 下可构建。
- cyclic graph、自定义 resource/extension/feasibility/dominance、stable numeric arc ID 可用。
- v1 使用 pinned upstream + project-local extension；不建立 fork，不应用 core patch。
- upstream 数据测试使用 Git LFS；本机未安装 git-lfs 时，LFS pointer 不能作为算法测试结果。

## pressure false-COMPLETE 最小复现

复现位于 `native/lunar_spprc/tests/test_native_pricer.cpp`：

1. source 到中间节点有 10 个互不支配的 cost/resource trade-off label；
2. 只有第 4 个及以后 label 能通过最后一个 capacity extension；
3. reference 无 pressure 时得到最优 cost `3.0`；
4. 配置 `memory_pressure_fraction=0`、每节点保留 1 个 label；
5. pinned upstream 返回 `COMPLETE`，但解集合为空，因为后续 pressure 释放了 truncated 非支配标签。

因此，upstream raw `COMPLETE` 不能在启用 pressure trimming 时直接提升为项目证书。

项目 v1 的外部规避为：

- exact mode 固定 `memory_pressure_fraction=1.0`；
- hard limit 检查先于 pressure hook，达到限制直接返回 incomplete；
- `release_after_solve=false`，状态计算前恢复可能的 truncated frontier；
- telemetry 一旦出现 pressure event，`labels_dropped/certificate_blocker` 阻止认证。

该规避已由 C++ test 固定，因此当前不需要 fork。若将来无法通过外部参数维持此语义，再启用本地 patch queue 决策流程。

## Lunar 模型 spike

- multi-sortie depot cycle 可表达；每个 sortie 必须访问新任务。
- visited bitset 在 recharge 后不清空。
- raw operating cost、risk、weighted completion 和 task dual reward 使用 `double` 累积。
- Python 重建 `JourneyColumn` 后执行 canonical rounding 和 manual true-RC audit。
- 真实 5-task 高 dual differential：native/Python 均返回 62 个负列，best RC 均为 `-47.808085`。
- 零 dual proof 不虚构正 reduced-cost 区间的 global minimum，而是输出 `proved_no_rc_below=-1e-6`。

## 尚未 promotion 的能力

- Ryan–Foster 非空 branch context；
- 非空 cut context 和 subset-row；
- completion bound、bucket、bidirectional join；
- PathWyse/DSSR exact role；
- 50/100 数据与正式稳定性 gate。
