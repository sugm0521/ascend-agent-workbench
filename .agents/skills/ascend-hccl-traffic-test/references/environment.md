# 环境准备与故障边界

仅在准备环境或定位对应失败时读取。通用身份、远程运行和资源管理遵循[根规则](../../../../AGENTS.md)与[能力映射](../../../../upstream/skill-mapping.md)，不重新运行完整初始化。实际接口按当前工具目录核对，旧初始化报告中的客户端状态可能已变化。

## 只读检查与现有环境复用

- 记录实际 host/port、root 用户、容器名称/ID、芯片型号、可见设备与卡映射；旧容器按用户已确认选择复用，不因默认名称 sugm 自行进入未知容器。检查 `uname -m`、`npu-smi info`、工作目录可用空间、通信网卡和 IP，不能把宿主结果当作容器结果。
- `npu-smi` 查询超时或设备显示 Alarm 时，保留证据并区分接口失败；温度/告警可读不等于整体健康，管理查询超时也不直接证明计算失败。用户已授权直接诊断时，独立检查设备文件持有者和实际进程后做有限验证；无占用证据则不能声称空闲。不自动重启/复位，只停止本任务拥有的查询，原工具确认收尾。
- 记录 CANN 版本及真实 `set_env.sh`，MPI 的实际 `mpirun`、编译器、版本、动态库路径；各节点匹配且路径可用。原包 MPICH 为 aarch64 3.2.1，但这是来源条件，不是所有当前环境的必需版本。
- 读取实际 `hccl_test` 的 README、Makefile、`alltoallvc_test --help` 或源码，核对芯片/CANN 是否支持 ccu_ms、aicpu_ts，以及 `-p`、数据类型、规模、正确性输出格式和预期测试行数。缺少一种模式或不兼容时标记未验证，不能擅自替换算法或宣称整套通过。
- 编译需加载本节点 CANN/MPI 环境。优先复用现成程序；需编译时按实际构建入口准备在已确认可写的位置，不直接在外部 CANN 根下生成文件。若工程不能移出原路径或必须写 CANN 安装目录，先明确该路径的修改授权。程序存在后检查执行权限和 `ldd` 缺库；发现缺库先定位版本/环境，不整体升级。

确认后可在每台相同工作目录生成如下环境文件，路径按实际内容引用；写入前读取同名文件。CANN/MPI 与工作目录可不同，但均须来自已核对输入。

```bash
source /actual/CANN/set_env.sh
export MPI_HOME=/actual/mpi
export PATH="$MPI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$MPI_HOME/lib:${LD_LIBRARY_PATH:-}"
export HCCL_SOCKET_IFNAME=actual-interface
```

环境变量以当前 CANN/MPI 要求为准，不无条件复制 OpenMPI/MPICH 专属配置。核对 Hydra/所选 MPI 远端环境继承方式，逐节点验证共享库和 `HCCL_SOCKET_IFNAME`；计划命令只加载启动节点的 env.sh，不能单凭它证明其他节点已加载。默认不关闭防火墙；连接受阻先检查路由和端口，调整防火墙需具体授权。

外层诊断预算与 HCCL 内部超时分开。已查证目标 CANN 9.2.0 的初始化日志要求 `HCCL_CONNECT_TIMEOUT` 在 120–7200 秒；不能为了短诊断把它设为 60 秒，否则 HcclGetRootInfo 在验证环境参数时就失败。其他版本和变量分别核对；短诊断用外层 timeout / 原监督器收尾，内部参数采用版本支持值。无依据时不主动设置内部超时。

## MPI 节点间 SSH 与 NPU 空闲

