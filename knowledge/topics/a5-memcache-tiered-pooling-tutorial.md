---
id: a5-memcache-tiered-pooling-tutorial
title: A5 HBM、DRAM、SSD三级池化配置教程
status: candidate
updated_at: '2026-10-26T14:40:16.513692+08:00'
verified_at: '2026-10-26T14:40:16.513692+08:00'
observed_at: '2026-10-24'
tags: [A5, MemCache, MemFabric, UBSIO, 三级池化, SSD, MultiConnector, device_urma]
applies_to: Ascend950DT、CANN9.2与memcache_hybrid/memfabric_hybrid1.3.0的历史部署；vLLM0.30系列叠加Ascend池化连接器；必须另行固定实际双仓、驱动和SDK构建
evidence_scope: 配置、初始化、64rank注册及模型启动有历史运行摘要；SSD刷盘与故障也有观测，但跨三级真实回读、回温收益及故障修复未闭环；配置示例为参数化整理，本次不执行远端操作
sources: []
---

# A5三级池化：从磁盘准备到真实回读验收

本文适用于已有可工作的P/D服务，在保留原模型、并行策略和Mooncake传输的基础上接入MemCache。三级指模型侧HBM缓存、共享DRAM池及SSD存储；UBSIO还需要自己的主机缓存预算。**HBM、DRAM池容量、UBSIO缓存和SSD容量分别记录，不能相加后当作模型可用KV容量。**

文中的地址均为文档示例。所有命令供使用者在获授权的目标环境执行；先替换地址、路径、设备及预算，不能直接复制历史机器配置。历史1.2.0用法保留在[基础配置参考](a5-memcache-pooling-setup.md)，问题分层见[池化诊断](a5-memcache-pooling-diagnostics.md)。

## 1. 部署结构与事前记录

| 组件 | 运行位置与职责 | 必须确认 |
|---|---|---|
| MetaService | 全池一个实例，提供目录、配置存储与指标 | 全部参与容器可达，不能每台各启动一个 |
| LocalService | 由各vLLM连接器随进程初始化 | 不另起standalone MemCache；按实际rank注册 |
| AscendStoreConnector | 模型与池之间的写入、查询和加载 | 与安装的连接器版本及KV布局兼容 |
| Mooncake连接器 | 保留既有P→D传输 | 原版本、engine、端口、并行描述不能被池化模板覆盖 |
| UBSIO | SSD访问及其缓存/刷盘路径 | 本地块设备在宿主和容器内身份一致 |

先记录Python解释器、CANN/驱动/固件、两SDK版本与实际库、vLLM双仓SHA及叠加PR。包metadata不一定随源码叠加而变，`pip show`不能代表完整实现。已有服务是否使用新代码，应以实际进程启动和加载路径核验。

预先确定Meta地址、端口、P/D角色、实际LocalService数量及每rank预算。以下示例假设每台8个设备、总64个存储rank，DRAM示例40GiB/rank，理论注册总量为2560GiB；这不是所有机器适用的默认值。`world_size=256`是历史配置中的最大支持rank数，不能据此宣称已注册256个rank。

## 2. 准备专用SSD或loop设备

优先复用已经分配、身份明确且允许本任务使用的块设备。loop镜像适合按历史方式组织验证，但不自动等于裸NVMe的性能，也不代表持久化和故障恢复已验收。

首次创建新镜像的示意，**必须使用专用、尚不存在的文件**：

```bash
# 在宿主执行；先核对目标文件系统容量与健康状态。
image=/path/to/dedicated/ubsio-1t.img
test ! -e "$image" || { echo '目标已存在，停止创建'; exit 1; }
df -h -- "$(dirname "$image")"
fallocate -l 1T -- "$image" || exit 1
loop_dev=$(losetup --find --show --direct-io=on "$image") || exit 1
printf '%s\n' "$loop_dev"
losetup --list --output NAME,BACK-FILE,SIZELIMIT,DIO "$loop_dev"
blockdev --getsize64 "$loop_dev"
ls -l -- "$loop_dev"
```

