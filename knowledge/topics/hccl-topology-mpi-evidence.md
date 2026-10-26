---
id: hccl-topology-mpi-evidence
title: HCCL多机测试中的拓扑、MPI兼容和结果分层
status: candidate
updated_at: '2026-10-26T14:40:16.513692+08:00'
verified_at: '2026-10-26T14:40:16.513692+08:00'
observed_at: '2026-10-23'
tags: [HCCL, A5, UB, UBoE, rootinfo, MPI, Hydra, GLIBC, NFS]
applies_to: A5历史UB-only与32卡失败诊断；MPICH3.2.1及相应容器组合，未验收96卡通信
evidence_scope: 保存的源脚本与单机/多机失败控制摘要；完整构建、拓扑和原件未公开，不能由仓库独立复验；不将未执行的96卡矩阵视为通过
sources: []
---

# 先确认测试走到哪一层

| 层次 | 应保留的证据 | 不能替代下一层 |
|---|---|---|
| 启动入口 | 真实容器ID、SSH和launcher argv | 容器能登录不证明MPI工作 |
| MPI运行时 | GLIBC兼容、远程可执行路径、空载各rank结果 | 4rank空载成功不证明全节点启动 |
| 设备拓扑 | 实际消费的rootinfo、rank数、设备Entity和通信plane | JSON生成成功不证明设备实体存在 |
| HCCL执行 | 每rank首错、接口返回码、正确性表、大小范围 | MPI退出0不证明HCCL成功 |
| 资源退出 | 任务PID与设备持有者终态 | 聊天结束不证明打流进程已退出 |

## 拓扑文件不是硬件能力证明

历史32卡中部分rank报`UB Entity not found`，其他rank报告NetLayer总rank数与32不一致，HCCL接口retcode非零，而MPI主程序仍返回0。应先保留这些错误及其rank映射，不从外层exit推导通信通过。

UB与UBoE按实际设备和用户选定路径区分。历史用户最终选UB-only，先前“等UBoE地址才能继续”的假设已不适用；不能为了修复UB Entity错误自行配置UBoE或猜邻机地址。rootinfo成功生成、与宿主相同、bind mount可见仍不证明设备communication plane完整。

某版交接脚本对`local_id`累加并统一改`net_instance_id`，重复执行非幂等，可能再次改变已有值。使用前读取原始拓扑、脚本和期望分组，保存diff；不将该历史脚本作为默认修复。只读bind mount还可能导致替换busy，候选文件写出不表示消费路径已更新。

## MPI兼容与Hydra启动

宿主MPI可能依赖容器没有的GLIBC版本。历史GLIBC2.38失败控制之后，容器内构建MPICH3.2.1并以真实launcher验证，部分空载rank成功；这不代表全部12节点可用。

Hydra远程launcher路径的引号曾改变实际可执行argv，需分别核对本地shell解析与远端启动参数。保持可执行路径和参数边界，不盲目复制跨版本wrapper补丁。远程缺`ip`命令导致地址变量为空时，外层shell仍可能返回0；必须核对真实stdout/stderr和各rank结果。

## NFS、单机与全机矩阵

一个空载rank阻塞在NFS读取，可以让MPI启动看似卡住，应与SSH、launcher和HCCL首错分开。历史定向终止自有probe，不把重挂NFS或重启Docker作为默认下一步。

单机8卡两个调度路径的8B–64MiB正确性表通过，只是对应单机矩阵；32卡失败保留，96卡矩阵未执行。工具将可选旧包缺失记为inconclusive也不能抹去原始正确性表或升级为全局成功。正式测试入口复用[HCCL打流skill](../../.agents/skills/ascend-hccl-traffic-test/SKILL.md)，重新运行需按当前设备占用和授权核对。

更换通信plane、驱动/CANN、rank组织、容器或MPI后复查。历史脚本和数值只限定当时组合，不授权修改系统拓扑。
