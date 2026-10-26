---
id: a5-memcache-pooling-setup
title: A5 MemCache池化的配置、前置检查与分阶段验收
status: candidate
updated_at: '2026-10-18T15:05:13+08:00'
verified_at: '2026-10-18T15:05:13+08:00'
observed_at: '2026-10-17'
tags: [A5, MemCache, MemFabric, vLLM-Ascend, 池化, MultiConnector, device_urma, rootinfo, engine_id, PIECEWISE, 预检]
applies_to: Ascend950DT、CANN9.2.0、memcache_hybrid与memfabric_hybrid1.2.0、vLLM0.30系列及对应Ascend连接器的历史配置参考；实际构建含额外叠加修改，包版本号不代表完整复现条件
evidence_scope: 复核用户提供的A5配置、历史启动配置、原生配置解析与MultiConnector展开回执，以及完整失败日志；原始运行材料及完整构建未公开，不能由本仓独立复验；本次只整理文档并检查示例，不重新连接服务器、运行NPU或重启服务；完整池化读写尚未通过
sources: []
---

# A5 MemCache池化配置与启动前准备

本条保留可复用的配置结构和排错顺序，不能当作已经跑通Kimi K3池化的一键部署方案。以下是加入已有P/D启动入口的增量，模型、原并行策略、Mooncake版本及其他参数由原服务配置提供；依赖、拓扑和后端功能仍须在目标环境验收。

## 1. 确认环境与资源

先记录实际Python、CANN、驱动/固件、MemCache/MemFabric及vLLM双仓版本和叠加修改，确认配置文件在运行容器内可读。HAL文件存在、符号可解析和实际接口可用是不同检查，参见[HAL与Notify兼容边界](../../topics/memfabric-hal-notify-compatibility.md)。不把独立替换一个HAL库作为默认准备步骤。

已有CANN及模型运行环境应先按其正常入口加载，再使用同一个Python解释器定位两个包。下面只补充历史1.2.0包布局中的动态库目录，避免硬编码某个Python3.11/3.12的site-packages路径：

```bash
pool_lib_path=$(python3 - <<'PY'
import importlib.util
import pathlib
import sysconfig

dirs = []
for name in ("memcache_hybrid", "memfabric_hybrid"):
    spec = importlib.util.find_spec(name)
    if spec is None or spec.origin is None:
        raise SystemExit(f"package not found in selected Python: {name}")
    lib = pathlib.Path(spec.origin).parent / "lib"
    if not lib.is_dir():
        raise SystemExit(f"check the actual package layout: {lib}")
    dirs.append(str(lib))
python_lib = sysconfig.get_config_var("LIBDIR")
if python_lib and pathlib.Path(python_lib).is_dir():
    dirs.append(python_lib)
print(":".join(dirs))
PY
) || exit 1
export LD_LIBRARY_PATH="${pool_lib_path}:${LD_LIBRARY_PATH:-}"
```

启动前确认每台目标机器的卡、端口、容器身份和已有服务归属；广播维护信息只起通知作用，不能阻止其他任务自动重拉。释放或暂停其他业务必须具有对应授权，不能把本条当作停止整机其他容器的指令。

## 2. 准备三份后端配置

A5配置结构为全池一个MetaService；各LocalService由vLLM连接器初始化，不另起standalone MemCache。以下以`/opt/memcache/`为可自行选择的配置目录，`192.0.2.10`是文档示例地址，部署时统一替换成实际MetaService可达地址。

`mmc-meta.conf`：

```ini
ock.mmc.meta_service_url = tcp://192.0.2.10:5000
ock.mmc.meta_service.config_store_url = tcp://192.0.2.10:6000
ock.mmc.meta_service.metrics_url = http://192.0.2.10:8001
ock.mmc.log_level = info
```

`mmc-local.conf`，供所有P/D启动单元读取：

```ini
ock.mmc.meta_service_url = tcp://192.0.2.10:5000
ock.mmc.local_service.config_store_url = tcp://192.0.2.10:6000
ock.mmc.log_level = info
ock.mmc.local_service.world_size = 256
ock.mmc.local_service.protocol = device_urma
ock.mmc.local_service.dram.size = 10GB
ock.mmc.local_service.max.dram.size = 1024GB
```