从实际启动环境对每个参与节点（包括自己）执行严格免交互 SSH：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=6 -o StrictHostKeyChecking=yes root@ACTUAL_HOST 'hostname; id -u'
```

以上 SSH 要求适用于通过 SSH 启动的测试。单机已验证 `mpirun -help` 支持 `-launcher fork` 时使用本地启动，不创建 SSH 配置。多机目标均需真实退出码 0。公钥拒绝时核对已有公钥；修复仅在明确授权目标添加并去重，保留原内容。不传私钥或关闭 StrictHostKeyChecking；主机密钥须核对目标指纹。Hydra 的 255 可能是前序 SSH 故障的次生输出，优先第一条错误。

逐节点检查 NPU 与 `/dev/davinciN` 持有者（如 fuser）和进程，核对返回码。设备缺失、权限不足或检测工具不可用不能声称空闲；宿主/容器视角差异结合资源状态查证。快照不是排他租用。默认原协调；已明确授权直接宿主诊断时记录例外范围/预算，启动前重查并关注冲突，不自动终止其他进程，也不把直接测试写成已授予托管资源。

## 明确需要安装时

复用环境是默认。缺 MPI/CANN 时先报告缺项，给出具体安装方案与副作用。用户确认后：

1. 查证服务器已有可信资源或用户指定的获取来源、版本、架构和许可；不携带原包 37.9 MB 的 MPICH，不上传超 1 MB 资源，不拆包绕限，不默认联网下载。
2. CANN 安装和临时目录约束在本任务工作目录；提供 toolkit 与适用芯片 ops 两个实际安装包，先 toolkit 后 ops，参数按该版本帮助核对。安装模式与复用模式二选一，不自动改系统已有安装。
3. 各节点验证 CANN 环境、hccl_test、MPI 编译/启动与共享库后回到主流程。安装成功不等于真实 HCCL 测试成功。

## 证据与来源

- 启动命令通过原工具运行，绑定真实 task/run/session 与进程/日志；记录超时预算和原退出码。不使用 `tee` 的退出码冒充 mpirun 的退出码，不因工具返回 session_id 就写为完成。
- CANN 9.2.0 本轮实测：HcclGetRootInfo 失败后 MPI 仍可能退出 0。该明确初始化失败必须覆盖外层退出码；去 root rank 的同期 debug/plog 查具体异常。静态配置路径先查文件类型与原内容，不执行既有启动脚本里的 mv，不把异常路径自动修复。配置问题未经对应异常日志确认只作线索。
- 已查证目标 CANN 9.2.0 在通信域初始化中读取 `/etc/hccl_rootinfo.json`：该路径若是目录，read 返回 EISDIR，UB 资源 JSON 加载失败并使 HcclCommInitRootInfoConfig 返回 4。预检存在的配置路径时核对类型；缺少该路径不自动生成，其他版本按实测核对。遇到该类错误保留 stat、最早 plog 与必要的路径访问证据；是否修复/替换系统配置按用户范围判断，不能仅依据文件名删除或移动。
- 完整日志与原始性能表保留在远端或 `.workbench-local/`，小摘要引用路径。helper 的失败提示是定位线索，未经确认不能写成根因；未观察到正确性输出、日志截断、未知格式、运行未终止均保留无定论。
- `passed_observed` 仍要求人工按实际程序的规模表和 rank/阶段核对覆盖；不得靠成功标记个数证明全部完成，不同版本的输出差异需保留原证据再适配。
- 本次真实服务器的 CANN 9.2.0 `common/src/hccl_opbase_rootinfo_base.cc` 中，结果表只打印一次 `check_result:` 表头，数据行是 `字节数 | 平均微秒 | 算法带宽 | success/failed/NULL`；非 root 校验失败另打印 `local rank_id N, check result failed`。helper 按该协议解析，不能只搜索重复的 `check_result: success`，也不能把 root 成功当作跨 rank 汇总成功。表数据最多保留 64 行，超出时显式标记摘要截断，完整原日志仍需保留。
- 用户于 2026-10-08 提供 WeLink 下载的 `hccl-traffic-test.zip`，其 `hccl-traffic-test/SKILL.md` SHA-256 为 `750e742a7cff529ab885b402b74f27c1f723cd7136a606f07d03a47817594638`。吸收其 alltoallvc 双模式顺序、hostfile 总进程数核对、SSH/NPU 检查和正确性验收方法。
- 本版本独立编写文档和 Python helper，未复制原脚本或二进制。包内没有发现版本/许可声明；不据此授权再分发原资源。移除固定 IP/网卡、MPI 资源部署及另一套远程生命周期，补充配置校验、日志摘要和覆盖限制。本地行为验证与真实单机有限范围成功/初始化失败路径已验证，具体范围和未完成的多机验收见[任务记录](../../../../tasks/2026-10-08-hccl-light-skill/任务说明.md)。
