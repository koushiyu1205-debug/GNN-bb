# FROZEN_P0V3_FULL_RUNTIME_CAPSULE_20260727

该目录是P0 V3当前基准的独立可运行保存包。它保留冻结Native二进制、当前
兼容Python运行壳、配置、测试、依赖清单、上游rcspp源码、scale5最小实例
以及80例正式结果快照。

验证并执行最小冷启动复现：

```bash
/home/kai/miniconda3/bin/python verify_capsule.py --capsule-dir . --smoke
```

预期scale5/instance_001得到：

- algorithm status：`BPC_OPTIMAL`
- exact status：`BPC_TREE_OPTIMAL`
- objective：`2.192192`

边界：历史V3冻结没有保存每个Native源码文件的字节副本，因此本包保证
冻结二进制可以完整运行和复现，不宣称能够从源码逐字节重建该历史二进制。
新的large-scale exact pricer必须使用不同backend/engine ID，不能覆盖本目录。
