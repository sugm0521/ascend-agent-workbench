---
name: ascend-hccl-traffic-test
description: 准备并验证昇腾单机或多机多卡 HCCL alltoallvc 打流，复用已有 MPI/CANN，检查连接和卡占用，顺序运行 ccu_ms、aicpu_ts 并归类失败。用于明确的通信测试或故障诊断；不替代模型性能基准或一般分布式日志分析。
---

# HCCL 轻量通信测试

遵循[项目规则](../../../AGENTS.md)，任务推进与记录沿用[execution](../ascend-task-execution/SKILL.md)。仅操作本任务确认的服务器、容器和路径。用户要求诊断时先区分管理查询故障与计算/通信故障；明确要求打流且范围已知时准备限时验证，不把管理查询超时直接判为硬件损坏或无限期停止测试。单机结果不能证明多机正常。

## 最短流程

1. 核对节点/卡数、宿主或已确认容器、启动节点、用户、路径、网卡和预算。复用已有决定与运行授权，不重复询问。故障诊断可先用较小规模和有限迭代，注明不能代替完整验收；正常验收沿用确认范围。缺环境按[环境准备](references/environment.md)检查，不自动安装或创建容器。
2. 通过原远程工具查版本、NPU 映射/占用、网卡、程序与动态库。多机须验证启动节点对所有节点含自身的严格免交互 SSH，以及远端环境传播；容器结果在实际容器核对。单机在已验证 MPICH 支持时采用 `-launcher fork`，不要求 self-SSH、不修改 known_hosts。
3. 用 `scripts/hccl_traffic.py plan` 生成命令；多机输出 hostfile，`--single-node` 输出本地 fork 命令和 `hostfile=null`，必须在声明的唯一节点运行。helper 只输出 JSON，不执行、上传或写文件；写文件前读原内容。核对实际程序帮助，特别是 `-p`、迭代与预热参数；限时命令需确认 GNU timeout，监督器预算覆盖终止宽限。
4. 默认使用原资源协调。用户已明确授权宿主直接诊断或本次例外时，可通过原远程运行工具执行限时测试：启动前独立核对所有参与卡的设备文件持有者、进程和映射，有占用或证据不足则停止；说明未获得托管排他租用，监测冲突，只清理本任务进程。协调总览因管理查询故障失效时保留失败，已有直接诊断授权不再请求；无该授权才确认例外。不安装第二套租约系统。顺序运行 ccu_ms、aicpu_ts；前者失败或正确性无定论先定位。
5. 原日志留远端/本机忽略目录，获取真实退出码与终态，用 `summarize` 汇总。程序退出 0 也可能失败；已查证的 `Process N HcclGetRootInfo failed` 和 `hccl interface return err ... retcode: 非零` 均判为失败，后者须按源码行核对调用阶段；未知/NULL/缺结果保持无定论。检查 CANN 结果表及非 root 正确性失败；`passed_observed` 仅表示观察记录成功，root 成功不能代替全部 rank。按实际规模和各 rank/阶段验收。
6. 报告节点/卡数、芯片与软件版本、实际命令、两种模式各自状态、正确性覆盖、性能原始表与证据路径。失败分为 SSH/Hydra、进程启动、HCCL 初始化、正确性或未知；脚本提示只是线索，结合实际日志查证。性能结论需要可比基线，不设无依据阈值。超时/取消通过原运行工具停止本任务运行，逐节点确认遗留 MPI/NPU 进程及资源释放。

## 工具入口

在本机用 Python 3 标准库执行，无需上传 helper 或安装第三方库。Linux 测试依赖 MPI/CANN 与真实 NPU，Windows 只负责生成和分析。

```bash
python scripts/hccl_traffic.py plan --work-dir /absolute/workdir \
  --hccl-dir /absolute/workdir/hccl_test --mpirun /absolute/mpi/bin/mpirun \
  --host node-a:8 --host node-b:8 --p-value 8

python scripts/hccl_traffic.py summarize --log /local/evidence/ccu_ms.log --exit-code 0

# 单机有限诊断；须在实际声明节点执行，先核对运行授权和卡占用
python scripts/hccl_traffic.py plan --work-dir /absolute/task \
  --hccl-dir /actual/hccl_test --mpirun /actual/mpi/bin/mpirun \
  --host actual-node:8 --p-value 8 --single-node --end 64M \
  --iters 10 --warmup-iters 3 --timeout-seconds 120
```

路径与节点都是示例，`--p-value 8` 仅在实际参数语义和环境已核对时采用。已查证 CANN 9.2.0 的 `-p` 表示每节点使用的 NPU 数；本版要求各节点 slots 与显式 -p 一致，不支持异构卡数映射。默认参数保留来源配置 `-b 8 -e 4G -f 2 -d int16`；可明确调整规模或单独选择算法，不能为获得通过而缩小已确认验收范围。`summarize` 退出码 0=已观察记录成功，1=运行/正确性失败，2=无定论；未知运行退出码不要填成 0。

`--iters`、`--warmup-iters` 可选，省略时保留程序默认；`--timeout-seconds` 增加 10 秒终止宽限。plan 的授权、占用与环境标记始终未验证，生成命令不能代替实际检查。初始化失败先看 root rank 的同期 plog/debug 日志与源代码，再区分配置、环境、设备错误；其他 rank 的 invalid data 可能只是 root 失败通知，不能据此归因于某张卡。

SSH 修复、环境/编译准备、按异常启用的拓扑/占用排查、安装分支与来源说明见[环境准备](references/environment.md)。原包的大型 MPICH、CANN 安装包不随 skill 携带；遵守用户上传不超过 1 MB 的限制，不通过拆包绕过。项目与依赖的已有身份/配置/资源状态复用，不建立另一套管理系统。
