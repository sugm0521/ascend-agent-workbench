---
id: eplb-runtime-evidence
title: EPLB运行阶段与日志指标的证据边界
status: verified
updated_at: '2026-10-15T16:52:33+08:00'
verified_at: '2026-10-15T16:52:33+08:00'
tags:
- EPLB
- HIXL
- STAIR
- MRV2
- 日志判读
applies_to: 2026-10-15任务所用vLLM-Ascend 0.30.0rc2.dev10+g6d4339aa1.d20261012加本地补丁；MRV2/async
  STAIR/HIXL。实际实现以列出的文件指纹为准，不外推所有同版本安装
sources:
- id: planner-and-commit
  path: tasks/eplb/results/eplb-log-explanation-20261015-1334/installed-eplb-sources.json
  revision: sha256:35dbf0f734c6353d20ae000436dc01207d1a7349530d040c01d140b9db511d38
  locator: patch/platform/patch_eplb.py L793–855；distributed/eplb/policy/stair.py
    L275、345–374
  observed_at: '2026-10-15T13:36:11+08:00'
  evidence: source
  access: local-only
- id: hixl-timing
  path: tasks/eplb/results/eplb-log-explanation-20261015-1334/installed-communicator-source.json
  revision: sha256:9522a60705962673cc536d5b71bfd02de7dc67c0fadaf6b1c8ca526791b9ac58
  locator: distributed/eplb/eplb_communicator.py::execute L612–650及初始化/内存注册日志位置
  observed_at: '2026-10-15T13:36:43+08:00'
  evidence: source
  access: local-only
- id: ready-counters
  path: tasks/eplb/results/eplb-log-explanation-20261015-1334/migration-counter-definitions.json
  revision: sha256:a717f9a95d5f7f28ef742ea35c58265d1feab805d7a32797dc25ff01db12ca49
  locator: distributed/eplb/eplb_state.py::_all_ranks_result_ready/_poll_pipelined_readiness
    L534–556
  observed_at: '2026-10-15T13:36:54+08:00'
  evidence: source
  access: local-only
- id: mrv2-validation
  path: tasks/eplb/results/current-kv-transfer-20261015-1132/mrv2-and-kv-lifetime-code.json
  revision: sha256:346c6cef5c3f222073618aaea90fefe74b712a836f38f3535c6e8629f68dee1e
  locator: source.platform.py.content中的_validate_eplb_config，原文件L965–1007
  observed_at: '2026-10-15T11:36:11+08:00'
  evidence: source
  access: local-only
- id: historical-extract
  path: tasks/eplb/results/eplb-log-explanation-20261015-1334/log-extract.json
  revision: sha256:6c64dddc5a436737700b03a67515cf0548a006d34a847443e808ce65cf2de215
  locator: cycles[0..81]和对应timings，原日志11:56:37–13:33:30
  observed_at: '2026-10-15T13:34:11+08:00'
  evidence: runtime
  access: local-only
---

# EPLB运行阶段与日志指标的证据边界

## 结论与适用条件

当前实现可从真实`cycle committed`判断专家布局完成一次提交；不能将HIXL选择、内存注册或profile当作真实业务迁移。均衡度after是对同一历史采样在新布局下的预测，不能当成迁移后实测吞吐、时延或精度。

verified限定于本机保存的实现与历史日志。采集范围为当日特定服务轮次，不代表当前服务状态或所有上游版本。基线Git/包版本不能完整描述直接叠加的生产文件，复用时核对代码指纹或等价实现。

## 初始化、预演与真实提交

| 日志/事件 | 能支持的判断 | 不能直接推出 |
|---|---|---|
| provisionally selected hixl | 进程暂选HIXL绑定 | 所有worker已就绪 |
| every EPLB rank resolved the ctypes binding | EPLB组对绑定达成共识 | 通信器已完成建链 |
| Registering NPU memory regions | 登记供专家迁移使用的内存 | 已传输这些字节或新增了等量显存 |
| Initialized EPLB communicator | 通信器初始化完成 | 真实迁移或推理已通过 |
| Rearranged experts (profile) | 启动profile路径完成 | 已发生业务负载驱动重排 |
| Ascend async EPLB cycle committed | 变更层迁移到workspace、路由刷新后，本轮布局已提交 | KV持续稳定、数值精度或性能通过 |