这里`1T`历史实测为1099511627776字节，即1TiB。另保留宿主自身空间和UBSIO元数据余量，不以“镜像能创建”代替长期容量规划。若预分配失败并留下部分文件，先核对文件大小、归属、loop绑定和使用者；不盲目重试、不自动删除已有同名文件。历史`Bad message`及损坏目录属于文件系统异常，增加空闲空间不证明它已修复。

每台记录真实设备，例如`/dev/loop3`。**设备编号不能跨机照抄。** 在容器内再核对：

```bash
# 在实际运行vLLM的容器里执行；参数换成该机已核对的设备。
python3 - /dev/loop3 <<'PY'
import os
import stat
import sys
p = sys.argv[1]
s = os.stat(p)
assert stat.S_ISBLK(s.st_mode), '需要块设备'
print('major/minor', os.major(s.st_rdev), os.minor(s.st_rdev))
fd = os.open(p, os.O_RDWR)
os.close(fd)
print('O_RDWR open passed; no data written')
PY
```

容器必须具备正确的设备映射及访问权限；宿主有节点不等于容器可见。仅`mknod`出同名路径也不能证明指向正确backing file，仍要对应major/minor和宿主loop绑定。上述打开检查不写数据，因此不能证明SSD读写、刷盘或恢复正确。容器重建、宿主重启后重新核对设备映射；本教程不自动安装持久化规则。

## 3. 配置MetaService

三份后端文件可放在使用者选择的目录，例如`/opt/memcache/`。历史1.3.0拒绝配置软链接，**实际读取的conf使用普通文件**。如果包默认路径与外部路径都必须保留，备份后同步字节，不再用软链接解决双份漂移。

`mmc-meta.conf`示例：

```ini
ock.mmc.meta_service_url = tcp://192.0.2.10:5000
ock.mmc.meta_service.config_store_url = tcp://192.0.2.10:6000
ock.mmc.meta_service.metrics_url = http://192.0.2.10:8001
ock.mmc.log_level = info
ock.mmc.evict_threshold_high = 70
ock.mmc.evict_threshold_low = 60
```

5000/6000是两项不同服务入口，8001用于指标，避开常用模型API8000。70/60来自该历史配置的高低阈值，不代表各层都使用同一百分比策略，换构建要核对字段语义。历史1.3.0曾拒绝`ock.mmc.rewarm.dram_watermark`，不把未知键直接加进配置；保留原文件和解析器错误后，才准备兼容版本。

`run_mem_cache.sh`只负责唯一Meta实例：

```bash
#!/usr/bin/env bash
set -euo pipefail
export MMC_META_CONFIG_PATH=/opt/memcache/mmc-meta.conf
# 调用部署环境既有的CANN和动态库初始化入口。
# 同一个Python解释器须能加载匹配的memcache_hybrid及memfabric_hybrid。
exec python3 -c 'from memcache_hybrid import MetaService; MetaService.main()'
```

先检查已有实例、实际命令和端口。由明确选定的Meta节点启动一次；不要依靠普通后台进程天然存活于网站的stop/cgroup清理。`nohup`仅解决一类终端信号问题，不抵抗SIGKILL。若需要网站前置脚本，在Meta节点用`flock`防重复，后台进程必须关闭继承的锁FD；其余节点等待接口，Meta节点须先执行或参与并发执行。失败要阻断模型启动。HTTP200还须检查响应体有效，不能只用空body返回码宣布指标健康。

## 4. 配置LocalService与UBSIO

每台`mmc-local.conf`示例：

```ini
ock.mmc.meta_service_url = tcp://192.0.2.10:5000
ock.mmc.local_service.config_store_url = tcp://192.0.2.10:6000
ock.mmc.log_level = info
ock.mmc.local_service.world_size = 256
ock.mmc.local_service.protocol = device_urma
ock.mmc.local_service.dram.size = 40GB
ock.mmc.local_service.max.dram.size = 1024GB
ock.mmc.local_service.storage.enabled = true
ubsio.mem.size_in_gb = 30
ubsio.standalone.device_count = 8
# 下面一行仅供获授权的专用新空盘首次初始化示例。
ubsio.standalone.force_new_disk = true
ubsio.disk.path = /dev/loop3
```

