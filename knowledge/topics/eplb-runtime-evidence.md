---
id: eplb-runtime-evidence
title: EPLB运行阶段与日志指标的证据边界
status: candidate
updated_at: '2026-10-15T19:23:21+08:00'
verified_at: '2026-10-15T16:52:33+08:00'
tags:
- EPLB
- HIXL
- STAIR
- MRV2
- 日志判读
applies_to: 2026-10-15任务所用vLLM-Ascend 0.30.0rc2.dev10+g6d4339aa1.d20261012加本地补丁；MRV2/async
  STAIR/HIXL。历史补丁实现未公开，不外推所有同版本安装，当前适用性待复核
sources: []
observed_at: '2026-10-15'
evidence_scope: 历史调查摘要；原始材料未发布，不能由本仓库独立复验当前部署或实现
---

# EPLB运行阶段与日志指标的证据边界

## 结论与适用条件

历史所核对实现可从真实`cycle committed`判断专家布局完成一次提交；不能将HIXL选择、内存注册或profile当作真实业务迁移。均衡度after是对同一历史采样在新布局下的预测，不能当成迁移后实测吞吐、时延或精度。

本条保留2026-10-15历史实现与日志调查的判读方法，原始材料及补丁未发布，因此状态为 candidate，当前适用性待复核。历史观察范围仅为当日特定服务轮次，不代表当前服务状态或所有上游版本；基线包版本不能完整描述叠加后的实现，复用时须检查目标代码是否等价。

## 初始化、预演与真实提交

| 日志/事件 | 能支持的判断 | 不能直接推出 |
|---|---|---|
| provisionally selected hixl | 进程暂选HIXL绑定 | 所有worker已就绪 |
| every EPLB rank resolved the ctypes binding | EPLB组对绑定达成共识 | 通信器已完成建链 |
| Registering NPU memory regions | 登记供专家迁移使用的内存 | 已传输这些字节或新增了等量显存 |
| Initialized EPLB communicator | 通信器初始化完成 | 真实迁移或推理已通过 |
| Rearranged experts (profile) | 启动profile路径完成 | 已发生业务负载驱动重排 |
| Ascend async EPLB cycle committed | 变更层迁移到workspace、路由刷新后，本轮布局已提交 | KV持续稳定、数值精度或性能通过 |

历史所核对实现只由EP rank0打印提交汇总；其他rank未打印该行不等于没有参与。历史调查摘要记录82次提交及82组阶段统计；原始运行材料未发布，该数量仅为历史观察，不作为仓库可独立复验的功能证据，也不固化为验收阈值。

## 均衡度与迁移计数

历史所核对的STAIR实现，以逻辑专家采样负载按副本数均分后估算rank负载。基础不均衡比为`最忙rank负载 / rank平均负载`，1表示完全均衡。

| 字段 | 该实现的统计口径 |
|---|---|
| mean=before->after | 每层先按样本计权求不均衡比均值，再对层取平均；同一批历史负载比较旧/新布局，after为预测 |
| p95=before->after | 每层先按样本计数求不均衡比95分位，再对层取平均；不是请求P95时延或全体层混合分位 |
| changed_layers | 物理到逻辑专家映射发生变化的MoE层数 |
| rank_transfers | 全部层目标专家槽位中，来源rank与目标rank不同的条目数 |
| cross_node_transfers | 上述条目中来源/目标rank所属节点不同的数量，是rank_transfers子集 |

迁移计数不是token数、不同逻辑专家ID数、字节数或HIXL请求数。历史示例mean从12.7194到1.7101说明新布局预测偏载降低，不能称吞吐提高同等倍数。后续before又升高，可能与负载变化和异步更新窗口有关，仅凭该值不能认定映射回滚或精度错误。

## HIXL阶段时间与异步等待

历史所核对实现中的`HIXL EPLB transfer`只汇总打印rank本轮的值，既非全局sum，也非最慢rank。requests为HIXL请求句柄数；bytes为该rank远端读字节累计。launch/background_transfer/confirmation分别累计发起、后台等待传输完成和跨rank确认的时间。

历史流水ready计数中foreground_wait_ms仅累计等待流水ready归约的Work.wait()；migration_span_steps为检查全rank结果ready的次数，migration_deferred_steps为其中尚未ready、暂缓提交的次数。deferred不是失败次数或秒数。

不能把上述阶段时间相加当成完整规划/迁移端到端耗时，也不能用bytes除后台等待时间当作链路实测带宽。前台ready等待小不代表全部EPLB开销小，需要完整性能测量才可评价吞吐/时延。

## 开关与warning的判断范围

历史所核对的 `_validate_eplb_config`在MRV2下拒绝DYNAMIC_EPLB或EXPERT_MAP_RECORD为true/1，提示用--enable-eplb。旧Dynamic EPLB is False字段不应单独作为主模型未启用证据；DSpark draft disabled且target remains enabled表示草稿关闭、主模型继续开启。

这些结论来自历史实现核对与日志调查，公开材料不足以独立重验对应补丁。不要据此替其他版本无条件添加/删除环境变量；先确认实际runner和参数消费路径。对异常级别也应沿调用链判断，warning与NotImplementedError等真正中断路径分别处理。

## 证据、访问限制与复查

原证据日期为2026-10-15，运行观察窗口为11:56:37–13:33:30；实现核对与日志判读分别属于源码层和历史运行层。原始材料与补丁未发布，本条仅保存可复用摘要，不提供私有材料索引。本次清理没有重新取证、发推理或运行NPU实验，也没有刷新原实验或 `verified_at` 时间。需要判断当前适用性时，须在目标实现中重新核对相关日志生产逻辑与指标定义。

模型runner、策略、日志生产代码、指标算法、通信器或采样窗口定义变化时，复查相应来源；新版本可能不打印相同字段。不能从本条推出抢核、硬件故障、融合算子精度退化或KV根因。Mooncake超时另见[分层超时条目](mooncake-nested-timeout.md)。
