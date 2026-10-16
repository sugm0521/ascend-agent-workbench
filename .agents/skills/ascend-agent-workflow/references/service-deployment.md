# vLLM服务部署准备与验收

用于实际启动/重启部署；普通状态查看或独立环境清单不执行整套准备。通用流程按目标硬件及运行方式选择分支，A5示例不代表其他机型已验证。遵循[根规则](../../../../AGENTS.md)与本次授权，不顺带完整初始化/升级。

## 目标、容器与执行方式

- 同会话继续同一任务，核对后沿用本会话已确认任务容器；重试/重启不重复创建。跨会话或其他任务容器只有用户明确指定复用才使用。新部署无已确认容器且未指定复用，按明确方案准备独立容器；不默认优先旧容器。
- 旧VAWS session、新MindIE binding/execution及用户指定手工Docker分别使用自身支持的原工具。旧[serving](../../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-serving/SKILL.md)/[PD](../../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-pd-serving/SKILL.md)有session前置条件，不传入新绑定，不伪造lease或重复资源分配。
- 核对实际工具、绑定、前置条件和代码路径，未知中断状态先查证；没有可用运行入口就记录缺口，不退回未经核对的裸SSH流程。

## 启动前检查

复用仍有效证据，重新核对资源/进程/端口及受变化影响项。同一实际容器的工具、驱动/运行时、相关后端和生效环境未变且已有成功结果时，引用原容器基线；重建或相关依赖/环境变化后只重查受影响项。占用、进程和端口等动态事实仍按当次启动确认。必需项失败或影响启动判断的关键状态未知，先解决缺口再加载模型；可选未使用项不阻塞。检查本身不授权改宿主网络/驱动、模型或源码。

| 项目 | 检查内容 | 通过标准 |
|---|---|---|
| 目标/入口 | 模型、节点、容器、卡范围、单机/多机/PD及绑定 | 范围明确，工具支持当前运行方式，归属正确 |
| 资源 | NPU状态、PID/cgroup及任务归属 | 卡正常且已协调，无未知占用、重复服务或其他任务干扰 |
| 容器 | image/devices/mounts/network/shm/ulimit及容器内设备 | 本次配置与所需设备实际可用；必需挂载的实际源、目标及类型符合本次方案，容器内路径类型正确；不以文件存在替代挂载核验 |
| 通信设备 | 多机时区分控制/bootstrap与高速数据平面，核对接口/设备映射、链路、速率或模式、MTU | 符合机器拓扑；不能仅凭SSH/ping/网卡名判通过，数据面按实际后端工具核对 |
| 地址/绑定 | 相关NIC/IP、对端路由、容器可见性，HCCL/Gloo/TP/连接器有效配置 | 每个字段绑定正确用途的网络，不要求所有组件无条件同一接口 |
| 端口 | API/master/DP/KV/proxy监听与归属 | 没有冲突，配置与实际端点一致；托管模式沿用原端口机制 |
| 软件 | 实际解释器、双仓代码/patch、驱动/CANN/torch_npu、容器内npu-smi及必要导入 | 实际容器的npu-smi info与框架查询正常，设备符合本次预期；相关后端独立识别结果一致；多机共同基线一致，角色差异明确 |
| 模型 | config、索引引用文件、量化与辅助配置、实现支持 | 文件完整可解析，与实际模型实现匹配，不跳过有效权重掩盖兼容问题 |
| 容量 | 显存/内存、缓存/日志磁盘、shm/nofile | 当前模型/并行/请求配置有合理依据，无已知不足；适用旧证据可复用，不每次完整模型分析 |
| 条件组件 | 使用时才检查FLA/DSpark/custom OPP/Mooncake等 | 必需组件可用且预检正常退出；包安装不等于live生效 |
| 最终参数 | 当前CLI/消费字段、TP/PP/DP/rank/master/headless/graph/MTP/融合 | 现场接受且实际生效，符合用户方案，不默默降级或改数值语义 |
| 多机/PD | rootinfo/hixlep或自动发现、角色、connector并行元数据、代理 | 拓扑与端点一致；证据缺失/变更/矛盾或失败时补最小相关通信验证，不默认全量打流 |