- MetaService的5000/6000须从参与节点可达，指标8001避开常见的vLLM API端口8000；实际端口按现有服务占用规划。
- `world_size`在本配置中用于支持的最大LocalService注册rank数，不能直接等同于机器数，也不能推断已经注册256个rank。
- `dram.size`是每个存储rank贡献的容量，应按实际可用内存预算，不能所有rank均为0。若每机8个存储rank各贡献10GB，预算为80GB/机；这只是容量计算，不是实际注册成功的证明。
- `max.dram.size`是容量上界，配置1024GB不等于各rank实际分配1024GB。
- 先使用实际版本接受的配置项。本次额外加入`ock.mmc.log_output_target`后，原生解析器报`Invalid key`并终止初始化，不能为了采集日志随意增加其他版本的字段。

`run_mem_cache.sh`，仅在选定MetaService节点执行一次：

```bash
#!/usr/bin/env bash
set -euo pipefail
export MMC_META_CONFIG_PATH=/opt/memcache/mmc-meta.conf
exec python3 -c 'from memcache_hybrid import MetaService; MetaService.main()'
```

在该进程启动前同样加载正确的CANN/Python环境和动态库路径；先检查已有实例，避免重复启动MetaService。

## 3. 在全部P/D启动入口增加环境变量

以下对应A5 UB及`device_urma`：

```bash
export MMC_LOCAL_CONFIG_PATH=/opt/memcache/mmc-local.conf
export PYTHONHASHSEED=0
export ASCEND_LOCAL_COMM_RES='{"version":"1.3"}'
```

`MMC_LOCAL_CONFIG_PATH`指向当前进程真正读取的文件；配置目录不需要绑定到Python安装目录。全部参与进程保持同一`PYTHONHASHSEED`。环境变量应在启动vLLM之前设置，并结合原生日志核对实际读取路径，不能只检查脚本中有无export。

用户提供的A5 UBOE配置参考是将协议改为`device_uboe`，使用`ASCEND_GLOBAL_RESOURCE_CONFIG='{"comm_resource_config.protocol_desc":["uboe:device"]}'`。该分支本次未做运行验收；UB与UBOE应按实际硬件及发行组合选择，检查继承环境，不混用两套通信配置。

## 4. 保留原Mooncake并组合池化连接器

使用`MultiConnector`组合已有Mooncake与`AscendStoreConnector`，不因开启池化改写Mooncake的连接器版本、端口、engine ID、并行描述或模型TP/PP/DP/DCP参数。

下面读取使用者自己的原单个Mooncake JSON并生成增量配置；输入为`original-mooncake.json`，输出为`pooling-kv.json`。输入若已是MultiConnector，先核对现有子项后合并，不再次嵌套执行此片段。

```bash
# P侧示例；D侧改为kv_consumer，并按实际启动单元规划LOOKUP_ID。
export POOL_KV_ROLE=kv_producer
export POOL_LOOKUP_ID=0
python3 - original-mooncake.json > pooling-kv.json <<'PY'
import copy
import json
import os
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    original = json.load(source)
role = os.environ["POOL_KV_ROLE"]
assert role in ("kv_producer", "kv_consumer")
assert original["kv_connector"] in ("MooncakeConnectorV1", "MooncakeConnectorV2")
assert original["kv_role"] == role, "preserve the original P/D role"
moon = copy.deepcopy(original)
parent = {"kv_connector": "MultiConnector", "kv_role": role}
# 历史实现会再次显式传入engine_id；放父级继承，避免子项重复关键字。
if "engine_id" in moon:
    parent["engine_id"] = moon.pop("engine_id")
store = {
    "kv_connector": "AscendStoreConnector",
    "kv_role": role,
    "kv_connector_extra_config": {
        "backend": "memcache",
        "lookup_rpc_port": os.environ["POOL_LOOKUP_ID"],
        "use_layerwise": True,
    },
}
parent["kv_connector_extra_config"] = {"connectors": [moon, store]}
effective_moon = copy.deepcopy(moon)
if "engine_id" in parent:
    effective_moon["engine_id"] = parent["engine_id"]
assert effective_moon == original
print(json.dumps(parent, ensure_ascii=False))
PY
```