planner-and-commit中只由EP rank0打印提交汇总；其他rank未打印该行不等于没有参与。historical-extract记录82次提交及82组阶段统计；这里只将它作为历史功能执行证据，不把次数固化为验收阈值。

## 均衡度与迁移计数

planner-and-commit的STAIR实现，以逻辑专家采样负载按副本数均分后估算rank负载。基础不均衡比为`最忙rank负载 / rank平均负载`，1表示完全均衡。

| 字段 | 该实现的统计口径 |
|---|---|
| mean=before->after | 每层先按样本计权求不均衡比均值，再对层取平均；同一批历史负载比较旧/新布局，after为预测 |
| p95=before->after | 每层先按样本计数求不均衡比95分位，再对层取平均；不是请求P95时延或全体层混合分位 |
| changed_layers | 物理到逻辑专家映射发生变化的MoE层数 |
| rank_transfers | 全部层目标专家槽位中，来源rank与目标rank不同的条目数 |
| cross_node_transfers | 上述条目中来源/目标rank所属节点不同的数量，是rank_transfers子集 |

迁移计数不是token数、不同逻辑专家ID数、字节数或HIXL请求数。历史示例mean从12.7194到1.7101说明新布局预测偏载降低，不能称吞吐提高同等倍数。后续before又升高，可能与负载变化和异步更新窗口有关，仅凭该值不能认定映射回滚或精度错误。

用于重核的源文件文本SHA256：patch_eplb.py为`3605c7337f45b80ccda874850ba7575288f3c688d04e821c8ae67681beb32c68`；stair.py为`f340c5b95404c65d3da6e67242aa9499212d6a6e7ede2279dec2dcb9ef68d708`。源码集合的容器文件哈希另见frontmatter revision。

## HIXL阶段时间与异步等待

hixl-timing和planner-and-commit中的`HIXL EPLB transfer`只汇总打印rank本轮的值，既非全局sum，也非最慢rank。requests为HIXL请求句柄数；bytes为该rank远端读字节累计。launch/background_transfer/confirmation分别累计发起、后台等待传输完成和跨rank确认的时间。

ready-counters中foreground_wait_ms仅累计等待流水ready归约的Work.wait()；migration_span_steps为检查全rank结果ready的次数，migration_deferred_steps为其中尚未ready、暂缓提交的次数。deferred不是失败次数或秒数。

不能把上述阶段时间相加当成完整规划/迁移端到端耗时，也不能用bytes除后台等待时间当作链路实测带宽。前台ready等待小不代表全部EPLB开销小，需要完整性能测量才可评价吞吐/时延。

## 开关与warning的判断范围

mrv2-validation的当前_validate_eplb_config在MRV2下拒绝DYNAMIC_EPLB或EXPERT_MAP_RECORD为true/1，提示用--enable-eplb。旧Dynamic EPLB is False字段不应单独作为主模型未启用证据；DSpark draft disabled且target remains enabled表示草稿关闭、主模型继续开启。

这些是所列实现的源码事实和本轮日志解释。不要据此替其他版本无条件添加/删除环境变量；先确认实际runner和参数消费路径。对异常级别也应沿调用链判断，warning与NotImplementedError等真正中断路径分别处理。

## 证据、访问限制与复查

frontmatter各source id对应上述章节。planner-and-commit、hixl-timing、ready-counters、mrv2-validation为源码层核验；historical-extract为原运行日志摘录，原始完整快照在本机任务目录。历史摘录文件生成于13:36:31，其observed_at沿用13:34:11原日志快照边界；源码时间为原读取落盘时间。本次仅重读并核对哈希，未重新取证、发推理或运行NPU实验。

全部本机材料为local-only，未随知识上传。其他agent缺少原文件时只能参考本条限定实现的判读方法，不能声称自行验证部署/运行；需要当前适用性而缺证据时标待复查。

模型runner、策略、日志生产代码、指标算法、通信器或采样窗口定义变化时，复查相应来源；新版本可能不打印相同字段。不能从本条推出抢核、硬件故障、融合算子精度退化或KV根因。Mooncake超时另见[分层超时条目](mooncake-nested-timeout.md)。