模型专属量化字段、旧开关失效或接口变化按实际实现核对，不能固化某次修复为所有启动必做步骤。代码/环境变更后必要reload由执行方在授权范围内完成。

### 通信分支与必需挂载的执行检查

新建/重建容器、相关挂载或通信方式变化时，按[部署预检说明](../../../../docs/deployment-preflight.md)先确定本次采用静态端点、受支持的自动资源方式或不适用该路径。静态方式按实际物理NPU检查端点JSON及挂载；自动方式确认当前版本/拓扑支持、声明设备与工具前提，并清除冲突静态配置；不能因文件缺失擅自切换方案。

手工Docker入口使用同一份本次声明生成首台与批量的挂载/env参数，调用[只读检查工具](../../../../scripts/deployment_preflight.py)的`docker-args`阶段；创建后对照该节点实际`docker inspect`执行`verify`，缺必需项时停止对应后续启动。托管入口已有等价检查时复用原契约，不插入另一套生命周期。只核对本次声明范围；容器内路径/工具和后续通信/业务请求仍分别验收，普通状态查看不触发此流程。

`verify`只核对已声明条件，不能发现所有漏声明资源。昇腾容器的`npu-smi info`可用性属于下文容器环境基线，不依赖是否写入挂载清单；镜像已有可用工具就复用，缺失时按实际驱动补齐工具及依赖，不固定宿主安装路径。挂载声明通过后，容器环境基线也须通过或具有仍适用的成功证据，才能加载模型。

## A5新建容器示例

仅用于已确认host网络、runc/privileged方案的A5手工容器。根据实际授权卡范围和宿主设备填写变量；托管容器使用原工具，不执行此模板。已有本会话任务容器或明确指定复用时跳过创建。保存镜像有正确默认入口时优先保留；下例用于已确认需显式加载环境的镜像。

以下代码是设备/基础选项的命令构造示例，不是公共启动脚本或已实测的通用镜像配方。实际入口按上一节声明统一生成所需mount/env并验收，不能把示例中手写列表当作另一套批量配置。本例声明须包含模型与driver挂载及env中的ENV_SCRIPT。ENV_SCRIPT须在镜像内存在且加载本次全部必需CANN/NNAL/OPP；不把某个版本固定路径当通用入口。

本例已确认使用`--privileged`，按[Docker设备权限语义](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities)，容器可访问全部宿主设备，下面的逐卡`--device`清单不构成设备访问隔离。仅授权子集卡时，须在实际NPU进程入口落实该后端支持的选卡机制并核对物理/逻辑映射，未落实前不启动NPU负载；若要求设备访问隔离，则使用经验证且符合该要求的非privileged或托管方案，运行时选卡不能代替访问隔离。