把输出JSON作为已有serve命令的`--kv-transfer-config`参数。P侧父配置及两个子项均为`kv_producer`，D侧均为`kv_consumer`。为连接器的独立lookup服务按当前实现规划不冲突的`lookup_rpc_port`值；示例可按P侧`"0"`–`"3"`、D侧`"4"`–`"7"`分配，但不能脱离真实实例/rank关系照抄节点编号，实际监听端口也应核对。

### 4.1 配置版本兼容性：engine_id与原生字段

该片段只是JSON转换。历史部署的MultiConnector展开曾报`KVTransferConfig() got multiple values for keyword argument 'engine_id'`；将该键放父级后，实际展开的Mooncake有效字段与原配置逐字段核对通过。复用时仍须在安装的连接器实现中做同样的展开检查，不能把这里的字典相等检查当作任意版本的运行证明。

连接器参数展开与MemCache原生配置解析是两层检查；前者通过不能排除第2节中原生解析器拒绝字段的问题。JSON语法正确、环境变量已导出均不能替代安装版本的实际解析结果。

### 4.2 layerwise连接器与实际图模式

同时记录最终图模式。本次layerwise的AscendMultiConnector将D侧`FULL_DECODE_ONLY`自动覆盖为`PIECEWISE`；argv保持不变不意味着最终执行模式不变，也不能据此推断性能收益。

## 5. rootinfo前置条件：核对实际消费路径

历史现场的MemFabric初始化实际由`TopoReader::ParseRootInfo`读取`/etc/hccl_rootinfo.json`，无法打开后出现`Failed to create smem bm`及HYBM=-1。这说明还要核对当前构建真正消费的文件、容器可见性、拓扑内容和rank/通信plane关系；其他目录准备了候选文件，并不表示该读取路径会自动采用它。

不能只因另一份候选源码存在自动构造rootinfo的回退，就认定安装二进制也具有相同行为。也不能盲目把整集群文件复制到全局路径：文件须与实际硬件及P/D通信分组兼容，恢复文件能否排除后续故障尚未验证。

## 6. 真实后端预检：init_bm=False的覆盖边界

建议按以下层次推进，后面各层是仍需完成的验收方法，不是本次已有通过结果：

| 层次 | 检查与继续条件 | 不能替代的验证 |
|---|---|---|
| 配置预检 | 包/库可解析；读取正确MMC文件；实际连接器展开保留原Mooncake | 不等于驱动、通信和LocalService正常 |
| 元数据连通 | MetaService及config store可达；原生元数据初始化成功 | `DistributedObjectStore.init(..., init_bm=False)`不覆盖真实内存后端初始化 |
| 最小真实后端 | 在获授权的空闲少量设备上初始化实际使用的LocalService，确认注册、容量、写入/查询/加载和资源释放 | 不能由导入、符号检查或不启用BM的预检代替；最小API按安装版本核对 |
| P/D服务 | 各角色完成初始化与健康检查；分别保留首错和实际生效配置 | 某一侧失败不能说明另一侧同样失败；正常D是否保留按用户要求执行 |
| 模型池化 | 同一长前缀冷请求与重复请求，区分本地prefix cache和外部池命中；关联池写入、查询、加载、容量与命中指标 | HTTP成功、重复回答或总prefix命中数不能单独证明外部池读命中 |

## 7. 启动顺序与适用边界

启动顺序为**唯一MetaService → 各P/D vLLM → Proxy**。先做上述最小后端检查；P/D启动后确认LocalService注册及容量，再在服务就绪后启动Proxy并进行模型请求。每次重试独立保留配置和首错，不用包装脚本退出0替代服务健康。

本次已核对配置解析、环境路径、有效Mooncake继承及部分实际初始化路径，但服务没有完成完整池化读写验收。P侧还出现独立的profile/HCCL/AICPU错误，不能把D侧拓扑文件错误套用为P侧根因。因此本条保持`candidate`，不将配置模板、换HAL或补rootinfo表述为已验证修复。

原证据日期为2026-10-17；本次文档及示例复核不刷新原实验时间。更换MemCache/MemFabric构建、驱动/CANN、UB/UBOE、连接器实现、并行策略、拓扑或图模式后重新核实。HAL问题复用[已有条目](../../topics/memfabric-hal-notify-compatibility.md)，模型角色参数参见[Kimi K3 P/D参考](../../topics/kimik3-pd-configuration-reference.md)，不在本条复制模型整套启动参数。
