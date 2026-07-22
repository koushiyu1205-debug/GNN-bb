# P0 screened candidate 冻结说明

这里冻结的是后续可重复测试的 P0 候选，不是已晋级 release。

- policy hash：`9f0e7c4f7e2cab50267e197d55a17950aeee35aad388e47448f24873a7e92ba1`；
- config SHA-256：`a928c1c5dfe83b35b77f483ff2dd6268966e3b8999321e1afb74aea0a6d1c13d`；
- in-process engine：`dfaedf6d273c5c56`；
- host engine：`bddc7afddc232ceb`；
- 当前生产默认：`no_cut`。

只有 fresh paired promotion 的全部 correctness 和 performance gate 通过后，才允许把这个候选改标为 promoted。