```bash
# 在目标宿主设置本次实际值，不将占位符直接执行。
: "${IMAGE:?}" "${CONTAINER:?}" "${MODEL_DIR:?}" "${ENV_SCRIPT:?}"
: "${NPU_IDS:?逗号分隔的已授权卡号}" "${SHM_SIZE:?}" "${NOFILE_LIMIT:?}"
: "${DEPLOYMENT_PLAN:?本节点部署声明JSON}" "${DEPLOYMENT_PREFLIGHT:?已上传的预检脚本路径}"
docker image inspect "$IMAGE" >/dev/null || exit 1
if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
    echo '容器名冲突，停止；不自动复用、删除或覆盖'
    exit 1
fi
test -f "$MODEL_DIR/config.json" || exit 1
test -d /usr/local/Ascend/driver || exit 1
run_args=(--runtime=runc --user root -it -d --name "$CONTAINER"
    --network host --privileged --shm-size="$SHM_SIZE"
    --ulimit "nofile=$NOFILE_LIMIT:$NOFILE_LIMIT" --workdir /workspace
    --entrypoint /bin/bash)
IFS=, read -r -a card_ids <<< "$NPU_IDS"
for card in "${card_ids[@]}"; do
    [[ "$card" =~ ^[0-9]+$ ]] || exit 1
    device="/dev/davinci$card"
    test -e "$device" || exit 1
    run_args+=(--device "$device")
done
# 管理设备按本次A5驱动/镜像要求确认；不同后端需调整。
for device in /dev/davinci_manager /dev/hisi_hdc /dev/ummu /dev/uburma; do
    test -e "$device" || exit 1
    run_args+=(--device "$device")
done
# 模型、driver及本次必需源码/共享/通信挂载统一写入声明。
# 下面同一入口用于首台和批量；verify失败时不进入后续模型启动。
python3 - "$DEPLOYMENT_PREFLIGHT" "$DEPLOYMENT_PLAN" "$IMAGE" "$CONTAINER" \
    "$MODEL_DIR" "$ENV_SCRIPT" "${run_args[@]}" <<'PY'
import json, pathlib, subprocess, sys
helper, plan_path, image, container, model, env_script, *base_args = sys.argv[1:]
plan = json.loads(pathlib.Path(plan_path).read_text())
if plan['container'] != container or plan.get('env', {}).get('ENV_SCRIPT') != env_script:
    raise SystemExit('声明container/ENV_SCRIPT与本次启动参数不一致')
for source in (model, '/usr/local/Ascend/driver'):
    if not any(m['source'] == source and m['target'] == source for m in plan['mounts']):
        raise SystemExit('声明缺少本例必需挂载: ' + source)
declared = json.loads(subprocess.check_output(
    [sys.executable, helper, 'docker-args', '--plan', plan_path], text=True))
subprocess.run(['docker', 'run', *base_args, *declared, image, '-lc',
                'set -e; source "$ENV_SCRIPT"; exec /bin/bash'], check=True)
inspection = pathlib.Path(plan_path + '.inspect.json')
inspection.write_text(subprocess.check_output(['docker', 'inspect', container], text=True))
subprocess.run([sys.executable, helper, 'verify', '--plan', plan_path,
                '--inspect', str(inspection)], check=True)
PY
```

不覆盖整个宿主/usr/lib64或/usr/local/sbin；rootinfo/hixlep先核对内容和本次拓扑。镜像保存不包含外部模型挂载及其元数据修改，需另行记录和准备。容器running不代表基础导入、通信或推理通过。

## 通信与环境检查示例

多机逐目标确认预期控制和高速数据面，不固定网卡名、IP或Gbps。以太网部分的只读示例：

```bash
: "${COMM_NIC:?}" "${LOCAL_IP:?}" "${PEER_IP:?}"
ip -br link
ip -br addr
ip -d link show dev "$COMM_NIC"
ip route get "$PEER_IP" from "$LOCAL_IP"
ethtool "$COMM_NIC"
```

UP/carrier、地址、MTU、协商速率/模式和路由需符合实际拓扑；不支持或未知时保留限制，不能自动标通过。NPU/RDMA/UB设备和端口使用实际驱动/原工具查询；自动发现开关和配置文件存在不是链路证明。相关节点间路径按拓扑检查，不只查启动节点。证据仍有效时不重复完整HCCL测试。

基础环境检查必须与实际启动使用同一解释器和环境入口；下例python3需替换为已确认解释器。新建或相关环境变化时，将工具与框架检查合并到同一次原执行调用。仅需单项检查时按上文复用已有结果，不重复整段导入；独立快照不调用这段：

```bash
docker exec --env "ENV_SCRIPT=$ENV_SCRIPT" "$CONTAINER" bash -lc '
    set -e
    source "$ENV_SCRIPT"
    npu-smi info
    python3 -c "import ssl, hashlib, torch, torch_npu, vllm, vllm_ascend; print(ssl.OPENSSL_VERSION); n=torch.npu.device_count(); assert n > 0; print(n, torch.npu.get_device_name(0))"
'
```

命令缺失、依赖加载失败或查询非零会直接中断该基线，不能以宿主可用、bind存在或torch导入成功替代。后端若另有芯片识别/编译能力探测，仅在本次实际使用该路径且缺少有效结果时，将其与预期芯片的一致性断言并入同一个既有[原生导入用例](../../../../docs/runtime-tools.md)。不把某版Triton字段或PCI编号写成所有芯片的判断标准，也不只记录导入成功而忽略错误能力值。

当前CLI或参数消费存在疑问时再做针对性解析检查，不在每次基线中重复`vllm --help`。上述就绪确认不额外触发编译、采样、HCCL或模型冒烟；真实通信和业务验收沿用本轮原有必需用例，不重复建立一套。定位到具体失败项后暂停对应启动并处理该项，满足本次就绪条件即继续主任务。