| 字段 | 配置含义与使用条件 |
|---|---|
| `dram.size` | 每个存储rank贡献的DRAM池预算；历史40GB按40GiB注册 |
| `max.dram.size` | 上限字段，不是立即预分配1024GB |
| `storage.enabled` | 允许SSD路径；还须UBSIO和实际设备初始化成功 |
| `ubsio.mem.size_in_gb` | UBSIO自己的缓存预算，和DRAM池预算分开；30是历史最终选值，不是推荐默认值或总机内存 |
| `standalone.device_count` | 与该机实际设备/运行组织匹配；历史为8，换组织重新核对 |
| `force_new_disk` | 可能改变已有盘状态；上例只针对明确可初始化的新空盘。复用已有数据前先核对该构建对false/恢复模式的支持和已验证流程，不反复用true启动 |
| `disk.path` | 本机容器可见、身份一致的专用块设备，不能填写其他机器的设备编号 |

历史曾在40GiB配置下只检测到26.53GiB可用额度而失败。该额度的计算公式未查明，不能把事后整机MemAvailable直接等同其额度，也不能把清缓存或一次内存整理当作后续模型加载必然成功。初始化探针的临时资源和常驻模型内存也要分开预算。

## 5. 在原P/D入口增加环境变量与连接器

保留已经验证的CANN/动态库入口，在vLLM启动前增加：

```bash
export PYTHONHASHSEED=0
export MMC_LOCAL_CONFIG_PATH=/opt/memcache/mmc-local.conf
export ASCEND_LOCAL_COMM_RES='{"version":"1.3"}'
```

参与进程使用相同hash seed。上述为`device_urma`历史UB组合；不自动追加UBoE地址或混入另一协议的全局环境。rootinfo要核对当前二进制真正读取的路径、设备和通信plane，文件生成成功不等于通信拓扑成立。

只替换既有`--kv-transfer-config`为MultiConnector组合。以下转换保留原Mooncake对象，**不加历史layerwise默认值，不替用户决定D回写，也不改模型并行参数**：

```bash
# 在对应P/D启动单元设置，D改成kv_consumer。
export POOL_ROLE=kv_producer
# 按当前实现和DP/进程组织确定IPC标识，不按机器尾号猜端口。
export POOL_LOOKUP_ID=0
python3 - original-mooncake.json > pooling-kv.json <<'PY'
import copy
import json
import os
import sys
with open(sys.argv[1], encoding='utf-8') as f:
    original = json.load(f)
role = os.environ['POOL_ROLE']
assert role in ('kv_producer', 'kv_consumer')
assert original['kv_role'] == role
assert original['kv_connector'] in ('MooncakeConnectorV1', 'MooncakeConnectorV2')
moon = copy.deepcopy(original)
parent = {'kv_connector': 'MultiConnector', 'kv_role': role}
if 'engine_id' in moon:
    parent['engine_id'] = moon.pop('engine_id')
store = {'kv_connector': 'AscendStoreConnector', 'kv_role': role,
         'kv_connector_extra_config': {
             'backend': 'memcache', 'lookup_rpc_port': os.environ['POOL_LOOKUP_ID']}}
parent['kv_connector_extra_config'] = {'connectors': [moon, store]}
effective = copy.deepcopy(moon)
if 'engine_id' in parent:
    effective['engine_id'] = parent['engine_id']
assert effective == original
print(json.dumps(parent, ensure_ascii=False))
PY
```

将输出JSON用作原serve命令对应参数；这是增量，不是完整模型启动命令。若原配置已经是MultiConnector，先审查现有子项，不能重复套一层。历史实现展开子项时再次传`engine_id`，故放父级继承，避免重复关键字；安装版本仍须核验真实构造逻辑。

常规P写池，D默认不回写；不擅自加入`consumer_is_to_put=true`或池化`prefill_pp_size`。已有Mooncake的prefill并行描述仍保留原值。`lookup_rpc_port`在对应实现用于构造本地lookup IPC地址，并非可直接按外部TCP端口理解；同一namespace内多个启动单元如何隔离应读实际`get_zmq_rpc_path_lookup`实现。P=0或D的某个rank表达式都不是跨版本通用公式。

