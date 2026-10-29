# 服务性能压测调用说明

使用 `aisbench_auto_tools_prefix` 时读取本说明，其他压测工具按其实际接口使用。

## 来源和运行范围

按 [sources.lock.yaml](../../../../upstream/sources.lock.yaml) 的 `aisbench_auto_tools_prefix` 与本机同名配置解析路径，核对实际 HEAD。来源为 [rayn-zzz/aisbench_auto_tools_prefix](https://github.com/rayn-zzz/aisbench_auto_tools_prefix)，首次固定 `ef2b6d8653d57487b622b0dc9db458f8a1e8dec6`（MIT）；以后升级通过 dependencies 流程，不能运行前自动 pull。

读取原 [README](../../../../deps/aisbench-auto-tools-prefix/README.md)、[CLI](../../../../deps/aisbench-auto-tools-prefix/aisbench_test.py) 和 [config.py](../../../../deps/aisbench-auto-tools-prefix/config.py)。原仓没有requirements/安装清单，AISBench和Python依赖由当前原声明、imports及请求端环境确定；源码就绪不等于已安装或服务可用。

只需在一个可访问服务及tokenizer的请求发起端运行。`deps/` 保持只读；复用已核实的任务专属客户端，或在任务目录/远端任务根创建锁定源码的可写副本。工具会写入 `WORK_PATH/ais_bench/benchmark/configs/models/vllm_api/vllm_api_chat_temp.py` 和 `WORK_PATH/ais_bench/datasets/gsm8k/`，因此使用隔离的AISBench环境或专用checkout；共享同一WORK_PATH的测试须串行。配置与必要兼容patch只改执行副本，保存diff，不改服务依赖或上游子模块。

## 配置和调用

1. 沿用本任务已经确认的服务、tokenizer、输入/输出长度、并发、条数、流式与否、请求速率、重复次数和前缀需求；缺失且会改变实验的问题才澄清。明确k的token换算，并记录实际输入/输出统计，不直接把生成目标长度当最终请求长度。
2. 核对当前服务健康与在途任务，记录运行版本/拓扑引用；只发HTTP负载，不自行启动、停止或重配P/D。部署尚未就绪时先按原部署流程处理。首次安装仅在请求端准备所需依赖，已有可用环境不整体升级。
3. 在可写副本修改以下字段；真实地址、权重路径和鉴权值不写入公共依赖或提交文件。固定版会把`API_KEY`替换进模板、打印并写入`temp_api.py`，因此不能直接传真实密钥；带鉴权场景先在执行副本适配为运行时读取且不回显/落盘密钥，核验后再运行。无鉴权服务保持空值。

| config.py字段 | 取值依据 |
|---|---|
| `DATASET_PATH` / `OUTPUT_DIR` | 本次任务独立且可写的目录 |
| `WORK_PATH` | 专用AISBench源码根或实际site-packages父目录；其下应有`ais_bench/` |
| `MODEL_NAME` / `MODEL_PATH` | 服务实际模型名、请求端可访问的匹配tokenizer路径 |
| `HOST_IP` / `HOST_PORT` / `URL` | 当前服务入口；非空URL优先，按当前AISBench接口确认完整请求URL |
| `POD_INFO` | 收集cache metrics的API列表；PD场景是各P的DP域端点，不是全部机器或D地址 |
| `DEFAULT_PERFORMANCE_TEST` | 当前AISBench支持的`default_perf`或用户明确要求的其他统计配置 |

4. 从副本目录显式传入参数。`python aisbench_test.py --help`只用于已具备imports的客户端；禁止用无参数调用探测安装，因为默认会发起2048并发、8192条负载。下例仅展示16k/1k、99%公共前缀、64并发256条的参数映射，实际值始终来自任务，不作为默认负载：

```bash
python aisbench_test.py \
  --input_len 16384 --output_len 1024 --data_num 256 --concurrency 64 \
  --request_rate 0 --test_type stream --repeat 1 \
  --dataset_type prefix_cache --prefix_num 1 --repeat_rate 99% --prefix_test \
  --dp "$PREFILL_DP" --npu_num "$NPU_COUNT" --seed 1
```

`PREFILL_DP`、`NPU_COUNT`须先按真实拓扑赋值。普通无前缀测试用`--dataset_type normal`并去掉前缀参数；指定数据集使用`--dataset`，当前只支持工具声明的GSM8K格式。`--repeat_rate`是数据集公共前缀比例，不是保证的实际命中率；`--prefix_test`在正式负载前预热，`--dp`按需预热的域数填写，PD不得误用总机器数或D域数。固定版`--repeat`仅在normal分支生效，且汇总仅采集最后一次；前缀多轮或需要逐轮结果时，使用独立目录顺序执行，保留各轮日志。

## 同数据对照与重放

仅在需要比较同一批输入的配置、重复轮或性能回归时，固定正式dataset和公共prefix两份文件的内容、行序与完整SHA；相同seed、名义长度或命中率不足以证明同数据。

固定提交中，`generate_dataset.py:create_multi_prefix_dataset`先生成前缀，随后`generate_unique_tokens`才设置seed；`data_picker.py`的prefix选择使用`random.choice`及持久化的已选集合。`write_data`还会以写入模式覆盖目标，预先放入同名文件不能保证重放。源码按 [固定来源](../../../../upstream/sources.lock.yaml) 的 aisbench_auto_tools_prefix 提交，在维护源内按上述文件和符号核对，不依赖私有知识库才能执行本流程。

对照时保留原件，在新run中复制或只读引用已固定的两份文件，发请求前后校验身份和实际token统计。当前CLI的`--dataset`分支只指定正式集、将prefix路径置空，不能仅加该参数就声称同时复用两份文件。若目标版本没有成对重放入口，只在隔离执行副本将数据生成分支改为校验既定参数和两份文件SHA后返回它们的路径，保存diff；HTTP请求及性能统计路径保持不变，不修改`deps/`或服务端。

固定数据不等于固定服务预热史；需要解释PD吞吐或长尾差异时，分开检查P计算、D排队、KV传输和实际D分流。已有私有知识绑定时可按[知识入口](../../../../knowledge/README.md)检索“PD性能对照、冷态、长尾”并核对版本；未接入不阻塞本流程。普通单轮测量继续原流程，不为此新增默认采样或全量检查。

## 与性能回归工具交接

仅在使用 `performance-regression` 判定基线/候选时进入本节；普通单轮测量不做额外封装。先按[运行体系与执行入口](../../../../upstream/skill-mapping.md#运行体系与执行入口)核对目标接口，再读固定来源的[回归行为契约](../../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-performance-regression/references/behavior.md)。AISBench 的 CSV 不能直接当作该工具的 Benchmark JSON；封装和映射保存在本次任务，不改原生结果或新增一套运行状态。

1. 每个实际 run 对应一个结果。先核对原生正式阶段、成功/失败数、输出完整性及解析有效性，保留失败；只有证据满足本轮测量要求时才将交接 JSON 标为 `status: "ok"`。外层退出0、汇总文件存在或 `9999/99999` 占位值不足以作此判断。
2. 从本轮原生统计读取数值，组织 `{"status":"ok","metrics":{...}}`，按下表映射。延迟须核对实际单位并转换为毫秒；`--metric-map` 只重命名，不换算单位。吞吐保持 token/s，不用请求吞吐、总吞吐或每卡值替代输出 token 吞吐。缺失指标不填0、不以P90替代均值；必需指标缺失时保留无定论，不能因其他指标可解析而通过。

| 固定版 CSV 列或原生统计 | 交接 `metrics` 字段 | 含义与单位 |
|---|---|---|
| `output_throughput` / Output Token Throughput | `output_throughput` | 完整run的输出 token/s |
| `TTFT avg` / TTFT均值 | `mean_ttft_ms` | 均值，毫秒 |
| `TPOT avg` / TPOT均值 | `mean_tpot_ms` | 均值，毫秒 |
| 原生ITL均值，确有该项时 | `mean_itl_ms` | 均值，毫秒；没有则缺省 |

3. 将该 JSON 交给原 `performance_regression.py normalize`。`--state`、`--phase`、`--ordinal` 和 `--config-hash` 取自本实验 `schedule.json`；预热和正式测量分别归档，不把AISBench内部预热当成另一条正式观测。若保留CSV列名，只有数值单位已对齐后才使用 `--metric-map 'ttft=TTFT avg'` 等显式映射。`normalize` 成功只表示已解析字段，仍须检查本任务必需指标是否齐全。
4. 当前 `normalize` 不复制输入中的 `observation`。在 `record` 前，为每条正式测量单独关联该次运行实际采集的代码、环境、模型、拓扑、参数、并发、速率、设备及原生产物身份，按原契约加入测量 JSON 的 `observation` 并保留证据来源。不能照抄 `shared` 声明、首轮观测或计划哈希来冒充后续实测；缺少兼容的观测证据时停在指标汇总，不伪造字段来获得 `passed`。
5. 严格按原 `plan → schedule → normalize/record → analyze` 顺序处理，保留原生文件、映射/单位换算与失败。原比较器负责配置一致性、逐轮观测、预热排除和波动判定；本节不放宽其门槛，也不把只允许代码变化的对照契约套给改变拓扑等条件的配置搜索。

## 固定版本的已知边界

- [default_api.py](../../../../deps/aisbench-auto-tools-prefix/default_api.py)写死`temperature=0, ignore_eos=True`；CLI尝试替换的`generation_kwargs_for_replace`标记实际不存在。不能声称`--enable_think`或`--test_accuracy`已生效，也不能用它替代GPQA采样精度流程。需要其他采样语义时先核对实际生成的API配置与请求，在执行副本做明确适配并留证。
- 自定义tokenizer遇到加载限制时只针对可信模型处理`trust_remote_code`等必要兼容项，记录实际patch；不要把某次Kimi、PyArrow版本或路径变成所有客户端的安装默认值。
- 工具内部有`ais_bench ... | tee ...`管道，生成数据失败的路径也可能退出0。因此外层exit0不足以验收；必须检查AISBench原生结果、正式阶段成功/失败数、期望条数及实际输入/输出。工具汇总解析失败时可能残留`9999/99999`默认值，不得当实测；失败轮保留，不纳入完整成功测量。

## 交付

同一 run 按[材料和总表约定](../../../../docs/guides/task-records.md#aisbench-总表)保存实际源码 SHA 及 patch、完整 config/命令、数据集身份、当时容器环境版本、预热与正式阶段日志及原生统计。正式测试把约定的关键数值直接写入本机总表；内部筛选保留任务记录。前缀测试用相应 P 域 metrics 前后差分报告命中率；解析器依赖当前标签格式，缺少指标时记不可用，不当作零命中。公共前缀比例与实测值分别报告。原始 `aisbench.log` 与工具汇总日志分别标识，运行前保留旧日志，避免覆盖或跨轮拼接。

采样profiling与纯性能测量分别记录，已有服务的采样开关/离线分析复用原profiling入口。结果与日志超过通道预算时保留文件并取摘要/分块，不把截断文本当完整结果。历史机器、容器和运行结果不是当前可用性证明；当前接入方式和检查步骤以本文及[性能压测入口](../SKILL.md)为准，具体运行证据留所属本机任务。