核对最终退出码和实际进程的可见卡范围；子集卡按已核对的运行时选卡机制确认映射，不能以`docker inspect`中的`--device`清单代替。此检查不覆盖模型配置、所有原生组件、NPU计算或数值精度。

## 版本清单与服务参数

每次实际启动/重启前调用[ascend-runtime-snapshot](../../ascend-runtime-snapshot/SKILL.md)，输出并保存该attempt选用的CANN、代码SHA/dirty/PR、依赖替换及模型/最终argv/env。字段与证据边界仅在[共同清单定义](../../ascend-runtime-snapshot/references/snapshot-fields.md)维护。启动后在变更或来源歧义影响判断时补实际加载证据。

单机进程参数示例（在实际容器已加载环境，管理生命周期仍由原工具负责）：

```bash
set -e
source "$ENV_SCRIPT"
vllm serve "$MODEL_DIR" --host "$BIND_IP" --port "$PORT" \
    --served-model-name "$SERVED_MODEL" --tensor-parallel-size "$TP"
```

多机multiproc的参数形状如下，完整额外参数、executor和环境须由现场版本接受；headless仅适用于该方式的worker角色，不能套到Ray或其他后端。以该版本正确解释物理/逻辑卡映射，不对非连续卡号猜可见索引：

```bash
set -e
source "$ENV_SCRIPT"
args=(vllm serve "$MODEL_DIR" --host "$BIND_IP" --port "$PORT"
    --served-model-name "$SERVED_MODEL" --tensor-parallel-size "$TP"
    --pipeline-parallel-size "$PP" --nnodes "$NNODES" --node-rank "$NODE_RANK"
    --master-addr "$MASTER_ADDR" --master-port "$MASTER_PORT"
    --distributed-executor-backend mp)
if [[ "$NODE_RANK" != 0 ]]; then args+=(--headless); fi
"${args[@]}"
```

PD按当前连接器明确P/D角色、engine标识、KV端口、TP/PP/DP及必要状态元数据；参数化形状是追加`--kv-transfer-config "$KV_TRANSFER_JSON"`，不提供与模型无关的万能JSON。使用原实现核对代理启动参数和连接器要求的顺序；[PD流程](../../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-pd-serving/SKILL.md)的proxy生命周期在其边界之外，不把启动代理误称其wrapper已管理。准备角色命令后同环境解析，确认master/rendezvous与实际监听一致。

仅当本次计划启用EPLB时，可按需参考[MRV2/STAIR版本化启用样例](../../../../knowledge/topics/eplb-enable-reference.md)，先核对模型/量化、runner与并行约束；该样例不作为所有服务的默认配置，P/D角色分别确认，不因套用样例自动叠加历史PR或修改环境。

## 启动、验收和交接

1. 刷新资源/端口及前次进程状态，通过所选原工具启动，保存最终配置、attempt、日志及PID/starttime/进程组或cgroup等归属证据。
2. 跟踪初始化、权重加载、编译/图捕获、API ready。headless worker按初始化日志与进程判断，不要求每个worker有HTTP接口。首次编译耗时不当稳态性能。
3. 核对health/models和目标路径短请求，保留原始文本。PD关联request_id与P/D传输日志；任务要求的流式/非流式路径分别验收。仅检查启动且用户排除请求时记功能未验证。
4. 分别报告启动、接口、传输、输出；HTTP200、token数或传输完成不能掩盖异常文本。异常时必要同输入单D/手动PD对照，不自动扩大源码修复。
5. 按用户最新要求保留服务并交付URL可达范围、请求样例、日志、版本清单和占用；只回收本次已确认失败组件，按部署回滚合同保留已要求保留的组件。用户要求停服务时核对实际退出，不处理其他业务或删除产物。

参考方法来自本项目锁定workspace serving/PD入口和本项目近期任务；本文新增通用编排及A5条件示例，不复制外部维护源。历史OpenSSL、QuaRot、jemalloc、MLAPO、KDA等症状仅按当前证据触发排查，不固化为每次安装/修复步骤。