`use_layerwise`与图模式另行确认。历史layerwise将FULL_DECODE_ONLY覆盖为PIECEWISE且部分模型跳过捕获；Breakable图只是曾提出的兼容候选，不能在本教程默认启用。以最终生效模式和所有目标worker的capture完成证据验收，argv有参数不够。

## 6. 按阶段启动和验收

| 阶段 | 继续条件 | 本阶段不能证明 |
|---|---|---|
| 配置解析 | 普通conf、实际读取路径和原生解析成功，包/动态库相容 | 硬件通信或池读写成功 |
| Meta | 唯一实例、5000/6000监听、各容器可达，指标body有效 | LocalService已注册 |
| 元数据预检 | `init_bm=False`成功 | BM/UBSIO真实后端初始化 |
| 少rank真实预检 | 在明确空闲设备上`init_bm=True`、UBSIO成功、持有及关闭分别核对 | 全机8rank或全池64rank成功 |
| 全rank注册 | 实际rank唯一、每rank初始化和容量符合预算，错误按rank检查 | 带模型或SSD回读成功 |
| P/D与Proxy | 模型加载、各角色健康、目标worker捕获完成、代理目标正确 | 所有外部路径可达或缓存加速 |
| 模型请求 | 请求真实返回、官方评测/精度达标 | 池中读取确实发生 |
| 三级收益 | 写入/刷盘、目录query、正向加载、请求返回及相同负载时延分别关联 | 短时无错就是长期稳定 |

顺序为**唯一Meta → P/D（LocalService随之初始化）→ Proxy → 推理及池化验证**。原服务已经运行时按当前状态推进，不为遵循顺序擅自重启。P的headless节点不一定监听模型API，按角色检查进程/worker，不能把它没有8000端口认定为失败。

历史64rank曾全部初始化成功、保持20秒，但关闭时11个进程SIGSEGV；初始化通过和退出缺陷必须同时保留。后续新服务成功启动属于另一实例的证据，不能把它写成SDK退出问题已修复。

## 7. 验证真正的池读取与性能价值

保留本地HBM prefix cache作为正常策略。重复相同前缀如果已命中本地缓存，池中即使有对象也可能`need to load: 0`，是合理路径。不要为让池指标增长默认清掉高效本地缓存。

可选择本地自然淘汰后、池里仍保留的前缀重放，或使用两套完整且KV格式兼容的独立P实例：P1写入后，P2处理相同token前缀。PP4的四台机器通常是一套P实例，并不是四套独立P。能否获益还依赖路由、对象是否仍在、加载成本和重算成本。

同时关联以下证据：

1. 原始请求/token前缀、模型与KV布局一致，排除输入和模板变化。
2. 目录query命中，与本地computed token、真正需要load的token分开。
3. `need to load > 0`及连接器加载完成；get/batch_get、DRAM/SSD读取计数在同窗口变化。
4. 模型正常返回，输出质量与正式精度未退化。
5. 固定工作负载与冷/热条件比较TTFT、吞吐和资源开销。

D侧外部命中可能来自Mooncake P→D，不能当作池回读；刷盘数、分配数和容量也不能证明读取收益。记录segment当前占用，别把累计allocated_bytes当当前占用。配置repeat_rate不是实测缓存命中率。

## 8. 复用与回退

保留改前conf、版本和原启动入口；修改后同步所有实际消费文件并核对哈希，保留差异。停止模型不代表宿主transient转发或Meta随之停止，端口冲突要按unit/目标/PID识别，不按端口一杀了之。撤销仅处理明确属于本次的配置或组件。

历史资料提供配置结构和失败边界，未公开完整安装构建、驱动环境及运行原件，因此本条保持candidate。换SDK/CANN/驱动、盘恢复方式、协议、连接器、并行/KV格式或模型后重新检查；SSD长期回收与真正回读未闭环，参见[诊断与待验证机制](a5-memcache-pooling-diagnostics.md)。
