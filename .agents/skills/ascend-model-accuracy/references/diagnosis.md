# 按症状收敛精度问题

发生输出质量或任务分数异常时读取。方法参考固定版本的[上游诊断手册](../../../../deps/awesome-agent-skills/vllm-ascend-accuracy/references/diagnostic-playbook.md)，只展开与当前症状相关的分支；项目执行与授权约定见[来源与接入](source-and-tools.md)。

## 先区分哪条路径异常

| 症状或对照 | 优先证据与下一判断 |
|---|---|
| 乱码、异常字符 | 对比原始响应字节、文本、token IDs 和同 tokenizer 的 decode，区分传输/编码、token 生成与展示问题 |
| completion 正常、chat 异常 | 对齐渲染后的模板、special/stop tokens 与 reasoning/tool parser，保留解析前后结果 |
| 复读，尤其仅 stream 出现 | 保留 delta 和最终聚合文本，先排除重复拼接，再看模型 token 与 sampler/约束路径；不提高 repetition_penalty 掩盖错误 |
| 空输出、截断或工具调用丢失 | 核对原始与解析后响应、finish/stop reason、终止 token 和输出预算；stop 本身不能证明答案完整 |
| 精度分数下降 | 对齐 dataset revision、few-shot、输入 token IDs、generation config、答案抽取与评分，保存逐题结果；区分评测差异、少量灾难性 case 与整体偏移 |
| 仅 graph、多卡、量化或特定负载异常 | 保留原配置后选择对应分支；特性关闭或版本回退只提供关联/规避证据 |

使用上游完整消融表时按证据选择维度。模型不能单卡或非量化运行时选可行 reference 或较小同结构复现，说明覆盖差异，不把简化场景当作原目标已通过。

## 并发、KV、async 与 MTP

仅在异常依赖长上下文、动态 batch、高并发或这些特性时展开：

1. 保存原配置及有界触发负载，包含前台 bad case 与必要的后台长短混合请求。
2. 分别改变一个相关开关，记录失败数/总数和实际启动配置，避免无效修改叠加。
3. 单开关结果提示交互时，再选择对应二因素/多因素实验；写清实验包含的变量，不称为单变量对照。
4. 在首个异常请求/step 检查 batch row、接受 token 数、KV 生命周期与映射；有证据指向通信或图回放时交由对应领域 skill。

设定请求量、超时和停止条件；未复现只说明该规模内未观察到故障。纯 TP、短请求或关闭 MTP 后正常，不能替代原 PD/DP/EP、长度与负载的回归。

## 从首个分叉进入实现

- 先对齐输入 token IDs 与生成配置，比较 prefill 末位置及首次分叉 decode step 的 token/top-k/logits。比较数值时确认两端使用相同 token 前缀，避免将不同上下文误判成数值根因。
- 有必要时在首个分叉窗口内增加 layer/rank/算子证据；先选小型统计和局部样本，不默认全层全量 dump。
- graph 路径按 graph-debug 使用预分配设备 buffer、图外读回，避免调试同步或打印改变复现；确定性开关作为显式诊断变量，交付前在目标配置复验。
- 同步定位浮点误差、token 排序或 expert selection 的影响；精度阈值使用任务 reference，不能用放宽阈值消除失败。

致因已收敛且有修复授权时，再读[上游修复手册](../../../../deps/awesome-agent-skills/vllm-ascend-accuracy/references/remediation-playbook.md)。先核对目标版本源码与兼容接口，修复后保留最小 case 和原始目标的证据。
